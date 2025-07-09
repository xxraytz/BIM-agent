import pandas as pd
import sqlite3
import os
import json

from .templates import (
    sql_chat_template,
    semantic_check_prompt_template,
    table_identification_template,
    sql_fix_prompt_template,
    response_formalizing_prompt,
    Queries, Query, RelevantTables, SemanticCheck
)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser

from typing import List


# Load database description once
with open('./full_context_based/db_description.txt', 'r', encoding='utf-8') as file:
    DB_DESCRIPTION = file.read()


DATABASE_PATH = "database.sqlite"
MAX_ITERATIONS = 5
PREVIEW_ROWS = 5
DELAY = 0

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    api_key = input("Please enter your Google API Key: ")
if api_key == "":
    raise(
    "Not valid api key"
    )

llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash', # Updated to a newer model
    google_api_key=api_key
)


def get_table_previews(table_names: List[str], conn: sqlite3.Connection) -> str:
    """Queries the database for a preview of rows from specified tables."""
    previews = []
    for table_name in table_names:
        try:
            # Use pandas to safely query and format the preview
            df = pd.read_sql_query(f'SELECT * FROM "{table_name}" LIMIT {PREVIEW_ROWS};', conn)
            previews.append(f"--- Top {PREVIEW_ROWS} rows from table: {table_name} ---\n{df.to_string()}\n")

        except pd.io.sql.DatabaseError as e:
            previews.append(f"--- Could not retrieve preview for table: {table_name} (Error: {e}) ---\n")

    if not previews:
        return "No relevant tables were identified or no data could be previewed."

    return "\n".join(previews)


def identify_relevant_tables(user_query: str) -> List[str]:
    """Step 1: Use LLM to identify tables relevant to the user query."""
    print("--- Identifying relevant tables... ---")
    parser = PydanticOutputParser(pydantic_object=RelevantTables)
    prompt_vars = {
        "db_info": DB_DESCRIPTION,
        "query": user_query,
        "instructions": parser.get_format_instructions(),
    }
    chain = table_identification_template | llm | parser
    try:
        result = chain.invoke(prompt_vars)
        print(f"--- Identified tables: {result.table_names} ---")
        return result.table_names
    except Exception as e:
        print(f"--- Could not identify tables: {e} ---")
        return []


def generate_sql(user_query: str, conn: sqlite3.Connection):
    """Generates SQL queries by first identifying tables and getting previews."""
    # Step 1: Identify relevant tables
    table_names = identify_relevant_tables(user_query)
    
    # Step 2: Get previews of those tables
    table_previews = get_table_previews(table_names, conn)

    # Step 3: Generate SQL using the previews as context
    print("--- Generating SQL query... ---")
    parser = PydanticOutputParser(pydantic_object=Queries)
    prompt_vars = {
        'instructions': parser.get_format_instructions(),
        'query': user_query,
        'db_info': DB_DESCRIPTION,
        'table_previews': table_previews
    }
    chain = sql_chat_template | llm | parser
    output = chain.invoke(prompt_vars)
    return output.queries # Returns a list of Query objects


def fix_sql(original_question: str, query: dict, problem: str, conn: sqlite3.Connection):
    """Fixes a broken SQL query using the new two-step logic."""
    print("--- Attempting to fix SQL... ---")
    # Step 1: Re-identify tables based on the original question
    table_names = identify_relevant_tables(original_question)
    
    # Step 2: Get previews
    table_previews = get_table_previews(table_names, conn)
    
    # Step 3: Fix SQL using the previews as context
    parser = PydanticOutputParser(pydantic_object=Query)
    prompt_vars = {
        'instructions': parser.get_format_instructions(),
        'db_info': DB_DESCRIPTION,
        'table_previews': table_previews,
        'problem': str(problem),
        'prev_query': query['sql'],
        'prev_annotation': query['annotation'],
        'original_question': original_question
    }

    chain = sql_fix_prompt_template | llm | parser
    fixed_query = chain.invoke(prompt_vars).model_dump()
    return fixed_query


def execute_and_evaluate(str_query: str, sql_query: dict, conn: sqlite3.Connection, iteration: int = 0):
    """Executes a single query and evaluates it, with a recursive fix loop."""
    if iteration >= MAX_ITERATIONS:
        print(f"--- Max iterations reached for query: {sql_query['goal']}. Aborting. ---")
        return 'error: max iterations reached'

    try:
        print(f"\n--- [Iteration {iteration+1}] Executing SQL for goal: {sql_query['goal']} ---")
        print(f"SQL: {sql_query['sql']}")
        print(f'Annotation to the SQL: {sql_query["annotation"]}')
        retrieved_data = pd.read_sql_query(sql_query['sql'], conn).to_json(orient='records')
        print(f"Result: {retrieved_data}")

        # If data is empty, it could be a semantic issue.
        if retrieved_data in ('[]', '{}', 'null'):
             raise ValueError("The query returned no data. This might be incorrect. Please check the query logic, especially JOIN conditions and WHERE clauses.")

        parser = PydanticOutputParser(pydantic_object=SemanticCheck)
        prompt_vars = {
            'instructions': parser.get_format_instructions(),
            'goal': sql_query['goal'],
            'sql_query': sql_query['sql'],
            'sql_annotation': sql_query['annotation'],
            'db_result': retrieved_data
        }

        chain = semantic_check_prompt_template | llm | parser
        check_res = chain.invoke(prompt_vars).model_dump()

        if check_res['state']:
            print("--- Semantic check PASSED. ---")
            print(f"Annotation: {check_res['annotation']}")
            return retrieved_data
        else:
            print(f"--- Semantic check FAILED: {check_res['annotation']} ---")
            new_sql_query = fix_sql(str_query, sql_query, check_res['annotation'], conn)
            return execute_and_evaluate(str_query, new_sql_query, conn, iteration + 1)

    except (pd.io.sql.DatabaseError, ValueError, Exception) as e:
        print(f"--- SQL execution FAILED with error: {e} ---")
        new_sql_query = fix_sql(str_query, sql_query, e, conn)
        return execute_and_evaluate(str_query, new_sql_query, conn, iteration + 1)
    

def formalizing_response(user_question, database_response):
    '''formalizing the response based on user question and database response'''
    parser = StrOutputParser()
    prompt_vars = {
            'user_question': user_question,
            'database_response': database_response
        }
    
    chain = response_formalizing_prompt | llm | parser
    answer = chain.invoke(prompt_vars)

    return answer

    
def run_pipeline(user_question: str):
    """Main function to run the entire text-to-SQL pipeline."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        # Generate the initial list of SQL queries
        sql_queries_as_dicts = [q.model_dump() for q in generate_sql(user_question, conn)]
        print(f"\n{'='*50}\nGenerated {len(sql_queries_as_dicts)} initial queries. Now evaluating...\n{'='*50}")
        
        # Evaluate each query
        final_data = [execute_and_evaluate(user_question, query, conn) for query in sql_queries_as_dicts]
        print(f'--- Final data: {final_data}')

    finally:
        conn.close()
        print("--- Database connection closed. ---")
    
    return formalizing_response(user_question, final_data)
    

def main():
    with open('./questions.json', 'r', encoding='utf-8') as file:
        questions = json.load(file)

    # for question in questions:
    #     question = question['question']
        
    #     print(f"User Question: {question}\n")
    
    #     final_result = run_pipeline(question)
        
    #     print('\n' * 3)
    #     print("=" * 75)
    #     print(" " * 25, "FINAL RESULTS")
    #     print("=" * 75)

    #     print(final_result)
    
    #     print("\n" * 5)

    run_pipeline(input('enter your question: '))
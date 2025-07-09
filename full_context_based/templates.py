from langchain.prompts import ChatPromptTemplate, PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from pydantic import BaseModel, Field
from typing import List


class RelevantTables(BaseModel):
    """Pydantic model for identifying relevant tables."""
    table_names: List[str] = Field(
        ...,
        description="A list of table names that are most relevant to answering the user's question, based on the schema."
    )

class Query(BaseModel):
    """Pydantic model for a single SQL query."""
    goal: str = Field(
        ...,
        description='Goal of the current SQL query.' 
    )
    annotation: str = Field(
        ...,
        description='Annotation explaining why this SQL query is necessary to answer the current question. Think step by step how your SQL query should work.' 
    )
    sql: str = Field(
        ...,
        description='SQL code to get necessary data from the database, strictly adhering to the database structure and sampled data.'
    )

class Queries(BaseModel):
    """Pydantic model for a list of SQL queries."""
    queries: List[Query] = Field(
        ...,
        description='A list of SQL queries. Try to make as few requests as possible.'
    )

class SemanticCheck(BaseModel):
    """Pydantic model for the semantic plausibility check."""
    state: bool = Field(
        ...,
        description='true if the database response is semantically plausible, false otherwise.'
    )
    annotation: str = Field(
        ...,
        description='An annotation explaining why you think the state should be true or false.'
    )


table_identification_template = PromptTemplate(
    input_variables=['db_info', 'query', 'instructions'],
    template='''You are a database expert. Your task is to identify the most relevant tables from a database schema to answer a user's question. Only list the tables that are strictly necessary.

Database Schema:
{db_info}

User Question:
{query}

Often you can find useful information in these tables, don\'t forgot to check them:
| Custom Element Type | IFC Class(es)                        |
| ------------------- | ------------------------------------ |
| Property Set        | IfcPropertySet                     |
| Property            | IfcProperty*                       |
| Object Type         | IfcTypeObject, IfcTypeProduct    |
| Classification      | IfcClassificationReference         |
| Material            | IfcMaterial, IfcMaterialLayerSet |
| Group/System        | IfcGroup, IfcSystem              |
| Quantity Set        | IfcElementQuantity                 |
| Relationships       | IfcRel...                          |
| Undefined Objects   | IfcProxy                           |

Your output must strictly adhere to the following instructions:
{instructions}'''
)

sql_generation_sys_template = SystemMessagePromptTemplate(
    prompt=PromptTemplate(
        input_variables=['instructions', 'db_info', 'table_previews'],
        template='''You are an expert SQL developer. Your primary task is to generate precise SQLite queries for a database with a known schema. Your goal is to use these queries to answer a user question about a building.

Information about database structure:
{db_info}

To help you, here are some sample rows from the most relevant tables for the current task:
{table_previews}

The response must be made in accordance with the instructions:
{instructions}'''
    )
)

sql_generation_hum_template = HumanMessagePromptTemplate.from_template('{query}')
sql_chat_template = ChatPromptTemplate.from_messages([sql_generation_sys_template, sql_generation_hum_template])

sql_fix_prompt_template = PromptTemplate(
    input_variables=['instructions', 'db_info', 'table_previews', 'problem', 'prev_annotation', 'prev_query', 'original_question'],
    template='''You are an expert SQL developer. Your task is to fix a broken SQLite query. You will be provided with the original intent, the incorrect query, the error message, the database schema, and sample data from relevant tables.

Original User Question:
{original_question}

Information about database structure:
{db_info}

Here are some sample rows from potentially relevant tables:
{table_previews}

Incorrect Original SQL Query:
{prev_query}

Original Query Annotation:
{prev_annotation}

Problem Description (Error Message or Semantic Issue):
{problem}

Your goal is to provide a corrected query that accurately fulfills the original intent. The response must be made in accordance with the instructions:
{instructions}'''
)

semantic_check_prompt_template = PromptTemplate(
    input_variables=['goal', 'sql_query', 'sql_annotation', 'db_result', 'instructions'],
    template='''You are an expert in the field of construction. Perform a semantic plausibility check. Given the following context, evaluate if the database response is semantically plausible for answering the user query. Remember you do not need to give advice about writing sql code.
Floor area and volume can not be equal 0 or be null or {{}}, [].

Goal of query: {goal}
Generated SQL: {sql_query}
Explanation of the sql code: {sql_annotation}
Database Response: {db_result}

Your output must strictly adhere to the following instructions:
{instructions}'''
)

response_formalizing_prompt = PromptTemplate(
    input_variables=['user_question', 'database_response'],
    template='''**Role:** You are an AI assistant acting as a seasoned construction expert and technical consultant.

**Task:** Your goal is to synthesize a user's question and a raw data response from a database into a human-readable, expert answer.

**Instructions:**
1.  Analyze the user's question to understand their intent.
2.  Interpret the provided database response.
3.  Formulate an answer that is:
    *   **Clear and Concise:** Get straight to the point. Avoid unnecessary fluff.
    *   **Comprehensive:** Fully address the user's question using the provided data.
    *   **Professional:** Use accurate construction terminology (e.g., "compressive strength," "curing time," "load-bearing wall," "rebar").
    *   **Practical:** Frame the answer in a helpful, advisory tone.
4.  **Crucially, do not just repeat the raw data.** Transform it into a coherent explanation in Russian lenguage.

**Input:**
*   **User Question:** `{user_question}`
*   **Database Response:** `{database_response}`

**Generate the expert answer now.**'''
)

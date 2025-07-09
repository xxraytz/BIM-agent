from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOpenAI


MAX_ITERATIONS = 5

key = input('Enter API key:')
llm = ChatOpenAI(model='gpt-4o-mini-2024-07-18', openai_api_key=key)

sys_message_gen = SystemMessagePromptTemplate(
    prompt=PromptTemplate(
        template=(
            "You are an expert in Cypher query language for Memgraph, a graph database compatible with open Cypher. "
            "Generate an accurate Cypher query to solve the given task. Answer only with a JSON object with one key 'cypher' "
            "whose value is the Cypher query string. Do not include any markdown or extra text. Please respond in Russian."
        ),
        input_variables=[]
    )
)


hum_message_gen = HumanMessagePromptTemplate(
    prompt=PromptTemplate(
        template=(
            "You are an AI agent that translates user questions into Cypher queries for a Neo4j database built from an IFC (Industry Foundation Classes) building model.\n\n"
            "The graph schema reflects the structure of IFC data, including nodes like IfcDoor, IfcSpace, IfcWall, IfcRelDefinesByProperties, IfcElementQuantity, etc., and relationships such as IFCRELCONTAINEDINSPATIALSTRUCTURE and IFCRELDEFINESBYPROPERTIES.\n\n"
            "Your task is to:\n"
            "1. Generate an accurate Cypher query that answers the user's question using correct node labels, relationships, and property names.\n"
            "2. Provide a natural-language response template that would be used to present the result to the user.\n\n"
            "Use case-insensitive matching for names and labels where appropriate (e.g., for IfcSpace.Name or Quantity.Name).\n"
            "Include only one Cypher query and one sentence of response.\n\n"
            "Example 1:\n"
            "Question: How many doors exist in the building?\n"
            "Cypher: MATCH (n:IfcDoor) RETURN COUNT(n) AS DoorCount\n"
            "Response: There are {{DoorCount}} doors in the building.\n\n"
            "Example 2:\n"
            "Question: What is the perimeter of the entrance hall?\n"
            "Cypher: MATCH (n1:IfcSpace)-[:IFCRELDEFINESBYPROPERTIES]->(:IfcRelDefinesByProperties)-[]->(qset:IfcElementQuantity)-[]->(quantity)\n"
            "WHERE toLower(n1.Name) CONTAINS toLower('entrance hall') AND toLower(quantity.Name) CONTAINS 'perimeter'\n"
            "RETURN quantity.LengthValue AS Perimeter\n"
            "Response: The entrance hall has a perimeter of {{Perimeter}}.\n\n"
            "Additional context on nodes and relationships in the IFC graph:\n\n"
            "- Nodes such as (:IfcWindow) contain nested properties like BaseQuantities (Area: 3.53486, Height: 1210, Width: 1810, id: 36130), Constraints (Level: \"Level: Ground Floor\", Sill_Height: 900, id: 36140), Dimensions (Area: 3.53486, Volume: 0.0884819, id: 36146), Identity_Data (Mark: \"4\", id: 36153), Other (Category: \"Windows\", Family: \"Windows_Sgl_Plain: 1810x1210mm\", Family_and_Type: \"Windows_Sgl_Plain: 1810x1210mm\", Head_Height: 2110, Host_Id: \"Basic Wall: Wall-Ext_102Bwk-75Ins-100LBlk-12P\", Type: \"Windows_Sgl_Plain: 1810x1210mm\", Type_Id: \"Windows_Sgl_Plain: 1810x1210mm\", id: 36159), along with GlobalId: \"3cUkl32yn9qRSPvBJVyZTO\", Name: \"Windows_Sgl_Plain:1810x1210mm:287567\", ObjectType: \"1810x1210mm\", OverallHeight: 1210, OverallWidth: 1810, PartitioningType: \"NOTDEFINED\", Phasing (Phase_Created: \"New Construction\", id: 36165), PredefinedType: \"WINDOW\", Pset_ManufacturerTypeInformation (Manufacturer: \"Revit\", id: 36117), Pset_WindowCommon (IsExternal: true, Reference: \"1810x1210mm\", ThermalTransmittance: 5.5617, id: 36113), and Tag: \"287567\".\n\n"
            "- Relationships include types like [:HASPROPERTIES] and [:RELATINGPROPERTYDEFINITION], which connect property-related nodes such as IfcRelDefinesByProperties.\n\n"
            "- Other node types include (:IfcRelDefinesByProperties), (:IfcCartesianPoint) with Coordinates, (:IfcAxis2Placement3D), (:IfcProductDefinitionShape), and (:IfcShapeRepresentation) with RepresentationIdentifier and RepresentationType.\n\n"
            "Now, generate the Cypher query and the natural-language response for the following user question:\n"
            "{user_query}"
        ),
        input_variables=["user_query"]
    )
)



chat_template_gen = ChatPromptTemplate([sys_message_gen, hum_message_gen])

class CypherQuery(BaseModel):
    cypher: str = Field(..., description="Cypher query")

def generate_initial_cypher(user_query: str) -> str:
    parser = PydanticOutputParser(pydantic_object=CypherQuery)
    prompt_vars = {"user_query": user_query}
    chain = chat_template_gen | llm | parser
    result = chain.invoke(prompt_vars).model_dump()
    return result["cypher"]

sys_message_fix = SystemMessagePromptTemplate(
    prompt=PromptTemplate(
        template=(
            "You are an expert in Cypher query language for Memgraph. You are given a Cypher query that needs to be improved or corrected. "
            "Also, compare this query with the original user question to ensure the query matches the user's intent. "
            "Answer only with a JSON object with one key 'cypher' whose value is the corrected Cypher query string. "
            "Do not include any markdown or extra text. Please respond in Russian."
        ),
        input_variables=[]
    )
)

hum_message_fix = HumanMessagePromptTemplate(
    prompt=PromptTemplate(
        template=(
            "User question:\n{user_query}\n\n"
            "Previous Cypher query:\n{prev_cypher}\n\n"
            "Problem description or notes:\n{problem}\n\n"
            "Please fix the query."
        ),
        input_variables=["user_query", "prev_cypher", "problem"]
    )
)

chat_template_fix = ChatPromptTemplate([sys_message_fix, hum_message_fix])

class CypherFix(BaseModel):
    cypher: str = Field(..., description="Corrected Cypher query")

def fix_cypher(user_query: str, prev_cypher: str, problem: str) -> str:
    parser = PydanticOutputParser(pydantic_object=CypherFix)
    prompt_vars = {"user_query": user_query, "prev_cypher": prev_cypher, "problem": problem}
    chain = chat_template_fix | llm | parser
    result = chain.invoke(prompt_vars).model_dump()
    return result["cypher"]

def run_query():
    user_query = input("Enter your question in English: ")
    cypher = generate_initial_cypher(user_query)
    for _ in range(MAX_ITERATIONS):
        problem = f"Previous query: {cypher}. Fix it if necessary and ensure it matches the user's question."
        new_cypher = fix_cypher(user_query, cypher, problem)
        if new_cypher.strip() == cypher.strip():
            break
        cypher = new_cypher
    return cypher

if __name__ == "__main__":
    final_cypher = run_query()
    print(final_cypher)

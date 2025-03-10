"""MCP prompt templates for SQL generation."""

from typing import Tuple


def get_sql_generation_prompt(
	natural_language_query: str,
	schema_context: str,
) -> Tuple[str, str]:
	"""Get SQL generation prompt for the given query and schema."""
	system_prompt = """You are a PostgreSQL expert that converts natural language questions into accurate SQL queries.
Your task is to analyze the database schema provided and generate an appropriate SQL query that answers the user's question.

Guidelines:
1. Generate valid PostgreSQL syntax only
2. Use proper table aliases when joining multiple tables
3. Include comments to explain complex parts
4. Structure and format the query for readability
5. Use appropriate JOINs based on the foreign key relationships
6. Consider performance by using efficient query patterns
7. Return only the SQL query, enclosed in ```sql code blocks

Pay careful attention to the schema, including table names, column names, and relationships."""

	user_prompt = f"""Database Schema:
{schema_context}

User Question:
{natural_language_query}

Please generate a PostgreSQL query that answers this question."""

	return system_prompt, user_prompt

"""
PostgreSQL MCP Server

This server provides Model Context Protocol (MCP) access to a PostgreSQL database,
including:
- Table schema resources
- Database metadata resources
- Read-only SQL query tools
- Table analysis tools
- SQL query prompt templates

Usage:
    export POSTGRES_CONNECTION_STRING="postgresql://user:password@localhost:5432/dbname"
    python postgres_server.py
"""

import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator
from urllib.parse import urlparse

import asyncpg
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


@dataclass
class DatabaseContext:
	pool: asyncpg.Pool
	connection_string: str
	database_name: str


@asynccontextmanager
async def postgres_lifespan(server: FastMCP) -> AsyncIterator[DatabaseContext]:
	"""Set up and tear down the PostgreSQL connection"""
	connection_string = os.environ.get('POSTGRES_CONNECTION_STRING')
	if not connection_string:
		logger.error('POSTGRES_CONNECTION_STRING environment variable not set')
		yield None
		return

	# Parse connection string to extract database name
	parsed_url = urlparse(connection_string)
	database_name = parsed_url.path.lstrip('/')

	# Create a connection pool
	try:
		pool = await asyncpg.create_pool(connection_string)
		logger.info(f'Connected to PostgreSQL database: {database_name}')

		# Yield context to the server
		yield DatabaseContext(pool=pool, connection_string=connection_string, database_name=database_name)
	except Exception as e:
		logger.error(f'Failed to connect to PostgreSQL: {str(e)}')
		yield None
	finally:
		# Clean up connection pool when server shuts down
		if 'pool' in locals() and pool is not None:
			await pool.close()
			logger.info('PostgreSQL connection pool closed')


# Initialize the MCP server
mcp = FastMCP('PostgreSQL Explorer', lifespan=postgres_lifespan, dependencies=['asyncpg'])

"""
RESOURCES
"""


@mcp.resource('postgres://schema')
async def list_schema_tables() -> str:
	"""List all tables in the database schema"""
	# Get the context from the FastMCP global request context
	ctx = mcp.get_context()
	db_ctx = ctx.request_context.lifespan_context
	if not db_ctx:
		return 'Database connection not available'

	async with db_ctx.pool.acquire() as conn:
		tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

		if not tables:
			return 'No tables found in the public schema'

		table_list = '\n'.join([f'- {table["table_name"]}' for table in tables])
		return f'Tables in {db_ctx.database_name}:\n\n{table_list}'


@mcp.resource('postgres://table/{table_name}')
async def get_table_schema(table_name: str) -> str:
	"""Get the schema definition for a specific table"""
	ctx = mcp.get_context()
	db_ctx = ctx.request_context.lifespan_context
	if not db_ctx:
		return 'Database connection not available'

	async with db_ctx.pool.acquire() as conn:
		# Check if table exists
		table_check = await conn.fetchrow(
			"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1
            )
        """,
			table_name,
		)

		if not table_check or not table_check[0]:
			return f"Table '{table_name}' not found"

		# Get columns information
		columns = await conn.fetch(
			"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """,
			table_name,
		)

		# Get primary key information
		primary_keys = await conn.fetch(
			"""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = $1::regclass AND i.indisprimary
        """,
			table_name,
		)

		pk_list = [pk['attname'] for pk in primary_keys]

		# Format columns info
		columns_info = []
		for col in columns:
			nullable = 'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'
			default = f'DEFAULT {col["column_default"]}' if col['column_default'] else ''
			pk_marker = 'PRIMARY KEY' if col['column_name'] in pk_list else ''

			columns_info.append(f'  {col["column_name"]} {col["data_type"]} {nullable} {default} {pk_marker}'.strip())

		# Build the complete schema
		schema_def = f'CREATE TABLE {table_name} (\n' + ',\n'.join(columns_info) + '\n);'

		# Add indexes information
		indexes = await conn.fetch(
			"""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = $1
        """,
			table_name,
		)

		indexes_info = ''
		if indexes:
			indexes_info = '\n\n-- Indexes:\n' + '\n'.join([idx['indexdef'] + ';' for idx in indexes])

		return schema_def + indexes_info


@mcp.resource('postgres://database/info')
async def get_database_info() -> str:
	"""Get general information about the connected database"""

	ctx = mcp.get_context()
	db_ctx = ctx.request_context.lifespan_context
	if not db_ctx:
		return 'Database connection not available'

	async with db_ctx.pool.acquire() as conn:
		# Get PostgreSQL version
		version = await conn.fetchval('SELECT version()')

		# Get database size
		db_size = await conn.fetchval('SELECT pg_size_pretty(pg_database_size(current_database()))')

		# Get count of schemas, tables, views
		counts = await conn.fetchrow("""
            SELECT 
                (SELECT COUNT(*) FROM information_schema.schemata) AS schema_count,
                (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') AS table_count,
                (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public') AS view_count
        """)

		return f"""
Database Information:
--------------------
Name: {db_ctx.database_name}
PostgreSQL Version: {version}
Size: {db_size}
Schema Count: {counts['schema_count']}
Table Count: {counts['table_count']}
View Count: {counts['view_count']}
"""


"""
TOOLS
"""


@mcp.tool()
async def run_sql_query(query: str) -> str:
	"""
	Run a read-only SQL query against the PostgreSQL database

	Args:
		query: SQL query to execute (must be SELECT only)

	Returns:
		Query results formatted as text
	"""

	ctx = mcp.get_context()
	db_ctx = ctx.request_context.lifespan_context
	if not db_ctx:
		return 'Database connection not available'

	# Validate this is a read-only query
	query = query.strip()
	if not query.lower().startswith('select'):
		return 'Error: Only SELECT queries are allowed for security reasons'

	async with db_ctx.pool.acquire() as conn:
		try:
			results = await conn.fetch(query)

			if not results:
				return 'Query executed successfully. No results returned.'

			# Get column names from the first result
			columns = results[0].keys()

			# Format as a table
			header = ' | '.join(columns)
			separator = '-' * len(header)
			rows = [' | '.join([str(row[col]) for col in columns]) for row in results]

			result_count = len(results)
			formatted_results = f'{header}\n{separator}\n' + '\n'.join(rows[:100])

			if result_count > 100:
				formatted_results += f'\n\n(Showing 100 of {result_count} results)'

			return formatted_results
		except Exception as e:
			return f'Error executing query: {str(e)}'


@mcp.tool()
async def get_table_stats(table_name: str) -> str:
	"""
	Get statistics about a specific table

	Args:
		table_name: Name of the table to analyze

	Returns:
		Statistics about the table including row count, size, and column statistics
	"""

	ctx = mcp.get_context()
	db_ctx = ctx.request_context.lifespan_context
	if not db_ctx:
		return 'Database connection not available'

	async with db_ctx.pool.acquire() as conn:
		# Check if table exists
		table_check = await conn.fetchrow(
			"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1
            )
        """,
			table_name,
		)

		if not table_check or not table_check[0]:
			return f"Table '{table_name}' not found"

		# Get row count
		row_count = await conn.fetchval(f'SELECT COUNT(*) FROM {table_name}')

		# Get table size
		table_size = await conn.fetchval(
			"""
            SELECT pg_size_pretty(pg_total_relation_size($1))
        """,
			table_name,
		)

		# Get column stats
		columns = await conn.fetch(
			"""
            SELECT 
                column_name, 
                data_type
            FROM 
                information_schema.columns
            WHERE 
                table_schema = 'public' AND table_name = $1
            ORDER BY 
                ordinal_position
        """,
			table_name,
		)

		# For each column, get basic stats
		column_stats = []
		for col in columns:
			col_name = col['column_name']
			data_type = col['data_type']

			# Get nulls percentage
			null_count = await conn.fetchval(f"""
                SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL
            """)
			null_percent = (null_count / row_count * 100) if row_count > 0 else 0

			# Get distinct values count
			distinct_count = await conn.fetchval(f"""
                SELECT COUNT(DISTINCT {col_name}) FROM {table_name}
            """)

			distinct_percent = (distinct_count / row_count * 100) if row_count > 0 else 0

			column_stats.append(
				f"""
Column: {col_name}
Type: {data_type}
Null Values: {null_count} ({null_percent:.1f}%)
Distinct Values: {distinct_count} ({distinct_percent:.1f}%)
""".strip()
			)

		# Combine all stats
		return f"""
Table Statistics: {table_name}
-----------------------
Row Count: {row_count}
Table Size: {table_size}

Column Statistics:
-----------------
{''.join([f'{stat}\n\n' for stat in column_stats])}
""".strip()


@mcp.tool()
async def find_related_tables(table_name: str) -> str:
	"""
	Find tables related to the specified table through foreign keys

	Args:
		table_name: Name of the table to find relationships for

	Returns:
		Description of tables related through foreign keys
	"""

	ctx = mcp.get_context()
	db_ctx = ctx.request_context.lifespan_context
	if not db_ctx:
		return 'Database connection not available'

	async with db_ctx.pool.acquire() as conn:
		# Check if table exists
		table_check = await conn.fetchrow(
			"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1
            )
        """,
			table_name,
		)

		if not table_check or not table_check[0]:
			return f"Table '{table_name}' not found"

		# Tables that this table references (outgoing foreign keys)
		outgoing_refs = await conn.fetch(
			"""
            SELECT
                kcu.table_name as foreign_table,
                rel_kcu.column_name as foreign_column,
                kcu.column_name as local_column
            FROM information_schema.table_constraints tco
            JOIN information_schema.key_column_usage kcu
                ON tco.constraint_schema = kcu.constraint_schema
                AND tco.constraint_name = kcu.constraint_name
            JOIN information_schema.referential_constraints rco
                ON tco.constraint_schema = rco.constraint_schema
                AND tco.constraint_name = rco.constraint_name
            JOIN information_schema.key_column_usage rel_kcu
                ON rco.unique_constraint_schema = rel_kcu.constraint_schema
                AND rco.unique_constraint_name = rel_kcu.constraint_name
                AND kcu.ordinal_position = rel_kcu.ordinal_position
            WHERE
                tco.constraint_type = 'FOREIGN KEY'
                AND kcu.table_name = $1
        """,
			table_name,
		)

		# Tables that reference this table (incoming foreign keys)
		incoming_refs = await conn.fetch(
			"""
            SELECT
                kcu.table_name as foreign_table,
                kcu.column_name as foreign_column,
                rel_kcu.column_name as local_column
            FROM information_schema.table_constraints tco
            JOIN information_schema.key_column_usage kcu
                ON tco.constraint_schema = kcu.constraint_schema
                AND tco.constraint_name = kcu.constraint_name
            JOIN information_schema.referential_constraints rco
                ON tco.constraint_schema = rco.constraint_schema
                AND tco.constraint_name = rco.constraint_name
            JOIN information_schema.key_column_usage rel_kcu
                ON rco.unique_constraint_schema = rel_kcu.constraint_schema
                AND rco.unique_constraint_name = rel_kcu.constraint_name
                AND kcu.ordinal_position = rel_kcu.ordinal_position
            WHERE
                tco.constraint_type = 'FOREIGN KEY'
                AND rel_kcu.table_name = $1
        """,
			table_name,
		)

		result = [f'Relationships for table: {table_name}\n']

		if outgoing_refs:
			result.append('References to other tables (outgoing):')
			for ref in outgoing_refs:
				result.append(f'  - {table_name}.{ref["local_column"]} → {ref["foreign_table"]}.{ref["foreign_column"]}')
		else:
			result.append('No outgoing references found.')

		result.append('')

		if incoming_refs:
			result.append('References from other tables (incoming):')
			for ref in incoming_refs:
				result.append(f'  - {ref["foreign_table"]}.{ref["foreign_column"]} → {table_name}.{ref["local_column"]}')
		else:
			result.append('No incoming references found.')

		return '\n'.join(result)


"""
PROMPTS
"""


@mcp.prompt()
def basic_query_template(table_name: str) -> str:
	"""
	Generate a basic SELECT query template for a specific table

	Args:
		table_name: Name of the table to query
	"""
	return f"""
Generate a SELECT query for the '{table_name}' table.

Sample:
```sql
SELECT * FROM {table_name} LIMIT 10;
```

Please modify this query to select specific columns, add WHERE conditions, 
or include any other SQL features needed to answer my question.
"""


@mcp.prompt()
def join_tables_template(table1: str, table2: str) -> str:
	"""
	Generate a template for joining two tables

	Args:
		table1: First table to join
		table2: Second table to join
	"""
	return f"""
I need help creating a SQL query that joins the '{table1}' and '{table2}' tables.

Please generate a query that:
1. Properly joins these tables based on their relationship
2. Selects relevant columns from both tables
3. Includes appropriate filtering conditions if needed
4. Is formatted for readability

Example structure:
```sql
SELECT t1.column1, t1.column2, t2.column1
FROM {table1} t1
JOIN {table2} t2 ON t1.id = t2.{table1}_id
WHERE t1.column1 = 'value'
LIMIT 100;
```
"""


@mcp.prompt()
def data_analysis_template(table_name: str) -> str:
	"""
	Generate a template for data analysis on a specific table

	Args:
		table_name: Name of the table to analyze
	"""
	return f"""
Help me perform data analysis on the '{table_name}' table.

I'd like to explore:
1. Basic statistics (counts, averages, mins, maxes)
2. Distributions of key columns
3. Potential patterns or anomalies
4. Grouping data in meaningful ways

Please suggest SQL queries for these analyses, explaining what each one shows and how to interpret the results.

Example for basic statistics:
```sql
SELECT 
  COUNT(*) as total_records,
  AVG(numeric_column) as average_value,
  MIN(date_column) as earliest_date,
  MAX(date_column) as latest_date
FROM {table_name};
```
"""


@mcp.prompt()
def query_optimization_template(query: str) -> str:
	"""
	Generate a template for optimizing a SQL query

	Args:
		query: The SQL query to optimize
	"""
	return f"""
I need help optimizing this SQL query:

```sql
{query}
```

Please analyze this query and suggest optimizations for:
1. Performance improvements
2. Better readability
3. Following SQL best practices
4. Potential issues or edge cases

Provide an optimized version of the query with explanations for each change made.
"""


@mcp.prompt()
def database_exploration_workflow() -> str:
	"""Generate a workflow for systematically exploring a new database"""
	return """
I want to explore and understand this database systematically.

Please guide me through a step-by-step process to:

1. First understand the overall database structure
   - What tables exist?
   - How are they related?
   - What's the purpose of each table?

2. Then explore specific tables of interest
   - What columns and data types are in these tables?
   - What are example values?
   - Are there any constraints or indexes?

3. Finally, help me create queries to answer questions about the data
   - How to retrieve specific information?
   - How to aggregate and analyze data?
   - What insights might be available?

Please ask me questions to guide this exploration and help me understand the database thoroughly.
"""


if __name__ == '__main__':
	mcp.run(transport='stdio')

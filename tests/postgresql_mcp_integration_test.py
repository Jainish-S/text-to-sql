"""
Integration Test for PostgreSQL MCP Server

This script tests the PostgreSQL MCP server by starting it as a subprocess
and connecting to it using the MCP client API.

Prerequisites:
1. PostgreSQL test database is set up with test_data.sql
2. The postgres_server.py file is in the same directory
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TEST_CONNECTION_STRING = os.environ.get('POSTGRES_TEST_CONNECTION_STRING', 'postgresql://localhost/mcp_test')


async def main():
	"""Run integration tests for the PostgreSQL MCP server"""

	print('\n=== PostgreSQL MCP Server Integration Test ===\n')

	server_params = StdioServerParameters(
		command=sys.executable,
		args=['src/postgres_mcp_server/main.py'],
		env={'POSTGRES_CONNECTION_STRING': TEST_CONNECTION_STRING},
	)

	try:
		print('Connecting to the server...')
		async with stdio_client(server_params) as (read, write):
			async with ClientSession(read, write) as session:
				await session.initialize()
				print('Connected to the server and initialized the session')

				await test_resources(session)
				await test_tools(session)
				await test_prompts(session)

				print('\n✅ All integration tests passed!')
	except Exception as e:
		print(f'\n❌ Integration test failed: {str(e)}')
		raise


async def test_resources(session: ClientSession):
	"""Test resource functionality"""
	print('\n--- Testing Resources ---')

	print('Listing resources...')
	resources = await session.list_resources()
	resource_uris = [r.uri for r in resources.resources]
	print(f'Found {len(resources.resources)} resources')

	print("Testing 'postgres://schema' resource...")
	schema_content = await session.read_resource('postgres://schema')
	assert schema_content.contents[0].text, 'Schema resource content should not be empty'
	print(f'Schema resource content (excerpt): {schema_content.contents[0].text[:100]}...')

	print("Testing 'postgres://table/customers' resource...")
	customers_schema = await session.read_resource('postgres://table/customers')
	assert 'customer_id' in customers_schema.contents[0].text, "Customers schema should contain 'customer_id'"
	print(f'Customers schema (excerpt): {customers_schema.contents[0].text[:100]}...')

	print("Testing 'postgres://database/info' resource...")
	db_info = await session.read_resource('postgres://database/info')
	assert 'Database Information' in db_info.contents[0].text, "Database info should contain 'Database Information'"
	print(f'Database info (excerpt): {db_info.contents[0].text[:100]}...')

	print('✅ Resources tests passed')


async def test_tools(session: ClientSession):
	"""Test tool functionality"""
	print('\n--- Testing Tools ---')

	print('Listing tools...')
	tools = await session.list_tools()
	tool_names = [t.name for t in tools.tools]
	print(f'Found {len(tools.tools)} tools: {", ".join(tool_names)}')

	print("Testing 'run_sql_query' tool...")
	query_result = await session.call_tool('run_sql_query', {'query': 'SELECT * FROM customers'})
	assert query_result.content[0].text, 'Query result should not be empty'
	print(f'Query result: {query_result.content[0].text}')

	print("Testing 'get_table_stats' tool...")
	stats_result = await session.call_tool('get_table_stats', {'table_name': 'products'})
	assert 'Table Statistics: products' in stats_result.content[0].text, 'Stats result should contain table name'
	print(f'Table stats (excerpt): {stats_result.content[0].text[:100]}...')

	print("Testing 'find_related_tables' tool...")
	relations_result = await session.call_tool('find_related_tables', {'table_name': 'orders'})
	assert 'Relationships for table: orders' in relations_result.content[0].text, 'Relations result should contain table name'
	print(f'Table relations (excerpt): {relations_result.content[0].text[:100]}...')

	print('Testing error handling in tools...')
	error_result = await session.call_tool('run_sql_query', {'query': "INSERT INTO customers (first_name) VALUES ('Test')"})
	assert 'Error' in error_result.content[0].text, 'Non-SELECT query should return an error'
	print(f'Expected error: {error_result.content[0].text}')

	print('✅ Tools tests passed')


async def test_prompts(session: ClientSession):
	"""Test prompt functionality"""
	print('\n--- Testing Prompts ---')

	print('Listing prompts...')
	prompts = await session.list_prompts()
	prompt_names = [p.name for p in prompts.prompts]
	print(f'Found {len(prompts.prompts)} prompts: {", ".join(prompt_names)}')

	print("Testing 'basic_query_template' prompt...")
	query_prompt = await session.get_prompt('basic_query_template', {'table_name': 'customers'})
	assert 'SELECT' in query_prompt.messages[0].content.text, "Query prompt should contain 'SELECT'"
	print(f'Query prompt (excerpt): {query_prompt.messages[0].content.text[:100]}...')

	print("Testing 'join_tables_template' prompt...")
	join_prompt = await session.get_prompt('join_tables_template', {'table1': 'customers', 'table2': 'orders'})
	assert 'JOIN' in join_prompt.messages[0].content.text, "Join prompt should contain 'JOIN'"
	print(f'Join prompt (excerpt): {join_prompt.messages[0].content.text[:100]}...')

	print("Testing 'data_analysis_template' prompt...")
	analysis_prompt = await session.get_prompt('data_analysis_template', {'table_name': 'orders'})
	assert 'data analysis' in analysis_prompt.messages[0].content.text.lower(), 'Analysis prompt should mention data analysis'
	print(f'Analysis prompt (excerpt): {analysis_prompt.messages[0].content.text[:100]}...')

	print('✅ Prompts tests passed')


if __name__ == '__main__':
	asyncio.run(main())

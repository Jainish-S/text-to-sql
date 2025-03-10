# PostgreSQL MCP Server Testing Guide

This guide explains how to set up a test environment and run tests for the PostgreSQL MCP server.

## Setting Up the Test Environment

### 1. Create a Test Database

First, create a dedicated test database in PostgreSQL:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create test database
CREATE DATABASE mcp_test;

# Connect to the new database
\c mcp_test
```

### 2. Load Test Data

The `test_data.sql` script creates a sample e-commerce database with tables for customers, products, orders, and more:

```bash
# Run the test data script
psql -U postgres -d mcp_test -f test_data.sql
```

### 3. Configure Test Environment Variables

Set the connection string for your test database:

```bash
# For Linux/Mac
export POSTGRES_TEST_CONNECTION_STRING="postgresql://username:password@hostname:5432/mcp_test"

# For Windows (Command Prompt)
set POSTGRES_TEST_CONNECTION_STRING=postgresql://username:password@hostname:5432/mcp_test

# For Windows (PowerShell)
$env:POSTGRES_TEST_CONNECTION_STRING="postgresql://username:password@hostname:5432/mcp_test"
```

## Running the Tests

### Unit Tests

The unit tests verify individual components of the server:

```bash
# Run the unit tests
python test_postgres_server.py
```

You should see output showing all tests passing, similar to:

```
......................
----------------------------------------------------------------------
Ran 22 tests in 2.453s

OK
```

### Integration Tests

The integration tests verify the server's functionality as a whole by starting it as a subprocess and connecting to it:

```bash
# Run the integration tests
python integration_test.py
```

You should see detailed output showing the tests connecting to the server and exercising its resources, tools, and prompts.

## Test Coverage

The tests cover all aspects of the PostgreSQL MCP server:

### Resources
- Listing tables in the database schema
- Retrieving table schemas with column definitions
- Getting database metadata and statistics

### Tools
- Running SELECT queries and formatting results
- Retrieving table statistics including row counts and column distributions
- Finding relationships between tables through foreign keys
- Handling errors gracefully (e.g., rejecting non-SELECT queries)

### Prompts
- Basic query templates for specific tables
- Templates for joining tables
- Data analysis prompt templates
- Query optimization templates
- Database exploration workflow

## Manual Testing with the MCP Inspector

For interactive testing, you can use the MCP Inspector:

```bash
# Set the connection string first
export POSTGRES_CONNECTION_STRING="postgresql://username:password@hostname:5432/mcp_test"

# Start the server with the MCP Inspector
mcp dev postgres_server.py
```

This will open a browser interface where you can:
- Explore available resources, tools, and prompts
- Execute tools with custom parameters
- Test prompts with different arguments
- View server logs in real-time

## Testing with Claude Desktop

To test the server with Claude Desktop:

1. Install the server in Claude Desktop:
   ```bash
   mcp install postgres_server.py --name "PostgreSQL Test" -v POSTGRES_CONNECTION_STRING="postgresql://username:password@hostname:5432/mcp_test"
   ```

2. Restart Claude Desktop

3. Ask Claude questions about your test database:
   - "What tables are in my database?"
   - "Show me the schema for the customers table"
   - "How many orders do we have per customer?"
   - "Find tables related to the orders table"

## Troubleshooting Test Issues

### Database Connection Problems

If tests fail with connection errors:
- Verify your connection string is correct
- Check that PostgreSQL is running
- Ensure the test database exists
- Confirm the user has proper permissions

### Missing Tables or Incorrect Schema

If tests fail due to missing tables:
- Make sure you ran the `test_data.sql` script successfully
- Check for error messages during script execution
- Verify table creation with `\dt` in psql

### Server Startup Issues

If the integration tests fail to start the server:
- Check that `postgres_server.py` is in the correct location
- Verify Python environment includes all requirements
- Ensure environment variables are set correctly

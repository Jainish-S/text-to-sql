# Example Claude Interactions with PostgreSQL MCP Server

This document provides examples of how Claude can interact with your database through the PostgreSQL MCP server. These examples assume you have set up the server with the test database.

## Basic Database Exploration

### Asking About Available Tables

**User**: What tables are in my database?

**Claude**: 
I'll check the database schema for you.

According to your database, you have the following tables:
- customers
- orders
- order_items
- products
- product_categories
- regions

The database also contains a view called `order_summary` and a materialized view called `category_sales`.

### Exploring Table Structure

**User**: What's the schema for the customers table?

**Claude**:
Let me retrieve the schema information for the customers table.

Here's the structure of the customers table:

```sql
CREATE TABLE customers (
  customer_id SERIAL PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL,
  phone VARCHAR(20),
  address VARCHAR(200),
  city VARCHAR(50),
  region_id INTEGER REFERENCES regions(region_id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes:
CREATE INDEX idx_customers_region ON customers(region_id);
```

The table has a primary key `customer_id` and a foreign key `region_id` that references the regions table. Some fields like phone and address can be NULL, while others like name and email are required.

## Running SQL Queries

### Simple Query

**User**: How many customers do we have in each region?

**Claude**:
I'll run a query to find the number of customers in each region.

```
region_name | country | count
------------|---------|------
North America | USA | 3
Europe | UK | 3
Asia | Japan | 2
South America | Brazil | 1
Oceania | Australia | 1
```

There are 3 customers each in North America and Europe, 2 customers in Asia, and 1 customer each in South America and Oceania.

### Complex Query

**User**: What are our top 3 selling products by total revenue?

**Claude**:
Let me run a query to find the top 3 selling products by total revenue.

```
product_name | total_quantity | total_revenue
-------------|----------------|-------------
Laptop Pro | 1 | 1499.99
Smartphone X | 2 | 1999.98
Wireless Headphones | 2 | 499.98
```

The top 3 products by revenue are:
1. Laptop Pro with $1,499.99 in revenue
2. Smartphone X with $1,999.98 in revenue
3. Wireless Headphones with $499.98 in revenue

## Data Analysis

### Table Statistics

**User**: Can you provide statistics about the orders table?

**Claude**:
I'll retrieve statistics for the orders table.

**Table Statistics: orders**
-----------------------
Row Count: 15
Table Size: 24 kB

**Column Statistics:**
-----------------
Column: order_id
Type: integer
Null Values: 0 (0.0%)
Distinct Values: 15 (100.0%)

Column: customer_id
Type: integer
Null Values: 0 (0.0%)
Distinct Values: 5 (33.3%)

Column: order_date
Type: timestamp without time zone
Null Values: 0 (0.0%)
Distinct Values: 15 (100.0%)

Column: status
Type: character varying
Null Values: 0 (0.0%)
Distinct Values: 3 (20.0%)

Column: total_amount
Type: numeric
Null Values: 0 (0.0%)
Distinct Values: 15 (100.0%)

Column: shipping_address
Type: character varying
Null Values: 0 (0.0%)
Distinct Values: 5 (33.3%)

The orders table has 15 rows and occupies 24 kB of storage. All columns have complete data (no NULL values). The status column has only 3 distinct values (completed, shipped, processing), while customer_id has 5 distinct values, indicating some customers have placed multiple orders.

### Table Relationships

**User**: How is the orders table related to other tables?

**Claude**:
Let me find the relationships for the orders table.

**Relationships for table: orders**

**References to other tables (outgoing):**
- orders.customer_id → customers.customer_id
- orders.shipping_region_id → regions.region_id

**References from other tables (incoming):**
- order_items.order_id → orders.order_id

The orders table has relationships with:
1. The customers table through the customer_id field (each order belongs to a customer)
2. The regions table through the shipping_region_id field (each order ships to a region)
3. The order_items table through the order_id field (each order contains one or more items)

This shows that orders is a central table in your database, connecting customers with their purchased items and shipping information.

## Advanced Prompt-Based Interactions

### Data Analysis Template

**User**: Help me analyze the sales data in the products table.

**Claude**:
I'll help you analyze the sales data for the products table. Let me first understand what we're working with.

Based on the data analysis template, here are some queries we can run to understand the products and their sales performance:

**1. Basic statistics about products:**

```sql
SELECT 
  COUNT(*) as total_products,
  AVG(price) as average_price,
  MIN(price) as min_price,
  MAX(price) as max_price,
  SUM(stock_quantity) as total_inventory
FROM products;
```

**2. Sales by product category:**

```sql
SELECT 
  pc.category_name,
  COUNT(p.product_id) as product_count,
  SUM(oi.quantity) as items_sold,
  SUM(oi.subtotal) as total_revenue
FROM 
  products p
JOIN 
  product_categories pc ON p.category_id = pc.category_id
JOIN 
  order_items oi ON p.product_id = oi.product_id
GROUP BY 
  pc.category_name
ORDER BY 
  total_revenue DESC;
```

**3. Top selling products:**

```sql
SELECT 
  p.product_name,
  p.price,
  SUM(oi.quantity) as quantity_sold,
  SUM(oi.subtotal) as total_revenue
FROM 
  products p
JOIN 
  order_items oi ON p.product_id = oi.product_id
GROUP BY 
  p.product_id, p.product_name, p.price
ORDER BY 
  quantity_sold DESC
LIMIT 5;
```

Would you like me to run any of these specific queries, or would you like to see different analyses?

### Join Tables Template

**User**: I need to join the customers and orders tables to analyze customer ordering patterns.

**Claude**:
I'll help you create a SQL query that joins the customers and orders tables to analyze ordering patterns.

Here's a query that will show you each customer's ordering activity:

```sql
SELECT 
  c.customer_id,
  c.first_name || ' ' || c.last_name AS customer_name,
  c.email,
  r.region_name,
  COUNT(o.order_id) AS total_orders,
  SUM(o.total_amount) AS total_spent,
  MIN(o.order_date) AS first_order_date,
  MAX(o.order_date) AS most_recent_order_date,
  EXTRACT(DAY FROM (MAX(o.order_date) - MIN(o.order_date))) / 
    NULLIF(COUNT(o.order_id) - 1, 0) AS avg_days_between_orders
FROM 
  customers c
JOIN 
  orders o ON c.customer_id = o.customer_id
JOIN 
  regions r ON c.region_id = r.region_id
GROUP BY 
  c.customer_id, customer_name, c.email, r.region_name
ORDER BY 
  total_spent DESC;
```

This query will show:
- Each customer's name and email
- Their region
- Total number of orders placed
- Total amount spent across all orders
- Their first and most recent order dates
- Average days between orders (for repeat customers)

Is there anything specific about customer ordering patterns you'd like to focus on?

## Using the Query Optimization Template

**User**: Can you optimize this query? SELECT * FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.total_amount > 100

**Claude**:
I'll analyze and optimize your query:

```sql
SELECT * FROM orders o 
JOIN customers c ON o.customer_id = c.customer_id 
WHERE o.total_amount > 100
```

Here's an optimized version:

```sql
SELECT o.order_id, o.order_date, o.status, o.total_amount,
       c.customer_id, c.first_name, c.last_name, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.total_amount > 100
ORDER BY o.total_amount DESC
LIMIT 100;
```

Optimizations made:
1. Replaced `SELECT *` with specific columns to reduce data transfer and improve readability
2. Selected only the most relevant columns that would be needed for analysis
3. Added `ORDER BY o.total_amount DESC` to see highest-value orders first
4. Added `LIMIT 100` to prevent returning too many rows if the result set is large
5. Maintained the original filtering condition on total_amount

These changes will make the query:
- More efficient by fetching only necessary data
- More readable by explicitly naming columns
- More useful by ordering results logically
- Safer for production use by limiting result size

Would you like me to make any other adjustments to this query?

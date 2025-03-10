-- Test Database Setup Script
-- This script creates a sample database for testing the PostgreSQL MCP server
-- It includes multiple tables with relationships and sample data

-- Clear existing tables if they exist
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS product_categories;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS regions;

-- Create regions table
CREATE TABLE regions (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL
);

-- Create customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    region_id INTEGER REFERENCES regions(region_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create product categories table
CREATE TABLE product_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    description TEXT
);

-- Create products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category_id INTEGER REFERENCES product_categories(category_id),
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(12, 2),
    shipping_address VARCHAR(200),
    shipping_city VARCHAR(50),
    shipping_region_id INTEGER REFERENCES regions(region_id)
);

-- Create order items table
CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL
);

-- Add indexes for performance
CREATE INDEX idx_customers_region ON customers(region_id);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Insert sample data for regions
INSERT INTO regions (region_name, country) VALUES
    ('North America', 'USA'),
    ('Europe', 'UK'),
    ('Asia', 'Japan'),
    ('South America', 'Brazil'),
    ('Oceania', 'Australia');

-- Insert sample data for customers
INSERT INTO customers (first_name, last_name, email, phone, address, city, region_id) VALUES
    ('John', 'Doe', 'john.doe@example.com', '555-1234', '123 Main St', 'New York', 1),
    ('Jane', 'Smith', 'jane.smith@example.com', '555-5678', '456 Oak Ave', 'London', 2),
    ('Akira', 'Tanaka', 'akira.tanaka@example.com', '555-9012', '789 Sakura Blvd', 'Tokyo', 3),
    ('Maria', 'Garcia', 'maria.garcia@example.com', '555-3456', '321 Lima St', 'Sao Paulo', 4),
    ('James', 'Wilson', 'james.wilson@example.com', '555-7890', '654 Beach Rd', 'Sydney', 5),
    ('Emma', 'Johnson', 'emma.johnson@example.com', '555-2345', '987 Elm St', 'Chicago', 1),
    ('Hans', 'Schmidt', 'hans.schmidt@example.com', '555-6789', '654 Berlin Ave', 'Berlin', 2),
    ('Yuki', 'Sato', 'yuki.sato@example.com', '555-0123', '321 Cherry St', 'Osaka', 3),
    ('Carlos', 'Mendez', 'carlos.mendez@example.com', '555-4567', '159 Park Ave', 'Mexico City', 4),
    ('Sophie', 'Brown', 'sophie.brown@example.com', '555-8901', '753 Hill Rd', 'Melbourne', 5);

-- Insert sample data for product categories
INSERT INTO product_categories (category_name, description) VALUES
    ('Electronics', 'Electronic devices and accessories'),
    ('Clothing', 'Apparel and fashion items'),
    ('Home & Kitchen', 'Household and kitchen appliances'),
    ('Books', 'Books and literature'),
    ('Sports', 'Sports equipment and gear');

-- Insert sample data for products
INSERT INTO products (product_name, description, price, category_id, stock_quantity) VALUES
    ('Smartphone X', 'Latest model with high-end features', 999.99, 1, 50),
    ('Laptop Pro', 'Professional laptop with powerful specs', 1499.99, 1, 30),
    ('Wireless Headphones', 'Premium noise-cancelling headphones', 249.99, 1, 100),
    ('T-shirt Basic', 'Comfortable cotton t-shirt', 19.99, 2, 200),
    ('Jeans Classic', 'Classic fit denim jeans', 59.99, 2, 150),
    ('Dress Shirt', 'Formal dress shirt for professional settings', 49.99, 2, 80),
    ('Coffee Maker', 'Automatic coffee maker with timer', 89.99, 3, 60),
    ('Blender', 'High-speed blender for smoothies and more', 69.99, 3, 40),
    ('Toaster', '4-slice toaster with multiple settings', 39.99, 3, 75),
    ('Sci-Fi Novel', 'Bestselling science fiction novel', 14.99, 4, 120),
    ('Cookbook', 'Gourmet cooking recipes', 24.99, 4, 90),
    ('History Book', 'Comprehensive world history', 34.99, 4, 60),
    ('Basketball', 'Official size basketball', 29.99, 5, 50),
    ('Tennis Racket', 'Professional tennis racket', 119.99, 5, 30),
    ('Yoga Mat', 'Non-slip yoga and exercise mat', 24.99, 5, 100);

-- Insert sample data for orders with different dates (last 60 days)
INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address, shipping_city, shipping_region_id) VALUES
    (1, CURRENT_TIMESTAMP - INTERVAL '1 day', 'completed', 1249.98, '123 Main St', 'New York', 1),
    (2, CURRENT_TIMESTAMP - INTERVAL '3 days', 'completed', 309.97, '456 Oak Ave', 'London', 2),
    (3, CURRENT_TIMESTAMP - INTERVAL '5 days', 'shipped', 89.99, '789 Sakura Blvd', 'Tokyo', 3),
    (4, CURRENT_TIMESTAMP - INTERVAL '8 days', 'processing', 149.97, '321 Lima St', 'Sao Paulo', 4),
    (5, CURRENT_TIMESTAMP - INTERVAL '10 days', 'completed', 249.99, '654 Beach Rd', 'Sydney', 5),
    (6, CURRENT_TIMESTAMP - INTERVAL '15 days', 'completed', 139.98, '987 Elm St', 'Chicago', 1),
    (7, CURRENT_TIMESTAMP - INTERVAL '18 days', 'cancelled', 69.99, '654 Berlin Ave', 'Berlin', 2),
    (8, CURRENT_TIMESTAMP - INTERVAL '20 days', 'completed', 119.99, '321 Cherry St', 'Osaka', 3),
    (9, CURRENT_TIMESTAMP - INTERVAL '25 days', 'completed', 74.98, '159 Park Ave', 'Mexico City', 4),
    (10, CURRENT_TIMESTAMP - INTERVAL '30 days', 'completed', 999.99, '753 Hill Rd', 'Melbourne', 5),
    (1, CURRENT_TIMESTAMP - INTERVAL '35 days', 'completed', 24.99, '123 Main St', 'New York', 1),
    (2, CURRENT_TIMESTAMP - INTERVAL '40 days', 'completed', 1499.99, '456 Oak Ave', 'London', 2),
    (3, CURRENT_TIMESTAMP - INTERVAL '45 days', 'completed', 34.99, '789 Sakura Blvd', 'Tokyo', 3),
    (4, CURRENT_TIMESTAMP - INTERVAL '50 days', 'completed', 119.98, '321 Lima St', 'Sao Paulo', 4),
    (5, CURRENT_TIMESTAMP - INTERVAL '55 days', 'completed', 79.98, '654 Beach Rd', 'Sydney', 5);

-- Insert sample data for order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
    (1, 1, 1, 999.99, 999.99),
    (1, 3, 1, 249.99, 249.99),
    (2, 6, 1, 49.99, 49.99),
    (2, 9, 1, 39.99, 39.99),
    (2, 14, 1, 119.99, 119.99),
    (3, 7, 1, 89.99, 89.99),
    (4, 10, 1, 14.99, 14.99),
    (4, 12, 1, 34.99, 34.99),
    (4, 15, 1, 24.99, 24.99),
    (5, 3, 1, 249.99, 249.99),
    (6, 4, 2, 19.99, 39.98),
    (6, 11, 1, 24.99, 24.99),
    (7, 8, 1, 69.99, 69.99),
    (8, 14, 1, 119.99, 119.99),
    (9, 4, 1, 19.99, 19.99),
    (9, 11, 1, 24.99, 24.99),
    (9, 15, 1, 24.99, 24.99),
    (10, 1, 1, 999.99, 999.99),
    (11, 15, 1, 24.99, 24.99),
    (12, 2, 1, 1499.99, 1499.99),
    (13, 12, 1, 34.99, 34.99),
    (14, 5, 1, 59.99, 59.99),
    (14, 11, 1, 24.99, 24.99),
    (15, 7, 1, 89.99, 89.99),
    (15, 10, 1, 14.99, 14.99);

-- Create a view for order summaries
CREATE VIEW order_summary AS
SELECT 
    o.order_id,
    o.order_date,
    o.status,
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(oi.item_id) AS item_count,
    SUM(oi.quantity) AS total_quantity,
    o.total_amount
FROM 
    orders o
JOIN 
    customers c ON o.customer_id = c.customer_id
JOIN 
    order_items oi ON o.order_id = oi.order_id
GROUP BY 
    o.order_id, o.order_date, o.status, c.customer_id, customer_name, o.total_amount
ORDER BY 
    o.order_date DESC;

-- Create a materialized view for sales by category
CREATE MATERIALIZED VIEW category_sales AS
SELECT 
    pc.category_id,
    pc.category_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(oi.quantity) AS total_items_sold,
    SUM(oi.subtotal) AS total_sales
FROM 
    product_categories pc
JOIN 
    products p ON pc.category_id = p.category_id
JOIN 
    order_items oi ON p.product_id = oi.product_id
JOIN 
    orders o ON oi.order_id = o.order_id
WHERE 
    o.status = 'completed'
GROUP BY 
    pc.category_id, pc.category_name
ORDER BY 
    total_sales DESC;

-- Create a function to get monthly sales
CREATE OR REPLACE FUNCTION get_monthly_sales(year_num INT)
RETURNS TABLE (
    month VARCHAR(20),
    order_count BIGINT,
    total_sales NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        TO_CHAR(o.order_date, 'Month') AS month,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(o.total_amount) AS total_sales
    FROM 
        orders o
    WHERE 
        EXTRACT(YEAR FROM o.order_date) = year_num
        AND o.status = 'completed'
    GROUP BY 
        EXTRACT(MONTH FROM o.order_date),
        TO_CHAR(o.order_date, 'Month')
    ORDER BY 
        EXTRACT(MONTH FROM o.order_date);
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to update the total_amount in orders when order_items change
CREATE OR REPLACE FUNCTION update_order_total() RETURNS TRIGGER AS $$
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT SUM(subtotal)
        FROM order_items
        WHERE order_id = NEW.order_id
    )
    WHERE order_id = NEW.order_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_items_after_insert_update
AFTER INSERT OR UPDATE ON order_items
FOR EACH ROW
EXECUTE FUNCTION update_order_total();

-- Add some NULL values for testing NULL handling
UPDATE customers SET phone = NULL WHERE customer_id IN (2, 7);
UPDATE customers SET address = NULL WHERE customer_id IN (3, 8);
UPDATE products SET description = NULL WHERE product_id IN (4, 9, 14);
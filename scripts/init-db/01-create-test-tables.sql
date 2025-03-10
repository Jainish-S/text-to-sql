-- Create a test schema
CREATE SCHEMA IF NOT EXISTS test_schema;

-- Create sample tables for testing the text-to-SQL functionality
-- Users table
CREATE TABLE test_schema.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE test_schema.users IS 'Users registered in the system';
COMMENT ON COLUMN test_schema.users.user_id IS 'Unique identifier for the user';
COMMENT ON COLUMN test_schema.users.username IS 'User login name';
COMMENT ON COLUMN test_schema.users.email IS 'User email address';

-- Products table
CREATE TABLE test_schema.products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50),
    in_stock BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_schema.products IS 'Products available for purchase';
COMMENT ON COLUMN test_schema.products.product_id IS 'Unique identifier for the product';
COMMENT ON COLUMN test_schema.products.price IS 'Product price in dollars';

-- Orders table
CREATE TABLE test_schema.orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES test_schema.users(user_id),
    order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(12, 2) NOT NULL
);

COMMENT ON TABLE test_schema.orders IS 'Customer orders';

-- Order items table
CREATE TABLE test_schema.order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES test_schema.orders(order_id),
    product_id INTEGER NOT NULL REFERENCES test_schema.products(product_id),
    quantity INTEGER NOT NULL,
    price_per_unit DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * price_per_unit) STORED
);

COMMENT ON TABLE test_schema.order_items IS 'Individual items within an order';

-- Insert some sample data
INSERT INTO test_schema.users (username, email, first_name, last_name)
VALUES 
    ('johndoe', 'john@example.com', 'John', 'Doe'),
    ('janedoe', 'jane@example.com', 'Jane', 'Doe'),
    ('bobsmith', 'bob@example.com', 'Bob', 'Smith');

INSERT INTO test_schema.products (name, description, price, category)
VALUES 
    ('Laptop', 'High-performance laptop', 1200.00, 'Electronics'),
    ('Smartphone', 'Latest model smartphone', 800.00, 'Electronics'),
    ('Headphones', 'Noise-cancelling headphones', 150.00, 'Accessories'),
    ('Mouse', 'Wireless ergonomic mouse', 50.00, 'Accessories');

INSERT INTO test_schema.orders (user_id, status, total_amount)
VALUES 
    (1, 'completed', 1250.00),
    (2, 'pending', 800.00),
    (1, 'processing', 200.00);

INSERT INTO test_schema.order_items (order_id, product_id, quantity, price_per_unit)
VALUES 
    (1, 1, 1, 1200.00),
    (1, 3, 1, 50.00),
    (2, 2, 1, 800.00),
    (3, 3, 1, 150.00),
    (3, 4, 1, 50.00);
-- ============================================
-- Olist E-Commerce Database Schema
-- ============================================

-- Customers: one row per customer PER ORDER
-- (customer_unique_id identifies the actual person across orders)
CREATE TABLE customers (
    customer_id             VARCHAR(32) PRIMARY KEY,
    customer_unique_id      VARCHAR(32) NOT NULL,
    customer_zip_code_prefix VARCHAR(5),
    customer_city           VARCHAR(100),
    customer_state          CHAR(2)
);

-- Sellers
CREATE TABLE sellers (
    seller_id               VARCHAR(32) PRIMARY KEY,
    seller_zip_code_prefix  VARCHAR(5),
    seller_city             VARCHAR(100),
    seller_state            CHAR(2)
);

-- Product category name translation (Portuguese -> English)
CREATE TABLE category_translation (
    product_category_name          VARCHAR(100) PRIMARY KEY,
    product_category_name_english  VARCHAR(100)
);

-- Products
CREATE TABLE products (
    product_id                  VARCHAR(32) PRIMARY KEY,
    product_category_name       VARCHAR(100) REFERENCES category_translation(product_category_name),
    product_name_length         INT,
    product_description_length  INT,
    product_photos_qty          INT,
    product_weight_g            INT,
    product_length_cm           INT,
    product_height_cm           INT,
    product_width_cm            INT
);

-- Orders: the central table
CREATE TABLE orders (
    order_id                        VARCHAR(32) PRIMARY KEY,
    customer_id                     VARCHAR(32) NOT NULL REFERENCES customers(customer_id),
    order_status                    VARCHAR(20),
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP
);

-- Order items: many rows per order (one per product line)
CREATE TABLE order_items (
    order_id             VARCHAR(32) NOT NULL REFERENCES orders(order_id),
    order_item_id        INT NOT NULL,
    product_id           VARCHAR(32) REFERENCES products(product_id),
    seller_id            VARCHAR(32) REFERENCES sellers(seller_id),
    shipping_limit_date  TIMESTAMP,
    price                NUMERIC(10,2),
    freight_value        NUMERIC(10,2),
    PRIMARY KEY (order_id, order_item_id)
);

-- Order payments: an order can have multiple payment methods/installments
CREATE TABLE order_payments (
    order_id              VARCHAR(32) NOT NULL REFERENCES orders(order_id),
    payment_sequential    INT NOT NULL,
    payment_type          VARCHAR(20),
    payment_installments  INT,
    payment_value         NUMERIC(10,2),
    PRIMARY KEY (order_id, payment_sequential)
);

-- Order reviews
CREATE TABLE order_reviews (
    review_id                 VARCHAR(32) PRIMARY KEY,
    order_id                  VARCHAR(32) NOT NULL REFERENCES orders(order_id),
    review_score              INT,
    review_comment_title      VARCHAR(255),
    review_comment_message    TEXT,
    review_creation_date      TIMESTAMP,
    review_answer_timestamp   TIMESTAMP
);

-- Geolocation: zip prefix -> lat/lng (many rows per zip prefix, not unique)
CREATE TABLE geolocation (
    geolocation_zip_code_prefix VARCHAR(5),
    geolocation_lat             NUMERIC(10,6),
    geolocation_lng             NUMERIC(10,6),
    geolocation_city            VARCHAR(100),
    geolocation_state           CHAR(2)
);

-- Helpful indexes for common joins/filters
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_seller_id ON order_items(seller_id);
CREATE INDEX idx_order_reviews_order_id ON order_reviews(order_id);
CREATE INDEX idx_order_payments_order_id ON order_payments(order_id);

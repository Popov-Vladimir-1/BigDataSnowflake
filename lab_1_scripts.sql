CREATE TABLE dim_suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(255),
    supplier_contact VARCHAR(255),
    supplier_email VARCHAR(255),
    supplier_phone VARCHAR(50),
    supplier_address TEXT,
    supplier_city VARCHAR(100),
    supplier_country VARCHAR(100)
);

CREATE TABLE dim_stores (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(255),
    store_location VARCHAR(255),
    store_city VARCHAR(100),
    store_state VARCHAR(100),
    store_country VARCHAR(100),
    store_phone VARCHAR(50),
    store_email VARCHAR(255)
);

CREATE TABLE dim_customers (
    customer_id INT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INT,
    email VARCHAR(255),
    country VARCHAR(100),
    postal_code VARCHAR(50),
    pet_type VARCHAR(50),
    pet_name VARCHAR(100),
    pet_breed VARCHAR(100)
);

CREATE TABLE dim_sellers (
    seller_id INT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    country VARCHAR(100),
    postal_code VARCHAR(50)
);

CREATE TABLE dim_products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(255),
    product_category VARCHAR(100),
    pet_category VARCHAR(100),
    price DECIMAL(10, 2),
    weight DECIMAL(10, 2),
    color VARCHAR(50),
    size VARCHAR(50),
    brand VARCHAR(100),
    material VARCHAR(100),
    description TEXT,
    rating DECIMAL(3, 1),
    reviews INT,
    release_date DATE,
    expiry_date DATE,
    supplier_id INT REFERENCES dim_suppliers(supplier_id)
);

CREATE TABLE fact_sales (
    sale_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES dim_customers(customer_id),
    seller_id INT REFERENCES dim_sellers(seller_id),
    product_id INT REFERENCES dim_products(product_id),
    store_id INT REFERENCES dim_stores(store_id),
    sale_date DATE,
    sale_quantity INT,
    sale_total_price DECIMAL(10, 2)
);

INSERT INTO dim_suppliers (supplier_name, supplier_contact, supplier_email, supplier_phone, supplier_address, supplier_city, supplier_country)
SELECT DISTINCT supplier_name, supplier_contact, supplier_email, supplier_phone, supplier_address, supplier_city, supplier_country
FROM raw_petshop_data WHERE supplier_name IS NOT NULL;

INSERT INTO dim_stores (store_name, store_location, store_city, store_state, store_country, store_phone, store_email)
SELECT DISTINCT store_name, store_location, store_city, store_state, store_country, store_phone, store_email
FROM raw_petshop_data WHERE store_name IS NOT NULL;

INSERT INTO dim_customers (customer_id, first_name, last_name, age, email, country, postal_code, pet_type, pet_name, pet_breed)
SELECT DISTINCT ON (sale_customer_id) sale_customer_id, customer_first_name, customer_last_name, customer_age, customer_email, customer_country, customer_postal_code, customer_pet_type, customer_pet_name, customer_pet_breed
FROM raw_petshop_data WHERE sale_customer_id IS NOT NULL ORDER BY sale_customer_id;

INSERT INTO dim_sellers (seller_id, first_name, last_name, email, country, postal_code)
SELECT DISTINCT ON (sale_seller_id) sale_seller_id, seller_first_name, seller_last_name, seller_email, seller_country, seller_postal_code
FROM raw_petshop_data WHERE sale_seller_id IS NOT NULL ORDER BY sale_seller_id;

INSERT INTO dim_products (product_id, product_name, product_category, pet_category, price, weight, color, size, brand, material, description, rating, reviews, release_date, expiry_date, supplier_id)
SELECT DISTINCT ON (r.sale_product_id) r.sale_product_id, r.product_name, r.product_category, r.pet_category, r.product_price, r.product_weight, r.product_color, r.product_size, r.product_brand, r.product_material, r.product_description, r.product_rating, r.product_reviews, r.product_release_date, r.product_expiry_date, s.supplier_id
FROM raw_petshop_data r
LEFT JOIN dim_suppliers s ON r.supplier_email = s.supplier_email
WHERE r.sale_product_id IS NOT NULL ORDER BY r.sale_product_id;

INSERT INTO fact_sales (customer_id, seller_id, product_id, store_id, sale_date, sale_quantity, sale_total_price)
SELECT r.sale_customer_id, r.sale_seller_id, r.sale_product_id, st.store_id, r.sale_date, r.sale_quantity, r.sale_total_price
FROM raw_petshop_data r
LEFT JOIN dim_stores st ON r.store_email = st.store_email;
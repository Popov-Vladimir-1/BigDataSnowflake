import psycopg2
import glob
import os

# Получаем путь к папке скрипта
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "petshop_db"
DB_USER = "admin"
DB_PASS = "adminpassword"

SQL_CLEANUP = """
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS dim_sellers CASCADE;
DROP TABLE IF EXISTS dim_stores CASCADE;
DROP TABLE IF EXISTS dim_suppliers CASCADE;
DROP TABLE IF EXISTS raw_petshop_data CASCADE;
"""

SQL_CREATE_RAW = """
CREATE TABLE raw_petshop_data (
    id INT,
    customer_first_name VARCHAR(100),
    customer_last_name VARCHAR(100),
    customer_age INT,
    customer_email VARCHAR(255),
    customer_country VARCHAR(100),
    customer_postal_code VARCHAR(50),
    customer_pet_type VARCHAR(50),
    customer_pet_name VARCHAR(100),
    customer_pet_breed VARCHAR(100),
    seller_first_name VARCHAR(100),
    seller_last_name VARCHAR(100),
    seller_email VARCHAR(255),
    seller_country VARCHAR(100),
    seller_postal_code VARCHAR(50),
    product_name VARCHAR(255),
    product_category VARCHAR(100),
    product_price DECIMAL(10,2),
    product_quantity INT,
    sale_date DATE,
    sale_customer_id INT,
    sale_seller_id INT,
    sale_product_id INT,
    sale_quantity INT,
    sale_total_price DECIMAL(10,2),
    store_name VARCHAR(255),
    store_location VARCHAR(255),
    store_city VARCHAR(100),
    store_state VARCHAR(100),
    store_country VARCHAR(100),
    store_phone VARCHAR(50),
    store_email VARCHAR(255),
    pet_category VARCHAR(100),
    product_weight DECIMAL(10,2),
    product_color VARCHAR(50),
    product_size VARCHAR(50),
    product_brand VARCHAR(100),
    product_material VARCHAR(100),
    product_description TEXT,
    product_rating DECIMAL(3,1),
    product_reviews INT,
    product_release_date DATE,
    product_expiry_date DATE,
    supplier_name VARCHAR(255),
    supplier_contact VARCHAR(255),
    supplier_email VARCHAR(255),
    supplier_phone VARCHAR(50),
    supplier_address TEXT,
    supplier_city VARCHAR(100),
    supplier_country VARCHAR(100)
);
"""

SQL_CREATE_SNOWFLAKE = """
CREATE TABLE dim_suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(255) UNIQUE,
    supplier_contact VARCHAR(255),
    supplier_email VARCHAR(255),
    supplier_phone VARCHAR(50),
    supplier_address TEXT,
    supplier_city VARCHAR(100),
    supplier_country VARCHAR(100)
);

CREATE TABLE dim_stores (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(255) UNIQUE,
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
    price DECIMAL(10,2),
    weight DECIMAL(10,2),
    color VARCHAR(50),
    size VARCHAR(50),
    brand VARCHAR(100),
    material VARCHAR(100),
    description TEXT,
    rating DECIMAL(3,1),
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
    sale_total_price DECIMAL(10,2)
);
"""

SQL_POPULATE_SNOWFLAKE = """
-- Заполнение поставщиков (уникальные по имени)
INSERT INTO dim_suppliers (supplier_name, supplier_contact, supplier_email, supplier_phone, supplier_address, supplier_city, supplier_country)
SELECT supplier_name, MIN(supplier_contact), MIN(supplier_email), MIN(supplier_phone), MIN(supplier_address), MIN(supplier_city), MIN(supplier_country)
FROM raw_petshop_data 
WHERE supplier_name IS NOT NULL
GROUP BY supplier_name
ON CONFLICT (supplier_name) DO NOTHING;

-- Заполнение магазинов (уникальные по имени)
INSERT INTO dim_stores (store_name, store_location, store_city, store_state, store_country, store_phone, store_email)
SELECT store_name, MIN(store_location), MIN(store_city), MIN(store_state), MIN(store_country), MIN(store_phone), MIN(store_email)
FROM raw_petshop_data 
WHERE store_name IS NOT NULL
GROUP BY store_name
ON CONFLICT (store_name) DO NOTHING;

-- Заполнение покупателей
INSERT INTO dim_customers (customer_id, first_name, last_name, age, email, country, postal_code, pet_type, pet_name, pet_breed)
SELECT DISTINCT ON (sale_customer_id) 
    sale_customer_id, 
    customer_first_name, 
    customer_last_name, 
    customer_age, 
    customer_email, 
    customer_country, 
    customer_postal_code, 
    customer_pet_type, 
    customer_pet_name, 
    customer_pet_breed
FROM raw_petshop_data 
WHERE sale_customer_id IS NOT NULL
ORDER BY sale_customer_id
ON CONFLICT (customer_id) DO NOTHING;

-- Заполнение продавцов
INSERT INTO dim_sellers (seller_id, first_name, last_name, email, country, postal_code)
SELECT DISTINCT ON (sale_seller_id) 
    sale_seller_id, 
    seller_first_name, 
    seller_last_name, 
    seller_email, 
    seller_country, 
    seller_postal_code
FROM raw_petshop_data 
WHERE sale_seller_id IS NOT NULL
ORDER BY sale_seller_id
ON CONFLICT (seller_id) DO NOTHING;

-- Заполнение товаров (связываем с поставщиком по имени)
INSERT INTO dim_products (product_id, product_name, product_category, pet_category, price, weight, color, size, brand, material, description, rating, reviews, release_date, expiry_date, supplier_id)
SELECT DISTINCT ON (r.sale_product_id) 
    r.sale_product_id, 
    r.product_name, 
    r.product_category, 
    r.pet_category, 
    r.product_price, 
    r.product_weight, 
    r.product_color, 
    r.product_size, 
    r.product_brand, 
    r.product_material, 
    r.product_description, 
    r.product_rating, 
    r.product_reviews, 
    r.product_release_date, 
    r.product_expiry_date, 
    s.supplier_id
FROM raw_petshop_data r
LEFT JOIN dim_suppliers s ON r.supplier_name = s.supplier_name
WHERE r.sale_product_id IS NOT NULL
ORDER BY r.sale_product_id
ON CONFLICT (product_id) DO NOTHING;

-- Заполнение фактов (связываем с магазином по имени)
INSERT INTO fact_sales (customer_id, seller_id, product_id, store_id, sale_date, sale_quantity, sale_total_price)
SELECT 
    r.sale_customer_id, 
    r.sale_seller_id, 
    r.sale_product_id, 
    st.store_id, 
    r.sale_date, 
    r.sale_quantity, 
    r.sale_total_price
FROM raw_petshop_data r
LEFT JOIN dim_stores st ON r.store_name = st.store_name
LEFT JOIN dim_customers c ON c.customer_id = r.sale_customer_id
LEFT JOIN dim_sellers sel ON sel.seller_id = r.sale_seller_id
LEFT JOIN dim_products p ON p.product_id = r.sale_product_id
WHERE c.customer_id IS NOT NULL 
  AND sel.seller_id IS NOT NULL 
  AND p.product_id IS NOT NULL 
  AND st.store_id IS NOT NULL;
"""

SQL_VALIDATION = """
SELECT 'Сырые данные (raw_petshop_data)' AS table_name, COUNT(*) AS count FROM raw_petshop_data
UNION ALL
SELECT 'Факты (fact_sales)', COUNT(*) FROM fact_sales
UNION ALL
SELECT 'Поставщики (dim_suppliers)', COUNT(*) FROM dim_suppliers
UNION ALL
SELECT 'Магазины (dim_stores)', COUNT(*) FROM dim_stores
UNION ALL
SELECT 'Покупатели (dim_customers)', COUNT(*) FROM dim_customers
UNION ALL
SELECT 'Продавцы (dim_sellers)', COUNT(*) FROM dim_sellers
UNION ALL
SELECT 'Товары (dim_products)', COUNT(*) FROM dim_products;
"""

SQL_ANALYTICS = """
SELECT 
    p.product_category,
    p.pet_category,
    COUNT(*) AS sales_count,
    SUM(f.sale_quantity) AS total_units,
    SUM(f.sale_total_price) AS total_revenue
FROM fact_sales f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.product_category, p.pet_category
ORDER BY total_revenue DESC
LIMIT 10;
"""


def main():
    conn = None
    try:
        print("Подключение к базе данных PostgreSQL...")
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        print("Подключение успешно!")

        print("Очистка старых данных...")
        cur.execute(SQL_CLEANUP)
        print("Очистка выполнена.")

        print("Создание таблицы raw_petshop_data...")
        cur.execute(SQL_CREATE_RAW)
        print("Таблица создана.")
        conn.commit()

        # Ищем файлы в папке data
        csv_files = glob.glob(os.path.join(DATA_DIR, "mock_data*.csv"))
        print(f"Поиск файлов в: {DATA_DIR}")
        print(f"Найдено CSV файлов: {len(csv_files)}")
        
        if not csv_files:
            print("ОШИБКА: CSV файлы не найдены в папке data/")
            print(f"Проверьте путь: {DATA_DIR}")
            return

        print("Начинаем загрузку CSV файлов...")
        cur.execute("SET datestyle = 'MDY';")

        for file in csv_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    next(f)
                    cur.copy_expert("COPY raw_petshop_data FROM STDIN WITH CSV", f)
                print(f"OK: {os.path.basename(file)}")
            except Exception as e:
                print(f"Ошибка при загрузке {file}: {e}")

        conn.commit()
        print("Все CSV файлы загружены.")

        print("Создание таблиц снежинки...")
        cur.execute(SQL_CREATE_SNOWFLAKE)
        conn.commit()
        print("Таблицы созданы.")

        print("Заполнение измерений и фактов...")
        cur.execute(SQL_POPULATE_SNOWFLAKE)
        conn.commit()
        print("Данные заполнены.")

        print("\n" + "="*50)
        print("ПРОВЕРКА РЕЗУЛЬТАТОВ:")
        print("="*50)
        cur.execute(SQL_VALIDATION)
        results = cur.fetchall()
        for row in results:
            print(f"{row[0]}: {row[1]}")
        
        print("\n" + "="*50)
        print("ТОП-10 КАТЕГОРИЙ ПО ВЫРУЧКЕ:")
        print("="*50)
        cur.execute(SQL_ANALYTICS)
        results = cur.fetchall()
        for row in results:
            print(f"{row[0]} / {row[1]}: {row[2]} продаж, выручка: {row[4]:.2f}")

        print("\nГОТОВО! База данных успешно спроектирована и заполнена.")

    except Exception as e:
        print(f"ПРОИЗОШЛА ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
    finally:
        if 'cur' in locals(): 
            cur.close()
        if conn: 
            conn.close()


if __name__ == "__main__":
    main()
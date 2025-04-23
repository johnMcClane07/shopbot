import sqlite3
import logging
import config


def get_db_connection():
    conn = sqlite3.connect(config.DB_PATH)  
    conn.row_factory = sqlite3.Row  
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category TEXT NOT NULL COLLATE NOCASE,
        image_url TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(id),
        UNIQUE (user_id, product_id)  -- Запрещаем дублирование товара в корзине
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_quantity INTEGER NOT NULL,
        address TEXT NOT NULL,
        total_price REAL NOT NULL,
        status TEXT CHECK(status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    ''')

    conn.commit()
    conn.close()

create_tables()


def add_product(name, description, price, category, image_url):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO products (name, description, price, category, image_url) 
    VALUES (?, ?, ?, ?, ?)
    ''', (name, description, price, category.lower().strip(), image_url))

    conn.commit()
    conn.close()

def get_products_by_category(category):
    category = category.split('category_')[1]
    logging.info(f"🔍 Полученная категория: {category}")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM products")
    all_categories = cursor.fetchall()
    logging.info(f"📂 Все категории в БД: {[row[0] for row in all_categories]}")

    cursor.execute("SELECT * FROM products WHERE LOWER(category) = LOWER(?)", (category,))
    products = cursor.fetchall()

    conn.close()
    return products


def get_user(user_id):

    conn=get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    conn.close()
    return user

def create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, last_name)
    )

    conn.commit()
    conn.close()

def add_to_cart(product_id,user_id):
    print(product_id)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    existing_item = cursor.fetchone()

    if existing_item:
        new_quantity = existing_item[0] + 1
        cursor.execute("UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?", (new_quantity, user_id, product_id))
    else:
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, 1))


    conn.commit()
    conn.close()



def get_users_cart(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.name, p.price, p.image_url, c.quantity 
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    """, (user_id,))

    cart_items = cursor.fetchall()
    conn.close()

    return [
        {
            "id": item[0],
            "name": item[1],
            "price": item[2],
            "image_url": item[3],
            "quantity": item[4]
        }
        for item in cart_items
    ]


def delete_from_cart(user_id: int, product_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))

    conn.commit()
    conn.close()


def search (query):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + query + '%',))
    products = cursor.fetchall()

    conn.close()
    return products

def create_order(user_id, total_price, status='pending',products=None, adress=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO orders (user_id, total_price, status, adress) VALUES (?, ?, ?)", (user_id, total_price, status,adress))
    order_id = cursor.lastrowid

    if products:
        for product in products:
            cursor.execute("INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)", (order_id, product['id'], product['quantity']))

    conn.commit()
    conn.close()

    return order_id


def clear_cart(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))

    conn.commit()
    conn.close()

def add_discount_to_product(product_id, discount_value):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE products
    SET discounts = ?
    WHERE id = ?
    ''', (discount_value, product_id))

    conn.commit()
    conn.close()








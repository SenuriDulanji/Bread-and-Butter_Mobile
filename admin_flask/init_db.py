import sqlite3
import hashlib

# Connect to the database
conn = sqlite3.connect('bread_and_butter.db')
cursor = conn.cursor()

# Drop existing tables if they exist
cursor.execute("DROP TABLE IF EXISTS bread_admin")
cursor.execute("DROP TABLE IF EXISTS bread_users")
cursor.execute("DROP TABLE IF EXISTS bread_items")
cursor.execute("DROP TABLE IF EXISTS bread_orders")

# Create bread_admin table
cursor.execute("""
CREATE TABLE bread_admin (
    bread_admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bread_admin_username TEXT NOT NULL,
    bread_admin_password TEXT NOT NULL
)
""")

# Create bread_users table
cursor.execute("""
CREATE TABLE bread_users (
    bread_user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bread_user_name TEXT NOT NULL,
    bread_user_password TEXT NOT NULL,
    bread_user_phone TEXT,
    bread_user_otp TEXT,
    bread_user_is_verified INTEGER DEFAULT 0,
    bread_user_created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Create bread_items table
cursor.execute("""
CREATE TABLE bread_items (
    bread_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bread_item_name TEXT NOT NULL,
    bread_item_description TEXT,
    bread_item_price REAL NOT NULL,
    bread_item_type TEXT,
    bread_item_image TEXT,
    bread_item_created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    bread_item_updated_at DATETIME
)
""")

# Create bread_orders table
cursor.execute("""
CREATE TABLE bread_orders (
    bread_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bread_user_id INTEGER,
    bread_order_total REAL NOT NULL,
    bread_order_status TEXT DEFAULT 'pending',
    bread_order_created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bread_user_id) REFERENCES bread_users (bread_user_id)
)
""")

# Insert a default admin user
admin_username = 'admin'
admin_password = 'password'  # In a real application, use a more secure password
md5_password = hashlib.md5(admin_password.encode()).hexdigest()

cursor.execute("INSERT INTO bread_admin (bread_admin_username, bread_admin_password) VALUES (?, ?)", (admin_username, md5_password))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database initialized successfully.")

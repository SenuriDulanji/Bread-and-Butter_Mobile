import sqlite3
import json
import os

# We import your existing function to grab the JSON from Google Cloud
from app.services.ai_service import get_menu_from_gcs

# Define the path to your SQLite DB exactly where your app expects it
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'breadandbutter.db')

def sync_cloud_to_sqlite():
    print("☁️ Fetching menu from Google Cloud...")
    json_text = get_menu_from_gcs()
    
    if not json_text:
        print("❌ Failed to download JSON. Check your Cloud Storage permissions.")
        return

    # Parse the text into a Python dictionary
    data = json.loads(json_text)
    
    print(f"📂 Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # --- 1. SAFELY RESET ONLY THE MENU TABLES ---
        # This keeps your users table completely safe!
        print("🧹 Cleaning old menu schemas...")
        cursor.execute('DROP TABLE IF EXISTS menu_item')
        cursor.execute('DROP TABLE IF EXISTS category')

        # --- 2. RECREATE TABLES WITH EXACT FLASK SCHEMA ---
        print("🏗️ Creating fresh tables...")
        cursor.execute('''
            CREATE TABLE category (
                id INTEGER PRIMARY KEY,
                name TEXT,
                image TEXT,                                   -- Added for Flask
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- Added for Flask
            )
        ''')

        cursor.execute('''
                CREATE TABLE menu_item (
                    id INTEGER PRIMARY KEY, 
                    name TEXT,
                    price REAL,          
                    description TEXT,
                    image TEXT,          
                    category_id INTEGER,
                    is_available BOOLEAN DEFAULT 1,                -- Added for Flask (1 = True)
                    discount_percentage REAL DEFAULT 0.0,          -- Added for Flask (0 discount)
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Added for Flask
                    FOREIGN KEY (category_id) REFERENCES category(id)
                )
            ''')
        # --- 3. INSERT THE DATA ---
        cat_count = 0
        item_count = 0
        print("📥 Inserting new data from Cloud...")

        for category_data in data.get('menu_items', []):
            # Force these to be standard integers and strings
            cat_id = int(category_data['category_id']) 
            cat_name = str(category_data['category'])
            
            # Insert the Category
            cursor.execute('INSERT INTO category (id, name) VALUES (?, ?)', (cat_id, cat_name))
            cat_count += 1

            # Insert the Items for this Category
            for item in category_data.get('items', []):
                
                # We force the types here so SQLite never throws a datatype mismatch
                safe_item_id = int(item['item_id'])
                safe_price = float(item['price'])
                
                cursor.execute('''
                    INSERT INTO menu_item (id, name, price, description, image, category_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    safe_item_id, 
                    item['name'], 
                    safe_price, 
                    item.get('description', ''), 
                    item.get('image_url', ''), # Grabs the cloud URL from JSON to save in the 'image' column
                    cat_id
                ))
                item_count += 1

        # Save the changes to the database!
        conn.commit()
        print(f"✅ Success! Synced {cat_count} categories and {item_count} items from Cloud to SQLite.")

    except Exception as e:
        # If anything crashes, undo the changes so the database isn't corrupted
        conn.rollback() 
        print(f"❌ Error during sync: {e}")
    finally:
        # Always close the connection
        conn.close()

if __name__ == "__main__":
    sync_cloud_to_sqlite()
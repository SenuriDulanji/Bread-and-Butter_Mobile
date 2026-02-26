import sqlite3
import os

def fix_feedback_table():
    # 1. Set the absolute path to your database
    db_path = r"D:\AI-Project-Group-4\backend\instance\breadandbutter.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Error: Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🛠️  Dropping old table...")
        cursor.execute("DROP TABLE IF EXISTS cloud_feedback;")

        print("🏗️  Creating new table with AUTOINCREMENT...")
        # id INTEGER PRIMARY KEY AUTOINCREMENT ensures the ID changes every time
        cursor.execute("""
            CREATE TABLE cloud_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                category TEXT NOT NULL,
                reward REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("✅ Success! The feedback table is now clean and fixed.")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_feedback_table()
import sqlite3

# Path to your database
conn = sqlite3.connect("instance/breadandbutter.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
conn.close()

print("✅ ai_recommendations table created successfully!")
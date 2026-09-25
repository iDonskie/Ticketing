import sqlite3
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'tickets.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if resolution_feedback column already exists
    cursor.execute("PRAGMA table_info(tickets);")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'resolution_feedback' not in columns:
        cursor.execute("ALTER TABLE tickets ADD COLUMN resolution_feedback TEXT DEFAULT '';")
        conn.commit()
        print("Successfully added missing 'resolution_feedback' column!")
    else:
        print("'resolution_feedback' column already exists.")

except Exception as e:
    print("Error updating database:", e)
finally:
    conn.close()
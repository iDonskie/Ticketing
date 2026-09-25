import sqlite3
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'tickets.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE tickets ADD COLUMN notif_read INTEGER DEFAULT 1;")
    conn.commit()
    print("Successfully added 'notif_read' column to tickets table without losing data!")
except sqlite3.OperationalError as e:
    print("Column might already exist:", e)
finally:
    conn.close()
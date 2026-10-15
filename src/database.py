import sqlite3
import os

def get_db_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, '..', 'tickets.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, '..', 'tickets.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            q1 TEXT, a1 TEXT,
            q2 TEXT, a2 TEXT,
            q3 TEXT, a3 TEXT,
            role TEXT CHECK(role IN ('Admin', 'Requestor', 'Developer')) NOT NULL
        )
    ''')

    # Tickets Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT CHECK(status IN ('Open', 'In Progress', 'Pending Verification', 'Resolved', 'Reopened')) DEFAULT 'Open',
            requestor_id INTEGER,
            assigned_to INTEGER,
            notifications TEXT DEFAULT '',
            resolution_feedback TEXT DEFAULT '',
            priority TEXT CHECK(priority IN ('Low', 'Medium', 'High', 'Urgent')) DEFAULT 'Medium',
            FOREIGN KEY(requestor_id) REFERENCES users(id),
            FOREIGN KEY(assigned_to) REFERENCES users(id)
        )
    ''')

    # Safely inject missing columns if they don't exist yet in older DB files
    columns_to_check = [
        ("resolution_feedback", "TEXT DEFAULT ''"),
        ("priority", "TEXT CHECK(priority IN ('Low', 'Medium', 'High', 'Urgent')) DEFAULT 'Medium'")
    ]

    for col_name, col_def in columns_to_check:
        try:
            cursor.execute(f"ALTER TABLE tickets ADD COLUMN {col_name} {col_def};")
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, safe to ignore
            pass

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully for eTickette.")
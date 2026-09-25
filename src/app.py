import os
import re
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, '..', 'public')

app = Flask(__name__, static_folder=PUBLIC_DIR)

def get_db_path():
    return os.path.join(BASE_DIR, '..', 'tickets.db')

def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def ensure_columns():
    """ Automatically ensures all required columns exist in the database without losing data """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tickets);")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'resolution_feedback' not in columns:
        try:
            cursor.execute("ALTER TABLE tickets ADD COLUMN resolution_feedback TEXT DEFAULT '';")
            conn.commit()
            print("Auto-migration: Added missing 'resolution_feedback' column successfully!")
        except Exception as e:
            print("Error auto-adding column:", e)
    conn.close()

def is_valid_username(username):
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(username) > 20:
        return False, "Username cannot exceed 20 characters."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    weak_passwords = ['12345678', 'password', '123456789', 'qwertyuiop']
    if password.lower() in weak_passwords:
        return False, "Password is too common and unsafe."
    return True, ""

@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password')
    email = data.get('email', '').strip()
    q1, a1 = data.get('q1'), data.get('a1')
    q2, a2 = data.get('q2'), data.get('a2')
    q3, a3 = data.get('q3'), data.get('a3')

    if not username or not password or not email:
        return jsonify({"error": "Username, password, and email are required."}), 400

    is_valid_user, user_err = is_valid_username(username)
    if not is_valid_user:
        return jsonify({"error": user_err}), 400

    if not a1 or not a2 or not a3:
        return jsonify({"error": "All three verification answers are required."}), 400

    is_valid_pass, pass_err = is_strong_password(password)
    if not is_valid_pass:
        return jsonify({"error": pass_err}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    user_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assigned_role = 'Admin' if user_count == 0 else 'Requestor'

    try:
        cursor.execute('''
            INSERT INTO users (username, password, email, q1, a1, q2, a2, q3, a3, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, email, q1, a1.lower().strip(), q2, a2.lower().strip(), q3, a3.lower().strip(), assigned_role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"id": user_id, "message": f"User registered successfully as {assigned_role}."})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Username already exists"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if user and check_password_hash(user['password'], password):
        if user['id'] == 1 and user['role'] != 'Admin':
            cursor.execute("UPDATE users SET role = 'Admin' WHERE id = 1")
            conn.commit()
            user = cursor.execute("SELECT * FROM users WHERE id = 1").fetchone()

        conn.close()
        user_dict = dict(user)
        del user_dict['password']
        return jsonify({"user": user_dict})
        
    conn.close()
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/get-question', methods=['POST'])
def get_question():
    data = request.json
    username = data.get('username')

    conn = get_db_connection()
    user = conn.execute("SELECT q1 FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user:
        return jsonify({"q1": user['q1']})
    return jsonify({"error": "Username not found"}), 404

@app.route('/api/reset-password', methods=['PUT'])
def reset_password():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    answer = data.get('answer', '').lower().strip()
    new_password = data.get('new_password')

    if not username or not email or not answer or not new_password:
        return jsonify({"error": "All reset fields are required."}), 400

    is_valid_pass, pass_err = is_strong_password(new_password)
    if not is_valid_pass:
        return jsonify({"error": pass_err}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "Username not found."}), 404

    if user['email'] != email:
        conn.close()
        return jsonify({"error": "Registered email does not match."}), 400

    if user['a1'] != answer:
        conn.close()
        return jsonify({"error": "Verification answer is incorrect."}), 400

    hashed_password = generate_password_hash(new_password)
    conn.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Password updated successfully! You can now log in."})

@app.route('/api/users', methods=['GET'])
def get_all_users():
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role FROM users").fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route('/api/developers', methods=['GET'])
def get_developers():
    conn = get_db_connection()
    devs = conn.execute("SELECT id, username FROM users WHERE role = 'Developer'").fetchall()
    conn.close()
    return jsonify([dict(d) for d in devs])

@app.route('/api/users/role', methods=['PUT'])
def update_user_role():
    data = request.json
    target_user_id = data.get('userId')
    new_role = data.get('role')

    if new_role not in ['Admin', 'Requestor', 'Developer']:
        return jsonify({"error": "Invalid role specified."}), 400

    if target_user_id == 1 and new_role != 'Admin':
        return jsonify({"error": "Action denied: The primary System Admin (ID: 1) cannot be demoted."}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    target_user = cursor.execute("SELECT role FROM users WHERE id = ?", (target_user_id,)).fetchone()
    if not target_user:
        conn.close()
        return jsonify({"error": "User not found."}), 404

    if target_user['role'] == 'Admin' and new_role != 'Admin':
        conn.close()
        return jsonify({"error": "Action denied: Cannot demote existing Admin accounts."}), 403

    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, target_user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": f"User #{target_user_id} role updated to {new_role} successfully!"})

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tickets (title, description, requestor_id, status, notifications, resolution_feedback) VALUES (?, ?, ?, 'Open', '', '')",
                   (data['title'], data['description'], data['requestor_id']))
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return jsonify({"ticketId": ticket_id, "status": "Ticket Created"})

@app.route('/api/tickets/assign', methods=['PUT'])
def assign_ticket():
    data = request.json
    ticket_id = data.get('ticketId')
    developer_id = data.get('developerId')

    conn = get_db_connection()
    cursor = conn.cursor()

    ticket = cursor.execute("SELECT assigned_to, status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    
    if not ticket:
        conn.close()
        return jsonify({"error": "Ticket not found."}), 404

    if ticket['status'] == 'Resolved':
        conn.close()
        return jsonify({"error": "Cannot assign a resolved ticket. Reopen it first."}), 400

    notification_msg = f"Ticket #{ticket_id} has been assigned to a developer and is now In Progress."
    
    cursor.execute("""
        UPDATE tickets 
        SET assigned_to = ?, status = 'In Progress', notifications = ? 
        WHERE id = ?
    """, (developer_id, notification_msg, ticket_id))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Ticket assigned successfully and status updated to In Progress."})

@app.route('/api/tickets/submit-fix', methods=['PUT'])
def submit_fix():
    data = request.json
    ticket_id = data.get('ticketId')
    feedback = data.get('feedback', '').strip()

    if not feedback:
        return jsonify({"error": "Developer feedback/details are required to submit a fix."}), 400

    conn = get_db_connection()
    ticket = conn.execute("SELECT title FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    
    if not ticket:
        conn.close()
        return jsonify({"error": "Ticket ID not found."}), 404

    notification_msg = f"PENDING VERIFICATION: Fix submitted for ticket #{ticket_id} ('{ticket['title']}'). Please verify if the issue is resolved."
    
    conn.execute("UPDATE tickets SET status = 'Pending Verification', notifications = ?, resolution_feedback = ? WHERE id = ?",
                 (notification_msg, feedback, ticket_id))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Fix submitted for ticket #{ticket_id}. Sent to requestor for verification."})

@app.route('/api/tickets/verify', methods=['PUT'])
def verify_ticket():
    data = request.json
    ticket_id = data.get('ticketId')
    is_resolved = data.get('isResolved')

    conn = get_db_connection()
    ticket = conn.execute("SELECT title FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    
    if not ticket:
        conn.close()
        return jsonify({"error": "Ticket ID not found."}), 404

    if is_resolved:
        notification_msg = f"RESOLVED: Ticket #{ticket_id} ('{ticket['title']}') has been verified and closed by the requestor."
        conn.execute("UPDATE tickets SET status = 'Resolved', notifications = ? WHERE id = ?", (notification_msg, ticket_id))
        msg = f"Ticket #{ticket_id} successfully marked as Resolved!"
    else:
        notification_msg = f"REOPENED / ISSUE PERSISTS: Requestor rejected the fix for ticket #{ticket_id}. Pushed back to developer."
        conn.execute("UPDATE tickets SET status = 'Reopened', notifications = ? WHERE id = ?", (notification_msg, ticket_id))
        msg = f"Ticket #{ticket_id} sent back to developer for further work."

    conn.commit()
    conn.close()
    return jsonify({"message": msg})

@app.route('/api/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    data = request.json or {}
    user_id = data.get('user_id')
    role = data.get('role')

    conn = get_db_connection()
    cursor = conn.cursor()

    ticket = cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()

    if not ticket:
        conn.close()
        return jsonify({"error": "Ticket not found."}), 404

    if role == 'Admin' or (role == 'Requestor' and ticket['requestor_id'] == user_id and ticket['status'] == 'Open'):
        cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Ticket #{ticket_id} has been deleted successfully."})
    else:
        conn.close()
        return jsonify({"error": "Action denied: You do not have permission to delete this ticket."}), 403

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    conn = get_db_connection()
    tickets = conn.execute("SELECT * FROM tickets").fetchall()
    conn.close()
    return jsonify([dict(t) for t in tickets])

@app.route('/api/tickets/user/<int:user_id>', methods=['GET'])
def get_user_tickets(user_id):
    conn = get_db_connection()
    tickets = conn.execute("SELECT * FROM tickets WHERE requestor_id = ?", (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(t) for t in tickets])

@app.route('/api/tickets/assigned/<int:dev_id>', methods=['GET'])
def get_developer_tickets(dev_id):
    conn = get_db_connection()
    tickets = conn.execute("SELECT * FROM tickets WHERE assigned_to = ?", (dev_id,)).fetchall()
    conn.close()
    return jsonify([dict(t) for t in tickets])

if __name__ == '__main__':
    from database import init_db
    init_db()
    ensure_columns()  # Automatically patch the correct database file on launch
    app.run(port=3000, debug=True)
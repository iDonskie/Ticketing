import re
import sqlite3

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

if __package__:
    from .database import get_db_connection
else:
    from database import get_db_connection

auth_bp = Blueprint('auth', __name__)


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


@auth_bp.route('/api/register', methods=['POST'])
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


@auth_bp.route('/api/login', methods=['POST'])
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


@auth_bp.route('/api/get-question', methods=['POST'])
def get_question():
    data = request.json
    username = data.get('username')

    conn = get_db_connection()
    user = conn.execute("SELECT q1 FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user:
        return jsonify({"q1": user['q1']})
    return jsonify({"error": "Username not found"}), 404


@auth_bp.route('/api/reset-password', methods=['PUT'])
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


@auth_bp.route('/api/users', methods=['GET'])
def get_all_users():
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role FROM users").fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])


@auth_bp.route('/api/developers', methods=['GET'])
def get_developers():
    conn = get_db_connection()
    developers = conn.execute("SELECT id, username FROM users WHERE role = 'Developer'").fetchall()
    conn.close()
    return jsonify([dict(developer) for developer in developers])


@auth_bp.route('/api/users/role', methods=['PUT'])
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
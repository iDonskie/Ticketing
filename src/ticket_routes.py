from flask import Blueprint, jsonify, request

if __package__:
    from .database import get_db_connection
else:
    from database import get_db_connection

ticket_bp = Blueprint('tickets', __name__)


@ticket_bp.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tickets (title, description, requestor_id, status, notifications, resolution_feedback, priority) VALUES (?, ?, ?, 'Open', '', '', 'Medium')",
                   (data['title'], data['description'], data['requestor_id']))
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return jsonify({"ticketId": ticket_id, "status": "Ticket Created"})


@ticket_bp.route('/api/tickets/assign', methods=['PUT'])
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


@ticket_bp.route('/api/tickets/priority', methods=['PUT'])
def update_priority():
    data = request.json
    ticket_id = data.get('ticketId')
    priority = data.get('priority')

    if priority not in ['Low', 'Medium', 'High', 'Urgent']:
        return jsonify({"error": "Invalid priority level."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    ticket = cursor.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        conn.close()
        return jsonify({"error": "Ticket not found."}), 404

    cursor.execute("UPDATE tickets SET priority = ? WHERE id = ?", (priority, ticket_id))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Ticket #{ticket_id} priority updated to {priority}."})


@ticket_bp.route('/api/tickets/submit-fix', methods=['PUT'])
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


@ticket_bp.route('/api/tickets/verify', methods=['PUT'])
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
        message = f"Ticket #{ticket_id} successfully marked as Resolved!"
    else:
        notification_msg = f"REOPENED / ISSUE PERSISTS: Requestor rejected the fix for ticket #{ticket_id}. Pushed back to developer."
        conn.execute("UPDATE tickets SET status = 'Reopened', notifications = ? WHERE id = ?", (notification_msg, ticket_id))
        message = f"Ticket #{ticket_id} sent back to developer for further work."

    conn.commit()
    conn.close()
    return jsonify({"message": message})


@ticket_bp.route('/api/tickets/<int:ticket_id>', methods=['DELETE'])
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

    conn.close()
    return jsonify({"error": "Action denied: You do not have permission to delete this ticket."}), 403


@ticket_bp.route('/api/tickets', methods=['GET'])
def get_tickets():
    conn = get_db_connection()
    tickets = conn.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(ticket) for ticket in tickets])


@ticket_bp.route('/api/tickets/user/<int:user_id>', methods=['GET'])
def get_user_tickets(user_id):
    conn = get_db_connection()
    tickets = conn.execute("SELECT * FROM tickets WHERE requestor_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(ticket) for ticket in tickets])


@ticket_bp.route('/api/tickets/assigned/<int:dev_id>', methods=['GET'])
def get_developer_tickets(dev_id):
    conn = get_db_connection()
    tickets = conn.execute("SELECT * FROM tickets WHERE assigned_to = ? ORDER BY id DESC", (dev_id,)).fetchall()
    conn.close()
    return jsonify([dict(ticket) for ticket in tickets])
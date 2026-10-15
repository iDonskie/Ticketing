import os
from flask import Flask, send_from_directory

if __package__:
    from .auth_routes import auth_bp
    from .database import init_db
    from .ticket_routes import ticket_bp
else:
    from auth_routes import auth_bp
    from database import init_db
    from ticket_routes import ticket_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, '..', 'public')

app = Flask(__name__, static_folder=PUBLIC_DIR)
app.register_blueprint(auth_bp)
app.register_blueprint(ticket_bp)


@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')


if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
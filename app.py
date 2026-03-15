import os
from flask import Flask, jsonify
from flask_cors import CORS
from database import get_db

# Import Blueprints
from routes_admin import admin_bp
from routes_teacher import teacher_bp
from routes_student import student_bp
from routes_parent import parent_bp
from routes_auth import auth_bp
from routes_notifications import notifications_bp

app = Flask(__name__, static_folder='uploads', static_url_path='/uploads')
# Allow CORS for all domains so frontend can fetch without issues
CORS(app)

# Register Blueprints
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
app.register_blueprint(student_bp, url_prefix='/api/student')
app.register_blueprint(parent_bp, url_prefix='/api/parent')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

@app.route('/health')
def health():
    db_status = "connected" if get_db() is not None else "disconnected"
    return jsonify({"status": "ok", "message": "AstraMind Backend Running", "database": db_status})

if __name__ == '__main__':
    # Start on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)

import datetime
from flask import Blueprint, request, jsonify
from database import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    db = get_db()
    
    email = data.get('email', '')
    password = data.get('password', '')
    name = data.get('name', '')
    
    if not email.endswith('@college.com'):
        return jsonify({"status": "error", "message": "Email must end with @college.com"}), 400
        
    if db is None:
        return jsonify({"status": "error", "message": "Database not connected"}), 500
        
    # Check if exists
    if db.users.find_one({"email": email}):
        return jsonify({"status": "error", "message": "Teacher already registered."}), 400
        
    # Create user document
    user_doc = {
        "email": email,
        "password": password,  # In real world, hash this password
        "name": name,
        "role": "teacher",
        "approved": False,
        "timestamp": datetime.datetime.now()
    }
    
    db.users.insert_one(user_doc)
    return jsonify({"status": "success", "message": "Registration successful. Awaiting admin approval."})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    db = get_db()
    
    email = data.get('email', '')
    password = data.get('password', '')
    
    if db is None:
         return jsonify({"status": "success", "message": "Demo login", "user": {"email": email, "approved": True}})

    user = db.users.find_one({"email": email, "password": password})
    if not user:
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401
        
    if not user.get('approved', False):
        return jsonify({"status": "error", "message": "Account pending admin approval"}), 403
        
    return jsonify({
        "status": "success", 
        "user": {
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    })

@auth_bp.route('/pending_teachers', methods=['GET'])
def get_pending_teachers():
    db = get_db()
    if db is None:
        return jsonify([])
        
    pending = list(db.users.find({"role": "teacher", "approved": False}, {"_id": 0, "password": 0}))
    return jsonify(pending)

@auth_bp.route('/approve_teacher', methods=['POST'])
def approve_teacher():
    data = request.json
    db = get_db()
    
    email = data.get('email')
    
    if db is None:
         return jsonify({"status": "error", "message": "DB mostly disconnected"})
         
    result = db.users.update_one({"email": email}, {"$set": {"approved": True}})
    if result.modified_count > 0:
        return jsonify({"status": "success", "message": f"{email} approved successfully"})
    else:
        return jsonify({"status": "error", "message": "Teacher not found or already approved"}), 404

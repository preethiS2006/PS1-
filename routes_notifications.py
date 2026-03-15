import datetime
from flask import Blueprint, request, jsonify
from database import get_db

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/urgent', methods=['POST'])
def post_urgent_alert():
    data = request.json
    db = get_db()
    
    alert_doc = {
        "title": data.get('title'),
        "message": data.get('message'),
        "sender": data.get('sender', 'Teacher'),
        "type": "urgent",
        "timestamp": datetime.datetime.now()
    }
    
    if db is not None:
        db.notifications.insert_one(alert_doc)
        
    return jsonify({"status": "success", "message": "Urgent alert broadcasted successfully!"})

@notifications_bp.route('/all', methods=['GET'])
def get_notifications():
    db = get_db()
    if db is None:
        return jsonify([])
        
    notifs = list(db.notifications.find({}, {"_id": 0}).sort("timestamp", -1))
    return jsonify(notifs)

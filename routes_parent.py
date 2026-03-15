from flask import Blueprint, jsonify
from database import get_db

parent_bp = Blueprint('parent', __name__)

@parent_bp.route('/updates', methods=['GET'])
def get_updates():
    db = get_db()
    if db is None:
        return jsonify([
            {
                "studentName": "Demo Student",
                "culturalMessage": "Namaste 🙏. Demo Student is making steady progress! The teacher noted: 'Doing great in science'. We are proud of their dedication. Let's continue to support their journey toward excellence. 🌟",
                "timestamp": "2026-03-15T12:00:00Z"
            }
        ])
        
    updates = list(db.progress.find({}, {"_id": 0}).sort("timestamp", -1))
    return jsonify(updates)

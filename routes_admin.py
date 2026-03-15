from flask import Blueprint, jsonify
from database import get_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    db = get_db()
    if db is None:
         return jsonify({"totalUploads": 12, "hoursSaved": 5, "categories": {"Deadline": 3, "Topic": 5, "Note": 2, "Exam Announcement": 2}})

    # Fetch real stats
    total_uploads = db.materials.count_documents({})
    # Calculate hours saved (e.g., each upload saves 5 minutes => 5/60 hours)
    hours_saved = round((total_uploads * 5) / 60, 1)
    
    # Categorize
    cat_counts = {
        "Deadline": db.materials.count_documents({"category": "Deadline"}),
        "Topic": db.materials.count_documents({"category": "Topic"}),
        "Note": db.materials.count_documents({"category": "Note"}),
        "Exam Announcement": db.materials.count_documents({"category": "Exam Announcement"})
    }
    
    return jsonify({
        "totalUploads": total_uploads,
        "hoursSaved": hours_saved,
        "categories": cat_counts
    })

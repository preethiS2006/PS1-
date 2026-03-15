import os
import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from database import get_db
from agents import categorize_material, generate_cultural_progress, generate_student_ai_feedback, get_extracted_text
import threading

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/upload', methods=['POST'])
def upload_material():
    # Support both JSON and FormData for robustness
    if request.is_json:
        data = request.json
        title = data.get('title', '')
        description = data.get('description', '')
        filename = data.get('fileName', '')
        content_type = data.get('content_type', 'text')
    else:
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        file = request.files.get('file')
        
        if not file or file.filename == '':
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
            
        filename = secure_filename(file.filename)
        content_type = filename.split('.')[-1] if '.' in filename else 'text'
        
        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
    
    # Create the URL for the frontend to access the static file later
    file_url = f"http://localhost:5000/uploads/{filename}"

    db = get_db()
    
    # Run through the categorization agent
    agent_result = categorize_material(title, description, content_type)
    
    # Extract actual content immediately for RAG and search
    content_text = get_extracted_text(filename, title, description, content_type)
    
    material_doc = {
        "title": title,
        "description": description,
        "content_type": content_type,
        "fileName": filename,
        "fileUrl": file_url,
        "content_text": content_text, # Store extracted text!
        "category": agent_result.get('category', 'Note'),
        "tags": agent_result.get('tags', []),
        "ai_feedback": None,  # Will be filled by background thread
        "timestamp": datetime.datetime.now()
    }
    
    material_id = None
    if db is not None:
        result = db.materials.insert_one(material_doc)
        material_id = str(result.inserted_id)

    # Generate AI feedback in background so upload response is immediate
    def generate_feedback_bg():
        try:
            print(f"--- Starting Background AI Feedback for: {title} ---")
            feedback = generate_student_ai_feedback(title, description, content_type, filename)
            
            # Re-fetch DB inside the thread to be safe
            thread_db = get_db()
            if thread_db is not None and material_id:
                from bson import ObjectId
                res = thread_db.materials.update_one(
                    {"_id": ObjectId(material_id)},
                    {"$set": {"ai_feedback": feedback}}
                )
                print(f"--- AI feedback generated and saved! Update Success: {res.modified_count > 0} ---")
            else:
                print("--- AI feedback failed: Database connection not available in thread ---")
        except Exception as e:
            print(f"--- Background AI feedback error: {e} ---")

    thread = threading.Thread(target=generate_feedback_bg, daemon=True)
    thread.start()
        
    return jsonify({
        "status": "success",
        "category": material_doc["category"],
        "message": "Material routed automatically"
    })

@teacher_bp.route('/progress', methods=['POST'])
def send_progress():
    data = request.json
    db = get_db()
    
    student_name = data.get('studentName')
    subject = data.get('subject')
    grade = data.get('grade')
    behavior = data.get('behavior')
    raw_progress = data.get('rawProgress')
    
    # Run through cultural translation agent
    cultural_msg = generate_cultural_progress(raw_progress, student_name, subject, grade, behavior)
    
    progress_doc = {
        "studentName": student_name,
        "subject": subject,
        "grade": grade,
        "behavior": behavior,
        "rawProgress": raw_progress,
        "culturalMessage": cultural_msg,
        "timestamp": datetime.datetime.now()
    }
    
    if db is not None:
        db.progress.insert_one(progress_doc)
        
    return jsonify({
        "status": "success",
        "message": "Cultural echo delivered"
    })

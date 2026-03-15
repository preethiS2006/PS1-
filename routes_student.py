from flask import Blueprint, jsonify, request
from database import get_db
from agents import generate_rag_summary, extract_individual_material_insight

student_bp = Blueprint('student', __name__)

@student_bp.route('/materials', methods=['GET'])
def get_materials():
    db = get_db()
    if db is None:
        return jsonify([
            {
                "title": "Welcome to AstraMind Demo",
                "description": "This is a placeholder since MongoDB isn't connected.",
                "content_type": "PDF",
                "category": "Topic"
            }
        ])
        
    materials = list(db.materials.find().sort("timestamp", -1))
    # Stringify ObjectId for JSON compatibility
    for m in materials:
        m['_id'] = str(m['_id'])
    
    return jsonify(materials)

@student_bp.route('/generate_feedback', methods=['POST'])
def generate_feedback_on_demand():
    data = request.json
    db = get_db()
    if not db or not data.get('material_id'):
        return jsonify({"error": "Invalid request"}), 400
    
    from bson import ObjectId
    from agents import generate_student_ai_feedback
    
    m = db.materials.find_one({"_id": ObjectId(data['material_id'])})
    if not m:
        return jsonify({"error": "Material not found"}), 404
        
    feedback = generate_student_ai_feedback(
        m.get('title'),
        m.get('description'),
        m.get('content_type'),
        m.get('fileName')
    )
    
    db.materials.update_one({"_id": m["_id"]}, {"$set": {"ai_feedback": feedback}})
    return jsonify({"feedback": feedback})

@student_bp.route('/extract_rag', methods=['POST'])
def extract_rag():
    db = get_db()
    if db is None:
        return jsonify({
            "summary": "✨ Insightful Summary: Database not connected. RAG Simulation running on empty data. Knowledge is wealth. ✨"
        })
        
    materials = list(db.materials.find({}, {"_id": 0}))
    
    # Combine texts to simulate RAG context - now using RICH EXTRACTED content
    texts = []
    for m in materials:
        if m.get('content_text'):
            texts.append(f"Title: {m.get('title')}\nContent: {m.get('content_text')[:2000]}")
        else:
            texts.append(f"Title: {m.get('title')}\nDescription: {m.get('description')}")
            
    combined_text = "\n---\n".join(texts)
    
    if not combined_text:
        return jsonify({"summary": "No materials available to extract insights from."})
        
    summary = generate_rag_summary(combined_text)
    
    return jsonify({"summary": summary})

@student_bp.route('/extract_single', methods=['POST'])
def extract_single():
    data = request.json
    db = get_db()
    
    if not data or 'title' not in data:
        return jsonify({"summary": "Invalid direct extraction request."}), 400
    
    language = data.get('language', 'English')
        
    summary = extract_individual_material_insight(
        data.get('title'),
        data.get('description'),
        data.get('content_type', 'file'),
        data.get('fileName'),
        language=language
    )
    
    return jsonify({"summary": summary})

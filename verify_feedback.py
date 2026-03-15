from database import get_db
db = get_db()
mats = list(db.materials.find())
print("--- AI Feedback Verification ---")
for m in mats:
    title = m.get('title', 'Unknown')
    feedback = m.get('ai_feedback', '')
    content_type = m.get('content_type', 'unknown')
    file_name = m.get('fileName', 'None')
    has_feedback = bool(feedback and not feedback.startswith('📚 **About this material:**'))
    print(f"Title: {title} | Type: {content_type} | File: {file_name}")
    print(f"Has Real Feedback: {has_feedback}")
    if feedback:
        print(f"Feedback Snippet: {feedback[:100]}...")
    else:
        print("Feedback: MISSING")
    print("-" * 50)

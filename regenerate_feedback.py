import os
import sys
import logging
from dotenv import load_dotenv

# Setup paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

from database import get_db
from agents import generate_student_ai_feedback

load_dotenv()

def regenerate_all_feedback():
    print("🚀 Starting Feedback Regeneration with Groq...")
    db = get_db()
    if db is None:
        print("❌ Could not connect to database.")
        return

    # Find all materials
    mats = list(db.materials.find())
    total = len(mats)
    print(f"📊 Found {total} materials to process.")

    for i, m in enumerate(mats):
        title = m.get('title', 'Untitled')
        print(f"[{i+1}/{total}] Processing: {title}...")
        
        try:
            # Force regeneration by calling the agent
            feedback = generate_student_ai_feedback(
                title,
                m.get('description', ''),
                m.get('content_type', 'pdf'),
                m.get('fileName')
            )
            
            # Simple check to see if it's the fallback
            if "About this material:" in feedback and "REVIEW_THIS_MATERIAL" in feedback: # Check for unique hallmarks if possible
                 # But our fallback is quite specific. Let's just update regardless if it's new.
                 pass

            db.materials.update_one(
                {"_id": m["_id"]},
                {"$set": {"ai_feedback": feedback}}
            )
            print(f"✅ Updated {title}")
        except Exception as e:
            print(f"❌ Error updating {title}: {e}")

    print("✨ Feedback regeneration complete!")

if __name__ == "__main__":
    regenerate_all_feedback()

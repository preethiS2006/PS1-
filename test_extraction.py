
from agents import extract_individual_material_insight, generate_student_ai_feedback
import os

def test_file(file_name, content_type):
    print(f"\n--- Testing Extraction for: {file_name} ({content_type}) ---")
    summary = extract_individual_material_insight(
        title="Test Title",
        description="Test Description",
        content_type=content_type,
        file_name=file_name,
        language="English"
    )
    print("SUMMARY RESULT:")
    print(summary)
    
    print(f"\n--- Testing Feedback for: {file_name} ---")
    feedback = generate_student_ai_feedback(
        title="Test Title",
        description="Test Description",
        content_type=content_type,
        file_name=file_name
    )
    print("FEEDBACK RESULT:")
    print(feedback)

if __name__ == "__main__":
    # Test with a PDF that exists
    test_file("Essay_questions.pdf", "pdf")
    # Test with a TXT that exists
    test_file("test.txt", "txt")

import os
import json
import requests
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client if key exists, otherwise fallback
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
    else:
        client = None
except Exception as e:
    print(f"Failed to initialize Groq: {e}")
    client = None

# Local Hugging Face Model initialization
hf_audio_pipe = None

def get_audio_pipeline():
    global hf_audio_pipe
    if hf_audio_pipe is None:
        from transformers import pipeline
        # chunk_length_s is REQUIRED for processing videos longer than 30s so memory doesn't crash!
        hf_audio_pipe = pipeline('automatic-speech-recognition', model='openai/whisper-tiny.en', chunk_length_s=30)
    return hf_audio_pipe

def extract_audio_offline(file_path):
    text = ""
    # 1. First attempt: Hugging Face Local Model as requested
    try:
        import soundfile as sf
        audio_data, sr = sf.read(file_path)
        
        # If stereo, take only one channel
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]
            
        pipe = get_audio_pipeline()
        res = pipe({'raw': audio_data, 'sampling_rate': sr})
        if res and 'text' in res:
            text = res['text']
            return text
    except Exception as e:
        print(f"HF Local Audio Error (falling back): {e}")

    # 2. Second attempt: Bulletproof Free Google API (SpeechRecognition) if HF fails or runs out of memory
    if not text:
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(file_path) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
                return text
        except Exception as e:
            print(f"SpeechRecognition Native Error: {e}")
            
    return ""

def get_extracted_text(file_name, title, description, content_type):
    """
    Core extraction logic shared between feedback and insights.
    """
    real_text = ""
    file_path = os.path.join(os.path.dirname(__file__), 'uploads', file_name)
    if not os.path.exists(file_path):
        print(f"File not found for extraction: {file_path}")
        return ""
        
    try:
        ext = file_name.lower().split('.')[-1]
        
        # PDF EXTRACTION
        if ext == 'pdf':
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for i in range(min(10, len(reader.pages))):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        real_text += page_text + "\n"
                        
        # TEXT EXTRACTION
        elif ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                real_text = f.read(10000)
                
        # IMAGE EXTRACTION
        elif ext in ['jpg', 'jpeg', 'png', 'webp']:
            real_text = extract_image_text_local(file_path)
        
        # AUDIO EXTRACTION
        elif ext in ['mp3', 'wav', 'ogg', 'm4a', 'flac']:
            real_text = extract_audio_offline(file_path)

        # VIDEO EXTRACTION
        elif ext in ['mp4', 'avi', 'mov', 'mpeg', 'webm', 'mkv']:
            import imageio_ffmpeg
            import subprocess
            audio_path = file_path + "_temp.wav"
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            subprocess.run([exe, "-i", file_path, "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", audio_path, "-y"], capture_output=True, check=False)
            
            if os.path.exists(audio_path):
                real_text = extract_audio_offline(audio_path)
                os.remove(audio_path)
    except Exception as e:
        print(f"Extraction error for {file_name}: {e}")
        
    return real_text.strip()

# Local OCR Model initialization
easyocr_reader = None

def get_ocr_reader():
    global easyocr_reader
    if easyocr_reader is None:
        import easyocr
        # Initialize reader (downloads small language models if not present)
        easyocr_reader = easyocr.Reader(['en'])
    return easyocr_reader

def extract_image_text_local(file_path):
    try:
        reader = get_ocr_reader()
        result = reader.readtext(file_path, detail=0)
        extracted_text = " ".join(result)
        return extracted_text
    except Exception as e:
        print(f"Local OCR Error: {e}")
        return ""

def categorize_material(title, description, content_type):
    """
    Categorizes the material into Deadline, Topic, Note, or Exam Announcement.
    Also extracts a short culturally adapted title.
    """
    if client:
        try:
            prompt = f"Categorize this educational material. Title: {title}. Description: {description}. Type: {content_type}. Return JSON with 'category' (Options: Deadline, Topic, Note, Exam Announcement) and 'tags' (list of strings)."
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            print(f"Categorization error: {e}")
            
    # Fallback to simple matching if no LLM
    category = "Note"
    if "exam" in title.lower() or "exam" in description.lower():
        category = "Exam Announcement"
    elif "deadline" in title.lower() or "due" in title.lower():
        category = "Deadline"
    
    return {"category": category, "tags": [category.lower(), content_type]}


def generate_rag_summary(materials_text):
    """
    Simulates extracting knowledge and summarizing using RAG approach
    """
    if client:
        try:
            prompt = f"Summarize the following class materials providing beautiful insights with a cultural Indian echo:\n\n{materials_text}"
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"RAG error: {e}")
            
    # Fallback summary
    return f"✨ Insightful Summary: The class materials cover key topics. Make sure to review the core concepts closely. As the ancient saying goes, 'Knowledge is the true wealth that grows when shared.' ✨\n\n(Extracted from {len(materials_text.split())} words)"

def generate_student_ai_feedback(title, description, content_type, file_name=None):
    """
    Analyzes the uploaded material (video, audio, pdf, image) deeply and generates
    personalized, encouraging AI feedback for students. Triggered automatically when
    a teacher uploads a new material.
    """
    # Step 1: Extract actual content from the file
    real_text = ""
    if file_name:
        file_path = os.path.join(os.path.dirname(__file__), 'uploads', file_name)
        if os.path.exists(file_path):
            try:
                ext = file_name.lower().split('.')[-1]
                if ext == 'pdf':
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for i in range(min(5, len(reader.pages))):
                            page_text = reader.pages[i].extract_text()
                            if page_text:
                                real_text += page_text + "\n"
                elif ext in ['jpg', 'jpeg', 'png', 'webp']:
                    real_text = extract_image_text_local(file_path)
                elif ext in ['mp3', 'wav', 'ogg', 'm4a', 'flac']:
                    real_text = extract_audio_offline(file_path)
                elif ext in ['mp4', 'avi', 'mov', 'mpeg', 'webm', 'mkv']:
                    import imageio_ffmpeg
                    import subprocess
                    audio_path = file_path + "_feedback.wav"
                    exe = imageio_ffmpeg.get_ffmpeg_exe()
                    subprocess.run([exe, "-i", file_path, "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", audio_path, "-y"], capture_output=True, check=False)
                    if os.path.exists(audio_path):
                        real_text = extract_audio_offline(audio_path)
                        os.remove(audio_path)
                elif ext == 'txt':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        real_text = f.read(5000)
            except Exception as e:
                print(f"AI Feedback extraction error: {e}")

    analysis_text = str(real_text)[:4000]  # Limit context

    # Step 2: Groq generates deep student feedback
    if client:
        try:
            content_context = f"Content extracted:\n{real_text}" if real_text else f"Title: {title}\nDescription: {description}\nType: {content_type}"
            prompt = f"""You are a warm, encouraging AI study coach for college students in India.

A teacher just uploaded a new {content_type} material titled "{title}".
{content_context}

Generate personalized AI feedback for students viewing this material. Include:
1. 📚 **What this material is about** (2-3 sentences)
2. 🎯 **Key learning objectives** (2-3 bullet points)
3. 💡 **Study tips** for this material (2-3 bullet points)
4. ⚠️ **Important points to focus on** (1-2 bullet points)
5. 🌟 **Motivational message** (1 sentence)

Be specific to the actual content, warm, and encouraging. Use emojis."""
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"AI Feedback generation error: {e}")

    # Fallback feedback when Groq is unavailable
    return f"""📚 **About this material:** This {content_type} covers key academic content on {title}. Review it carefully to understand the core concepts.

🎯 **Learning Objectives:**
• Understand the main topics covered in this material
• Take notes on key definitions and concepts
• Connect this content to previous knowledge

💡 **Study Tips:**
• Review this material at least twice
• Summarize key points in your own words
• Discuss with classmates for better understanding

⚠️ **Focus on:** The core concepts introduced in this {content_type} will likely appear in upcoming assessments.

🌟 Knowledge is power — you've got this! 🚀"""

def extract_individual_material_insight(title, description, content_type, file_name=None, language='English'):
    """
    Generates a targeted, specific summary for an individual file (audio, video, pdf, image).
    Actually extracts multimodal text using PyPDF2, MoviePy, and Hugging Face Inference APIs.
    """
    if file_name:
        real_text_extracted = get_extracted_text(file_name, title, description, content_type)
        if not real_text_extracted:
            print(f"Extraction returned no content for {file_name}")
            real_text_extracted = f"Title: {title}\nDescription: {description}"
                
    # Map user-friendly language names to Google Translate language codes
    LANG_CODES = {
        'English': 'en',
        'Tamil': 'ta',
        'Hindi': 'hi',
        'French': 'fr'
    }
    lang_code = LANG_CODES.get(language, 'en')

    # Step 1: Google Translate the extracted raw text
    translated_text = real_text_extracted
    if real_text_extracted and lang_code != 'en':
        try:
            from deep_translator import GoogleTranslator
            # Google Translate has a 5000 char limit per call — chunk it
            chunk_size = 4500
            chunks = [real_text_extracted[i:i+chunk_size] for i in range(0, min(len(real_text_extracted), 9000), chunk_size)]
            translated_chunks = []
            for chunk in chunks:
                result = GoogleTranslator(source='auto', target=lang_code).translate(chunk)
                if result:
                    translated_chunks.append(result)
            if translated_chunks:
                translated_text = "\n".join(translated_chunks)
                print(f"Google Translated to {language} successfully.")
        except Exception as e:
            print(f"Google Translate error: {e}")
            translated_text = real_text_extracted  # fallback to English

    # Step 2: Groq generates a summary of the (already translated) text in target language
    summary = ""
    if client and translated_text:
        try:
            prompt = f"""You are a study assistant. Summarize the following content from a {content_type}:
1. A brief summary paragraph
2. 3-5 key bullet points

Write your response entirely in {language}.

Content:
{translated_text[:4000]}"""
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500
            )
            summary = completion.choices[0].message.content
        except Exception as e:
            print(f"Summary error: {e}")

    if real_text_extracted:
        if summary:
            return f"🌐 {language} Summary:\n\n{summary}\n\n---\n📄 Translated Content ({language}):\n{translated_text[:3000]}{'...' if len(translated_text) > 3000 else ''}"
        elif translated_text != real_text_extracted:
            # Translation succeeded but no Groq summary
            return f"🌐 Translated Content ({language}):\n{translated_text}"
        else:
            return f"📄 Extracted Text:\n{real_text_extracted}"

    return f"🔍 Simulated {content_type.upper()} Extraction:\n- Found metadata for {title}."


def generate_cultural_progress(raw_progress, student_name, subject, grade, behavior):
    """
    Takes teacher's structured input and creates an emotional culturally adapted message for the parent.
    Formats it cleanly into distinct bullet points.
    """
    if client:
        try:
            prompt = f"""
            You are an Indian teacher sending a WhatsApp-style progress report to a parent. 
            Format the following structured data into a warm, emotionally supportive, but strictly professional report using bullet points and appropriate emojis. 
            Do NOT include conversational filler at the start, just the formatted report.

            Data:
            - Student: {student_name}
            - Subject: {subject}
            - Current Score/Grade: {grade}
            - Behavior: {behavior}
            - Teacher's Additional Comments: {raw_progress}
            """
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Progress generation error: {e}")
            
    # Fallback
    return f"Namaste 🙏\n\nHere is {student_name}'s Progress Update:\n\n📚 Subject: {subject}\n📝 Grade: {grade}\n🌟 Behavior: {behavior}\n\nTeacher Comments: '{raw_progress}'.\n\nWe are proud of their dedication. Let's continue to support their journey toward excellence. ✨"

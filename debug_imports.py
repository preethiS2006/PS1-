
try:
    import PyPDF2
    print("PyPDF2 imported successfully")
except ImportError:
    print("PyPDF2 NOT found")

try:
    import easyocr
    print("easyocr imported successfully")
except ImportError:
    print("easyocr NOT found")

try:
    import soundfile
    print("soundfile imported successfully")
except ImportError:
    print("soundfile NOT found")

try:
    import speech_recognition
    print("speech_recognition imported successfully")
except ImportError:
    print("speech_recognition NOT found")

try:
    import transformers
    print("transformers imported successfully")
except ImportError:
    print("transformers NOT found")

try:
    import imageio_ffmpeg
    print("imageio_ffmpeg imported successfully")
except ImportError:
    print("imageio_ffmpeg NOT found")

try:
    from deep_translator import GoogleTranslator
    print("deep_translator imported successfully")
except ImportError:
    print("deep_translator NOT found")

try:
    from groq import Groq
    print("groq imported successfully")
except ImportError:
    print("groq NOT found")

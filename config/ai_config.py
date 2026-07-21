import os
from google import genai

# Pull the API key from your secure .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("⚠️ GEMINI_API_KEY is missing. Please check your .env file!")

# Initialize the global Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Pull the specific model name from your .env file (defaulting to flash if not found)
model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

print(f"✅ Gemini AI Initialized successfully using model: {model_name}")
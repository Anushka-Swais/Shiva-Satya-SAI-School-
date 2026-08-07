import os
from google import genai

# Pull the API key from your secure .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("⚠️ GEMINI_API_KEY is missing. Please check your .env file!")

# Initialize the global Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Fixing the model directly to gemini-3.5-flash for the entire backend
model_name = "gemini-3.5-flash"

print(f"✅ Gemini AI Initialized successfully using model: {model_name}")
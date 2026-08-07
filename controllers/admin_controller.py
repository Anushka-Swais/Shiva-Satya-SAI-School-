import os
import base64
from google.cloud import texttospeech
from google.cloud import speech
from google.api_core.client_options import ClientOptions

# Centralized AI config
from config.ai_config import client, model_name

# --- NEW TRACKING IMPORTS ---
from config.database import SessionLocal
from utils.ai_tracker import log_gemini_usage

class AdminAIController:
    def __init__(self):
        # 3. Voice to Text and Text to Voice Initialization
        gcp_key = os.getenv("GOOGLE_TTS_API_KEY")
        if not gcp_key:
             raise ValueError("GOOGLE_TTS_API_KEY is missing from environment variables.")
             
        client_options = ClientOptions(api_key=gcp_key)
        self.tts_client = texttospeech.TextToSpeechClient(client_options=client_options)
        self.stt_client = speech.SpeechClient(client_options=client_options)

        # Fully upgraded language mapping for premium Standard & Neural2 Google TTS voices
        # Fixed regional voices from Wavenet to Standard (Wavenet voices are not supported for these language codes)
        self.advanced_language_map = {
            "english": {"code": "en-IN", "voice": "en-IN-Neural2-B"},
            "hindi": {"code": "hi-IN", "voice": "hi-IN-Neural2-A"},
            "telugu": {"code": "te-IN", "voice": "te-IN-Standard-A"},
            "kannada": {"code": "kn-IN", "voice": "kn-IN-Standard-A"},
            "tamil": {"code": "ta-IN", "voice": "ta-IN-Standard-A"},
            "malayalam": {"code": "ml-IN", "voice": "ml-IN-Standard-A"},
            "bengali": {"code": "bn-IN", "voice": "bn-IN-Standard-A"},
            "marathi": {"code": "mr-IN", "voice": "mr-IN-Standard-A"},
            "oriya": {"code": "or-IN", "voice": "or-IN-Standard-A"},
            "gujarati": {"code": "gu-IN", "voice": "gu-IN-Standard-A"},
            "gujrati": {"code": "gu-IN", "voice": "gu-IN-Standard-A"}
        }

    def _get_voice_config(self, language_name: str) -> dict:
        lang_lower = language_name.lower().strip()
        # Defaults to Indian English Neural2 if language is not found
        return self.advanced_language_map.get(lang_lower, {"code": "en-IN", "voice": "en-IN-Neural2-A"})

    # --- 1. Language script translator (OPTIMIZED FOR HIGH SPEED) ---
    def translate_text(self, text: str, target_language: str, user_email: str, client_name: str) -> str:
        # SUPER COMPRESSED PROMPT: Fewer words for the AI to read = much faster response time.
        prompt = f"Translate to {target_language} (use native script only). Return ONLY the translation. Text: {text}"
        
        # 🚀 ZERO TEMPERATURE FIX: Forces Gemini to translate instantly without "thinking"
        response = client.models.generate_content(
            model=model_name, 
            contents=prompt,
            config={"temperature": 0.0}
        )
        
        # --- TRACKING LOGIC ---
        db = SessionLocal()
        try:
            log_gemini_usage(
                db=db,
                response=response,
                client_name=client_name,
                user_email=user_email,
                module_name="Admin Dashboard",
                feature_name="Fast Text Translation"
            )
        finally:
            db.close()
        # ----------------------

        return response.text.strip()

    # --- 3. Text to Voice (With Premium Accents & Clarity Fix) ---
    def generate_speech(self, text: str, language: str = "English") -> str:
        voice_config = self._get_voice_config(language)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_config["code"], 
            name=voice_config["voice"]
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.75,       
            sample_rate_hertz=24000   
        )
        
        response = self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        return base64.b64encode(response.audio_content).decode("utf-8")

    # --- 3. Voice to Text (UPDATED TO WEBM_OPUS) ---
    def process_audio_to_text(self, audio_bytes: bytes, language: str = "English") -> str:
        voice_config = self._get_voice_config(language)
        audio = speech.RecognitionAudio(content=audio_bytes)
        
        # Updated to WEBM_OPUS so it automatically handles the frontend WebM headers
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            language_code=voice_config["code"],
        )
        response = self.stt_client.recognize(config=config, audio=audio)
        
        # Safety check if Google returns an empty result
        if not response.results:
            return ""
            
        return " ".join([result.alternatives[0].transcript for result in response.results])

    # --- 2. Audio language translator ---
    def audio_language_translator(self, audio_bytes: bytes, source_language: str, target_language: str, user_email: str, client_name: str) -> dict:
        original_text = self.process_audio_to_text(audio_bytes, source_language)
        
        # If the audio couldn't be processed or is empty
        if not original_text.strip():
            return {"original_text": "", "translated_text": "Please provide valid audio to translate.", "audio_base64": ""}
            
        # Pass the credentials down to translate_text where Gemini is called!
        translated_text = self.translate_text(original_text, target_language, user_email, client_name)
        translated_audio_base64 = self.generate_speech(translated_text, target_language)
        
        return {
            "original_text": original_text,
            "translated_text": translated_text,
            "audio_base64": translated_audio_base64
        }
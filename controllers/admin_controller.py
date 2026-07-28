import os
import base64
from google.cloud import texttospeech
from google.cloud import speech
from google.api_core.client_options import ClientOptions

# Centralized AI config
from config.ai_config import client, model_name

class AdminAIController:
    def __init__(self):
        # 3. Voice to Text and Text to Voice Initialization
        gcp_key = os.getenv("GOOGLE_TTS_API_KEY")
        if not gcp_key:
             raise ValueError("GOOGLE_TTS_API_KEY is missing from environment variables.")
             
        client_options = ClientOptions(api_key=gcp_key)
        self.tts_client = texttospeech.TextToSpeechClient(client_options=client_options)
        self.stt_client = speech.SpeechClient(client_options=client_options)

        # Upgraded language mapping for native scripts and premium Google TTS voices
        # Fully upgraded language mapping for premium Wavenet & Neural2 Google TTS voices
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

    # --- 1. Language script translator ---
    def translate_text(self, text: str, target_language: str) -> str:
        # Strictly enforce native script output to prevent defaulting to English
        prompt = f"You are an expert linguistic translator. Translate the following text natively into {target_language}. You MUST output the text in the native script/characters of {target_language}. Provide only the precise translation without any markdown formatting or conversational filler:\n\n{text}"
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.strip()

    # --- 3. Text to Voice (With Premium Accents & Clarity Fix) ---
    def generate_speech(self, text: str, language: str = "English") -> str:
        voice_config = self._get_voice_config(language)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Enforce the specific regional voice model (e.g., Wavenet or Neural2)
        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_config["code"], 
            name=voice_config["voice"]
        )
        
        # Upgraded Audio Config for maximum clarity
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.75,       # Slows down the voice slightly for better articulation
            sample_rate_hertz=24000   # Forces high-definition audio quality
        )
        
        response = self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        return base64.b64encode(response.audio_content).decode("utf-8")

    # --- 3. Voice to Text ---
    def process_audio_to_text(self, audio_bytes: bytes, language: str = "English") -> str:
        voice_config = self._get_voice_config(language)
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code=voice_config["code"],
        )
        response = self.stt_client.recognize(config=config, audio=audio)
        return " ".join([result.alternatives[0].transcript for result in response.results])

    # --- 2. Audio language translator ---
    def audio_language_translator(self, audio_bytes: bytes, source_language: str, target_language: str) -> dict:
        # Step A: Convert source audio to text
        original_text = self.process_audio_to_text(audio_bytes, source_language)
        # Step B: Translate the text
        translated_text = self.translate_text(original_text, target_language)
        # Step C: Convert translated text back to audio
        translated_audio_base64 = self.generate_speech(translated_text, target_language)
        
        return {
            "original_text": original_text,
            "translated_text": translated_text,
            "audio_base64": translated_audio_base64
        }
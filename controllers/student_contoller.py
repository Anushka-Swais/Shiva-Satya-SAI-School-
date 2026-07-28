import os
import base64
import json
from google.cloud import texttospeech
from google.cloud import speech
from google.api_core.client_options import ClientOptions

# Centralized AI config
from config.ai_config import client, model_name

class StudentAIController:
    def __init__(self):
        # 6. Voice to Text and Text to Voice Initialization
        gcp_key = os.getenv("GOOGLE_TTS_API_KEY")
        if not gcp_key:
             raise ValueError("GOOGLE_TTS_API_KEY is missing from environment variables.")
             
        client_options = ClientOptions(api_key=gcp_key)
        self.tts_client = texttospeech.TextToSpeechClient(client_options=client_options)
        self.stt_client = speech.SpeechClient(client_options=client_options)

        # Upgraded language mapping for native scripts and premium Google TTS voices
        # Fully upgraded language mapping for premium Wavenet & Neural2 Google TTS voices
        self.advanced_language_map = {
            "english": {"code": "en-IN", "voice": "en-IN-Neural2-A"},
            "hindi": {"code": "hi-IN", "voice": "hi-IN-Neural2-A"},
            "telugu": {"code": "te-IN", "voice": "te-IN-Wavenet-A"},
            "kannada": {"code": "kn-IN", "voice": "kn-IN-Wavenet-A"},
            "tamil": {"code": "ta-IN", "voice": "ta-IN-Wavenet-A"},
            "gujrati": {"code": "gu-IN", "voice": "gu-IN-Wavenet-A"}, 
            "gujarati": {"code": "gu-IN", "voice": "gu-IN-Wavenet-A"},
            "marathi": {"code": "mr-IN", "voice": "mr-IN-Wavenet-A"}
        }

    def _get_voice_config(self, language_name: str) -> dict:
        lang_lower = language_name.lower().strip()
        # Defaults to Indian English Neural2 if language is not found
        return self.advanced_language_map.get(lang_lower, {"code": "en-IN", "voice": "en-IN-Neural2-A"})

    # --- 4. Language script translator ---
    def translate_text(self, text: str, target_language: str) -> str:
        # Strictly enforce native script output to prevent defaulting to English
        prompt = f"You are an expert linguistic translator. Translate the following text natively into {target_language}. You MUST output the text in the native script/characters of {target_language}. Provide only the precise translation without any markdown formatting or conversational filler:\n\n{text}"
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.strip()

    # --- 6. Text to Voice (With Premium Accents) ---
    def generate_speech(self, text: str, language: str = "English") -> str:
        voice_config = self._get_voice_config(language)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Enforce the specific regional voice model (e.g., Wavenet or Neural2)
        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_config["code"], 
            name=voice_config["voice"]
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        return base64.b64encode(response.audio_content).decode("utf-8")

    # --- 6. Voice to Text ---
    def process_audio_to_text(self, audio_bytes: bytes, language: str = "English") -> str:
        voice_config = self._get_voice_config(language)
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code=voice_config["code"],
        )
        response = self.stt_client.recognize(config=config, audio=audio)
        return " ".join([result.alternatives[0].transcript for result in response.results])

    # --- 5. Audio language translator ---
    def audio_language_translator(self, audio_bytes: bytes, source_language: str, target_language: str) -> dict:
        original_text = self.process_audio_to_text(audio_bytes, source_language)
        translated_text = self.translate_text(original_text, target_language)
        translated_audio_base64 = self.generate_speech(translated_text, target_language)
        return {
            "original_text": original_text, 
            "translated_text": translated_text, 
            "audio_base64": translated_audio_base64
        }

    # --- 1. Automatic content generation based on learning capacity ---
    def generate_content(self, topic: str, learning_capacity: str) -> str:
        prompt = f"""
        Act as an encouraging, expert tutor. Generate educational content on the topic: '{topic}'.
        The content must be tailored for a student with a '{learning_capacity}' learning capacity.
        Make it engaging, easy to understand, and structured with bullet points or short paragraphs.
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.strip()

    # --- 2. Automatic quiz generation (Part A) ---
    def generate_quiz(self, topic: str, difficulty: str, num_questions: int) -> str:
        prompt = f"""
        Generate a multiple-choice mock test with {num_questions} questions on '{topic}' at a '{difficulty}' level.
        Return ONLY valid JSON format. Do not use markdown blocks.
        Schema: [{{"question": "...", "options": ["A", "B", "C", "D"], "correct_answer": "..."}}]
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.replace("```json", "").replace("```", "").strip()

    # --- 2. Auto correction (Part B) ---
    def evaluate_quiz(self, student_submission_data: dict) -> str:
        prompt = f"""
        Act as an encouraging tutor. Evaluate this student quiz submission and provide auto-correction feedback.
        Return ONLY valid JSON format. Do not use markdown blocks.
        Schema: {{ "total_score": "X/Y", "corrections": [ {{"question": "...", "student_answer": "...", "correct_answer": "...", "explanation": "..."}} ] }}
        
        Submission Data: {student_submission_data}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.replace("```json", "").replace("```", "").strip()

    # --- 3. Self Assessment with graphical representation ---
    def assess_self_performance(self, performance_data: dict) -> str:
        prompt = f"""
        Analyze this student's performance data. You must return a strict JSON object that the frontend can use for graphical charts.
        Do not use markdown blocks.
        Schema:
        {{
            "textual_report": "A supportive self-assessment directed at the student. Point out strengths and 3 actionable study tips.",
            "chart_data_per_subject": [ {{"subject": "Math", "score": 85, "average": 70}} ],
            "overall_summary_metrics": {{ "overall_growth_percentage": 5, "top_subject": "Math", "focus_subject": "Science" }}
        }}
        
        Performance Data: {performance_data}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.replace("```json", "").replace("```", "").strip()

    # --- 7. Assignment due date alerts ---
    def generate_assignment_alert(self, assignment_name: str, due_date: str) -> str:
        prompt = f"""
        Write a brief, friendly, and motivating alert message for a student reminding them that 
        their assignment '{assignment_name}' is due on {due_date}. Keep it under 3 sentences.
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.strip()
import os
import base64
import json
from google.cloud import texttospeech
from google.cloud import speech
from google.api_core.client_options import ClientOptions

from config.ai_config import client, model_name
from config.database import SessionLocal
from utils.ai_tracker import log_gemini_usage

class FacultyAIController:
    def __init__(self):
        # 1. Voice to Text and Text to Voice Initialization
        gcp_key = os.getenv("GOOGLE_TTS_API_KEY")
        if not gcp_key:
             raise ValueError("GOOGLE_TTS_API_KEY is missing from environment variables.")
             
        client_options = ClientOptions(api_key=gcp_key)
        self.tts_client = texttospeech.TextToSpeechClient(client_options=client_options)
        self.stt_client = speech.SpeechClient(client_options=client_options)

        # 2. Premium Language mapping for Standard & Neural2 Google TTS voices
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

    # --- REAL: Language script translator (OPTIMIZED FOR HIGH SPEED) ---
    def translate_text(self, text: str, target_language: str, user_email: str, client_name: str) -> str:
        # SUPER COMPRESSED PROMPT: Fewer words for the AI to read = much faster response time.
        prompt = f"Translate to {target_language} (use native script only). Return ONLY the translation. Text: {text}"
        
        # Uses the dynamic model_name from config.ai_config
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        # --- TRACKING ---
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", "Translate Text")
        finally:
            db.close()
            
        return response.text.strip()

    # --- REAL: Text to Voice ---
    def generate_speech(self, text: str, language: str = "English") -> str:
        voice_config = self._get_voice_config(language)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(language_code=voice_config["code"], name=voice_config["voice"])
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=0.75, sample_rate_hertz=24000)
        
        response = self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        return base64.b64encode(response.audio_content).decode("utf-8")

    # --- REAL: Voice to Text ---
    def process_audio_to_text(self, audio_bytes: bytes, language: str = "English") -> str:
        voice_config = self._get_voice_config(language)
        audio = speech.RecognitionAudio(content=audio_bytes)
        
        # We removed sample_rate_hertz so Google can automatically detect it from the WebM header!
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            language_code=voice_config["code"]
        )
        
        response = self.stt_client.recognize(config=config, audio=audio)
        
        # Safety check if Google returns an empty result
        if not response.results:
            return ""
            
        return " ".join([result.alternatives[0].transcript for result in response.results])

    # --- REAL: Audio language translator ---
    def audio_language_translator(self, audio_bytes: bytes, source_language: str, target_language: str, user_email: str, client_name: str) -> dict:
        original_text = self.process_audio_to_text(audio_bytes, source_language)
        
        # If the audio couldn't be processed or is empty
        if not original_text.strip():
            return {"original_text": "", "translated_text": "Please provide valid audio to translate.", "audio_base64": ""}
            
        translated_text = self.translate_text(original_text, target_language, user_email, client_name) 
        translated_audio_base64 = self.generate_speech(translated_text, target_language)
        return {"original_text": original_text, "translated_text": translated_text, "audio_base64": translated_audio_base64}


    # --- Core Faculty Specific AI Methods ---
    
    def generate_teaching_material(self, topic: str, grade_level: str, user_email: str, client_name: str):
        prompt = f"""
        Act as an expert teacher. Generate a lesson plan for '{topic}' suited for '{grade_level}'.
        Return ONLY valid JSON format.
        Schema: {{"topic": "...", "grade_level": "...", "material": "...", "activities": ["...", "..."]}}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", "Generate Material")
        finally:
            db.close()
            
        return response.text.replace("```json", "").replace("```", "").strip()

    def generate_question_paper(self, topic: str, difficulty: str, format_type: str, num_questions: int, user_email: str, client_name: str):
        prompt = f"""
        Create a {difficulty} exam on '{topic}' containing {num_questions} {format_type} questions.
        Return ONLY valid JSON format.
        Schema: {{"topic": "...", "difficulty": "...", "format": "...", "questions": ["...", "..."]}}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", "Generate Exam")
        finally:
            db.close()
            
        return response.text.replace("```json", "").replace("```", "").strip()

    def auto_correct_answer(self, question: str, student_answer: str, rubric: str, user_email: str, client_name: str):
        prompt = f"""
        Grade this student answer based on the rubric.
        Question: {question} | Student Answer: {student_answer} | Rubric: {rubric}
        Return ONLY valid JSON format.
        Schema: {{"score": 85, "feedback": "...", "areas_for_improvement": ["...", "..."]}}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", "Auto Correct")
        finally:
            db.close()
            
        return response.text.replace("```json", "").replace("```", "").strip()

    def generate_teacher_alert(self, alert_type: str, details: dict, user_email: str, client_name: str):
        prompt = f"Draft a short, professional alert to a teacher regarding {alert_type}. Details: {details}"
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", "Generate Alert")
        finally:
            db.close()
            
        return response.text.strip()

    def evaluate_performance(self, performance_data: dict, scope_description: str, user_email: str, client_name: str):
        prompt = f"""
        Evaluate this classroom performance data ({scope_description}): {performance_data}
        Return ONLY valid JSON format.
        Schema: {{"scope": "...", "overall_score": 90, "strengths": ["..."], "weaknesses": ["..."], "recommendation": "..."}}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", "Evaluate Performance")
        finally:
            db.close()
            
        return response.text.replace("```json", "").replace("```", "").strip()

    # --- Competitive Exam Prep Features ---

    def get_competitive_exam_structure(self, exam_type: str, class_level: str, user_email: str, client_name: str):
        """
        Dynamically fetches the subjects and topics based on the selected exam and class.
        Use this to populate your frontend dropdowns!
        """
        prompt = f"""
        You are an expert curriculum designer for Indian competitive exams.
        A student in Class {class_level} wants to start foundation preparation for the '{exam_type}' exam.
        List the required subjects for this exam. For each subject, provide a list of foundational topics appropriate for a Class {class_level} cognitive level.
        
        Return ONLY valid JSON format. Do not use markdown blocks.
        Schema: {{"exam": "{exam_type}", "class": "{class_level}", "subjects": [{{"subject_name": "Biology", "topics": ["Cell Structure", "Tissues"]}}]}}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", "Fetch Exam Structure")
        finally:
            db.close()
            
        return response.text.replace("```json", "").replace("```", "").strip()

    def generate_competitive_content(self, exam_type: str, class_level: str, subject: str, topic: str, content_type: str, user_email: str, client_name: str):
        """
        Generates the actual Study Material or Quiz based on the specific exam, class, subject, and topic.
        content_type should be either 'Quiz' or 'Study Material'.
        """
        prompt = f"""
        Act as an expert coaching instructor for the {exam_type} exam in India.
        Create '{content_type}' for a student in Class {class_level} focusing on the subject '{subject}' and the topic '{topic}'.
        Since the student is in Class {class_level}, ensure the difficulty is at a 'Foundation' level—building core concepts that will help them later in their actual {exam_type} exam.

        Return ONLY valid JSON format. Do not use markdown blocks.
        """
        
        # Adjusting the required JSON schema based on what the user requested (Quiz vs Material)
        if content_type.lower() == "quiz":
            prompt += f"""
            Schema: {{"exam": "{exam_type}", "topic": "{topic}", "questions": [{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "...", "explanation": "..."}}]}}
            """
        else:
            prompt += f"""
            Schema: {{"exam": "{exam_type}", "topic": "{topic}", "core_concepts": ["...", "..."], "detailed_notes": "...", "important_formulas_or_facts": ["...", "..."]}}
            """
            
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", f"Generate Competitive {content_type}")
        finally:
            db.close()
            
        return response.text.replace("```json", "").replace("```", "").strip()
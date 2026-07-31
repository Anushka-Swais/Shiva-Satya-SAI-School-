import json
from config.ai_config import client, model_name
from config.database import SessionLocal
from utils.ai_tracker import log_gemini_usage

# Note: If FacultyAIController uses Google Cloud TTS/STT, you can inherit from AdminAIController.
# For now, I have implemented the core Gemini Generative features with Tracking!

class FacultyAIController:
    def __init__(self):
        pass

    # --- Core Translation & Voice Methods (Placeholders as provided, but added tracking arguments) ---
    def translate_text(self, text: str, target_language: str, user_email: str, client_name: str):
        # Your AI translation logic goes here
        return f"Translated '{text}' to {target_language}"

    def generate_speech(self, text: str, language: str):
        # Your TTS logic goes here
        return "base64_audio_string_mock"

    def process_audio_to_text(self, audio_bytes, language: str):
        # Your STT logic goes here
        return f"Transcribed text in {language}"

    def audio_language_translator(self, audio_bytes, source_language: str, target_language: str, user_email: str, client_name: str):
        # Your Audio translation logic
        return {"original_text": "Audio text", "translated_text": f"Translated to {target_language}"}

    # --- Faculty Specific AI Methods (Upgraded to use Gemini + Usage Tracking) ---
    
    def generate_teaching_material(self, topic: str, grade_level: str, user_email: str, client_name: str):
        prompt = f"""
        Act as an expert teacher. Generate a lesson plan for '{topic}' suited for '{grade_level}'.
        Return ONLY valid JSON format.
        Schema: {{"topic": "...", "grade_level": "...", "material": "...", "activities": ["...", "..."]}}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        # --- TRACKING ---
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
        
        # --- TRACKING ---
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
        
        # --- TRACKING ---
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", "Auto Correct")
        finally:
            db.close()
            
        return response.text.replace("```json", "").replace("```", "").strip()

    def generate_teacher_alert(self, alert_type: str, details: dict, user_email: str, client_name: str):
        prompt = f"Draft a short, professional alert to a teacher regarding {alert_type}. Details: {details}"
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        # --- TRACKING ---
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
        
        # --- TRACKING ---
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Faculty Dashboard", "Evaluate Performance")
        finally:
            db.close()
            
        return response.text.replace("```json", "").replace("```", "").strip()
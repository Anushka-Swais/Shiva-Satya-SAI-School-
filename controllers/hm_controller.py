import os
import json
from google.cloud import texttospeech
from google.cloud import speech
from google.api_core.client_options import ClientOptions

from controllers.admin_controller import AdminAIController
from config.ai_config import client, model_name
from config.database import SessionLocal
from utils.ai_tracker import log_gemini_usage

class HMAIController(AdminAIController):
    def __init__(self):
        # Inherits base routing from AdminAIController
        super().__init__()

        # --- EXPLICIT GOOGLE CLOUD TTS & STT INITIALIZATION ---
        # Securely pulls the API key from your .env file
        gcp_key = os.getenv("GOOGLE_TTS_API_KEY")
        if not gcp_key:
             raise ValueError("GOOGLE_TTS_API_KEY is missing from environment variables.")
             
        client_options = ClientOptions(api_key=gcp_key)
        self.tts_client = texttospeech.TextToSpeechClient(client_options=client_options)
        self.stt_client = speech.SpeechClient(client_options=client_options)

    # --- OVERRIDE: Ultra-Fast Translation & Native Script Fix ---
    def translate_text(self, text: str, target_language: str, user_email: str, client_name: str) -> str:
        # SUPER COMPRESSED PROMPT: Ensures ~1 second response time
        prompt = f"Translate to {target_language} (use native script only). Return ONLY the translation. Text: {text}"
        
        # Dynamically pulls from ai_config
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        # --- TRACKING LOGIC ---
        db = SessionLocal()
        try:
            log_gemini_usage(
                db=db,
                response=response,
                client_name=client_name,
                user_email=user_email,
                module_name="HM Dashboard",
                feature_name="Fast Text Translation"
            )
        finally:
            db.close()
            
        return response.text.strip()

    # --- 4. Assessment of students (UPDATED WITH TRACKING) ---
    def assess_student(self, student_data: dict, user_email: str, client_name: str) -> str:
        prompt = f"""
        Act as an expert Head Master and Academic Analyst. Analyze the following student performance data. 
        Provide a comprehensive, encouraging, but objective assessment report.
        
        You MUST return the output STRICTLY as a valid JSON object. Do not use markdown blocks.
        Schema:
        {{
            "executive_summary": "Overall text summary of the student's academic standing.",
            "strengths": ["...", "..."],
            "areas_for_improvement": ["...", "..."],
            "recommended_actions": ["...", "..."],
            "chart_data": [ {{"subject": "Math", "score": 85, "class_average": 75}} ]
        }}
        
        Student Data:
        {student_data}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        # --- TRACKING LOGIC ---
        db = SessionLocal()
        try:
            log_gemini_usage(
                db=db,
                response=response,
                client_name=client_name,
                user_email=user_email,
                module_name="HM Dashboard",
                feature_name="Assess Student"
            )
        finally:
            db.close()
        # ----------------------

        return response.text.replace("```json", "").replace("```", "").strip()

    # --- 5. Assessment of classroom (UPDATED WITH TRACKING) ---
    def assess_classroom(self, classroom_data: dict, user_email: str, client_name: str) -> str:
        prompt = f"""
        Act as an expert Head Master and Academic Analyst. Analyze the following macro-level classroom performance data.
        Identify specific subjects where the class excels and subjects that require pedagogical attention or teacher intervention.
        
        You MUST return the output STRICTLY as a valid JSON object. Do not use markdown blocks.
        Schema:
        {{
            "macro_summary": "Overall evaluation of the classroom's performance.",
            "top_performing_areas": ["...", "..."],
            "areas_needing_intervention": ["...", "..."],
            "teacher_recommendations": ["...", "..."],
            "chart_data": [ {{"metric_name": "Overall Attendance", "value": 92}}, {{"metric_name": "Science Pass Rate", "value": 78}} ]
        }}
        
        Classroom Data:
        {classroom_data}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        # --- TRACKING LOGIC ---
        db = SessionLocal()
        try:
            log_gemini_usage(
                db=db,
                response=response,
                client_name=client_name,
                user_email=user_email,
                module_name="HM Dashboard",
                feature_name="Assess Classroom"
            )
        finally:
            db.close()
        # ----------------------

        return response.text.replace("```json", "").replace("```", "").strip()

    # --- 6. Assessment of teacher (NEW FEATURE WITH TRACKING) ---
    def assess_teacher(self, teacher_data: dict, user_email: str, client_name: str) -> str:
        prompt = f"""
        Act as an expert Head Master. Analyze the following teacher performance and classroom management data.
        Provide a comprehensive, objective assessment report for this specific teacher. 
        Evaluate their effectiveness based on student outcomes, subject mastery, assignment completion rates, and any provided feedback.
        Identify areas of excellence and suggest actionable pedagogical improvements if necessary.

        CRITICAL INSTRUCTIONS: 
        - Write this as a clean, plain-text professional report. 
        - Do NOT output raw JSON.
        - Do NOT use markdown code blocks (like ```).

        Teacher Data:
        {teacher_data}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)

        # --- TRACKING LOGIC ---
        db = SessionLocal()
        try:
            log_gemini_usage(
                db=db,
                response=response,
                client_name=client_name,
                user_email=user_email,
                module_name="HM Dashboard",
                feature_name="Assess Teacher"
            )
        finally:
            db.close()
        # ----------------------

        return response.text.replace("```json", "").replace("```", "").strip()
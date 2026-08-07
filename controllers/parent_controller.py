import os
import json
from google.cloud import texttospeech
from google.cloud import speech
from google.api_core.client_options import ClientOptions

from controllers.admin_controller import AdminAIController
from config.ai_config import client, model_name
from config.database import SessionLocal
from utils.ai_tracker import log_gemini_usage

class ParentAIController(AdminAIController):
    def __init__(self):
        # Inherit base functionalities
        super().__init__()

        # --- EXPLICIT GOOGLE CLOUD TTS & STT INITIALIZATION ---
        gcp_key = os.getenv("GOOGLE_TTS_API_KEY")
        if not gcp_key:
             raise ValueError("GOOGLE_TTS_API_KEY is missing from environment variables.")
             
        client_options = ClientOptions(api_key=gcp_key)
        self.tts_client = texttospeech.TextToSpeechClient(client_options=client_options)
        self.stt_client = speech.SpeechClient(client_options=client_options)

    # --- OVERRIDE: Ultra-Fast Translation (ZERO TEMPERATURE) ---
    def translate_text(self, text: str, target_language: str, user_email: str, client_name: str) -> str:
        prompt = f"Translate to {target_language} (native script). Return ONLY translation. Text: {text}"
        
        # TEMPERATURE 0.0 forces maximum speed and prevents creative delays
        response = client.models.generate_content(
            model=model_name, 
            contents=prompt,
            config={"temperature": 0.0} 
        )
        
        # --- TRACKING LOGIC ---
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Parent Dashboard", "Fast Text Translation")
        finally:
            db.close()
            
        return response.text.strip()


    # --- 3. Student assessment per subject and per test ---
    def generate_assessment_summary(self, student_name: str, subject: str, test_name: str, marks_obtained: float, total_marks: float, teacher_remarks: str, user_email: str, client_name: str) -> str:
        prompt = f"""
        Act as an empathetic school counselor. Briefly summarize this test performance.
        Student: {student_name} | Subject: {subject} | Test: {test_name} | Score: {marks_obtained}/{total_marks} | Notes: "{teacher_remarks}"
        
        Return ONLY valid JSON object. No markdown.
        Schema: {{"summary_title": "...", "performance_breakdown": "...", "encouraging_feedback": "...", "home_support_tips": ["...", "..."]}}
        """
        # Low temperature (0.2) for fast, structured JSON generation
        response = client.models.generate_content(
            model=model_name, 
            contents=prompt,
            config={"temperature": 0.2}
        )
        
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Parent Dashboard", "Assessment Summary")
        finally:
            db.close()

        return response.text.replace("```json", "").replace("```", "").strip()

    # --- 4. Assignment due date alerts ---
    def generate_due_date_alert(self, student_name: str, assignment_title: str, subject: str, due_date: str, description: str, user_email: str, client_name: str) -> str:
        prompt = f"""
        Draft a friendly reminder alert to a parent.
        Student: {student_name} | Task: {assignment_title} | Subject: {subject} | Due: {due_date} | Details: {description}
        
        Return ONLY valid JSON object. No markdown.
        Schema: {{"alert_title": "...", "notification_message": "...", "suggested_parent_action": "..."}}
        """
        response = client.models.generate_content(
            model=model_name, 
            contents=prompt,
            config={"temperature": 0.1}
        )
        
        db = SessionLocal()
        try:
            log_gemini_usage(db, response, client_name, user_email, "Parent Dashboard", "Due Date Alert")
        finally:
            db.close()

        return response.text.replace("```json", "").replace("```", "").strip()
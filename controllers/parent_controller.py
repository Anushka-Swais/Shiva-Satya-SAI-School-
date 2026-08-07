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
        # Securely pulls the API key from your .env file
        gcp_key = os.getenv("GOOGLE_TTS_API_KEY")
        if not gcp_key:
             raise ValueError("GOOGLE_TTS_API_KEY is missing from environment variables.")
             
        client_options = ClientOptions(api_key=gcp_key)
        self.tts_client = texttospeech.TextToSpeechClient(client_options=client_options)
        self.stt_client = speech.SpeechClient(client_options=client_options)

    # --- OVERRIDE: Fast Translation & Telugu Quality Fix ---
    def translate_text(self, text: str, target_language: str, user_email: str, client_name: str) -> str:
        """
        Overridden to use gemini-3.5-flash for lightning-fast responses.
        Also includes strict enforcement for native scripts (like Telugu).
        """
        prompt = f"""Translate the following text into {target_language}. 
        CRITICAL: You MUST use the native script of {target_language} (e.g., if Telugu, use valid తెలుగు characters, NOT English alphabet transliteration).
        Return ONLY the translated text. Do not add quotes, notes, or markdown.
        
        Text: {text}"""
        
        # Explicitly using gemini-3.5-flash as requested
        response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
        
        # --- TRACKING LOGIC ---
        db = SessionLocal()
        try:
            log_gemini_usage(
                db=db,
                response=response,
                client_name=client_name,
                user_email=user_email,
                module_name="Parent Dashboard",
                feature_name="Fast Text Translation"
            )
        finally:
            db.close()
            
        return response.text.strip()


    # --- 3. Student assessment per subject and per test (UPDATED WITH TRACKING) ---
    def generate_assessment_summary(self, student_name: str, subject: str, test_name: str, marks_obtained: float, total_marks: float, teacher_remarks: str, user_email: str, client_name: str) -> str:
        prompt = f"""
        You are an empathetic, supportive AI school counselor communicating with a parent.
        Provide a brief, clear summary of the student's performance on a recent test.
        
        Student Name: {student_name}
        Subject: {subject}
        Test Name: {test_name}
        Score: {marks_obtained}/{total_marks}
        Teacher's Notes: "{teacher_remarks}"
        
        Guidelines:
        1. Break down what this grade means simply (avoid confusing educational jargon).
        2. Keep the tone encouraging, highlighting strengths while gently addressing areas for growth.
        3. Provide 1-2 practical, easy things the parent can do at home to support their child.
        
        You MUST return the output STRICTLY as a valid JSON object. Do not use markdown blocks.
        Schema:
        {{
            "summary_title": "...",
            "performance_breakdown": "...",
            "encouraging_feedback": "...",
            "home_support_tips": ["...", "..."]
        }}
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
                module_name="Parent Dashboard",
                feature_name="Assessment Summary"
            )
        finally:
            db.close()
        # ----------------------

        return response.text.replace("```json", "").replace("```", "").strip()

    # --- 4. Assignment due date alerts (UPDATED WITH TRACKING) ---
    def generate_due_date_alert(self, student_name: str, assignment_title: str, subject: str, due_date: str, description: str, user_email: str, client_name: str) -> str:
        prompt = f"""
        You are a helpful school assistant sending a friendly reminder alert to a parent.
        
        Student Name: {student_name}
        Assignment: {assignment_title}
        Subject: {subject}
        Due Date: {due_date}
        Task Details: {description}
        
        You MUST return the output STRICTLY as a valid JSON object. Do not use markdown blocks.
        Schema:
        {{
            "alert_title": "...",
            "notification_message": "...",
            "suggested_parent_action": "..."
        }}
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
                module_name="Parent Dashboard",
                feature_name="Due Date Alert"
            )
        finally:
            db.close()
        # ----------------------

        return response.text.replace("```json", "").replace("```", "").strip()
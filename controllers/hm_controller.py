import json
from controllers.admin_controller import AdminAIController
from config.ai_config import client, model_name

# --- NEW TRACKING IMPORTS ---
from config.database import SessionLocal
from utils.ai_tracker import log_gemini_usage

class HMAIController(AdminAIController):
    def __init__(self):
        # Inherits the Google Cloud Voice TTS/STT clients and translation from AdminAIController
        super().__init__()

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
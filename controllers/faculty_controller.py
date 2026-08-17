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
        lang_lower = language_name.lower().strip() if language_name else "english"
        return self.advanced_language_map.get(lang_lower, {"code": "en-IN", "voice": "en-IN-Neural2-A"})

    # --- PYTHON MATH HELPER FOR DYNAMIC MARKS BREAKDOWN ---
    def _calculate_mixed_distribution(self, total_marks: int) -> dict:
        """Calculates exact question counts for ANY total_marks so Gemini doesn't default to MCQs."""
        dist = {"mcq": 0, "true_false": 0, "fill_in_the_blank": 0, "short_answer": 0, "long_answer": 0}
        
        # Standard 50-mark pattern requested
        if total_marks == 50:
            return {
                "mcq": 5,              # 5 x 1m = 5 marks
                "true_false": 5,       # 5 x 1m = 5 marks (Or Fill in blanks/TF split)
                "fill_in_the_blank": 5,# 5 x 1m = 5 marks
                "short_answer": 10,    # 10 x 2m = 20 marks
                "long_answer": 3       # 3 x 5m = 15 marks (or 5 x 4m = 20 marks depending on breakdown)
            }
            
        # Dynamic calculation for non-50 total marks (e.g., 20, 30, 100)
        remaining = total_marks
        
        # Long answers (~40% of total marks, 4 marks each)
        long_count = int(total_marks * 0.4) // 4
        dist["long_answer"] = max(1 if total_marks >= 20 else 0, long_count)
        remaining -= (dist["long_answer"] * 4)
        
        # Short answers (~30% of total marks, 2 marks each)
        short_count = int(total_marks * 0.3) // 2
        dist["short_answer"] = max(1 if total_marks >= 10 else 0, short_count)
        remaining -= (dist["short_answer"] * 2)
        
        # Divide remaining 1-mark questions evenly across MCQ, True/False, Fill in Blank
        cycle = ["mcq", "true_false", "fill_in_the_blank"]
        idx = 0
        while remaining > 0:
            dist[cycle[idx % 3]] += 1
            remaining -= 1
            idx += 1
            
        return dist

    # --- REAL: Language script translator ---
    def translate_text(self, text: str, target_language: str, user_email: str, client_name: str) -> str:
        prompt = f"Translate to {target_language} (use native script only). Return ONLY the translation. Text: {text}"
        response = client.models.generate_content(model=model_name, contents=prompt)
        
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
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            language_code=voice_config["code"]
        )
        
        response = self.stt_client.recognize(config=config, audio=audio)
        if not response.results:
            return ""
            
        return " ".join([result.alternatives[0].transcript for result in response.results])

    # --- REAL: Audio language translator ---
    def audio_language_translator(self, audio_bytes: bytes, source_language: str, target_language: str, user_email: str, client_name: str) -> dict:
        original_text = self.process_audio_to_text(audio_bytes, source_language)
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

    # --- BULLETPROOF QUESTION PAPER GENERATOR ---
   # --- BULLETPROOF QUESTION PAPER GENERATOR ---
    def generate_question_paper(self, topic: str, difficulty: str, format_type: str = "all", num_questions: int = 0, user_email: str = "", client_name: str = "", total_marks: int = 50):
        
        # FIX: Ensure we capture the marks correctly even if the frontend passes it via 'num_questions'
        actual_marks = int(num_questions) if (int(num_questions) > 0 and int(total_marks) == 50) else int(total_marks)
        
        # Normalize format string
        format_clean = str(format_type).lower().strip() if format_type else "all"
        
        # Treats empty, 'optional', 'all', 'mixed', 'all types' as Mixed mode
        is_mixed_mode = format_clean in ["all", "all type", "all types", "mixed", "mixed type", "optional", "", "none"]
        
        if is_mixed_mode:
            dist = self._calculate_mixed_distribution(actual_marks)
            
            prompt = f"""
            Act as an expert school exam setter. Create a {difficulty} exam paper for '{topic}' totaling EXACTLY {actual_marks} marks.

            CRITICAL REQUIREMENT: You MUST generate questions with different types. Do NOT generate only MCQs.
            Generate a single flat array called 'questions' containing EXACTLY:
            - {dist['mcq']} MCQs (type: "mcq", 1 mark each)
            - {dist['true_false']} True/False questions (type: "true_false", 1 mark each)
            - {dist['fill_in_the_blank']} Fill in the Blanks (type: "fill_in_the_blank", 1 mark each)
            - {dist['short_answer']} Short Answer questions (type: "short_answer", 2 marks each, response max 180 chars)
            - {dist['long_answer']} Long Answer questions (type: "long_answer", 4 marks each, response max 2000 chars)

            STRICT JSON RULES:
            1. For 'mcq', include "options": ["A) ...", "B) ...", "C) ...", "D) ..."]
            2. For 'true_false', include "options": ["True", "False"]
            3. For 'fill_in_the_blank', 'short_answer', and 'long_answer', DO NOT include an 'options' field at all!

            Return ONLY valid JSON format without markdown code fences.
            Schema Example:
            {{
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "total_marks": {actual_marks},
                "format": "Mixed",
                "questions": [
                    {{"q_num": 1, "type": "mcq", "question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "marks": 1, "answer": "..."}},
                    {{"q_num": 2, "type": "true_false", "question": "...", "options": ["True", "False"], "marks": 1, "answer": "..."}},
                    {{"q_num": 3, "type": "fill_in_the_blank", "question": "...", "marks": 1, "answer": "..."}},
                    {{"q_num": 4, "type": "short_answer", "question": "...", "marks": 2, "max_characters": 180, "expected_answer": "..."}},
                    {{"q_num": 5, "type": "long_answer", "question": "...", "marks": 4, "max_characters": 2000, "expected_answer": "..."}}
                ]
            }}
            """

        elif "true" in format_clean or "false" in format_clean or "tf" in format_clean:
            prompt = f"""
            Create a {difficulty} exam on '{topic}' containing EXACTLY {actual_marks} True/False questions (1 mark each).
            Return ONLY valid JSON.
            Schema:
            {{
                "topic": "{topic}", "difficulty": "{difficulty}", "total_marks": {actual_marks}, "format": "True/False",
                "questions": [{{"q_num": 1, "type": "true_false", "question": "...", "options": ["True", "False"], "marks": 1, "answer": "..."}}]
            }}
            """

        elif "mcq" in format_clean or "quiz" in format_clean:
            prompt = f"""
            Create a {difficulty} exam on '{topic}' containing EXACTLY {actual_marks} MCQ questions (1 mark each).
            Return ONLY valid JSON.
            Schema:
            {{
                "topic": "{topic}", "difficulty": "{difficulty}", "total_marks": {actual_marks}, "format": "MCQ",
                "questions": [{{"q_num": 1, "type": "mcq", "question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "...", "marks": 1}}]
            }}
            """

        elif "short" in format_clean:
            count = max(1, actual_marks // 2)
            prompt = f"""
            Create a {difficulty} exam on '{topic}' containing EXACTLY {count} Short Answer questions (2 marks each = {count * 2} marks total).
            Do NOT include options array. Maximum 180 characters allowed per response.
            Return ONLY valid JSON.
            Schema:
            {{
                "topic": "{topic}", "difficulty": "{difficulty}", "total_marks": {count * 2}, "format": "Short Answers",
                "questions": [{{"q_num": 1, "type": "short_answer", "question": "...", "marks": 2, "max_characters": 180, "expected_answer": "..."}}]
            }}
            """

        elif "fill" in format_clean or "blank" in format_clean:
            prompt = f"""
            Create a {difficulty} exam on '{topic}' containing EXACTLY {actual_marks} Fill in the Blank questions (1 mark each).
            Do NOT include options array.
            Return ONLY valid JSON.
            Schema:
            {{
                "topic": "{topic}", "difficulty": "{difficulty}", "total_marks": {actual_marks}, "format": "Fill in the Blanks",
                "questions": [{{"q_num": 1, "type": "fill_in_the_blank", "question": "...", "marks": 1, "answer": "..."}}]
            }}
            """

        else:
            # FIX: Properly applied the exact quantities calculated by 'dist' to enforce limits on standard edge cases
            dist = self._calculate_mixed_distribution(actual_marks)
            prompt = f"""
            Create a {difficulty} exam on '{topic}' for EXACTLY {actual_marks} marks containing a mix of MCQs, True/False, Fill in Blanks, Short and Long answers.
            
            CRITICAL REQUIREMENT: You MUST strictly generate:
            - {dist['mcq']} MCQs (type: "mcq", 1 mark each)
            - {dist['true_false']} True/False questions (type: "true_false", 1 mark each)
            - {dist['fill_in_the_blank']} Fill in the Blanks (type: "fill_in_the_blank", 1 mark each)
            - {dist['short_answer']} Short Answer questions (type: "short_answer", 2 marks each)
            - {dist['long_answer']} Long Answer questions (type: "long_answer", 4 marks each)

            Return ONLY valid JSON.
            Schema:
            {{
                "topic": "{topic}", "difficulty": "{difficulty}", "total_marks": {actual_marks}, "format": "Mixed",
                "questions": [
                    {{"q_num": 1, "type": "mcq", "question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "marks": 1, "answer": "..."}},
                    {{"q_num": 2, "type": "short_answer", "question": "...", "marks": 2, "max_characters": 180, "expected_answer": "..."}}
                ]
            }}
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
        prompt = f"""
        Act as an expert coaching instructor for the {exam_type} exam in India.
        Create '{content_type}' for a student in Class {class_level} focusing on the subject '{subject}' and the topic '{topic}'.
        Since the student is in Class {class_level}, ensure the difficulty is at a 'Foundation' level—building core concepts that will help them later in their actual {exam_type} exam.

        Return ONLY valid JSON format. Do not use markdown blocks.
        """
        
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
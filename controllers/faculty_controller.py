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
    def _calculate_mixed_distribution(self, total_questions: int) -> dict:
        """Evenly distributes the exact requested question count across all 5 types."""
        base_count = total_questions // 5
        remainder = total_questions % 5
        
        dist = {
            "mcq": base_count,
            "true_false": base_count,
            "fill_in_the_blank": base_count,
            "short_answer": base_count,
            "long_answer": base_count
        }
        
        # Distribute any remaining questions sequentially so the count is EXACT
        keys = ["mcq", "true_false", "fill_in_the_blank", "short_answer", "long_answer"]
        for i in range(remainder):
            dist[keys[i]] += 1
            
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
    def generate_question_paper(self, topic: str, difficulty: str, format_type: str = "all", num_questions: int = 0, user_email: str = "", client_name: str = "", total_marks: int = 50):
        # We explicitly set the requested question count to exactly match the marks slider selection
        target_question_count = int(num_questions) if (int(num_questions) > 0 and int(total_marks) == 50) else int(total_marks)
        if target_question_count <= 0:
            target_question_count = 50
            
        format_clean = str(format_type).lower().strip() if format_type else "all"
        is_mixed_mode = format_clean in ["all", "all type", "all types", "mixed", "mixed type", "optional", "", "none"]
        
        # We mathematically force the LLM to see the exact sequential list it must complete
        q_numbers_list = list(range(1, target_question_count + 1))
        
        strict_rules = f"""
        !!! CRITICAL ANTI-LAZY INSTRUCTIONS !!!
        1. You MUST generate EXACTLY {target_question_count} questions. 
        2. The 'q_num' field MUST increment sequentially and perfectly match this list: {q_numbers_list}.
        3. DO NOT stop early. DO NOT output partial arrays. DO NOT use placeholders like "..." for questions.
        4. Keep questions extremely concise (max 1 sentence) to prevent output API truncation.
        5. Your final output MUST contain exactly {target_question_count} JSON objects in the 'questions' list.
        """

        if is_mixed_mode:
            dist = self._calculate_mixed_distribution(target_question_count)
            
            prompt = f"""
            Act as an expert school exam setter. Create a '{difficulty}' exam paper for '{topic}'.

            {strict_rules}
            
            QUESTION DISTRIBUTION (Total {target_question_count} questions):
            - {dist['mcq']} MCQs (type: "mcq")
            - {dist['true_false']} True/False questions (type: "true_false")
            - {dist['fill_in_the_blank']} Fill in the Blanks (type: "fill_in_the_blank")
            - {dist['short_answer']} Short Answers (type: "short_answer")
            - {dist['long_answer']} Long Answers (type: "long_answer")

            Return ONLY valid JSON format without markdown code fences.

            OVERALL JSON STRUCTURE:
            {{
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "total_marks": {target_question_count},
                "format": "Mixed",
                "questions": [ /* Insert all {target_question_count} question objects here */ ]
            }}

            OBJECT SCHEMAS (use the matching schema based on the question type):
            
            For "mcq":
            {{"q_num": <num>, "type": "mcq", "question": "<short text>", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "marks": 1, "answer": "<correct option>"}}

            For "true_false":
            {{"q_num": <num>, "type": "true_false", "question": "<short text>", "options": ["True", "False"], "marks": 1, "answer": "<correct option>"}}

            For "fill_in_the_blank":
            {{"q_num": <num>, "type": "fill_in_the_blank", "question": "<short text with blank>", "marks": 1, "answer": "<answer>"}}

            For "short_answer":
            {{"q_num": <num>, "type": "short_answer", "question": "<short text>", "marks": 1, "max_characters": 180, "expected_answer": "<answer>"}}

            For "long_answer":
            {{"q_num": <num>, "type": "long_answer", "question": "<short text>", "marks": 1, "max_characters": 2000, "expected_answer": "<answer>"}}
            """

        elif "true" in format_clean or "false" in format_clean or "tf" in format_clean:
            prompt = f"""
            Create a '{difficulty}' exam on '{topic}'.
            
            {strict_rules}
            
            REQUIREMENT: ALL {target_question_count} questions MUST be True/False questions (marks: 1 each).
            
            Return ONLY valid JSON format without markdown code fences.
            
            OVERALL JSON STRUCTURE:
            {{
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "total_marks": {target_question_count},
                "format": "True/False",
                "questions": [ /* Insert all {target_question_count} question objects here */ ]
            }}

            STRUCTURE FOR EACH QUESTION OBJECT:
            {{"q_num": <num>, "type": "true_false", "question": "<short text>", "options": ["True", "False"], "marks": 1, "answer": "<correct option>"}}
            """

        elif "mcq" in format_clean or "quiz" in format_clean:
            prompt = f"""
            Create a '{difficulty}' exam on '{topic}'.
            
            {strict_rules}
            
            REQUIREMENT: ALL {target_question_count} questions MUST be MCQ questions (marks: 1 each).
            
            Return ONLY valid JSON format without markdown code fences.
            
            OVERALL JSON STRUCTURE:
            {{
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "total_marks": {target_question_count},
                "format": "MCQ",
                "questions": [ /* Insert all {target_question_count} question objects here */ ]
            }}

            STRUCTURE FOR EACH QUESTION OBJECT:
            {{"q_num": <num>, "type": "mcq", "question": "<short text>", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "marks": 1, "answer": "<correct option>"}}
            """

        elif "short" in format_clean:
            prompt = f"""
            Create a '{difficulty}' exam on '{topic}'.
            
            {strict_rules}
            
            REQUIREMENT: ALL {target_question_count} questions MUST be Short Answer questions (marks: 1 each).
            
            Return ONLY valid JSON format without markdown code fences.
            
            OVERALL JSON STRUCTURE:
            {{
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "total_marks": {target_question_count},
                "format": "Short Answers",
                "questions": [ /* Insert all {target_question_count} question objects here */ ]
            }}

            STRUCTURE FOR EACH QUESTION OBJECT:
            {{"q_num": <num>, "type": "short_answer", "question": "<short text>", "marks": 1, "max_characters": 180, "expected_answer": "<answer>"}}
            """

        elif "fill" in format_clean or "blank" in format_clean:
            prompt = f"""
            Create a '{difficulty}' exam on '{topic}'.
            
            {strict_rules}
            
            REQUIREMENT: ALL {target_question_count} questions MUST be Fill in the Blank questions (marks: 1 each).
            
            Return ONLY valid JSON format without markdown code fences.
            
            OVERALL JSON STRUCTURE:
            {{
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "total_marks": {target_question_count},
                "format": "Fill in the Blanks",
                "questions": [ /* Insert all {target_question_count} question objects here */ ]
            }}

            STRUCTURE FOR EACH QUESTION OBJECT:
            {{"q_num": <num>, "type": "fill_in_the_blank", "question": "<short text with blank>", "marks": 1, "answer": "<answer>"}}
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
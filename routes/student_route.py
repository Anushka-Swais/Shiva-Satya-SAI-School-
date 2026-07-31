import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from controllers.student_controller import StudentAIController

router = APIRouter()
student_controller = StudentAIController()

# --- Schemas (Updated with Tracking Fields) ---
class TranslationRequest(BaseModel):
    text: str
    target_language: str
    user_email: str
    client_name: str = "SSS"

class TTSRequest(BaseModel):
    text: str
    language: str = "English"
    user_email: str
    client_name: str = "SSS"

class ContentRequest(BaseModel):
    topic: str
    learning_capacity: str  
    user_email: str
    client_name: str = "SSS"

class QuizRequest(BaseModel):
    topic: str
    difficulty: str
    num_questions: int = 5
    user_email: str
    client_name: str = "SSS"

class QuizEvaluationRequest(BaseModel):
    submission_data: dict  
    user_email: str
    client_name: str = "SSS"

class SelfAssessmentRequest(BaseModel):
    performance_data: dict 
    user_email: str
    client_name: str = "SSS"

class AlertRequest(BaseModel):
    assignment_name: str
    due_date: str
    user_email: str
    client_name: str = "SSS"


# --- Endpoints ---

# 4. Language script translator
@router.post("/translate")
async def translate_script(req: TranslationRequest):
    try:
        translated = student_controller.translate_text(req.text, req.target_language, req.user_email, req.client_name)
        return {"status": "success", "translated_text": translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Text to Voice
@router.post("/text-to-voice")
async def text_to_voice(req: TTSRequest):
    try:
        # TTS doesn't use Gemini tokens, but passing tracking vars keeps frontend payload standardized
        return {"status": "success", "audio_base64": student_controller.generate_speech(req.text, req.language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Voice to Text
@router.post("/voice-to-text")
async def voice_to_text(
    file: UploadFile = File(...), 
    language: str = Form("English"),
    user_email: str = Form(...),
    client_name: str = Form("SSS")
):
    try:
        audio_bytes = await file.read()
        return {"status": "success", "transcription": student_controller.process_audio_to_text(audio_bytes, language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Audio language translator
@router.post("/audio-translator")
async def audio_translator(
    file: UploadFile = File(...), 
    source_language: str = Form("English"), 
    target_language: str = Form(...),
    user_email: str = Form(...),
    client_name: str = Form("SSS")
):
    try:
        audio_bytes = await file.read()
        result = student_controller.audio_language_translator(audio_bytes, source_language, target_language, user_email, client_name)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 1. Automatic content generation
@router.post("/content/generate")
async def generate_content(req: ContentRequest):
    try:
        content = student_controller.generate_content(req.topic, req.learning_capacity, req.user_email, req.client_name)
        return {"status": "success", "generated_content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Automatic quiz generation
@router.post("/quiz/generate")
async def generate_quiz(req: QuizRequest):
    try:
        quiz_string = student_controller.generate_quiz(req.topic, req.difficulty, req.num_questions, req.user_email, req.client_name)
        return {"status": "success", "quiz_data": json.loads(quiz_string)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Auto correction
@router.post("/quiz/evaluate")
async def evaluate_quiz(req: QuizEvaluationRequest):
    try:
        # Separate the tracking credentials from the actual payload data
        data = req.model_dump()
        user_email = data.pop("user_email")
        client_name = data.pop("client_name")
        
        eval_string = student_controller.evaluate_quiz(data["submission_data"], user_email, client_name)
        return {"status": "success", "evaluation_report": json.loads(eval_string)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Self Assessment with graphical representation
@router.post("/assess/self")
async def self_assessment(req: SelfAssessmentRequest):
    try:
        data = req.model_dump()
        user_email = data.pop("user_email")
        client_name = data.pop("client_name")
        
        assessment_string = student_controller.assess_self_performance(data["performance_data"], user_email, client_name)
        return {"status": "success", "assessment_data": json.loads(assessment_string)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7. Assignment due date alerts
@router.post("/alerts/generate")
async def generate_alert(req: AlertRequest):
    try:
        alert_msg = student_controller.generate_assignment_alert(req.assignment_name, req.due_date, req.user_email, req.client_name)
        return {"status": "success", "alert_message": alert_msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from controllers.faculty_controller import FacultyAIController

router = APIRouter()
faculty_controller = FacultyAIController()

# --- Schemas ---
class TranslationRequest(BaseModel):
    text: str
    target_language: str

class TTSRequest(BaseModel):
    text: str
    language: str = "English"

class MaterialRequest(BaseModel):
    topic: str
    grade_level: str

class QuestionPaperRequest(BaseModel):
    topic: str
    difficulty: str
    format_type: str
    num_questions: int

class AutoCorrectRequest(BaseModel):
    question: str
    student_answer: str
    rubric: str

class AlertRequest(BaseModel):
    alert_type: str 
    details: dict 

class AssessmentRequest(BaseModel):
    scope_description: str 
    performance_data: dict

# --- Endpoints ---

# 10. Language script translator
@router.post("/translate")
async def translate_script(req: TranslationRequest):
    try:
        return {"status": "success", "translated_text": faculty_controller.translate_text(req.text, req.target_language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 12. Text to Voice
@router.post("/text-to-voice")
async def text_to_voice(req: TTSRequest):
    try:
        return {"status": "success", "audio_base64": faculty_controller.generate_speech(req.text, req.language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 12. Voice to Text
@router.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...), language: str = Form("English")):
    try:
        audio_bytes = await file.read()
        return {"status": "success", "transcription": faculty_controller.process_audio_to_text(audio_bytes, language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 11. Audio language translator
@router.post("/audio-translator")
async def audio_translator(
    file: UploadFile = File(...), 
    source_language: str = Form("English"), 
    target_language: str = Form(...)
):
    try:
        audio_bytes = await file.read()
        return {"status": "success", "data": faculty_controller.audio_language_translator(audio_bytes, source_language, target_language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 1. Automatic teaching material generation
@router.post("/generate-material")
async def generate_material(req: MaterialRequest):
    try:
        material_str = faculty_controller.generate_teaching_material(req.topic, req.grade_level)
        return {"status": "success", "teaching_material": json.loads(material_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Automatic question paper generation
@router.post("/generate-exam")
async def generate_exam(req: QuestionPaperRequest):
    try:
        exam_str = faculty_controller.generate_question_paper(req.topic, req.difficulty, req.format_type, req.num_questions)
        return {"status": "success", "question_paper": json.loads(exam_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Automatic correction
@router.post("/auto-correct")
async def auto_correct(req: AutoCorrectRequest):
    try:
        feedback_str = faculty_controller.auto_correct_answer(req.question, req.student_answer, req.rubric)
        return {"status": "success", "grading_feedback": json.loads(feedback_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4 & 5. Assignment alerts
@router.post("/alerts")
async def generate_alert(req: AlertRequest):
    try:
        alert = faculty_controller.generate_teacher_alert(req.alert_type, req.details)
        return {"status": "success", "alert_message": alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 8 & 9. Student/Classroom Assessment (Per Subject or Overall)
@router.post("/assess")
async def evaluate_performance(req: AssessmentRequest):
    try:
        assessment_str = faculty_controller.evaluate_performance(req.performance_data, req.scope_description)
        return {"status": "success", "assessment_report": json.loads(assessment_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
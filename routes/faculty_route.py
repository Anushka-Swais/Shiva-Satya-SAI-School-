import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from controllers.faculty_controller import FacultyAIController

router = APIRouter()
faculty_controller = FacultyAIController()

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

class MaterialRequest(BaseModel):
    topic: str
    grade_level: str
    user_email: str
    client_name: str = "SSS"

class QuestionPaperRequest(BaseModel):
    topic: str
    difficulty: str
    format_type: str
    num_questions: int
    user_email: str
    client_name: str = "SSS"

class AutoCorrectRequest(BaseModel):
    question: str
    student_answer: str
    rubric: str
    user_email: str
    client_name: str = "SSS"

class AlertRequest(BaseModel):
    alert_type: str 
    details: dict 
    user_email: str
    client_name: str = "SSS"

class AssessmentRequest(BaseModel):
    scope_description: str 
    performance_data: dict
    user_email: str
    client_name: str = "SSS"

class CompetitiveStructureRequest(BaseModel):
    exam_type: str
    class_level: str
    user_email: str
    client_name: str = "SSS"

class CompetitiveContentRequest(BaseModel):
    exam_type: str
    class_level: str
    subject: str
    topic: str
    content_type: str # 'Quiz' or 'Study Material'
    user_email: str
    client_name: str = "SSS"

# --- Endpoints ---

@router.post("/translate")
async def translate_script(req: TranslationRequest):
    try:
        translated = faculty_controller.translate_text(req.text, req.target_language, req.user_email, req.client_name)
        return {"status": "success", "translated_text": translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/text-to-voice")
async def text_to_voice(req: TTSRequest):
    try:
        # Note: Usually no Gemini tokens used here, but keeping API payload consistent
        return {"status": "success", "audio_base64": faculty_controller.generate_speech(req.text, req.language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice-to-text")
async def voice_to_text(
    file: UploadFile = File(...), 
    language: str = Form("English"),
    user_email: str = Form(...),
    client_name: str = Form("SSS")
):
    try:
        audio_bytes = await file.read()
        return {"status": "success", "transcription": faculty_controller.process_audio_to_text(audio_bytes, language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        result = faculty_controller.audio_language_translator(audio_bytes, source_language, target_language, user_email, client_name)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-material")
async def generate_material(req: MaterialRequest):
    try:
        material_str = faculty_controller.generate_teaching_material(req.topic, req.grade_level, req.user_email, req.client_name)
        return {"status": "success", "teaching_material": json.loads(material_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-exam")
async def generate_exam(req: QuestionPaperRequest):
    try:
        exam_str = faculty_controller.generate_question_paper(req.topic, req.difficulty, req.format_type, req.num_questions, req.user_email, req.client_name)
        return {"status": "success", "question_paper": json.loads(exam_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-correct")
async def auto_correct(req: AutoCorrectRequest):
    try:
        feedback_str = faculty_controller.auto_correct_answer(req.question, req.student_answer, req.rubric, req.user_email, req.client_name)
        return {"status": "success", "grading_feedback": json.loads(feedback_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts")
async def generate_alert(req: AlertRequest):
    try:
        alert = faculty_controller.generate_teacher_alert(req.alert_type, req.details, req.user_email, req.client_name)
        return {"status": "success", "alert_message": alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assess")
async def evaluate_performance(req: AssessmentRequest):
    try:
        assessment_str = faculty_controller.evaluate_performance(req.performance_data, req.scope_description, req.user_email, req.client_name)
        return {"status": "success", "assessment_report": json.loads(assessment_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/competitive/structure")
async def get_competitive_structure(req: CompetitiveStructureRequest):
    try:
        structure_str = faculty_controller.get_competitive_exam_structure(
            req.exam_type, req.class_level, req.user_email, req.client_name
        )
        return {"status": "success", "exam_structure": json.loads(structure_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/competitive/generate")
async def generate_competitive_content(req: CompetitiveContentRequest):
    try:
        content_str = faculty_controller.generate_competitive_content(
            req.exam_type, req.class_level, req.subject, req.topic, req.content_type, req.user_email, req.client_name
        )
        return {"status": "success", "competitive_content": json.loads(content_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
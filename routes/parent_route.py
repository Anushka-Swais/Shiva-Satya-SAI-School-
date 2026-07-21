import json
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from controllers.parent_controller import ParentAIController 

router = APIRouter()
parent_ai = ParentAIController()

# --- Schemas ---
class TranslationRequest(BaseModel):
    text: str
    target_language: str

class TTSRequest(BaseModel):
    text: str
    language: str = "English"

class AssessmentSummaryRequest(BaseModel):
    student_name: str
    subject: str
    test_name: str
    marks_obtained: float
    total_marks: float
    teacher_remarks: str

class DueDateAlertRequest(BaseModel):
    student_name: str
    assignment_title: str
    subject: str
    due_date: str
    description: str


# --- Endpoints ---

# 1. Language script translator (Inherited logic)
@router.post("/translate")
async def translate_script(req: TranslationRequest):
    try:
        return {"status": "success", "translated_text": parent_ai.translate_text(req.text, req.target_language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Text to Voice (Inherited logic)
@router.post("/text-to-voice")
async def text_to_voice(req: TTSRequest):
    try:
        return {"status": "success", "audio_base64": parent_ai.generate_speech(req.text, req.language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Voice to Text (Inherited logic)
@router.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...), language: str = Form("English")):
    try:
        audio_bytes = await file.read()
        return {"status": "success", "transcription": parent_ai.process_audio_to_text(audio_bytes, language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Audio language translator (Inherited logic)
@router.post("/audio-translator")
async def audio_translator(
    file: UploadFile = File(...), 
    source_language: str = Form("English"), 
    target_language: str = Form(...)
):
    try:
        audio_bytes = await file.read()
        return {"status": "success", "data": parent_ai.audio_language_translator(audio_bytes, source_language, target_language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 3. Student assessment per subject and per test
@router.post("/assessment-summary")
async def get_assessment_summary(req: AssessmentSummaryRequest):
    try:
        summary_str = parent_ai.generate_assessment_summary(
            student_name=req.student_name, subject=req.subject, test_name=req.test_name,
            marks_obtained=req.marks_obtained, total_marks=req.total_marks, teacher_remarks=req.teacher_remarks
        )
        return {"status": "success", "summary": json.loads(summary_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Assignment due date alerts
@router.post("/due-date-alert")
async def get_due_date_alert(req: DueDateAlertRequest):
    try:
        alert_str = parent_ai.generate_due_date_alert(
            student_name=req.student_name, assignment_title=req.assignment_title, 
            subject=req.subject, due_date=req.due_date, description=req.description
        )
        return {"status": "success", "alert_data": json.loads(alert_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
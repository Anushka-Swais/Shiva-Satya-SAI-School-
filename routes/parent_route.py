import json
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from controllers.parent_controller import ParentAIController 

router = APIRouter()
parent_ai = ParentAIController()

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

class AssessmentSummaryRequest(BaseModel):
    student_name: str
    subject: str
    test_name: str
    marks_obtained: float
    total_marks: float
    teacher_remarks: str
    user_email: str
    client_name: str = "SSS"

class DueDateAlertRequest(BaseModel):
    student_name: str
    assignment_title: str
    subject: str
    due_date: str
    description: str
    user_email: str
    client_name: str = "SSS"


# --- Endpoints ---

# 1. Language script translator (REMOVED ASYNC FOR THREADING)
@router.post("/translate")
def translate_script(req: TranslationRequest):
    try:
        translated = parent_ai.translate_text(
            req.text, 
            req.target_language, 
            req.user_email, 
            req.client_name
        )
        return {"status": "success", "translated_text": translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Text to Voice (REMOVED ASYNC FOR THREADING)
@router.post("/text-to-voice")
def text_to_voice(req: TTSRequest):
    try:
        return {"status": "success", "audio_base64": parent_ai.generate_speech(req.text, req.language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Voice to Text (REMOVED ASYNC FOR THREADING)
@router.post("/voice-to-text")
def voice_to_text(
    file: UploadFile = File(...), 
    language: str = Form("English"),
    user_email: str = Form(...),
    client_name: str = Form("SSS")
):
    try:
        # Changed to synchronous read
        audio_bytes = file.file.read() 
        return {"status": "success", "transcription": parent_ai.process_audio_to_text(audio_bytes, language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Audio language translator (REMOVED ASYNC FOR THREADING)
@router.post("/audio-translator")
def audio_translator(
    file: UploadFile = File(...), 
    source_language: str = Form("English"), 
    target_language: str = Form(...),
    user_email: str = Form(...),
    client_name: str = Form("SSS")
):
    try:
        # Changed to synchronous read
        audio_bytes = file.file.read()
        result = parent_ai.audio_language_translator(
            audio_bytes, 
            source_language, 
            target_language, 
            user_email, 
            client_name
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Student assessment per subject and per test (REMOVED ASYNC FOR THREADING)
@router.post("/assessment-summary")
def get_assessment_summary(req: AssessmentSummaryRequest):
    try:
        summary_str = parent_ai.generate_assessment_summary(
            student_name=req.student_name, 
            subject=req.subject, 
            test_name=req.test_name,
            marks_obtained=req.marks_obtained, 
            total_marks=req.total_marks, 
            teacher_remarks=req.teacher_remarks,
            user_email=req.user_email,
            client_name=req.client_name
        )
        parsed_data = json.loads(summary_str)
        return {"status": "success", **parsed_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Assignment due date alerts (REMOVED ASYNC FOR THREADING)
@router.post("/due-date-alert")
def get_due_date_alert(req: DueDateAlertRequest):
    try:
        alert_str = parent_ai.generate_due_date_alert(
            student_name=req.student_name, 
            assignment_title=req.assignment_title, 
            subject=req.subject, 
            due_date=req.due_date, 
            description=req.description,
            user_email=req.user_email,
            client_name=req.client_name
        )
        parsed_alert = json.loads(alert_str)
        return {"status": "success", **parsed_alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
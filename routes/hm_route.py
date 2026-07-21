import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from controllers.hm_controller import HMAIController

router = APIRouter()
hm_controller = HMAIController()

# --- Schemas ---
class TranslationRequest(BaseModel):
    text: str
    target_language: str

class TTSRequest(BaseModel):
    text: str
    language: str = "English"

class StudentAssessmentRequest(BaseModel):
    student_name: str
    metrics: dict

class ClassroomAssessmentRequest(BaseModel):
    class_name: str
    metrics: dict


# --- Endpoints ---

# 1. Language script translator (Inherited logic)
@router.post("/translate")
async def translate_script(req: TranslationRequest):
    try:
        return {"status": "success", "translated_text": hm_controller.translate_text(req.text, req.target_language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Text to Voice (Inherited logic)
@router.post("/text-to-voice")
async def text_to_voice(req: TTSRequest):
    try:
        return {"status": "success", "audio_base64": hm_controller.generate_speech(req.text, req.language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Voice to Text (Inherited logic)
@router.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...), language: str = Form("English")):
    try:
        audio_bytes = await file.read()
        return {"status": "success", "transcription": hm_controller.process_audio_to_text(audio_bytes, language)}
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
        return {"status": "success", "data": hm_controller.audio_language_translator(audio_bytes, source_language, target_language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Assessment of students (per student, per subject, or all subjects)
@router.post("/assess/student")
async def generate_student_assessment(req: StudentAssessmentRequest):
    try:
        assessment_str = hm_controller.assess_student(req.model_dump())
        return {"status": "success", "assessment_report": json.loads(assessment_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Assessment of classroom (per subject or overall)
@router.post("/assess/classroom")
async def generate_classroom_assessment(req: ClassroomAssessmentRequest):
    try:
        assessment_str = hm_controller.assess_classroom(req.model_dump())
        return {"status": "success", "assessment_report": json.loads(assessment_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
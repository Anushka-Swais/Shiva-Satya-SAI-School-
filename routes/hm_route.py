import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from controllers.hm_controller import HMAIController

router = APIRouter()
hm_controller = HMAIController()

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

class StudentAssessmentRequest(BaseModel):
    student_name: str
    metrics: dict
    user_email: str
    client_name: str = "SSS"

class ClassroomAssessmentRequest(BaseModel):
    class_name: str
    metrics: dict
    user_email: str
    client_name: str = "SSS"

class TeacherAssessmentRequest(BaseModel):
    teacher_name: str
    metrics: dict
    user_email: str
    client_name: str = "SSS"


# --- Endpoints ---

# 1. Language script translator (Inherited logic - Now passes tracking data)
@router.post("/translate")
async def translate_script(req: TranslationRequest):
    try:
        translated = hm_controller.translate_text(req.text, req.target_language, req.user_email, req.client_name)
        return {"status": "success", "translated_text": translated}
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
async def voice_to_text(
    file: UploadFile = File(...), 
    language: str = Form("English"),
    user_email: str = Form(...),
    client_name: str = Form("SSS")
):
    try:
        audio_bytes = await file.read()
        return {"status": "success", "transcription": hm_controller.process_audio_to_text(audio_bytes, language)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Audio language translator (Inherited logic - Now passes tracking data)
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
        result = hm_controller.audio_language_translator(audio_bytes, source_language, target_language, user_email, client_name)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Assessment of students
@router.post("/assess/student")
async def generate_student_assessment(req: StudentAssessmentRequest):
    try:
        # Separate the tracking credentials from the actual payload data
        data = req.model_dump()
        user_email = data.pop("user_email")
        client_name = data.pop("client_name")
        
        assessment_str = hm_controller.assess_student(data, user_email, client_name)
        return {"status": "success", "assessment_report": json.loads(assessment_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Assessment of classroom
@router.post("/assess/classroom")
async def generate_classroom_assessment(req: ClassroomAssessmentRequest):
    try:
        # Separate the tracking credentials from the actual payload data
        data = req.model_dump()
        user_email = data.pop("user_email")
        client_name = data.pop("client_name")
        
        assessment_str = hm_controller.assess_classroom(data, user_email, client_name)
        return {"status": "success", "assessment_report": json.loads(assessment_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Assessment of teacher
@router.post("/assess/teacher")
async def generate_teacher_assessment(req: TeacherAssessmentRequest):
    try:
        # Separate the tracking credentials from the actual payload data
        data = req.model_dump()
        user_email = data.pop("user_email")
        client_name = data.pop("client_name")
        
        assessment_str = hm_controller.assess_teacher(data, user_email, client_name)
        return {"status": "success", "assessment_report": assessment_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
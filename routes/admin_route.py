import time
from typing import Union
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from controllers.admin_controller import AdminAIController

router = APIRouter()
admin_controller = AdminAIController()

# --- Schemas ---
class TranslationRequest(BaseModel):
    # 🚀 FIX: Now accepts a single string OR an array of strings for bulk translation!
    text: Union[str, list[str]]
    target_language: str
    user_email: str
    client_name: str = "SSS"

class TTSRequest(BaseModel):
    text: str
    language: str = "English"
    user_email: str
    client_name: str = "SSS"

# --- Endpoints ---

# 1. Language script translator (REMOVED ASYNC FOR THREADING)
@router.post("/translate")
def translate_script(req: TranslationRequest):
    try:
        # Start Stopwatch
        start_time = time.time()
        
        translated = admin_controller.translate_text(
            text=req.text, 
            target_language=req.target_language,
            user_email=req.user_email,
            client_name=req.client_name
        )
        
        # Stop Stopwatch
        execution_time = round(time.time() - start_time, 2)
        
        # Smart logging based on whether it was a bulk list or single string
        if isinstance(req.text, list):
            print(f"⏱️ Admin Bulk Translation Backend Time ({len(req.text)} items): {execution_time} seconds")
        else:
            print(f"⏱️ Admin Translation Backend Time: {execution_time} seconds")
        
        return {
            "status": "success", 
            "translated_text": translated,
            "backend_time_seconds": execution_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Text to Voice (REMOVED ASYNC FOR THREADING)
@router.post("/text-to-voice")
def text_to_voice(req: TTSRequest):
    try:
        audio_base64 = admin_controller.generate_speech(req.text, req.language)
        return {"status": "success", "audio_base64": audio_base64}
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
        # 🚀 Fix: Synchronous file read
        audio_bytes = file.file.read()
        transcription = admin_controller.process_audio_to_text(audio_bytes, language)
        return {"status": "success", "transcription": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Audio language translator (REMOVED ASYNC FOR THREADING)
@router.post("/audio-translator")
def audio_translator(
    file: UploadFile = File(...), 
    source_language: str = Form("English"), 
    target_language: str = Form(...),
    user_email: str = Form(...),
    client_name: str = Form("SSS")
):
    try:
        # 🚀 Fix: Synchronous file read
        audio_bytes = file.file.read()
        result = admin_controller.audio_language_translator(
            audio_bytes=audio_bytes, 
            source_language=source_language, 
            target_language=target_language,
            user_email=user_email,
            client_name=client_name
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
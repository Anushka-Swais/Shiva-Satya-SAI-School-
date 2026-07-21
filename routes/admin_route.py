from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from controllers.admin_controller import AdminAIController

router = APIRouter()
admin_controller = AdminAIController()

# --- Schemas ---
class TranslationRequest(BaseModel):
    text: str
    target_language: str

class TTSRequest(BaseModel):
    text: str
    language: str = "English"


# --- Endpoints ---

# 1. Language script translator
@router.post("/translate")
async def translate_script(req: TranslationRequest):
    try:
        translated = admin_controller.translate_text(req.text, req.target_language)
        return {"status": "success", "translated_text": translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Text to Voice
@router.post("/text-to-voice")
async def text_to_voice(req: TTSRequest):
    try:
        audio_base64 = admin_controller.generate_speech(req.text, req.language)
        return {"status": "success", "audio_base64": audio_base64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Voice to Text
@router.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...), language: str = Form("English")):
    try:
        audio_bytes = await file.read()
        transcription = admin_controller.process_audio_to_text(audio_bytes, language)
        return {"status": "success", "transcription": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Audio language translator
@router.post("/audio-translator")
async def audio_translator(
    file: UploadFile = File(...), 
    source_language: str = Form("English"), 
    target_language: str = Form(...)
):
    try:
        audio_bytes = await file.read()
        result = admin_controller.audio_language_translator(audio_bytes, source_language, target_language)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
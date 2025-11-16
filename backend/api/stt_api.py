from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
from loguru import logger

from tools.stt_whisper import get_stt

router = APIRouter(prefix="/api/stt", tags=["stt"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Offline transcription endpoint.
    Accepts a WAV/MP3/OGG file (prefer mono 16k WAV) and returns text.
    """
    try:
        audio_bytes = await file.read()
        stt = get_stt()
        text = stt.transcribe_wav_bytes(audio_bytes, language=language)
        return JSONResponse({"success": True, "text": text})
    except Exception as e:
        logger.error(f"/stt/transcribe error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)



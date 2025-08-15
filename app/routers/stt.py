"""Speech-to-Text API endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.models.schemas import TranscriptionResponse, UploadResponse
from app.services.stt import stt_service
from app.core.config import settings
from app.core.logging import get_logger
from pathlib import Path
import shutil

logger = get_logger(__name__)

router = APIRouter(prefix="/stt", tags=["Speech-to-Text"])

# Ensure upload folder exists
UPLOAD_FOLDER = Path(settings.UPLOAD_FOLDER)
UPLOAD_FOLDER.mkdir(exist_ok=True)


@router.post("/transcribe", response_model=TranscriptionResponse, summary="Transcribe audio file")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file to text using AssemblyAI.
    
    - **file**: Audio file to transcribe (supported formats: webm, wav, mp3, m4a, ogg, opus)
    """
    try:
        # Validate file type
        if not stt_service.validate_audio_format(file.content_type):
            logger.error(f"Unsupported file type: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {settings.ALLOWED_AUDIO_TYPES}"
            )
        
        if not stt_service.is_configured():
            logger.error("STT service not configured")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Transcription service unavailable - API key not configured",
                    "service_type": "STT"
                }
            )
        
        # Read audio data
        audio_data = await file.read()
        logger.info(f"Transcribing audio file: {file.filename} ({len(audio_data)} bytes)")
        
        # Transcribe audio
        transcription = stt_service.transcribe_audio(audio_data)
        
        if transcription:
            logger.info("Transcription successful")
            return TranscriptionResponse(
                transcription=transcription,
                filename=file.filename,
                content_type=file.content_type,
                size_bytes=len(audio_data)
            )
        else:
            logger.error("Transcription failed")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Transcription failed",
                    "service_type": "STT"
                }
            )
            
    except ValueError as e:
        logger.error(f"STT validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"STT endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload", response_model=UploadResponse, summary="Upload audio file")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload an audio file for processing.
    
    - **file**: Audio file to upload
    """
    try:
        # Validate file type
        if not stt_service.validate_audio_format(file.content_type):
            logger.error(f"Unsupported file type: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Save the uploaded file
        file_location = UPLOAD_FOLDER / file.filename
        
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Get file size
        file_size = file_location.stat().st_size
        
        logger.info(f"File uploaded: {file.filename} ({file_size} bytes)")
        
        return UploadResponse(
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=file_size
        )
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")

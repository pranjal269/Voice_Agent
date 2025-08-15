"""Text-to-Speech API endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models.schemas import TTSRequest, TTSResponse, ErrorResponse
from app.services.tts import tts_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])


@router.post("/generate", response_model=TTSResponse, summary="Generate Audio from Text")
async def generate_audio(request: TTSRequest):
    """
    Generate speech audio from text using Murf AI.
    
    - **text**: Text to convert to speech (max 5000 characters)
    - **voiceId**: Voice ID to use for generation (default: en-US-natalie)
    """
    try:
        if not tts_service.is_configured():
            logger.error("TTS service not configured")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "TTS service unavailable - API key not configured",
                    "fallback_text": request.text,
                    "service_type": "TTS"
                }
            )
        
        logger.info(f"TTS request for {len(request.text)} characters")
        
        audio_url = tts_service.generate_speech(request.text, request.voiceId)
        
        if audio_url:
            logger.info("TTS generation successful")
            return TTSResponse(
                audio_url=audio_url,
                text=request.text,
                voiceId=request.voiceId
            )
        else:
            logger.error("TTS generation failed")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Failed to generate audio",
                    "fallback_text": request.text,
                    "service_type": "TTS"
                }
            )
            
    except ValueError as e:
        logger.error(f"TTS validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"TTS endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

"""Large Language Model API endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
from app.models.schemas import LLMQueryRequest, LLMQueryResponse
from app.services.llm import llm_service
from app.services.stt import stt_service
from app.services.tts import tts_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["Large Language Model"])


@router.post("/query", response_model=LLMQueryResponse, summary="Query LLM with text or audio input")
async def llm_query(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    model: str = Form("gemini-1.5-flash"),
    temperature: float = Form(0.7),
    system_instruction: Optional[str] = Form(None),
    voiceId: str = Form("en-US-natalie")
):
    """
    Query the Large Language Model with either text or audio input.
    
    - **file**: Audio file to transcribe and process (optional)
    - **text**: Direct text input (optional, used if no file provided)
    - **model**: LLM model to use
    - **temperature**: Generation temperature (0.0 to 2.0)
    - **system_instruction**: System instruction for the model
    - **voiceId**: Voice ID for TTS response generation
    """
    try:
        if not llm_service.is_configured():
            logger.error("LLM service not configured")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "LLM service unavailable - API key not configured",
                    "service_type": "LLM"
                }
            )
        
        user_text = None
        
        # Process audio input if provided
        if file:
            if not stt_service.is_configured():
                logger.error("STT service not configured for audio input")
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "Transcription service unavailable for audio input",
                        "service_type": "STT"
                    }
                )
            
            # Validate audio format
            if not stt_service.validate_audio_format(file.content_type):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported audio format: {file.content_type}"
                )
            
            # Transcribe audio
            audio_data = await file.read()
            logger.info(f"Processing audio file: {file.filename} ({len(audio_data)} bytes)")
            
            user_text = stt_service.transcribe_audio(audio_data)
            if not user_text:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Transcription failed",
                        "service_type": "STT"
                    }
                )
        elif text:
            user_text = text.strip()
        else:
            raise HTTPException(
                status_code=400,
                detail="Either audio file or text input is required"
            )
        
        if not user_text:
            raise HTTPException(
                status_code=400,
                detail="No valid input text found"
            )
        
        logger.info(f"Processing LLM query: {user_text[:100]}...")
        
        # Generate LLM response
        llm_response = llm_service.generate_response(
            prompt=user_text,
            model=model,
            temperature=temperature,
            system_instruction=system_instruction
        )
        
        if not llm_response:
            error_type = "LLM_GENERAL_ERROR"
            fallback_message = llm_service.get_fallback_message(error_type)
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": fallback_message,
                    "error_type": error_type,
                    "service_type": "LLM"
                }
            )
        
        # Generate TTS audio for response (optional)
        audio_url = None
        tts_error = None
        
        if tts_service.is_configured():
            try:
                audio_url = tts_service.generate_speech(llm_response, voiceId)
                if not audio_url:
                    tts_error = "Audio generation failed"
                    logger.warning("TTS generation failed for LLM response")
            except Exception as e:
                tts_error = f"TTS error: {str(e)}"
                logger.warning(f"TTS generation error: {str(e)}")
        else:
            tts_error = "TTS service not configured"
        
        logger.info("LLM query processed successfully")
        
        response_data = {
            "transcription": user_text if file else None,
            "llm_response": llm_response,
            "audio_url": audio_url,
            "model": model,
            "voiceId": voiceId,
            "filename": file.filename if file else None
        }
        
        # Add TTS error if applicable
        if tts_error and not audio_url:
            response_data["tts_error"] = tts_error
        
        return LLMQueryResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

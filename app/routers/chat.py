"""Chat session API endpoints with conversation history."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from app.models.schemas import ChatRequest, ChatResponse, FallbackResponse
from app.services.llm import llm_service
from app.services.stt import stt_service
from app.services.tts import tts_service
from app.services.chat_session import chat_manager
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat Sessions"])


@router.post("/{session_id}", response_model=ChatResponse, summary="AI Chat with Session History")
async def chat_with_session(
    session_id: str,
    file: UploadFile = File(...),
    model: str = Form("gemini-1.5-flash"),
    temperature: float = Form(0.7),
    voiceId: str = Form("en-US-natalie")
):
    """
    AI Chat endpoint with session-based conversation history.
    Audio input → STT → Chat History → LLM → TTS → Audio Output
    
    - **session_id**: Unique session identifier for conversation continuity
    - **file**: Audio file with user's voice input
    - **model**: LLM model to use for generating responses
    - **temperature**: Generation temperature (0.0 to 2.0)
    - **voiceId**: Voice ID for TTS response generation
    """
    try:
        logger.info(f"Processing chat request for session: {session_id}")
        
        # Validate services
        if not llm_service.is_configured():
            logger.error("LLM service not configured")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "LLM service unavailable - API key not configured",
                    "service_type": "LLM"
                }
            )
        
        # Validate audio file
        if not stt_service.validate_audio_format(file.content_type):
            logger.error(f"Unsupported file type: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(stt_service.validate_audio_format.__defaults__[0])}"
            )
        
        # Transcribe audio
        audio_data = await file.read()
        logger.info(f"Transcribing audio: {file.filename} ({len(audio_data)} bytes)")
        
        if not stt_service.is_configured():
            logger.error("STT service not configured")
            fallback_message = "I'm having trouble understanding your audio right now. Please try speaking again or check your microphone."
            return await _generate_fallback_response(session_id, fallback_message, voiceId, "STT_ERROR")
        
        user_message = stt_service.transcribe_audio(audio_data)
        if not user_message:
            logger.error("Transcription failed")
            fallback_message = "I'm having trouble understanding your audio right now. Please try speaking again or check your microphone."
            return await _generate_fallback_response(session_id, fallback_message, voiceId, "STT_ERROR")
        
        logger.info(f"User message transcribed: {user_message[:100]}...")
        
        # Add user message to chat history
        chat_manager.add_message(session_id, "user", user_message)
        
        # Get conversation history and generate response
        conversation_history = chat_manager.get_session_history(session_id)
        logger.info(f"Generating response with {len(conversation_history)} messages in history")
        
        llm_response = llm_service.generate_conversational_response(
            conversation_history=conversation_history,
            model=model,
            temperature=temperature
        )
        
        if not llm_response:
            logger.error("LLM response generation failed")
            error_type = "LLM_GENERAL_ERROR"
            fallback_message = llm_service.get_fallback_message(error_type)
            return await _generate_fallback_response(session_id, fallback_message, voiceId, error_type)
        
        # Add assistant response to chat history
        chat_manager.add_message(session_id, "assistant", llm_response)
        
        logger.info(f"LLM response generated: {llm_response[:100]}...")
        
        # Generate TTS audio for the response
        audio_url = None
        tts_error = None
        
        if tts_service.is_configured():
            try:
                audio_url = tts_service.generate_speech(llm_response, voiceId)
                if audio_url:
                    logger.info("TTS audio generated successfully")
                else:
                    tts_error = "Audio generation failed"
                    logger.warning("TTS generation failed")
            except Exception as e:
                tts_error = f"TTS error: {str(e)}"
                logger.error(f"TTS generation error: {str(e)}")
        else:
            tts_error = "TTS service not configured"
            logger.warning("TTS service not configured")
        
        message_count = chat_manager.get_message_count(session_id)
        
        # Prepare response
        response_data = {
            "session_id": session_id,
            "model": model,
            "transcription": user_message,
            "llm_response": llm_response,
            "audio_url": audio_url,
            "voiceId": voiceId,
            "filename": file.filename,
            "message_count": message_count
        }
        
        # Add TTS error if applicable
        if tts_error and not audio_url:
            response_data["tts_error"] = tts_error
            response_data["error_type"] = "TTS_ERROR"
        
        logger.info(f"Chat response completed for session {session_id}")
        return ChatResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _generate_fallback_response(
    session_id: str, 
    message: str, 
    voice_id: str, 
    error_type: str
) -> JSONResponse:
    """Generate a fallback response when services fail."""
    logger.info(f"Generating fallback response for {error_type}")
    
    audio_url = None
    if tts_service.is_configured():
        try:
            audio_url = tts_service.generate_fallback_speech(message, voice_id)
            if audio_url:
                logger.info("Fallback TTS generated successfully")
        except Exception as e:
            logger.warning(f"Fallback TTS failed: {str(e)}")
    
    message_count = chat_manager.get_message_count(session_id)
    
    fallback_data = {
        "session_id": session_id,
        "error_type": error_type,
        "transcription": None,
        "llm_response": message,
        "audio_url": audio_url,
        "voiceId": voice_id,
        "is_fallback": True,
        "message_count": message_count
    }
    
    if audio_url:
        return JSONResponse(status_code=200, content=fallback_data)
    else:
        return JSONResponse(
            status_code=503,
            content={
                "error": message,
                "error_type": error_type,
                "fallback_text": message,
                "service_unavailable": True
            }
        )


@router.get("/{session_id}/history", summary="Get chat session history")
async def get_session_history(session_id: str):
    """
    Get conversation history for a specific session.
    
    - **session_id**: Unique session identifier
    """
    try:
        history = chat_manager.get_session_history(session_id)
        message_count = chat_manager.get_message_count(session_id)
        
        return {
            "session_id": session_id,
            "message_count": message_count,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session history")


@router.delete("/{session_id}", summary="Clear chat session")
async def clear_session(session_id: str):
    """
    Clear conversation history for a specific session.
    
    - **session_id**: Unique session identifier
    """
    try:
        success = chat_manager.clear_session(session_id)
        
        if success:
            logger.info(f"Session {session_id} cleared successfully")
            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear session")


@router.get("/stats", summary="Get chat statistics")
async def get_chat_stats():
    """Get statistics about all chat sessions."""
    try:
        stats = chat_manager.get_session_stats()
        active_sessions = chat_manager.get_active_sessions()
        
        return {
            "statistics": stats,
            "active_sessions": active_sessions
        }
        
    except Exception as e:
        logger.error(f"Error getting chat stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat statistics")

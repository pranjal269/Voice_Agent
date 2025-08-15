"""
AI Voice Agent - Refactored Application

A comprehensive voice agent with Text-to-Speech, Speech-to-Text, and LLM capabilities.
Refactored for better maintainability, readability, and separation of concerns.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path

# Import core modules
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

# Import routers
from app.routers import tts, stt, llm, chat

# Import services for initialization
from app.services.tts import tts_service
from app.services.stt import stt_service  
from app.services.llm import llm_service
from app.services.chat_session import chat_manager

# Setup logging
setup_logging(debug=settings.DEBUG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.VERSION} Starting Up...")
    logger.info("=" * 60)
    
    # Check API key configurations
    api_status = settings.get_api_status()
    for status in api_status:
        logger.info(status)
    
    # Check if all services are properly configured
    services_status = {
        "TTS": tts_service.is_configured(),
        "STT": stt_service.is_configured(),
        "LLM": llm_service.is_configured()
    }
    
    if not all(services_status.values()):
        logger.warning("=" * 60)
        logger.warning("⚠️  WARNING: Some services are not configured!")
        for service, configured in services_status.items():
            if not configured:
                logger.warning(f"   {service} service: Not configured")
        logger.warning("The application will use fallback responses for failed services.")
        logger.warning("=" * 60)
    else:
        logger.info("=" * 60)
        logger.info("✅ All services configured. Application ready!")
        logger.info("=" * 60)
    
    # Ensure upload directory exists
    upload_dir = Path(settings.UPLOAD_FOLDER)
    upload_dir.mkdir(exist_ok=True)
    logger.info(f"Upload directory ready: {upload_dir.absolute()}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="A comprehensive AI voice agent with TTS, STT, and LLM capabilities",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(tts.router)
app.include_router(stt.router)
app.include_router(llm.router)
app.include_router(chat.router, prefix="/agent")

# Legacy endpoints for backward compatibility
app.include_router(tts.router, prefix="/generate-audio", include_in_schema=False)


@app.get("/", summary="Homepage", tags=["Frontend"])
async def homepage(request: Request):
    """Serve the main application interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", summary="Health Check", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify system status.
    
    Returns service configuration status and basic system information.
    """
    services_status = {
        "tts": tts_service.is_configured(),
        "stt": stt_service.is_configured(),
        "llm": llm_service.is_configured()
    }
    
    chat_stats = chat_manager.get_session_stats()
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "services": services_status,
        "chat_statistics": chat_stats,
        "all_services_configured": all(services_status.values())
    }


@app.get("/api/info", summary="API Information", tags=["System"])
async def api_info():
    """
    Get API information and configuration details.
    
    Returns information about available endpoints and service status.
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug_mode": settings.DEBUG,
        "endpoints": {
            "tts": "/tts/generate",
            "stt": "/stt/transcribe", 
            "llm": "/llm/query",
            "chat": "/agent/chat/{session_id}",
            "health": "/health"
        },
        "supported_audio_formats": settings.ALLOWED_AUDIO_TYPES,
        "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024),
        "max_text_length": settings.MAX_TEXT_LENGTH
    }


# Legacy endpoint redirects for backward compatibility
@app.post("/upload-audio", include_in_schema=False)
async def legacy_upload_audio(*args, **kwargs):
    """Legacy endpoint redirect."""
    from app.routers.stt import upload_audio
    return await upload_audio(*args, **kwargs)


@app.post("/transcribe/file", include_in_schema=False) 
async def legacy_transcribe_file(*args, **kwargs):
    """Legacy endpoint redirect."""
    from app.routers.stt import transcribe_audio
    return await transcribe_audio(*args, **kwargs)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )

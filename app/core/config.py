"""Configuration management for the voice agent application."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # API Keys
    MURF_API_KEY: Optional[str] = os.getenv("MURF_API_KEY")
    ASSEMBLYAI_API_KEY: Optional[str] = os.getenv("ASSEMBLYAI_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    # App Configuration
    APP_NAME: str = "AI Voice Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # File Upload Settings
    UPLOAD_FOLDER: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_AUDIO_TYPES: list = [
        "audio/webm", "audio/wav", "audio/mp3", 
        "audio/m4a", "audio/ogg", "audio/opus"
    ]
    
    # API Settings
    REQUEST_TIMEOUT: int = 30
    TTS_TIMEOUT: int = 10
    MAX_TEXT_LENGTH: int = 5000
    MURF_MAX_CHARS: int = 3000
    
    # Recording Settings
    MAX_RECORDING_DURATION: int = 300  # 5 minutes in seconds
    
    def validate_api_keys(self) -> dict:
        """Validate which API keys are configured."""
        return {
            "murf": bool(self.MURF_API_KEY),
            "assemblyai": bool(self.ASSEMBLYAI_API_KEY),
            "gemini": bool(self.GEMINI_API_KEY)
        }
    
    def get_api_status(self) -> list:
        """Get human-readable API key status."""
        status = []
        
        if self.MURF_API_KEY:
            status.append("✅ Murf AI (TTS) API key configured")
        else:
            status.append("⚠️  Murf AI (TTS) API key missing - TTS will fail")
        
        if self.ASSEMBLYAI_API_KEY:
            status.append("✅ AssemblyAI (STT) API key configured")
        else:
            status.append("⚠️  AssemblyAI (STT) API key missing - Transcription will fail")
        
        if self.GEMINI_API_KEY:
            status.append("✅ Gemini (LLM) API key configured")
        else:
            status.append("⚠️  Gemini (LLM) API key missing - AI responses will fail")
        
        return status


# Create global settings instance
settings = Settings()

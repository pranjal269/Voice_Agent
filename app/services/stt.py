"""Speech-to-Text service using AssemblyAI."""

import assemblyai as aai
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class STTService:
    """Speech-to-Text service using AssemblyAI."""
    
    def __init__(self):
        self.api_key = settings.ASSEMBLYAI_API_KEY
        if self.api_key:
            aai.settings.api_key = self.api_key
            logger.info("AssemblyAI STT service initialized")
        else:
            logger.warning("AssemblyAI API key not configured")
    
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(self.api_key)
    
    def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio data to text using AssemblyAI.
        
        Args:
            audio_data: Raw audio data bytes
            
        Returns:
            Transcribed text, or None if failed
        """
        if not self.is_configured():
            logger.error("STT service not configured - missing API key")
            raise ValueError("STT service not configured")
        
        try:
            logger.info(f"Transcribing audio data ({len(audio_data)} bytes)")
            
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_data)
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"AssemblyAI transcription failed: {transcript.error}")
                return None
            
            transcribed_text = (transcript.text or "").strip()
            
            if not transcribed_text:
                logger.warning("Transcription returned empty result")
                return None
            
            logger.info(f"Transcription successful: '{transcribed_text[:100]}...'")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return None
    
    def validate_audio_format(self, content_type: str) -> bool:
        """
        Validate if the audio format is supported.
        
        Args:
            content_type: MIME type of the audio file
            
        Returns:
            True if format is supported, False otherwise
        """
        return content_type in settings.ALLOWED_AUDIO_TYPES


# Global STT service instance
stt_service = STTService()

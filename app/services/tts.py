"""Text-to-Speech service using Murf AI."""

import requests
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TTSService:
    """Text-to-Speech service using Murf AI."""
    
    def __init__(self):
        self.api_key = settings.MURF_API_KEY
        self.base_url = "https://api.murf.ai/v1/speech/generate"
        self.timeout = settings.TTS_TIMEOUT
        
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(self.api_key)
    
    def generate_speech(
        self, 
        text: str, 
        voice_id: str = "en-US-natalie"
    ) -> Optional[str]:
        """
        Generate speech from text using Murf AI.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use for generation
            
        Returns:
            URL to the generated audio file, or None if failed
        """
        if not self.is_configured():
            logger.error("TTS service not configured - missing API key")
            raise ValueError("TTS service not configured")
        
        # Truncate text if too long
        if len(text) > settings.MURF_MAX_CHARS:
            original_length = len(text)
            text = text[:settings.MURF_MAX_CHARS - 20] + "... (truncated)"
            logger.warning(
                f"Text truncated from {original_length} to {len(text)} chars for TTS"
            )
        
        payload = {
            "text": text,
            "voiceId": voice_id,
            "format": "mp3"
        }
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": self.api_key
        }
        
        try:
            logger.info(f"Generating TTS for {len(text)} characters with voice {voice_id}")
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                audio_url = data.get("audioFile")
                
                if audio_url:
                    logger.info(f"TTS generation successful: {audio_url}")
                    return audio_url
                else:
                    logger.error("TTS API did not return audioFile URL")
                    return None
            else:
                logger.error(
                    f"TTS API returned status {response.status_code}: {response.text}"
                )
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"TTS request timed out after {self.timeout} seconds")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("TTS connection error")
            return None
        except Exception as e:
            logger.error(f"TTS generation failed: {str(e)}")
            return None
    
    def generate_fallback_speech(
        self, 
        message: str, 
        voice_id: str = "en-US-natalie"
    ) -> Optional[str]:
        """
        Generate speech for fallback messages with shorter timeout.
        
        Args:
            message: Fallback message to convert to speech
            voice_id: Voice ID to use
            
        Returns:
            URL to the generated audio file, or None if failed
        """
        if not self.is_configured():
            return None
        
        payload = {
            "text": message,
            "voiceId": voice_id,
            "format": "mp3"
        }
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": self.api_key
        }
        
        try:
            logger.info(f"Generating fallback TTS: {message[:50]}...")
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=5  # Shorter timeout for fallback
            )
            
            if response.status_code == 200:
                data = response.json()
                audio_url = data.get("audioFile")
                
                if audio_url:
                    logger.info("Fallback TTS generation successful")
                    return audio_url
                    
        except Exception as e:
            logger.warning(f"Fallback TTS generation failed: {str(e)}")
        
        return None


# Global TTS service instance
tts_service = TTSService()

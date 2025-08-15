"""
Tests for the Voice Agent application.
Run with: python test_app.py
"""

import sys
import os

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.tts import tts_service
from app.services.stt import stt_service
from app.services.llm import llm_service
from app.services.chat_session import chat_manager


def test_settings_loaded():
    """Test that settings are properly loaded."""
    assert settings.APP_NAME == "AI Voice Agent"
    assert settings.VERSION == "1.0.0"
    assert isinstance(settings.ALLOWED_AUDIO_TYPES, list)
    assert len(settings.ALLOWED_AUDIO_TYPES) > 0


def test_tts_service_initialization():
    """Test TTS service initialization."""
    assert tts_service is not None
    # Test configuration check (should not raise error)
    is_configured = tts_service.is_configured()
    assert isinstance(is_configured, bool)


def test_stt_service_initialization():
    """Test STT service initialization."""
    assert stt_service is not None
    is_configured = stt_service.is_configured()
    assert isinstance(is_configured, bool)


def test_llm_service_initialization():
    """Test LLM service initialization."""
    assert llm_service is not None
    is_configured = llm_service.is_configured()
    assert isinstance(is_configured, bool)


def test_chat_manager_initialization():
    """Test chat manager initialization."""
    assert chat_manager is not None
    
    # Test session creation
    test_session = "test_session_123"
    history = chat_manager.get_session_history(test_session)
    assert history == []
    
    # Test adding messages
    chat_manager.add_message(test_session, "user", "Hello")
    chat_manager.add_message(test_session, "assistant", "Hi there!")
    
    history = chat_manager.get_session_history(test_session)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there!"
    
    # Test message count
    count = chat_manager.get_message_count(test_session)
    assert count == 2
    
    # Test session clearing
    success = chat_manager.clear_session(test_session)
    assert success is True
    
    history = chat_manager.get_session_history(test_session)
    assert history == []


def test_stt_audio_format_validation():
    """Test STT audio format validation."""
    # Valid formats
    assert stt_service.validate_audio_format("audio/webm") is True
    assert stt_service.validate_audio_format("audio/wav") is True
    assert stt_service.validate_audio_format("audio/mp3") is True
    
    # Invalid format
    assert stt_service.validate_audio_format("video/mp4") is False
    assert stt_service.validate_audio_format("text/plain") is False


def test_llm_error_type_classification():
    """Test LLM error type classification."""
    assert llm_service.get_error_type("quota exceeded") == "LLM_QUOTA_ERROR"
    assert llm_service.get_error_type("API key invalid") == "LLM_AUTH_ERROR"
    assert llm_service.get_error_type("network timeout") == "LLM_NETWORK_ERROR"
    assert llm_service.get_error_type("unknown error") == "LLM_GENERAL_ERROR"


def test_llm_fallback_messages():
    """Test LLM fallback message generation."""
    quota_msg = llm_service.get_fallback_message("LLM_QUOTA_ERROR")
    assert "limit" in quota_msg.lower()
    
    auth_msg = llm_service.get_fallback_message("LLM_AUTH_ERROR")
    assert "authentication" in auth_msg.lower()
    
    network_msg = llm_service.get_fallback_message("LLM_NETWORK_ERROR")
    assert "connect" in network_msg.lower()


def test_api_key_validation():
    """Test API key validation."""
    api_status = settings.validate_api_keys()
    assert isinstance(api_status, dict)
    assert "murf" in api_status
    assert "assemblyai" in api_status
    assert "gemini" in api_status


if __name__ == "__main__":
    # Run tests manually
    test_settings_loaded()
    test_tts_service_initialization()
    test_stt_service_initialization()
    test_llm_service_initialization()
    test_chat_manager_initialization()
    test_stt_audio_format_validation()
    test_llm_error_type_classification()
    test_llm_fallback_messages()
    test_api_key_validation()
    
    print("✅ All tests passed!")

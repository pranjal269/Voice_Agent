"""Request and response models for the voice agent API."""

from typing import Optional
from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Text-to-Speech request model."""
    text: str = Field(
        title="Text to Convert",
        description="Enter the text you want to convert to speech.",
        min_length=1,
        max_length=5000,
        example="Hello World"
    )
    voiceId: str = Field(
        default="en-US-natalie",
        title="Voice ID",
        description="Voice ID for the TTS generation.",
        example="en-US-natalie"
    )


class TTSResponse(BaseModel):
    """Text-to-Speech response model."""
    audio_url: str = Field(description="URL to the generated audio file")
    text: str = Field(description="Original text that was converted")
    voiceId: str = Field(description="Voice ID used for generation")
    service_type: str = Field(default="TTS", description="Service type identifier")


class TranscriptionRequest(BaseModel):
    """Speech-to-Text transcription request model."""
    file_content_type: str = Field(description="MIME type of the audio file")
    filename: str = Field(description="Name of the audio file")


class TranscriptionResponse(BaseModel):
    """Speech-to-Text transcription response model."""
    transcription: str = Field(description="Transcribed text from audio")
    filename: str = Field(description="Original filename")
    content_type: str = Field(description="MIME type of the audio file")
    size_bytes: int = Field(description="Size of the audio file in bytes")


class LLMQueryRequest(BaseModel):
    """Large Language Model query request model."""
    text: str = Field(min_length=1, example="Summarize the main features of this voice agent.")
    model: str = Field(default="gemini-1.5-flash", description="LLM model to use")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2, description="Model temperature")
    system_instruction: Optional[str] = Field(default=None, description="System instruction for the model")
    voiceId: str = Field(default="en-US-natalie", description="Voice ID for TTS generation")


class LLMQueryResponse(BaseModel):
    """Large Language Model query response model."""
    transcription: Optional[str] = Field(description="Transcribed input text")
    llm_response: str = Field(description="Generated response from LLM")
    audio_url: Optional[str] = Field(description="URL to generated audio response")
    model: str = Field(description="LLM model used")
    voiceId: str = Field(description="Voice ID used for TTS")
    filename: Optional[str] = Field(description="Original audio filename if applicable")


class ChatRequest(BaseModel):
    """Chat session request model."""
    model: str = Field(default="gemini-1.5-flash", description="LLM model to use")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Model temperature")
    voiceId: str = Field(default="en-US-natalie", description="Voice ID for TTS generation")


class ChatResponse(BaseModel):
    """Chat session response model."""
    session_id: str = Field(description="Unique session identifier")
    model: str = Field(description="LLM model used")
    transcription: str = Field(description="Transcribed user input")
    llm_response: str = Field(description="Generated AI response")
    audio_url: Optional[str] = Field(description="URL to generated audio response")
    voiceId: str = Field(description="Voice ID used for TTS")
    filename: str = Field(description="Original audio filename")
    message_count: int = Field(description="Total messages in this session")
    is_fallback: Optional[bool] = Field(default=False, description="Whether this is a fallback response")
    error_type: Optional[str] = Field(description="Error type if applicable")
    tts_error: Optional[str] = Field(description="TTS error message if applicable")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(description="Error message")
    error_type: Optional[str] = Field(description="Type of error")
    fallback_text: Optional[str] = Field(description="Fallback text if available")
    service_type: Optional[str] = Field(description="Service that failed")
    retry_suggestion: Optional[str] = Field(description="Suggestion for retry")
    timestamp: Optional[int] = Field(description="Error timestamp")
    original_error: Optional[str] = Field(description="Original error details")


class FallbackResponse(BaseModel):
    """Fallback response when services fail."""
    session_id: Optional[str] = Field(description="Session ID if applicable")
    error_type: str = Field(description="Type of error that triggered fallback")
    transcription: Optional[str] = Field(description="Transcribed input if available")
    llm_response: str = Field(description="Fallback message")
    audio_url: Optional[str] = Field(description="Fallback audio URL if generated")
    voiceId: str = Field(description="Voice ID used")
    is_fallback: bool = Field(default=True, description="Indicates this is a fallback response")
    message_count: int = Field(description="Messages in session")


class UploadResponse(BaseModel):
    """File upload response model."""
    filename: str = Field(description="Name of uploaded file")
    content_type: str = Field(description="MIME type of uploaded file")
    size_bytes: int = Field(description="Size of uploaded file in bytes")

# Voice Agent - AI-Powered Voice & Speech Processing Platform

## 📝 Day 14 Update: Refactored & Production-Ready! 

This project has been completely refactored for better maintainability, readability, and scalability. The codebase now follows best practices with proper separation of concerns, comprehensive logging, and modular architecture.

## Problem Statement
In today's digital landscape, there's a growing need for accessible and efficient voice-based interactions. Many users and developers face challenges with:
- Converting text to natural-sounding speech
- Recording and processing voice inputs
- Transcribing spoken content to text
- Managing audio files and transcriptions effectively
- Building conversational AI systems

## Project Overview
Voice Agent is a comprehensive web application that combines Text-to-Speech (TTS), Speech-to-Text (STT), and Large Language Model (LLM) capabilities for natural voice conversations with AI. The platform offers:

### Key Features
1. **Conversational AI Agent**
   - Natural voice conversations with AI using Google Gemini
   - Session-based conversation history
   - Automatic speech recognition and response generation
   - Fallback handling for service failures

2. **Text-to-Speech Generation**
   - Convert written text to natural-sounding speech using Murf AI
   - Support for multiple voices and languages
   - Real-time audio preview and playback
   - Character limit management (up to 5000 characters)

3. **Speech-to-Text Processing**
   - Convert recorded speech to text using AssemblyAI
   - Support for multiple audio formats (WebM, WAV, MP3, M4A, OGG, Opus)
   - Real-time transcription with error handling

4. **Professional UI/UX**
   - Clean, intuitive design with responsive feedback
   - Real-time recording controls with visual indicators
   - Session management and conversation history
   - Auto-recording for seamless conversations

### 🏗️ Refactored Architecture
The application now features a clean, modular architecture:

```
app/
├── core/               # Core configuration and utilities
│   ├── config.py      # Environment & settings management
│   └── logging.py     # Centralized logging setup
├── models/            # Pydantic models for request/response
│   └── schemas.py     # API schemas and validation
├── services/          # Third-party service integrations
│   ├── tts.py        # Murf AI Text-to-Speech service
│   ├── stt.py        # AssemblyAI Speech-to-Text service
│   ├── llm.py        # Google Gemini LLM service
│   └── chat_session.py # Session management
└── routers/           # API endpoint handlers
    ├── tts.py        # TTS endpoints
    ├── stt.py        # STT endpoints
    ├── llm.py        # LLM endpoints
    └── chat.py       # Chat session endpoints
```

### Technical Stack
- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **AI Services**: 
  - Google Gemini for LLM responses
  - Murf AI for Text-to-Speech
  - AssemblyAI for Speech-to-Text
- **Audio Processing**: WebAudio API, MediaRecorder API
- **Architecture**: Clean Architecture, Dependency Injection, Service Layer Pattern

### Key Improvements in Refactor
- ✅ **Pydantic Models**: Proper request/response validation and documentation
- ✅ **Service Layer**: Separated third-party integrations into dedicated services
- ✅ **Comprehensive Logging**: Structured logging with colored console output
- ✅ **Error Handling**: Robust error handling with fallback responses
- ✅ **Configuration Management**: Environment-based configuration
- ✅ **Session Management**: Proper conversation history handling
- ✅ **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- ✅ **Modular Routing**: Organized endpoints by feature

## Getting Started

### Prerequisites
- Python 3.11 or higher
- API keys for:
  - Google Gemini (GEMINI_API_KEY)
  - Murf AI (MURF_API_KEY) 
  - AssemblyAI (ASSEMBLYAI_API_KEY)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/pranjal269/Voice_Agent.git
   cd Voice_Agent
   ```

2. Set up environment variables in `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   MURF_API_KEY=your_murf_api_key
   ASSEMBLYAI_API_KEY=your_assemblyai_api_key
   DEBUG=false
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   # Main application
   python main.py
   
   # Or using uvicorn directly
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Open your browser and navigate to:
   - Main App: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## API Endpoints

### Core Endpoints
- `POST /tts/generate` - Generate speech from text
- `POST /stt/transcribe` - Transcribe audio to text
- `POST /llm/query` - Query LLM with text or audio
- `POST /agent/chat/{session_id}` - Conversational AI chat
- `GET /health` - System health check

### Legacy Compatibility
The refactored version maintains backward compatibility with the original endpoints. The original implementation is preserved in `main_original.py` for reference.

## Usage Examples

### Text-to-Speech
```bash
curl -X POST "http://localhost:8000/tts/generate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, this is a test!", "voiceId": "en-US-natalie"}'
```

### Speech-to-Text
```bash
curl -X POST "http://localhost:8000/stt/transcribe" \
     -F "file=@audio.wav"
```

### Conversational AI
```bash
curl -X POST "http://localhost:8000/agent/chat/my-session-123" \
     -F "file=@voice_input.webm" \
     -F "model=gemini-1.5-flash" \
     -F "temperature=0.7"
```

## Development

### Project Structure
```
voice-agent/
├── app/                    # Refactored application code
│   ├── core/              # Core utilities and configuration
│   │   ├── config.py      # Environment & settings management
│   │   └── logging.py     # Centralized logging setup
│   ├── models/            # Pydantic schemas for validation
│   │   └── schemas.py     # API request/response models
│   ├── services/          # Service layer for external APIs
│   │   ├── tts.py        # Murf AI Text-to-Speech service
│   │   ├── stt.py        # AssemblyAI Speech-to-Text service
│   │   ├── llm.py        # Google Gemini LLM service
│   │   └── chat_session.py # Session management
│   └── routers/           # API endpoint handlers
│       ├── tts.py        # TTS endpoints
│       ├── stt.py        # STT endpoints
│       ├── llm.py        # LLM endpoints
│       └── chat.py       # Chat session endpoints
├── static/                # Frontend assets
│   └── script.js         # Enhanced voice agent UI
├── templates/             # HTML templates
│   └── index.html        # Main application interface
├── uploads/               # File upload directory
├── main.py               # Main FastAPI application (refactored)
├── main_original.py      # Original implementation (reference)
├── test_app.py           # Application tests
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md            # This documentation
```

### Logging
The application includes comprehensive logging:
- Console output with colored formatting
- File logging to `logs/voice_agent.log`
- Different log levels for development and production

### Error Handling
- Graceful fallback responses when services fail
- Proper HTTP status codes and error messages
- Retry logic for transient failures

## Deployment

### Environment Variables
```env
# Required API Keys
GEMINI_API_KEY=your_google_gemini_api_key
MURF_API_KEY=your_murf_ai_api_key  
ASSEMBLYAI_API_KEY=your_assemblyai_api_key

# Optional Configuration
DEBUG=false
```

### Production Considerations
- Set `DEBUG=false` in production
- Configure CORS origins appropriately
- Use a reverse proxy (nginx) for static files
- Set up proper logging rotation
- Consider rate limiting for API endpoints

## API Documentation
Visit http://localhost:8000/docs for interactive API documentation powered by Swagger UI.

## Future Enhancements
- Support for additional voice models and languages
- Advanced audio editing features
- Batch processing capabilities
- Voice emotion detection
- Custom voice model training

---
Built with ❤️ by Pranjal | #30DaysOfCode

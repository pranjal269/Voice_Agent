# Voice Agent - AI-Powered Voice & Speech Processing Platform

## Problem Statement
In today's digital landscape, there's a growing need for accessible and efficient voice-based interactions. Many users and developers face challenges with:
- Converting text to natural-sounding speech
- Recording and processing voice inputs
- Transcribing spoken content to text
- Managing audio files and transcriptions effectively

## Project Overview
Voice Agent is a comprehensive web application that combines Text-to-Speech (TTS) and voice recording capabilities with advanced AI features. The platform offers:

### Key Features
1. **Text-to-Speech Generation**
   - Convert written text to natural-sounding speech
   - Support for multiple voices and languages
   - Real-time audio preview and playback
   - Character limit management (up to 5000 characters)

2. **Echo Bot & Voice Recording**
   - High-quality voice recording with noise suppression
   - Echo functionality for instant playback
   - Automatic audio file management
   - Recording duration control (up to 5 minutes)

3. **Voice Transcription**
   - Convert recorded speech to text using AssemblyAI
   - Support for multiple audio formats
   - Real-time transcription status updates

### Technical Stack
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Python with FastAPI
- **AI Services**: 
  - Murf AI for Text-to-Speech
  - AssemblyAI for Speech-to-Text
- **Audio Processing**: WebAudio API, MediaRecorder API

### Key Benefits
- **User-Friendly Interface**: Clean, intuitive design with responsive feedback
- **Real-Time Processing**: Immediate audio generation and playback
- **Cross-Platform Compatibility**: Works across different browsers and devices
- **Scalable Architecture**: Built with modern web technologies and APIs

## Getting Started
1. Clone the repository
2. Set up environment variables:
   - MURF_API_KEY for text-to-speech
   - ASSEMBLYAI_API_KEY for transcription
3. Install dependencies:
   ```bash
   pip install "fastapi[all]" python-dotenv requests assemblyai
   ```
4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Future Enhancements
- Support for additional voice models and languages
- Advanced audio editing features
- Batch processing capabilities
- Voice emotion detection
- Custom voice model training

---
Built with ❤️ by Pranjal | #30DaysOfCode

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import requests
import os
from dotenv import load_dotenv
from fastapi import UploadFile, File
import shutil
from pathlib import Path
import assemblyai as aai
from typing import Optional

# Try importing Gemini SDK
try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # Fallback if the package is not installed

# Load environment variables from .env file
load_dotenv()

# Load the API keys once at startup
MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Initialize AssemblyAI
aai.settings.api_key = ASSEMBLYAI_API_KEY

# Initialize Gemini
if genai is not None and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as _e:
        # Do not crash app on startup; endpoint will surface config errors
        pass

# FastAPI app setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Startup checks for API keys
@app.on_event("startup")
async def startup_event():
    """Check API keys on startup and provide warnings"""
    print("=" * 60)
    print("🚀 AI Voice Agent Starting Up...")
    print("=" * 60)
    
    # Check API keys and provide status
    api_status = []
    
    if MURF_API_KEY:
        api_status.append("✅ Murf AI (TTS) API key configured")
    else:
        api_status.append("⚠️  Murf AI (TTS) API key missing - TTS will fail")
    
    if ASSEMBLYAI_API_KEY:
        api_status.append("✅ AssemblyAI (STT) API key configured")
    else:
        api_status.append("⚠️  AssemblyAI (STT) API key missing - Transcription will fail")
    
    if GEMINI_API_KEY:
        api_status.append("✅ Gemini (LLM) API key configured")
    else:
        api_status.append("⚠️  Gemini (LLM) API key missing - AI responses will fail")
    
    for status in api_status:
        print(status)
    
    # Warn if any API is missing
    if not all([MURF_API_KEY, ASSEMBLYAI_API_KEY, GEMINI_API_KEY]):
        print("=" * 60)
        print("⚠️  WARNING: Some API keys are missing!")
        print("The application will use fallback responses for failed services.")
        print("=" * 60)
    else:
        print("=" * 60)
        print("✅ All API keys configured. Application ready!")
        print("=" * 60)

# In-memory chat history storage
# Format: {session_id: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
chat_history: dict = {}

# Fallback response generator
async def generate_fallback_response(session_id: str, message: str, voice_id: str, error_type: str):
    """Generate a fallback response when APIs fail"""
    try:
        # Try to generate TTS for the fallback message
        if MURF_API_KEY:
            murf_url = "https://api.murf.ai/v1/speech/generate"
            murf_payload = {
                "text": message,
                "voiceId": voice_id,
                "format": "mp3",
            }
            murf_headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": MURF_API_KEY,
            }
            
            # Add timeout for TTS fallback generation
            try:
                murf_response = requests.post(
                    murf_url, 
                    json=murf_payload, 
                    headers=murf_headers,
                    timeout=10  # 10 second timeout for fallback
                )
                
                if murf_response.status_code == 200:
                    murf_data = murf_response.json()
                    audio_url = murf_data.get("audioFile")
                    if audio_url:
                        print(f"✅ [Chat-{session_id}] Generated fallback audio for {error_type}")
                        return {
                            "session_id": session_id,
                            "error_type": error_type,
                            "transcription": None,
                            "llm_response": message,
                            "audio_url": audio_url,
                            "voiceId": voice_id,
                            "is_fallback": True,
                            "message_count": len(chat_history.get(session_id, []))
                        }
            except requests.exceptions.Timeout:
                print(f"⏱️ [Chat-{session_id}] Fallback TTS timed out")
            except requests.exceptions.ConnectionError:
                print(f"🌐 [Chat-{session_id}] Fallback TTS connection error")
                
    except Exception as tts_error:
        print(f"❌ [Chat-{session_id}] Fallback TTS also failed: {str(tts_error)}")
    
    # If TTS also fails, return text-only fallback
    return JSONResponse(
        status_code=503, 
        content={
            "error": message,
            "error_type": error_type,
            "fallback_text": message,
            "service_unavailable": True
        }
    )

# Homepage route
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Request model
class TTSRequest(BaseModel):
    text: str = Field(
        title="Text to Convert",
        description="Enter the text you want to convert to speech.",
        min_length=1,
        example="Hello World"
    )
    voiceId: str = Field(
        default="en-US-natalie",
        title="Voice ID",
        description="Voice ID for the TTS generation.",
        example="en-US-natalie"
    )

# LLM request model
class LLMQueryRequest(BaseModel):
    text: str = Field(min_length=1, example="Summarize Echo Bot v2.")
    model: str = Field(default="gemini-1.5-flash")
    temperature: Optional[float] = Field(default=0.8, ge=0, le=2)
    system_instruction: Optional[str] = Field(default=None)
    voiceId: str = Field(default="en-US-natalie")

# TTS audio generation endpoint
@app.post("/generate-audio", summary="Generate Audio from Text", tags=["Text-to-Speech"])
async def generate_audio(req: TTSRequest):
    try:
        if not MURF_API_KEY:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "TTS service unavailable - API key not configured",
                    "fallback_text": req.text
                }
            )
        
        url = "https://api.murf.ai/v1/speech/generate"
        payload = {
            "text": req.text,
            "voiceId": req.voiceId,
            "format": "mp3"
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": MURF_API_KEY
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            audio_url = data.get("audioFile")
            if audio_url:
                print("✅ Murf API Response:", data)
                return {"audio_url": audio_url}
            else:
                raise Exception("Murf API did not return an audio URL")
        else:
            raise Exception(f"Murf API error {response.status_code}: {response.text}")
            
    except Exception as e:
        error_str = str(e)
        print(f"❌ TTS Error: {error_str}")
        
        # Return error with fallback text
        if "timeout" in error_str.lower():
            error_message = "Audio generation timed out. Please try again."
        elif "api key" in error_str.lower() or "authentication" in error_str.lower():
            error_message = "TTS service authentication failed."
        elif "network" in error_str.lower() or "connection" in error_str.lower():
            error_message = "Network error connecting to TTS service."
        else:
            error_message = "Audio generation failed. Please try again."
            
        return JSONResponse(
            status_code=503,
            content={
                "error": error_message,
                "fallback_text": req.text,
                "service_type": "TTS"
            }
        )

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

@app.post("/upload-audio", summary="Upload audio recording", tags=["Echo Bot"])
async def upload_audio(file: UploadFile = File(...)):
    try:
        file_location = UPLOAD_FOLDER / file.filename

        # Save the uploaded file
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Get file size
        file_size = file_location.stat().st_size

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": file_size
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/transcribe/file", summary="Transcribe audio file", tags=["Transcription"])
async def transcribe_file(file: UploadFile = File(...)):
    """
    Transcribe an audio file using AssemblyAI.
    Accepts audio file and returns transcription.
    """
    try:
        # Validate file type
        allowed_types = ["audio/webm", "audio/wav", "audio/mp3", "audio/m4a", "audio/ogg"]
        if file.content_type not in allowed_types:
            return JSONResponse(
                status_code=400, 
                content={"error": f"Unsupported file type: {file.content_type}. Allowed types: {allowed_types}"}
            )

        # Read the file content into memory
        audio_data = await file.read()
        
        print(f"Starting transcription for file: {file.filename}")
        print(f"File size: {len(audio_data)} bytes")
        print(f"Content type: {file.content_type}")

        # Initialize the transcriber
        transcriber = aai.Transcriber()
        
        # Transcribe the audio data directly (no need to save to disk)
        transcript = transcriber.transcribe(audio_data)
        
        # Check if transcription was successful
        if transcript.status == aai.TranscriptStatus.error:
            print(f"❌ Transcription failed: {transcript.error}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Transcription failed: {transcript.error}"}
            )
        
        # Get the transcription text
        transcription_text = transcript.text
        
        print(f" Transcription successful!")
        print(f"Transcription: {transcription_text}")
        
        return {
            "transcription": transcription_text,
            "confidence": transcript.confidence if hasattr(transcript, 'confidence') else None,
            "audio_duration": transcript.audio_duration if hasattr(transcript, 'audio_duration') else None,
            "filename": file.filename
        }
        
    except Exception as e:
        print(f"❌ Transcription error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to transcribe audio: {str(e)}"}
        )

@app.post("/tts/echo", summary="Echo audio with Murf voice (transcribe then TTS)", tags=["Echo Bot"]) 
async def tts_echo(file: UploadFile = File(...)):
    try:
        allowed_types = [
            "audio/webm",
            "audio/wav",
            "audio/mp3",
            "audio/m4a",
            "audio/ogg",
            "audio/opus",
        ]
        if file.content_type not in allowed_types:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Unsupported file type: {file.content_type}. Allowed types: {allowed_types}"
                },
            )

        audio_data = await file.read()
        print(f"[Echo] Received audio '{file.filename}' ({len(audio_data)} bytes, {file.content_type})")

        # 1) Transcribe with AssemblyAI (with enhanced error handling)
        transcription_text = None
        try:
            if not ASSEMBLYAI_API_KEY:
                raise Exception("AssemblyAI API key not configured")
                
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_data)

            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")

            transcription_text = (transcript.text or "").strip()
            if not transcription_text:
                raise Exception("Empty transcription result")
                
        except Exception as stt_error:
            print(f"❌ [Echo] STT Error: {str(stt_error)}")
            
            # Generate fallback audio response for STT failure
            fallback_message = "I'm having trouble understanding your audio right now. Please try speaking clearly or check your microphone."
            
            if MURF_API_KEY:
                try:
                    murf_url = "https://api.murf.ai/v1/speech/generate"
                    murf_payload = {
                        "text": fallback_message,
                        "voiceId": "en-US-natalie",
                        "format": "mp3",
                    }
                    murf_headers = {
                        "accept": "application/json",
                        "content-type": "application/json",
                        "api-key": MURF_API_KEY,
                    }
                    murf_response = requests.post(murf_url, json=murf_payload, headers=murf_headers, timeout=10)
                    
                    if murf_response.status_code == 200:
                        murf_data = murf_response.json()
                        audio_url = murf_data.get("audioFile")
                        if audio_url:
                            return {
                                "audio_url": audio_url,
                                "transcription": None,
                                "error_message": fallback_message,
                                "error_type": "STT_ERROR",
                                "voiceId": "en-US-natalie",
                                "filename": file.filename,
                            }
                except Exception:
                    pass
            
            return JSONResponse(
                status_code=500,
                content={"error": fallback_message, "error_type": "STT_ERROR"},
            )

        print(f"✅ [Echo] Transcription: {transcription_text}")

        # 2) Generate TTS with Murf (with enhanced error handling)
        try:
            if not MURF_API_KEY:
                raise Exception("Murf API key not configured")
                
            murf_url = "https://api.murf.ai/v1/speech/generate"
            murf_payload = {
                "text": transcription_text,
                "voiceId": "en-US-natalie",
                "format": "mp3",
            }
            murf_headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": MURF_API_KEY,
            }
            murf_response = requests.post(murf_url, json=murf_payload, headers=murf_headers, timeout=30)

            if murf_response.status_code != 200:
                raise Exception(f"Murf API returned status {murf_response.status_code}: {murf_response.text}")

            murf_data = murf_response.json()
            audio_url = murf_data.get("audioFile")
            if not audio_url:
                raise Exception("Murf API did not return an audioFile URL")

            print(f"✅ [Echo] Murf audio URL: {audio_url}")
            return {
                "audio_url": audio_url,
                "transcription": transcription_text,
                "voiceId": "en-US-natalie",
                "filename": file.filename,
            }
            
        except Exception as tts_error:
            print(f"❌ [Echo] TTS Error: {str(tts_error)}")
            
            # Return transcription even if TTS fails
            return JSONResponse(
                status_code=503,
                content={
                    "transcription": transcription_text,
                    "error": "Audio generation failed. Displaying text only.",
                    "error_type": "TTS_ERROR"
                }
            )

    except Exception as e:
        print(f"❌ [Echo] Unexpected Error: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={
                "error": "An unexpected error occurred. Please try again.",
                "error_details": str(e)
            }
        )

@app.post("/llm/query", summary="Query LLM (Gemini) with audio/text input", tags=["LLM"]) 
async def llm_query(
    request: Request,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = None,
    model: str = "gemini-1.5-flash",
    temperature: float = 0.8,
    system_instruction: Optional[str] = None,
    voiceId: str = "en-US-natalie"
):
    """
    Call Google's Gemini API to generate a response for audio or text input.
    If audio file is provided, transcribe it first, then send to LLM, then convert response to speech.
    If text is provided, send directly to LLM and return text response.
    """
    if genai is None:
        return JSONResponse(
            status_code=500,
            content={"error": "google-generativeai is not installed. Run: pip install google-generativeai"},
        )
    if not GEMINI_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "Missing GEMINI_API_KEY or GOOGLE_API_KEY in environment."},
        )
    
    try:
        # Handle JSON request body for text-only queries
        if file is None and text is None:
            try:
                body = await request.json()
                text = body.get("text")
                model = body.get("model", model)
                temperature = body.get("temperature", temperature)
                system_instruction = body.get("system_instruction", system_instruction)
                voiceId = body.get("voiceId", voiceId)
            except Exception:
                pass  # Not JSON, continue with form data
        
        input_text = text
        transcription = None
        
        # If audio file is provided, transcribe it first
        if file is not None:
            allowed_types = [
                "audio/webm", "audio/wav", "audio/mp3", "audio/m4a", "audio/ogg", "audio/opus"
            ]
            if file.content_type not in allowed_types:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Unsupported file type: {file.content_type}. Allowed types: {allowed_types}"}
                )
            
            audio_data = await file.read()
            print(f"[LLM] Transcribing audio '{file.filename}' ({len(audio_data)} bytes)")
            
            # Transcribe with AssemblyAI
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_data)
            
            if transcript.status == aai.TranscriptStatus.error:
                print(f"❌ [LLM] Transcription failed: {transcript.error}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Transcription failed: {transcript.error}"}
                )
            
            transcription = (transcript.text or "").strip()
            if not transcription:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Empty transcription. Please try recording again."}
                )
            
            input_text = transcription
            print(f"✅ [LLM] Transcription: {transcription}")
        
        if not input_text:
            return JSONResponse(
                status_code=400,
                content={"error": "Either 'file' (audio) or 'text' parameter is required."}
            )
        
        # Generate LLM response (with enhanced error handling)
        print(f"[LLM] Sending to Gemini: {input_text[:100]}...")
        try:
            if not GEMINI_API_KEY:
                raise Exception("Gemini API key not configured")
            
            if genai is None:
                raise Exception("Google Generative AI package not available")
                
            model_instance = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction if system_instruction else None,
            )
            generation_config = {"temperature": temperature}
            result = model_instance.generate_content(input_text, generation_config=generation_config)
            
            llm_response = getattr(result, "text", None)
            if not llm_response:
                # Fallback: some SDK versions expose candidates/parts
                try:
                    candidates = getattr(result, "candidates", []) or []
                    llm_response = "\n".join(
                        part.text
                        for c in candidates
                        for part in getattr(getattr(c, "content", {}), "parts", [])
                        if hasattr(part, "text")
                    )
                except Exception:
                    llm_response = ""
                    
            if not llm_response:
                raise Exception("LLM returned empty response")
                
        except Exception as e:
            error_str = str(e)
            print(f"❌ [LLM] Error: {error_str}")
            
            # Provide appropriate fallback response based on error type
            if "quota" in error_str.lower() or "429" in error_str:
                llm_response = "I've reached my daily conversation limit. Please try again tomorrow, or consider upgrading for unlimited conversations!"
            elif "api key" in error_str.lower() or "authentication" in error_str.lower():
                llm_response = "I'm having authentication issues right now. Please try again in a few moments."
            elif "network" in error_str.lower() or "connection" in error_str.lower() or "timeout" in error_str.lower():
                llm_response = "I'm having trouble connecting to my AI brain right now. Please try again in a moment!"
            else:
                llm_response = "I'm experiencing some technical difficulties right now. Please try asking your question again!"
            
            print(f"⚠️ [LLM] Using fallback response: {llm_response[:50]}...")
        
        if not llm_response:
            return JSONResponse(
                status_code=500,
                content={"error": "LLM returned empty response"}
            )
        
        print(f"✅ [LLM] Response: {llm_response[:100]}...")
        
        # If audio was provided, convert LLM response to speech
        if file is not None:
            # Truncate response if it's too long for Murf (3000 char limit)
            if len(llm_response) > 3000:
                llm_response = llm_response[:2980] + "... (truncated)"
                print(f"⚠️ [LLM] Response truncated to fit Murf 3000 char limit")
            
            # Generate TTS with Murf
            murf_url = "https://api.murf.ai/v1/speech/generate"
            murf_payload = {
                "text": llm_response,
                "voiceId": voiceId,
                "format": "mp3",
            }
            murf_headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": MURF_API_KEY,
            }
            murf_response = requests.post(murf_url, json=murf_payload, headers=murf_headers)
            
            if murf_response.status_code != 200:
                print(f"❌ [LLM] Murf API Error: {murf_response.text}")
                return JSONResponse(
                    status_code=murf_response.status_code,
                    content={"error": f"Murf TTS failed: {murf_response.text}"}
                )
            
            murf_data = murf_response.json()
            audio_url = murf_data.get("audioFile")
            if not audio_url:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Murf API did not return an audioFile URL."}
                )
            
            print(f"✅ [LLM] Murf audio URL: {audio_url}")
            return {
                "model": model,
                "transcription": transcription,
                "llm_response": llm_response,
                "audio_url": audio_url,
                "voiceId": voiceId,
                "filename": file.filename if file else None
            }
        else:
            # Text-only request, return text response
            return {"model": model, "response": llm_response}
    
    except Exception as e:
        print(f"❌ [LLM] Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/agent/chat/{session_id}", summary="AI Chat with Session History", tags=["AI Chat"])
async def agent_chat(
    session_id: str,
    file: UploadFile = File(...),
    model: str = "gemini-1.5-flash", 
    temperature: float = 0.7,
    voiceId: str = "en-US-natalie"
):
    """
    AI Chat endpoint with session-based conversation history.
    Audio input -> STT -> Chat History -> LLM -> TTS -> Audio Output
    """
    if genai is None:
        return JSONResponse(
            status_code=500,
            content={"error": "google-generativeai is not installed. Run: pip install google-generativeai"},
        )
    if not GEMINI_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "Missing GEMINI_API_KEY or GOOGLE_API_KEY in environment."},
        )
    
    try:
        # Validate audio file
        allowed_types = [
            "audio/webm", "audio/wav", "audio/mp3", "audio/m4a", "audio/ogg", "audio/opus"
        ]
        if file.content_type not in allowed_types:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unsupported file type: {file.content_type}. Allowed types: {allowed_types}"}
            )
        
        # Read audio data
        audio_data = await file.read()
        print(f"[Chat-{session_id}] Received audio '{file.filename}' ({len(audio_data)} bytes)")
        
        # Transcribe audio with AssemblyAI (with error handling)
        user_message = None
        try:
            if not ASSEMBLYAI_API_KEY:
                raise Exception("AssemblyAI API key not configured")
                
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_data)
            
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"AssemblyAI transcription failed: {transcript.error}")
            
            user_message = (transcript.text or "").strip()
            if not user_message:
                raise Exception("Empty transcription result")
                
        except Exception as stt_error:
            print(f"❌ [Chat-{session_id}] STT Error: {str(stt_error)}")
            # Fallback: Return error with fallback audio
            fallback_message = "I'm having trouble understanding your audio right now. Please try speaking again or check your microphone."
            return await generate_fallback_response(session_id, fallback_message, voiceId, "STT_ERROR")
        
        print(f"✅ [Chat-{session_id}] User said: {user_message}")
        
        # Get or initialize chat history for this session
        if session_id not in chat_history:
            chat_history[session_id] = []
        
        # Add user message to chat history
        chat_history[session_id].append({"role": "user", "content": user_message})
        
        # Prepare conversation context for LLM
        conversation_text = ""
        for msg in chat_history[session_id]:
            if msg["role"] == "user":
                conversation_text += f"User: {msg['content']}\n"
            else:
                conversation_text += f"Assistant: {msg['content']}\n"
        
        conversation_text += "Assistant:"
        
        print(f"[Chat-{session_id}] Sending conversation context to Gemini...")
        
        # Generate LLM response with conversation context (with enhanced error handling)
        llm_response = None
        try:
            if not GEMINI_API_KEY:
                raise Exception("Gemini API key not configured")
            
            if genai is None:
                raise Exception("Google Generative AI package not available")
                
            model_instance = genai.GenerativeModel(
                model_name=model,
                system_instruction="You are a helpful AI assistant. Respond naturally and remember the conversation context."
            )
            generation_config = {"temperature": temperature}
            result = model_instance.generate_content(conversation_text, generation_config=generation_config)
            
            llm_response = getattr(result, "text", None)
            if not llm_response:
                # Fallback for different SDK versions
                try:
                    candidates = getattr(result, "candidates", []) or []
                    llm_response = "\n".join(
                        part.text
                        for c in candidates
                        for part in getattr(getattr(c, "content", {}), "parts", [])
                        if hasattr(part, "text")
                    )
                except Exception:
                    llm_response = ""
                    
            if not llm_response:
                raise Exception("LLM returned empty response")
                
        except Exception as llm_error:
            error_str = str(llm_error)
            print(f"❌ [Chat-{session_id}] LLM Error: {error_str}")
            
            # Determine error type and provide appropriate fallback
            if "quota" in error_str.lower() or "429" in error_str:
                fallback_message = "I've reached my daily conversation limit. Please try again tomorrow, or consider upgrading for unlimited conversations!"
                return await generate_fallback_response(session_id, fallback_message, voiceId, "LLM_QUOTA_ERROR")
            elif "api key" in error_str.lower() or "authentication" in error_str.lower():
                fallback_message = "I'm having authentication issues right now. Please try again in a few moments."
                return await generate_fallback_response(session_id, fallback_message, voiceId, "LLM_AUTH_ERROR")
            elif "network" in error_str.lower() or "connection" in error_str.lower() or "timeout" in error_str.lower():
                fallback_message = "I'm having trouble connecting to my AI brain right now. Please try again in a moment!"
                return await generate_fallback_response(session_id, fallback_message, voiceId, "LLM_NETWORK_ERROR")
            else:
                fallback_message = "I'm experiencing some technical difficulties right now. Please try asking your question again!"
                return await generate_fallback_response(session_id, fallback_message, voiceId, "LLM_GENERAL_ERROR")
        
        # Add LLM response to chat history
        chat_history[session_id].append({"role": "assistant", "content": llm_response})
        
        print(f"✅ [Chat-{session_id}] AI responded: {llm_response[:100]}...")
        
        # Generate TTS audio for the response (with enhanced error handling)
        audio_url = None
        try:
            if not MURF_API_KEY:
                raise Exception("Murf API key not configured")
                
            # Truncate response if too long for Murf
            tts_text = llm_response
            if len(tts_text) > 3000:
                tts_text = tts_text[:2980] + "... (truncated for audio)"
                print(f"⚠️ [Chat-{session_id}] Response truncated to fit Murf 3000 char limit")
            
            murf_url = "https://api.murf.ai/v1/speech/generate"
            murf_payload = {
                "text": tts_text,
                "voiceId": voiceId,
                "format": "mp3",
            }
            murf_headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": MURF_API_KEY,
            }
            
            murf_response = requests.post(murf_url, json=murf_payload, headers=murf_headers, timeout=30)
            
            if murf_response.status_code != 200:
                raise Exception(f"Murf API returned status {murf_response.status_code}: {murf_response.text}")
            
            murf_data = murf_response.json()
            audio_url = murf_data.get("audioFile")
            if not audio_url:
                raise Exception("Murf API did not return an audioFile URL")
                
        except Exception as tts_error:
            error_str = str(tts_error)
            print(f"❌ [Chat-{session_id}] TTS Error: {error_str}")
            
            # TTS failed, but we still have the text response - return text-only response
            print(f"⚠️ [Chat-{session_id}] Returning text-only response due to TTS failure")
            return {
                "session_id": session_id,
                "model": model,
                "transcription": user_message,
                "llm_response": llm_response,
                "audio_url": None,
                "voiceId": voiceId,
                "filename": file.filename,
                "message_count": len(chat_history[session_id]),
                "tts_error": "Audio generation failed, displaying text response only",
                "error_type": "TTS_ERROR"
            }
        
        print(f"✅ [Chat-{session_id}] Generated audio URL: {audio_url}")
        
        return {
            "session_id": session_id,
            "model": model,
            "transcription": user_message,
            "llm_response": llm_response,
            "audio_url": audio_url,
            "voiceId": voiceId,
            "filename": file.filename,
            "message_count": len(chat_history[session_id])
        }
        
    except Exception as e:
        print(f"❌ [Chat-{session_id}] Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
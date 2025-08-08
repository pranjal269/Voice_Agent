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

# Load environment variables from .env file
load_dotenv()

# Load the API keys once at startup
MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# Initialize AssemblyAI
aai.settings.api_key = ASSEMBLYAI_API_KEY

# FastAPI app setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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

# TTS audio generation endpoint
@app.post("/generate-audio", summary="Generate Audio from Text", tags=["Text-to-Speech"])
async def generate_audio(req: TTSRequest):
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

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("✅ Murf API Response:", data)
        return {"audio_url": data.get("audioFile")}
    else:
        print("❌ Murf API Error:", response.text)
        return JSONResponse(status_code=response.status_code, content={"error": response.text})

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
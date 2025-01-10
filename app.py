# app.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
import io
import base64
from pydub import AudioSegment
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables if .env exists
load_dotenv(override=True)

# Access environment variables - Koyeb will provide these
ULTRAVOX_API_KEY = os.getenv("ULTRAVOX_API_KEY")
ULTRAVOX_URL = os.getenv("ULTRAVOX_URL")

app = FastAPI(
    title="UltraVox Audio Service",
    description="A service for handling audio transcription and responses using UltraVox API",
    version="1.0.0"
)

# Enable CORS for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aaas-automations.github.io",  # Your GitHub Pages domain
        "http://localhost:3000",  # For local development
        "http://127.0.0.1:5500",  # For VS Code Live Server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return {"status": "healthy", "service": "UltraVox Audio Service"}

@app.post("/transcribe_and_reply/")
async def transcribe_and_reply(file: UploadFile = File(...)):
    """Endpoint to handle audio transcription and response generation"""
    logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
    
    try:
        # Read the uploaded file
        logger.debug("Reading uploaded file")
        audio_bytes = await file.read()
        logger.info(f"Read {len(audio_bytes)} bytes from uploaded file")
        
        # Log file details
        logger.debug(f"File content first 100 bytes (hex): {audio_bytes[:100].hex()}")
        
        # Validate and convert the file to WAV using pydub
        try:
            logger.debug("Attempting to convert audio with pydub")
            # Explicitly specify format as webm
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
            logger.info(f"Audio properties - Channels: {audio.channels}, Sample width: {audio.sample_width}, Frame rate: {audio.frame_rate}, Duration: {len(audio)}ms")
        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")
            return JSONResponse(
                content={
                    "error": "Invalid audio file",
                    "details": str(e),
                    "content_type": file.content_type,
                    "file_size": len(audio_bytes)
                },
                status_code=400
            )

        # Convert audio to WAV format with specific parameters
        logger.debug("Converting to WAV format")
        buffer = io.BytesIO()
        # Set specific audio properties before export
        audio = audio.set_channels(1)  # Convert to mono
        audio = audio.set_frame_rate(16000)  # Set sample rate to 16kHz
        audio.export(buffer, format="wav", parameters=[
            "-acodec", "pcm_s16le",  # Use standard 16-bit PCM codec
            "-ac", "1",              # Mono
            "-ar", "16000"           # 16kHz sample rate
        ])
        buffer.seek(0)
        wav_bytes = buffer.read()
        logger.info(f"Converted WAV size: {len(wav_bytes)} bytes")

        # Encode as Base64
        audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")
        logger.info(f"Base64 encoded length: {len(audio_base64)}")

        # Prepare UltraVox payload for Baseten
        payload = {
            "audio": audio_base64,
            "text": "For like Michigan"
        }

        # Make request to UltraVox API
        logger.debug("Checking UltraVox configuration")
        
        if not ULTRAVOX_API_KEY:
            logger.error("ULTRAVOX_API_KEY not configured")
            return JSONResponse(
                content={"error": "ULTRAVOX_API_KEY not configured"},
                status_code=500
            )
            
        if not ULTRAVOX_URL:
            logger.error("ULTRAVOX_URL not configured")
            return JSONResponse(
                content={"error": "ULTRAVOX_URL not configured"},
                status_code=500
            )
            
        logger.debug(f"Sending request to UltraVox API at {ULTRAVOX_URL}")
        headers = {
            "Authorization": f"Api-Key {ULTRAVOX_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            ULTRAVOX_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"UltraVox API response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"UltraVox API error response: {response.text}")
            return JSONResponse(
                content={
                    "error": "Failed to connect to UltraVox API",
                    "details": response.text
                },
                status_code=response.status_code
            )

        # Get response audio
        response_data = response.json()
        logger.debug(f"API response structure: {response_data.keys()}")
        response_audio_base64 = response_data.get("audio")
        
        if not response_audio_base64:
            logger.error("No audio in UltraVox response")
            return JSONResponse(
                content={"error": "No audio response received from UltraVox"},
                status_code=500
            )

        # Decode response audio
        try:
            response_audio = base64.b64decode(response_audio_base64)
            logger.info(f"Decoded response audio size: {len(response_audio)} bytes")
        except Exception as e:
            logger.error(f"Error decoding response audio: {str(e)}")
            return JSONResponse(
                content={
                    "error": "Failed to decode audio response",
                    "details": str(e)
                },
                status_code=500
            )

        # Return audio response
        audio_io = io.BytesIO(response_audio)
        logger.info("Sending audio response")
        return FileResponse(
            audio_io,
            media_type="audio/wav",
            filename="response.wav",
            headers={
                "Content-Disposition": "attachment; filename=response.wav"
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "error": "An unexpected error occurred",
                "details": str(e)
            },
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
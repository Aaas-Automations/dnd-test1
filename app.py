# app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.logger import logger as fastapi_logger
from dotenv import load_dotenv
import os
import requests
import io
import base64
from pydub import AudioSegment
import logging
import json
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Environment variables
ULTRAVOX_API_KEY = os.getenv("ULTRAVOX_API_KEY")
ULTRAVOX_URL = os.getenv("ULTRAVOX_URL")
DEFAULT_PROMPT = os.getenv("DEFAULT_PROMPT", "For like Michigan")

# Validate required environment variables
if not ULTRAVOX_API_KEY:
    raise ValueError("ULTRAVOX_API_KEY environment variable is required")
if not ULTRAVOX_URL:
    raise ValueError("ULTRAVOX_URL environment variable is required")

app = FastAPI(
    title="UltraVox Audio Service",
    description="A service for handling audio transcription and responses using UltraVox API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aaas-automations.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AudioProcessingError(Exception):
    """Custom exception for audio processing errors"""
    pass

async def process_audio_file(file_bytes: bytes, content_type: str) -> tuple[bytes, dict]:
    """
    Process uploaded audio file and convert to required format
    Returns: (processed_audio_bytes, audio_info)
    """
    try:
        # Load audio file using pydub
        audio = AudioSegment.from_file(io.BytesIO(file_bytes), format="webm")
        
        # Log audio properties
        audio_info = {
            "channels": audio.channels,
            "sample_width": audio.sample_width,
            "frame_rate": audio.frame_rate,
            "duration_ms": len(audio)
        }
        logger.info(f"Audio properties: {audio_info}")

        # Convert to required format (16kHz mono WAV)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        
        # Export to WAV
        buffer = io.BytesIO()
        audio.export(buffer, format="wav", parameters=[
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "16000"
        ])
        buffer.seek(0)
        return buffer.read(), audio_info

    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}", exc_info=True)
        raise AudioProcessingError(f"Failed to process audio: {str(e)}")


async def call_ultravox_api(audio_base64: str) -> tuple[bytes, dict]:
    """
    Call UltraVox API with the processed audio
    Returns: (response_audio_bytes, response_info)
    """
    try:
        # Structure payload according to API requirements
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": f"content: {DEFAULT_PROMPT}\naudio_data: {audio_base64}"
                }
            ]
        }

        headers = {
            "Authorization": f"Api-Key {ULTRAVOX_API_KEY}",
            "Content-Type": "application/json"
        }

        logger.debug(f"Sending request to UltraVox API with payload structure: {payload.keys()}")
        
        response = requests.post(
            ULTRAVOX_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            error_detail = None
            try:
                error_detail = response.json()
                logger.error(f"UltraVox API error detail: {error_detail}")
            except:
                error_detail = response.text
                logger.error(f"UltraVox API error text: {error_detail}")

            raise HTTPException(
                status_code=response.status_code,
                detail=f"UltraVox API error: {error_detail}"
            )

        response_data = response.json()
        
        # Extract audio response carefully
        if not isinstance(response_data, dict):
            raise ValueError(f"Unexpected response format: {type(response_data)}")
            
        response_audio = response_data.get("audio")
        if not response_audio:
            raise ValueError("No audio in UltraVox response")

        return base64.b64decode(response_audio), response_data

    except requests.RequestException as e:
        logger.error(f"Request error to UltraVox API: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"UltraVox API connection error: {str(e)}")
    
@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "UltraVox Audio Service",
        "version": "1.0.0"
    }

@app.post("/transcribe_and_reply/")
async def transcribe_and_reply(file: UploadFile = File(...)):
    """
    Process audio file and get response from UltraVox
    """
    try:
        logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
        
        # Read uploaded file
        audio_bytes = await file.read()
        logger.info(f"Read {len(audio_bytes)} bytes from uploaded file")

        # Process audio file
        processed_audio, audio_info = await process_audio_file(audio_bytes, file.content_type)
        logger.info(f"Processed audio size: {len(processed_audio)} bytes")

        # Convert to base64
        audio_base64 = base64.b64encode(processed_audio).decode("utf-8")
        
        # Call UltraVox API
        response_audio, response_info = await call_ultravox_api(audio_base64)
        
        # Return audio response
        audio_io = io.BytesIO(response_audio)
        return FileResponse(
            audio_io,
            media_type="audio/wav",
            filename="response.wav",
            headers={"Content-Disposition": "attachment; filename=response.wav"}
        )

    except AudioProcessingError as e:
        logger.error(str(e))
        return JSONResponse(
            content={"error": "Audio processing error", "details": str(e)},
            status_code=400
        )
    
    except HTTPException as e:
        # Re-raise FastAPI HTTP exceptions
        raise e
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JSONResponse(
            content={"error": "Server error", "details": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
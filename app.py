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

# Load environment variables
load_dotenv()

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
        "https://your-github-username.github.io",  # Replace with your GitHub Pages domain
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
    return {"status": "healthy", "service": "UltraVox Audio Service"}

@app.post("/transcribe_and_reply/")
async def transcribe_and_reply(file: UploadFile = File(...)):
    """
    Endpoint to handle audio transcription and response generation
    
    Args:
        file (UploadFile): The uploaded audio file
        
    Returns:
        FileResponse: Audio response from UltraVox
    """
    try:
        # Read the uploaded file
        audio_bytes = await file.read()
        
        # Validate and convert the file to WAV using pydub
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        except Exception as e:
            return JSONResponse(
                content={
                    "error": "Invalid audio file",
                    "details": str(e)
                },
                status_code=400
            )

        # Convert audio to WAV format and save in-memory
        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        buffer.seek(0)

        # Encode the audio file as Base64 for UltraVox
        audio_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        # Prepare the payload for UltraVox API
        payload = {
            "model": "ultravox",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": "For like Michigan,", "type": "text"},
                        {"type": "audio_blob", "audio_blob": audio_base64}
                    ]
                }
            ]
        }

        # Make request to UltraVox API
        headers = {
            "Authorization": f"Api-Key {ULTRAVOX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        if not ULTRAVOX_API_KEY:
            return JSONResponse(
                content={"error": "ULTRAVOX_API_KEY not configured"},
                status_code=500
            )

        response = requests.post(
            ULTRAVOX_URL,
            headers=headers,
            json=payload,
            timeout=30  # Add timeout to prevent hanging
        )

        if response.status_code != 200:
            return JSONResponse(
                content={
                    "error": "Failed to connect to UltraVox API",
                    "details": response.text
                },
                status_code=response.status_code
            )

        # Get the response audio
        response_data = response.json()
        response_audio_base64 = response_data.get("audio")
        
        if not response_audio_base64:
            return JSONResponse(
                content={"error": "No audio response received from UltraVox"},
                status_code=500
            )

        # Decode the Base64 audio
        try:
            response_audio = base64.b64decode(response_audio_base64)
        except Exception as e:
            return JSONResponse(
                content={
                    "error": "Failed to decode audio response",
                    "details": str(e)
                },
                status_code=500
            )

        # Create a temporary file-like object with the audio data
        audio_io = io.BytesIO(response_audio)
        return FileResponse(
            audio_io,
            media_type="audio/wav",
            filename="response.wav",
            headers={
                "Content-Disposition": "attachment; filename=response.wav"
            }
        )

    except requests.exceptions.RequestException as e:
        return JSONResponse(
            content={
                "error": "Failed to communicate with UltraVox API",
                "details": str(e)
            },
            status_code=500
        )
    except Exception as e:
        return JSONResponse(
            content={
                "error": "An unexpected error occurred",
                "details": str(e)
            },
            status_code=500
        )

# Add this for Koyeb deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
import soundfile as sf
import io
import base64

# Load environment variables
load_dotenv()

# Access environment variables
ULTRAVOX_API_KEY = os.getenv("ULTRAVOX_API_KEY")
ULTRAVOX_URL = os.getenv("ULTRAVOX_URL")

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to restrict access to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/transcribe_and_reply/")
async def transcribe_and_reply(file: UploadFile = File(...)):
    try:
        # Read the uploaded file
        audio_bytes = await file.read()
        
        # Validate the file format using soundfile
        try:
            audio_data, samplerate = sf.read(io.BytesIO(audio_bytes))
        except sf.LibsndfileError:
            return JSONResponse(content={"error": "Invalid audio file. Please upload a valid WAV file."}, status_code=400)

        # Encode the audio file as Base64 for UltraVox
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

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

        headers = {"Authorization": f"Api-Key {ULTRAVOX_API_KEY}"}
        response = requests.post(ULTRAVOX_URL, headers=headers, json=payload)

        if response.status_code != 200:
            return JSONResponse(content={"error": "Failed to connect to UltraVox API.", "details": response.text}, status_code=500)

        # Get the response audio (assuming UltraVox returns audio in Base64 format)
        response_data = response.json()
        response_audio_base64 = response_data.get("audio", "")

        # Decode the Base64 audio and return it as a file response
        response_audio = base64.b64decode(response_audio_base64)
        return FileResponse(io.BytesIO(response_audio), media_type="audio/wav", filename="response.wav")

    except Exception as e:
        return JSONResponse(content={"error": f"An unexpected error occurred: {str(e)}"}, status_code=500)

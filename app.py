from fastapi import FastAPI, UploadFile, File
from dotenv import load_dotenv
import os
import requests
import soundfile as sf

# Load environment variables from .env
load_dotenv()

# Access environment variables
ULTRAVOX_API_KEY = os.getenv("ULTRAVOX_API_KEY")
ULTRAVOX_URL = os.getenv("ULTRAVOX_URL")

app = FastAPI()

@app.get("/favicon.ico")
async def favicon():
    return {"message": "No favicon set"}

@app.get("/")
async def read_root():
    return {"message": "Welcome to your FastAPI application!"}

@app.post("/transcribe_and_reply/")
async def transcribe_and_reply(file: UploadFile = File(...)):
    # Save audio file locally
    audio_data, samplerate = sf.read(file.file)
    audio_path = "temp_audio.wav"
    sf.write(audio_path, audio_data, samplerate)

    # Upload to your S3 bucket or temporary hosting service
    audio_url = "https://your-temp-host/audio.wav"  # Replace with actual logic to upload to S3

    # Send request to UltraVox
    payload = {
        "model": "ultravox",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": "For like Michigan,", "type": "text"},
                    {"type": "audio_url", "audio_url": {"url": audio_url}}
                ]
            }
        ]
    }
    headers = {"Authorization": f"Api-Key {ULTRAVOX_API_KEY}"}
    response = requests.post(ULTRAVOX_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return {"response": response.json()}
    else:
        return {"error": response.text}

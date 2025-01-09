from fastapi import FastAPI, UploadFile, File
from dotenv import load_dotenv
import os
import requests
import soundfile as sf
import io

# Load environment variables from .env
load_dotenv()

# Access environment variables
ULTRAVOX_API_KEY = os.getenv("ULTRAVOX_API_KEY")
ULTRAVOX_URL = os.getenv("ULTRAVOX_URL")

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to your FastAPI application!"}

@app.post("/transcribe_and_reply/")
async def transcribe_and_reply(file: UploadFile = File(...)):
    # Read the audio data directly from the uploaded file
    audio_data, samplerate = sf.read(io.BytesIO(file.file.read()))

    # Convert audio data to a WAV format in memory
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, samplerate, format='WAV')
    buffer.seek(0)

    # Send the audio data to UltraVox
    payload = {
        "model": "ultravox",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": "For like Michigan,", "type": "text"},
                    {"type": "audio_url", "audio_url": {"url": "data:audio/wav;base64," + buffer.read().decode('utf-8')}}
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

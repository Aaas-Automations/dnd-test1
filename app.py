from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
import requests
import soundfile as sf
import io

# Load environment variables
load_dotenv()

# Access environment variables
ULTRAVOX_API_KEY = os.getenv("ULTRAVOX_API_KEY")
ULTRAVOX_URL = os.getenv("ULTRAVOX_URL")

app = FastAPI()

@app.post("/transcribe_and_reply/")
async def transcribe_and_reply(file: UploadFile = File(...)):
    # Read uploaded audio file
    audio_data, samplerate = sf.read(io.BytesIO(await file.read()))

    # Process the audio file (e.g., save to WAV in memory)
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, samplerate, format='WAV')
    buffer.seek(0)

    # Send audio data to UltraVox
    payload = {
        "model": "ultravox",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": "For like Michigan,", "type": "text"},
                    {"type": "audio_blob", "audio_blob": buffer.read()}
                ]
            }
        ]
    }
    headers = {"Authorization": f"Api-Key {ULTRAVOX_API_KEY}"}
    response = requests.post(ULTRAVOX_URL, headers=headers, json=payload)

    # Generate a dummy response audio (replace with actual audio from UltraVox)
    dummy_audio = io.BytesIO()
    sf.write(dummy_audio, audio_data, samplerate, format='WAV')
    dummy_audio.seek(0)

    return FileResponse(dummy_audio, media_type="audio/wav", filename="response.wav")

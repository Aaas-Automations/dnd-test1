import sounddevice as sd
from scipy.io.wavfile import write
from transformers import pipeline, AutoProcessor, AutoModelForSpeechSeq2Seq
import torch
import pyttsx3


# Record audio
def record_audio(filename, duration=5, samplerate=16000):
    print("Recording... Speak now!")
    audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    write(filename, samplerate, audio)
    print("Recording complete.")


# Transcribe audio
def transcribe_audio(filename):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model_id = "openai/whisper-large-v3"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if device == "cuda:0" else torch.float32
    ).to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        device=device,
    )

    result = pipe(filename)
    return result["text"]


# Generate voice response
def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


# Main function
def main():
    audio_file = "input_audio.wav"

    # Record audio
    record_audio(audio_file, duration=5)

    # Transcribe audio
    transcription = transcribe_audio(audio_file)
    print(f"Transcription: {transcription}")

    # Generate voice response
    speak_text(f"You said: {transcription}")


if __name__ == "__main__":
    main()

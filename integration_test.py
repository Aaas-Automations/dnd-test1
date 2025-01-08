def main():
    # Record audio
    audio_file = "input_audio.wav"
    record_audio(audio_file, duration=5)

    # Transcribe audio
    transcription = transcribe_audio(audio_file)
    print(f"Transcription: {transcription}")

    # Generate voice response
    speak_text(f"You said: {transcription}")

if __name__ == "__main__":
    main()

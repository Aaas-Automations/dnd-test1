import sounddevice as sd
from scipy.io.wavfile import write

def record_audio(filename, duration=5, samplerate=16000):
    print("Recording... Speak now!")
    audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    write(filename, samplerate, audio)
    print("Recording complete.")

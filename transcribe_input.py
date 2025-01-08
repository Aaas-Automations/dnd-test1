from transformers import pipeline, AutoProcessor, AutoModelForSpeechSeq2Seq
import torch

# Load Whisper model and processor
device = "cuda:0" if torch.cuda.is_available() else "cpu"
model_id = "openai/whisper-large-v3"

model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id, torch_dtype=torch.float16 if device == "cuda:0" else torch.float32).to(device)
processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    device=device
)

def transcribe_audio(filename):
    result = pipe(filename)
    return result["text"]

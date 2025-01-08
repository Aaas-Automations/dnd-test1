Install dependencies 
pip install fastapi uvicorn python-dotenv requests soundfile transformers
pip install python-multipart



Run your FastAPI app locally to ensure it correctly reads from .env:

uvicorn app:app --reload

Use the endpoint (e.g., POST /transcribe_and_reply/) to test the flow.
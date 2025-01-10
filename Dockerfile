FROM python:3.9-slim

WORKDIR /

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
COPY .env .

CMD ["python", "app.py"]
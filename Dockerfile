# Use a lightweight Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /

# Copy the frontend files
COPY fe/ ./fe

# Copy the Python server script
COPY serve.py .

# Expose port 8080
EXPOSE 8080

# Run the Python server
CMD ["python", "serve.py"]

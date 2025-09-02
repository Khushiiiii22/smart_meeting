# Base image with Python
FROM python:3.11-slim

# Install ffmpeg and system dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (matches your Flask or Gunicorn app)
EXPOSE 5001

# Command to run your app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5001"]

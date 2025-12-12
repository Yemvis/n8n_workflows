# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY gmail_telegram_monitor.py .
COPY start_monitor.py .

# Copy credentials (these will be mounted as volumes in production)
# Don't copy .env, credentials.json, token.json in Dockerfile
# They will be mounted from host

# Run the monitor
CMD ["python", "start_monitor.py"]

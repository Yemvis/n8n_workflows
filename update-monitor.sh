#!/bin/bash
# Gmail Monitor Update Script
# This script pulls latest changes and restarts the monitor

echo "Updating Gmail Monitor..."

# Go to project directory
cd ~/n8n_workflows

# Pull latest code from GitHub
echo "Pulling latest changes..."
git pull

# Rebuild Docker image
echo "Rebuilding Docker image..."
docker build -t gmail-telegram-monitor:latest .

# Stop and remove old container
echo "Stopping old container..."
docker stop gmail-monitor 2>/dev/null
docker rm gmail-monitor 2>/dev/null

# Start new container
echo "Starting updated container..."
docker run -d \
  --name gmail-monitor \
  --restart unless-stopped \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/token.json:/app/token.json:rw \
  gmail-telegram-monitor:latest

# Show status
echo ""
echo "Update complete! Container status:"
docker ps --filter name=gmail-monitor

echo ""
echo "Recent logs:"
docker logs --tail 20 gmail-monitor

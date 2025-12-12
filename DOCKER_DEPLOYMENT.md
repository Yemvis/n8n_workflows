# Docker Deployment Guide (Using Termius)

Deploy your Gmail-to-Telegram monitor using Docker on your VPS. This is the easiest and most reliable method.

## Prerequisites

- VPS with Ubuntu/Debian (or any Linux)
- Termius app installed on your device
- Docker and Docker Compose installed on VPS

## Step 1: Connect to VPS with Termius

1. Open Termius app
2. Add your VPS connection:
   - Host: your-vps-ip
   - Username: your-username
   - Password or SSH key
3. Connect to your VPS

## Step 2: Install Docker (if not installed)

Run these commands on your VPS:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
exit
```

## Step 3: Clone Repository on VPS

```bash
# Connect again with Termius
# Clone your repository
git clone https://github.com/Yemvis/n8n_workflows.git
cd n8n_workflows
```

## Step 4: Upload Credentials

### Option A: Using Termius SFTP

1. In Termius, go to SFTP tab
2. Navigate to `/home/your-username/n8n_workflows/`
3. Upload these files from your computer:
   - `.env`
   - `credentials.json`
   - `token.json`

### Option B: Using SCP from your computer

```bash
scp .env credentials.json token.json user@your-vps-ip:~/n8n_workflows/
```

## Step 5: Start with Docker

On your VPS (via Termius):

```bash
# Make sure you're in the project directory
cd ~/n8n_workflows

# Build and start the container
docker-compose up -d

# That's it! The monitor is now running!
```

## Managing the Docker Container

### View logs (real-time)
```bash
docker-compose logs -f
```

### Check if running
```bash
docker-compose ps
```

### Stop the monitor
```bash
docker-compose down
```

### Restart the monitor
```bash
docker-compose restart
```

### Update code and restart
```bash
git pull
docker-compose down
docker-compose up -d --build
```

### View container status
```bash
docker ps
```

## Benefits of Docker Deployment

✓ **Isolated environment** - No conflicts with other software
✓ **Auto-restart** - Restarts automatically if it crashes
✓ **Easy updates** - Just pull and rebuild
✓ **Consistent** - Works the same on any VPS
✓ **Clean** - All dependencies contained in the image
✓ **Portable** - Move to different VPS easily

## Troubleshooting

### Container keeps restarting
```bash
# Check logs for errors
docker-compose logs

# Common issues:
# 1. Missing credentials files (.env, credentials.json, token.json)
# 2. Wrong file permissions
```

### Fix file permissions
```bash
chmod 600 .env credentials.json token.json
```

### Rebuild from scratch
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Access container shell for debugging
```bash
docker exec -it gmail-telegram-monitor /bin/bash
```

## Quick Setup Script

Save this as `setup.sh` on your VPS:

```bash
#!/bin/bash
echo "Setting up Gmail-Telegram Monitor with Docker"

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose if needed
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt install docker-compose -y
fi

# Clone repository
if [ ! -d "n8n_workflows" ]; then
    git clone https://github.com/Yemvis/n8n_workflows.git
fi

cd n8n_workflows

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Upload .env, credentials.json, token.json to this directory"
echo "2. Run: docker-compose up -d"
echo ""
```

Make it executable and run:
```bash
chmod +x setup.sh
./setup.sh
```

## Monitoring in Termius

1. Keep a Termius session open
2. Run: `docker-compose logs -f`
3. You'll see real-time output
4. Press Ctrl+C to exit logs (container keeps running)

The monitor will run 24/7 even after you disconnect from Termius!

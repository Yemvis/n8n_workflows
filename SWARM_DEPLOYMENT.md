# Docker Swarm Deployment Guide

Deploy the Gmail-to-Telegram monitor on your Docker Swarm cluster.

## Prerequisites

- Docker Swarm initialized
- Access to your swarm manager node
- Credentials files (.env, credentials.json, token.json) in the project directory

## Quick Deployment

### 1. Build the Docker image

```bash
cd ~/n8n_workflows

# Build the image
docker build -t gmail-telegram-monitor:latest .
```

### 2. Deploy as a Swarm Stack

```bash
# Deploy the stack
docker stack deploy -c stack-gmail-monitor.yml gmail

# Check if it's running
docker stack ps gmail

# View logs
docker service logs -f gmail_gmail-monitor
```

## Simple Deployment (Without Swarm Stack)

If you prefer a simpler approach, deploy as a single service:

```bash
cd ~/n8n_workflows

# Build the image
docker build -t gmail-telegram-monitor:latest .

# Create Docker secrets
printf "%s" "$(cat .env)" | docker secret create gmail_env -
printf "%s" "$(cat credentials.json)" | docker secret create gmail_credentials -

# Deploy as a service
docker service create \
  --name gmail-monitor \
  --secret gmail_env \
  --secret gmail_credentials \
  --mount type=bind,source=$(pwd)/token.json,target=/app/token.json \
  --restart-condition on-failure \
  --restart-delay 10s \
  --restart-max-attempts 3 \
  gmail-telegram-monitor:latest
```

## Even Simpler: Docker Run with Bind Mounts

The easiest way for Swarm environments:

```bash
cd ~/n8n_workflows

# Build the image
docker build -t gmail-telegram-monitor:latest .

# Run as a regular container (will auto-restart)
docker run -d \
  --name gmail-monitor \
  --restart unless-stopped \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/token.json:/app/token.json:rw \
  gmail-telegram-monitor:latest
```

## Management Commands

### View logs
```bash
# If deployed as stack
docker service logs -f gmail_gmail-monitor

# If deployed as service
docker service logs -f gmail-monitor

# If deployed as container
docker logs -f gmail-monitor
```

### Check status
```bash
# Stack
docker stack ps gmail

# Service
docker service ps gmail-monitor

# Container
docker ps | grep gmail-monitor
```

### Update/Restart
```bash
# Stack
docker stack rm gmail
docker stack deploy -c stack-gmail-monitor.yml gmail

# Service
docker service update --force gmail-monitor

# Container
docker restart gmail-monitor
```

### Stop
```bash
# Stack
docker stack rm gmail

# Service
docker service rm gmail-monitor

# Container
docker stop gmail-monitor && docker rm gmail-monitor
```

## Integration with Traefik

If you want to add a web interface later (optional), add these labels:

```yaml
deploy:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.gmail-monitor.rule=Host(`gmail.yourdomain.com`)"
    - "traefik.http.routers.gmail-monitor.entrypoints=websecure"
    - "traefik.http.routers.gmail-monitor.tls.certresolver=letsencrypt"
    - "traefik.http.services.gmail-monitor.loadbalancer.server.port=8000"
```

## Recommended: Simple Docker Run

For this monitoring service, I recommend using the simple `docker run` approach since:
- It's a background service (no web interface)
- Doesn't need load balancing
- Simpler to manage and debug
- Auto-restarts with `--restart unless-stopped`

## Troubleshooting

### Container keeps restarting
```bash
docker logs gmail-monitor
```

### Check if credentials are mounted correctly
```bash
docker exec gmail-monitor ls -la /app/
```

### Rebuild image
```bash
docker build --no-cache -t gmail-telegram-monitor:latest .
```

### Clean restart
```bash
docker stop gmail-monitor
docker rm gmail-monitor
docker build -t gmail-telegram-monitor:latest .
# Then run again with docker run command
```

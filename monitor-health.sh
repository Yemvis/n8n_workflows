#!/bin/bash
# Gmail Monitor Health Check & Auto-Recovery
# Run this with cron every 5 minutes

CONTAINER_NAME="gmail-monitor"
TELEGRAM_TOKEN="${1}"
TELEGRAM_CHAT_ID="${2}"

send_alert() {
    local message="$1"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="🚨 Gmail Monitor Alert: ${message}" \
        -d parse_mode="HTML" > /dev/null
}

# Check if container is running
if ! docker ps --filter "name=${CONTAINER_NAME}" --filter "status=running" | grep -q ${CONTAINER_NAME}; then
    echo "[$(date)] Container not running. Attempting restart..."
    send_alert "Container stopped. Restarting automatically..."

    # Restart container
    docker start ${CONTAINER_NAME}

    # Wait and check
    sleep 5
    if docker ps --filter "name=${CONTAINER_NAME}" --filter "status=running" | grep -q ${CONTAINER_NAME}; then
        send_alert "✅ Container restarted successfully"
        echo "[$(date)] Container restarted successfully"
    else
        send_alert "❌ Failed to restart container. Manual intervention needed."
        echo "[$(date)] Failed to restart container"
    fi
    exit 0
fi

# Check for errors in logs (last 50 lines)
ERROR_COUNT=$(docker logs --tail 50 ${CONTAINER_NAME} 2>&1 | grep -i "error\|exception\|failed" | wc -l)

if [ "$ERROR_COUNT" -gt 5 ]; then
    echo "[$(date)] High error count detected: ${ERROR_COUNT}"
    send_alert "High error count detected (${ERROR_COUNT} errors). Check logs."
fi

# Check container health (exit code)
CONTAINER_STATUS=$(docker inspect ${CONTAINER_NAME} --format='{{.State.Status}}')
if [ "$CONTAINER_STATUS" != "running" ]; then
    echo "[$(date)] Container unhealthy: ${CONTAINER_STATUS}"
    send_alert "Container status: ${CONTAINER_STATUS}. Attempting recovery..."
    docker restart ${CONTAINER_NAME}
fi

echo "[$(date)] Health check passed"

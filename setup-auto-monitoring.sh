#!/bin/bash
# Setup Automatic Health Monitoring with Cron

echo "Setting up automatic health monitoring..."

# Get credentials from .env
source .env

# Create cron job to run health check every 5 minutes
CRON_JOB="*/5 * * * * /root/n8n_workflows/monitor-health.sh ${TELEGRAM_BOT_TOKEN} ${TELEGRAM_CHAT_ID} >> /var/log/gmail-monitor-health.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null | grep -v "monitor-health.sh"; echo "$CRON_JOB") | crontab -

echo "✓ Health monitoring enabled"
echo "✓ Checks every 5 minutes"
echo "✓ Auto-restarts on failure"
echo "✓ Sends Telegram alerts"
echo ""
echo "Logs: /var/log/gmail-monitor-health.log"
echo ""
echo "To disable: crontab -e (remove the monitor-health.sh line)"

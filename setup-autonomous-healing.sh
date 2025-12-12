#!/bin/bash
# Setup Claude-Powered Autonomous Self-Healing System

echo "🤖 Setting up Autonomous Self-Healing with Claude AI"
echo "===================================================="
echo ""

# Load .env file
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if Anthropic API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not found in .env file"
    echo ""
    echo "Please add your Anthropic API key to .env file:"
    echo "ANTHROPIC_API_KEY=your_api_key_here"
    echo ""
    echo "Get your key at: https://console.anthropic.com/"
    exit 1
fi

echo "✓ API key found in .env"

# Install Python dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Make healer executable
chmod +x autonomous_healer.py

# Setup cron job to run every 5 minutes
CRON_JOB="*/5 * * * * cd /root/n8n_workflows && /usr/bin/python3 autonomous_healer.py >> /var/log/autonomous-healer.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null | grep -v "autonomous_healer.py"; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ Autonomous healing system activated!"
echo ""
echo "📋 How it works:"
echo "   - Checks health every 5 minutes"
echo "   - Detects errors automatically"
echo "   - Sends errors to Claude API"
echo "   - Claude analyzes and creates fix"
echo "   - System applies fix automatically"
echo "   - You get notified via Telegram"
echo ""
echo "🔍 Monitor logs: tail -f /var/log/autonomous-healer.log"
echo "⚙️  Test manually: python3 autonomous_healer.py"
echo "🛑 Disable: crontab -e (remove autonomous_healer.py line)"
echo ""
echo "🚀 You're now FULLY AUTONOMOUS!"

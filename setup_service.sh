#!/bin/bash
# Gmail Monitor - VPS Service Setup Script

echo "Gmail to Telegram Monitor - Service Setup"
echo "=========================================="

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CURRENT_USER=$(whoami)

# Find Python3 path
PYTHON_PATH=$(which python3)

echo "Installing to: $SCRIPT_DIR"
echo "Running as user: $CURRENT_USER"
echo "Python path: $PYTHON_PATH"
echo ""

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/gmail-monitor.service"

echo "Creating systemd service file..."
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Gmail to Telegram Real-time Monitor
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$PYTHON_PATH $SCRIPT_DIR/start_monitor.py
Restart=always
RestartSec=10
StandardOutput=append:$SCRIPT_DIR/monitor.log
StandardError=append:$SCRIPT_DIR/error.log

[Install]
WantedBy=multi-user.target
EOF

echo "[OK] Service file created at $SERVICE_FILE"

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling service to start on boot..."
sudo systemctl enable gmail-monitor

# Start service
echo "Starting Gmail monitor service..."
sudo systemctl start gmail-monitor

# Wait a moment
sleep 2

# Check status
echo ""
echo "=========================================="
echo "Service Status:"
echo "=========================================="
sudo systemctl status gmail-monitor --no-pager

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  Status:  sudo systemctl status gmail-monitor"
echo "  Stop:    sudo systemctl stop gmail-monitor"
echo "  Start:   sudo systemctl start gmail-monitor"
echo "  Restart: sudo systemctl restart gmail-monitor"
echo "  Logs:    tail -f $SCRIPT_DIR/monitor.log"
echo "  Errors:  tail -f $SCRIPT_DIR/error.log"
echo ""
echo "The monitor is now running and will auto-start on reboot!"

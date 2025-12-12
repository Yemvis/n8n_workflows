# VPS Deployment Guide

This guide shows how to deploy the Gmail-to-Telegram monitor on your VPS to run 24/7.

## Step 1: Prepare Your Files

On your local machine, you need these files for the VPS:
- `start_monitor.py` (the main script)
- `gmail_telegram_monitor.py` (the monitor class)
- `requirements.txt` (dependencies)
- `.env` (your credentials)
- `credentials.json` (Gmail API credentials)
- `token.json` (Gmail authentication token)

## Step 2: Upload Files to VPS

### Option A: Using SCP (Secure Copy)
```bash
# From your local machine, upload all files
scp start_monitor.py gmail_telegram_monitor.py requirements.txt .env credentials.json token.json user@your-vps-ip:/home/user/gmail-monitor/
```

### Option B: Using Git
```bash
# On VPS
cd ~
git clone your-repo-url gmail-monitor
cd gmail-monitor

# Then manually upload .env, credentials.json, and token.json
# (Don't commit these sensitive files to git!)
```

### Option C: Manual Upload
- Use FileZilla, WinSCP, or your VPS control panel to upload the files

## Step 3: Install Dependencies on VPS

SSH into your VPS:
```bash
ssh user@your-vps-ip
```

Install Python and pip (if not installed):
```bash
# For Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip -y

# For CentOS/RHEL
sudo yum install python3 python3-pip -y
```

Navigate to your project folder and install requirements:
```bash
cd ~/gmail-monitor
pip3 install -r requirements.txt
```

## Step 4: Run the Monitor on VPS

### Method 1: Using Screen (Recommended for simplicity)

Screen keeps your script running even after you disconnect from SSH.

```bash
# Install screen if needed
sudo apt install screen -y

# Start a new screen session
screen -S gmail-monitor

# Run the monitor
python3 start_monitor.py

# Detach from screen: Press Ctrl+A then D
# The script continues running in background
```

**To check on it later:**
```bash
# List screen sessions
screen -ls

# Re-attach to the session
screen -r gmail-monitor

# To stop: Attach and press Ctrl+C
```

### Method 2: Using tmux

```bash
# Install tmux
sudo apt install tmux -y

# Start tmux session
tmux new -s gmail-monitor

# Run the monitor
python3 start_monitor.py

# Detach: Press Ctrl+B then D
```

**To re-attach:**
```bash
tmux attach -t gmail-monitor
```

### Method 3: Using nohup (Simple background process)

```bash
# Run in background, output to log file
nohup python3 start_monitor.py > monitor.log 2>&1 &

# Check if running
ps aux | grep start_monitor

# View logs
tail -f monitor.log

# Stop it
pkill -f start_monitor.py
```

### Method 4: As a Systemd Service (Best for production)

This method auto-restarts the script if it crashes and starts on boot.

Create a service file:
```bash
sudo nano /etc/systemd/system/gmail-monitor.service
```

Add this content (replace paths and user):
```ini
[Unit]
Description=Gmail to Telegram Monitor
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/gmail-monitor
ExecStart=/usr/bin/python3 /home/your-username/gmail-monitor/start_monitor.py
Restart=always
RestartSec=10
StandardOutput=append:/home/your-username/gmail-monitor/monitor.log
StandardError=append:/home/your-username/gmail-monitor/error.log

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable gmail-monitor

# Start the service
sudo systemctl start gmail-monitor

# Check status
sudo systemctl status gmail-monitor

# View logs
journalctl -u gmail-monitor -f

# Stop service
sudo systemctl stop gmail-monitor

# Restart service
sudo systemctl restart gmail-monitor
```

## Step 5: Verify It's Working

1. **Check if running:**
```bash
ps aux | grep start_monitor
```

2. **Check logs:**
```bash
# If using nohup
tail -f monitor.log

# If using systemd
journalctl -u gmail-monitor -f
```

3. **Test by sending yourself an email** - you should receive a Telegram notification!

## Troubleshooting

### Issue: "Module not found" errors
```bash
# Make sure you installed requirements
pip3 install -r requirements.txt --user
```

### Issue: Permission errors
```bash
# Make files executable
chmod +x start_monitor.py gmail_telegram_monitor.py
```

### Issue: Python path issues
```bash
# Find Python path
which python3

# Use full path in commands
/usr/bin/python3 start_monitor.py
```

### Issue: Authentication errors
- Make sure `credentials.json` and `token.json` are uploaded
- Make sure `.env` file has correct Telegram credentials

## Monitoring and Maintenance

### Check if monitor is running:
```bash
# Using screen
screen -ls

# Using systemd
sudo systemctl status gmail-monitor

# Using process list
ps aux | grep start_monitor
```

### View logs:
```bash
# If using nohup
tail -f ~/gmail-monitor/monitor.log

# If using systemd
journalctl -u gmail-monitor -f
```

### Auto-start on reboot:
- **Screen/tmux**: Add to crontab
```bash
crontab -e
# Add this line:
@reboot cd /home/user/gmail-monitor && screen -dmS gmail-monitor python3 start_monitor.py
```

- **Systemd**: Already auto-starts if enabled

## Security Best Practices

1. **Protect sensitive files:**
```bash
chmod 600 .env credentials.json token.json
```

2. **Use firewall:**
```bash
sudo ufw enable
sudo ufw allow ssh
```

3. **Regular updates:**
```bash
sudo apt update && sudo apt upgrade -y
```

4. **Monitor logs for errors:**
```bash
# Check for error patterns
grep -i error monitor.log
```

## Recommended: Systemd Service

For a production VPS, I recommend using **Method 4 (Systemd Service)** because:
- Auto-restarts if the script crashes
- Starts automatically on server reboot
- Easy to manage with systemctl commands
- Proper logging with journalctl
- Runs as a proper system service

# Gmail to Telegram Monitor

Async Python application that monitors your Gmail account and sends real-time notifications to Telegram.

## Features

- Fetch all Gmail emails with sender and subject information
- Real-time monitoring for new incoming emails
- Asynchronous implementation for efficient performance
- Telegram notifications with formatted email details

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Enable the **Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials file
5. Rename the downloaded file to `credentials.json` and place it in the project root

### 3. Set Up Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions to create a new bot
3. Copy the bot token provided by BotFather
4. Get your Chat ID:
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat.id` in the response

### 4. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

## Usage

Run the application:

```bash
python gmail_telegram_monitor.py
```

You'll be prompted to choose a mode:

1. **Send all emails summary** - Fetches existing emails and sends a one-time summary
2. **Monitor for new emails** - Continuously monitors for new emails and sends real-time notifications

### First Run

On the first run, you'll be prompted to authorize the application:
- A browser window will open for Gmail authentication
- Sign in with your Google account
- Grant the requested permissions
- The credentials will be saved in `token.pickle` for future use

## How It Works

### Async Function Architecture

The main async function `monitor_new_emails()` does the following:

1. Authenticates with Gmail API using OAuth2
2. Initializes the Telegram bot
3. Polls Gmail every 30 seconds for new messages
4. Tracks seen message IDs to avoid duplicates
5. Sends formatted notifications to Telegram for each new email

### Email Information Sent

Each notification includes:
- Sender (From address)
- Subject line
- Date received

## Files

- `gmail_telegram_monitor.py` - Main application code
- `requirements.txt` - Python dependencies
- `.env` - Your API credentials (create from .env.example)
- `credentials.json` - Gmail API credentials (download from Google Cloud Console)
- `token.pickle` - Cached Gmail authentication (auto-generated)

## Security Notes

- Keep your `.env` file and `credentials.json` secure
- Never commit these files to version control
- The application only requests read-only access to Gmail
- Add `.env`, `credentials.json`, and `token.pickle` to `.gitignore`

## Customization

You can modify the monitoring interval by changing the `interval` parameter:

```python
await monitor.monitor_new_emails(interval=60)  # Check every 60 seconds
```

## Troubleshooting

- **Authentication errors**: Delete `token.pickle` and re-authenticate
- **Telegram errors**: Verify your bot token and chat ID are correct
- **No emails found**: Check Gmail API is enabled in Google Cloud Console
- **Rate limiting**: Increase the monitoring interval if you hit API limits

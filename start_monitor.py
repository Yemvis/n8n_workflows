import asyncio
import os
from dotenv import load_dotenv
from gmail_telegram_monitor import GmailTelegramMonitor

# Load environment variables
load_dotenv()


async def main():
    """Start real-time Gmail monitoring directly."""
    # Load configuration
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat_id:
        print("Error: Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file")
        return

    # Create monitor instance
    monitor = GmailTelegramMonitor(telegram_token, telegram_chat_id)

    # Authenticate with Gmail
    print("Authenticating with Gmail...")
    monitor.authenticate_gmail()

    # Start monitoring (checking every 60 seconds / 1 minute)
    await monitor.monitor_new_emails(interval=60)


if __name__ == '__main__':
    asyncio.run(main())

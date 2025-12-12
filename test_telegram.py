import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

# Load environment variables
load_dotenv()


async def send_test_email():
    """Send a mockup email notification to Telegram."""

    # Load credentials
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in .env file")
        return

    # Create bot instance
    bot = Bot(token=telegram_token)

    # Mockup email data
    mockup_email = {
        'sender': 'john.doe@example.com',
        'subject': 'Test Email - Your Gmail Monitor is Working!',
        'date': 'Thu, 12 Dec 2024 10:30:00 -0300'
    }

    # Format message
    message = (
        f"📧 <b>New Email</b>\n\n"
        f"<b>From:</b> {mockup_email['sender']}\n"
        f"<b>Subject:</b> {mockup_email['subject']}\n"
        f"<b>Date:</b> {mockup_email['date']}\n"
    )

    try:
        print("Sending test notification to Telegram...")
        await bot.send_message(
            chat_id=telegram_chat_id,
            text=message,
            parse_mode='HTML'
        )
        print("[OK] Test notification sent successfully!")
        print("\nYour Telegram bot is working correctly.")
        print("You're ready to start real-time monitoring!")

    except TelegramError as e:
        print(f"[ERROR] Error sending message: {e}")
        print("\nPlease check:")
        print("1. Your bot token is correct")
        print("2. Your chat ID is correct")
        print("3. You've started a conversation with your bot on Telegram")


if __name__ == '__main__':
    asyncio.run(send_test_email())

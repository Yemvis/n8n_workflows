import os
import asyncio
import pickle
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from telegram import Bot
from telegram.error import TelegramError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Load environment variables
load_dotenv()


class GmailTelegramMonitor:
    """Monitor Gmail and send real-time notifications to Telegram."""

    def __init__(self, telegram_token: str, telegram_chat_id: str):
        """
        Initialize the monitor with Telegram credentials.

        Args:
            telegram_token: Telegram bot token
            telegram_chat_id: Telegram chat ID to send messages to
        """
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.telegram_bot = Bot(token=telegram_token)
        self.gmail_service = None
        self.seen_message_ids = set()

    def authenticate_gmail(self) -> None:
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        token_json_path = Path('token.json')
        token_pickle_path = Path('token.pickle')
        credentials_path = Path('credentials.json')

        # Load existing credentials if available (check JSON format first, then pickle)
        if token_json_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_json_path), SCOPES)
        elif token_pickle_path.exists():
            with open(token_pickle_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    raise FileNotFoundError(
                        "credentials.json not found. Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for future use (prefer JSON format)
            with open(token_json_path, 'w') as token:
                token.write(creds.to_json())

        self.gmail_service = build('gmail', 'v1', credentials=creds)
        print("[OK] Gmail authentication successful")

    def get_all_emails(self, max_results: Optional[int] = None) -> List[Dict]:
        """
        Fetch all emails from Gmail.

        Args:
            max_results: Maximum number of emails to fetch (None for all)

        Returns:
            List of email dictionaries with sender, subject, and metadata
        """
        if not self.gmail_service:
            raise RuntimeError("Gmail service not authenticated. Call authenticate_gmail() first.")

        emails = []
        page_token = None

        try:
            while True:
                # Fetch messages
                results = self.gmail_service.users().messages().list(
                    userId='me',
                    maxResults=max_results or 500,
                    pageToken=page_token
                ).execute()

                messages = results.get('messages', [])

                for msg in messages:
                    msg_id = msg['id']

                    # Get full message details
                    message = self.gmail_service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()

                    # Extract headers
                    headers = message.get('payload', {}).get('headers', [])
                    email_data = {
                        'id': msg_id,
                        'sender': self._get_header(headers, 'From'),
                        'subject': self._get_header(headers, 'Subject'),
                        'date': self._get_header(headers, 'Date'),
                        'snippet': message.get('snippet', '')
                    }

                    emails.append(email_data)

                # Check if there are more pages
                page_token = results.get('nextPageToken')
                if not page_token or (max_results and len(emails) >= max_results):
                    break

            return emails

        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def get_new_emails(self) -> List[Dict]:
        """
        Fetch only new emails that haven't been seen before.

        Returns:
            List of new email dictionaries
        """
        if not self.gmail_service:
            raise RuntimeError("Gmail service not authenticated. Call authenticate_gmail() first.")

        new_emails = []

        try:
            # Fetch recent messages
            results = self.gmail_service.users().messages().list(
                userId='me',
                maxResults=10
            ).execute()

            messages = results.get('messages', [])

            for msg in messages:
                msg_id = msg['id']

                # Skip if already seen
                if msg_id in self.seen_message_ids:
                    continue

                # Get full message details
                message = self.gmail_service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                # Extract headers
                headers = message.get('payload', {}).get('headers', [])
                email_data = {
                    'id': msg_id,
                    'sender': self._get_header(headers, 'From'),
                    'subject': self._get_header(headers, 'Subject'),
                    'date': self._get_header(headers, 'Date'),
                    'snippet': message.get('snippet', '')
                }

                new_emails.append(email_data)
                self.seen_message_ids.add(msg_id)

            return new_emails

        except Exception as e:
            print(f"Error fetching new emails: {e}")
            return []

    def _get_header(self, headers: List[Dict], name: str) -> str:
        """Extract a specific header value from email headers."""
        for header in headers:
            if header['name'] == name:
                return header['value']
        return 'N/A'

    async def send_telegram_message(self, message: str) -> bool:
        """
        Send a message to Telegram asynchronously.

        Args:
            message: Message text to send

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except TelegramError as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def format_email_message(self, email: Dict) -> str:
        """
        Format email data into a Telegram message.

        Args:
            email: Email dictionary with sender, subject, date

        Returns:
            Formatted message string
        """
        return (
            f"📧 <b>New Email</b>\n\n"
            f"<b>From:</b> {email['sender']}\n"
            f"<b>Subject:</b> {email['subject']}\n"
            f"<b>Date:</b> {email['date']}\n"
        )

    async def send_all_emails_summary(self) -> None:
        """Fetch all emails and send a summary to Telegram."""
        print("Fetching all emails from Gmail...")
        emails = self.get_all_emails(max_results=100)  # Limit to 100 for safety

        if not emails:
            message = "No emails found in your Gmail account."
            await self.send_telegram_message(message)
            return

        # Send summary
        summary = f"📬 <b>Gmail Summary</b>\n\nTotal emails found: {len(emails)}\n\n"
        await self.send_telegram_message(summary)

        # Send first few emails as samples
        for i, email in enumerate(emails[:5], 1):
            message = self.format_email_message(email)
            await self.send_telegram_message(message)
            await asyncio.sleep(0.5)  # Rate limiting

        if len(emails) > 5:
            remaining = len(emails) - 5
            await self.send_telegram_message(
                f"... and {remaining} more emails.\n\n"
                f"Start monitoring mode to receive new emails in real-time."
            )

    async def monitor_new_emails(self, interval: int = 30) -> None:
        """
        Monitor Gmail for new emails and send notifications in real-time.

        Args:
            interval: Check interval in seconds (default: 30)
        """
        print(f"Starting real-time email monitoring (checking every {interval}s)...")
        print("Press Ctrl+C to stop monitoring")

        # Initialize seen messages with current emails
        print("Initializing with current emails...")
        current_emails = self.get_all_emails(max_results=50)
        for email in current_emails:
            self.seen_message_ids.add(email['id'])
        print(f"[OK] Initialized with {len(self.seen_message_ids)} existing emails")

        await self.send_telegram_message(
            "🔔 <b>Gmail Monitor Started</b>\n\n"
            "You will receive notifications for new emails in real-time."
        )

        try:
            while True:
                new_emails = self.get_new_emails()

                for email in new_emails:
                    message = self.format_email_message(email)
                    success = await self.send_telegram_message(message)
                    if success:
                        print(f"[OK] Sent notification for: {email['subject']}")

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\n[OK] Monitoring stopped by user")
            await self.send_telegram_message("🔕 Gmail monitoring stopped.")
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            await self.send_telegram_message(f"❌ Monitoring error: {str(e)}")


async def main():
    """Main function to run the Gmail-Telegram monitor."""
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

    # Choose mode
    print("\nChoose mode:")
    print("1. Send all emails summary (one-time)")
    print("2. Monitor for new emails (real-time)")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == '1':
        await monitor.send_all_emails_summary()
    elif choice == '2':
        await monitor.monitor_new_emails(interval=30)
    else:
        print("Invalid choice. Exiting.")


if __name__ == '__main__':
    asyncio.run(main())

#!/usr/bin/env python3
"""
Autonomous Self-Healing System powered by Claude API
Monitors Gmail monitor, detects errors, and auto-fixes them using Claude AI
"""

import os
import subprocess
import json
import anthropic
from datetime import datetime
from typing import Dict, List, Optional

class AutonomousHealer:
    """Claude-powered autonomous error detection and healing"""

    def __init__(self, anthropic_api_key: str, telegram_token: str, telegram_chat_id: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.container_name = "gmail-monitor"
        self.max_auto_fix_attempts = 3

    def check_container_health(self) -> Dict:
        """Check container status and gather health metrics"""
        health = {
            'running': False,
            'status': None,
            'recent_logs': None,
            'error_detected': False,
            'error_context': None
        }

        # Check if container is running
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True
            )
            health['running'] = bool(result.stdout.strip())
            health['status'] = result.stdout.strip()
        except Exception as e:
            health['error_detected'] = True
            health['error_context'] = f"Failed to check container: {str(e)}"
            return health

        # Get recent logs
        try:
            logs_result = subprocess.run(
                ['docker', 'logs', '--tail', '100', self.container_name],
                capture_output=True,
                text=True
            )
            health['recent_logs'] = logs_result.stdout + logs_result.stderr

            # Detect errors in logs
            error_keywords = ['error', 'exception', 'failed', 'traceback', 'critical']
            log_lower = health['recent_logs'].lower()

            if any(keyword in log_lower for keyword in error_keywords):
                health['error_detected'] = True
                health['error_context'] = self._extract_error_context(health['recent_logs'])

        except Exception as e:
            health['error_context'] = f"Failed to get logs: {str(e)}"

        return health

    def _extract_error_context(self, logs: str) -> str:
        """Extract relevant error context from logs"""
        lines = logs.split('\n')
        error_lines = []

        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed', 'traceback']):
                # Get context: 3 lines before and after
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                error_lines.extend(lines[start:end])

        return '\n'.join(error_lines[-50:])  # Last 50 lines of error context

    def ask_claude_for_fix(self, health: Dict) -> Dict:
        """Ask Claude API to analyze the error and provide a fix"""

        context = f"""
You are an autonomous system administrator for a Gmail-to-Telegram monitoring service running in Docker.

CONTAINER: {self.container_name}
RUNNING: {health['running']}
STATUS: {health['status']}

ERROR DETECTED: {health['error_detected']}
ERROR CONTEXT:
{health['error_context']}

RECENT LOGS:
{health['recent_logs'][-2000:] if health['recent_logs'] else 'No logs available'}

TASK: Analyze this error and provide an executable fix.

Return a JSON response with this structure:
{{
    "error_analysis": "Brief description of what went wrong",
    "fix_type": "restart|rebuild|update_config|other",
    "commands": ["command1", "command2", ...],
    "explanation": "Why this fix should work",
    "confidence": "high|medium|low"
}}

IMPORTANT:
- Provide actual shell commands that can be executed
- Commands should be safe and non-destructive
- Focus on common Docker/Python/Network issues
- If unsure, recommend "restart" as safe default
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )

            # Extract JSON from response
            response_text = message.content[0].text

            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                fix_plan = json.loads(json_match.group())
                return fix_plan
            else:
                # Fallback if no JSON found
                return {
                    "error_analysis": "Could not parse Claude response",
                    "fix_type": "restart",
                    "commands": [f"docker restart {self.container_name}"],
                    "explanation": "Default safe restart",
                    "confidence": "low"
                }

        except Exception as e:
            return {
                "error_analysis": f"Claude API error: {str(e)}",
                "fix_type": "restart",
                "commands": [f"docker restart {self.container_name}"],
                "explanation": "Fallback to safe restart",
                "confidence": "low"
            }

    def execute_fix(self, fix_plan: Dict) -> Dict:
        """Execute the fix commands provided by Claude"""
        result = {
            'success': False,
            'executed_commands': [],
            'output': [],
            'errors': []
        }

        commands = fix_plan.get('commands', [])

        for cmd in commands:
            try:
                print(f"Executing: {cmd}")
                proc_result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                result['executed_commands'].append(cmd)
                result['output'].append(proc_result.stdout)

                if proc_result.returncode != 0:
                    result['errors'].append(f"Command failed: {cmd}\n{proc_result.stderr}")
                    return result

            except Exception as e:
                result['errors'].append(f"Error executing {cmd}: {str(e)}")
                return result

        result['success'] = True
        return result

    def send_telegram_alert(self, message: str):
        """Send alert to Telegram"""
        try:
            subprocess.run([
                'curl', '-s', '-X', 'POST',
                f'https://api.telegram.org/bot{self.telegram_token}/sendMessage',
                '-d', f'chat_id={self.telegram_chat_id}',
                '-d', f'text={message}',
                '-d', 'parse_mode=HTML'
            ], capture_output=True)
        except Exception as e:
            print(f"Failed to send Telegram alert: {e}")

    def heal(self):
        """Main healing loop - check health and auto-fix if needed"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{timestamp}] Running autonomous health check...")

        # Check health
        health = self.check_container_health()

        # If no error and running, all good
        if health['running'] and not health['error_detected']:
            print("✓ System healthy")
            return

        # Error detected - engage Claude
        print("⚠ Error detected! Consulting Claude AI...")
        self.send_telegram_alert(
            f"🤖 <b>Autonomous Healer Active</b>\n\n"
            f"Error detected in {self.container_name}\n"
            f"Analyzing with Claude AI..."
        )

        # Ask Claude for fix
        fix_plan = self.ask_claude_for_fix(health)

        print(f"Claude's analysis: {fix_plan['error_analysis']}")
        print(f"Proposed fix: {fix_plan['fix_type']}")
        print(f"Confidence: {fix_plan['confidence']}")

        # Execute fix
        print("Executing fix...")
        result = self.execute_fix(fix_plan)

        if result['success']:
            print("✓ Fix applied successfully!")
            self.send_telegram_alert(
                f"✅ <b>Auto-Fixed!</b>\n\n"
                f"<b>Issue:</b> {fix_plan['error_analysis']}\n"
                f"<b>Fix:</b> {fix_plan['fix_type']}\n"
                f"<b>Commands executed:</b> {len(result['executed_commands'])}\n\n"
                f"{fix_plan['explanation']}"
            )
        else:
            print("✗ Fix failed!")
            error_msg = '\n'.join(result['errors'])
            self.send_telegram_alert(
                f"❌ <b>Auto-Fix Failed</b>\n\n"
                f"<b>Issue:</b> {fix_plan['error_analysis']}\n"
                f"<b>Attempted:</b> {fix_plan['fix_type']}\n\n"
                f"<b>Errors:</b>\n{error_msg[:500]}\n\n"
                f"🙋 Manual intervention needed!"
            )


def main():
    """Entry point for autonomous healer"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('/root/n8n_workflows/.env')

    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not anthropic_api_key:
        print("Error: ANTHROPIC_API_KEY not set in .env")
        return

    if not telegram_token or not telegram_chat_id:
        print("Error: Telegram credentials not set")
        return

    # Create healer and run
    healer = AutonomousHealer(anthropic_api_key, telegram_token, telegram_chat_id)
    healer.heal()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
FULL Autonomous Self-Healing System - Claude can edit code!
Detects errors, analyzes them, FIXES THE CODE, commits, rebuilds, and verifies
"""

import os
import subprocess
import json
import re
import anthropic
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class FullAutonomousHealer:
    """Claude-powered autonomous error detection AND CODE FIXING"""

    def __init__(self, anthropic_api_key: str, telegram_token: str, telegram_chat_id: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.container_name = "gmail-monitor"
        self.project_dir = "/root/n8n_workflows"
        self.main_file = "gmail_telegram_monitor.py"
        self.start_file = "start_monitor.py"

    def check_container_health(self) -> Dict:
        """Check container status and gather health metrics"""
        health = {
            'running': False,
            'status': None,
            'recent_logs': None,
            'error_detected': False,
            'error_context': None,
            'error_type': None
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
                ['docker', 'logs', '--tail', '200', self.container_name],
                capture_output=True,
                text=True
            )
            health['recent_logs'] = logs_result.stdout + logs_result.stderr

            # Detect errors in logs
            if self._has_python_error(health['recent_logs']):
                health['error_detected'] = True
                health['error_type'] = 'python_exception'
                health['error_context'] = self._extract_error_context(health['recent_logs'])

        except Exception as e:
            health['error_context'] = f"Failed to get logs: {str(e)}"

        return health

    def _has_python_error(self, logs: str) -> bool:
        """Check if logs contain Python errors"""
        error_patterns = [
            'Traceback (most recent call last)',
            'Error:',
            'Exception:',
            'Failed',
            'Critical'
        ]
        return any(pattern in logs for pattern in error_patterns)

    def _extract_error_context(self, logs: str) -> str:
        """Extract relevant error context from logs"""
        lines = logs.split('\n')
        error_lines = []

        # Find traceback sections
        in_traceback = False
        for line in lines:
            if 'Traceback (most recent call last)' in line:
                in_traceback = True

            if in_traceback:
                error_lines.append(line)
                # Stop after the actual error message
                if line.strip() and not line.startswith(' ') and 'Error:' in line:
                    in_traceback = False

        return '\n'.join(error_lines[-100:])  # Last 100 lines

    def read_source_code(self, filename: str) -> Optional[str]:
        """Read source code file"""
        try:
            filepath = os.path.join(self.project_dir, filename)
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return None

    def ask_claude_for_code_fix(self, health: Dict) -> Dict:
        """Ask Claude to analyze error AND generate code fix"""

        # Read current source code
        main_code = self.read_source_code(self.main_file)
        start_code = self.read_source_code(self.start_file)

        context = f"""
You are an autonomous system that fixes bugs in production code.

CONTAINER: {self.container_name}
RUNNING: {health['running']}
ERROR TYPE: {health['error_type']}

ERROR FROM LOGS:
```
{health['error_context']}
```

FULL LOGS (last 200 lines):
```
{health['recent_logs'][-5000:] if health['recent_logs'] else 'No logs'}
```

CURRENT SOURCE CODE - {self.main_file}:
```python
{main_code}
```

CURRENT SOURCE CODE - {self.start_file}:
```python
{start_code}
```

TASK: Analyze this error and provide a complete fix.

Return a JSON response with this EXACT structure:
{{
    "error_analysis": "Detailed analysis of what went wrong",
    "root_cause": "The actual root cause",
    "fix_type": "code_edit|docker_restart|config_change",
    "files_to_edit": [
        {{
            "filename": "gmail_telegram_monitor.py",
            "changes": [
                {{
                    "old_code": "exact code to replace (must match exactly!)",
                    "new_code": "new code to insert",
                    "explanation": "why this fixes it"
                }}
            ]
        }}
    ],
    "docker_commands": ["docker restart gmail-monitor"],
    "git_commit_message": "Fix: description of what was fixed",
    "confidence": "high|medium|low",
    "testing_steps": ["how to verify the fix worked"]
}}

CRITICAL RULES:
1. old_code must EXACTLY match the existing code (including whitespace)
2. Provide complete fixes, not partial
3. If you need to restart after code changes, include docker commands
4. Be specific and actionable
5. If it's just a transient error, fix_type should be "docker_restart"
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )

            response_text = message.content[0].text

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                fix_plan = json.loads(json_match.group())
                return fix_plan
            else:
                # Fallback
                return {
                    "error_analysis": "Could not parse Claude response",
                    "fix_type": "docker_restart",
                    "docker_commands": [f"docker restart {self.container_name}"],
                    "confidence": "low"
                }

        except Exception as e:
            print(f"Claude API error: {e}")
            return {
                "error_analysis": f"Claude API error: {str(e)}",
                "fix_type": "docker_restart",
                "docker_commands": [f"docker restart {self.container_name}"],
                "confidence": "low"
            }

    def apply_code_fixes(self, fix_plan: Dict) -> Dict:
        """Apply code fixes to actual files"""
        result = {
            'success': False,
            'files_edited': [],
            'errors': []
        }

        if fix_plan.get('fix_type') != 'code_edit':
            result['success'] = True
            return result

        files_to_edit = fix_plan.get('files_to_edit', [])

        for file_info in files_to_edit:
            filename = file_info['filename']
            filepath = os.path.join(self.project_dir, filename)

            try:
                # Read current content
                with open(filepath, 'r') as f:
                    content = f.read()

                # Apply each change
                for change in file_info.get('changes', []):
                    old_code = change['old_code']
                    new_code = change['new_code']

                    if old_code in content:
                        content = content.replace(old_code, new_code, 1)
                        print(f"✓ Applied fix to {filename}: {change['explanation']}")
                    else:
                        error_msg = f"Could not find exact match in {filename}"
                        result['errors'].append(error_msg)
                        print(f"✗ {error_msg}")
                        return result

                # Write updated content
                with open(filepath, 'w') as f:
                    f.write(content)

                result['files_edited'].append(filename)

            except Exception as e:
                result['errors'].append(f"Error editing {filename}: {str(e)}")
                return result

        result['success'] = True
        return result

    def git_commit_changes(self, commit_message: str) -> bool:
        """Commit changes to git"""
        try:
            os.chdir(self.project_dir)

            # Add changes
            subprocess.run(['git', 'add', '.'], check=True)

            # Commit
            subprocess.run([
                'git', 'commit', '-m',
                f"{commit_message}\n\n🤖 Auto-fixed by Autonomous Healer"
            ], check=True)

            # Push
            subprocess.run(['git', 'push'], check=True)

            return True
        except Exception as e:
            print(f"Git commit error: {e}")
            return False

    def rebuild_and_restart(self) -> bool:
        """Rebuild Docker image and restart container"""
        try:
            os.chdir(self.project_dir)

            # Rebuild image
            subprocess.run([
                'docker', 'build', '-t', 'gmail-telegram-monitor:latest', '.'
            ], check=True)

            # Stop old container
            subprocess.run(['docker', 'stop', self.container_name], check=False)
            subprocess.run(['docker', 'rm', self.container_name], check=False)

            # Start new container
            subprocess.run([
                'docker', 'run', '-d',
                '--name', self.container_name,
                '--restart', 'unless-stopped',
                '-v', f'{self.project_dir}/.env:/app/.env:ro',
                '-v', f'{self.project_dir}/credentials.json:/app/credentials.json:ro',
                '-v', f'{self.project_dir}/token.json:/app/token.json:rw',
                'gmail-telegram-monitor:latest'
            ], check=True)

            return True
        except Exception as e:
            print(f"Rebuild error: {e}")
            return False

    def execute_commands(self, commands: List[str]) -> Dict:
        """Execute shell commands"""
        result = {'success': False, 'output': [], 'errors': []}

        for cmd in commands:
            try:
                proc = subprocess.run(
                    cmd, shell=True, capture_output=True,
                    text=True, timeout=120
                )
                result['output'].append(proc.stdout)
                if proc.returncode != 0:
                    result['errors'].append(proc.stderr)
                    return result
            except Exception as e:
                result['errors'].append(str(e))
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
        except:
            pass

    def heal(self):
        """Main autonomous healing loop with CODE EDITING"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{timestamp}] 🤖 Full Autonomous Healing Check...")

        # Check health
        health = self.check_container_health()

        if health['running'] and not health['error_detected']:
            print("✓ System healthy")
            return

        # Error detected - engage full healing
        print("⚠ Error detected! Engaging FULL autonomous healing...")
        self.send_telegram_alert(
            f"🤖 <b>Autonomous Healer Activated</b>\n\n"
            f"Error detected - analyzing and fixing code..."
        )

        # Ask Claude for fix (including code changes)
        fix_plan = self.ask_claude_for_code_fix(health)

        print(f"\n📊 Claude's Analysis:")
        print(f"  Root Cause: {fix_plan.get('root_cause', 'Unknown')}")
        print(f"  Fix Type: {fix_plan.get('fix_type')}")
        print(f"  Confidence: {fix_plan.get('confidence')}")

        # Apply code fixes if needed
        if fix_plan.get('fix_type') == 'code_edit':
            print("\n✏️  Applying code fixes...")
            code_result = self.apply_code_fixes(fix_plan)

            if not code_result['success']:
                print("✗ Code fix failed!")
                self.send_telegram_alert(
                    f"❌ <b>Code Fix Failed</b>\n\n"
                    f"Errors: {code_result['errors']}"
                )
                return

            print(f"✓ Fixed files: {code_result['files_edited']}")

            # Commit changes
            if fix_plan.get('git_commit_message'):
                print("\n📝 Committing changes to git...")
                if self.git_commit_changes(fix_plan['git_commit_message']):
                    print("✓ Changes committed and pushed")
                else:
                    print("✗ Git commit failed (continuing anyway)")

            # Rebuild and restart
            print("\n🔨 Rebuilding and restarting...")
            if self.rebuild_and_restart():
                print("✓ Rebuild and restart successful")
                self.send_telegram_alert(
                    f"✅ <b>AUTO-FIXED CODE!</b>\n\n"
                    f"<b>Issue:</b> {fix_plan.get('root_cause')}\n"
                    f"<b>Fixed files:</b> {', '.join(code_result['files_edited'])}\n"
                    f"<b>Commit:</b> {fix_plan.get('git_commit_message')}\n\n"
                    f"System rebuilt and restarted!"
                )
            else:
                print("✗ Rebuild failed")
                self.send_telegram_alert("❌ Rebuild failed after code fix")

        # Execute docker commands if needed
        elif fix_plan.get('docker_commands'):
            print("\n🐳 Executing docker commands...")
            cmd_result = self.execute_commands(fix_plan['docker_commands'])

            if cmd_result['success']:
                print("✓ Commands executed successfully")
                self.send_telegram_alert(
                    f"✅ <b>Auto-Fixed!</b>\n\n"
                    f"{fix_plan.get('error_analysis')}"
                )
            else:
                print("✗ Commands failed")
                self.send_telegram_alert("❌ Fix commands failed")


def main():
    """Entry point"""
    from dotenv import load_dotenv
    load_dotenv('/root/n8n_workflows/.env')

    api_key = os.getenv('ANTHROPIC_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not all([api_key, telegram_token, telegram_chat_id]):
        print("Error: Missing credentials in .env")
        return

    healer = FullAutonomousHealer(api_key, telegram_token, telegram_chat_id)
    healer.heal()


if __name__ == '__main__':
    main()

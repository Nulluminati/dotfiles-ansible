# Create Hook Command

Help create Claude Code hooks in Python (using uv) or Bash.

## Process

1. Ask the user what type of hook they want to create:
   - **Event type**: Start, Stop, Notification, or ToolCall
   - **Language**: Python or Bash
   - **Hook purpose**: What should the hook do?

2. For Python hooks:
   - Create a new Python script in an appropriate location
   - Use uv to manage dependencies if needed
   - Make the script executable

3. For Bash hooks:
   - Create a simple bash script
   - Make it executable
   - Follow standard bash practices

4. Generate the settings.json hook configuration
   - Show the matcher pattern options
   - Provide the complete hook entry to add to settings.json

## Hook Event Types

- **PreToolUse**: Triggered before Claude executes any tool
- **PostToolUse**: Triggered after Claude completes a tool execution
- **Notification**: Triggered during Claude notifications
- **Stop**: Triggered when the main agent finishes
- **SubagentStop**: Triggered when a subagent finishes

## Common Matcher Patterns

- **Bash**: Matches bash command execution
- **Task**: Matches subagent/task tool calls
- **Glob**: Matches file pattern operations
- **Grep**: Matches content search operations
- **Read**: Matches file reading operations
- **Edit/MultiEdit**: Matches file editing operations
- **Write**: Matches file writing operations
- **WebFetch/WebSearch**: Matches web-related operations

## Example Hook Ideas

- **PostToolUse + Edit**: Auto-format code after Claude edits files
- **PreToolUse + Write**: Block writes to production config files
- **Stop**: Play sound or send notification when task completes
- **PreToolUse + Bash**: Log all bash commands before execution
- **PostToolUse + Write**: Run linting after file writes
- **Notification**: Send alerts to external monitoring systems

## Example Hook Implementations

### 1. Python Auto-Formatter Hook
**Purpose**: Automatically format Python files after Claude edits them

**Python Script** (`~/.claude/hooks/python-formatter.py`):
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "black",
# ]
# ///

"""Python Auto-Formatter Hook for Claude.

Automatically formats Python files using black after Claude edits them.
Uses uv script dependencies for black formatting.
"""

import json
import os
import subprocess
import sys


def main() -> None:
    """Format Python files after Claude edits them.
    
    Triggered on: PostToolUse + Edit
    Processes: .py files only
    """
    try:
        hook_data = json.loads(sys.stdin.read())
        
        if hook_data.get("tool") == "Edit":
            file_path = hook_data.get("parameters", {}).get("file_path", "")
            if file_path.endswith(".py"):
                subprocess.run(["black", file_path], check=True)
                print(f"✓ Formatted {file_path}")
    except subprocess.CalledProcessError:
        print(f"✗ Failed to format {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Settings.json entry**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run ~/.claude/hooks/python-formatter.py"
          }
        ]
      }
    ]
  }
}
```

### 2. Production File Protection Hook
**Purpose**: Prevent Claude from modifying production configuration files

**Bash Script** (`~/.claude/hooks/protect-prod.sh`):
```bash
#!/bin/bash
# Production File Protection Hook
# Prevents Claude from writing to production configuration files
# Blocks Write operations to files matching production patterns

set -euo pipefail

# Read hook data from stdin
hook_data=$(cat)

# Extract file path from the hook data
file_path=$(echo "$hook_data" | jq -r '.parameters.file_path // empty')

# Check if file matches production patterns
if [[ "$file_path" =~ \.(prod|production)\.yaml$ ]] || 
   [[ "$file_path" =~ /prod/ ]] || 
   [[ "$file_path" =~ /production/ ]]; then
    echo "🚫 BLOCKED: Cannot modify production file: $file_path"
    echo '{"decision": "block", "message": "Production files are protected"}' | jq .
    exit 1
fi

echo "✓ Write allowed for: $file_path"
exit 0
```

**Settings.json entry**:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/protect-prod.sh"
          }
        ]
      }
    ]
  }
}
```

### 3. TTS Notification Hook
**Purpose**: Provide audio feedback for Claude tool execution with TTS and notifications

**Python Script** (`~/.claude/hooks/tts-notification.py`):
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pyttsx3",
# ]
# ///

"""TTS notification script for Claude hooks.

This script provides audio feedback for Claude tool execution by parsing JSON
input from stdin and converting tool execution information into speech using
offline text-to-speech. It supports both desktop notifications and TTS output.
"""

import argparse
import json
import platform
import random
import subprocess
import sys
from typing import Dict, Any, Optional, List


def send_notification(title: str, message: str) -> None:
    """Send desktop notification based on platform.
    
    Args:
        title: Notification title
        message: Notification message
    """
    system = platform.system().lower()

    try:
        if system == 'linux':
            subprocess.run(['notify-send', title, message], check=False)
        elif system == 'darwin':
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], check=False)
        else:
            print(f"📱 {title}: {message}")
    except (FileNotFoundError, Exception) as e:
        print(f"📱 {title}: {message}")


def speak_text(text: str) -> None:
    """Speak the given text using TTS engine.
    
    Args:
        text: Text to be spoken
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.setProperty('volume', 0.8)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"❌ TTS Error: {e}")


def generate_tts_message(data: Dict[str, Any]) -> str:
    """Generate appropriate TTS message based on tool execution data."""
    hook_event_name = data.get('hook_event_name', '')
    tool = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})
    
    if hook_event_name == "Stop":
        return "Claude Code Finished"
    elif tool == 'Bash':
        command = tool_input.get('command', '')
        return f"Bash command executed: {command}" if command else "Bash command completed"
    elif tool in ['Edit', 'Read', 'Write']:
        file_path = tool_input.get('file_path', '')
        filename = file_path.split('/')[-1] if file_path else 'file'
        action = 'Edited' if tool == 'Edit' else 'Read' if tool == 'Read' else 'Created'
        return f"{action} {filename}"
    elif tool == 'TodoWrite':
        todos = tool_input.get('todos', [])
        completed_todos = [todo for todo in todos if todo.get('status') == 'completed']
        if completed_todos:
            return f"Marked {len(completed_todos)} task(s) as complete"
        return "Updated todo list"
    elif tool:
        return f"Tool {tool} executed successfully"
    else:
        return "Hook executed!"


def main() -> None:
    """Main entry point for TTS notification script."""
    parser = argparse.ArgumentParser(description='TTS notification script for Claude hooks')
    parser.add_argument('--tts', action='store_true', help='Enable text-to-speech output')
    parser.add_argument('--notifications', action='store_true', help='Enable desktop notifications')
    args = parser.parse_args()
    
    if not args.tts and not args.notifications:
        return

    try:
        input_data = sys.stdin.read()
        if input_data.strip():
            data = json.loads(input_data)
            text = generate_tts_message(data)
        else:
            text = random.choice(["Hook executed!", "Task complete!", "Ready for next command!"])
        
        if args.notifications:
            send_notification("Claude", text)
        if args.tts:
            speak_text(text)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Settings.json entry** (with TTS and notifications):
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run ~/.claude/hooks/tts-notification.py --tts --notifications"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run ~/.claude/hooks/tts-notification.py --tts --notifications"
          }
        ]
      }
    ]
  }
}
```

**Settings.json entry** (TTS only):
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run ~/.claude/hooks/tts-notification.py --tts"
          }
        ]
      }
    ]
  }
}
```

### 4. Command Logger Hook
**Purpose**: Log all bash commands Claude executes

**Bash Script** (`~/.claude/hooks/log-commands.sh`):
```bash
#!/bin/bash
# Command Logger Hook
# Logs all bash commands executed by Claude to a timestamped file
# Creates detailed audit trail of Claude's command execution

set -euo pipefail

LOG_FILE="$HOME/.claude/logs/commands-$(date +%Y%m%d).log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read hook data from stdin
hook_data=$(cat)

# Extract command from the hook data
command=$(echo "$hook_data" | jq -r '.parameters.command // empty')

# Log the command with timestamp
echo "$(date '+%Y-%m-%d %H:%M:%S') - $command" >> "$LOG_FILE"

echo "✓ Command logged: $command"
exit 0
```

**Settings.json entry**:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/log-commands.sh"
          }
        ]
      }
    ]
  }
}
```

## Settings.json Integration

After creating the hook script, provide the exact JSON to add to the hooks section of settings.json, including proper matcher patterns and command paths.

**Complete settings.json structure**:
```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here"
          }
        ]
      }
    ]
  }
}
```
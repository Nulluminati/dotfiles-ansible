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
            # Use notify-send on Linux
            subprocess.run(['notify-send', title, message], check=False)
        elif system == 'darwin':
            # Use osascript on macOS
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], check=False)
        else:
            # Unsupported platform - just print
            print(f"📱 {title}: {message}")
    except Exception as e:
        # Any other error - just print
        print(f"📱 {title}: {message} (notification error: {e})")

def generate_tts_message(data: Dict[str, Any]) -> str:
    """Generate appropriate TTS message based on tool execution data.
    
    Args:
        data: JSON data containing tool execution information
        
    Returns:
        Text message to be spoken
    """
    hook_event_name = data.get('hook_event_name', '')
    tool = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})
    command = tool_input.get('command', '')
    file_path = tool_input.get('file_path', '')

    if hook_event_name == "Stop":
        return "Claude Code Finished"
    elif tool == 'Bash':
        return (f"Bash command executed: {command}" 
                if command else "Bash command completed")
    elif tool == 'Edit' || tool == 'MultiEdit':
        filename = file_path.split('/')[-1] if file_path else 'file'
        return f"Edited {filename}"
    elif tool == 'Read':
        filename = file_path.split('/')[-1] if file_path else 'file'
        return f"Read {filename}"
    elif tool == 'Write':
        filename = file_path.split('/')[-1] if file_path else 'file'
        return f"Created {filename}"
    elif tool == 'TodoWrite':
        todos = tool_input.get('todos', [])
        completed_todos = [todo for todo in todos 
                          if todo.get('status') == 'completed']
        if completed_todos:
            completed_count = len(completed_todos)
            return f"Marked {completed_count} task(s) as complete"
        else:
            return "Updated todo list"
    elif tool:
        return f"Tool {tool} executed successfully"
    else:
        return json.dumps(data, indent=2)


def speak_text(text: str) -> None:
    """Speak the given text using TTS engine.
    
    Args:
        text: Text to be spoken
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        # Configure engine settings
        engine.setProperty('rate', 180)    # Speech rate (words per minute)
        engine.setProperty('volume', 0.8)  # Volume (0.0 to 1.0)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"❌ TTS Error: {e}")


def get_default_message() -> str:
    """Get a random default message for empty input.
    
    Returns:
        Random completion message
    """
    messages = [
        "Hook executed!",
        "Task complete!",
        "Operation finished!",
        "Ready for next command!"
    ]
    return random.choice(messages)


def parse_input() -> str:
    """Parse JSON input from stdin and generate TTS message.
    
    Returns:
        Text message to be spoken or sent as notification
    """
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            return get_default_message()
        
        data = json.loads(input_data)
        return generate_tts_message(data)
        
    except json.JSONDecodeError:
        return "Invalid JSON input received"
    except Exception as e:
        return f"Input parsing error: {str(e)}"


def main() -> None:
    """Main entry point for TTS notification script.
    
    Parses JSON input from stdin containing tool execution information
    and provides audio feedback using offline text-to-speech.
    
    Features:
    - Offline TTS (no API key required)
    - JSON input parsing from stdin
    - Tool-specific audio feedback
    - Cross-platform compatibility
    """
    parser = argparse.ArgumentParser(
        description='TTS notification script for Claude hooks'
    )
    parser.add_argument('--tts', action='store_true', 
                       help='Enable text-to-speech output')
    parser.add_argument('--notifications', action='store_true', 
                       help='Enable desktop notifications')
    args = parser.parse_args()
    
    # If no flags are provided, exit silently
    if not args.tts and not args.notifications:
        return

    try:
        text = parse_input()
        
        # Send desktop notification if enabled
        if args.notifications:
            send_notification("Claude", text)

        # Speak the text if enabled
        if args.tts:
            speak_text(text)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
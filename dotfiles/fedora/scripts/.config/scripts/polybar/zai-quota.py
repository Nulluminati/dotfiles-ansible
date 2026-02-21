#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
zai-quota.py

Displays remaining API quota and time until reset for zai (api.z.ai).
Shows TOKENS_LIMIT and TIME_LIMIT quotas.
Intended for use in polybar.

Usage: zai-quota.py
"""

import requests
import os
import sys
from datetime import datetime, timezone


def format_time_remaining(minutes_remaining):
    """Format time remaining in compact form (e.g., '4h 30m', '45m')."""
    if minutes_remaining is None:
        return ""
    if minutes_remaining <= 0:
        return "now"

    hours = int(minutes_remaining // 60)
    minutes = int(minutes_remaining % 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def get_time_to_reset(next_reset_timestamp_ms):
    """Calculate minutes remaining until nextResetTime (Unix timestamp in milliseconds)."""
    if not next_reset_timestamp_ms:
        return None

    now = datetime.now(timezone.utc)
    reset_time = datetime.fromtimestamp(next_reset_timestamp_ms / 1000, tz=timezone.utc)
    diff = reset_time - now

    return max(0, diff.total_seconds() / 60)


def get_color(percentage_remaining):
    """Return color based on percentage remaining."""
    if percentage_remaining > 50:
        return "#2aa198"  # Green
    elif percentage_remaining >= 20:
        return "#b58900"  # Yellow
    else:
        return "#dc322f"  # Red


def format_limit(limit_data, icon="", show_time=True):
    """Format a single limit for display."""
    if not limit_data:
        if icon:
            return f"%{{F#dc322f}}{icon}?%{{F-}}"
        return "%{{F#dc322f}}?%{{F-}}"

    percentage_used = limit_data.get("percentage", 0)
    percentage_remaining = 100 - percentage_used
    color = get_color(percentage_remaining)

    next_reset_ms = limit_data.get("nextResetTime")
    minutes_to_reset = get_time_to_reset(next_reset_ms)
    time_remaining = format_time_remaining(minutes_to_reset) if (minutes_to_reset is not None and show_time) else ""

    prefix = f"{icon} " if icon else ""
    if time_remaining:
        return f"{prefix}%{{F{color}}}{int(percentage_remaining)}%%{{F-}} [{time_remaining}]"
    else:
        return f"{prefix}%{{F{color}}}{int(percentage_remaining)}%%{{F-}}"


# ZAI API Key
api_key = os.environ.get('ZAI_API_KEY', '')

if not api_key:
    print("%{{F#dc322f}}?%{{F-}}")
    sys.exit(1)

# Get quota data from zai API
try:
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    response = requests.get(
        "https://api.z.ai/api/monitor/usage/quota/limit",
        headers=headers,
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
except Exception:
    print("%{{F#dc322f}}?%{{F-}}")
    sys.exit(1)

# Extract quota data
try:
    limits = data.get("data", {}).get("limits", [])

    # Find limits by type
    tokens_limit = None
    time_limit = None
    for item in limits:
        if item.get("type") == "TOKENS_LIMIT":
            tokens_limit = item
        elif item.get("type") == "TIME_LIMIT":
            time_limit = item

    if tokens_limit is None and time_limit is None:
        print("%{{F#dc322f}}?%{{F-}}")
        sys.exit(1)

    # Format main token limit (no icon, with time)
    tokens_str = format_limit(tokens_limit, icon="", show_time=True)

    # Format time limit (search icon for web tool rate limits, no time)
    time_str = format_limit(time_limit, icon="\uf002", show_time=False)

    # Output both quotas
    if tokens_str and time_str:
        print(f"{tokens_str} · {time_str}")
    elif tokens_str:
        print(tokens_str)
    else:
        print(time_str)

except (KeyError, TypeError):
    print("%{{F#dc322f}}?%{{F-}}")
    sys.exit(1)

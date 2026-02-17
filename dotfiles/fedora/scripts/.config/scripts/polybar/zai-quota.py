#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
zai-quota.py

Displays remaining API quota and time until reset for zai (api.z.ai) subscription.
Intended for use in polybar.

Usage: zai-quota.py
"""

import requests
import os
import sys
from datetime import datetime, timezone


def format_time_remaining(minutes_remaining):
    """Format time remaining in compact form (e.g., '4h 30m', '45m')."""
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

    return max(0, diff.total_seconds() / 60)  # Return minutes remaining


# ZAI API Key
api_key = os.environ.get('ZAI_API_KEY', '')

if not api_key:
    print("%{F#dc322f}?%{F-}")
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
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

# Extract quota data
try:
    limits = data.get("data", {}).get("limits", [])

    # Find TOKENS_LIMIT (main API quota)
    tokens_limit = None
    for item in limits:
        if item.get("type") == "TOKENS_LIMIT":
            tokens_limit = item
            break

    if tokens_limit is None:
        print("%{F#dc322f}?%{F-}")
        sys.exit(1)

    # Get percentage (0-100, where 100 means fully used)
    percentage_used = tokens_limit.get("percentage", 0)
    percentage_remaining = 100 - percentage_used

    # Determine color based on percentage remaining
    if percentage_remaining > 50:
        color = "#2aa198"  # Green
    elif percentage_remaining >= 20:
        color = "#b58900"  # Yellow
    else:
        color = "#dc322f"  # Red

    # Get time to next reset from API response
    next_reset_ms = tokens_limit.get("nextResetTime")
    minutes_to_reset = get_time_to_reset(next_reset_ms)
    time_remaining = format_time_remaining(minutes_to_reset) if minutes_to_reset is not None else "5h 0m"

    # Output formatted percentage with polybar color tags
    if time_remaining:
        print(f"%{{F{color}}}{int(percentage_remaining)}%%{{F-}} ({time_remaining})")
    else:
        print(f"%{{F{color}}}{int(percentage_remaining)}%%{{F-}}")

except (KeyError, TypeError):
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

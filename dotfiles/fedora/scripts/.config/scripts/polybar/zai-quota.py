#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
zai-quota.py

Displays remaining API quota and time until reset for zai (api.z.ai).
Shows TOKENS_LIMIT and TIME_LIMIT quotas, plus available quota reset
cards for the 5-hour and weekly pools (green count when >= 1).
Intended for use in polybar.

Usage: zai-quota.py
"""

import requests
import os
import sys
from datetime import datetime, timezone

GREEN = "#2aa198"
RED = "#dc322f"

QUOTA_URL = "https://api.z.ai/api/monitor/usage/quota/limit"
RESETS_URL = "https://api.z.ai/api/biz/customer-package-reset/list?targetType=PERSONAL"

# Clock marks the 5-hour reset pool, calendar the weekly pool,
# matching the window icons used by openai-usage.py.
FIVE_HOUR_RESET_ICON = "\uf017"
WEEK_RESET_ICON = "\uf073"


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
        return GREEN
    elif percentage_remaining >= 20:
        return "#b58900"  # Yellow
    else:
        return RED


def format_limit(limit_data, icon="", show_time=True):
    """Format a single limit for display."""
    if not limit_data:
        if icon:
            return f"%{{F{RED}}}{icon}?%{{F-}}"
        return f"%{{F{RED}}}?%{{F-}}"

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


def count_available(cards):
    """Count reset cards that are still available."""
    if not cards:
        return 0
    return sum(1 for card in cards if card.get("available"))


def format_resets(reset_data):
    """Format available quota reset counts for the 5-hour and weekly pools.

    Green count when any card is available, plain 0 otherwise.
    Returns "" when no reset data could be fetched.
    """
    if not reset_data:
        return ""

    parts = []
    for icon, key in [
        (FIVE_HOUR_RESET_ICON, "fiveHourResets"),
        (WEEK_RESET_ICON, "weekResets"),
    ]:
        count = count_available(reset_data.get(key))
        if count > 0:
            parts.append(f"{icon} %{{F{GREEN}}}{count}%{{F-}}")
        else:
            parts.append(f"{icon} 0")
    return " ".join(parts)


def fetch_quota(api_key):
    """Fetch quota limits from the zai monitor API."""
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    response = requests.get(QUOTA_URL, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_resets(api_key):
    """Fetch available quota reset cards (5-hour and weekly pools)."""
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    response = requests.get(RESETS_URL, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def format_output(quota_data, reset_data):
    """Format quota limits plus reset card counts as a polybar label."""
    limits = quota_data.get("data", {}).get("limits", [])

    # Find limits by type
    tokens_limit = None
    time_limit = None
    for item in limits:
        if item.get("type") == "TOKENS_LIMIT":
            tokens_limit = item
        elif item.get("type") == "TIME_LIMIT":
            time_limit = item

    if tokens_limit is None and time_limit is None:
        raise ValueError("no usable limits in quota response")

    # Format main token limit (no icon, with time)
    tokens_str = format_limit(tokens_limit, icon="", show_time=True)

    # Format time limit (search icon for web tool rate limits, no time)
    time_str = format_limit(time_limit, icon="\uf002", show_time=False)

    parts = [tokens_str, time_str]

    # Append reset card counts (best effort - omitted when unavailable)
    reset_str = format_resets(reset_data)
    if reset_str:
        parts.append(reset_str)

    return " · ".join(parts)


def main():
    # ZAI API Key
    api_key = os.environ.get("ZAI_API_KEY", "")

    if not api_key:
        print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(1)

    # Get quota data from zai API
    try:
        quota_data = fetch_quota(api_key)
    except Exception:
        print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(1)

    # Reset cards are additive - a failed lookup still shows quota
    try:
        reset_data = fetch_resets(api_key).get("data")
    except Exception:
        reset_data = None

    # Extract quota data
    try:
        print(format_output(quota_data, reset_data))
    except (KeyError, TypeError, ValueError):
        print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(1)


if __name__ == "__main__":
    main()

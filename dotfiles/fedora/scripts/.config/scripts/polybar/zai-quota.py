#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
zai-quota.py

Displays remaining zai (api.z.ai) coding-plan quota in polybar.
Shows the 5-hour and weekly token windows (clock and calendar icons,
percentage remaining, time until reset), and available quota reset
cards per pool (green count when >= 1).
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

# The two token pools use the same window icons as openai-usage.py.
FIVE_HOUR_ICON = "\uf017"
WEEK_ICON = "\uf073"

# Token window units from the quota API: 3 = hours (the 5-hour pool),
# 6 = weeks (the weekly pool). Verified against live responses.
UNIT_HOURS = 3
UNIT_WEEKS = 6


def format_time_remaining(minutes_remaining):
    """Format time remaining in compact form (e.g., '4d 13h', '4h 30m', '45m')."""
    if minutes_remaining is None:
        return ""
    if minutes_remaining <= 0:
        return "now"

    total_minutes = int(minutes_remaining)
    days = total_minutes // (24 * 60)
    hours = (total_minutes % (24 * 60)) // 60
    minutes = total_minutes % 60

    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
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
    """Format a single limit window for display."""
    percentage_used = limit_data.get("percentage", 0)
    percentage_remaining = max(0, min(100, 100 - percentage_used))
    color = get_color(percentage_remaining)

    next_reset_ms = limit_data.get("nextResetTime")
    minutes_to_reset = get_time_to_reset(next_reset_ms)
    time_remaining = format_time_remaining(minutes_to_reset) if (minutes_to_reset is not None and show_time) else ""

    prefix = f"{icon} " if icon else ""
    if time_remaining:
        return f"{prefix}%{{F{color}}}{int(percentage_remaining)}%%{{F-}} [{time_remaining}]"
    else:
        return f"{prefix}%{{F{color}}}{int(percentage_remaining)}%%{{F-}}"


def find_limits(limits):
    """Split the token windows into (five_hour, week) by unit.

    Token windows are identified by unit; when units are missing or
    unknown, the window that resets sooner is treated as the 5-hour pool.
    Search-tool TIME_LIMIT entries are ignored.
    """
    token_limits = [l for l in limits if l.get("type") == "TOKENS_LIMIT"]

    five_hour = next((l for l in token_limits if l.get("unit") == UNIT_HOURS), None)
    week = next((l for l in token_limits if l.get("unit") == UNIT_WEEKS), None)

    if five_hour is None and week is None:
        by_reset = sorted(token_limits, key=lambda l: l.get("nextResetTime") or 0)
        if len(by_reset) == 1:
            five_hour = by_reset[0]
        elif len(by_reset) >= 2:
            five_hour, week = by_reset[0], by_reset[-1]
    else:
        identified = [l for l in (five_hour, week) if l is not None]
        others = [l for l in token_limits if all(l is not x for x in identified)]
        if len(others) == 1:
            if five_hour is None:
                five_hour = others[0]
            else:
                week = others[0]

    return five_hour, week


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
        (FIVE_HOUR_ICON, "fiveHourResets"),
        (WEEK_ICON, "weekResets"),
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
    """Format the token windows and reset cards as a polybar label."""
    limits = quota_data.get("data", {}).get("limits", [])

    five_hour_limit, week_limit = find_limits(limits)
    if five_hour_limit is None and week_limit is None:
        raise ValueError("no usable limits in quota response")

    parts = []
    for limit, icon in [
        (five_hour_limit, FIVE_HOUR_ICON),
        (week_limit, WEEK_ICON),
    ]:
        if limit is not None:
            parts.append(format_limit(limit, icon=icon))

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

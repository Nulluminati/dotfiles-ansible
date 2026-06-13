#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
opencode-go-usage.py

Displays OpenCode Go subscription usage.
Shows 5-hour rolling, weekly, and monthly usage percentages plus time to reset.
Intended for use in polybar.

Usage: uv run opencode-go-usage.py
"""

import os
import sys

import requests


# OpenCode Go API endpoint for usage
USAGE_URL = "https://opencode.ai/zen/go/v1/usage"

# Colors (solarized)
GREEN = "#2aa198"
YELLOW = "#b58900"
RED = "#dc322f"


def format_time_remaining(seconds):
    """Format seconds remaining until window reset."""
    if seconds is None or seconds <= 0:
        return "now"

    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)
    minutes %= 60
    hours %= 24

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def color_for_percent(usage_percent):
    """Return color based on percent used (higher usage = warmer color)."""
    remaining = 100 - usage_percent
    if remaining >= 50:
        return GREEN
    elif remaining >= 20:
        return YELLOW
    return RED


def format_window(data, icon=""):
    """Format a single usage window for display."""
    if not data:
        return ""

    usage_percent = data.get("usagePercent", 0)
    reset_in_sec = data.get("resetInSec", 0)
    status = data.get("status", "ok")

    color = color_for_percent(usage_percent)
    time_str = format_time_remaining(reset_in_sec)
    prefix = f"{icon} " if icon else ""

    if status == "rate-limited":
        return f"{prefix}%{{F{RED}}}{usage_percent}%% [lim]%{{F-}}"

    return f"{prefix}%{{F{color}}}{usage_percent}%% [{time_str}]%{{F-}}"


def main():
    api_key = os.environ.get("OPENCODE_API_KEY", "")
    if not api_key:
        print("%{F#dc322f}go:?%{F-}")
        sys.exit(1)

    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(USAGE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        print("%{F#dc322f}go:?%{F-}")
        sys.exit(1)

    try:
        parts = []

        rolling = data.get("rollingUsage")
        if rolling:
            parts.append(format_window(rolling, icon="\uf017"))

        weekly = data.get("weeklyUsage")
        if weekly:
            parts.append(format_window(weekly, icon="\uf073"))

        monthly = data.get("monthlyUsage")
        if monthly:
            parts.append(format_window(monthly, icon="\uf133"))

        if not parts:
            print("%{F#dc322f}go:?%{F-}")
            sys.exit(1)

        if data.get("useBalance"):
            parts.append("\uf155")

        print(f"{' · '.join(parts)}")

    except (KeyError, TypeError):
        print("%{F#dc322f}go:?%{F-}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
synthetic-quota.py

Displays remaining API quota for synthetic.new.
Shows 5-hour rolling, weekly token, and search hourly quotas.
Each shows: remaining count/$ / percentage / time to reset
Intended for use in polybar.

Usage: synthetic-quota.py
"""

import requests
import os
import sys
from datetime import datetime, timezone


def format_time_remaining_iso(renews_at_str):
    """Format time remaining until renewal in compact form."""
    if not renews_at_str:
        return ""
    try:
        renews_at = datetime.fromisoformat(renews_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)

        diff = renews_at - now
        if diff.total_seconds() <= 0:
            return "now"

        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60

        if days > 0:
            return f"{days}d"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except (ValueError, TypeError):
        return ""


def get_color(percentage):
    """Return color based on percentage remaining."""
    if percentage > 50:
        return "#2aa198"  # Green
    elif percentage >= 20:
        return "#b58900"  # Yellow
    else:
        return "#dc322f"  # Red


def format_rolling_quota(data, icon=""):
    """Format 5-hour rolling limit: remaining / percentage / time."""
    if not data:
        return ""

    remaining = data.get("remaining", 0)
    max_limit = data.get("max", 0)

    if max_limit == 0:
        return ""

    percentage = (remaining / max_limit) * 100
    color = get_color(percentage)

    next_tick = data.get("nextTickAt")
    time_str = format_time_remaining_iso(next_tick)

    prefix = f"{icon} " if icon else ""
    return f"{prefix}%{{F{color}}}{remaining:.2f}/{int(percentage)}%%{{F-}} [{time_str}]"


def format_weekly_token(data, icon=""):
    """Format weekly token limit: $ remaining / percentage / time."""
    if not data:
        return ""

    remaining_str = data.get("remainingCredits", "$0.00").replace("$", "")
    try:
        remaining = float(remaining_str)
    except ValueError:
        remaining = 0

    percent_remaining = data.get("percentRemaining", 0)
    color = get_color(percent_remaining)

    next_regen = data.get("nextRegenAt")
    time_str = format_time_remaining_iso(next_regen)

    prefix = f"{icon} " if icon else ""
    return f"{prefix}%{{F{color}}}${remaining:.2f}/{int(percent_remaining)}%%{{F-}} [{time_str}]"


def format_search_quota(data, icon=""):
    """Format search hourly limit: remaining / percentage / time."""
    if not data:
        return ""

    limit = data.get("limit", 0)
    used = data.get("requests", 0)

    if limit == 0:
        return ""

    remaining = limit - used
    percentage = (remaining / limit) * 100
    color = get_color(percentage)

    renews_at = data.get("renewsAt")
    time_str = format_time_remaining_iso(renews_at)

    prefix = f"{icon} " if icon else ""
    return f"{prefix}%{{F{color}}}{remaining:.2f}/{int(percentage)}%%{{F-}} [{time_str}]"


# Synthetic API Key
api_key = os.environ.get('SYNTHETIC_API_KEY', '')

if not api_key:
    print("%{{F#dc322f}}syn:?%{{F-}}")
    sys.exit(1)

# Get quota data from synthetic.new API
try:
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.synthetic.new/v2/quotas", headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception:
    print("%{{F#dc322f}}syn:?%{{F-}}")
    sys.exit(1)

# Build output with exactly 3 items: 5-hour, weekly, search
try:
    parts = []

    # 5-hour rolling - clock icon
    rolling = data.get("rollingFiveHourLimit", {})
    if rolling:
        rolling_str = format_rolling_quota(rolling, icon="\uf017")
        if rolling_str:
            parts.append(rolling_str)

    # Weekly token - dollar icon
    weekly = data.get("weeklyTokenLimit", {})
    if weekly:
        weekly_str = format_weekly_token(weekly, icon="\uf155")
        if weekly_str:
            parts.append(weekly_str)

    # Search hourly - magnifying glass icon
    search = data.get("search", {}).get("hourly", {})
    if search.get("limit", 0) > 0:
        search_str = format_search_quota(search, icon="\uf002")
        if search_str:
            parts.append(search_str)

    # Output with dot separator
    if parts:
        print(f"{' · '.join(parts)}")
    else:
        print("%{{F#dc322f}}syn:?%{{F-}}")

except (KeyError, TypeError, ZeroDivisionError):
    print("%{{F#dc322f}}syn:?%{{F-}}")
    sys.exit(1)

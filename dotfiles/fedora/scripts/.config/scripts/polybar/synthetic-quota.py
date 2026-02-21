#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
synthetic-quota.py

Displays remaining API quota and time until renewal for synthetic.new.
Shows subscription, search.hourly, and freeToolCalls quotas.
Intended for use in polybar.

Usage: synthetic-quota.py
"""

import requests
import os
import sys
from datetime import datetime, timezone


def format_time_remaining(renews_at_str):
    """Format time remaining until renewal in compact form (e.g., '2d', '5h 30m', '45m')."""
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


def format_quota(limit, used, renews_at, icon="", show_time=True):
    """Format a single quota for display."""
    if limit == 0:
        if icon:
            return f"%{{F#dc322f}}{icon}?%{{F-}}"
        return "%{{F#dc322f}}?%{{F-}}"

    remaining = limit - used
    percentage = (remaining / limit) * 100
    color = get_color(percentage)
    time_remaining = format_time_remaining(renews_at) if (renews_at and show_time) else ""

    prefix = f"{icon} " if icon else ""
    if time_remaining:
        return f"{prefix}%{{F{color}}}{int(percentage)}%%{{F-}} [{time_remaining}]"
    else:
        return f"{prefix}%{{F{color}}}{int(percentage)}%%{{F-}}"


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

# Extract and format all quotas
try:
    # Subscription (main API quota) - no icon
    sub = data.get("subscription", {})
    sub_str = format_quota(sub.get("limit", 0), sub.get("requests", 0), sub.get("renewsAt"))

    # Search (hourly quota) - magnifying glass icon, no time
    search = data.get("search", {}).get("hourly", {})
    search_str = format_quota(search.get("limit", 0), search.get("requests", 0), search.get("renewsAt"), icon="\uf002", show_time=False)

    # Free tool calls (daily quota) - wrench icon, no time
    free = data.get("freeToolCalls", {})
    free_str = format_quota(free.get("limit", 0), free.get("requests", 0), free.get("renewsAt"), icon="\uf0ad", show_time=False)

    # Output all quotas with dot separator
    print(f"{sub_str} · {search_str} · {free_str}")

except (KeyError, TypeError, ZeroDivisionError):
    print("%{{F#dc322f}}syn:?%{{F-}}")
    sys.exit(1)

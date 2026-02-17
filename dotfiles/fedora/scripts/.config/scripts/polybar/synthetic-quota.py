#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
synthetic-quota.py

Displays remaining API quota and time until renewal for synthetic.new subscription.
Intended for use in polybar.

Usage: synthetic-quota.py
"""

import requests
import os
import sys
from datetime import datetime, timezone


def format_time_remaining(renews_at_str):
    """Format time remaining until renewal in compact form (e.g., '2d 5h', '3h 20m')."""
    try:
        # Parse ISO 8601 timestamp
        renews_at = datetime.fromisoformat(renews_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)

        diff = renews_at - now
        if diff.total_seconds() <= 0:
            return "now"

        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except (ValueError, TypeError):
        return ""


# Synthetic API Key
api_key = os.environ.get('SYNTHETIC_API_KEY', '')

if not api_key:
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

# Get quota data from synthetic.new API
try:
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.synthetic.new/v2/quotas", headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception:
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

# Extract subscription data
try:
    subscription = data.get("subscription", {})
    limit = subscription.get("limit", 0)
    requests_used = subscription.get("requests", 0)
    renews_at = subscription.get("renewsAt")

    if limit == 0:
        print("%{F#dc322f}?%{F-}")
        sys.exit(1)

    # Calculate percentage remaining
    remaining = limit - requests_used
    percentage = (remaining / limit) * 100

    # Determine color based on percentage
    if percentage > 50:
        color = "#2aa198"  # Green
    elif percentage >= 20:
        color = "#b58900"  # Yellow
    else:
        color = "#dc322f"  # Red

    # Format time remaining until renewal
    time_remaining = format_time_remaining(renews_at) if renews_at else ""

    # Output formatted percentage with polybar color tags
    if time_remaining:
        print(f"%{{F{color}}}{int(percentage)}%%{{F-}} ({time_remaining})")
    else:
        print(f"%{{F{color}}}{int(percentage)}%%{{F-}}")

except (KeyError, TypeError, ZeroDivisionError):
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

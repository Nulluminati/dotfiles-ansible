#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
copilot-quota.py

Displays remaining GitHub Copilot premium interactions quota.
Intended for use in polybar.

Usage: copilot-quota.py
"""

import subprocess
import requests
import sys
from datetime import datetime, timezone


def get_copilot_token():
    """Get OAuth token from gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def format_days_until(reset_date_str):
    """Format days until reset date."""
    try:
        # Parse ISO 8601 timestamp
        reset_date = datetime.fromisoformat(reset_date_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = reset_date - now
        days = diff.days
        if days < 0:
            return "0d"
        return f"{days}d"
    except (ValueError, TypeError):
        return ""


token = get_copilot_token()

if not token:
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

# Get quota data from GitHub Copilot API
try:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    response = requests.get(
        "https://api.github.com/copilot_internal/user",
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
    quota_snapshots = data.get("quota_snapshots", {})
    premium = quota_snapshots.get("premium_interactions", {})

    entitlement = premium.get("entitlement", 0)
    remaining = premium.get("remaining", 0)
    used = entitlement - remaining

    if entitlement == 0:
        print("%{F#dc322f}?%{F-}")
        sys.exit(1)

    # Calculate percentage remaining
    percentage = (remaining / entitlement) * 100

    # Determine color based on percentage
    if percentage > 50:
        color = "#2aa198"  # Green
    elif percentage >= 20:
        color = "#b58900"  # Yellow
    else:
        color = "#dc322f"  # Red

    # Get days until reset
    reset_date = data.get("quota_reset_date_utc", "")
    days_until = format_days_until(reset_date) if reset_date else ""

    # Output format: used/limit (percentage) [days until reset]
    if days_until:
        print(f"%{{F{color}}}{used}/{entitlement} ({int(percentage)}%) %{{F-}}[{days_until}]")
    else:
        print(f"%{{F{color}}}{used}/{entitlement} ({int(percentage)}%)%{{F-}}")

except (KeyError, TypeError, ZeroDivisionError):
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

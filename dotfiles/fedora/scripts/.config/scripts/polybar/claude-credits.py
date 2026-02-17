#!/usr/bin/env python3
# /// script
# dependencies = ["browser-cookie3", "requests"]
# ///
"""\
claude-credits.py

Displays remaining Anthropic Claude prepaid credit balance.
Uses browser_cookie3 to extract session cookies automatically from Firefox/Chrome.

Usage: uv run claude-credits.py
"""

import os
import sys

import requests
import browser_cookie3


# Configuration
ORG_ID_PATH = os.path.expanduser("~/.config/anthropic/org_id")

# Colors (solarized scheme)
RED = "#dc322f"


def get_org_id():
    """Get organization ID from file."""
    try:
        with open(ORG_ID_PATH) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def get_browser_cookies():
    """Extract cookies from Firefox or Chrome for platform.claude.com."""
    # Try Firefox first (most reliable on Linux - no encryption issues)
    try:
        return browser_cookie3.firefox(domain_name="platform.claude.com")
    except Exception:
        pass

    # Fallback to Chrome/Chromium
    try:
        return browser_cookie3.chrome(domain_name="platform.claude.com")
    except Exception:
        pass

    return None


def fetch_balance(org_id, cookies):
    """Fetch prepaid credits from Anthropic console API."""
    headers = {
        "Accept": "application/json",
        "Referer": "https://platform.claude.com/settings/billing",
    }
    response = requests.get(
        f"https://platform.claude.com/api/organizations/{org_id}/prepaid/credits",
        cookies=cookies,
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def main():
    # Get org ID
    org_id = get_org_id()
    if not org_id:
        print("Setup")
        sys.exit(0)

    # Get cookies from browser
    cookies = get_browser_cookies()
    if not cookies:
        print("Login")
        sys.exit(0)

    # Try to fetch balance
    try:
        data = fetch_balance(org_id, cookies)
        amount_cents = data.get("amount", 0)
        balance_dollars = amount_cents / 100.0

        # Color red only when low balance (< $5)
        if balance_dollars < 5:
            print(f"%{{F{RED}}}${balance_dollars:.2f}%{{F-}}")
        else:
            print(f"${balance_dollars:.2f}")

    except requests.HTTPError as e:
        if e.response.status_code in (401, 403):
            print(f"%{{F{RED}}}Expired%{{F-}}")
        else:
            print(f"%{{F{RED}}}?%{{F-}}")
    except Exception:
        print(f"%{{F{RED}}}?%{{F-}}")


if __name__ == "__main__":
    main()

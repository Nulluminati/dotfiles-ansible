#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///
"""\
neuralwatt-credits.py

Displays remaining NeuralWatt Cloud credit balance (USD prepaid credits,
not subscription usage). Intended for use in polybar.

Usage: uv run neuralwatt-credits.py
"""

import os
import sys

import requests


# Configuration (solarized scheme)
RED = "#dc322f"
YELLOW = "#b58900"
API_URL = "https://api.neuralwatt.com/v1/quota"


def fetch_balance(api_key):
    """Fetch prepaid credit balance from NeuralWatt quota API.

    Returns credits_remaining_usd (float), defaulting to 0 when the
    balance field is absent.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(API_URL, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("balance", {}).get("credits_remaining_usd", 0)


def format_balance(balance):
    """Format balance for polybar display.

    Red below $1, yellow below $3, otherwise default foreground.
    """
    if balance < 1:
        return f"%{{F{RED}}}${balance:.2f}%{{F-}}"
    if balance < 3:
        return f"%{{F{YELLOW}}}${balance:.2f}%{{F-}}"
    return f"${balance:.2f}"


def main():
    api_key = os.environ.get("NEURALWATT_API_KEY", '')

    if not api_key:
        print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(1)

    try:
        balance = fetch_balance(api_key)
        print(format_balance(balance))
    except Exception:
        print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(1)


if __name__ == "__main__":
    main()

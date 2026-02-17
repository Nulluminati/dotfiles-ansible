#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""\
openrouter-balance.py

Displays remaining account balance for OpenRouter.
Intended for use in polybar.

Usage: openrouter-balance.py
"""

import requests
import os
import sys


# OpenRouter API Key
api_key = os.environ.get('OPENROUTER_API_KEY', '')

if not api_key:
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

# Get credits data from OpenRouter API
try:
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        "https://openrouter.ai/api/v1/credits",
        headers=headers,
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
except Exception:
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

# Extract balance data
try:
    total_credits = data.get("data", {}).get("total_credits", 0)
    total_usage = data.get("data", {}).get("total_usage", 0)

    # Calculate remaining balance
    balance = total_credits - total_usage

    # Determine color based on balance (only red if under $5)
    if balance < 5:
        print(f"$%{{F#dc322f}}{balance:.2f}%{{F-}}")
    else:
        print(f"${balance:.2f}")

except (KeyError, TypeError):
    print("%{F#dc322f}?%{F-}")
    sys.exit(1)

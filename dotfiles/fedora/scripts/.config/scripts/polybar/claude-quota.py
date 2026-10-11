#!/usr/bin/env python3
"""Display remaining Claude subscription quota in polybar.

Reads the OAuth access token Claude Code stores in ~/.claude/.credentials.json
and calls the usage endpoint behind Claude Code's /status. The token is never
refreshed here: refreshing can rotate the refresh token and log Claude Code
out, so an expired token shows "Expired" until Claude Code refreshes it.

The endpoint returns 429 quickly when polled hard, so responses are cached and
the last good values stay on screen (marked with *) when a fetch fails.

Usage: claude-quota.py
"""

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


GREEN = "#2aa198"
YELLOW = "#b58900"
RED = "#dc322f"

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
BETA_HEADER = "oauth-2025-04-20"
# The endpoint rate-limits requests without a Claude Code User-Agent.
USER_AGENT = "claude-code/2.1.200"
TIMEOUT = 10

CREDENTIALS_PATH = Path.home() / ".claude/.credentials.json"
CACHE_PATH = Path(
    os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
) / "polybar/claude-quota.json"
# Slightly under the polybar interval so each tick fetches once.
CACHE_MAX_AGE = 290

CLOCK_ICON = "\uf017"
CALENDAR_ICON = "\uf073"


class TokenExpired(Exception):
    """The stored OAuth token is expired or was rejected."""


def color_for_percent(remaining_percent):
    """Return a color based on percentage remaining."""
    if remaining_percent > 50:
        return GREEN
    if remaining_percent >= 20:
        return YELLOW
    return RED


def format_time_remaining(resets_at, now=None):
    """Format an ISO 8601 reset time as a compact countdown."""
    if now is None:
        now = time.time()

    seconds = max(0, int(datetime.fromisoformat(resets_at).timestamp() - now))
    if seconds == 0:
        return "now"

    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    minutes %= 60
    hours %= 24

    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _scope_label(scope):
    """Name of the model a scoped limit applies to, or "" for global limits."""
    if isinstance(scope, str):
        return scope
    if isinstance(scope, dict):
        return scope.get("display_name") or scope.get("name") or ""
    return ""


def _windows(data):
    """Normalize the response into (group, percent, resets_at, label) tuples.

    Prefers the generalized limits[] array; falls back to the five_hour and
    seven_day fields when limits[] is absent.
    """
    limits = data.get("limits")
    if limits:
        return [
            (
                limit.get("group"),
                limit.get("percent"),
                limit.get("resets_at"),
                _scope_label(limit.get("scope")),
            )
            for limit in limits
        ]

    windows = []
    for key, group in (("five_hour", "session"), ("seven_day", "weekly")):
        window = data.get(key)
        if window:
            windows.append(
                (group, window.get("utilization"), window.get("resets_at"), "")
            )
    return windows


def format_usage(data, now=None):
    """Format usage windows for polybar."""
    parts = []
    for group, used_percent, resets_at, label in _windows(data):
        if used_percent is None:
            continue

        remaining_percent = max(0, min(100, round(100 - used_percent)))
        color = color_for_percent(remaining_percent)
        icon = CLOCK_ICON if group == "session" else CALENDAR_ICON
        prefix = f"{icon} {label} " if label else f"{icon} "
        part = f"{prefix}%{{F{color}}}{remaining_percent}%%{{F-}}"
        if resets_at:
            part += f" [{format_time_remaining(resets_at, now)}]"
        parts.append(part)

    return " · ".join(parts)


def read_token(path=CREDENTIALS_PATH, now=None):
    """Return the stored access token, or None when Claude Code is not logged in."""
    if now is None:
        now = time.time()

    try:
        oauth = json.loads(Path(path).read_text())["claudeAiOauth"]
    except (OSError, ValueError, KeyError):
        return None

    expires_at_ms = oauth.get("expiresAt")
    if expires_at_ms is not None and expires_at_ms / 1000 <= now:
        raise TokenExpired()
    return oauth.get("accessToken")


def load_cache(path=CACHE_PATH):
    """Return (fetched_at, data) from the cache, or None when absent."""
    try:
        cached = json.loads(Path(path).read_text())
        return cached["fetched_at"], cached["data"]
    except (OSError, ValueError, KeyError):
        return None


def save_cache(path, data, now):
    """Write the latest response to the cache."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"fetched_at": now, "data": data}))


def fetch_usage(token):
    """Fetch quota windows from the OAuth usage endpoint."""
    request = urllib.request.Request(
        USAGE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": BETA_HEADER,
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.load(response)


def get_usage(cache_path=CACHE_PATH, credentials_path=CREDENTIALS_PATH,
              now=None, fetch=fetch_usage):
    """Return (data, stale), fetching only when the cache is old."""
    if now is None:
        now = time.time()

    cached = load_cache(cache_path)
    if cached and now - cached[0] < CACHE_MAX_AGE:
        return cached[1], False

    token = read_token(credentials_path, now)
    if not token:
        raise TokenExpired()

    try:
        data = fetch(token)
    except urllib.error.HTTPError as error:
        if error.code == 401:
            raise TokenExpired() from error
        if cached:
            return cached[1], True
        raise
    except (urllib.error.URLError, OSError, ValueError):
        if cached:
            return cached[1], True
        raise

    save_cache(cache_path, data, now)
    return data, False


def render(data, stale, now=None):
    """Build the polybar label, marking stale values with *."""
    output = format_usage(data, now)
    if not output:
        return f"%{{F{RED}}}?%{{F-}}"
    return f"{output} *" if stale else output


def main():
    try:
        print(render(*get_usage()))
    except TokenExpired:
        print(f"%{{F{RED}}}Expired%{{F-}}")
    except Exception:
        print(f"%{{F{RED}}}?%{{F-}}")


if __name__ == "__main__":
    main()

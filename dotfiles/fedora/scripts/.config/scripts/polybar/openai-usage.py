#!/usr/bin/env python3
"""Display remaining OpenAI Codex subscription usage in polybar.

Uses the authenticated Codex CLI app-server so Codex owns OAuth token storage
and refresh. Usage windows are identified by duration because the API can put a
weekly window in the primary slot when no five-hour window is active.

Usage: openai-usage.py
"""

import json
import select
import subprocess
import time


GREEN = "#2aa198"
YELLOW = "#b58900"
RED = "#dc322f"
RPC_TIMEOUT = 15


def color_for_percent(remaining_percent):
    """Return a color based on percentage remaining."""
    if remaining_percent > 50:
        return GREEN
    if remaining_percent >= 20:
        return YELLOW
    return RED


def format_time_remaining(resets_at, now=None):
    """Format a Unix reset timestamp as a compact countdown."""
    if now is None:
        now = time.time()

    seconds = max(0, int(resets_at - now))
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


def _window_icon(window_duration_mins):
    """Select the five-hour or weekly window icon by duration."""
    if window_duration_mins <= 24 * 60:
        return "\uf017"  # clock
    return "\uf073"  # calendar


def format_usage(result, now=None):
    """Format Codex app-server rate limits for polybar."""
    rate_limits = result.get("rateLimits") or {}
    windows = [
        window
        for window in (rate_limits.get("primary"), rate_limits.get("secondary"))
        if window
    ]
    windows.sort(key=lambda window: window.get("windowDurationMins") or float("inf"))

    parts = []
    for window in windows:
        used_percent = window.get("usedPercent")
        duration = window.get("windowDurationMins")
        resets_at = window.get("resetsAt")
        if used_percent is None or duration is None or resets_at is None:
            continue

        remaining_percent = max(0, min(100, 100 - used_percent))
        color = color_for_percent(remaining_percent)
        icon = _window_icon(duration)
        reset_time = format_time_remaining(resets_at, now)
        parts.append(
            f"{icon} %{{F{color}}}{remaining_percent}%%{{F-}} [{reset_time}]"
        )

    return " · ".join(parts)


def fetch_usage(timeout=RPC_TIMEOUT):
    """Fetch rate limits from the authenticated Codex app-server."""
    process = subprocess.Popen(
        ["codex", "-s", "read-only", "-a", "untrusted", "app-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    try:
        requests = (
            {
                "method": "initialize",
                "id": 0,
                "params": {
                    "clientInfo": {
                        "name": "polybar_openai_usage",
                        "title": "Polybar OpenAI usage",
                        "version": "1.0.0",
                    }
                },
            },
            {"method": "initialized", "params": {}},
            {"method": "account/rateLimits/read", "id": 1, "params": {}},
        )
        for request in requests:
            process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            ready, _, _ = select.select([process.stdout], [], [], remaining)
            if not ready:
                break

            line = process.stdout.readline()
            if not line:
                break

            message = json.loads(line)
            if message.get("id") != 1:
                continue
            if "error" in message:
                raise RuntimeError(message["error"].get("message", "Codex RPC failed"))
            return message.get("result") or {}

        raise TimeoutError("Codex rate-limit request timed out")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main():
    try:
        output = format_usage(fetch_usage())
        print(output or f"%{{F{RED}}}?%{{F-}}")
    except Exception:
        print(f"%{{F{RED}}}?%{{F-}}")


if __name__ == "__main__":
    main()

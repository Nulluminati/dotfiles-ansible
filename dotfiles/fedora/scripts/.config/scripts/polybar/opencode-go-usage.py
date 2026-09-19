#!/usr/bin/env python3
# /// script
# dependencies = ["browser-cookie3", "requests"]
# ///
"""\
opencode-go-usage.py

Displays OpenCode Go subscription usage (5-hour / weekly / monthly windows).
Usage data comes from the console API:
  GET https://console.opencode.ai/api/go/status
authenticated with the console session token as a bearer token and the
workspace ID as the x-org-id header. The dashboard itself is now a
client-rendered SPA at https://opencode.ai/console, so usage can no longer
be scraped from server-rendered HTML.

Authentication mirrors the claude-credits monitor: the workspace ID is read
from a local config file, and the console session token is pulled from the
browser (Firefox, then Chrome) via browser_cookie3. The API answers 401 once
the session expires; signing in at https://opencode.ai/console refreshes it.

Credentials are resolved in this order (first non-empty wins):
  Workspace ID:    OPENCODE_GO_WORKSPACE_ID env
                   ~/.config/opencode/workspace_id
                   ~/.config/opencode-bar/opencode-go.json  (cross-tool compat)
  Session token:   OPENCODE_GO_AUTH_COOKIE env (raw console session token)
                   ~/.config/opencode-bar/opencode-go.json  (cross-tool compat)
                   browser cookies for opencode.ai (cookie "__Host-console_session")

Usage: uv run opencode-go-usage.py
"""

import glob
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

import requests

try:
    import browser_cookie3
except Exception:
    browser_cookie3 = None


# Configuration
WORKSPACE_ID_PATH = os.path.expanduser("~/.config/opencode/workspace_id")
OPENCODE_BAR_CONFIG_PATH = os.path.expanduser("~/.config/opencode-bar/opencode-go.json")
GO_STATUS_URL = "https://console.opencode.ai/api/go/status"
CONSOLE_SESSION_COOKIE = "__Host-console_session"
COOKIE_NAME = "auth"
# Domains whose session cookies must be sent together for the authenticated
# dashboard request. opencode.ai holds the Iron-sealed session cookie;
# auth.opencode.ai holds the OpenAuth tokens used during the OAuth handshake.
COOKIE_DOMAINS = ("opencode.ai", "auth.opencode.ai")
FIREFOX_PROFILE_GLOB = os.path.expanduser("~/.mozilla/firefox/*")

# Colors (solarized scheme, matching the other quota monitors)
GREEN = "#2aa198"
YELLOW = "#b58900"
RED = "#dc322f"


# --------------------------------------------------------------------------- #
# Credential resolution
# --------------------------------------------------------------------------- #
def _read_opencode_bar_config():
    """Read the opencode-bar JSON config if present (cross-tool compatibility)."""
    try:
        with open(OPENCODE_BAR_CONFIG_PATH) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (FileNotFoundError, ValueError, OSError):
        pass
    return None


def get_workspace_id():
    """Resolve the OpenCode workspace ID."""
    env = os.environ.get("OPENCODE_GO_WORKSPACE_ID", "").strip()
    if env:
        return env

    try:
        with open(WORKSPACE_ID_PATH) as f:
            value = f.read().strip()
        if value:
            return value
    except FileNotFoundError:
        pass

    config = _read_opencode_bar_config()
    if config:
        for key in ("workspaceId", "workspaceID", "workspace_id"):
            value = config.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None


def _read_firefox_cookies_live():
    """Read cookies from Firefox with WAL checkpointing.

    browser_cookie3 opens cookies.sqlite without the accompanying -wal journal,
    so while Firefox is running it reads stale cookie values. OpenCode's OpenAuth
    session cookie rotates frequently, and the stale value is rejected (the
    dashboard redirects to a login page). Copying cookies.sqlite together with
    cookies.sqlite-wal into a temp DB and running a WAL checkpoint gives the
    live values Firefox is actually using.

    Returns a requests RequestsCookieJar spanning every domain in COOKIE_DOMAINS.
    """
    jar = requests.cookies.RequestsCookieJar()
    domains = tuple(COOKIE_DOMAINS)

    for profile in glob.glob(FIREFOX_PROFILE_GLOB):
        src = os.path.join(profile, "cookies.sqlite")
        if not os.path.exists(src):
            continue

        tmp_dir = tempfile.mkdtemp(prefix="ocg-cookies-")
        tmp_db = os.path.join(tmp_dir, "cookies.sqlite")
        try:
            shutil.copy2(src, tmp_db)
            wal = src + "-wal"
            if os.path.exists(wal):
                shutil.copy2(wal, tmp_db + "-wal")

            con = sqlite3.connect(tmp_db)
            con.execute("PRAGMA wal_checkpoint(FULL)")
            cur = con.cursor()
            query = (
                "SELECT name, value, host, path, isSecure FROM moz_cookies WHERE "
                + " OR ".join(["host LIKE ?" for _ in domains])
            )
            cur.execute(query, [f"%{d}" for d in domains])
            for name, value, host, path, secure in cur.fetchall():
                if not value:
                    continue
                jar.set(name, value, domain=host, path=path, secure=bool(secure))
            con.close()
        except Exception:
            continue
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return jar


def get_cookie_jar():
    """Build a cookie jar for the authenticated dashboard request.

    Resolution order (first source yielding the auth cookie wins):
      1. OPENCODE_GO_AUTH_COOKIE env (single value, or a full "name=value; ..." string).
      2. ~/.config/opencode-bar/opencode-go.json (cross-tool compatibility).
      3. Firefox cookies read with WAL checkpointing (live values).
      4. browser_cookie3 fallback (Chrome/Chromium/Brave/Edge, then Firefox).
    """
    # 1. Explicit env var.
    env = os.environ.get("OPENCODE_GO_AUTH_COOKIE", "").strip()
    if env:
        jar = requests.cookies.RequestsCookieJar()
        if "=" in env:
            for part in env.split(";"):
                name, _, val = part.strip().partition("=")
                if name and val:
                    jar.set(name, val, domain=COOKIE_DOMAINS[0], path="/")
        else:
            jar.set(COOKIE_NAME, env, domain=COOKIE_DOMAINS[0], path="/")
        if len(jar):
            return jar

    # 2. opencode-bar JSON config.
    config = _read_opencode_bar_config()
    if config:
        for key in ("authCookie", "auth_cookie", "cookie"):
            value = config.get(key)
            if isinstance(value, str) and value.strip():
                jar = requests.cookies.RequestsCookieJar()
                jar.set(COOKIE_NAME, value.strip(), domain=COOKIE_DOMAINS[0], path="/")
                return jar

    # 3. Firefox (live, WAL-checkpointed).
    try:
        jar = _read_firefox_cookies_live()
        if any(c.name == COOKIE_NAME for c in jar):
            return jar
    except Exception:
        pass

    # 4. browser_cookie3 fallback for other browsers.
    if browser_cookie3 is not None:
        jar = requests.cookies.RequestsCookieJar()
        for domain in COOKIE_DOMAINS:
            for loader_name in ("chrome", "chromium", "brave", "edge", "firefox"):
                loader = getattr(browser_cookie3, loader_name, None)
                if loader is None:
                    continue
                try:
                    for cookie in loader(domain_name=domain):
                        if cookie.value:
                            jar.set(cookie.name, cookie.value,
                                    domain=cookie.domain, path=cookie.path)
                except Exception:
                    continue
        if any(c.name == COOKIE_NAME for c in jar):
            return jar

    return None


# --------------------------------------------------------------------------- #
# Console API (go/status)
#
# The console SPA fetches usage from console.opencode.ai with the console
# session token as a bearer token and the workspace ID as x-org-id. The
# payload carries per-meter spend in micro-cents:
#   access.meters.{fiveHour,week,month}.{limitMicroCents,usedMicroCents,resetsAt}
# --------------------------------------------------------------------------- #
def _console_session_token(jar):
    """Resolve the console API bearer token from a cookie jar.

    The console session cookie (__Host-console_session) doubles as the API
    bearer token. Env/config-provided values arrive as the "auth" cookie;
    accept those when they carry a console session token (st_ prefix).
    """
    for cookie in jar:
        if cookie.name == CONSOLE_SESSION_COOKIE and cookie.value:
            return cookie.value
    for cookie in jar:
        if cookie.name == COOKIE_NAME and (cookie.value or "").startswith("st_"):
            return cookie.value
    return None


def fetch_status(workspace_id, bearer_token, timeout=15):
    """Fetch the Go subscription status from the console API.

    Returns None when the session token was rejected (401), which means the
    user needs to sign in to https://opencode.ai/console again.
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer_token}",
        "x-org-id": workspace_id,
        "Referer": "https://opencode.ai/console/",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
    }
    response = requests.get(GO_STATUS_URL, headers=headers, timeout=timeout)
    if response.status_code == 401:
        return None
    response.raise_for_status()
    return response.json()


def _iso_to_reset_seconds(iso_ts, now):
    """Seconds from now until an ISO-8601 timestamp (None when absent)."""
    if not iso_ts:
        return None
    reset_at = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return max(0, int((reset_at - now).total_seconds()))


# Meter order and icons: clock -> 5-hour, calendar -> weekly,
# calendar-o -> monthly (matches the previous dashboard presentation).
METERS = (
    ("fiveHour", "\uf017"),
    ("week", "\uf073"),
    ("month", "\uf133"),
)


def parse_status(data, now=None):
    """Extract usage windows from the go/status payload."""
    if now is None:
        now = datetime.now(timezone.utc)

    access = data.get("access") or {}
    meters = access.get("meters") or {}
    # Only fiveHour/week carry resetsAt; the monthly meter has no date fields
    # in the API schema and resets at the end of the billing cycle instead.
    cycle_reset = access.get("endsAt")
    windows = []
    for meter_name, icon in METERS:
        meter = meters.get(meter_name)
        if not meter:
            continue
        limit = float(meter.get("limitMicroCents") or 0)
        used = float(meter.get("usedMicroCents") or 0)
        if limit <= 0:
            continue
        usage_percent = max(0.0, min(100.0, used / limit * 100))
        windows.append({
            "icon": icon,
            "usagePercent": usage_percent,
            "resetInSec": _iso_to_reset_seconds(
                meter.get("resetsAt") or cycle_reset, now
            ),
        })
    return windows


def format_status(data, now=None):
    """Format the go/status payload for polybar."""
    parts = [format_window(window, icon=window["icon"])
             for window in parse_status(data, now)]
    if data.get("useBalance"):
        parts.append("\uf155")  # dollar icon -> Zen balance fallback enabled
    return " \u00b7 ".join(parts)  # middle-dot separator, like zai/synthetic


# --------------------------------------------------------------------------- #
# Formatting (matches the synthetic / zai monitor styling)
# --------------------------------------------------------------------------- #
def format_time_remaining(seconds):
    """Format seconds remaining until window reset in compact form."""
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


def color_for_percent(remaining_percent):
    """Return color based on percentage remaining (matches zai/synthetic monitors)."""
    if remaining_percent > 50:
        return GREEN
    elif remaining_percent >= 20:
        return YELLOW
    return RED


def format_window(window, icon=""):
    """Format a single usage window: icon + colored percent + time to reset."""
    if not window:
        return ""

    usage_percent = window["usagePercent"]
    remaining_percent = max(0, 100 - usage_percent)
    prefix = f"{icon} " if icon else ""

    color = color_for_percent(remaining_percent)
    percent = f"%{{F{color}}}{int(remaining_percent)}%%{{F-}}"
    reset_in_sec = window.get("resetInSec")
    if reset_in_sec is None:
        # Meters without a reset timestamp (monthly) show percent only.
        return f"{prefix}{percent}"
    return f"{prefix}{percent} [{format_time_remaining(reset_in_sec)}]"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    workspace_id = get_workspace_id()
    if not workspace_id:
        # Mirrors claude-credits.py: prompt the user to run the setup action.
        print("Setup")
        sys.exit(0)

    cookie_jar = get_cookie_jar()
    bearer_token = _console_session_token(cookie_jar) if cookie_jar else None
    if not bearer_token:
        print("Login")
        sys.exit(0)

    # Fetch usage from the console API.
    try:
        data = fetch_status(workspace_id, bearer_token)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            print(f"%{{F{RED}}}Expired%{{F-}}")
        else:
            print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(0)
    except Exception:
        print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(0)

    # A None result means the console session token was rejected.
    if data is None:
        print(f"%{{F{RED}}}Expired%{{F-}}")
        sys.exit(0)

    try:
        output = format_status(data)
    except (KeyError, TypeError, ValueError):
        output = ""
    print(output or f"%{{F{RED}}}?%{{F-}}")


if __name__ == "__main__":
    main()

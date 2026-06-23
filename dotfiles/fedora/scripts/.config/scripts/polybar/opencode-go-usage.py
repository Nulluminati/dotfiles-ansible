#!/usr/bin/env python3
# /// script
# dependencies = ["browser-cookie3", "requests"]
# ///
"""\
opencode-go-usage.py

Displays OpenCode Go subscription usage (5-hour / weekly / monthly windows).
Usage windows are not exposed through a public API; they are embedded in the
authenticated dashboard at https://opencode.ai/workspace/<workspaceId>/go.

Authentication mirrors the claude-credits monitor: the workspace ID is read
from a local config file, and the session cookie is pulled from the browser
(Firefox, then Chrome) via browser_cookie3.

Credentials are resolved in this order (first non-empty wins):
  Workspace ID: OPENCODE_GO_WORKSPACE_ID env
                ~/.config/opencode/workspace_id
                ~/.config/opencode-bar/opencode-go.json  (cross-tool compat)
  Auth cookie:  OPENCODE_GO_AUTH_COOKIE env
                ~/.config/opencode-bar/opencode-go.json  (cross-tool compat)
                browser cookies for opencode.ai (cookie name "auth")

Usage: uv run opencode-go-usage.py
"""

import glob
import json
import os
import re
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
DASHBOARD_URL_TMPL = "https://opencode.ai/workspace/{workspace_id}/go"
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
# Dashboard HTML parsing
#
# Ports the parser from opgginc/opencode-bar's OpenCodeGoProvider. The dashboard
# is a Next.js/Solid app that embeds JSON-like blobs in <script> tags. Usage
# windows appear either as escaped JSON strings ("rollingUsage":{"usagePercent":...})
# or as Solid resource refs ($R[31]={...rollingUsage:$R[31]={status:"ok",...}}).
# --------------------------------------------------------------------------- #
def normalize_html(html):
    """Decode HTML entities and escaped quotes so the regexes can match both forms."""
    for encoded, decoded in (
        ("&quot;", '"'),
        ("&#34;", '"'),
        ("&#x27;", "'"),
        ("&#39;", "'"),
        ("&amp;", "&"),
        ('\\"', '"'),
        ("\\u0022", '"'),
    ):
        html = html.replace(encoded, decoded)
    return html


def _capture_object_body(text, field_name):
    """Capture the flat object body following `field_name:` (handles $R[n]= prefix)."""
    pattern = (
        r'''["']?''' + re.escape(field_name) + r'''["']?\s*:\s*(?:\$R\[\d+\]\s*=\s*)?\{([^{}]*)\}'''
    )
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1) if match else None


def _capture_number(body, field_name):
    """Capture a numeric value (quoted or unquoted) from a parsed object body."""
    pattern = r'''["']?''' + re.escape(field_name) + r'''["']?\s*:\s*"?(-?\d+(?:\.\d+)?)"?'''
    match = re.search(pattern, body)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _capture_status(body):
    """Capture the status string if present (e.g. "ok", "rate-limited")."""
    match = re.search(r'''["']?status["']?\s*:\s*"([^"]*)"''', body)
    return match.group(1) if match else None


def parse_window(text, field_name):
    """Parse a single usage window object from the normalized dashboard text."""
    body = _capture_object_body(text, field_name)
    if body is None:
        return None

    usage_percent = _capture_number(body, "usagePercent")
    reset_in_sec = _capture_number(body, "resetInSec")
    if usage_percent is None or reset_in_sec is None:
        return None

    return {
        "usagePercent": usage_percent,
        "resetInSec": max(0, int(reset_in_sec)),
        "status": _capture_status(body),
    }


def parse_use_balance(text):
    """Detect whether the workspace has "use Zen balance" enabled."""
    return bool(re.search(r'''["']?useBalance["']?\s*:\s*(?:true|!0)''', text))


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
    status = window.get("status") or "ok"
    remaining_percent = max(0, 100 - usage_percent)
    prefix = f"{icon} " if icon else ""

    # When rate-limited there is no meaningful reset time; flag it red.
    if status != "ok":
        return f"{prefix}%{{F{RED}}}{int(remaining_percent)}%%{{F-}} [lim]"

    color = color_for_percent(remaining_percent)
    time_str = format_time_remaining(window["resetInSec"])
    return f"{prefix}%{{F{color}}}{int(remaining_percent)}%%{{F-}} [{time_str}]"


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
    if cookie_jar is None:
        print("Login")
        sys.exit(0)

    # Fetch the authenticated dashboard HTML.
    try:
        headers = {
            "Accept": "text/html,application/xhtml+xml",
            "Referer": "https://opencode.ai/",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            ),
        }
        session = requests.Session()
        session.cookies = cookie_jar
        response = session.get(
            DASHBOARD_URL_TMPL.format(workspace_id=workspace_id),
            headers=headers,
            timeout=15,
        )
        # A redirect onto the auth host means the session cookie was rejected
        # (expired, rotated, or stale). Surface that specifically rather than a
        # generic parse failure.
        if response.url.startswith("https://auth.opencode.ai/"):
            print(f"%{{F{RED}}}Expired%{{F-}}")
            sys.exit(0)
        response.raise_for_status()
        html = response.text
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            print(f"%{{F{RED}}}Expired%{{F-}}")
        else:
            print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(0)
    except Exception:
        print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(0)

    # Parse usage windows from the embedded dashboard JSON.
    try:
        text = normalize_html(html)

        parts = []
        for field_name, icon in (
            ("rollingUsage", "\uf017"),   # clock  -> 5-hour window
            ("weeklyUsage", "\uf073"),    # calendar -> weekly window
            ("monthlyUsage", "\uf133"),   # calendar-o -> monthly window
        ):
            window = parse_window(text, field_name)
            if window:
                parts.append(format_window(window, icon=icon))

        if parse_use_balance(text):
            parts.append("\uf155")  # dollar icon -> Zen balance fallback enabled

        if not parts:
            print(f"%{{F{RED}}}?%{{F-}}")
            sys.exit(0)

        print(" \u00b7 ".join(parts))  # middle-dot separator, like zai/synthetic

    except (KeyError, TypeError, ValueError):
        print(f"%{{F{RED}}}?%{{F-}}")
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Tests for opencode-go-usage.py (stdlib + requests)."""
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

SCRIPT = Path(__file__).with_name("opencode-go-usage.py")

spec = importlib.util.spec_from_file_location("opencode_go_usage", SCRIPT)
opencode_go_usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opencode_go_usage)

GREEN = "#2aa198"
YELLOW = "#b58900"
RED = "#dc322f"

# Captured from GET https://console.opencode.ai/api/go/status.
SAMPLE_STATUS = {
    "subscriberUserId": "acc_01KTZBQXN2NY6PYVC046DF83P7",
    "paymentMethodId": "payment_method_01M2WN3ZRS9TEDG09J151P6AV3",
    "renewalCurrency": "usd",
    "useBalance": False,
    "cancelAtPeriodEnd": False,
    "renewalPending": False,
    "access": {
        "startsAt": "2026-09-13T02:08:39.000Z",
        "endsAt": "2026-10-13T02:08:39.000Z",
        "cancelAtPeriodEnd": False,
        "meters": {
            "fiveHour": {
                "startsAt": "2026-09-19T16:06:41.938Z",
                "resetsAt": "2026-09-19T21:06:41.938Z",
                "limitMicroCents": "1200000000",
                "usedMicroCents": "243046381",
            },
            "week": {
                "startsAt": "2026-09-14T00:00:00.000Z",
                "resetsAt": "2026-09-21T00:00:00.000Z",
                "limitMicroCents": "3000000000",
                "usedMicroCents": "662654386",
            },
            "month": {
                "limitMicroCents": "6000000000",
                "usedMicroCents": "666459768",
            },
        },
    },
}

NOW = datetime(2026, 9, 19, 16, 6, 41, 938000, tzinfo=timezone.utc)


def test_parse_status_extracts_all_meters():
    windows = opencode_go_usage.parse_status(SAMPLE_STATUS, NOW)
    assert [w["icon"] for w in windows] == ["\uf017", "\uf073", "\uf133"]
    # usagePercent stores used share; format_window renders remaining.
    assert [int(w["usagePercent"]) for w in windows] == [20, 22, 11]
    assert windows[0]["resetInSec"] == 5 * 3600  # fiveHour: 16:06 -> 21:06
    assert windows[1]["resetInSec"] == 31 * 3600 + 53 * 60 + 18  # week: -> Sun 00:00
    assert windows[2]["resetInSec"] is None  # month carries no resetsAt


def test_parse_status_without_access_is_empty():
    assert opencode_go_usage.parse_status({}, NOW) == []
    assert opencode_go_usage.parse_status({"access": None}, NOW) == []


def test_format_status_renders_windows_and_balance_icon():
    assert opencode_go_usage.format_status(SAMPLE_STATUS, NOW) == (
        f"\uf017 %{{F{GREEN}}}79%%{{F-}} [5h 0m]"
        f" · \uf073 %{{F{GREEN}}}77%%{{F-}} [1d 7h]"
        f" · \uf133 %{{F{GREEN}}}88%%{{F-}}"
    )


def test_format_status_appends_balance_icon_when_enabled():
    data = {**SAMPLE_STATUS, "useBalance": True}
    assert opencode_go_usage.format_status(data, NOW).endswith(" · \uf155")


def test_format_status_skips_bracket_without_reset():
    data = {"access": {"meters": {"month": {
        "limitMicroCents": "6000000000", "usedMicroCents": "5400000000"}}}}
    assert opencode_go_usage.format_status(data, NOW) == f"\uf133 %{{F{RED}}}10%%{{F-}}"


def test_console_session_token_prefers_console_cookie():
    jar = requests.cookies.RequestsCookieJar()
    jar.set("__Host-console_session", "st_abc123", domain="opencode.ai", path="/")
    jar.set("auth", "Fe26.2**stale", domain="opencode.ai", path="/")
    assert opencode_go_usage._console_session_token(jar) == "st_abc123"


def test_console_session_token_accepts_st_token_in_auth_cookie():
    jar = requests.cookies.RequestsCookieJar()
    jar.set("auth", "st_def456", domain="opencode.ai", path="/")
    assert opencode_go_usage._console_session_token(jar) == "st_def456"


def test_console_session_token_rejects_iron_cookie():
    jar = requests.cookies.RequestsCookieJar()
    jar.set("auth", "Fe26.2**66137fde", domain="opencode.ai", path="/")
    assert opencode_go_usage._console_session_token(jar) is None

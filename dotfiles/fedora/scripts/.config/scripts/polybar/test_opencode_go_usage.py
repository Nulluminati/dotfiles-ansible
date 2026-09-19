#!/usr/bin/env python3
"""Tests for opencode-go-usage.py (stdlib + requests)."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("opencode-go-usage.py")

spec = importlib.util.spec_from_file_location("opencode_go_usage", SCRIPT)
opencode_go_usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opencode_go_usage)


def test_login_redirect_detects_console_login():
    # Sessions rejected by the dashboard land on the console login page.
    assert opencode_go_usage._is_login_redirect("https://opencode.ai/console/login")


def test_login_redirect_detects_auth_authorize():
    assert opencode_go_usage._is_login_redirect("https://opencode.ai/auth/authorize")


def test_login_redirect_detects_legacy_auth_host():
    assert opencode_go_usage._is_login_redirect("https://auth.opencode.ai/authorize")


def test_login_redirect_accepts_dashboard():
    assert not opencode_go_usage._is_login_redirect(
        "https://opencode.ai/workspace/wrk_01ABCDEF/go"
    )

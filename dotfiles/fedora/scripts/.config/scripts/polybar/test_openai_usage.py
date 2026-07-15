#!/usr/bin/env python3
"""Tests for openai-usage.py (stdlib only)."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("openai-usage.py")

spec = importlib.util.spec_from_file_location("openai_usage", SCRIPT)
openai_usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(openai_usage)

GREEN = "#2aa198"
YELLOW = "#b58900"
RED = "#dc322f"


def test_color_for_percent():
    assert openai_usage.color_for_percent(51) == GREEN
    assert openai_usage.color_for_percent(20) == YELLOW
    assert openai_usage.color_for_percent(19) == RED


def test_format_time_remaining():
    now = 1_700_000_000
    assert openai_usage.format_time_remaining(now + 2 * 86400 + 3 * 3600, now) == "2d 3h"
    assert openai_usage.format_time_remaining(now + 2 * 3600 + 14 * 60, now) == "2h 14m"
    assert openai_usage.format_time_remaining(now - 1, now) == "now"


def test_format_usage_classifies_windows_by_duration():
    now = 1_700_000_000
    result = {
        "rateLimits": {
            # The API can put a weekly window in the primary slot.
            "primary": {
                "usedPercent": 2,
                "windowDurationMins": 10080,
                "resetsAt": now + 6 * 86400 + 4 * 3600,
            },
            "secondary": {
                "usedPercent": 25,
                "windowDurationMins": 300,
                "resetsAt": now + 2 * 3600 + 30 * 60,
            },
        }
    }

    assert openai_usage.format_usage(result, now) == (
        f"\uf017 %{{F{GREEN}}}75%%{{F-}} [2h 30m]"
        f" · \uf073 %{{F{GREEN}}}98%%{{F-}} [6d 4h]"
    )


def test_format_usage_omits_missing_window():
    now = 1_700_000_000
    result = {
        "rateLimits": {
            "primary": {
                "usedPercent": 82,
                "windowDurationMins": 10080,
                "resetsAt": now + 86400,
            },
            "secondary": None,
        }
    }

    assert openai_usage.format_usage(result, now) == (
        f"\uf073 %{{F{RED}}}18%%{{F-}} [1d 0h]"
    )


def test_format_usage_returns_empty_without_windows():
    assert openai_usage.format_usage({"rateLimits": {}}, 1_700_000_000) == ""

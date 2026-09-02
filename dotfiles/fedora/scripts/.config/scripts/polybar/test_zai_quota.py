#!/usr/bin/env python3
"""Tests for zai-quota.py (stdlib only, no external deps)."""
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPT = Path(__file__).with_name("zai-quota.py")

spec = importlib.util.spec_from_file_location("zai_quota", SCRIPT)
zq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zq)

GREEN = "#2aa198"
RED = "#dc322f"

QUOTA_PAYLOAD = {
    "code": 200,
    "msg": "Operation successful",
    "data": {
        "limits": [
            {
                "type": "TIME_LIMIT",
                "unit": 5,
                "number": 1,
                "usage": 100,
                "currentValue": 0,
                "remaining": 100,
                "percentage": 0,
                "nextResetTime": 1789365078999,
                "usageDetails": [],
            },
            {
                "type": "TOKENS_LIMIT",
                "unit": 3,
                "number": 5,
                "percentage": 1,
                "nextResetTime": 1788384041822,
            },
        ],
        "level": "lite",
    },
    "success": True,
}

RESET_PAYLOAD = {
    "code": 200,
    "msg": "Operation successful",
    "data": {
        "customerId": 74471760416802850,
        "targetType": "PERSONAL",
        "lastFiveHourResetTime": None,
        "lastWeekResetTime": None,
        "fiveHourResets": [{"recordId": 324277, "expireTime": "2026-10-01 23:59:59", "available": True}],
        "weekResets": [{"recordId": 166598, "expireTime": "2026-10-01 23:59:59", "available": True}],
    },
    "success": True,
}


def test_format_time_remaining():
    assert zq.format_time_remaining(4 * 60 + 30) == "4h 30m"
    assert zq.format_time_remaining(45) == "45m"
    assert zq.format_time_remaining(0) == "now"
    assert zq.format_time_remaining(None) == ""


def test_format_limit_shows_percentage_and_countdown():
    limit = {"percentage": 47, "nextResetTime": 1788384041822}
    result = zq.format_limit(limit, icon="", show_time=True)
    assert f"%{{F{GREEN}}}" in result
    assert "53%" in result
    assert "[" in result and "]" in result


def test_count_available_only_counts_available_cards():
    cards = [
        {"recordId": 1, "available": True},
        {"recordId": 2, "available": False},
        {"recordId": 3},
    ]
    assert zq.count_available(cards) == 1
    assert zq.count_available(None) == 0
    assert zq.count_available([]) == 0


def test_format_resets_both_pools_available():
    data = RESET_PAYLOAD["data"]
    assert zq.format_resets(data) == (
        f"\uf017 %{{F{GREEN}}}1%{{F-}} \uf073 %{{F{GREEN}}}1%{{F-}}"
    )


def test_format_resets_mixed_counts():
    data = {
        "fiveHourResets": [{"available": True}, {"available": True}],
        "weekResets": [{"available": False}],
    }
    assert zq.format_resets(data) == (
        f"\uf017 %{{F{GREEN}}}2%{{F-}} \uf073 0"
    )


def test_format_resets_none_returns_empty():
    assert zq.format_resets(None) == ""
    assert zq.format_resets({}) == ""


def test_format_output_appends_resets():
    result = zq.format_output(QUOTA_PAYLOAD, RESET_PAYLOAD["data"])
    assert result.endswith(f"\uf017 %{{F{GREEN}}}1%{{F-}} \uf073 %{{F{GREEN}}}1%{{F-}}")
    # Quota part comes first: tokens pct with countdown, then MCP window.
    assert result.startswith(f"%{{F{GREEN}}}99%%{{F-}} [")
    assert " \uf002 " in result


def test_format_output_without_reset_data_keeps_quota_only():
    result = zq.format_output(QUOTA_PAYLOAD, None)
    assert "\uf017" not in result and "\uf073" not in result
    assert " \uf002 " in result


def test_fetch_quota_uses_raw_key_header():
    fake = MagicMock()
    fake.json.return_value = QUOTA_PAYLOAD
    fake.raise_for_status = MagicMock()
    with patch("requests.get", return_value=fake) as mock_get:
        zq.fetch_quota("test-key")
    args, kwargs = mock_get.call_args
    assert kwargs["headers"]["Authorization"] == "test-key"
    assert kwargs["timeout"] == 10


def test_fetch_resets_hits_package_reset_list():
    fake = MagicMock()
    fake.json.return_value = RESET_PAYLOAD
    fake.raise_for_status = MagicMock()
    with patch("requests.get", return_value=fake) as mock_get:
        result = zq.fetch_resets("test-key")
    assert result == RESET_PAYLOAD
    args, kwargs = mock_get.call_args
    assert "customer-package-reset/list" in args[0] or "customer-package-reset/list" in kwargs.get("url", "")
    assert "targetType=PERSONAL" in args[0] or "targetType=PERSONAL" in kwargs.get("url", "")
    assert kwargs["headers"]["Authorization"] == "test-key"
    assert kwargs["timeout"] == 10


def test_main_no_api_key_prints_red_question():
    with patch.dict("os.environ", {}, clear=True):
        with patch("builtins.print") as mock_print:
            try:
                zq.main()
            except SystemExit:
                pass
            mock_print.assert_called_once_with(f"%{{F{RED}}}?%{{F-}}")


def test_main_prints_quota_and_resets():
    def fake_get(url, **kwargs):
        fake = MagicMock()
        fake.raise_for_status = MagicMock()
        if "quota/limit" in url:
            fake.json.return_value = QUOTA_PAYLOAD
        else:
            fake.json.return_value = RESET_PAYLOAD
        return fake

    with patch.dict("os.environ", {"ZAI_API_KEY": "test-key"}):
        with patch("requests.get", side_effect=fake_get):
            with patch("builtins.print") as mock_print:
                zq.main()
    printed = mock_print.call_args[0][0]
    assert "99%" in printed
    assert f"\uf017 %{{F{GREEN}}}1%{{F-}}" in printed
    assert f"\uf073 %{{F{GREEN}}}1%{{F-}}" in printed


def test_main_resets_failure_still_shows_quota():
    def fake_get(url, **kwargs):
        fake = MagicMock()
        fake.raise_for_status = MagicMock()
        if "quota/limit" in url:
            fake.json.return_value = QUOTA_PAYLOAD
        else:
            fake.raise_for_status.side_effect = Exception("404")
        return fake

    with patch.dict("os.environ", {"ZAI_API_KEY": "test-key"}):
        with patch("requests.get", side_effect=fake_get):
            with patch("builtins.print") as mock_print:
                zq.main()
    printed = mock_print.call_args[0][0]
    assert "99%" in printed
    assert "\uf017" not in printed


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))

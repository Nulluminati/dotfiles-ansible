#!/usr/bin/env python3
"""Tests for neuralwatt-credits.py (stdlib only, no external deps)."""
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPT = Path(__file__).with_name("neuralwatt-credits.py")

spec = importlib.util.spec_from_file_location("neuralwatt_credits", SCRIPT)
nw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nw)

RED = "#dc322f"
YELLOW = "#b58900"


def test_format_balance_normal():
    assert nw.format_balance(32.6774) == "$32.68"


def test_format_balance_critical_turns_red():
    # Below $1 is red
    assert nw.format_balance(0.99) == f"%{{F{RED}}}$0.99%{{F-}}"


def test_format_balance_zero_is_red():
    assert nw.format_balance(0) == f"%{{F{RED}}}$0.00%{{F-}}"


def test_format_balance_low_turns_yellow():
    # $1 up to $3 is yellow
    assert nw.format_balance(1) == f"%{{F{YELLOW}}}$1.00%{{F-}}"


def test_format_balance_two_fifty_is_yellow():
    assert nw.format_balance(2.50) == f"%{{F{YELLOW}}}$2.50%{{F-}}"


def test_format_balance_exactly_three_not_yellow():
    # 3 is the threshold; not below it, so default color
    assert nw.format_balance(3) == "$3.00"


def test_fetch_balance_extracts_credits_remaining():
    fake = MagicMock()
    fake.json.return_value = {
        "balance": {
            "credits_remaining_usd": 32.6774,
            "total_credits_usd": 52.34,
            "credits_used_usd": 19.6626,
        }
    }
    fake.raise_for_status = MagicMock()
    with patch("requests.get", return_value=fake) as mock_get:
        result = nw.fetch_balance("sk-test")
        assert result == 32.6774
        # Authorization bearer header sent
        args, kwargs = mock_get.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer sk-test"
        assert kwargs["timeout"] == 10


def test_fetch_balance_missing_balance_defaults_to_zero():
    fake = MagicMock()
    fake.json.return_value = {"usage": {}}
    fake.raise_for_status = MagicMock()
    with patch("requests.get", return_value=fake):
        assert nw.fetch_balance("sk-test") == 0


def test_main_no_api_key_prints_red_question():
    with patch.dict("os.environ", {}, clear=True):
        with patch("builtins.print") as mock_print:
            try:
                nw.main()
            except SystemExit:
                pass
            mock_print.assert_called_once_with(f"%{{F{RED}}}?%{{F-}}")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))

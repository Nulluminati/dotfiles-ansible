"""Tests for the OpenCode Go polybar monitor.

Run with: uv run --with requests --with browser-cookie3 python -m unittest discover -s tests
"""

import contextlib
import importlib.util
import io
import os
import pathlib
import unittest
from datetime import datetime, timezone

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "dotfiles/fedora/scripts/.config/scripts/polybar/opencode-go-usage.py"
)

spec = importlib.util.spec_from_file_location("opencode_go_usage", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

NOW = datetime(2026, 10, 19, 12, 0, 0, tzinfo=timezone.utc)

API_PAYLOAD = {
    "usage": {
        "rolling": {"status": "ok", "percent": 0, "resetsAt": "2026-10-19T13:00:00.000Z"},
        "weekly": {"status": "ok", "percent": 8, "resetsAt": "2026-10-26T00:00:00.000Z"},
        "monthly": {"status": "ok", "percent": 21, "resetsAt": "2026-11-13T02:08:39.000Z"},
    }
}


class GetApiKeyTest(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.pop(k, None) for k in ("OPENCODE_API_KEY", "OPENCODE_GO_API_KEY")}

    def tearDown(self):
        for key, value in self._saved.items():
            os.environ.pop(key, None)
            if value is not None:
                os.environ[key] = value

    def test_returns_none_without_key(self):
        self.assertIsNone(module.get_api_key())

    def test_reads_opencode_api_key(self):
        os.environ["OPENCODE_API_KEY"] = "oc_sk_test"
        self.assertEqual(module.get_api_key(), "oc_sk_test")

    def test_prefers_opencode_api_key(self):
        os.environ["OPENCODE_API_KEY"] = "oc_sk_primary"
        os.environ["OPENCODE_GO_API_KEY"] = "oc_sk_secondary"
        self.assertEqual(module.get_api_key(), "oc_sk_primary")


class ParseApiUsageTest(unittest.TestCase):
    def test_maps_three_windows_in_order(self):
        windows = module.parse_api_usage(API_PAYLOAD, NOW)
        self.assertEqual(len(windows), 3)
        self.assertEqual([w["usagePercent"] for w in windows], [0.0, 8.0, 21.0])
        self.assertEqual([w["resetInSec"] for w in windows], [3600, 561600, 2124519])

    def test_skips_missing_meters(self):
        payload = {"usage": {"weekly": {"percent": 50, "resetsAt": "2026-10-26T00:00:00Z"}}}
        windows = module.parse_api_usage(payload, NOW)
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0]["usagePercent"], 50.0)

    def test_clamps_percent(self):
        payload = {"usage": {"rolling": {"percent": 150, "resetsAt": "2026-10-19T13:00:00Z"}}}
        self.assertEqual(module.parse_api_usage(payload, NOW)[0]["usagePercent"], 100.0)

    def test_empty_payload(self):
        self.assertEqual(module.parse_api_usage({"usage": {}}, NOW), [])


class FormatApiStatusTest(unittest.TestCase):
    def test_formats_percent_remaining_and_reset(self):
        output = module.format_api_status(API_PAYLOAD, NOW)
        self.assertEqual(output.count("\u00b7"), 2)
        self.assertIn("%{F#2aa198}100%%{F-}", output)
        self.assertIn("%{F#2aa198}92%%{F-}", output)
        self.assertIn("%{F#2aa198}79%%{F-}", output)
        self.assertIn("[1h 0m]", output)
        self.assertIn("[6d 12h]", output)
        self.assertIn("[24d 14h]", output)

    def test_low_remaining_uses_warning_colors(self):
        payload = {
            "usage": {
                "rolling": {"percent": 60, "resetsAt": "2026-10-19T13:00:00Z"},
                "weekly": {"percent": 90, "resetsAt": "2026-10-26T00:00:00Z"},
            }
        }
        output = module.format_api_status(payload, NOW)
        self.assertIn("%{F#b58900}40%%{F-}", output)
        self.assertIn("%{F#dc322f}10%%{F-}", output)

    def test_empty_payload_returns_empty_string(self):
        self.assertEqual(module.format_api_status({"usage": {}}, NOW), "")


class FetchApiUsageTest(unittest.TestCase):
    def setUp(self):
        self._saved_get = module.requests.get

    def tearDown(self):
        module.requests.get = self._saved_get

    def _stub(self, status_code, payload):
        captured = {}

        class Response:
            def __init__(self):
                self.status_code = status_code
                self._payload = payload

            def json(self):
                return self._payload

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise module.requests.HTTPError(response=self)

        def fake_get(url, headers=None, timeout=None):
            captured["url"] = url
            captured["headers"] = headers
            return Response()

        module.requests.get = fake_get
        return captured

    def test_uses_zen_usage_endpoint_with_bearer_token(self):
        captured = self._stub(200, API_PAYLOAD)
        self.assertEqual(module.fetch_api_usage("oc_sk_test"), API_PAYLOAD)
        self.assertEqual(captured["url"], "https://opencode.ai/zen/go/v1/usage")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer oc_sk_test")

    def test_returns_none_on_401(self):
        self._stub(401, {"type": "error"})
        self.assertIsNone(module.fetch_api_usage("oc_sk_bad"))


class MainTest(unittest.TestCase):
    """main() must use the API key and never touch browser cookies when a key is set."""

    def setUp(self):
        self._saved = {name: getattr(module, name) for name in ("get_api_key", "fetch_api_usage", "get_cookie_jar")}
        self._stdout = io.StringIO()

    def tearDown(self):
        for name, value in self._saved.items():
            setattr(module, name, value)

    def _run_main(self):
        with contextlib.redirect_stdout(self._stdout):
            try:
                module.main()
            except SystemExit:
                pass
        return self._stdout.getvalue().strip()

    def test_prints_usage_without_reading_cookies(self):
        module.get_api_key = lambda: "oc_sk_test"
        module.fetch_api_usage = lambda key, timeout=15: API_PAYLOAD

        def explode():
            raise AssertionError("browser cookies must not be read when a key is set")

        module.get_cookie_jar = explode
        output = self._run_main()
        self.assertIn("%{F#2aa198}92%%{F-}", output)

    def test_reports_expired_when_key_is_rejected(self):
        module.get_api_key = lambda: "oc_sk_bad"
        module.fetch_api_usage = lambda key, timeout=15: None
        module.get_cookie_jar = lambda: (_ for _ in ()).throw(AssertionError("no cookies"))
        self.assertEqual(self._run_main(), "%{F#dc322f}Expired%{F-}")


if __name__ == "__main__":
    unittest.main()

"""Tests for setup.api.client — BoomiClient HTTP client."""
from __future__ import annotations

import base64
import time
from unittest.mock import MagicMock, patch

import pytest

from setup.api.client import BoomiApiError, BoomiClient, _MIN_CALL_INTERVAL


def _mock_response(
    status_code: int = 200,
    json_data: dict | None = None,
    text: str = "",
    content_type: str = "application/json",
) -> MagicMock:
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text or (str(json_data) if json_data else "")
    resp.headers = {"Content-Type": content_type}
    if json_data is not None:
        resp.json.return_value = json_data
        resp.text = str(json_data)
    return resp


class TestAuthentication:
    def test_basic_auth_header_format(self) -> None:
        """Verify Authorization header is correct Base64 of 'BOOMI_TOKEN.{email}:{token}'."""
        client = BoomiClient(user="admin@example.com", token="my-secret-token")
        expected_raw = "BOOMI_TOKEN.admin@example.com:my-secret-token"
        expected_encoded = base64.b64encode(expected_raw.encode()).decode()
        expected_header = f"Basic {expected_encoded}"

        assert client._session.headers["Authorization"] == expected_header


class TestRateLimiting:
    @patch("setup.api.client.time.sleep")
    @patch("setup.api.client.time.monotonic")
    def test_rate_limiting_delay(
        self, mock_monotonic: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Two rapid calls should trigger sleep to enforce >= 120ms gap."""
        client = BoomiClient(user="u", token="t")

        # First call: monotonic returns 100.0, no prior call (last_call_time=0)
        # so elapsed = 100.0 > _MIN_CALL_INTERVAL, no sleep
        # After rate_limit, monotonic() is called again to set _last_call_time
        mock_monotonic.side_effect = [100.0, 100.0, 100.05, 100.12]
        #                             ^1st _rate_limit now, ^set last, ^2nd now, ^set last

        mock_response = _mock_response(200, {"ok": True})
        client._session.request = MagicMock(return_value=mock_response)

        client.get("https://api.boomi.com/test1")
        client.get("https://api.boomi.com/test2")

        # Second call: elapsed = 100.05 - 100.0 = 0.05 < 0.120
        # Should sleep for 0.120 - 0.05 = 0.07
        mock_sleep.assert_called()
        sleep_call_args = [call.args[0] for call in mock_sleep.call_args_list]
        assert any(0 < arg <= _MIN_CALL_INTERVAL for arg in sleep_call_args)


class TestRetryBehavior:
    @patch("setup.api.client.time.sleep")
    @patch("setup.api.client.time.monotonic", return_value=0.0)
    def test_retry_on_429(
        self, mock_monotonic: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """First call returns 429, second succeeds."""
        client = BoomiClient(user="u", token="t")
        resp_429 = _mock_response(429, text="Rate limited")
        resp_200 = _mock_response(200, {"result": "ok"})

        client._session.request = MagicMock(side_effect=[resp_429, resp_200])

        result = client.get("https://api.boomi.com/test")
        assert result == {"result": "ok"}
        assert client._session.request.call_count == 2

    @patch("setup.api.client.time.sleep")
    @patch("setup.api.client.time.monotonic", return_value=0.0)
    def test_retry_on_503(
        self, mock_monotonic: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """First call returns 503, second succeeds."""
        client = BoomiClient(user="u", token="t")
        resp_503 = _mock_response(503, text="Service unavailable")
        resp_200 = _mock_response(200, {"healthy": True})

        client._session.request = MagicMock(side_effect=[resp_503, resp_200])

        result = client.get("https://api.boomi.com/health")
        assert result == {"healthy": True}
        assert client._session.request.call_count == 2

    @patch("setup.api.client.time.sleep")
    @patch("setup.api.client.time.monotonic", return_value=0.0)
    def test_no_retry_on_401(
        self, mock_monotonic: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """401 raises immediately without retry."""
        client = BoomiClient(user="u", token="t")
        resp_401 = _mock_response(401, text="Unauthorized")

        client._session.request = MagicMock(return_value=resp_401)

        with pytest.raises(BoomiApiError) as exc_info:
            client.get("https://api.boomi.com/test")

        assert exc_info.value.status_code == 401
        assert client._session.request.call_count == 1

    @patch("setup.api.client.time.sleep")
    @patch("setup.api.client.time.monotonic", return_value=0.0)
    def test_max_retries_exceeded(
        self, mock_monotonic: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """3 consecutive 429s (+ 1 initial = 4 attempts), then raises BoomiApiError."""
        client = BoomiClient(user="u", token="t")
        resp_429 = _mock_response(429, text="Rate limited")

        # _MAX_RETRIES = 3, so total attempts = 3 + 1 = 4
        client._session.request = MagicMock(return_value=resp_429)

        with pytest.raises(BoomiApiError) as exc_info:
            client.get("https://api.boomi.com/test")

        assert exc_info.value.status_code == 429
        # 1 initial + 3 retries = 4 calls
        assert client._session.request.call_count == 4


class TestResponseParsing:
    @patch("setup.api.client.time.sleep")
    @patch("setup.api.client.time.monotonic", return_value=0.0)
    def test_json_response_parsing(
        self, mock_monotonic: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Verify JSON responses are parsed to dict."""
        client = BoomiClient(user="u", token="t")
        resp = _mock_response(200, json_data={"name": "test", "version": 1})

        client._session.request = MagicMock(return_value=resp)

        result = client.get("https://api.boomi.com/component/123")
        assert isinstance(result, dict)
        assert result["name"] == "test"

    @patch("setup.api.client.time.sleep")
    @patch("setup.api.client.time.monotonic", return_value=0.0)
    def test_xml_response_handling(
        self, mock_monotonic: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Verify XML responses are returned as string."""
        client = BoomiClient(user="u", token="t")
        xml_text = "<Component><id>abc</id></Component>"
        resp = _mock_response(200, text=xml_text, content_type="application/xml")
        resp.json = MagicMock(side_effect=ValueError("Not JSON"))

        client._session.request = MagicMock(return_value=resp)

        result = client.get("https://api.boomi.com/component/123", accept_xml=True)
        assert isinstance(result, str)
        assert "<Component>" in result

    @patch("setup.api.client.time.sleep")
    @patch("setup.api.client.time.monotonic", return_value=0.0)
    def test_empty_204_response(
        self, mock_monotonic: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """204 No Content returns empty dict."""
        client = BoomiClient(user="u", token="t")
        resp = _mock_response(204, text="", content_type="application/json")

        client._session.request = MagicMock(return_value=resp)

        result = client.delete("https://api.boomi.com/branch/123")
        assert result == {}

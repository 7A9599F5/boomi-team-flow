"""Base HTTP client for Boomi Platform and DataHub APIs."""
from __future__ import annotations

import base64
import logging
import time
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

# Minimum gap between API calls (seconds) to respect rate limits
_MIN_CALL_INTERVAL = 0.120

# Retry configuration
_MAX_RETRIES = 3
_BACKOFF_SECONDS = [1, 2, 4]
_RETRYABLE_STATUS_CODES = {429, 503}


class BoomiApiError(Exception):
    """Raised when a Boomi API call fails."""

    def __init__(self, status_code: int, body: str, url: str = "") -> None:
        self.status_code = status_code
        self.body = body
        self.url = url
        super().__init__(
            f"Boomi API error {status_code} for {url}: {body[:500]}"
        )


class BoomiClient:
    """Low-level HTTP client with auth, rate limiting, and retry logic."""

    def __init__(self, user: str, token: str) -> None:
        auth_string = f"BOOMI_TOKEN.{user}:{token}"
        encoded = base64.b64encode(auth_string.encode()).decode()
        self._auth_header = f"Basic {encoded}"
        self._last_call_time: float = 0.0
        self._session = requests.Session()
        self._session.headers["Authorization"] = self._auth_header
        self._session.headers["Accept"] = "application/json"

    def _rate_limit(self) -> None:
        """Enforce minimum gap between API calls."""
        now = time.monotonic()
        elapsed = now - self._last_call_time
        if elapsed < _MIN_CALL_INTERVAL:
            time.sleep(_MIN_CALL_INTERVAL - elapsed)
        self._last_call_time = time.monotonic()

    def _request(
        self,
        method: str,
        url: str,
        data: Optional[str] = None,
        content_type: str = "application/json",
        accept_xml: bool = False,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute an HTTP request with rate limiting and retry."""
        headers: dict[str, str] = {}
        if data is not None:
            headers["Content-Type"] = content_type
        if accept_xml:
            headers["Accept"] = "application/xml"

        for attempt in range(_MAX_RETRIES + 1):
            self._rate_limit()
            logger.debug("%s %s (attempt %d)", method, url, attempt + 1)

            resp = self._session.request(
                method, url, data=data, headers=headers, **kwargs
            )

            if resp.status_code == 401:
                raise BoomiApiError(resp.status_code, resp.text, url)

            if resp.status_code in _RETRYABLE_STATUS_CODES and attempt < _MAX_RETRIES:
                wait = _BACKOFF_SECONDS[attempt]
                logger.warning(
                    "Retryable %d from %s, waiting %ds", resp.status_code, url, wait
                )
                time.sleep(wait)
                continue

            if resp.status_code >= 400:
                raise BoomiApiError(resp.status_code, resp.text, url)

            return resp

        # Should not reach here, but handle edge case
        raise BoomiApiError(resp.status_code, resp.text, url)  # type: ignore[possibly-undefined]

    def _parse_response(
        self, resp: requests.Response, accept_xml: bool = False
    ) -> dict | str:
        """Parse response as JSON dict or XML string."""
        content_type = resp.headers.get("Content-Type", "")
        if resp.status_code == 204 or not resp.text:
            return {}
        if "xml" in content_type or accept_xml:
            return resp.text
        return resp.json()

    def get(self, url: str, accept_xml: bool = False, **kwargs: Any) -> dict | str:
        """HTTP GET, returns parsed JSON dict or XML string."""
        resp = self._request("GET", url, accept_xml=accept_xml, **kwargs)
        return self._parse_response(resp, accept_xml=accept_xml)

    def post(
        self,
        url: str,
        data: str,
        content_type: str = "application/json",
        accept_xml: bool = False,
        **kwargs: Any,
    ) -> dict | str:
        """HTTP POST, returns parsed JSON dict or XML string."""
        resp = self._request(
            "POST", url, data=data, content_type=content_type,
            accept_xml=accept_xml, **kwargs,
        )
        return self._parse_response(resp, accept_xml=accept_xml)

    def put(
        self,
        url: str,
        data: str,
        content_type: str = "application/json",
        accept_xml: bool = False,
        **kwargs: Any,
    ) -> dict | str:
        """HTTP PUT, returns parsed JSON dict or XML string."""
        resp = self._request(
            "PUT", url, data=data, content_type=content_type,
            accept_xml=accept_xml, **kwargs,
        )
        return self._parse_response(resp, accept_xml=accept_xml)

    def delete(self, url: str, accept_xml: bool = False, **kwargs: Any) -> dict | str:
        """HTTP DELETE, returns parsed response."""
        resp = self._request("DELETE", url, accept_xml=accept_xml, **kwargs)
        return self._parse_response(resp, accept_xml=accept_xml)

"""Boomi DataHub MDM API wrapper.

All Platform API endpoints are XML-only — JSON request/response bodies
are not supported.  See rest-api.md for full reference.

Two separate API surfaces:
  - Platform API  (api.boomi.com)   — model/repo lifecycle, credentials: BOOMI_TOKEN.user:token
  - Repository API (hub_cloud_url)  — record CRUD,          credentials: Basic generatedUser:hubAuthToken
    (generatedUser is from the repo's Authentication Token page, NOT the Boomi account ID)
"""
from __future__ import annotations

import base64
import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

from setup.api.client import BoomiClient, BoomiApiError
from setup.config import BoomiConfig

logger = logging.getLogger(__name__)

# Map JSON model-spec field types → Platform API type attribute values
# Valid types: BOOLEAN, CLOB, DATE, DATETIME, ENUMERATION, FLOAT, INTEGER,
#              REFERENCE, STRING, TIME
# Note: DATETIME (no underscore) is correct per Boomi docs. A prior "M1 fix"
# incorrectly changed this to DATE_TIME, which caused "Missing required
# properties" errors from the Create Model API.
_FIELD_TYPE_MAP = {
    "String": "STRING",
    "Number": "INTEGER",
    "Date": "DATETIME",
    "Boolean": "BOOLEAN",
}

_MDM_NS = "http://mdm.api.platform.boomi.com/"
_XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class DataHubApi:
    """Wrapper for Boomi DataHub MDM REST API v1 operations.

    Uses two distinct API surfaces:
    - Platform API (self._client, base=api.boomi.com) for model/repo lifecycle operations.
    - Repository API (self._repo_client, base=hub_cloud_url) for record CRUD operations.
      The Repository API uses Basic Auth with {generatedUser}:{hubAuthToken}.
    """

    def __init__(self, client: BoomiClient, config: BoomiConfig) -> None:
        self._client = client
        self._config = config
        self._base = (
            f"{config.cloud_base_url}/mdm/api/rest/v1/{config.boomi_account_id}"
        )
        # Lazily initialized Repository API client (different host + credentials)
        self._repo_client_instance: Optional[BoomiClient] = None

    # Auth format candidates for the Repository API (tried in order).
    # The correct username is the GENERATED USERNAME from the DataHub repo's
    # Authentication Token page — NOT the Boomi account ID.
    # https://help.boomi.com/docs/Atomsphere/Master%20Data%20Hub/REST%20APIs/r-mdm-Repository_API
    _AUTH_FORMATS = [
        # Format 1: generatedUser:hubAuthToken  (correct — generated username from repo)
        "generated_hub",
        # Format 2: accountId:hubAuthToken  (legacy fallback — some envs may accept)
        "account_hub",
        # Format 3: BOOMI_TOKEN.user:apiToken  (Platform API format — some envs may accept)
        "boomi_token",
        # Format 4: accountId:apiToken  (cross-format fallback)
        "account_api",
    ]

    # Response codes that confirm auth worked (even if the request itself had issues)
    _AUTH_OK_CODES = set(range(200, 400)) | {400, 403, 405, 409, 500, 502, 503}

    def _build_auth_header(self, fmt: str) -> str | None:
        """Build a Basic Auth header for the given format key.

        Returns None if required credentials are missing for that format.
        """
        cfg = self._config
        if fmt == "generated_hub" and cfg.hub_auth_user and cfg.hub_auth_token:
            raw = f"{cfg.hub_auth_user}:{cfg.hub_auth_token}"
        elif fmt == "account_hub" and cfg.boomi_account_id and cfg.hub_auth_token:
            raw = f"{cfg.boomi_account_id}:{cfg.hub_auth_token}"
        elif fmt == "boomi_token" and cfg.boomi_user and cfg.boomi_token:
            raw = f"BOOMI_TOKEN.{cfg.boomi_user}:{cfg.boomi_token}"
        elif fmt == "account_api" and cfg.boomi_account_id and cfg.boomi_token:
            raw = f"{cfg.boomi_account_id}:{cfg.boomi_token}"
        else:
            return None
        encoded = base64.b64encode(raw.encode()).decode()
        return f"Basic {encoded}"

    @staticmethod
    def _mask_header(header: str) -> str:
        """Mask a Basic Auth header for safe diagnostic display."""
        # "Basic <base64>" → show first 8 chars of base64
        if header.startswith("Basic ") and len(header) > 14:
            return f"Basic {header[6:14]}..."
        return "Basic ***"

    def _build_verbose_block(
        self,
        url: str,
        body: str,
        candidates: list[tuple[str, str]],
    ) -> str:
        """Build a verbose debug block with full request details for Postman/curl.

        Only called when config.verbose is True. Shows raw credentials so the
        user can copy-paste directly into Postman or a terminal.
        """
        lines = [
            "\n\n╔══ VERBOSE: Postman / curl debug ══════════════════════════",
            f"║ Method:  POST",
            f"║ URL:     {url}",
            f"║ Content-Type: application/xml",
            "║",
            "║ Request body:",
        ]
        for bline in body.strip().splitlines():
            lines.append(f"║   {bline}")
        lines.append("║")

        # Show each candidate's raw credentials and curl command
        for fmt, header in candidates:
            raw_cred = base64.b64decode(header.split(" ", 1)[1]).decode()
            lines.extend([
                f"║ ── {fmt} ──",
                f"║   Raw credentials: {raw_cred}",
                f"║   Authorization:   {header}",
                f"║   curl:",
                f"║     curl -X POST '{url}' \\",
                f"║       -H 'Authorization: {header}' \\",
                f"║       -H 'Content-Type: application/xml' \\",
                f"║       -d '{body.replace(chr(10), '')}'",
                "║",
            ])

        lines.append("╚══════════════════════════════════════════════════════════")
        return "\n".join(lines)

    def _make_repo_client(self, auth_header: str) -> BoomiClient:
        """Build a BoomiClient for Repository API with a pre-built auth header."""
        import requests as _requests  # noqa: PLC0415

        repo_client = BoomiClient.__new__(BoomiClient)
        repo_client._auth_header = auth_header
        repo_client._last_call_time = 0.0
        repo_client._session = _requests.Session()
        repo_client._session.headers["Authorization"] = auth_header
        repo_client._session.headers["Accept"] = "application/json"
        return repo_client

    @property
    def _repo_client(self) -> BoomiClient:
        """Lazy-initialized BoomiClient for Repository API record operations.

        Uses Basic base64({generatedUser}:{hubAuthToken}) where generatedUser
        is the generated username from the DataHub repo's Authentication Token
        page (NOT the Boomi account ID).  Falls back to accountId formats if
        the generated username is not configured.
        """
        if self._repo_client_instance is not None:
            return self._repo_client_instance

        hub_url = self._config.hub_cloud_url

        # Build candidate headers (primary format first)
        candidates: list[tuple[str, str]] = []
        for fmt in self._AUTH_FORMATS:
            header = self._build_auth_header(fmt)
            if header:
                candidates.append((fmt, header))

        if not candidates:
            raise BoomiApiError(
                401,
                "No DataHub credentials available. Ensure:\n"
                "  - datahub_user is set (generated username from repo Authentication Token page)\n"
                "  - hub_auth_token is set (run step 2.4 or set datahub_token in state)\n"
                "  - OR boomi_account_id + hub_auth_token as fallback\n"
                "  - OR boomi_user + boomi_token (env vars BOOMI_USER/BOOMI_TOKEN)",
                "",
            )

        # Can we do a live probe? Need both hub_url and a deployed universe.
        probe_url = self._build_probe_url(hub_url)
        if probe_url:
            import requests as _requests  # noqa: PLC0415

            # Log credential diagnostics (masked) for debugging
            cfg = self._config
            logger.info(
                "Auth probe diagnostics: account_id=%s (%d chars), "
                "hub_auth_token=%s (%d chars), hub_url=%s",
                cfg.boomi_account_id[:8] + "..." if cfg.boomi_account_id else "EMPTY",
                len(cfg.boomi_account_id),
                cfg.hub_auth_token[:4] + "..." if cfg.hub_auth_token else "EMPTY",
                len(cfg.hub_auth_token),
                hub_url,
            )

            probe_body = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<RecordQueryRequest limit="1"/>'
            )
            results: list[tuple[str, int, str]] = []

            for fmt, header in candidates:
                try:
                    hdrs = {
                        "Authorization": header,
                        "Content-Type": "application/xml",
                    }
                    resp = _requests.post(
                        probe_url, data=probe_body, headers=hdrs, timeout=15,
                    )
                    # Capture response body (truncated) for 401 diagnostics
                    body_preview = resp.text[:200].strip() if resp.text else ""
                    results.append((fmt, resp.status_code, body_preview))
                    logger.info(
                        "  Auth probe %s → HTTP %d (%s) body=%s",
                        fmt, resp.status_code, self._mask_header(header),
                        body_preview[:100],
                    )

                    # Accept any status that confirms auth worked
                    # (401 = wrong creds, 404 = ambiguous, anything else = auth OK)
                    if resp.status_code in self._AUTH_OK_CODES:
                        logger.info("Repository API auth: %s (HTTP %d)", fmt, resp.status_code)
                        self._repo_client_instance = self._make_repo_client(header)
                        return self._repo_client_instance
                except _requests.RequestException as exc:
                    results.append((fmt, -1, str(exc)))
                    logger.warning("  Auth probe %s → network error: %s", fmt, exc)
                    continue

            # No format produced a definitive auth-OK response
            detail_lines = [f"  {fmt}: HTTP {code}" for fmt, code, _ in results]
            detail = "\n".join(detail_lines)
            # Include the first non-empty response body for diagnostics
            resp_body = next(
                (body for _, code, body in results if code == 401 and body), ""
            )
            body_hint = f"\nServer response: {resp_body}" if resp_body else ""

            # Verbose mode: print full request details for Postman/curl testing
            verbose_block = ""
            if getattr(self._config, "verbose", False):
                verbose_block = self._build_verbose_block(
                    probe_url, probe_body, candidates,
                )

            raise BoomiApiError(
                401,
                f"No auth format succeeded against\n{probe_url}\n"
                f"Results:\n{detail}{body_hint}{verbose_block}\n\n"
                "Verify your DataHub token:\n"
                "  1. Services > DataHub > Repositories > PromotionHub > Configure\n"
                "  2. Copy the Authentication Token value\n"
                "  3. Re-run step 2.4 to enter the fresh token",
                hub_url,
            )

        # Cannot probe (no hub_url or no universe_ids deployed yet).
        # Use the first available format (generatedUser:hubAuthToken preferred).
        # Auth will be validated on the first real record operation.
        fmt, header = candidates[0]
        logger.info(
            "Repository API auth: using %s (no universe available for probe)", fmt,
        )
        self._repo_client_instance = self._make_repo_client(header)
        return self._repo_client_instance

    def _build_probe_url(self, hub_url: str) -> str | None:
        """Build a probe URL for auth testing, or None if probing isn't possible.

        Only returns a URL when we have both a hub_cloud_url AND a deployed
        universe.  The GET /mdm fallback was removed because it can return
        200/404 regardless of auth validity (false positive).
        """
        if not hub_url:
            return None
        universe_id = (
            next(iter(self._config.universe_ids.values()), None)
            if self._config.universe_ids
            else None
        )
        if not universe_id:
            return None
        return f"{hub_url}/mdm/universes/{universe_id}/records/query"

    def reset_repo_client(self) -> None:
        """Invalidate the cached Repository API client.

        Call after changing credentials on config so the next _repo_client
        access re-probes and rebuilds the client with fresh credentials.
        """
        self._repo_client_instance = None

    def verify_repo_auth(self) -> bool:
        """Test whether _repo_client can authenticate.

        Triggers the lazy init which probes auth if a universe is available.
        Returns True if auth appears valid or cannot be tested yet.
        Returns False only on definitive 401.

        If no universe was available for probing, the client is built with
        the primary format but then RESET so the next access can re-probe
        once universes are deployed.
        """
        could_probe = self._build_probe_url(self._config.hub_cloud_url) is not None
        try:
            _ = self._repo_client  # triggers probe if universe available
            if not could_probe:
                # Auth wasn't actually verified — reset so next access re-probes
                # (by then, universes from steps 1.2a-e may be available)
                self._repo_client_instance = None
            return True
        except BoomiApiError as exc:
            if exc.status_code == 401:
                logger.warning("Repository API auth verification failed: %s", exc.body)
                return False
            return True  # Non-auth errors mean auth itself succeeded

    def _record_base(self, model_name: str) -> str:
        """Base URL for Repository API record operations.

        C2a fix: Uses hub_cloud_url (not api.boomi.com) and universe_id (not repo_id/model_name).
        Pattern: https://{hub_cloud_url}/mdm/universes/{universeId}
        """
        hub_url = self._config.hub_cloud_url
        if not hub_url:
            raise BoomiApiError(
                400,
                "hub_cloud_url is not configured — call list_repositories() first to extract "
                "repositoryBaseUrl and store it in config.hub_cloud_url",
                "",
            )
        universe_id = self._config.universe_ids.get(model_name, "")
        if not universe_id:
            raise BoomiApiError(
                400,
                f"universe_id for model '{model_name}' is not configured — "
                "call create_model() and store the returned model ID in config.universe_ids",
                "",
            )
        return f"{hub_url}/mdm/universes/{universe_id}"

    # ------------------------------------------------------------------
    # Hub Cloud operations
    # ------------------------------------------------------------------

    def get_hub_clouds(self) -> list[dict[str, str]]:
        """GET /clouds — list available Hub Clouds.

        Returns list of dicts with keys: cloudId, containerId, name.
        """
        url = f"{self._base}/clouds"
        result = self._client.get(url, accept_xml=True)
        if isinstance(result, str):
            return self._parse_clouds_xml(result)
        return []

    @staticmethod
    def _parse_clouds_xml(xml_str: str) -> list[dict[str, str]]:
        """Parse <mdm:Clouds> XML response into list of cloud dicts.

        M13 fix: Use xml.etree.ElementTree instead of a regex that assumes
        fixed XML attribute ordering (XML attributes are unordered per spec).
        """
        clouds = []
        try:
            root = ET.fromstring(xml_str)
            # Try namespace-aware search first
            ns = {"mdm": "http://mdm.api.platform.boomi.com/"}
            cloud_elements = root.findall(".//mdm:Cloud", ns)
            if not cloud_elements:
                # Fall back to namespace-unaware search in case namespace differs
                cloud_elements = [
                    el for el in root.iter()
                    if el.tag.endswith("}Cloud") or el.tag == "Cloud"
                ]
            for cloud in cloud_elements:
                clouds.append({
                    "cloudId": cloud.get("cloudId", ""),
                    "containerId": cloud.get("containerId", ""),
                    "name": cloud.get("name", ""),
                })
        except ET.ParseError as exc:
            logger.warning("Failed to parse clouds XML: %s", exc)
        return clouds

    # ------------------------------------------------------------------
    # Repository operations
    # ------------------------------------------------------------------

    def create_repository(self, cloud_id: str, repo_name: str) -> str:
        """POST /clouds/{cloudId}/repositories/{repoName}/create.

        Sends an empty body.  Returns the repository ID string.
        """
        url = f"{self._base}/clouds/{cloud_id}/repositories/{repo_name}/create"
        # Empty body POST — pass None so no Content-Type is sent
        result = self._client.post(url, accept_xml=True)
        if isinstance(result, str):
            # Extract UUID via regex to handle BOM or other invisible chars
            # that .strip() doesn't remove — a BOM in the repo_id corrupts
            # the URL for subsequent GET /repositories/{repoId}/status calls.
            match = re.search(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                result,
                re.IGNORECASE,
            )
            if match:
                return match.group(0)
            return result.strip()
        if isinstance(result, dict):
            return result.get("id", str(result))
        return str(result)

    def get_repo_creation_status(self, repo_id: str) -> str:
        """GET /repositories/{repoId}/status — poll creation status.

        Returns status string: SUCCESS, PENDING, or DELETED.
        """
        url = f"{self._base}/repositories/{repo_id}/status"
        result = self._client.get(url, accept_xml=True)
        if isinstance(result, str):
            match = re.search(r'status="([^"]+)"', result)
            if match:
                return match.group(1)
        return "UNKNOWN"

    def poll_repo_created(
        self, repo_id: str, interval: int = 3, max_retries: int = 20
    ) -> str:
        """Poll get_repo_creation_status until SUCCESS or failure."""
        for attempt in range(max_retries):
            status = self.get_repo_creation_status(repo_id)
            if status == "SUCCESS":
                logger.info("Repository %s creation succeeded", repo_id)
                return status
            if status == "DELETED":
                raise BoomiApiError(
                    410, f"Repository {repo_id} was deleted during creation", ""
                )
            logger.debug(
                "Repository %s status=%s (attempt %d/%d)",
                repo_id, status, attempt + 1, max_retries,
            )
            time.sleep(interval)
        raise BoomiApiError(
            408, f"Repository {repo_id} not ready after {max_retries} polls", ""
        )

    def list_repositories(self) -> dict | str:
        """GET /repositories.

        Also extracts and stores repositoryBaseUrl (hub_cloud_url) from the response
        into config so that record operations can use the correct Repository API host.
        """
        url = f"{self._base}/repositories"
        result = self._client.get(url, accept_xml=True)
        if isinstance(result, str):
            self._extract_and_store_hub_cloud_url(result)
        return result

    def _extract_and_store_hub_cloud_url(self, xml_str: str) -> None:
        """Extract repositoryBaseUrl from GET /repositories XML and store in config.

        The repositoryBaseUrl attribute on the repository element contains the
        hub cloud hostname used for all Repository API record operations.
        """
        # Try attribute-based extraction (repositoryBaseUrl="https://...")
        match = re.search(r'repositoryBaseUrl="([^"]+)"', xml_str)
        if match:
            self._config.hub_cloud_url = match.group(1)
            logger.debug("Extracted hub_cloud_url: %s", self._config.hub_cloud_url)
        else:
            logger.warning(
                "Could not extract repositoryBaseUrl from GET /repositories response. "
                "Record operations will fail until hub_cloud_url is configured."
            )

    # ------------------------------------------------------------------
    # Source operations  (account-scoped, NOT repository-scoped)
    # ------------------------------------------------------------------

    def create_source(self, name: str) -> None:
        """POST /sources/create — create an account-level source.

        Response is ``<true/>`` on success; raises on error.
        The sourceId equals the name we provide.
        """
        url = f"{self._base}/sources/create"
        body = (
            f'<mdm:CreateSourceRequest xmlns:mdm="{_MDM_NS}"'
            f' xmlns:xsi="{_XSI_NS}">'
            f"<mdm:name>{xml_escape(name)}</mdm:name>"
            f"<mdm:sourceId>{xml_escape(name)}</mdm:sourceId>"
            f"</mdm:CreateSourceRequest>"
        )
        self._client.post(
            url, data=body, content_type="application/xml", accept_xml=True,
        )

    def list_sources(self) -> dict | str:
        """GET /sources — list account-level sources."""
        url = f"{self._base}/sources"
        return self._client.get(url, accept_xml=True)

    # ------------------------------------------------------------------
    # Staging area operations  (universe-scoped, Platform API)
    # ------------------------------------------------------------------

    def add_staging_area(
        self, universe_id: str, source_id: str, name: str, staging_id: str
    ) -> str:
        """POST /repositories/{repoId}/universes/{universeId}/sources/{sourceId}/stagingArea/create.

        Creates a staging area for the given source in a universe, which marks
        the source as allowed to send record update batches.  Without this,
        record writes from the source are rejected with:
          "this source is not yet marked as one that can send updates"

        Uses Platform API credentials (self._client), NOT Repository API.
        Returns the system staging area UUID from the response.
        """
        repo_id = self._config.boomi_repo_id
        url = (
            f"{self._base}/repositories/{repo_id}"
            f"/universes/{universe_id}"
            f"/sources/{source_id}/stagingArea/create"
        )
        body = (
            f'<mdm:CreateStagingAreaRequest xmlns:mdm="{_MDM_NS}"'
            f' xmlns:xsi="{_XSI_NS}">'
            f"<mdm:name>{xml_escape(name)}</mdm:name>"
            f"<mdm:id>{xml_escape(staging_id)}</mdm:id>"
            f"</mdm:CreateStagingAreaRequest>"
        )
        result = self._client.post(
            url, data=body, content_type="application/xml", accept_xml=True,
        )
        if isinstance(result, str):
            match = re.search(r"<mdm:id>([^<]+)</mdm:id>", result)
            if match:
                return match.group(1)
            # Fallback: try UUID pattern anywhere in the response
            match = re.search(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                result, re.IGNORECASE,
            )
            if match:
                return match.group(0)
        return staging_id  # Return the requested ID as fallback

    def get_staging_area_status(
        self, universe_id: str, source_id: str, system_staging_area_id: str
    ) -> str:
        """GET /repositories/{repoId}/universes/{universeId}/sources/{sourceId}/stagingArea/{systemId}/status.

        Returns state string: READY, CREATED, DISABLED, or DELETED.
        Used to verify a staging area was created successfully.
        """
        repo_id = self._config.boomi_repo_id
        url = (
            f"{self._base}/repositories/{repo_id}"
            f"/universes/{universe_id}"
            f"/sources/{source_id}"
            f"/stagingArea/{system_staging_area_id}/status"
        )
        result = self._client.get(url, accept_xml=True)
        if isinstance(result, str):
            match = re.search(r"<mdm:state>([^<]+)</mdm:state>", result)
            if match:
                return match.group(1)
            # Fallback: try status attribute pattern
            match = re.search(r'state="([^"]+)"', result)
            if match:
                return match.group(1)
        return "UNKNOWN"

    # ------------------------------------------------------------------
    # Initial Load operations  (universe-scoped, Platform API)
    # ------------------------------------------------------------------

    def enable_initial_load(self, universe_id: str, source_id: str) -> str:
        """POST /repositories/{repoId}/universes/{universeId}/sources/{sourceId}/enableInitialLoad.

        Puts the source into Initial Load mode so a staging area can be
        created.  Only one source per universe can be in this mode at a time.
        Sends an empty body.  Returns the raw response string.
        """
        repo_id = self._config.boomi_repo_id
        url = (
            f"{self._base}/repositories/{repo_id}"
            f"/universes/{universe_id}"
            f"/sources/{source_id}/enableInitialLoad"
        )
        return self._client.post(url, accept_xml=True)

    def finish_initial_load(self, universe_id: str, source_id: str) -> str:
        """POST /repositories/{repoId}/universes/{universeId}/sources/{sourceId}/finishInitialLoad.

        Releases the Initial Load lock for the source so the next source
        can be initialized.  Must be called after staging area creation.
        Sends an empty body.  Returns the raw response string.
        """
        repo_id = self._config.boomi_repo_id
        url = (
            f"{self._base}/repositories/{repo_id}"
            f"/universes/{universe_id}"
            f"/sources/{source_id}/finishInitialLoad"
        )
        return self._client.post(url, accept_xml=True)

    # ------------------------------------------------------------------
    # Model operations  (account-scoped, NOT repository-scoped)
    # ------------------------------------------------------------------

    def create_model(self, model_spec_dict: dict) -> str:
        """POST /models — create model from JSON spec dict.

        Converts the JSON model spec to XML ``<mdm:CreateModelRequest>``.
        Returns the model ID string.
        """
        url = f"{self._base}/models"
        body = self._model_spec_to_xml(model_spec_dict)
        result = self._client.post(
            url, data=body, content_type="application/xml", accept_xml=True,
        )
        if isinstance(result, str):
            match = re.search(r"<mdm:id>([^<]+)</mdm:id>", result)
            if match:
                return match.group(1)
        raise BoomiApiError(
            500, f"Could not parse model ID from response: {result!r}", url,
        )

    def get_model(self, model_id: str) -> dict | str:
        """GET /models/{modelId}."""
        url = f"{self._base}/models/{model_id}"
        return self._client.get(url, accept_xml=True)

    def publish_model(self, model_id: str) -> dict | str:
        """POST /models/{modelId}/publish."""
        url = f"{self._base}/models/{model_id}/publish"
        body = (
            f'<mdm:PublishModelRequest xmlns:xsi="{_XSI_NS}"'
            f' xmlns:mdm="{_MDM_NS}">'
            f"<mdm:notes>Initial publication</mdm:notes>"
            f"</mdm:PublishModelRequest>"
        )
        return self._client.post(
            url, data=body, content_type="application/xml", accept_xml=True,
        )

    def deploy_model(self, model_id: str) -> str:
        """POST /universe/{modelId}/deploy?repositoryId={repoId}.

        ``universeID == modelID`` in the DataHub Platform API.
        Sends an empty body.  Returns the deployment ID for polling.
        """
        repo_id = self._config.boomi_repo_id
        url = f"{self._base}/universe/{model_id}/deploy?repositoryId={repo_id}"
        result = self._client.post(url, accept_xml=True)
        if isinstance(result, str):
            match = re.search(r"<mdm:id>([^<]+)</mdm:id>", result)
            if match:
                return match.group(1)
        raise BoomiApiError(
            500,
            f"Could not parse deployment ID from response: {result!r}",
            url,
        )

    def get_deployment_status(
        self, universe_id: str, deployment_id: str
    ) -> str:
        """GET /universe/{universeId}/deployments/{deploymentId}.

        Returns status string: SUCCESS, PENDING, or CANCELED.
        """
        url = (
            f"{self._base}/universe/{universe_id}"
            f"/deployments/{deployment_id}"
        )
        result = self._client.get(url, accept_xml=True)
        if isinstance(result, str):
            match = re.search(r"<mdm:status>([^<]+)</mdm:status>", result)
            if match:
                return match.group(1)
        return "UNKNOWN"

    def poll_model_deployed(
        self,
        model_id: str,
        deployment_id: str,
        interval: int = 3,
        max_retries: int = 20,
    ) -> str:
        """Poll deployment status until SUCCESS or failure."""
        for attempt in range(max_retries):
            status = self.get_deployment_status(model_id, deployment_id)
            if status == "SUCCESS":
                logger.info("Model %s deployment succeeded", model_id)
                return status
            if status == "CANCELED":
                raise BoomiApiError(
                    410,
                    f"Model {model_id} deployment was canceled",
                    "",
                )
            logger.debug(
                "Model %s deployment status=%s (attempt %d/%d)",
                model_id, status, attempt + 1, max_retries,
            )
            time.sleep(interval)
        raise BoomiApiError(
            408, f"Model {model_id} not deployed after {max_retries} polls", ""
        )

    # ------------------------------------------------------------------
    # Record operations  (Repository API — hub_cloud_url, repo credentials)
    # ------------------------------------------------------------------

    def query_records(self, model_name: str, filter_xml: str) -> dict | str:
        """POST https://{hub_cloud_url}/mdm/universes/{universeId}/records/query.

        C2a fix: Uses Repository API host (hub_cloud_url) and universe ID path.
        C2b fix: Uses repo credentials via _repo_client (generatedUser:hubAuthToken Basic Auth).
        """
        url = f"{self._record_base(model_name)}/records/query"
        return self._repo_client.post(
            url, data=filter_xml, content_type="application/xml", accept_xml=True,
        )

    def create_record(self, model_name: str, record_xml: str, source: str) -> dict | str:
        """POST https://{hub_cloud_url}/mdm/universes/{universeId}/records.

        C2a fix: Uses Repository API host (hub_cloud_url) and universe ID path.
        C2b fix: Uses repo credentials via _repo_client.
        C2d fix: No ?source= query parameter — source is specified only in <batch src="...">.
        """
        url = f"{self._record_base(model_name)}/records"
        return self._repo_client.post(
            url, data=record_xml, content_type="application/xml", accept_xml=True,
        )

    def delete_record(self, model_name: str, record_id: str) -> dict | str:
        """End-date a record via batch POST with op="DELETE".

        C2a fix: Uses Repository API host and universe ID path.
        C2b fix: Uses repo credentials via _repo_client.
        C2e fix: Repository API does not support HTTP DELETE. Use batch POST with
                 op="DELETE" on the entity element to end-date the record.
        """
        entity_tag = xml_escape(model_name)
        delete_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<batch src="PROMOTION_ENGINE">\n'
            f'  <{entity_tag} op="DELETE"><id>{xml_escape(record_id)}</id></{entity_tag}>\n'
            "</batch>"
        )
        url = f"{self._record_base(model_name)}/records"
        return self._repo_client.post(
            url, data=delete_xml, content_type="application/xml", accept_xml=True,
        )

    # ------------------------------------------------------------------
    # XML builders
    # ------------------------------------------------------------------

    @staticmethod
    def _model_spec_to_xml(spec: dict) -> str:
        """Convert a JSON model spec dict to ``<mdm:CreateModelRequest>`` XML.

        Reads the repo-local model spec format (modelName, fields with
        name/type/required/matchField, matchRules, sources).
        """
        lines: list[str] = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            f'<mdm:CreateModelRequest xmlns:xsi="{_XSI_NS}"'
            f' xmlns:mdm="{_MDM_NS}">',
            f"    <mdm:name>{xml_escape(spec['modelName'])}</mdm:name>",
            "    <mdm:fields>",
        ]

        # --- fields ---
        for field in spec["fields"]:
            # Skip 'id' — DataHub auto-provides a system id field at the root level;
            # including a user-defined 'id' causes a 400 error.
            if field["name"] == "id":
                continue
            ftype = _FIELD_TYPE_MAP.get(field["type"], "STRING")
            # M3 fix: generate UPPER_SNAKE_CASE uniqueId (e.g. devComponentId → DEV_COMPONENT_ID)
            uid = re.sub(r"(?<!^)(?=[A-Z])", "_", field["name"]).upper()
            req = str(field.get("required", False)).lower()
            lines.append(
                f'        <mdm:field name="{xml_escape(field["name"])}"'
                f' repeatable="false" required="{req}"'
                f' type="{ftype}" uniqueId="{uid}"/>'
            )
        lines.append("    </mdm:fields>")

        # --- sources ---
        lines.append("    <mdm:sources>")
        for idx, src in enumerate(spec.get("sources", [])):
            is_default = "true" if idx == 0 else "false"
            sid = xml_escape(src["name"])
            lines.extend([
                # M2a fix: type="Both" (contribute + receive channel updates).
                # "Contribute" is not a valid DataHub source type value.
                f'        <mdm:source id="{sid}" type="Both"'
                f' allowMultipleLinks="false" default="{is_default}">',
                "            <mdm:inbound>",
                '                <mdm:createApproval required="false"/>',
                '                <mdm:updateApproval required="false"/>',
                "                <mdm:updateApprovalWithBaseValue>"
                "false</mdm:updateApprovalWithBaseValue>",
                '                <mdm:endDateApproval required="false"/>',
                "                <mdm:earlyChangeDetectionEnabled>"
                "true</mdm:earlyChangeDetectionEnabled>",
                "            </mdm:inbound>",
                # M2b fix: add <mdm:outbound> block so the source can receive channel updates.
                "            <mdm:outbound>",
                "                <mdm:channelUpdatesFields>All</mdm:channelUpdatesFields>",
                "                <mdm:sendCreates>true</mdm:sendCreates>",
                "            </mdm:outbound>",
                "        </mdm:source>",
            ])
        lines.append("    </mdm:sources>")

        # --- data quality (empty) ---
        lines.append("    <mdm:dataQualitySteps/>")

        # --- match rules ---
        lines.append("    <mdm:matchRules>")
        for rule in spec.get("matchRules", []):
            lines.append('        <mdm:matchRule topLevelOperator="AND">')
            for field_name in rule["fields"]:
                # M3 fix: fieldUniqueId must use UPPER_SNAKE_CASE to match the uniqueId
                # generated for the field above (e.g. devComponentId → DEV_COMPONENT_ID)
                field_uid = re.sub(r"(?<!^)(?=[A-Z])", "_", field_name).upper()
                lines.extend([
                    "            <mdm:simpleExpression>",
                    f"                <mdm:fieldUniqueId>"
                    f"{field_uid}</mdm:fieldUniqueId>",
                    "            </mdm:simpleExpression>",
                ])
            lines.append("        </mdm:matchRule>")
        lines.append("    </mdm:matchRules>")

        lines.append("    <mdm:tags/>")
        lines.append("</mdm:CreateModelRequest>")
        return "\n".join(lines)

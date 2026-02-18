"""Boomi DataHub MDM API wrapper.

All Platform API endpoints are XML-only — JSON request/response bodies
are not supported.  See rest-api.md for full reference.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

from setup.api.client import BoomiClient, BoomiApiError
from setup.config import BoomiConfig

logger = logging.getLogger(__name__)

# Map JSON model-spec field types → Platform API type attribute values
_FIELD_TYPE_MAP = {
    "String": "STRING",
    "Number": "INTEGER",
    "Date": "DATETIME",
    "Boolean": "BOOLEAN",
}

_MDM_NS = "http://mdm.api.platform.boomi.com/"
_XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class DataHubApi:
    """Wrapper for Boomi DataHub MDM REST API v1 operations."""

    def __init__(self, client: BoomiClient, config: BoomiConfig) -> None:
        self._client = client
        self._config = config
        self._base = (
            f"{config.cloud_base_url}/mdm/api/rest/v1/{config.boomi_account_id}"
        )

    @property
    def _repo_base(self) -> str:
        """Repository-scoped base URL (for record operations)."""
        return f"{self._base}/repositories/{self._config.boomi_repo_id}"

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
        """Parse <mdm:Clouds> XML response into list of cloud dicts."""
        clouds = []
        for match in re.finditer(
            r'<mdm:Cloud\s+cloudId="([^"]+)"\s+containerId="([^"]+)"\s+name="([^"]+)"',
            xml_str,
        ):
            clouds.append({
                "cloudId": match.group(1),
                "containerId": match.group(2),
                "name": match.group(3),
            })
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
        """GET /repositories."""
        url = f"{self._base}/repositories"
        return self._client.get(url, accept_xml=True)

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
    # Record operations  (repository-scoped)
    # ------------------------------------------------------------------

    def query_records(self, model_name: str, filter_xml: str) -> dict | str:
        """POST /repositories/{repoId}/models/{modelName}/records/query."""
        url = f"{self._repo_base}/models/{model_name}/records/query"
        return self._client.post(
            url, data=filter_xml, content_type="application/xml", accept_xml=True,
        )

    def create_record(
        self, model_name: str, record_xml: str, source: str
    ) -> dict | str:
        """POST /repositories/{repoId}/models/{modelName}/records?source={source}."""
        url = f"{self._repo_base}/models/{model_name}/records?source={source}"
        return self._client.post(
            url, data=record_xml, content_type="application/xml", accept_xml=True,
        )

    def delete_record(self, model_name: str, record_id: str) -> dict | str:
        """DELETE /repositories/{repoId}/models/{modelName}/records/{recordId}."""
        url = f"{self._repo_base}/models/{model_name}/records/{record_id}"
        return self._client.delete(url, accept_xml=True)

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
            ftype = _FIELD_TYPE_MAP.get(field["type"], "STRING")
            uid = field["name"].upper()
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
                f'        <mdm:source id="{sid}" type="Contribute"'
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
                lines.extend([
                    "            <mdm:simpleExpression>",
                    f"                <mdm:fieldUniqueId>"
                    f"{field_name.upper()}</mdm:fieldUniqueId>",
                    "            </mdm:simpleExpression>",
                ])
            lines.append("        </mdm:matchRule>")
        lines.append("    </mdm:matchRules>")

        lines.append("    <mdm:tags/>")
        lines.append("</mdm:CreateModelRequest>")
        return "\n".join(lines)

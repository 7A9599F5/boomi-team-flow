"""Boomi DataHub MDM API wrapper."""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

from setup.api.client import BoomiClient, BoomiApiError
from setup.config import BoomiConfig

logger = logging.getLogger(__name__)


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
        """Repository-scoped base URL."""
        return f"{self._base}/repositories/{self._config.boomi_repo_id}"

    # -- Hub Cloud operations --

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

    # -- Repository operations --

    def create_repository(self, cloud_id: str, repo_name: str) -> str:
        """POST /clouds/{cloudId}/repositories/{repoName}/create.

        Sends an empty body. Returns the repository ID string.
        """
        url = f"{self._base}/clouds/{cloud_id}/repositories/{repo_name}/create"
        # Empty body POST — pass None so no Content-Type is sent
        # (DataHub Platform API does not support JSON request bodies)
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
        return self._client.get(url)

    # -- Source operations --

    def create_source(
        self, name: str, source_type: str = "contribute-only"
    ) -> dict | str:
        """POST /repositories/{repoId}/sources."""
        url = f"{self._repo_base}/sources"
        body = json.dumps({"name": name, "type": source_type})
        return self._client.post(url, data=body)

    def list_sources(self) -> dict | str:
        """GET /repositories/{repoId}/sources."""
        url = f"{self._repo_base}/sources"
        return self._client.get(url)

    # -- Model operations --

    def create_model(self, model_spec_dict: dict) -> dict | str:
        """POST /repositories/{repoId}/models with JSON model spec."""
        url = f"{self._repo_base}/models"
        body = json.dumps(model_spec_dict)
        return self._client.post(url, data=body)

    def get_model(self, model_id: str) -> dict | str:
        """GET /repositories/{repoId}/models/{modelId}."""
        url = f"{self._repo_base}/models/{model_id}"
        return self._client.get(url)

    def publish_model(self, model_id: str) -> dict | str:
        """POST /repositories/{repoId}/models/{modelId}/publish."""
        url = f"{self._repo_base}/models/{model_id}/publish"
        return self._client.post(url, data="{}")

    def deploy_model(self, model_id: str) -> dict | str:
        """POST /repositories/{repoId}/models/{modelId}/deploy."""
        url = f"{self._repo_base}/models/{model_id}/deploy"
        return self._client.post(url, data="{}")

    def poll_model_deployed(
        self, model_id: str, interval: int = 3, max_retries: int = 10
    ) -> dict | str:
        """Poll get_model until status=DEPLOYED."""
        for attempt in range(max_retries):
            result = self.get_model(model_id)
            if isinstance(result, dict) and result.get("status") == "DEPLOYED":
                logger.info("Model %s is DEPLOYED", model_id)
                return result
            logger.debug(
                "Model %s not deployed (attempt %d/%d)",
                model_id, attempt + 1, max_retries,
            )
            time.sleep(interval)
        raise BoomiApiError(
            408, f"Model {model_id} not deployed after {max_retries} polls", ""
        )

    # -- Record operations --

    def query_records(self, model_name: str, filter_xml: str) -> dict | str:
        """POST /repositories/{repoId}/models/{modelName}/records/query with XML."""
        url = f"{self._repo_base}/models/{model_name}/records/query"
        return self._client.post(
            url, data=filter_xml, content_type="application/xml", accept_xml=True
        )

    def create_record(
        self, model_name: str, record_xml: str, source: str
    ) -> dict | str:
        """POST /repositories/{repoId}/models/{modelName}/records?source={source}."""
        url = f"{self._repo_base}/models/{model_name}/records?source={source}"
        return self._client.post(
            url, data=record_xml, content_type="application/xml", accept_xml=True
        )

    def delete_record(self, model_name: str, record_id: str) -> dict | str:
        """DELETE /repositories/{repoId}/models/{modelName}/records/{recordId}."""
        url = f"{self._repo_base}/models/{model_name}/records/{record_id}"
        return self._client.delete(url)

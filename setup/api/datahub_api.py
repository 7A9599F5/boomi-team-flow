"""Boomi DataHub MDM API wrapper."""
from __future__ import annotations

import json
import logging
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

    # -- Repository operations --

    def create_repository(self, name: str, description: str) -> dict | str:
        """POST /repositories to create a new repository."""
        url = f"{self._base}/repositories"
        body = json.dumps({"name": name, "description": description})
        return self._client.post(url, data=body)

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

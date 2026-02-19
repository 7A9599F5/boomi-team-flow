"""Boomi Partner Platform API wrapper."""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from setup.api.client import BoomiClient, BoomiApiError
from setup.config import BoomiConfig

logger = logging.getLogger(__name__)


class PlatformApi:
    """Wrapper for Boomi Partner REST API v1 operations."""

    def __init__(self, client: BoomiClient, config: BoomiConfig) -> None:
        self._client = client
        self._config = config
        self._base = (
            f"{config.cloud_base_url}/partner/api/rest/v1/{config.boomi_account_id}"
        )

    # -- Component operations --

    def get_component(
        self, component_id: str, account_id: Optional[str] = None
    ) -> dict | str:
        """GET /Component/{id}. Use overrideAccount for cross-account reads."""
        url = f"{self._base}/Component/{component_id}"
        if account_id and account_id != self._config.boomi_account_id:
            url += f"?overrideAccount={account_id}"
        return self._client.get(url, accept_xml=True)

    def create_component(self, xml_body: str) -> dict | str:
        """POST /Component with XML body."""
        url = f"{self._base}/Component"
        return self._client.post(url, data=xml_body, content_type="application/xml", accept_xml=True)

    def query_components(self, query_filter: str) -> dict | str:
        """POST /Component/query with XML filter body."""
        url = f"{self._base}/Component/query"
        return self._client.post(url, data=query_filter, content_type="application/xml", accept_xml=True)

    # -- Folder operations --

    def create_folder(self, name: str, parent_id: str = "") -> dict | str:
        """POST /Folder to create a folder under parent_id."""
        url = f"{self._base}/Folder"
        body = json.dumps({"name": name, "parentId": parent_id})
        return self._client.post(url, data=body)

    # -- Branch operations --

    def create_branch(self, name: str) -> dict | str:
        """POST /Branch to create a new branch."""
        url = f"{self._base}/Branch"
        body = json.dumps({"name": name})
        return self._client.post(url, data=body)

    def get_branch(self, branch_id: str) -> dict | str:
        """GET /Branch/{id}."""
        url = f"{self._base}/Branch/{branch_id}"
        return self._client.get(url)

    def poll_branch_ready(
        self, branch_id: str, interval: int = 5, max_retries: int = 6
    ) -> dict | str:
        """Poll GET /Branch/{id} until ready=true."""
        for attempt in range(max_retries):
            result = self.get_branch(branch_id)
            if isinstance(result, dict) and result.get("ready") == "true":
                logger.info("Branch %s is ready", branch_id)
                return result
            logger.debug(
                "Branch %s not ready (attempt %d/%d)", branch_id, attempt + 1, max_retries
            )
            time.sleep(interval)
        raise BoomiApiError(
            408, f"Branch {branch_id} not ready after {max_retries} polls", ""
        )

    def delete_branch(self, branch_id: str) -> dict | str:
        """DELETE /Branch/{id}. Treats 404 as success (already deleted)."""
        url = f"{self._base}/Branch/{branch_id}"
        try:
            return self._client.delete(url)
        except BoomiApiError as e:
            if e.status_code == 404:
                logger.debug("Branch %s already deleted (404)", branch_id)
                return {}
            raise

    # -- Merge operations --

    def create_merge_request(
        self, branch_id: str, main_branch_id: str, strategy: str = "OVERRIDE"
    ) -> dict | str:
        """POST /MergeRequest."""
        url = f"{self._base}/MergeRequest"
        body = json.dumps({
            "sourceBranchId": branch_id,
            "destinationBranchId": main_branch_id,
            "priorityBranch": branch_id,
            "strategy": strategy,
        })
        return self._client.post(url, data=body)

    def execute_merge(self, merge_request_id: str) -> dict | str:
        """POST /MergeRequest/{id}/execute."""
        url = f"{self._base}/MergeRequest/{merge_request_id}/execute"
        return self._client.post(url, data=json.dumps({"mergeRequestAction": "MERGE"}))

    def get_merge_request(self, merge_request_id: str) -> dict | str:
        """GET /MergeRequest/{id}."""
        url = f"{self._base}/MergeRequest/{merge_request_id}"
        return self._client.get(url)

    def poll_merge_status(
        self, merge_request_id: str, interval: int = 5, max_retries: int = 12
    ) -> dict | str:
        """Poll GET /MergeRequest/{id} until MERGED or FAILED_TO_MERGE."""
        terminal_statuses = {"MERGED", "FAILED_TO_MERGE"}
        for attempt in range(max_retries):
            result = self.get_merge_request(merge_request_id)
            if isinstance(result, dict):
                status = result.get("stage", "")
                if status in terminal_statuses:
                    logger.info("Merge %s reached status: %s", merge_request_id, status)
                    return result
            logger.debug(
                "Merge %s pending (attempt %d/%d)",
                merge_request_id, attempt + 1, max_retries,
            )
            time.sleep(interval)
        raise BoomiApiError(
            408,
            f"Merge {merge_request_id} not complete after {max_retries} polls",
            "",
        )

    # -- PackagedComponent operations --

    def create_packaged_component(
        self, component_id: str, version: str, notes: str = ""
    ) -> dict | str:
        """POST /PackagedComponent."""
        url = f"{self._base}/PackagedComponent"
        body = json.dumps({
            "componentId": component_id,
            "packageVersion": version,
            "notes": notes,
        })
        return self._client.post(url, data=body)

    def query_packaged_components(self, query_xml: str) -> dict | str:
        """POST /PackagedComponent/query with XML body."""
        url = f"{self._base}/PackagedComponent/query"
        return self._client.post(url, data=query_xml, content_type="application/xml")

    # -- Release status operations --

    def get_release_status(self, release_id: str) -> dict | str:
        """GET /ReleaseIntegrationPackStatus/{id}."""
        url = f"{self._base}/ReleaseIntegrationPackStatus/{release_id}"
        return self._client.get(url)

    # -- Integration Pack operations --

    def create_integration_pack(self, name: str, description: str) -> dict | str:
        """POST /IntegrationPack."""
        url = f"{self._base}/IntegrationPack"
        body = json.dumps({
            "name": name,
            "description": description,
            "installationType": "SINGLE",
        })
        result = self._client.post(url, data=body)
        if isinstance(result, dict):
            result_id = result.get("id", "")
            if result_id:
                result["id"] = result_id
        return result

    def add_to_integration_pack(self, pack_id: str, package_id: str) -> dict | str:
        """POST /IntegrationPack/{packId}/PackagedComponent/{packageId}."""
        url = f"{self._base}/IntegrationPack/{pack_id}/PackagedComponent/{package_id}"
        return self._client.post(url, data=None)

    def release_integration_pack(
        self, pack_id: str, components: list[dict], schedule: str = "IMMEDIATELY"
    ) -> dict | str:
        """POST /ReleaseIntegrationPack."""
        url = f"{self._base}/ReleaseIntegrationPack"
        comp_elements = "\n".join(
            f'      <bns:ReleasePackagedComponent componentId="{c["componentId"]}" version="{c["version"]}"/>'
            for c in components
        )
        body = (
            f'<bns:ReleaseIntegrationPack xmlns:bns="http://api.platform.boomi.com/"'
            f' id="{pack_id}" releaseSchedule="{schedule}">\n'
            f'  <bns:ReleasePackagedComponents>\n{comp_elements}\n'
            f'  </bns:ReleasePackagedComponents>\n'
            f'</bns:ReleaseIntegrationPack>'
        )
        return self._client.post(url, data=body, content_type="application/xml", accept_xml=True)

    # -- Utility --

    def count_components_by_prefix(self, prefix: str) -> int:
        """Query components with name starting with prefix, return count."""
        query_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<QueryFilter xmlns="http://api.platform.boomi.com/"'
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<expression operator="STARTS_WITH" property="name"'
            ' xsi:type="SimpleExpression">'
            f"<argument>{prefix}</argument>"
            "</expression>"
            "</QueryFilter>"
        )
        result = self.query_components(query_xml)
        if isinstance(result, str):
            import re
            match = re.search(r'numberOfResults="(\d+)"', result)
            if match:
                return int(match.group(1))
        return 0

    @staticmethod
    def parse_component_id(xml_response: str) -> str:
        """Extract componentId attribute from Component API XML response."""
        import re
        if isinstance(xml_response, str):
            match = re.search(r'componentId="([^"]+)"', xml_response)
            return match.group(1) if match else ""
        if isinstance(xml_response, dict):
            return xml_response.get("componentId", xml_response.get("id", ""))
        return ""

    def deploy_flow_service(self, package_id: str, env_id: str) -> dict | str:
        """POST /DeployedPackage — deploy to publisher's own environment."""
        url = f"{self._base}/DeployedPackage"
        body = json.dumps({"packageId": package_id, "environmentId": env_id})
        return self._client.post(url, data=body)

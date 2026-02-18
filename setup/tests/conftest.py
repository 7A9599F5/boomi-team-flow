"""Shared pytest fixtures for Boomi setup automation tests."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from setup.config import BoomiConfig
from setup.state import SetupState


@pytest.fixture
def mock_config() -> BoomiConfig:
    """BoomiConfig populated with test values."""
    return BoomiConfig(
        boomi_account_id="test-account-123",
        boomi_repo_id="test-repo-456",
        cloud_base_url="https://api.boomi.com",
        fss_environment_id="test-env-789",
        boomi_user="testuser@example.com",
        boomi_token="test-token-secret",
    )


@pytest.fixture
def mock_state(tmp_path: Path) -> SetupState:
    """SetupState backed by a temp file."""
    state_path = tmp_path / ".boomi-setup-state.json"
    return SetupState.create(path=state_path)


@pytest.fixture
def mock_client() -> MagicMock:
    """Mocked BoomiClient."""
    client = MagicMock()
    client.get.return_value = {}
    client.post.return_value = {}
    client.put.return_value = {}
    client.delete.return_value = {}
    return client


@pytest.fixture
def mock_platform_api() -> MagicMock:
    """Mocked PlatformApi."""
    api = MagicMock()
    api.get_component.return_value = {"componentId": "comp-1", "name": "TestComponent"}
    api.query_components.return_value = {"numberOfResults": 0, "result": []}
    api.count_components_by_prefix.return_value = 0
    return api


@pytest.fixture
def mock_datahub_api() -> MagicMock:
    """Mocked DataHubApi."""
    api = MagicMock()
    api.get_model.return_value = {"status": "DEPLOYED", "fields": []}
    api.list_sources.return_value = []
    return api


@pytest.fixture
def sample_component_response() -> dict:
    """Typical Boomi component API response."""
    return {
        "componentId": "abc-def-123",
        "name": "PROMO - FSS Op - ExecutePromotion",
        "type": "flowservice.operation",
        "folderId": "folder-001",
        "folderFullPath": "/Promoted/Promo/Operations",
        "version": 3,
        "currentVersion": 3,
        "createdDate": "2026-01-15T10:00:00Z",
        "modifiedDate": "2026-02-01T12:30:00Z",
    }


@pytest.fixture
def sample_model_response() -> dict:
    """Typical DataHub model API response."""
    return {
        "id": "model-001",
        "name": "ComponentMapping",
        "status": "DEPLOYED",
        "fields": [
            {"name": "devComponentId", "type": "String"},
            {"name": "devAccountId", "type": "String"},
            {"name": "prodComponentId", "type": "String"},
            {"name": "componentName", "type": "String"},
            {"name": "componentType", "type": "String"},
            {"name": "prodAccountId", "type": "String"},
            {"name": "prodLatestVersion", "type": "Number"},
            {"name": "lastPromotedAt", "type": "Date"},
            {"name": "lastPromotedBy", "type": "String"},
            {"name": "mappingSource", "type": "String"},
        ],
    }

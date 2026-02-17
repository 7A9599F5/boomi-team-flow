"""Tests for setup.validation.validators — per-step API verification."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from setup.validation.validators import (
    validate_models_deployed,
    validate_sources_exist,
    validate_http_ops_count,
    validate_total_components,
)


def _make_model_response(
    name: str, status: str = "DEPLOYED", field_count: int = 10
) -> dict:
    """Helper to create a model response dict."""
    return {
        "name": name,
        "status": status,
        "fields": [{"name": f"field_{i}"} for i in range(field_count)],
    }


# Expected field counts from validators module
_FIELD_COUNTS = {
    "ComponentMapping": 10,
    "DevAccountAccess": 5,
    "PromotionLog": 34,
}


class TestValidateModelsDeployed:
    def test_validate_models_deployed_success(self) -> None:
        """All 3 models return DEPLOYED with correct field counts."""
        mock_dh = MagicMock()
        mock_dh.get_model.side_effect = [
            _make_model_response("ComponentMapping", "DEPLOYED", 10),
            _make_model_response("DevAccountAccess", "DEPLOYED", 5),
            _make_model_response("PromotionLog", "DEPLOYED", 34),
        ]

        success, msg = validate_models_deployed(mock_dh, MagicMock())
        assert success is True
        assert "All 3 models deployed" in msg

    def test_validate_models_deployed_wrong_status(self) -> None:
        """One model not deployed."""
        mock_dh = MagicMock()
        mock_dh.get_model.side_effect = [
            _make_model_response("ComponentMapping", "DEPLOYED", 10),
            _make_model_response("DevAccountAccess", "DRAFT", 5),
            _make_model_response("PromotionLog", "DEPLOYED", 34),
        ]

        success, msg = validate_models_deployed(mock_dh, MagicMock())
        assert success is False
        assert "DevAccountAccess" in msg
        assert "DRAFT" in msg

    def test_validate_models_deployed_wrong_field_count(self) -> None:
        """One model has wrong field count."""
        mock_dh = MagicMock()
        mock_dh.get_model.side_effect = [
            _make_model_response("ComponentMapping", "DEPLOYED", 10),
            _make_model_response("DevAccountAccess", "DEPLOYED", 5),
            _make_model_response("PromotionLog", "DEPLOYED", 30),  # expect 34
        ]

        success, msg = validate_models_deployed(mock_dh, MagicMock())
        assert success is False
        assert "30 fields" in msg
        assert "expected 34" in msg

    def test_validate_models_deployed_api_error(self) -> None:
        """API error for one model still reports failure."""
        mock_dh = MagicMock()
        mock_dh.get_model.side_effect = [
            _make_model_response("ComponentMapping", "DEPLOYED", 10),
            Exception("Connection timeout"),
            _make_model_response("PromotionLog", "DEPLOYED", 34),
        ]

        success, msg = validate_models_deployed(mock_dh, MagicMock())
        assert success is False
        assert "failed to query" in msg


class TestValidateSourcesExist:
    def test_validate_sources_exist_success(self) -> None:
        """All 3 sources found."""
        mock_dh = MagicMock()
        mock_dh.list_sources.return_value = [
            {"name": "PROMOTION_ENGINE", "type": "contribute-only"},
            {"name": "ADMIN_SEEDING", "type": "contribute-only"},
            {"name": "ADMIN_CONFIG", "type": "contribute-only"},
        ]

        success, msg = validate_sources_exist(mock_dh, MagicMock())
        assert success is True
        assert "All 3 sources exist" in msg

    def test_validate_sources_missing(self) -> None:
        """One source missing."""
        mock_dh = MagicMock()
        mock_dh.list_sources.return_value = [
            {"name": "PROMOTION_ENGINE", "type": "contribute-only"},
            {"name": "ADMIN_CONFIG", "type": "contribute-only"},
        ]

        success, msg = validate_sources_exist(mock_dh, MagicMock())
        assert success is False
        assert "ADMIN_SEEDING" in msg

    def test_validate_sources_api_error(self) -> None:
        """API error returns failure."""
        mock_dh = MagicMock()
        mock_dh.list_sources.side_effect = Exception("Network error")

        success, msg = validate_sources_exist(mock_dh, MagicMock())
        assert success is False
        assert "Failed to list sources" in msg


class TestValidateHttpOpsCount:
    def test_validate_http_ops_count_correct(self) -> None:
        """Count returns 19 — success."""
        mock_platform = MagicMock()
        mock_platform.query_components.return_value = list(range(19))

        success, msg = validate_http_ops_count(mock_platform, MagicMock())
        assert success is True
        assert "19" in msg

    def test_validate_http_ops_count_wrong(self) -> None:
        """Count returns 15, expect failure."""
        mock_platform = MagicMock()
        mock_platform.query_components.return_value = list(range(15))

        success, msg = validate_http_ops_count(mock_platform, MagicMock())
        assert success is False
        assert "15" in msg


class TestValidateTotalComponents:
    def test_validate_total_components_success(self) -> None:
        """Count returns 85, success."""
        mock_platform = MagicMock()
        mock_platform.query_components.return_value = list(range(85))

        success, msg = validate_total_components(mock_platform, MagicMock())
        assert success is True
        assert "85" in msg

    def test_validate_total_components_wrong(self) -> None:
        """Count returns 80, expect failure."""
        mock_platform = MagicMock()
        mock_platform.query_components.return_value = list(range(80))

        success, msg = validate_total_components(mock_platform, MagicMock())
        assert success is False
        assert "80" in msg

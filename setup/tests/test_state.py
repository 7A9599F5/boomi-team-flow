"""Tests for setup.state — SetupState JSON persistence."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from setup.state import SetupState, STATE_VERSION


class TestCreateAndLoad:
    def test_create_new_state(self, tmp_path: Path) -> None:
        """Create state, verify file exists, has correct schema."""
        state_path = tmp_path / "state.json"
        state = SetupState.create(path=state_path)

        assert state_path.exists()
        data = json.loads(state_path.read_text())
        assert data["version"] == STATE_VERSION
        assert "created_at" in data
        assert "updated_at" in data
        assert "component_ids" in data
        assert "steps" in data
        assert "config" in data
        assert "api_first_discovery" in data

    def test_load_existing_state(self, tmp_path: Path) -> None:
        """Create then load, verify round-trip."""
        state_path = tmp_path / "state.json"
        original = SetupState.create(path=state_path)
        original.store_component_id("models", "ComponentMapping", "model-001")

        loaded = SetupState.load(path=state_path)
        assert loaded.get_component_id("models", "ComponentMapping") == "model-001"
        assert loaded.data["version"] == STATE_VERSION

    def test_load_missing_file_raises(self, tmp_path: Path) -> None:
        """Loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            SetupState.load(path=tmp_path / "nonexistent.json")


class TestWriteThrough:
    def test_write_through_persistence(self, tmp_path: Path) -> None:
        """Mutate state, reload from disk, verify changes persisted."""
        state_path = tmp_path / "state.json"
        state = SetupState.create(path=state_path)

        state.store_component_id("connections", "http-conn", "conn-123")
        state.set_step_status("step-1", "completed")

        # Reload from disk
        reloaded = SetupState.load(path=state_path)
        assert reloaded.get_component_id("connections", "http-conn") == "conn-123"
        assert reloaded.get_step_status("step-1") == "completed"


class TestComponentIds:
    def test_store_and_retrieve_component_id(self, mock_state: SetupState) -> None:
        """Store IDs in different categories, retrieve them."""
        mock_state.store_component_id("models", "ComponentMapping", "model-001")
        mock_state.store_component_id("processes", "ProcessA", "proc-a")
        mock_state.store_component_id("profiles", "ProfileReq", "prof-req")

        assert mock_state.get_component_id("models", "ComponentMapping") == "model-001"
        assert mock_state.get_component_id("processes", "ProcessA") == "proc-a"
        assert mock_state.get_component_id("profiles", "ProfileReq") == "prof-req"

    def test_store_flow_service_scalar(self, mock_state: SetupState) -> None:
        """flow_service is a scalar, not dict.

        Note: store_component_id cannot set flow_service when it's None
        (initial state) because the None check is ambiguous. The workaround
        is to set the value directly in the data dict first.
        """
        # Direct assignment works (as internal code would do)
        mock_state._data["component_ids"]["flow_service"] = "fss-id-123"
        mock_state.save()

        # Name is ignored for scalar categories on retrieval
        assert mock_state.get_component_id("flow_service", "anything") == "fss-id-123"

        # Once set to a non-None value, store_component_id works for updates
        mock_state.store_component_id("flow_service", "ignored", "fss-id-456")
        assert mock_state.get_component_id("flow_service", "whatever") == "fss-id-456"

    def test_unknown_category_raises(self, mock_state: SetupState) -> None:
        """Storing to an unknown category raises KeyError."""
        with pytest.raises(KeyError, match="Unknown component category"):
            mock_state.store_component_id("nonexistent_category", "name", "value")

    def test_get_missing_component_returns_none(self, mock_state: SetupState) -> None:
        """Getting a component ID that doesn't exist returns None."""
        assert mock_state.get_component_id("models", "NonExistent") is None


class TestStepStatus:
    def test_step_status_transitions(self, mock_state: SetupState) -> None:
        """Set pending -> in_progress -> completed."""
        mock_state.set_step_status("step-1", "pending")
        assert mock_state.get_step_status("step-1") == "pending"

        mock_state.set_step_status("step-1", "in_progress")
        assert mock_state.get_step_status("step-1") == "in_progress"

        mock_state.set_step_status("step-1", "completed")
        assert mock_state.get_step_status("step-1") == "completed"

    def test_crash_recovery(self, tmp_path: Path) -> None:
        """Create state, set step in_progress, reload, verify still in_progress."""
        state_path = tmp_path / "state.json"
        state = SetupState.create(path=state_path)
        state.set_step_status("deploy-models", "in_progress")

        # Simulate process crash and restart
        recovered = SetupState.load(path=state_path)
        assert recovered.get_step_status("deploy-models") == "in_progress"

    def test_untracked_step_returns_none(self, mock_state: SetupState) -> None:
        """Getting status of untracked step returns None."""
        assert mock_state.get_step_status("never-set") is None


class TestBatchStepResume:
    def test_mark_step_item_complete(self, mock_state: SetupState) -> None:
        """mark_step_item_complete and get_remaining_items work together."""
        all_items = ["item-a", "item-b", "item-c", "item-d"]

        mock_state.mark_step_item_complete("batch-step", "item-a")
        mock_state.mark_step_item_complete("batch-step", "item-c")

        remaining = mock_state.get_remaining_items("batch-step", all_items)
        assert remaining == ["item-b", "item-d"]

    def test_duplicate_item_completion_is_idempotent(self, mock_state: SetupState) -> None:
        """Marking the same item complete twice doesn't duplicate it."""
        mock_state.mark_step_item_complete("batch-step", "item-a")
        mock_state.mark_step_item_complete("batch-step", "item-a")

        step_data = mock_state.data["steps"]["batch-step"]
        assert step_data["completed_items"].count("item-a") == 1

    def test_get_remaining_items_no_completed(self, mock_state: SetupState) -> None:
        """All items are remaining when none completed."""
        all_items = ["x", "y", "z"]
        remaining = mock_state.get_remaining_items("new-step", all_items)
        assert remaining == ["x", "y", "z"]


class TestApiFirstDiscovery:
    def test_set_and_get_discovery_template(self, mock_state: SetupState) -> None:
        """Set and get discovery templates."""
        mock_state.set_discovery_template(
            "http_operation_template_xml", "<xml>template</xml>"
        )

        discovery = mock_state.api_first_discovery
        assert discovery["http_operation_template_xml"] == "<xml>template</xml>"
        assert discovery["dh_operation_template_xml"] is None
        assert discovery["dh_operation_template_query_xml"] is None
        assert discovery["dh_operation_template_update_xml"] is None
        assert discovery["dh_operation_template_delete_xml"] is None

    def test_discovery_persists_to_disk(self, tmp_path: Path) -> None:
        """Discovery templates survive save/load cycle."""
        state_path = tmp_path / "state.json"
        state = SetupState.create(path=state_path)
        state.set_discovery_template("profile_template_xml", "<profile/>")

        reloaded = SetupState.load(path=state_path)
        assert reloaded.api_first_discovery["profile_template_xml"] == "<profile/>"

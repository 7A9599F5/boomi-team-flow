"""JSON state persistence for Boomi Build Guide Setup Automation."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

STATE_VERSION = "1.0.0"
DEFAULT_STATE_FILE = ".boomi-setup-state.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_component_ids() -> dict:
    return {
        "models": {},
        "sources": {},
        "staging_areas": {},
        "folders": {},
        "connections": {},
        "http_operations": {},
        "dh_operations": {},
        "profiles": {},
        "scripts": {},
        "fss_operations": {},
        "processes": {},
        "flow_service": None,
    }


def _empty_api_first_discovery() -> dict:
    return {
        "http_operation_template_xml": None,
        "dh_operation_template_xml": None,
        "fss_operation_template_xml": None,
        "profile_template_xml": None,
    }


def _empty_state() -> dict:
    now = _now_iso()
    return {
        "version": STATE_VERSION,
        "created_at": now,
        "updated_at": now,
        "config": {
            "boomi_account_id": "",
            "boomi_repo_id": "",
            "cloud_base_url": "https://api.boomi.com",
            "fss_environment_id": "",
            "datahub_token": "",
            "datahub_user": "",
            "hub_cloud_url": "",
            "hub_cloud_name": "",
            "universe_ids": {},
        },
        "component_ids": _empty_component_ids(),
        "steps": {},
        "api_first_discovery": _empty_api_first_discovery(),
    }


class SetupState:
    """Manages persistent state for the setup automation.

    Every mutation calls save() immediately (write-through).
    """

    def __init__(self, data: dict, path: Path) -> None:
        self._data = data
        self._path = path

    # -- Construction ----------------------------------------------------------

    @classmethod
    def create(cls, path: Optional[Path] = None) -> SetupState:
        """Create a fresh state file."""
        path = path or Path.cwd() / DEFAULT_STATE_FILE
        data = _empty_state()
        state = cls(data, path)
        state.save()
        return state

    @classmethod
    def load(cls, path: Optional[Path] = None) -> SetupState:
        """Load state from an existing file.

        Raises FileNotFoundError if the state file does not exist.
        Backfills any component_ids categories added after the file was created.
        """
        path = path or Path.cwd() / DEFAULT_STATE_FILE
        if not path.exists():
            raise FileNotFoundError(f"State file not found: {path}")
        with open(path, "r") as f:
            data = json.load(f)
        # Backfill component_ids categories added after this state file was created
        defaults = _empty_component_ids()
        existing = data.get("component_ids", {})
        for key, default_val in defaults.items():
            if key not in existing:
                existing[key] = default_val
        data["component_ids"] = existing
        return cls(data, path)

    @classmethod
    def load_or_create(cls, path: Optional[Path] = None) -> SetupState:
        """Load existing state or create a new one."""
        path = path or Path.cwd() / DEFAULT_STATE_FILE
        if path.exists():
            return cls.load(path)
        return cls.create(path)

    # -- Persistence -----------------------------------------------------------

    def save(self) -> None:
        """Write state to disk."""
        self._data["updated_at"] = _now_iso()
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def data(self) -> dict:
        return self._data

    # -- Config ----------------------------------------------------------------

    @property
    def config(self) -> dict:
        return self._data.get("config", {})

    def update_config(self, config_dict: dict) -> None:
        """Update non-credential config fields and save."""
        self._data["config"].update(config_dict)
        self.save()

    def store_universe_id(self, model_name: str, universe_id: str) -> None:
        """Store a DataHub universe ID (model UUID) for a model name and save."""
        if "universe_ids" not in self._data["config"]:
            self._data["config"]["universe_ids"] = {}
        self._data["config"]["universe_ids"][model_name] = universe_id
        self.save()

    # -- Step Status -----------------------------------------------------------

    def get_step_status(self, step_id: str) -> Optional[str]:
        """Get the status of a step, or None if not tracked."""
        step_data = self._data["steps"].get(step_id)
        if step_data is None:
            return None
        return step_data.get("status")

    def set_step_status(self, step_id: str, status: str, **kwargs: Any) -> None:
        """Set step status with optional metadata and save."""
        if step_id not in self._data["steps"]:
            self._data["steps"][step_id] = {}
        self._data["steps"][step_id]["status"] = status
        self._data["steps"][step_id]["updated_at"] = _now_iso()
        for key, value in kwargs.items():
            self._data["steps"][step_id][key] = value
        self.save()

    # -- Component IDs ---------------------------------------------------------

    def store_component_id(self, category: str, name: str, value: str) -> None:
        """Store a component ID under a category and save."""
        bucket = self._data["component_ids"].get(category)
        if bucket is None:
            raise KeyError(f"Unknown component category: {category}")
        if isinstance(bucket, dict):
            bucket[name] = value
        else:
            # flow_service is a scalar
            self._data["component_ids"][category] = value
        self.save()

    def get_component_id(self, category: str, name: str) -> Optional[str]:
        """Retrieve a stored component ID, or None if not found."""
        bucket = self._data["component_ids"].get(category)
        if bucket is None:
            return None
        if isinstance(bucket, dict):
            return bucket.get(name)
        # Scalar (flow_service) — name is ignored
        return bucket

    # -- Step Item Tracking ----------------------------------------------------

    def mark_step_item_complete(self, step_id: str, item: str) -> None:
        """Mark a specific item within a step as complete and save."""
        step_data = self._data["steps"].setdefault(step_id, {})
        completed: list = step_data.setdefault("completed_items", [])
        if item not in completed:
            completed.append(item)
        self.save()

    def get_remaining_items(self, step_id: str, all_items: list[str]) -> list[str]:
        """Return items from all_items not yet marked complete for a step."""
        step_data = self._data["steps"].get(step_id, {})
        completed = set(step_data.get("completed_items", []))
        return [item for item in all_items if item not in completed]

    # -- API First Discovery ---------------------------------------------------

    @property
    def api_first_discovery(self) -> dict:
        return self._data.get("api_first_discovery", _empty_api_first_discovery())

    def set_discovery_template(self, key: str, xml: str) -> None:
        """Store an API-first discovery template XML and save."""
        self._data["api_first_discovery"][key] = xml
        self.save()

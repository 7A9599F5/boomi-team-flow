"""Tests for setup.templates.loader — template loading from repo files."""
from __future__ import annotations

from pathlib import Path

import pytest

from setup.templates.loader import (
    get_repo_root,
    list_profiles,
    load_model_spec,
    load_profile_schema,
    parameterize,
)


class TestGetRepoRoot:
    def test_get_repo_root(self) -> None:
        """Verify it finds the repo root containing .git."""
        root = get_repo_root()
        assert root.is_dir()
        assert (root / ".git").exists() or (root / "CLAUDE.md").exists()
        assert (root / "setup").is_dir()


class TestLoadModelSpec:
    def test_load_model_spec(self) -> None:
        """Load ComponentMapping spec, verify fields."""
        spec = load_model_spec("ComponentMapping")

        assert spec["modelName"] == "ComponentMapping"
        assert spec["rootElement"] == "ComponentMapping"
        assert "fields" in spec
        assert isinstance(spec["fields"], list)
        assert len(spec["fields"]) > 0

        # Verify key match fields exist
        field_names = [f["name"] for f in spec["fields"]]
        assert "devComponentId" in field_names
        assert "devAccountId" in field_names
        assert "prodComponentId" in field_names

    def test_load_all_model_specs(self) -> None:
        """Load all 3 model specs without error."""
        for model_name in ["ComponentMapping", "DevAccountAccess", "PromotionLog"]:
            spec = load_model_spec(model_name)
            assert "modelName" in spec
            assert "fields" in spec


class TestLoadProfileSchema:
    def test_load_profile_schema(self) -> None:
        """Load executePromotion-request.json, verify structure."""
        schema = load_profile_schema("executePromotion-request")

        assert isinstance(schema, dict)
        # This profile has devAccountId and components fields
        assert "devAccountId" in schema
        assert "components" in schema

    def test_load_nonexistent_profile_raises(self) -> None:
        """Loading a nonexistent profile raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_profile_schema("nonexistent-profile-xyz")


class TestParameterize:
    def test_parameterize_placeholders(self) -> None:
        """Replace {KEY} placeholders with values from params dict."""
        result = parameterize(
            "{ACCOUNT_ID}/test/{ENV_ID}",
            {"ACCOUNT_ID": "abc", "ENV_ID": "prod"},
        )
        assert result == "abc/test/prod"

    def test_parameterize_no_match(self) -> None:
        """Template without matching placeholders is unchanged."""
        result = parameterize("no-placeholders-here", {"KEY": "value"})
        assert result == "no-placeholders-here"

    def test_parameterize_multiple_occurrences(self) -> None:
        """Same placeholder used multiple times is replaced everywhere."""
        result = parameterize("{ID}-{ID}-end", {"ID": "x"})
        assert result == "x-x-end"


class TestListProfiles:
    def test_list_profiles(self) -> None:
        """Verify returns list of profile names."""
        profiles = list_profiles()

        assert isinstance(profiles, list)
        assert len(profiles) > 0

        # Check a few known profiles exist
        assert "executePromotion-request" in profiles
        assert "executePromotion-response" in profiles
        assert "getDevAccounts-request" in profiles

        # All names should be strings without .json extension
        for name in profiles:
            assert isinstance(name, str)
            assert not name.endswith(".json")

    def test_list_profiles_returns_sorted(self) -> None:
        """Profile list should be sorted alphabetically."""
        profiles = list_profiles()
        assert profiles == sorted(profiles)

"""Configuration management for Boomi Build Guide Setup Automation."""
from __future__ import annotations

import os
from typing import Optional

import click
from pydantic import BaseModel, Field


class BoomiConfig(BaseModel):
    """Boomi account and API configuration."""

    boomi_account_id: str = Field(default="", description="Boomi account ID")
    boomi_repo_id: str = Field(default="", description="Boomi repository ID")
    cloud_base_url: str = Field(
        default="https://api.boomi.com",
        description="Boomi Platform API base URL",
    )
    fss_environment_id: str = Field(
        default="", description="Flow Services Server environment ID"
    )
    boomi_user: str = Field(default="", description="Boomi API username")
    boomi_token: str = Field(default="", description="Boomi API token")
    # DataHub Repository API fields — populated during setup
    hub_cloud_url: str = Field(
        default="",
        description="Hub cloud base URL for Repository API (e.g. https://c01-usa-east.hub.boomi.com)",
    )
    hub_auth_token: str = Field(
        default="",
        description="DataHub auth token for Repository API Basic Auth",
    )
    hub_auth_user: str = Field(
        default="",
        description="DataHub auth username for Repository API Basic Auth (generated, not account ID)",
    )
    universe_ids: dict = Field(
        default_factory=dict,
        description="Mapping of model_name -> universe_id (model UUID) for record operations",
    )

    @property
    def is_complete(self) -> bool:
        """Check if all required input fields are populated.

        Note: boomi_repo_id is excluded — it is produced by Step 1.0
        (CreateRepo), not a user input.
        """
        return all([
            self.boomi_account_id,
            self.fss_environment_id,
            self.boomi_user,
            self.boomi_token,
        ])

    @property
    def has_credentials(self) -> bool:
        """Check if credentials are set."""
        return bool(self.boomi_user and self.boomi_token)

    def to_state_dict(self) -> dict:
        """Return config dict without credentials (for state file persistence)."""
        return {
            "boomi_account_id": self.boomi_account_id,
            "boomi_repo_id": self.boomi_repo_id,
            "cloud_base_url": self.cloud_base_url,
            "fss_environment_id": self.fss_environment_id,
            "hub_cloud_url": self.hub_cloud_url,
            "universe_ids": self.universe_ids,
        }


# Mapping of env var names to config field names
_ENV_MAP: dict[str, str] = {
    "BOOMI_USER": "boomi_user",
    "BOOMI_TOKEN": "boomi_token",
    "BOOMI_ACCOUNT": "boomi_account_id",
    "BOOMI_REPO": "boomi_repo_id",
    "BOOMI_FSS_ENVIRONMENT": "fss_environment_id",
}

# Fields that should be prompted interactively (with labels).
# Note: boomi_repo_id is intentionally excluded — it is produced by Step 1.0
# (CreateRepo), not a user input.  Users with a pre-existing repo can set the
# BOOMI_REPO env var to skip repository creation.
_INTERACTIVE_FIELDS: list[tuple[str, str, bool]] = [
    ("boomi_account_id", "Boomi Account ID", False),
    ("fss_environment_id", "FSS Environment ID", False),
    ("boomi_user", "Boomi API Username", False),
    ("boomi_token", "Boomi API Token", True),
]


def load_config(
    existing_state_config: Optional[dict] = None,
    interactive: bool = True,
) -> BoomiConfig:
    """Load configuration from env vars, state file, and interactive prompts.

    Priority: env vars > state file > interactive prompt.
    Credentials (user/token) are never loaded from state.
    """
    values: dict[str, str] = {}

    # Layer 1: Load non-credential fields from state file
    if existing_state_config:
        for key in (
            "boomi_account_id", "boomi_repo_id", "cloud_base_url", "fss_environment_id",
            "hub_cloud_url", "datahub_token",
        ):
            val = existing_state_config.get(key, "")
            if val:
                values[key] = val
        # hub_auth_token is stored in state as datahub_token; map to config field name
        if "datahub_token" in values:
            values["hub_auth_token"] = values.pop("datahub_token")
        # universe_ids is a dict, handle separately
        uid_val = existing_state_config.get("universe_ids")
        if uid_val and isinstance(uid_val, dict):
            values["universe_ids"] = uid_val

    # Layer 2: Override with env vars (including credentials)
    for env_var, field_name in _ENV_MAP.items():
        val = os.environ.get(env_var, "")
        if val:
            values[field_name] = val

    # Layer 3: Interactive prompts for missing values
    if interactive:
        for field_name, label, is_secret in _INTERACTIVE_FIELDS:
            if not values.get(field_name):
                if is_secret:
                    values[field_name] = click.prompt(label, hide_input=True)
                else:
                    values[field_name] = click.prompt(label)

    return BoomiConfig(**values)

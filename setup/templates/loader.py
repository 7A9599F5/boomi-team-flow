"""Template loading from repository files for Boomi Build Guide Setup Automation."""
from __future__ import annotations

import json
from pathlib import Path


def get_repo_root() -> Path:
    """Walk up from this file looking for .git or CLAUDE.md, return that directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / "CLAUDE.md").exists():
            return current
        current = current.parent
    raise FileNotFoundError(
        "Could not find repository root (no .git or CLAUDE.md found)"
    )


def load_template(relative_path: str) -> str:
    """Load a file relative to repo root, return content as string."""
    path = get_repo_root() / relative_path
    return path.read_text(encoding="utf-8")


def load_json_template(relative_path: str) -> dict:
    """Load and parse a JSON file relative to repo root."""
    content = load_template(relative_path)
    return json.loads(content)


def load_model_spec(model_name: str) -> dict:
    """Load a DataHub model spec by name (e.g., 'ComponentMapping')."""
    return load_json_template(f"datahub/models/{model_name}-model-spec.json")


def load_profile_schema(profile_name: str) -> dict:
    """Load a profile schema by name (e.g., 'executePromotion-request')."""
    return load_json_template(f"integration/profiles/{profile_name}.json")


def load_api_request(template_name: str) -> str:
    """Load an API request template by filename (e.g., 'create-branch.xml')."""
    return load_template(f"integration/api-requests/{template_name}")


def list_profiles() -> list[str]:
    """List all profile names from integration/profiles/ (strip .json extension)."""
    profiles_dir = get_repo_root() / "integration" / "profiles"
    return sorted(
        p.stem for p in profiles_dir.glob("*.json") if p.is_file()
    )


def parameterize(template_str: str, params: dict) -> str:
    """Replace {KEY} placeholders with values from params dict."""
    result = template_str
    for key, value in params.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result

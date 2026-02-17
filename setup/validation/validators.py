"""Per-step API verification for Boomi Build Guide Setup Automation.

Each validator takes API clients and state, returning (success: bool, message: str).
"""
from __future__ import annotations

from typing import Any

# Expected field counts per DataHub model
_MODEL_FIELD_COUNTS = {
    "ComponentMapping": 10,
    "DevAccountAccess": 5,
    "PromotionLog": 34,
}

# Required DataHub sources
_REQUIRED_SOURCES = ["PROMOTION_ENGINE", "ADMIN_SEEDING", "ADMIN_CONFIG"]


def validate_models_deployed(
    datahub_api: Any, state: Any
) -> tuple[bool, str]:
    """Check that 3 DataHub models are deployed with correct field counts."""
    models = ["ComponentMapping", "DevAccountAccess", "PromotionLog"]
    errors: list[str] = []

    for model_name in models:
        try:
            model = datahub_api.get_model(model_name)
        except Exception as e:
            errors.append(f"{model_name}: failed to query - {e}")
            continue

        if not model:
            errors.append(f"{model_name}: not found")
            continue

        if not isinstance(model, dict):
            errors.append(f"{model_name}: unexpected response format")
            continue

        status = model.get("status", "UNKNOWN")
        if status != "DEPLOYED":
            errors.append(f"{model_name}: status is {status}, expected DEPLOYED")

        field_count = len(model.get("fields", []))
        expected = _MODEL_FIELD_COUNTS[model_name]
        if field_count != expected:
            errors.append(
                f"{model_name}: has {field_count} fields, expected {expected}"
            )

    if errors:
        return False, "Model validation failed: " + "; ".join(errors)
    return True, "All 3 models deployed with correct field counts"


def validate_sources_exist(
    datahub_api: Any, state: Any
) -> tuple[bool, str]:
    """Check that required DataHub sources exist."""
    try:
        sources = datahub_api.list_sources()
    except Exception as e:
        return False, f"Failed to list sources: {e}"

    if isinstance(sources, dict):
        # API may wrap list in a dict with a results key
        source_list = sources.get("result", sources.get("results", []))
    elif isinstance(sources, list):
        source_list = sources
    else:
        return False, f"Unexpected sources response type: {type(sources)}"

    source_names = {s.get("name", "") for s in source_list if isinstance(s, dict)}
    missing = [s for s in _REQUIRED_SOURCES if s not in source_names]

    if missing:
        return False, f"Missing sources: {', '.join(missing)}"
    return True, "All 3 sources exist (PROMOTION_ENGINE, ADMIN_SEEDING, ADMIN_CONFIG)"


def validate_http_ops_count(
    platform_api: Any, state: Any
) -> tuple[bool, str]:
    """Count HTTP operations matching 'PROMO - HTTP Op' prefix, expect 19."""
    count = platform_api.count_components_by_prefix("PROMO - HTTP Op")
    if count != 19:
        return False, f"Found {count} HTTP operations, expected 19"
    return True, "All 19 HTTP operations found"


def validate_dh_ops_count(
    platform_api: Any, state: Any
) -> tuple[bool, str]:
    """Count DataHub operations matching 'PROMO - DH Op' prefix, expect 6."""
    count = platform_api.count_components_by_prefix("PROMO - DH Op")
    if count != 6:
        return False, f"Found {count} DataHub operations, expected 6"
    return True, "All 6 DataHub operations found"


def validate_profile_count(
    platform_api: Any, state: Any
) -> tuple[bool, str]:
    """Count profiles matching 'PROMO - Profile' prefix, expect 26."""
    count = platform_api.count_components_by_prefix("PROMO - Profile")
    if count != 26:
        return False, f"Found {count} profiles, expected 26"
    return True, "All 26 profiles found"


def validate_fss_ops_count(
    platform_api: Any, state: Any
) -> tuple[bool, str]:
    """Count FSS operations matching 'PROMO - FSS Op' prefix, expect 14."""
    count = platform_api.count_components_by_prefix("PROMO - FSS Op")
    if count != 14:
        return False, f"Found {count} FSS operations, expected 14"
    return True, "All 14 FSS operations found"


def validate_process_count(
    platform_api: Any, state: Any
) -> tuple[bool, str]:
    """Count processes matching 'PROMO - Process' prefix, expect 12."""
    count = platform_api.count_components_by_prefix("PROMO - Process")
    if count != 12:
        return False, f"Found {count} processes, expected 12"
    return True, "All 12 processes found"


def validate_flow_service_deployed(
    platform_api: Any, state: Any
) -> tuple[bool, str]:
    """Verify the Flow Service component exists via prefix count."""
    count = platform_api.count_components_by_prefix("PROMO - Flow Service")
    if count < 1:
        return False, "Flow Service component not found"
    return True, "Flow Service component found"


def validate_total_components(
    platform_api: Any, state: Any
) -> tuple[bool, str]:
    """Count all components matching 'PROMO -' prefix, expect 85."""
    count = platform_api.count_components_by_prefix("PROMO -")
    if count != 85:
        return False, f"Found {count} total PROMO components, expected 85"
    return True, "All 85 PROMO components found"

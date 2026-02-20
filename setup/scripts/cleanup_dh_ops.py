#!/usr/bin/env python3
"""Cleanup script: delete bad UPDATE/DELETE DH ops and reset steps 2.6 + 2.7.

Run from the project root:
    python -m setup.scripts.cleanup_dh_ops [--dry-run]

What it does:
  1. Deletes the 7 UPDATE/DELETE DH operations from Boomi (they have wrong
     inner XML from the old single-template approach)
  2. Clears their component IDs from state
  3. Resets step 2.6 (clears all DH template keys)
  4. Resets step 2.7 (clears the DH ops completion tracker)
  5. Leaves the 5 QUERY ops intact (their XML is correct)

After running this, re-run `python -m setup.main` — step 2.6 will:
  - Auto-find the existing Query ComponentMapping op → capture QUERY template
  - Prompt you to create one UPDATE op manually → capture UPDATE template
  - Prompt you to create one DELETE op manually → capture DELETE template
Then step 2.7 creates the remaining 9 ops from correct per-action templates.
"""
from __future__ import annotations

import sys
from pathlib import Path

from setup.config import load_config
from setup.state import SetupState

# The 7 operations that were created from the wrong (QUERY) template
BAD_OPS: list[str] = [
    "PROMO - DH Op - Update ComponentMapping",
    "PROMO - DH Op - Delete ComponentMapping",
    "PROMO - DH Op - Update DevAccountAccess",
    "PROMO - DH Op - Update PromotionLog",
    "PROMO - DH Op - Delete PromotionLog",
    "PROMO - DH Op - Update ExtensionAccessMapping",
    "PROMO - DH Op - Update ClientAccountConfig",
]

# Template keys to clear
TEMPLATE_KEYS: list[str] = [
    "dh_operation_template_xml",
    "dh_operation_template_query_xml",
    "dh_operation_template_update_xml",
    "dh_operation_template_delete_xml",
]


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN — no changes will be made ===\n")

    # Load state
    state = SetupState.load()
    print(f"State loaded from {state.path}\n")

    # Init API client
    config = load_config()
    if not config.has_credentials:
        print("ERROR: No API credentials found. Set BOOMI_USER and BOOMI_TOKEN env vars.")
        sys.exit(1)

    from setup.api.client import BoomiClient, BoomiApiError
    from setup.api.platform_api import PlatformApi

    client = BoomiClient(config.boomi_user, config.boomi_token)
    api = PlatformApi(client, config)
    base_url = f"{config.cloud_base_url}/partner/api/rest/v1/{config.boomi_account_id}"

    # --- Step 1: Delete bad ops from Boomi ---
    print("--- Step 1: Delete bad UPDATE/DELETE DH operations from Boomi ---")
    deleted = 0
    skipped = 0

    for op_name in BAD_OPS:
        comp_id = state.get_component_id("dh_operations", op_name)
        if not comp_id:
            print(f"  SKIP  {op_name} — no stored component ID")
            skipped += 1
            continue

        if dry_run:
            print(f"  WOULD DELETE  {op_name} ({comp_id})")
            deleted += 1
            continue

        try:
            url = f"{base_url}/Component/{comp_id}"
            client.delete(url)
            print(f"  DELETED  {op_name} ({comp_id})")
            deleted += 1
        except BoomiApiError as exc:
            # 404 = already gone, that's fine
            if "404" in str(exc) or "not found" in str(exc).lower():
                print(f"  GONE  {op_name} ({comp_id}) — already deleted")
                deleted += 1
            else:
                print(f"  FAILED  {op_name} ({comp_id}): {exc}")

    print(f"\n  {deleted} deleted, {skipped} skipped\n")

    # --- Step 2: Clear component IDs from state ---
    print("--- Step 2: Clear bad component IDs from state ---")
    dh_ops = state._data["component_ids"].get("dh_operations", {})
    for op_name in BAD_OPS:
        if op_name in dh_ops:
            if not dry_run:
                del dh_ops[op_name]
            print(f"  CLEARED  {op_name}")
        else:
            print(f"  SKIP  {op_name} — not in state")

    # --- Step 3: Reset step 2.6 (clear templates) ---
    print("\n--- Step 3: Clear DH discovery templates ---")
    disc = state._data.get("api_first_discovery", {})
    for key in TEMPLATE_KEYS:
        if disc.get(key):
            if not dry_run:
                disc[key] = None
            print(f"  CLEARED  {key}")
        else:
            print(f"  SKIP  {key} — already null")

    # Reset step 2.6 status
    if "2.6" in state._data["steps"]:
        if not dry_run:
            state._data["steps"]["2.6"]["status"] = "pending"
        print("  RESET  step 2.6 → pending")

    # --- Step 4: Reset step 2.7 (clear tracker + status) ---
    print("\n--- Step 4: Reset step 2.7 completion tracker ---")

    # Clear completed_items for the 7 bad ops (keep the 5 QUERY ops marked complete)
    tracker = state._data["steps"].get("2.7_create_dh_ops", {})
    completed = tracker.get("completed_items", [])
    kept = [item for item in completed if item not in BAD_OPS]
    removed = [item for item in completed if item in BAD_OPS]
    if removed:
        if not dry_run:
            tracker["completed_items"] = kept
        print(f"  REMOVED {len(removed)} items from 2.7 tracker:")
        for item in removed:
            print(f"    - {item}")
        print(f"  KEPT {len(kept)} items (QUERY ops)")
    else:
        print("  SKIP — no bad ops in tracker")

    # Reset step 2.7 status
    if "2.7" in state._data["steps"]:
        if not dry_run:
            state._data["steps"]["2.7"]["status"] = "pending"
        print("  RESET  step 2.7 → pending")

    # Reset 2.8 so verification re-runs
    if "2.8" in state._data["steps"]:
        if not dry_run:
            state._data["steps"]["2.8"]["status"] = "pending"
        print("  RESET  step 2.8 → pending")

    # --- Save ---
    if not dry_run:
        state.save()
        print(f"\nState saved to {state.path}")
    else:
        print("\n=== DRY RUN complete — no changes made ===")

    print(
        "\nNext: run `python -m setup.main` to re-discover templates "
        "and recreate the 9 missing DH operations."
    )


if __name__ == "__main__":
    main()

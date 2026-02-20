"""Phase 2b — DataHub connection and operation setup steps (2.4 through 2.8)."""
from __future__ import annotations

from setup.api.client import BoomiApiError
from setup.engine import StepStatus, StepType
from setup.state import SetupState
from setup.steps.base import BaseStep
from setup.ui import console as ui
from setup.ui.prompts import (
    collect_component_id,
    guide_and_collect,
    guide_and_wait,
    guide_wait_verify,
)


# 10 DataHub Operations — name, entity, action
DH_OPERATIONS: list[tuple[str, str, str]] = [
    ("PROMO - DH Op - Query ComponentMapping", "ComponentMapping", "QUERY"),
    ("PROMO - DH Op - Update ComponentMapping", "ComponentMapping", "UPSERT"),
    ("PROMO - DH Op - Query DevAccountAccess", "DevAccountAccess", "QUERY"),
    ("PROMO - DH Op - Query PromotionLog", "PromotionLog", "QUERY"),
    ("PROMO - DH Op - Update PromotionLog", "PromotionLog", "UPSERT"),
    ("PROMO - DH Op - Delete PromotionLog", "PromotionLog", "DELETE"),
    # Phase 7 — Extension Editor
    ("PROMO - DH Op - Query ExtensionAccessMapping", "ExtensionAccessMapping", "QUERY"),
    ("PROMO - DH Op - Update ExtensionAccessMapping", "ExtensionAccessMapping", "UPSERT"),
    ("PROMO - DH Op - Query ClientAccountConfig", "ClientAccountConfig", "QUERY"),
    ("PROMO - DH Op - Update ClientAccountConfig", "ClientAccountConfig", "UPSERT"),
]


class GetDhToken(BaseStep):
    """Step 2.4 — Guide user to obtain a DataHub authentication token."""

    @property
    def step_id(self) -> str:
        return "2.4"

    @property
    def name(self) -> str:
        return "Obtain DataHub Auth Token"

    @property
    def step_type(self) -> StepType:
        return StepType.MANUAL

    @property
    def depends_on(self) -> list[str]:
        return ["1.0"]

    def _collect_token(self) -> str:
        """Prompt user for the DataHub Hub Authentication Token."""
        return guide_and_collect(
            "Obtain the DataHub Hub Authentication Token:\n\n"
            "1. Navigate to Services > DataHub > Repositories\n"
            "2. Select the 'PromotionHub' repository\n"
            "3. Click Configure > Authentication Token\n"
            "4. Copy the 'Token' value (click Generate if none exists)\n\n"
            "Auth format: Basic base64({AccountID}:{Token})\n"
            "The Account ID is already in your config; only the token is needed.",
            "DataHub Token",
        )

    def _apply_token(self, state: SetupState, token: str) -> None:
        """Store token in both state and in-memory config."""
        # Strip whitespace — copy-paste from browser can add trailing newlines
        token = token.strip()
        state.update_config({"datahub_token": token})
        self.config.hub_auth_token = token
        # Invalidate cached repo client so it rebuilds with new credentials
        self.datahub_api.reset_repo_client()

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would guide user to obtain DataHub Hub Authentication Token")
            return StepStatus.COMPLETED

        existing_token = state.config.get("datahub_token", "")

        if existing_token:
            # Sync in-memory config with state value
            self.config.hub_auth_token = existing_token.strip()

            # Print diagnostic context
            acct = self.config.boomi_account_id
            tok_preview = existing_token[:8] + "..." if len(existing_token) > 8 else "***"
            ui.print_info(
                f"DataHub auth: accountId={acct[:8]}..., "
                f"token={tok_preview} ({len(existing_token)} chars)"
            )

            # Verify against Repository API if a universe is available for probing
            if self.datahub_api.verify_repo_auth():
                ui.print_success("DataHub token accepted (or deferred to first record operation)")
                return StepStatus.COMPLETED
            else:
                ui.print_warning(
                    "Existing DataHub token failed auth check — "
                    "token may have expired or been regenerated"
                )
                token = self._collect_token()
                self._apply_token(state, token)
        else:
            token = self._collect_token()
            self._apply_token(state, token)

        # Print what we stored
        acct = self.config.boomi_account_id
        stored_tok = self.config.hub_auth_token
        tok_preview = stored_tok[:8] + "..." if len(stored_tok) > 8 else "***"
        ui.print_info(
            f"DataHub auth stored: accountId={acct[:8]}..., "
            f"token={tok_preview} ({len(stored_tok)} chars)"
        )

        # Verify the new token against the Repository API
        if self.datahub_api.verify_repo_auth():
            ui.print_success("DataHub token verified (or deferred to first record operation)")
        else:
            ui.print_warning(
                "Token auth check failed — verify the token is from:\n"
                "  Services > DataHub > Repositories > PromotionHub > Configure > Authentication Token\n"
                "  (NOT the Platform API token from Settings > Account Information)"
            )

        return StepStatus.COMPLETED


class CreateDhConn(BaseStep):
    """Step 2.5 — Create the DataHub Connection component."""

    @property
    def step_id(self) -> str:
        return "2.5"

    @property
    def name(self) -> str:
        return "Create DataHub Connection"

    @property
    def step_type(self) -> StepType:
        return StepType.SEMI

    @property
    def depends_on(self) -> list[str]:
        return ["2.4"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        existing = state.get_component_id("connections", "datahub")
        if existing:
            ui.print_success(f"DataHub Connection already exists (ID: {existing})")
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info("Would create DataHub Connection component via Platform API")
            return StepStatus.COMPLETED

        account_id = state.config.get("boomi_account_id", "")
        token = state.config.get("datahub_token", "")
        cloud_name = state.config.get("hub_cloud_name", "")
        connections_folder_id = state.get_component_id("folders", "Connections") or ""

        if not account_id:
            ui.print_error("Account ID not found in config")
            return StepStatus.FAILED

        if not token:
            ui.print_error("DataHub token not found in state — run step 2.4 first")
            return StepStatus.FAILED

        if not cloud_name:
            # Backfill: fetch hub cloud name directly from API instead of hard-failing
            try:
                clouds = self.datahub_api.get_hub_clouds()
                if len(clouds) == 1:
                    cloud_name = clouds[0]["name"]
                elif clouds:
                    from setup.ui.prompts import prompt_choice
                    idx = prompt_choice(
                        "Select the Hub Cloud used for the PromotionHub repository:",
                        [f"{c['name']} ({c['cloudId']})" for c in clouds],
                    )
                    cloud_name = clouds[idx]["name"]
                if cloud_name:
                    state.update_config({"hub_cloud_name": cloud_name})
                    ui.print_info(f"Hub cloud name resolved: {cloud_name}")
                else:
                    ui.print_error("No Hub Clouds found — check DataHub provisioning")
                    return StepStatus.FAILED
            except BoomiApiError as exc:
                ui.print_error(f"Could not fetch Hub Clouds to resolve cloud name: {exc}")
                return StepStatus.FAILED

        # DataHub (MDM) connector uses GenericConnectionConfig with field elements.
        # subType is the official Boomi DataHub connector identifier.
        component_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<bns:Component xmlns:bns="http://api.platform.boomi.com/"\n'
            '              name="PROMO - DataHub Connection"\n'
            '              type="connector-settings"\n'
            '              subType="officialboomi-X3979C-boomid-prod"\n'
            f'              folderId="{connections_folder_id}">\n'
            "  <bns:encryptedValues/>\n"
            "  <bns:object>\n"
            '    <GenericConnectionConfig xmlns="">\n'
            f'      <field id="cloudName" type="string" value="{cloud_name}"/>\n'
            '      <field id="customUrl" type="string" value=""/>\n'
            f'      <field id="accountId" type="string" value="{account_id}"/>\n'
            f'      <field id="token" type="password" value="{token}"/>\n'
            "    </GenericConnectionConfig>\n"
            "  </bns:object>\n"
            "</bns:Component>"
        )

        try:
            result = self.platform_api.create_component(component_xml)
            conn_id = _extract_id(result)
            if not conn_id:
                ui.print_error("No connection ID returned from API")
                return StepStatus.FAILED
            state.store_component_id("connections", "datahub", conn_id)
            ui.print_success(f"Created DataHub Connection (ID: {conn_id})")
            return StepStatus.COMPLETED
        except BoomiApiError as exc:
            ui.print_error(f"Failed to create DataHub Connection: {exc}")
            return StepStatus.FAILED


class DiscoverDhTemplate(BaseStep):
    """Step 2.6 — Discover DataHub Operation template via API-first pattern."""

    @property
    def step_id(self) -> str:
        return "2.6"

    @property
    def name(self) -> str:
        return "Discover DataHub Operation Template"

    @property
    def step_type(self) -> StepType:
        return StepType.MANUAL

    @property
    def depends_on(self) -> list[str]:
        return ["2.5"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        existing = state.api_first_discovery.get("dh_operation_template_xml")
        if existing:
            ui.print_success("DataHub operation template already discovered")
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info("Would guide user to create a DataHub operation and export its XML")
            return StepStatus.COMPLETED

        op_name = "PROMO - DH Op - Query ComponentMapping"

        guide_and_wait(
            "Create ONE DataHub Operation manually in Boomi AtomSphere:\n\n"
            "1. Go to Build > New Component > Connector > MDM (DataHub)\n"
            f"2. Name it: {op_name}\n"
            "3. Set Connection: select the DataHub Connection from step 2.5\n"
            "4. Configure: Entity=ComponentMapping, Action=QUERY\n"
            "5. Save the component",
            build_guide_ref="05-connections-operations.md",
        )

        # Auto-discover by name first, fall back to manual ID entry
        comp_id = self.platform_api.find_component_id_by_name(op_name)
        if comp_id:
            ui.print_success(f"Found '{op_name}' → {comp_id}")
        else:
            ui.print_info("Could not find component by name — enter ID manually")
            comp_id = collect_component_id("DataHub Operation component ID")

            # Validate the pasted ID matches the expected component
            try:
                import re as _re
                comp_xml = self.platform_api.get_component(comp_id)
                comp_str = comp_xml if isinstance(comp_xml, str) else str(comp_xml)
                name_match = _re.search(r'name="([^"]*)"', comp_str)
                actual_name = name_match.group(1) if name_match else ""
                if actual_name and actual_name != op_name:
                    ui.print_error(
                        f"Component '{comp_id}' is named '{actual_name}', "
                        f"expected '{op_name}'. Please check the ID."
                    )
                    return StepStatus.FAILED
            except BoomiApiError:
                pass  # proceed — GET failure will be caught below

        try:
            template_xml = self.platform_api.get_component(comp_id)
            if not template_xml:
                ui.print_error("Empty response when fetching DataHub operation component")
                return StepStatus.FAILED

            template_str = template_xml if isinstance(template_xml, str) else str(template_xml)
            state.set_discovery_template("dh_operation_template_xml", template_str)
            ui.print_success("DataHub operation template captured and stored")

            state.store_component_id("dh_operations", op_name, comp_id)
            state.mark_step_item_complete("2.7_create_dh_ops", op_name)

            return StepStatus.COMPLETED
        except BoomiApiError as exc:
            ui.print_error(f"Failed to export DataHub operation template: {exc}")
            return StepStatus.FAILED


class CreateDhOps(BaseStep):
    """Step 2.7 — Batch-create the remaining DataHub Operations from template."""

    @property
    def step_id(self) -> str:
        return "2.7"

    @property
    def name(self) -> str:
        return "Create DataHub Operations"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    @property
    def depends_on(self) -> list[str]:
        return ["2.6"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        all_op_names = [op[0] for op in DH_OPERATIONS]
        remaining = state.get_remaining_items("2.7_create_dh_ops", all_op_names)

        if not remaining:
            ui.print_success(f"All {len(DH_OPERATIONS)} DataHub operations already created")
            return StepStatus.COMPLETED

        template_xml = state.api_first_discovery.get("dh_operation_template_xml")
        if not template_xml:
            ui.print_error("DataHub operation template not found — run step 2.6 first")
            return StepStatus.FAILED

        if dry_run:
            ui.print_info(f"Would create {len(remaining)} DataHub operations from template")
            return StepStatus.COMPLETED

        ops_folder_id = state.get_component_id("folders", "Operations") or ""
        total = len(remaining)

        for idx, op_name in enumerate(remaining, 1):
            op_def = next((o for o in DH_OPERATIONS if o[0] == op_name), None)
            if not op_def:
                ui.print_error(f"Unknown operation: {op_name}")
                return StepStatus.FAILED

            _, entity, action = op_def
            ui.print_progress(idx, total, op_name)

            parameterized = _parameterize_dh_template(
                template_xml, op_name, entity, action, ops_folder_id
            )

            try:
                result = self.platform_api.create_component(parameterized)
                comp_id = _extract_id(result)
                if not comp_id:
                    ui.print_error(f"No component ID returned for '{op_name}'")
                    return StepStatus.FAILED
                state.store_component_id("dh_operations", op_name, comp_id)
                state.mark_step_item_complete("2.7_create_dh_ops", op_name)
            except BoomiApiError as exc:
                ui.print_error(f"Failed to create '{op_name}': {exc}")
                return StepStatus.FAILED

        ui.print_success(f"Created {total} DataHub operations")
        return StepStatus.COMPLETED


class VerifyPhase2(BaseStep):
    """Step 2.8 — Validate Phase 2 component counts."""

    @property
    def step_id(self) -> str:
        return "2.8"

    @property
    def name(self) -> str:
        return "Verify Phase 2 Components"

    @property
    def step_type(self) -> StepType:
        return StepType.VALIDATE

    @property
    def depends_on(self) -> list[str]:
        return ["2.3", "2.7"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would verify: 28 HTTP ops, 10 DH ops, 2 connections")
            return StepStatus.COMPLETED

        checks = [
            ("PROMO - HTTP Op", 28, "HTTP operations"),
            ("PROMO - DH Op", 10, "DataHub operations"),
        ]

        all_passed = True
        for prefix, expected, label in checks:
            try:
                actual = self.platform_api.count_components_by_prefix(prefix)
                if actual >= expected:
                    ui.print_success(f"{label}: {actual}/{expected}")
                elif prefix == "PROMO - DH Op":
                    # Diagnose + auto-repair missing DH ops
                    repaired = self._diagnose_and_repair_dh_ops(state)
                    if repaired:
                        actual = self.platform_api.count_components_by_prefix(prefix)
                    if actual >= expected:
                        ui.print_success(f"{label}: {actual}/{expected} (repaired)")
                    else:
                        ui.print_error(f"{label}: {actual}/{expected} (missing {expected - actual})")
                        all_passed = False
                else:
                    ui.print_error(f"{label}: {actual}/{expected} (missing {expected - actual})")
                    all_passed = False
            except BoomiApiError as exc:
                ui.print_error(f"Failed to count {label}: {exc}")
                all_passed = False

        # Verify connections from state
        http_conn = state.get_component_id("connections", "http_client")
        dh_conn = state.get_component_id("connections", "datahub")
        conn_count = sum(1 for c in [http_conn, dh_conn] if c)
        if conn_count == 2:
            ui.print_success(f"Connections: {conn_count}/2")
        else:
            ui.print_error(f"Connections: {conn_count}/2")
            all_passed = False

        if all_passed:
            ui.print_success("Phase 2 verification passed")
            return StepStatus.COMPLETED
        else:
            ui.print_error("Phase 2 verification failed — check counts above")
            return StepStatus.FAILED

    def _diagnose_and_repair_dh_ops(self, state: SetupState) -> bool:
        """Check each DH op by stored ID, report actual name, repair if needed."""
        import re as _re

        template_xml = state.api_first_discovery.get("dh_operation_template_xml")
        ops_folder_id = state.get_component_id("folders", "Operations") or ""
        repaired = 0

        for op_name, entity, action in DH_OPERATIONS:
            stored_id = state.get_component_id("dh_operations", op_name)
            if not stored_id:
                ui.print_error(f"  {op_name}: NO stored ID")
                if template_xml:
                    repaired += self._try_create_dh_op(
                        state, op_name, entity, action, template_xml, ops_folder_id
                    )
                continue

            # Fetch component and check its actual name
            try:
                comp_xml = self.platform_api.get_component(stored_id)
                comp_str = comp_xml if isinstance(comp_xml, str) else str(comp_xml)
                name_match = _re.search(r'name="([^"]*)"', comp_str)
                actual_name = name_match.group(1) if name_match else "(unknown)"
                if actual_name == op_name:
                    ui.print_success(f"  {op_name}: OK ({stored_id})")
                else:
                    ui.print_error(
                        f"  {op_name}: NAME MISMATCH — stored ID {stored_id} "
                        f"has name '{actual_name}'"
                    )
                    # Re-create with correct name
                    if template_xml:
                        repaired += self._try_create_dh_op(
                            state, op_name, entity, action, template_xml, ops_folder_id
                        )
            except BoomiApiError as exc:
                ui.print_error(f"  {op_name}: GET failed ({stored_id}) — {exc}")
                if template_xml:
                    repaired += self._try_create_dh_op(
                        state, op_name, entity, action, template_xml, ops_folder_id
                    )

        return repaired > 0

    def _try_create_dh_op(
        self,
        state: SetupState,
        op_name: str,
        entity: str,
        action: str,
        template_xml: str,
        folder_id: str,
    ) -> int:
        """Attempt to create a single DH op from template. Returns 1 on success, 0 on failure."""
        ui.print_info(f"  Creating '{op_name}'...")
        parameterized = _parameterize_dh_template(
            template_xml, op_name, entity, action, folder_id
        )
        try:
            result = self.platform_api.create_component(parameterized)
            comp_id = _extract_id(result)
            if comp_id:
                state.store_component_id("dh_operations", op_name, comp_id)
                state.mark_step_item_complete("2.7_create_dh_ops", op_name)
                ui.print_success(f"  Created '{op_name}' → {comp_id}")
                return 1
        except BoomiApiError as exc:
            ui.print_error(f"  Failed to create '{op_name}': {exc}")
        return 0


# -- Shared utilities --


def _extract_id(result: dict | str) -> str:
    """Extract component ID from API response (XML or dict)."""
    from setup.api.platform_api import PlatformApi
    return PlatformApi.parse_component_id(result)


def _parameterize_dh_template(
    template_xml: str,
    name: str,
    entity: str,
    action: str,
    folder_id: str,
) -> str:
    """Replace name, entity, action, and folder in the DataHub operation template XML."""
    import re

    xml = template_xml

    # Replace component name
    xml = re.sub(r'name="[^"]*"', f'name="{name}"', xml, count=1)

    # Replace folder ID
    xml = re.sub(r'folderId="[^"]*"', f'folderId="{folder_id}"', xml, count=1)

    # Remove existing component ID so the API generates a new one
    xml = re.sub(r'\s+componentId="[^"]*"', "", xml)
    xml = re.sub(r'\s+@id="[^"]*"', "", xml)

    # Replace entity/model name
    xml = re.sub(r"<Entity>[^<]*</Entity>", f"<Entity>{entity}</Entity>", xml)
    xml = re.sub(r"<ObjectName>[^<]*</ObjectName>", f"<ObjectName>{entity}</ObjectName>", xml)

    # Replace action
    xml = re.sub(r"<Action>[^<]*</Action>", f"<Action>{action}</Action>", xml)

    return xml

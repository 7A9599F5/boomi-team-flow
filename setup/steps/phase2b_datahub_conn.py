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
    ("PROMO - DH Op - Upsert ComponentMapping", "ComponentMapping", "UPSERT"),
    ("PROMO - DH Op - Query DevAccountAccess", "DevAccountAccess", "QUERY"),
    ("PROMO - DH Op - Query PromotionLog", "PromotionLog", "QUERY"),
    ("PROMO - DH Op - Upsert PromotionLog", "PromotionLog", "UPSERT"),
    ("PROMO - DH Op - Delete PromotionLog", "PromotionLog", "DELETE"),
    # Phase 7 — Extension Editor
    ("PROMO - DH Op - Query ExtensionAccessMapping", "ExtensionAccessMapping", "QUERY"),
    ("PROMO - DH Op - Upsert ExtensionAccessMapping", "ExtensionAccessMapping", "UPSERT"),
    ("PROMO - DH Op - Query ClientAccountConfig", "ClientAccountConfig", "QUERY"),
    ("PROMO - DH Op - Upsert ClientAccountConfig", "ClientAccountConfig", "UPSERT"),
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

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        existing_token = state.config.get("datahub_token", "")
        if existing_token:
            ui.print_success("DataHub token already configured")
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info("Would guide user to obtain DataHub auth token")
            return StepStatus.COMPLETED

        token = guide_and_collect(
            "Obtain a DataHub authentication token:\n\n"
            "1. Navigate to Services > DataHub > Repositories\n"
            "2. Select the 'PromotionHub' repository\n"
            "3. Click Configure > Authentication Token\n"
            "4. Generate or copy the existing token\n\n"
            "This token is used by the DataHub Connection for API calls.",
            "DataHub Token",
        )

        # Verify by attempting a list-sources call
        try:
            self.datahub_api.list_sources()
            ui.print_success("DataHub token verified successfully")
        except BoomiApiError:
            ui.print_warning(
                "Could not verify token via API (may still be valid for connector use)"
            )

        state.update_config({"datahub_token": token})
        ui.print_success("DataHub token stored")
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

        repo_id = state.config.get("boomi_repo_id", "")
        token = state.config.get("datahub_token", "")
        connections_folder_id = state.get_component_id("folders", "Connections") or "0"

        if not repo_id:
            ui.print_error("Repository ID not found in state — run step 1.0 first")
            return StepStatus.FAILED

        if not token:
            ui.print_error("DataHub token not found in state — run step 2.4 first")
            return StepStatus.FAILED

        component_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<bns:Component xmlns:bns="http://api.platform.boomi.com/" '
            f'name="PROMO - DataHub Connection" type="connector-settings" '
            f'subType="mdm" folderId="{connections_folder_id}">\n'
            "  <bns:object>\n"
            "    <ConnectorSettings>\n"
            f"      <RepositoryId>{repo_id}</RepositoryId>\n"
            f"      <AuthToken>{token}</AuthToken>\n"
            "    </ConnectorSettings>\n"
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

        guide_and_wait(
            "Create ONE DataHub Operation manually in Boomi AtomSphere:\n\n"
            "1. Go to Build > New Component > Connector > MDM (DataHub)\n"
            "2. Name it: PROMO - DH Op - Query ComponentMapping\n"
            "3. Set Connection: select the DataHub Connection from step 2.5\n"
            "4. Configure: Entity=ComponentMapping, Action=QUERY\n"
            "5. Save the component\n"
            "6. Copy the component ID from the URL bar",
            build_guide_ref="05-connections-operations.md",
        )

        comp_id = collect_component_id("DataHub Operation component ID")

        try:
            template_xml = self.platform_api.get_component(comp_id)
            if not template_xml:
                ui.print_error("Empty response when fetching DataHub operation component")
                return StepStatus.FAILED

            template_str = template_xml if isinstance(template_xml, str) else str(template_xml)
            state.set_discovery_template("dh_operation_template_xml", template_str)
            ui.print_success("DataHub operation template captured and stored")

            # Store this first operation
            op_name = "PROMO - DH Op - Query ComponentMapping"
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

        ops_folder_id = state.get_component_id("folders", "Operations") or "0"
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


# -- Shared utilities --


def _extract_id(result: dict | str) -> str:
    """Extract component ID from API response."""
    if isinstance(result, dict):
        return result.get("@id", "") or result.get("id", "")
    return ""


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

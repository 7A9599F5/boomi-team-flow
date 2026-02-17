"""Phase 2a — HTTP connection and operation setup steps (2.0 through 2.3)."""
from __future__ import annotations

from setup.api.client import BoomiApiError
from setup.engine import StepStatus, StepType
from setup.state import SetupState
from setup.steps.base import BaseStep
from setup.ui import console as ui
from setup.ui.prompts import collect_component_id, guide_and_collect, guide_and_wait


# 27 HTTP Client Operations — name, method, URL path
HTTP_OPERATIONS: list[tuple[str, str, str]] = [
    ("PROMO - HTTP Op - GET Component", "GET", "/partner/api/rest/v1/{1}/Component/{2}"),
    ("PROMO - HTTP Op - POST Component Create", "POST", "/partner/api/rest/v1/{1}/Component~{2}"),
    ("PROMO - HTTP Op - POST Component Update", "POST", "/partner/api/rest/v1/{1}/Component/{2}~{3}"),
    ("PROMO - HTTP Op - GET ComponentReference", "GET", "/partner/api/rest/v1/{1}/ComponentReference/{2}"),
    ("PROMO - HTTP Op - GET ComponentMetadata", "GET", "/partner/api/rest/v1/{1}/ComponentMetadata/{2}"),
    ("PROMO - HTTP Op - QUERY PackagedComponent", "POST", "/partner/api/rest/v1/{1}/PackagedComponent/query"),
    ("PROMO - HTTP Op - POST PackagedComponent", "POST", "/partner/api/rest/v1/{1}/PackagedComponent"),
    ("PROMO - HTTP Op - POST DeployedPackage", "POST", "/partner/api/rest/v1/{1}/DeployedPackage"),
    ("PROMO - HTTP Op - POST IntegrationPack", "POST", "/partner/api/rest/v1/{1}/IntegrationPack"),
    ("PROMO - HTTP Op - POST Branch", "POST", "/partner/api/rest/v1/{1}/Branch"),
    ("PROMO - HTTP Op - QUERY Branch", "POST", "/partner/api/rest/v1/{1}/Branch/query"),
    ("PROMO - HTTP Op - POST MergeRequest", "POST", "/partner/api/rest/v1/{1}/MergeRequest"),
    ("PROMO - HTTP Op - POST MergeRequest Execute", "POST", "/partner/api/rest/v1/{1}/MergeRequest/execute/{2}"),
    ("PROMO - HTTP Op - GET Branch", "GET", "/partner/api/rest/v1/{1}/Branch/{2}"),
    ("PROMO - HTTP Op - DELETE Branch", "DELETE", "/partner/api/rest/v1/{1}/Branch/{2}"),
    ("PROMO - HTTP Op - QUERY IntegrationPack", "POST", "/partner/api/rest/v1/{1}/IntegrationPack/query"),
    ("PROMO - HTTP Op - POST Add To IntegrationPack", "POST", "/partner/api/rest/v1/{1}/IntegrationPack/{2}/PackagedComponent/{3}"),
    ("PROMO - HTTP Op - POST ReleaseIntegrationPack", "POST", "/partner/api/rest/v1/{1}/ReleaseIntegrationPack"),
    ("PROMO - HTTP Op - GET MergeRequest", "GET", "/partner/api/rest/v1/{1}/MergeRequest/{2}"),
    # Phase 7 — Extension Editor
    ("PROMO - HTTP Op - QUERY Account", "POST", "/partner/api/rest/v1/{1}/Account/query"),
    ("PROMO - HTTP Op - QUERY Environment", "POST", "/partner/api/rest/v1/{1}/Environment/query"),
    ("PROMO - HTTP Op - GET EnvironmentExtensions", "GET", "/partner/api/rest/v1/{1}/EnvironmentExtensions/{2}"),
    ("PROMO - HTTP Op - UPDATE EnvironmentExtensions", "POST", "/partner/api/rest/v1/{1}/EnvironmentExtensions/{2}/update"),
    ("PROMO - HTTP Op - QUERY EnvironmentMapExtensionsSummary", "POST", "/partner/api/rest/v1/{1}/EnvironmentMapExtensions/{2}/query"),
    ("PROMO - HTTP Op - GET EnvironmentMapExtension", "GET", "/partner/api/rest/v1/{1}/EnvironmentMapExtension/{2}"),
    ("PROMO - HTTP Op - UPDATE EnvironmentMapExtension", "POST", "/partner/api/rest/v1/{1}/EnvironmentMapExtension/{2}/update"),
    ("PROMO - HTTP Op - QUERY ComponentReference", "POST", "/partner/api/rest/v1/{1}/ComponentReference/query"),
]


class CreateFolders(BaseStep):
    """Step 2.0 — Create the /Promoted/ folder tree in AtomSphere."""

    FOLDERS = [
        ("Promoted", "0"),          # root
        ("Profiles", "Promoted"),   # sub-folder under Promoted
        ("Connections", "Promoted"),
        ("Operations", "Promoted"),
    ]

    @property
    def step_id(self) -> str:
        return "2.0"

    @property
    def name(self) -> str:
        return "Create Folder Structure"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        remaining = state.get_remaining_items(
            self.step_id, [f[0] for f in self.FOLDERS]
        )
        if not remaining:
            ui.print_success("All folders already created")
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info(f"Would create {len(remaining)} folders: {', '.join(remaining)}")
            return StepStatus.COMPLETED

        promoted_folder_id: str | None = state.get_component_id("folders", "Promoted")

        for folder_name, parent_ref in self.FOLDERS:
            if folder_name not in remaining:
                continue

            # Resolve parent ID
            if parent_ref == "0":
                parent_id = "0"
            else:
                parent_id = state.get_component_id("folders", parent_ref) or promoted_folder_id
                if not parent_id:
                    ui.print_error(
                        f"Cannot create '{folder_name}' — parent '{parent_ref}' not yet created"
                    )
                    return StepStatus.FAILED

            try:
                result = self.platform_api.create_folder(folder_name, parent_id)
                folder_id = result["id"] if isinstance(result, dict) else ""
                if not folder_id:
                    ui.print_error(f"No folder ID returned for '{folder_name}'")
                    return StepStatus.FAILED
                state.store_component_id("folders", folder_name, folder_id)
                state.mark_step_item_complete(self.step_id, folder_name)

                # Cache Promoted ID for sub-folders
                if folder_name == "Promoted":
                    promoted_folder_id = folder_id

                ui.print_success(f"Created folder '{folder_name}' (ID: {folder_id})")
            except BoomiApiError as exc:
                ui.print_error(f"Failed to create folder '{folder_name}': {exc}")
                return StepStatus.FAILED

        return StepStatus.COMPLETED


class CreateHttpConn(BaseStep):
    """Step 2.1 — Create the HTTP Client Connection for Boomi Platform API."""

    @property
    def step_id(self) -> str:
        return "2.1"

    @property
    def name(self) -> str:
        return "Create HTTP Client Connection"

    @property
    def step_type(self) -> StepType:
        return StepType.SEMI

    @property
    def depends_on(self) -> list[str]:
        return ["2.0"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        existing = state.get_component_id("connections", "http_client")
        if existing:
            ui.print_success(f"HTTP Client Connection already exists (ID: {existing})")
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info("Would guide user through HTTP Client Connection creation")
            return StepStatus.COMPLETED

        # Collect credentials
        api_user = guide_and_collect(
            "Enter the Boomi API username for the HTTP Client Connection.\n"
            "This is the user that will authenticate Platform API calls.\n"
            "Format: BOOMI_TOKEN.<user>",
            "API Username",
        )
        api_token = guide_and_collect(
            "Enter the Boomi API token for the HTTP Client Connection.",
            "API Token",
        )

        connections_folder_id = state.get_component_id("folders", "Connections") or "0"

        # Build connection component XML
        component_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<bns:Component xmlns:bns="http://api.platform.boomi.com/" '
            f'name="PROMO - HTTP Client Connection" type="connector-settings" '
            f'subType="http" folderId="{connections_folder_id}">\n'
            "  <bns:object>\n"
            "    <ConnectorSettings>\n"
            f"      <Url>https://api.boomi.com</Url>\n"
            "      <AuthType>BASIC</AuthType>\n"
            f"      <User>{api_user}</User>\n"
            f"      <Password>{api_token}</Password>\n"
            "    </ConnectorSettings>\n"
            "  </bns:object>\n"
            "</bns:Component>"
        )

        try:
            result = self.platform_api.create_component(component_xml)
            conn_id = result["@id"] if isinstance(result, dict) else ""
            if not conn_id:
                # Try alternate key
                conn_id = result.get("id", "") if isinstance(result, dict) else ""
            if not conn_id:
                ui.print_error("No connection ID returned from API")
                return StepStatus.FAILED
            state.store_component_id("connections", "http_client", conn_id)
            ui.print_success(f"Created HTTP Client Connection (ID: {conn_id})")
            return StepStatus.COMPLETED
        except BoomiApiError as exc:
            ui.print_error(f"Failed to create HTTP Client Connection: {exc}")
            return StepStatus.FAILED


class DiscoverHttpTemplate(BaseStep):
    """Step 2.2 — Discover HTTP Client Operation template via API-first pattern."""

    @property
    def step_id(self) -> str:
        return "2.2"

    @property
    def name(self) -> str:
        return "Discover HTTP Operation Template"

    @property
    def step_type(self) -> StepType:
        return StepType.MANUAL

    @property
    def depends_on(self) -> list[str]:
        return ["2.1"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        existing = state.api_first_discovery.get("http_operation_template_xml")
        if existing:
            ui.print_success("HTTP operation template already discovered")
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info("Would guide user to create an HTTP operation and export its XML")
            return StepStatus.COMPLETED

        guide_and_wait(
            "Create ONE HTTP Client Operation manually in Boomi AtomSphere:\n\n"
            "1. Go to Build > New Component > Connector > HTTP Client\n"
            "2. Name it: PROMO - HTTP Op - GET Component\n"
            "3. Set Connection: select the HTTP Client Connection from step 2.1\n"
            "4. Configure: Method=GET, URL=/partner/api/rest/v1/{1}/Component/{2}\n"
            "5. Save the component\n"
            "6. Copy the component ID from the URL bar",
            build_guide_ref="05-connections-operations.md",
        )

        comp_id = collect_component_id("HTTP Operation component ID")

        try:
            template_xml = self.platform_api.get_component(comp_id)
            if not template_xml:
                ui.print_error("Empty response when fetching HTTP operation component")
                return StepStatus.FAILED

            template_str = template_xml if isinstance(template_xml, str) else str(template_xml)
            state.set_discovery_template("http_operation_template_xml", template_str)
            ui.print_success("HTTP operation template captured and stored")

            # Also store this first operation
            op_name = "PROMO - HTTP Op - GET Component"
            state.store_component_id("http_operations", op_name, comp_id)
            state.mark_step_item_complete("2.3_create_http_ops", op_name)

            return StepStatus.COMPLETED
        except BoomiApiError as exc:
            ui.print_error(f"Failed to export HTTP operation template: {exc}")
            return StepStatus.FAILED


class CreateHttpOps(BaseStep):
    """Step 2.3 — Batch-create the remaining 18 HTTP Client Operations from template."""

    @property
    def step_id(self) -> str:
        return "2.3"

    @property
    def name(self) -> str:
        return "Create HTTP Client Operations"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    @property
    def depends_on(self) -> list[str]:
        return ["2.2"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        all_op_names = [op[0] for op in HTTP_OPERATIONS]
        remaining = state.get_remaining_items("2.3_create_http_ops", all_op_names)

        if not remaining:
            ui.print_success(f"All {len(HTTP_OPERATIONS)} HTTP operations already created")
            return StepStatus.COMPLETED

        template_xml = state.api_first_discovery.get("http_operation_template_xml")
        if not template_xml:
            ui.print_error("HTTP operation template not found — run step 2.2 first")
            return StepStatus.FAILED

        if dry_run:
            ui.print_info(f"Would create {len(remaining)} HTTP operations from template")
            return StepStatus.COMPLETED

        ops_folder_id = state.get_component_id("folders", "Operations") or "0"
        total = len(remaining)

        for idx, op_name in enumerate(remaining, 1):
            # Find the matching operation definition
            op_def = next((o for o in HTTP_OPERATIONS if o[0] == op_name), None)
            if not op_def:
                ui.print_error(f"Unknown operation: {op_name}")
                return StepStatus.FAILED

            _, method, url_path = op_def
            ui.print_progress(idx, total, op_name)

            parameterized = self._parameterize_template(
                template_xml, op_name, method, url_path, ops_folder_id
            )

            try:
                result = self.platform_api.create_component(parameterized)
                comp_id = self._extract_id(result)
                if not comp_id:
                    ui.print_error(f"No component ID returned for '{op_name}'")
                    return StepStatus.FAILED
                state.store_component_id("http_operations", op_name, comp_id)
                state.mark_step_item_complete("2.3_create_http_ops", op_name)
            except BoomiApiError as exc:
                ui.print_error(f"Failed to create '{op_name}': {exc}")
                return StepStatus.FAILED

        ui.print_success(f"Created {total} HTTP operations")
        return StepStatus.COMPLETED

    @staticmethod
    def _parameterize_template(
        template_xml: str,
        name: str,
        method: str,
        url_path: str,
        folder_id: str,
    ) -> str:
        """Replace name, method, URL, and folder in the template XML."""
        import re

        xml = template_xml

        # Replace component name
        xml = re.sub(r'name="[^"]*"', f'name="{name}"', xml, count=1)

        # Replace folder ID
        xml = re.sub(r'folderId="[^"]*"', f'folderId="{folder_id}"', xml, count=1)

        # Remove the existing component ID so the API generates a new one
        xml = re.sub(r'\s+componentId="[^"]*"', "", xml)
        xml = re.sub(r'\s+@id="[^"]*"', "", xml)

        # Replace HTTP method
        xml = re.sub(r"<Method>[^<]*</Method>", f"<Method>{method}</Method>", xml)

        # Replace URL path
        xml = re.sub(r"<Url>[^<]*</Url>", f"<Url>{url_path}</Url>", xml)
        xml = re.sub(
            r"<ResourcePath>[^<]*</ResourcePath>",
            f"<ResourcePath>{url_path}</ResourcePath>",
            xml,
        )

        return xml

    @staticmethod
    def _extract_id(result: dict | str) -> str:
        """Extract component ID from API response."""
        if isinstance(result, dict):
            return result.get("@id", "") or result.get("id", "")
        return ""

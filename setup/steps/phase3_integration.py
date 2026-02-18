"""Phase 3 build steps: Profile discovery, profile creation, FSS ops, processes."""
from __future__ import annotations

from setup.engine import StepStatus, StepType
from setup.generators.profile_xml import generate_profile_xml
from setup.generators.script_xml import SCRIPT_NAME_MAP, generate_script_xml, script_stem_to_component_name
from setup.state import SetupState
from setup.steps.base import BaseStep
from setup.templates.loader import list_profiles, load_template
from setup.ui import console as ui
from setup.ui.prompts import collect_component_id, guide_and_wait, guide_and_confirm


# ---------------------------------------------------------------------------
# Profile name mapping: file stem -> Boomi profile component name
# ---------------------------------------------------------------------------

def _profile_display_name(stem: str) -> str:
    """Convert profile file stem like 'getDevAccounts-request' to
    'PROMO - Profile - GetDevAccountsRequest'.
    """
    action, suffix = stem.rsplit("-", 1)
    # Capitalise first char of action (camelCase -> PascalCase)
    pascal_action = action[0].upper() + action[1:]
    pascal_suffix = suffix.capitalize()
    return f"PROMO - Profile - {pascal_action}{pascal_suffix}"


# Ordered list of FSS operations (message actions)
FSS_OPS = [
    ("getDevAccounts", "PROMO - FSS Op - GetDevAccounts"),
    ("listDevPackages", "PROMO - FSS Op - ListDevPackages"),
    ("resolveDependencies", "PROMO - FSS Op - ResolveDependencies"),
    ("executePromotion", "PROMO - FSS Op - ExecutePromotion"),
    ("packageAndDeploy", "PROMO - FSS Op - PackageAndDeploy"),
    ("queryStatus", "PROMO - FSS Op - QueryStatus"),
    ("queryPeerReviewQueue", "PROMO - FSS Op - QueryPeerReviewQueue"),
    ("submitPeerReview", "PROMO - FSS Op - SubmitPeerReview"),
    ("queryTestDeployments", "PROMO - FSS Op - QueryTestDeployments"),
    ("withdrawPromotion", "PROMO - FSS Op - WithdrawPromotion"),
    ("manageMappings", "PROMO - FSS Op - ManageMappings"),
    ("generateComponentDiff", "PROMO - FSS Op - GenerateComponentDiff"),
    ("listIntegrationPacks", "PROMO - FSS Op - ListIntegrationPacks"),
    ("cancelTestDeployment", "PROMO - FSS Op - CancelTestDeployment"),
    # Phase 7: Extension Editor
    ("listClientAccounts", "PROMO - FSS Op - ListClientAccounts"),
    ("getExtensions", "PROMO - FSS Op - GetExtensions"),
    ("updateExtensions", "PROMO - FSS Op - UpdateExtensions"),
    ("copyExtensionsTestToProd", "PROMO - FSS Op - CopyExtensionsTestToProd"),
    ("updateMapExtension", "PROMO - FSS Op - UpdateMapExtension"),
    ("checkReleaseStatus", "PROMO - FSS Op - CheckReleaseStatus"),
    ("validateScript", "PROMO - FSS Op - ValidateScript"),
]

# Ordered list of processes for manual build (letter_code, display_name, build_guide_file)
PROCESS_BUILD_ORDER = [
    ("F", "PROMO - FSS Op - ManageMappings (Process F)", "05-process-f-mapping-crud.md"),
    ("A0", "PROMO - Process A0 - GetDevAccounts", "06-process-a0-get-dev-accounts.md"),
    ("E", "PROMO - Process E - QueryStatus", "07-process-e-status-and-review.md"),
    ("E2", "PROMO - Process E2 - QueryPeerReviewQueue", "07-process-e-status-and-review.md"),
    ("E3", "PROMO - Process E3 - SubmitPeerReview", "07-process-e-status-and-review.md"),
    ("E4", "PROMO - Process E4 - QueryTestDeployments", "07-process-e-status-and-review.md"),
    ("E5", "PROMO - Process E5 - WithdrawPromotion", "07-process-e-status-and-review.md"),
    ("J", "PROMO - Process J - ListIntegrationPacks", "12-process-j-list-integration-packs.md"),
    ("G", "PROMO - Process G - GenerateComponentDiff", "13-process-g-component-diff.md"),
    ("A", "PROMO - Process A - ListDevPackages", "08-process-a-list-dev-packages.md"),
    ("B", "PROMO - Process B - ResolveDependencies", "09-process-b-resolve-dependencies.md"),
    ("C", "PROMO - Process C - ExecutePromotion", "10-process-c-execute-promotion.md"),
    ("D", "PROMO - Process D - PackageAndDeploy", "11-process-d-package-and-deploy.md"),
    # Phase 7: Extension Editor
    ("K", "PROMO - Process K - ListClientAccounts", "20-process-k-list-client-accounts.md"),
    ("L", "PROMO - Process L - GetExtensions", "20-process-l-get-extensions.md"),
    ("M", "PROMO - Process M - UpdateExtensions", "20-process-m-update-extensions.md"),
    ("N", "PROMO - Process N - CopyExtensionsTestToProd", "20-process-n-copy-extensions.md"),
    ("O", "PROMO - Process O - UpdateMapExtension", "20-process-o-update-map-extension.md"),
    ("P", "PROMO - Process P - CheckReleaseStatus", "11-process-d-package-and-deploy.md"),
    ("Q", "PROMO - Process Q - ValidateScript", "24-extension-processes.md"),
]


# ---- Step 3.0: DiscoverProfileTemplate ------------------------------------

class DiscoverProfileTemplate(BaseStep):
    """Guide user to create one JSON profile in Boomi, then capture its XML as a template."""

    @property
    def step_id(self) -> str:
        return "3.0"

    @property
    def name(self) -> str:
        return "Discover Profile Template"

    @property
    def step_type(self) -> StepType:
        return StepType.MANUAL

    @property
    def depends_on(self) -> list[str]:
        return ["2.5"]  # Phase 2 verification

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would guide user to create a sample JSON profile.")
            return StepStatus.COMPLETED

        guide_and_wait(
            "Create ONE JSON profile manually in Boomi AtomSphere:\n\n"
            "1. Go to Build > New Component > JSON Profile\n"
            "2. Name it: PROMO - Profile - GetDevAccountsRequest\n"
            "3. Import schema from: integration/profiles/getDevAccounts-request.json\n"
            "4. Save the component\n"
            "5. Copy the component ID from the URL",
            build_guide_ref="04-process-canvas-fundamentals.md",
        )

        comp_id = collect_component_id("Enter the profile component ID")
        state.store_component_id("profiles", "getDevAccounts-request", comp_id)

        # Export the component XML to use as a template
        ui.print_info("Fetching component XML as template...")
        xml_result = self.platform_api.get_component(comp_id)
        if isinstance(xml_result, dict):
            import json
            xml_str = json.dumps(xml_result)
        else:
            xml_str = str(xml_result)

        state.set_discovery_template("profile_template_xml", xml_str)
        state.mark_step_item_complete(self.step_id, "getDevAccounts-request")
        ui.print_success("Profile template captured.")
        return StepStatus.COMPLETED


# ---- Step 3.1: CreateProfiles ----------------------------------------------

class CreateProfiles(BaseStep):
    """Automatically create all 38 JSON profiles via Platform API using XML generator."""

    @property
    def step_id(self) -> str:
        return "3.1"

    @property
    def name(self) -> str:
        return "Create Profiles"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    @property
    def depends_on(self) -> list[str]:
        return ["2.8"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        import json as json_mod
        ui.print_step(self.step_id, self.name, self.step_type.value)

        all_profiles = list_profiles()
        remaining = state.get_remaining_items(self.step_id, all_profiles)

        if not remaining:
            ui.print_success("All 42 profiles already created.")
            return StepStatus.COMPLETED

        ui.print_info(f"Creating {len(remaining)} of {len(all_profiles)} profiles...")

        for i, stem in enumerate(remaining, 1):
            display_name = _profile_display_name(stem)
            ui.print_progress(
                len(all_profiles) - len(remaining) + i, len(all_profiles), display_name
            )

            if dry_run:
                state.mark_step_item_complete(self.step_id, stem)
                continue

            # Load JSON schema and generate profile XML
            schema_str = load_template(f"integration/profiles/{stem}.json")
            schema = json_mod.loads(schema_str)

            try:
                profile_xml = generate_profile_xml(schema, display_name, "PROMO/Profiles")
                result = self.platform_api.create_component(profile_xml)
                comp_id = self.platform_api.parse_component_id(result)
                if comp_id:
                    state.store_component_id("profiles", stem, comp_id)
                    state.mark_step_item_complete(self.step_id, stem)
                    ui.print_success(f"Created {display_name} -> {comp_id}")
                else:
                    ui.print_error(f"No component ID returned for {display_name}")
                    return StepStatus.FAILED
            except Exception as exc:
                ui.print_error(f"Failed to create {display_name}: {exc}")
                return StepStatus.FAILED

        ui.print_success(f"All {len(all_profiles)} profiles created.")
        return StepStatus.COMPLETED


# ---- Step 3.1b: CreateScripts ----------------------------------------------

class CreateScripts(BaseStep):
    """Automatically create all 11 Groovy process scripts via Platform API."""

    @property
    def step_id(self) -> str:
        return "3.1b"

    @property
    def name(self) -> str:
        return "Create Scripts"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    @property
    def depends_on(self) -> list[str]:
        return ["2.8"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        all_scripts = sorted(SCRIPT_NAME_MAP.keys())
        remaining = state.get_remaining_items(self.step_id, all_scripts)

        if not remaining:
            ui.print_success("All 11 scripts already created.")
            return StepStatus.COMPLETED

        ui.print_info(f"Creating {len(remaining)} of {len(all_scripts)} scripts...")

        for i, stem in enumerate(remaining, 1):
            component_name = script_stem_to_component_name(stem)
            ui.print_progress(
                len(all_scripts) - len(remaining) + i, len(all_scripts), component_name
            )

            if dry_run:
                state.mark_step_item_complete(self.step_id, stem)
                continue

            groovy_content = load_template(f"integration/scripts/{stem}.groovy")

            try:
                script_xml = generate_script_xml(
                    groovy_content, component_name, "Promoted/Scripts"
                )
                result = self.platform_api.create_component(script_xml)
                comp_id = self.platform_api.parse_component_id(result)
                if comp_id:
                    state.store_component_id("scripts", stem, comp_id)
                    state.mark_step_item_complete(self.step_id, stem)
                    ui.print_success(f"Created {component_name} -> {comp_id}")
                else:
                    ui.print_error(f"No component ID returned for {component_name}")
                    return StepStatus.FAILED
            except Exception as exc:
                ui.print_error(f"Failed to create {component_name}: {exc}")
                return StepStatus.FAILED

        ui.print_success(f"All {len(all_scripts)} scripts created.")
        return StepStatus.COMPLETED


# ---- Step 3.2: DiscoverFssTemplate ----------------------------------------

class DiscoverFssTemplate(BaseStep):
    """Guide user to create one FSS operation in Boomi, capture XML as template."""

    @property
    def step_id(self) -> str:
        return "3.2"

    @property
    def name(self) -> str:
        return "Discover FSS Operation Template"

    @property
    def step_type(self) -> StepType:
        return StepType.MANUAL

    @property
    def depends_on(self) -> list[str]:
        return ["3.1b"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would guide user to create a sample FSS operation.")
            return StepStatus.COMPLETED

        guide_and_wait(
            "Create ONE Flow Service Server (FSS) operation manually in Boomi:\n\n"
            "1. Go to Build > New Component > Connector Operation\n"
            "2. Type: Flow Service Server\n"
            "3. Name it: PROMO - FSS Op - GetDevAccounts\n"
            "4. Configure request/response profiles from created profiles\n"
            "5. Save and copy the component ID",
            build_guide_ref="04-process-canvas-fundamentals.md",
        )

        comp_id = collect_component_id("Enter the FSS operation component ID")
        state.store_component_id("fss_operations", "getDevAccounts", comp_id)

        ui.print_info("Fetching component XML as template...")
        xml_result = self.platform_api.get_component(comp_id)
        if isinstance(xml_result, dict):
            import json
            xml_str = json.dumps(xml_result)
        else:
            xml_str = str(xml_result)

        state.set_discovery_template("fss_operation_template_xml", xml_str)
        state.mark_step_item_complete(self.step_id, "getDevAccounts")
        ui.print_success("FSS operation template captured.")
        return StepStatus.COMPLETED


# ---------------------------------------------------------------------------
# FSS Operation XML builder — uses the captured template XML as a base
# ---------------------------------------------------------------------------

def _build_fss_op_xml(
    template_xml: str,
    display_name: str,
    req_profile_id: str | None,
    resp_profile_id: str | None,
) -> str:
    """Build FSS operation XML for a new connector-action component.

    Uses the captured template XML from DiscoverFssTemplate (Step 3.2) as a
    structural base so that the bns: namespace, folderFullPath, and all
    required attributes are present. Replaces only the component name,
    componentId (removed so API assigns a new one), and profile IDs.

    Falls back to a minimal correct inline XML if regex substitution cannot
    locate the expected attributes in the template.
    """
    import re

    # Strip the existing componentId so the API creates a brand-new component.
    xml = re.sub(r'\s*componentId="[^"]*"', "", template_xml)

    # Replace the component name attribute.
    xml = re.sub(r'(?<=\bname=")[^"]*', display_name, xml, count=1)

    # Replace requestProfileId content.
    req_val = req_profile_id or ""
    xml = re.sub(
        r"(<(?:bns:)?requestProfileId>)[^<]*(</(?:bns:)?requestProfileId>)",
        rf"\g<1>{req_val}\g<2>",
        xml,
    )

    # Replace responseProfileId content.
    resp_val = resp_profile_id or ""
    xml = re.sub(
        r"(<(?:bns:)?responseProfileId>)[^<]*(</(?:bns:)?responseProfileId>)",
        rf"\g<1>{resp_val}\g<2>",
        xml,
    )

    # Sanity check: if the result still contains the template's original name
    # or the bns: namespace is absent, fall back to a known-good inline XML.
    if 'xmlns:bns="http://api.platform.boomi.com/"' not in xml:
        # Fallback: build minimal correct namespaced XML directly.
        xml = (
            f'<bns:Component xmlns:bns="http://api.platform.boomi.com/"'
            f' name="{display_name}"'
            f' type="connector-action" subType="flowserviceserver">'
            f"<bns:object>"
            f"<requestProfileId>{req_val}</requestProfileId>"
            f"<responseProfileId>{resp_val}</responseProfileId>"
            f"</bns:object>"
            f"</bns:Component>"
        )

    return xml


# ---- Step 3.3: CreateFssOps -----------------------------------------------

class CreateFssOps(BaseStep):
    """Automatically create all 21 FSS operations via Platform API."""

    @property
    def step_id(self) -> str:
        return "3.3"

    @property
    def name(self) -> str:
        return "Create FSS Operations"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    @property
    def depends_on(self) -> list[str]:
        return ["3.2"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        template_xml = state.api_first_discovery.get("fss_operation_template_xml")
        if not template_xml:
            ui.print_error("FSS operation template not found. Complete step 3.2 first.")
            return StepStatus.FAILED

        all_ops = [key for key, _ in FSS_OPS]
        remaining = state.get_remaining_items(self.step_id, all_ops)

        if not remaining:
            ui.print_success(f"All {len(all_ops)} FSS operations already created.")
            return StepStatus.COMPLETED

        ops_lookup = dict(FSS_OPS)
        ui.print_info(f"Creating {len(remaining)} of {len(all_ops)} FSS operations...")

        for i, action_key in enumerate(remaining, 1):
            display_name = ops_lookup[action_key]
            ui.print_progress(
                len(all_ops) - len(remaining) + i, len(all_ops), display_name
            )

            # Look up request/response profile IDs
            req_profile_id = state.get_component_id(
                "profiles", f"{action_key}-request"
            )
            resp_profile_id = state.get_component_id(
                "profiles", f"{action_key}-response"
            )

            if dry_run:
                state.mark_step_item_complete(self.step_id, action_key)
                continue

            try:
                # Build FSS operation XML using the captured template as the
                # structural basis, replacing name and profile IDs. This
                # ensures the bns: namespace, folderFullPath, and all required
                # attributes are present exactly as the API expects them.
                fss_xml = _build_fss_op_xml(
                    template_xml, display_name, req_profile_id, resp_profile_id
                )
                result = self.platform_api.create_component(fss_xml)
                comp_id = self.platform_api.parse_component_id(result)
                if comp_id:
                    state.store_component_id("fss_operations", action_key, comp_id)
                    state.mark_step_item_complete(self.step_id, action_key)
                    ui.print_success(f"Created {display_name} -> {comp_id}")
                else:
                    ui.print_error(f"No component ID returned for {display_name}")
                    return StepStatus.FAILED
            except Exception as exc:
                ui.print_error(f"Failed to create {display_name}: {exc}")
                return StepStatus.FAILED

        ui.print_success(f"All {len(all_ops)} FSS operations created.")
        return StepStatus.COMPLETED


# ---- Step 3.4: BuildProcesses ----------------------------------------------

class BuildProcesses(BaseStep):
    """Guide user through manually building all 18 integration processes."""

    @property
    def step_id(self) -> str:
        return "3.4"

    @property
    def name(self) -> str:
        return "Build Integration Processes"

    @property
    def step_type(self) -> StepType:
        return StepType.MANUAL

    @property
    def depends_on(self) -> list[str]:
        return ["3.3"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        all_codes = [code for code, _, _ in PROCESS_BUILD_ORDER]
        remaining = state.get_remaining_items(self.step_id, all_codes)

        if not remaining:
            ui.print_success(f"All {len(PROCESS_BUILD_ORDER)} processes already built.")
            return StepStatus.COMPLETED

        ui.print_info(
            f"Building {len(remaining)} of {len(PROCESS_BUILD_ORDER)} processes..."
        )

        # Build a lookup for the remaining items
        order_lookup = {code: (name, guide) for code, name, guide in PROCESS_BUILD_ORDER}

        for i, code in enumerate(remaining, 1):
            proc_name, guide_file = order_lookup[code]
            total_done = len(all_codes) - len(remaining) + i
            ui.print_progress(total_done, len(all_codes), f"Process {code}")

            if dry_run:
                state.mark_step_item_complete(self.step_id, code)
                continue

            # Show relevant component IDs from state
            _show_process_context(state, code)

            guide_and_wait(
                f"Build Process {code}: {proc_name}\n\n"
                f"Follow the build guide for detailed shape-by-shape instructions.\n"
                f"When finished, save the process and copy the component ID.",
                build_guide_ref=guide_file,
            )

            comp_id = collect_component_id(f"Enter component ID for Process {code}")
            state.store_component_id("processes", code, comp_id)
            state.mark_step_item_complete(self.step_id, code)
            ui.print_success(f"Process {code} recorded -> {comp_id}")

        ui.print_success("All processes built.")
        return StepStatus.COMPLETED


def _show_process_context(state: SetupState, code: str) -> None:
    """Display relevant component IDs needed for building a process."""
    rows: list[list[str]] = []

    # Show FSS operation for this process
    action_map = {
        "F": "manageMappings",
        "A0": "getDevAccounts",
        "A": "listDevPackages",
        "B": "resolveDependencies",
        "C": "executePromotion",
        "D": "packageAndDeploy",
        "E": "queryStatus",
        "E2": "queryPeerReviewQueue",
        "E3": "submitPeerReview",
        "E4": "queryTestDeployments",
        "E5": "withdrawPromotion",
        "G": "generateComponentDiff",
        "J": "listIntegrationPacks",
        # Phase 7: Extension Editor
        "K": "listClientAccounts",
        "L": "getExtensions",
        "M": "updateExtensions",
        "N": "copyExtensionsTestToProd",
        "O": "updateMapExtension",
    }
    action = action_map.get(code)
    if action:
        fss_id = state.get_component_id("fss_operations", action) or "not yet created"
        rows.append(["FSS Op", action, fss_id])

        req_id = state.get_component_id("profiles", f"{action}-request") or "n/a"
        resp_id = state.get_component_id("profiles", f"{action}-response") or "n/a"
        rows.append(["Request Profile", f"{action}-request", req_id])
        rows.append(["Response Profile", f"{action}-response", resp_id])

    # Show connection IDs if available
    for conn_name in ("platformApi", "dataHub"):
        conn_id = state.get_component_id("connections", conn_name)
        if conn_id:
            rows.append(["Connection", conn_name, conn_id])

    if rows:
        ui.print_table(
            f"Component IDs for Process {code}",
            ["Type", "Name", "Component ID"],
            rows,
        )


# ---- Step 3.5: VerifyPhase3 ------------------------------------------------

class VerifyPhase3(BaseStep):
    """Validate Phase 3 artifact counts."""

    @property
    def step_id(self) -> str:
        return "3.5"

    @property
    def name(self) -> str:
        return "Verify Phase 3"

    @property
    def step_type(self) -> StepType:
        return StepType.VALIDATE

    @property
    def depends_on(self) -> list[str]:
        return ["3.4"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would verify Phase 3 component counts.")
            return StepStatus.COMPLETED

        passed = True

        # Count profiles
        profiles = state.data.get("component_ids", {}).get("profiles", {})
        profile_count = len(profiles)
        expected_profiles = len(list_profiles())
        if profile_count >= expected_profiles:
            ui.print_success(f"Profiles: {profile_count}/{expected_profiles}")
        else:
            ui.print_error(f"Profiles: {profile_count}/{expected_profiles} — expected {expected_profiles}")
            passed = False

        # Count scripts
        scripts = state.data.get("component_ids", {}).get("scripts", {})
        script_count = len(scripts)
        expected_scripts = len(SCRIPT_NAME_MAP)
        if script_count >= expected_scripts:
            ui.print_success(f"Scripts: {script_count}/{expected_scripts}")
        else:
            ui.print_error(f"Scripts: {script_count}/{expected_scripts} — expected {expected_scripts}")
            passed = False

        # Count FSS operations
        fss_ops = state.data.get("component_ids", {}).get("fss_operations", {})
        fss_count = len(fss_ops)
        expected_fss = len(FSS_OPS)
        if fss_count >= expected_fss:
            ui.print_success(f"FSS operations: {fss_count}/{expected_fss}")
        else:
            ui.print_error(f"FSS operations: {fss_count}/{expected_fss} — expected {expected_fss}")
            passed = False

        # Count processes
        processes = state.data.get("component_ids", {}).get("processes", {})
        proc_count = len(processes)
        expected_procs = len(PROCESS_BUILD_ORDER)
        if proc_count >= expected_procs:
            ui.print_success(f"Processes: {proc_count}/{expected_procs}")
        else:
            ui.print_error(f"Processes: {proc_count}/{expected_procs} — expected {expected_procs}")
            passed = False

        if passed:
            ui.print_success("Phase 3 verification passed.")
            return StepStatus.COMPLETED
        else:
            ui.print_error("Phase 3 verification failed. Fix missing components and re-run.")
            return StepStatus.FAILED

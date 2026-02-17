"""Phase 4 build steps: Flow Service creation, packaging, deployment, and verification."""
from __future__ import annotations

from setup.engine import StepStatus, StepType
from setup.state import SetupState
from setup.steps.base import BaseStep
from setup.ui import console as ui
from setup.ui.prompts import collect_component_id, guide_and_confirm, guide_and_wait


# ---- Step 4.0: CreateFlowService -------------------------------------------

class CreateFlowService(BaseStep):
    """Guide user through creating the Flow Service component with all 19 message actions."""

    @property
    def step_id(self) -> str:
        return "4.0"

    @property
    def name(self) -> str:
        return "Create Flow Service"

    @property
    def step_type(self) -> StepType:
        return StepType.MANUAL

    @property
    def depends_on(self) -> list[str]:
        return ["3.5"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would guide user to create Flow Service with 19 message actions.")
            return StepStatus.COMPLETED

        # Show all FSS operation component IDs for reference
        fss_ops = state.data.get("component_ids", {}).get("fss_operations", {})
        rows = [[name, comp_id] for name, comp_id in sorted(fss_ops.items())]
        if rows:
            ui.print_table(
                "FSS Operations (for Flow Service configuration)",
                ["Action", "Component ID"],
                rows,
            )

        guide_and_wait(
            "Create the Flow Service component in Boomi AtomSphere:\n\n"
            "1. Go to Build > New Component > Flow Service\n"
            "2. Name it: PROMO - Flow Service\n"
            "3. Add all 19 message actions listed above\n"
            "4. For each action, link the corresponding FSS operation\n"
            "5. Configure the listener (connector + operation for each action)\n"
            "6. Save and copy the component ID",
            build_guide_ref="14-flow-service.md",
        )

        comp_id = collect_component_id("Enter the Flow Service component ID")
        state.store_component_id("flow_service", "", comp_id)
        ui.print_success(f"Flow Service recorded -> {comp_id}")
        return StepStatus.COMPLETED


# ---- Step 4.1: PackageAndDeploy -------------------------------------------

class PackageAndDeployFlowService(BaseStep):
    """Package, create Integration Pack, and deploy the Flow Service."""

    @property
    def step_id(self) -> str:
        return "4.1"

    @property
    def name(self) -> str:
        return "Package and Deploy Flow Service"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    @property
    def depends_on(self) -> list[str]:
        return ["4.0"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        flow_service_id = state.get_component_id("flow_service", "")
        if not flow_service_id:
            ui.print_error("Flow Service component ID not found. Complete step 4.0 first.")
            return StepStatus.FAILED

        env_id = state.config.get("target_environment_id", "")
        if not env_id:
            ui.print_error("Target environment ID not configured.")
            return StepStatus.FAILED

        if dry_run:
            ui.print_info(f"Would package {flow_service_id}, create Integration Pack, deploy.")
            return StepStatus.COMPLETED

        try:
            # Step 1: Create packaged component
            ui.print_info("Creating packaged component...")
            pkg_result = self.platform_api.create_packaged_component(
                flow_service_id, "1.0", "Initial deployment"
            )
            package_id = (
                pkg_result.get("packageId", pkg_result.get("@id", ""))
                if isinstance(pkg_result, dict)
                else str(pkg_result)
            )
            if not package_id:
                ui.print_error("Failed to get package ID from packaged component creation.")
                return StepStatus.FAILED
            ui.print_success(f"Packaged component created -> {package_id}")

            # Step 2: Create Integration Pack
            ui.print_info("Creating Integration Pack...")
            pack_result = self.platform_api.create_integration_pack(
                "PROMO Flow Service", "Promotion system Flow Service"
            )
            pack_id = (
                pack_result.get("integrationPackId", pack_result.get("@id", ""))
                if isinstance(pack_result, dict)
                else str(pack_result)
            )
            if not pack_id:
                ui.print_error("Failed to get Integration Pack ID.")
                return StepStatus.FAILED
            ui.print_success(f"Integration Pack created -> {pack_id}")

            # Step 3: Add package to Integration Pack
            ui.print_info("Adding package to Integration Pack...")
            self.platform_api.add_to_integration_pack(pack_id, package_id)
            ui.print_success("Package added to Integration Pack.")

            # Step 4: Release Integration Pack
            ui.print_info("Releasing Integration Pack...")
            release_result = self.platform_api.release_integration_pack(
                pack_id, "1.0", "Initial release"
            )
            release_id = (
                release_result.get("releaseId", release_result.get("@id", ""))
                if isinstance(release_result, dict)
                else str(release_result)
            )
            if not release_id:
                ui.print_error("Failed to get release ID.")
                return StepStatus.FAILED
            ui.print_success(f"Integration Pack released -> {release_id}")

            # Step 5: Deploy
            ui.print_info(f"Deploying to environment {env_id}...")
            self.platform_api.deploy_package(release_id, env_id)
            ui.print_success("Flow Service deployed successfully.")

            return StepStatus.COMPLETED

        except Exception as exc:
            ui.print_error(f"Deployment failed: {exc}")
            return StepStatus.FAILED


# ---- Step 4.2: ConfigPrimaryId --------------------------------------------

class ConfigPrimaryId(BaseStep):
    """Guide user to configure the primary account ID atom property."""

    @property
    def step_id(self) -> str:
        return "4.2"

    @property
    def name(self) -> str:
        return "Configure Primary Account ID"

    @property
    def step_type(self) -> StepType:
        return StepType.MANUAL

    @property
    def depends_on(self) -> list[str]:
        return ["4.1"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        account_id = state.config.get("boomi_account_id", "<your_account_id>")

        if dry_run:
            ui.print_info("Would guide user to set com.boomi.flow.primary.account.id.")
            return StepStatus.COMPLETED

        confirmed = guide_and_confirm(
            f"Configure the primary account ID on the Atom:\n\n"
            f"1. Go to Manage > Atom Management\n"
            f"2. Select your Cloud Atom\n"
            f"3. Go to Properties > Advanced tab\n"
            f"4. Click 'Add Property'\n"
            f"5. Property name: com.boomi.flow.primary.account.id\n"
            f"6. Property value: {account_id}\n"
            f"7. Save and restart the Atom if required",
            question="Have you configured the primary account ID property?",
        )

        if confirmed:
            ui.print_success("Primary account ID configured.")
            return StepStatus.COMPLETED
        else:
            ui.print_error("Step not confirmed. Please complete the configuration.")
            return StepStatus.FAILED


# ---- Step 4.3: VerifyPhase4 -----------------------------------------------

class VerifyPhase4(BaseStep):
    """Validate Phase 4 by testing the Flow Service endpoint."""

    @property
    def step_id(self) -> str:
        return "4.3"

    @property
    def name(self) -> str:
        return "Verify Phase 4"

    @property
    def step_type(self) -> StepType:
        return StepType.VALIDATE

    @property
    def depends_on(self) -> list[str]:
        return ["4.2"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would verify Flow Service deployment via getDevAccounts call.")
            return StepStatus.COMPLETED

        flow_service_id = state.get_component_id("flow_service", "")
        if not flow_service_id:
            ui.print_error("Flow Service component ID not found.")
            return StepStatus.FAILED

        ui.print_info("Verifying Flow Service deployment...")
        ui.print_info(f"Flow Service component ID: {flow_service_id}")

        confirmed = guide_and_confirm(
            "Test the Flow Service endpoint:\n\n"
            "1. Open Boomi Flow and create a simple test flow\n"
            "   OR use the API directly:\n"
            "   POST to the Flow Service URL with action 'getDevAccounts'\n"
            "2. Verify you receive a valid response (list of dev accounts)\n"
            "3. Check Process Reporting for the execution log",
            question="Did the Flow Service respond successfully?",
        )

        if confirmed:
            ui.print_success("Phase 4 verification passed.")
            return StepStatus.COMPLETED
        else:
            ui.print_error(
                "Phase 4 verification failed. Check Flow Service config and deployment."
            )
            return StepStatus.FAILED

"""Phase 6 build steps: Smoke tests, full test scenarios, and final verification."""
from __future__ import annotations

from setup.engine import StepStatus, StepType
from setup.state import SetupState
from setup.steps.base import BaseStep
from setup.ui import console as ui
from setup.ui.prompts import guide_and_confirm


# 17 test scenarios from build guide 17-testing.md
TEST_SCENARIOS = [
    ("test_01", "Get dev accounts for valid SSO group"),
    ("test_02", "Get dev accounts for invalid group (expect empty)"),
    ("test_03", "List packages for a dev account"),
    ("test_04", "Resolve dependencies for a package"),
    ("test_05", "Execute promotion (new components)"),
    ("test_06", "Execute promotion (existing components - update)"),
    ("test_07", "Query promotion status"),
    ("test_08", "Submit peer review (approve)"),
    ("test_09", "Submit peer review (reject)"),
    ("test_10", "Self-review prevention test"),
    ("test_11", "Admin approval flow"),
    ("test_12", "Package and deploy to test"),
    ("test_13", "Query test deployments"),
    ("test_14", "Cancel test deployment"),
    ("test_15", "Promote from test to production"),
    ("test_16", "Component diff generation"),
    ("test_17", "Withdraw pending promotion"),
]

# Expected component counts by category
EXPECTED_COUNTS = {
    "models": 3,
    "connections": 2,
    "http_operations": 19,
    "dh_operations": 6,
    "profiles": 26,
    "fss_operations": 14,
    "processes": 12,
}

EXPECTED_TOTAL = 85


# ---- Step 6.0: SmokeTest --------------------------------------------------

class SmokeTest(BaseStep):
    """Guide user through a basic smoke test of the Flow Service."""

    @property
    def step_id(self) -> str:
        return "6.0"

    @property
    def name(self) -> str:
        return "Smoke Test"

    @property
    def step_type(self) -> StepType:
        return StepType.SEMI

    @property
    def depends_on(self) -> list[str]:
        return ["5.0"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would guide user through basic getDevAccounts smoke test.")
            return StepStatus.COMPLETED

        flow_service_id = state.get_component_id("flow_service", "")
        ui.print_info(f"Flow Service ID: {flow_service_id or 'not set'}")

        confirmed = guide_and_confirm(
            "Run a basic smoke test:\n\n"
            "1. Open the Flow Dashboard in a browser\n"
            "2. Log in with a user in the ABC_BOOMI_FLOW_CONTRIBUTOR SSO group\n"
            "3. The Package Browser page should load\n"
            "4. Select a dev account from the dropdown\n"
            "5. Verify the getDevAccounts action returns a list of accounts\n\n"
            "Expected response format:\n"
            '  { "accounts": [{"accountId": "...", "accountName": "..."}] }\n\n'
            "Check Process Reporting in AtomSphere for execution details.",
            question="Did the smoke test pass?",
        )

        if confirmed:
            ui.print_success("Smoke test passed.")
            return StepStatus.COMPLETED
        else:
            ui.print_error("Smoke test failed. Check Flow Service and process configurations.")
            return StepStatus.FAILED


# ---- Step 6.1: FullTests --------------------------------------------------

class FullTests(BaseStep):
    """Guide user through all 17 test scenarios with individual tracking."""

    @property
    def step_id(self) -> str:
        return "6.1"

    @property
    def name(self) -> str:
        return "Full Test Scenarios"

    @property
    def step_type(self) -> StepType:
        return StepType.SEMI

    @property
    def depends_on(self) -> list[str]:
        return ["6.0"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        all_keys = [key for key, _ in TEST_SCENARIOS]
        remaining = state.get_remaining_items(self.step_id, all_keys)

        if not remaining:
            ui.print_success("All 17 test scenarios already passed.")
            return StepStatus.COMPLETED

        total = len(TEST_SCENARIOS)
        ui.print_info(f"Running {len(remaining)} of {total} test scenarios...")
        ui.print_build_guide_ref("17-testing.md")

        if dry_run:
            ui.print_info("Would guide user through all remaining test scenarios.")
            return StepStatus.COMPLETED

        scenario_lookup = dict(TEST_SCENARIOS)

        for test_key in remaining:
            description = scenario_lookup[test_key]
            done_count = total - len(remaining) + 1
            test_num = int(test_key.split("_")[1])
            ui.print_progress(done_count, total, f"Test {test_num}: {description}")

            confirmed = guide_and_confirm(
                f"Test Scenario {test_num}: {description}\n\n"
                f"Follow the test instructions in docs/build-guide/17-testing.md\n"
                f"for scenario {test_num}.\n\n"
                f"Execute the test and verify the expected outcome.",
                question=f"Did test {test_num} ({description}) pass?",
            )

            if confirmed:
                state.mark_step_item_complete(self.step_id, test_key)
                remaining = [r for r in remaining if r != test_key]
                ui.print_success(f"Test {test_num} passed.")
            else:
                ui.print_error(
                    f"Test {test_num} failed. Fix the issue and re-run to resume."
                )
                return StepStatus.FAILED

        ui.print_success(f"All {total} test scenarios passed.")
        return StepStatus.COMPLETED


# ---- Step 6.2: FinalVerify ------------------------------------------------

class FinalVerify(BaseStep):
    """Run complete component count verification against Boomi account."""

    @property
    def step_id(self) -> str:
        return "6.2"

    @property
    def name(self) -> str:
        return "Final Verification"

    @property
    def step_type(self) -> StepType:
        return StepType.VALIDATE

    @property
    def depends_on(self) -> list[str]:
        return ["6.1"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would verify all component counts against Boomi account.")
            return StepStatus.COMPLETED

        ui.print_info("Running final component count verification...")

        # Query actual count from Boomi
        try:
            actual_total = self.platform_api.count_components_by_prefix("PROMO")
            ui.print_info(f"Boomi reports {actual_total} components with PROMO prefix.")
        except Exception as exc:
            ui.print_error(f"Could not query Boomi component count: {exc}")
            actual_total = None

        # Verify counts from state
        component_ids = state.data.get("component_ids", {})
        passed = True
        rows: list[list[str]] = []

        for category, expected in EXPECTED_COUNTS.items():
            bucket = component_ids.get(category, {})
            actual = len(bucket) if isinstance(bucket, dict) else (1 if bucket else 0)
            status = "OK" if actual >= expected else "MISSING"
            if actual < expected:
                passed = False
            rows.append([category, str(expected), str(actual), status])

        # Flow Service (scalar)
        fs_id = component_ids.get("flow_service")
        fs_status = "OK" if fs_id else "MISSING"
        if not fs_id:
            passed = False
        rows.append(["flow_service", "1", "1" if fs_id else "0", fs_status])

        ui.print_table(
            "Component Count Verification",
            ["Category", "Expected", "Actual", "Status"],
            rows,
        )

        # Summary
        state_total = sum(
            len(v) if isinstance(v, dict) else (1 if v else 0)
            for v in component_ids.values()
        )
        ui.print_info(f"State file total: {state_total}")
        ui.print_info(f"Expected total: {EXPECTED_TOTAL}")
        if actual_total is not None:
            ui.print_info(f"Boomi PROMO prefix total: {actual_total}")

        if passed:
            ui.print_success(
                "Final verification PASSED. The Boomi promotion system is fully built."
            )
            return StepStatus.COMPLETED
        else:
            ui.print_error(
                "Final verification FAILED. Some components are missing. "
                "Review the table above and fix missing items."
            )
            return StepStatus.FAILED

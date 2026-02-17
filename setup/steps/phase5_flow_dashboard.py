"""Phase 5 build step: Flow Dashboard construction (9 pages, 3 swimlanes)."""
from __future__ import annotations

from setup.engine import StepStatus, StepType
from setup.state import SetupState
from setup.steps.base import BaseStep
from setup.ui import console as ui
from setup.ui.prompts import guide_and_confirm, guide_and_wait


# Page definitions: (page_number, name, swimlane, build_guide_file)
FLOW_PAGES = [
    (1, "Package Browser", "Developer", "15-flow-dashboard-developer.md"),
    (2, "Promotion Review", "Developer", "15-flow-dashboard-developer.md"),
    (3, "Promotion Status", "Developer", "15-flow-dashboard-developer.md"),
    (4, "Deployment Submission", "Developer", "15-flow-dashboard-developer.md"),
    (5, "Peer Review Queue", "Peer Review", "16-flow-dashboard-review-admin.md"),
    (6, "Peer Review Detail", "Peer Review", "16-flow-dashboard-review-admin.md"),
    (7, "Admin Approval Queue", "Admin", "16-flow-dashboard-review-admin.md"),
    (8, "Mapping Viewer", "Admin", "16-flow-dashboard-review-admin.md"),
    (9, "Production Readiness Queue", "Developer", "16-flow-dashboard-review-admin.md"),
]


class FlowDashboard(BaseStep):
    """Guide user through building all 9 Flow pages across 3 swimlanes."""

    @property
    def step_id(self) -> str:
        return "5.0"

    @property
    def name(self) -> str:
        return "Build Flow Dashboard"

    @property
    def step_type(self) -> StepType:
        return StepType.MANUAL

    @property
    def depends_on(self) -> list[str]:
        return ["4.3"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        all_items = [f"page_{num}" for num, _, _, _ in FLOW_PAGES]
        all_items.extend(["sso_config", "custom_component", "navigation"])
        remaining = state.get_remaining_items(self.step_id, all_items)

        if not remaining:
            ui.print_success("Flow Dashboard fully built.")
            return StepStatus.COMPLETED

        total = len(all_items)
        ui.print_info(f"Building {len(remaining)} of {total} dashboard items...")

        if dry_run:
            ui.print_info("Would guide user through 9 pages + SSO + custom component + nav.")
            return StepStatus.COMPLETED

        # Build each page
        for page_num, page_name, swimlane, guide_file in FLOW_PAGES:
            item_key = f"page_{page_num}"
            if item_key not in remaining:
                continue

            done_count = total - len(remaining) + 1
            ui.print_progress(done_count, total, f"Page {page_num}: {page_name}")

            confirmed = guide_and_confirm(
                f"Build Page {page_num}: {page_name}\n\n"
                f"Swimlane: {swimlane}\n"
                f"Build guide: docs/build-guide/{guide_file}\n\n"
                f"Key steps:\n"
                f"  - Create the page layout in Boomi Flow\n"
                f"  - Add required components (tables, forms, buttons)\n"
                f"  - Wire message actions to UI elements\n"
                f"  - Configure page-level authorization",
                question=f"Have you completed Page {page_num} ({page_name})?",
            )
            if confirmed:
                state.mark_step_item_complete(self.step_id, item_key)
                remaining = [r for r in remaining if r != item_key]
                ui.print_success(f"Page {page_num} ({page_name}) completed.")
            else:
                ui.print_error(f"Page {page_num} not completed. Stopping here for resume.")
                return StepStatus.FAILED

        # SSO swimlane configuration
        if "sso_config" in remaining:
            done_count = total - len(remaining) + 1
            ui.print_progress(done_count, total, "SSO Swimlane Configuration")

            confirmed = guide_and_confirm(
                "Configure SSO swimlane authorization:\n\n"
                "1. Developer Swimlane: Requires SSO group\n"
                "   ABC_BOOMI_FLOW_CONTRIBUTOR or ABC_BOOMI_FLOW_ADMIN\n\n"
                "2. Peer Review Swimlane: Requires SSO group\n"
                "   ABC_BOOMI_FLOW_CONTRIBUTOR or ABC_BOOMI_FLOW_ADMIN\n\n"
                "3. Admin Swimlane: Requires SSO group\n"
                "   ABC_BOOMI_FLOW_ADMIN only\n\n"
                "Configure these in the Flow app's swimlane settings.",
                question="Have you configured SSO swimlane authorization?",
            )
            if confirmed:
                state.mark_step_item_complete(self.step_id, "sso_config")
                remaining = [r for r in remaining if r != "sso_config"]
                ui.print_success("SSO swimlane configuration completed.")
            else:
                ui.print_error("SSO configuration not completed.")
                return StepStatus.FAILED

        # Custom component (XmlDiffViewer)
        if "custom_component" in remaining:
            done_count = total - len(remaining) + 1
            ui.print_progress(done_count, total, "XmlDiffViewer Custom Component")

            confirmed = guide_and_confirm(
                "Install the XmlDiffViewer custom component:\n\n"
                "1. Navigate to the custom component spec:\n"
                "   flow/custom-components/\n"
                "2. Build or import the React component into Boomi Flow\n"
                "3. Register it in the Flow app for use on the Promotion Review page\n"
                "4. Verify it renders XML diff output correctly",
                question="Have you installed the XmlDiffViewer custom component?",
            )
            if confirmed:
                state.mark_step_item_complete(self.step_id, "custom_component")
                remaining = [r for r in remaining if r != "custom_component"]
                ui.print_success("XmlDiffViewer custom component installed.")
            else:
                ui.print_error("Custom component not installed.")
                return StepStatus.FAILED

        # Navigation wiring
        if "navigation" in remaining:
            done_count = total - len(remaining) + 1
            ui.print_progress(done_count, total, "Navigation Wiring")

            confirmed = guide_and_confirm(
                "Wire navigation between pages:\n\n"
                "1. Package Browser -> Promotion Review (on package select)\n"
                "2. Promotion Review -> Promotion Status (after promotion)\n"
                "3. Promotion Status -> Deployment Submission (on deploy action)\n"
                "4. Peer Review Queue -> Peer Review Detail (on review select)\n"
                "5. Production Readiness Queue -> Deployment Submission\n\n"
                "Verify all navigation paths work correctly.\n"
                "See: flow/flow-structure.md for the complete navigation map.",
                question="Have you wired all navigation between pages?",
            )
            if confirmed:
                state.mark_step_item_complete(self.step_id, "navigation")
                ui.print_success("Navigation wiring completed.")
            else:
                ui.print_error("Navigation not completed.")
                return StepStatus.FAILED

        ui.print_success("Flow Dashboard fully built.")
        return StepStatus.COMPLETED

# Team 4: Flow Dashboard Expert Review Findings

**Reviewer Role:** Boomi Flow Platform Expert
**Date:** 2026-02-16
**Files Reviewed:**
- `flow/flow-structure.md`
- `flow/page-layouts/page1-package-browser.md` through `page9-production-readiness.md`
- `docs/build-guide/15-flow-dashboard-developer.md`
- `docs/build-guide/16-flow-dashboard-review-admin.md`
- `docs/build-guide/22-phase7-multi-environment.md`
- `.claude/rules/flow-patterns.md`
- `integration/flow-service/flow-service-spec.md` (cross-reference)

---

## Critical Issues

### C1: SSO Group Name Inconsistency Across Specifications

**Severity:** Critical
**Files:** `flow/flow-structure.md:18`, `flow/page-layouts/page5-peer-review-queue.md:10`, `docs/build-guide/15-flow-dashboard-developer.md:49`, `.claude/rules/flow-patterns.md:10-13`

The SSO group names used for swimlane authorization are inconsistent across the specification:

- `flow/flow-structure.md` and `flow-patterns.md` use: `ABC_BOOMI_FLOW_CONTRIBUTOR`, `ABC_BOOMI_FLOW_ADMIN`
- `flow/page-layouts/page5-peer-review-queue.md`, `page4-deployment-submission.md`, `page7-admin-approval-queue.md` use: `"Boomi Developers"`, `"Boomi Admins"`
- `docs/build-guide/15-flow-dashboard-developer.md:49` uses: `Boomi Developers`, `Boomi Admins`
- `docs/build-guide/16-flow-dashboard-review-admin.md:95-100` uses: `Boomi Developers`, `Boomi Admins`
- `flow/page-layouts/page9-production-readiness.md:9` uses: `ABC_BOOMI_FLOW_CONTRIBUTOR`, `ABC_BOOMI_FLOW_ADMIN`

These are different names. In Azure AD/Entra, the group display name and the group identifier used in SSO claims are distinct. The spec must standardize on one canonical name and clarify whether this is the Azure AD group display name or the claim value. Mixing these will cause SSO authorization failures at runtime.

**Recommendation:** Standardize all references to the `ABC_BOOMI_FLOW_*` format (which appears to be the SSO claim value), and add a mapping table clarifying: `ABC_BOOMI_FLOW_CONTRIBUTOR` = Azure AD display name "Boomi Developers", etc.

### C2: Build Guide Step 5.4 Navigation Missing Page 9

**Severity:** Critical
**File:** `docs/build-guide/15-flow-dashboard-developer.md:59`, `docs/build-guide/16-flow-dashboard-review-admin.md:104-126`

The build guide Step 5.2 says "Build the 8 pages in order" (line 59) and Step 5.4 (Wire Navigation) only lists 16 navigation outcomes covering Pages 1-8. Page 9 is completely absent from the core build guide navigation wiring.

Page 9 navigation is referenced in `docs/build-guide/22-phase7-multi-environment.md:211` ("Add Page 9 to Developer swimlane"), but it is only described at a high level (5 bullet points) and does not include:
- Specific outcome wiring instructions (comparable to Step 5.4's numbered list)
- Navigation from Page 4 test success → Page 9 ("View in Production Readiness" button described in `page4-deployment-submission.md:303`)
- Navigation from Page 1 or a sidebar menu → Page 9 (how does a developer reach Page 9 to check previously tested deployments?)

**Impact:** A builder following the guide will not know how to wire Page 9 into the Flow canvas, and the developer may have no way to navigate to Page 9 without a direct URL.

### C3: Page 9 Navigation Entry Point Unspecified

**Severity:** Critical
**Files:** `flow/flow-structure.md:127-132`, `flow/page-layouts/page9-production-readiness.md`

`flow-structure.md:127` shows Page 9 as navigation step 14, but there is no numbered step showing how the user reaches Page 9 in the first place. The only entry paths mentioned are:

1. From Page 4 test success: a "View in Production Readiness" button (`page4-deployment-submission.md:303`)
2. From Page 1? Sidebar? Direct URL?

There is no sidebar/navigation menu specification for the Developer swimlane that would let users reach Page 9 independently (e.g., returning to check test deployments days later without going through the full promotion flow again). The user flow example in `page9-production-readiness.md:280-281` says "Developer returns to dashboard" and "Navigates to 'Tested Packages' / Production Readiness page" but does not specify the navigation mechanism.

**Recommendation:** Add a sidebar or tab navigation to the Developer swimlane with links to Package Browser (Page 1) and Production Readiness (Page 9), or add a "Tested Deployments" button on Page 1.

---

## Major Issues

### M1: `packageAndDeploy` Usage Inconsistency — flow-structure.md References Wrong Page

**Severity:** Major
**File:** `flow/flow-structure.md:241-249`

Message step 6 (Package and Deploy) says it is "Used in: Page 5, on 'Approve' button click". This is incorrect — `packageAndDeploy` is used on Page 7 (Admin Approval Queue) for production deployments, and on Page 4 for test deployments. Page 5 is the Peer Review Queue, which has no deploy button.

The `page7-admin-approval-queue.md:315-318` correctly documents `packageAndDeploy` on Page 7. The `page4-deployment-submission.md:14` correctly documents it for test deployments.

### M2: Missing Direct-Navigation Guards for Deep Pages

**Severity:** Major
**Files:** All page layouts

None of the page layout specifications define what happens when a user bookmarks or directly navigates to a deep page (e.g., Page 3, Page 6, Page 9) without the prerequisite Flow values being set. In Boomi Flow, if a user shares a URL or bookmarks the page, they may return to a page without `selectedPackage`, `selectedPeerReview`, `promotionResults`, etc. being populated.

Affected pages and their missing guard conditions:
- **Page 2**: Requires `selectedPackage` from Page 1. No guard documented.
- **Page 3**: Requires `promotionResults` from `executePromotion`. No guard documented.
- **Page 4**: Requires `promotionId`, `promotionResults`, `targetEnvironment`. No guard documented.
- **Page 6**: Requires `selectedPeerReview` from Page 5. `page6-peer-review-detail.md:9` has a "Pre-condition" note but no redirect/guard behavior specified.
- **Page 9**: Requires no prerequisites (loads its own data), but should still verify `accessibleAccounts` is populated.

**Recommendation:** For each page with prerequisites, add a Decision step on page load that checks whether required Flow values exist. If not, redirect to the appropriate entry page (Page 1 for developer, Page 5 for peer review, Page 7 for admin).

### M3: Error Page Not Defined as a Formal Page Layout

**Severity:** Major
**File:** `flow/flow-structure.md:522-541`

The Error Page is specified in `flow-structure.md` with components (icon, title, message, technical details, Back/Retry/Home buttons) but does NOT have a dedicated page layout file in `flow/page-layouts/`. Every other page has a full specification file. This shared Error Page is referenced by all Decision step failure paths across all 9 pages and is a core navigation target.

The Error Page specification at `flow-structure.md:522-541` is also missing:
- How the "Retry" button re-executes the failed Message step (what state is needed?)
- How the "Back" button determines which page to return to (Flow history? Stored value?)
- Whether the Error Page lives in a specific swimlane or is accessible cross-swimlane

### M4: Admin Approval Merge-Then-Deploy Workflow Not in Message Step Spec

**Severity:** Major
**Files:** `flow/page-layouts/page7-admin-approval-queue.md:299-339`, `flow/flow-structure.md:150-153`

Page 7 approval involves a 5-step workflow: Create MergeRequest (OVERRIDE) -> Execute merge -> Poll until MERGED -> Call `packageAndDeploy` -> Delete branch. However, this merge workflow is described inline in the page layout spec, not as a formal Message step in `flow-structure.md`.

The merge/deploy sequence involves 3 separate API calls (POST MergeRequest, POST execute, DELETE Branch) that are NOT message actions in the Flow Service. These are direct Platform API calls. But Boomi Flow's Boomi Integration Service connector only supports Message Actions — it cannot make arbitrary HTTP calls.

This means either:
1. The `packageAndDeploy` message action (Process D) must handle the merge internally (which `flow-structure.md:153` suggests), OR
2. A new message action is needed for the merge step

Cross-referencing with the integration spec: `docs/build-guide/13-process-d.md` would need to confirm Process D handles merge+deploy+branch-delete. If it does, the Page 7 spec is misleadingly detailed about steps the UI should not be orchestrating.

### M5: `queryTestDeployments` References Process E4 But Architecture Only Lists 11 Processes

**Severity:** Major
**Files:** `flow/page-layouts/page9-production-readiness.md:2`, `integration/flow-service/flow-service-spec.md:450`, `CLAUDE.md`

Page 9 references `queryTestDeployments` linked to "Process E4." The `CLAUDE.md` architecture section lists 11 processes (A0, A, B, C, D, E, E2, E3, F, G, J) with no E4. The flow-service-spec.md correctly documents E4 at line 450. However, the main architecture documentation and the integration-patterns rule file (`.claude/rules/integration-patterns.md`) do not include Process E4 in their lists.

This creates confusion about whether E4 is part of the core architecture or a Phase 7 addition that has not been backported to the canonical process inventory.

**Recommendation:** Update `CLAUDE.md`, `docs/architecture.md`, and `.claude/rules/integration-patterns.md` to include Process E4 in the process list with proper dependencies.

---

## Minor Issues

### m1: `flow-structure.md` Page Count Inconsistency with `flow-patterns.md`

**Severity:** Minor
**Files:** `flow/flow-structure.md:10`, `.claude/rules/flow-patterns.md:3-20`

`flow-structure.md:10` says "9 pages total (4 developer pages + 1 production readiness page, 2 peer review pages, 2 admin pages)" but `flow-patterns.md` only lists 8 pages (Pages 1-8), omitting Page 9. The `flow-patterns.md` file needs updating to include Page 9.

### m2: Flow Value `userEffectiveTier` Not Used in Any Page Guard

**Severity:** Minor
**Files:** `flow/flow-structure.md:57`, all page layouts

`flow-structure.md:57` defines `userEffectiveTier` as a Flow value set from `getDevAccounts` response, but no page layout references this value for conditional UI behavior. The tier determines "CONTRIBUTOR" vs "ADMIN" dashboard access level, yet no page layout shows different UI elements based on tier. For example:
- Should Contributors see a link to Page 9?
- Should only Admins see certain controls?

If this value is only used for backend authorization (swimlane-level), it should be documented as such. If it affects UI rendering, page layouts should specify the conditional logic.

### m3: Missing Loading State on Page 9

**Severity:** Minor
**File:** `flow/page-layouts/page9-production-readiness.md`

Page 9 does not explicitly specify a loading state during the `queryTestDeployments` message step execution. Other pages (e.g., Page 1 at line 133-135, Page 2 at lines 335-346) explicitly describe loading spinners and messages. Page 9 should specify: "Loading tested deployments..." spinner during the API call.

### m4: Page 4 Test Success Navigation Options Incomplete

**Severity:** Minor
**File:** `flow/page-layouts/page4-deployment-submission.md:302-303`

After a successful test deployment, two buttons are shown: "Return to Dashboard" (→ Page 1) and "View in Production Readiness" (→ Page 9). But neither the flow-structure.md navigation section nor the build guide Step 5.4 includes these navigation outcomes. They are only documented in the page layout spec.

### m5: `selectedPromotion` vs `selectedPeerReview` — Inconsistent Flow Value Names

**Severity:** Minor
**Files:** `flow/page-layouts/page7-admin-approval-queue.md:101`, `flow/flow-structure.md:46-86`

Page 7 stores the selected row as `selectedPromotion` (line 101), but this Flow value is not listed in the Flow Values table in `flow-structure.md:46-86`. The Flow Values table includes `selectedPeerReview` (line 70) and `selectedTestDeployment` (line 85), but no `selectedPromotion` for the Admin queue.

### m6: Page 5 Peer Review Queue Missing Environment/Hotfix Columns in Build Guide

**Severity:** Minor
**File:** `docs/build-guide/16-flow-dashboard-review-admin.md:14`

The build guide Step for Page 5 (line 14) lists columns: "Submitter, Process Name, Components count, Created/Updated counts, Submitted date, Status badge, Notes" — but omits the Environment and Hotfix columns that are specified in `flow/page-layouts/page5-peer-review-queue.md:46-47`. These columns were added as part of the multi-environment feature (Phase 7) and the build guide for the peer review section was not updated to reflect them.

### m7: Email Notification 6 (Test Deployment Complete) Not Triggered from Page 4

**Severity:** Minor
**Files:** `flow/flow-structure.md:475-492`, `flow/page-layouts/page4-deployment-submission.md`

`flow-structure.md` defines Email Notification 6 ("Test Deployed") but `page4-deployment-submission.md:17` only mentions "Simplified 'Deployed to Test' notification to submitter only" without formally referencing the email template from flow-structure.md. The two descriptions should be cross-linked.

### m8: Page 8 Missing Delete Confirmation

**Severity:** Minor
**File:** `flow/page-layouts/page8-mapping-viewer.md:606-619`

The delete mapping operation (`manageMappings` with `operation="delete"`) does not specify a confirmation modal. Other destructive actions (Page 7 Deny, Page 6 Reject) all have confirmation modals with required reason fields. Deleting a component mapping is a destructive action that could break future promotions if done accidentally.

**Recommendation:** Add a confirmation modal: "Are you sure you want to delete the mapping for {componentName}? This may affect future promotions from {devAccountName}."

---

## Observations

### O1: Well-Structured Multi-Environment Architecture

The three deployment modes (Test, Production from Test, Emergency Hotfix) are cleanly separated in Page 4's conditional rendering. The use of `targetEnvironment` and `isHotfix` as discriminators is elegant and avoids page duplication.

### O2: Comprehensive Self-Review Prevention

The dual-layer self-review prevention (backend exclusion in Process E2 + UI Decision step fallback) is a good defense-in-depth pattern. The specification correctly identifies this as a potential bypass vector and addresses it at both layers.

### O3: Strong Async Pattern with Flow Service Wait Responses

The specification correctly leverages Flow Service's built-in async handling (IndexedDB caching, wait responses) for long-running operations like `executePromotion`. The explicit note that users can close the browser and return later is important for UX.

### O4: XmlDiffViewer Custom Component Well-Integrated

The diff viewer is consistently specified across Pages 3, 6, and 7 with identical behavior (single panel open at a time, 500px max height, loading spinner, close button). The build guide (Step 5.5) provides clear registration steps.

### O5: Branch Age Warning is a Good Governance Feature

Page 9's branch age column with green/amber/red color coding and the stale branch warning banner provide visual governance without hard enforcement — appropriate for a team-based workflow.

---

## Multi-Environment Assessment

### Completeness of the 3-Path Architecture

| Path | Page Flow | Email | Branch Lifecycle | Assessed |
|------|-----------|-------|------------------|----------|
| Test | 1→2→3→4 (test deploy inline) | Email 6 (test complete) | Preserved | Complete |
| Production from Test | 9→4→5→6→7 (merge→deploy) | Email 1, 2/3, 4/5 | Deleted after merge+deploy or rejection | Complete |
| Emergency Hotfix | 1→2→3→4→5→6→7 (merge→deploy) | Email 7, 2/3, 4/5 | Deleted after merge+deploy or rejection | Complete |

### Gaps in Multi-Environment Flow

1. **No "Cancel Test Deployment" action on Page 9** — if a developer determines a test deployment is no longer needed, there is no mechanism to clean up the branch and mark the promotion as cancelled. The stale branch warning (30 days) is advisory only. A "Cancel" button with branch deletion would prevent branch accumulation.

2. **Branch limit handling** — the architecture references `BRANCH_LIMIT_REACHED` as an error code, but no page spec addresses what happens when the user hits the branch limit. Process C would return this error, but the Error Page does not provide specific guidance for this scenario (e.g., "Delete stale branches on Page 9 before retrying").

3. **Test-to-production gap — no re-validation** — when a developer selects a 30-day-old test deployment on Page 9, there is no warning that the main branch may have changed significantly since the test deployment. The merge (OVERRIDE strategy) will succeed, but the merged result may differ from what was tested. Consider adding a "Branch age exceeds 30 days — main branch may have changed since testing" warning modal before allowing production promotion.

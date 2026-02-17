# Contributor User Stories

**Role:** Contributor (`ABC_BOOMI_FLOW_CONTRIBUTOR`)
**Swimlane access:** Developer (Pages 1–4, 9) and Peer Review (Pages 5–6)
**Scope:** This document covers all Developer-path actions available to a Contributor. Peer-review actions (Pages 5–6) are documented separately.

---

## C-01: View Accessible Dev Accounts on Login

**As a** Contributor, **I want to** see the dev accounts I have permission to access when I open the dashboard, **so that** I can quickly choose which account to promote from without navigating elsewhere.

**Preconditions:**
- User is authenticated via Azure AD SSO
- User belongs to at least one `ABC_BOOMI_FLOW_DEVTEAM*` group and the `ABC_BOOMI_FLOW_CONTRIBUTOR` tier group
- DevAccountAccess records exist in DataHub mapping the user's team group(s) to dev account IDs

**Flow:**
1. User opens the Promotion Dashboard URL in a browser
2. The Developer swimlane verifies the user's SSO groups include `ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN`; otherwise denies access
3. Page 1 (Package Browser) loads and immediately executes the `getDevAccounts` message step
4. The request passes `userSsoGroups` from the SSO context; Process A0 resolves the user's `effectiveTier` and queries DevAccountAccess to build the list of accessible accounts
5. If only one account is returned, it is auto-selected, the Account Selector combobox is hidden, and `listDevPackages` fires automatically
6. If multiple accounts are returned, the Account Selector combobox is displayed with a "Choose a development account..." placeholder
7. The `userEffectiveTier` Flow value is set to `"CONTRIBUTOR"` or `"ADMIN"` for use in downstream UI decisions

**Acceptance Criteria:**
- [ ] User sees only the dev accounts mapped to their team group(s) in DevAccountAccess (CONTRIBUTOR tier)
- [ ] Admin users see all active dev accounts (tier bypass)
- [ ] If the user belongs to no valid tier group, `getDevAccounts` returns `success=false` with `errorCode=INSUFFICIENT_TIER` and the user is redirected to the Error Page
- [ ] Single-account users skip the combobox and land directly on the package list
- [ ] `userEffectiveTier` is correctly stored for downstream use

**Triggered API Calls:**
- `getDevAccounts` → Process A0

**Error Scenarios:**
- `INSUFFICIENT_TIER`: User lacks any dashboard-access tier group — Error Page shown with message and contact instructions
- `DATAHUB_ERROR`: DevAccountAccess query fails — Error Page shown with retry option

---

## C-02: Browse Packages in a Selected Dev Account

**As a** Contributor, **I want to** browse the packaged components available in a selected dev account, **so that** I can identify the correct package to promote.

**Preconditions:**
- User has reached Page 1 with at least one accessible account
- User has selected a dev account (or it was auto-selected)

**Flow:**
1. User selects a dev account from the Account Selector combobox (or auto-selection has occurred)
2. The `selectedDevAccountId` and `selectedDevAccountName` Flow values are set
3. `listDevPackages` fires with `devAccountId`
4. A loading spinner appears on the Packages Data Grid while the request executes
5. On success, the grid populates with packages sorted by Created date (newest first)
6. Each row shows: Package Name, Version, Type (color-coded badge), Created date, Notes
7. If the account has no packages, an empty-state message is shown: "No packages found in this account"
8. User can sort the grid by any sortable column (Package Name, Version, Type, Created)
9. User can search/filter the list client-side by name or type (optional enhancement)
10. User selects a row; the row highlights and the "Review for Promotion" button becomes enabled

**Acceptance Criteria:**
- [ ] Grid shows all packages from the selected dev account
- [ ] Grid is sorted by Created date descending by default
- [ ] Selecting a row enables the "Review for Promotion" button
- [ ] Changing the account selection refreshes the grid with packages from the new account
- [ ] Pagination activates when more than 50 packages exist (showing 50 per page)
- [ ] Loading spinner appears while `listDevPackages` executes

**Triggered API Calls:**
- `listDevPackages` → Process A

**Error Scenarios:**
- `ACCOUNT_NOT_FOUND`: Dev account ID is invalid — Error Page shown
- `AUTH_FAILED`: API token authentication failure — Error Page shown with contact-admin guidance
- `API_RATE_LIMIT`: Rate limit hit — inline retry banner shown

---

## C-03: Review Dependency Tree Before Promotion

**As a** Contributor, **I want to** see the full dependency tree for a selected package before executing a promotion, **so that** I understand which components will be created or updated and can catch problems early.

**Preconditions:**
- User has selected a package on Page 1
- `selectedPackage` and `selectedDevAccountId` Flow values are set

**Flow:**
1. User clicks "Review for Promotion" on Page 1
2. Page 2 (Promotion Review) loads and immediately calls `resolveDependencies` with `selectedPackage.componentId` and `selectedDevAccountId`
3. A "Analyzing dependencies..." spinner is shown during execution
4. On success, the Dependency Tree Data Grid populates (pre-sorted by type hierarchy: profiles → connections → operations → maps → processes)
5. Summary badges display: Total Components, N to create (blue), N to update (green), N with credentials to reconfigure (orange — shown if > 0), N shared connections pre-mapped (cyan)
6. Connection rows display with "(shared)" suffix; MAPPED connections show a cyan "MAPPED" badge; UNMAPPED connections show a red "UNMAPPED" badge
7. Rows with `hasEnvConfig=true` are highlighted in yellow/orange with a warning icon
8. User reviews the tree and notes which components are new vs. updating existing ones
9. If any unmapped connections exist, the "Promote to Primary Account" button is disabled with tooltip explaining the blocker

**Acceptance Criteria:**
- [ ] Dependency tree is shown in correct type-hierarchy order (not alphabetical)
- [ ] "NEW" vs "UPDATE" status is accurate for each component
- [ ] Shared connections show the MAPPED or UNMAPPED badge, not included in the promotable count
- [ ] Unmapped connections disable the Promote button with a descriptive tooltip
- [ ] Components with `hasEnvConfig=true` are visually highlighted
- [ ] Cancel button returns user to Page 1 without data loss
- [ ] Direct navigation to Page 2 without a selected package redirects to Page 1 with a toast message

**Triggered API Calls:**
- `resolveDependencies` → Process B

**Error Scenarios:**
- `DEPENDENCY_CYCLE`: Circular reference detected — Error Page shown with component names
- `COMPONENT_NOT_FOUND`: Root component not found in dev account — Error Page shown
- `MISSING_CONNECTION_MAPPINGS`: Returned at dependency-resolve time — unmapped connections surfaced in grid, Promote button disabled

---

## C-04: Execute Promotion to Create a Branch

**As a** Contributor, **I want to** execute the promotion so components are moved from my dev account to a branch in the primary account, **so that** reviewers can inspect the exact changes before anything merges to production.

**Preconditions:**
- User is on Page 2 with a valid dependency tree loaded
- No unmapped connections exist (`unmappedConnections` is empty)
- Account branch count is below the operational threshold (< 15)

**Flow:**
1. User clicks "Promote to Primary Account"
2. A confirmation modal appears showing the counts: components to create, components to update, components with credentials, shared connections
3. User clicks "Confirm Promotion" in the modal
4. The modal closes; the Promote button shows a spinner and "Promoting..." label and is disabled
5. A page-level overlay appears: "Promoting components to primary account... This may take several minutes."
6. The `executePromotion` message step fires with `componentId`, `selectedDevAccountId`, `dependencyTree`, and `userSsoGroups`
7. Process C validates the user's tier (defense-in-depth), creates a branch `promo-{promotionId}`, and promotes each component to the branch via tilde syntax
8. The Flow Service sends async wait responses; the user may safely close the browser — state is persisted via IndexedDB
9. On completion (success), Flow navigates to Page 3 (Promotion Status) with the results
10. On completion (failure), Flow navigates to the Error Page with `errorMessage`

**Acceptance Criteria:**
- [ ] Confirmation modal shows accurate counts before committing
- [ ] User can cancel from the confirmation modal without executing the promotion
- [ ] Async wait responses allow the user to close the browser and return later without losing progress
- [ ] On success, `promotionId`, `branchId`, `branchName`, `promotionResults`, `componentsCreated`, `componentsUpdated`, `componentsFailed` are all populated as Flow values
- [ ] On failure (any component fails), the branch is deleted; no partial state remains in the primary account
- [ ] `BRANCH_LIMIT_REACHED` is surfaced before the branch is created if the account has >= 15 active branches

**Triggered API Calls:**
- `executePromotion` → Process C

**Error Scenarios:**
- `BRANCH_LIMIT_REACHED`: >= 15 active branches in the account — Error Page; user must wait for pending reviews to complete or withdraw a promotion
- `MISSING_CONNECTION_MAPPINGS`: One or more connections lack mappings — Error Page listing missing mappings; admin must seed them via Mapping Viewer
- `INSUFFICIENT_TIER`: Process C detected the user's SSO groups are below CONTRIBUTOR — access denied
- `PROMOTION_FAILED`: One or more components failed — branch deleted; Error Page shows per-component results
- `CONCURRENT_PROMOTION`: Another promotion for this dev account is already IN_PROGRESS — Error Page

---

## C-05: View Component XML Diff After Promotion

**As a** Contributor, **I want to** inspect the side-by-side XML diff for any promoted component, **so that** I can verify the changes are correct before submitting for review.

**Preconditions:**
- User is on Page 3 (Promotion Status) with a successful promotion (`componentsFailed == 0`)
- `branchId` is populated in Flow state

**Flow:**
1. User sees the Results Data Grid with all promoted components
2. UPDATE rows show a "View Diff" link in the Changes column; CREATE rows show "View New"
3. User clicks "View Diff" on a desired component row
4. `generateComponentDiff` fires with `branchId`, `prodComponentId`, `componentName`, and `componentAction`
5. A loading spinner appears in the diff panel area below the grid
6. On success, the XmlDiffViewer custom component renders with side-by-side XML: LEFT = main branch (current production), RIGHT = promotion branch (proposed change)
7. Panel is scrollable (max-height 500px); a close button (X) dismisses it
8. Only one diff panel is open at a time — clicking another row closes the previous panel and opens a new one
9. For CREATE rows (`componentAction = "CREATE"`), `mainXml` is empty; the viewer shows only the new component XML on the right
10. User can close the panel and proceed to deployment submission

**Acceptance Criteria:**
- [ ] "View Diff" links appear only on SUCCESS rows (not FAILED or SKIPPED rows)
- [ ] Diff panel shows normalized, line-by-line XML comparison
- [ ] Branch version and main version numbers are displayed in the panel header
- [ ] CREATE components show empty left pane with a "New component" label
- [ ] Only one diff panel is open at a time
- [ ] Diff links are absent when `branchId` is missing (failed promotion)

**Triggered API Calls:**
- `generateComponentDiff` → Process G

**Error Scenarios:**
- `COMPONENT_NOT_FOUND`: Component not found on branch or main — inline error shown in diff panel area; user can dismiss and try another component
- `AUTH_FAILED`: API error fetching component XML — inline error shown

---

## C-06: Choose a Deployment Target

**As a** Contributor, **I want to** select whether to deploy components to a test environment or as an emergency hotfix directly to production, **so that** I can follow the appropriate workflow for my situation.

**Preconditions:**
- User is on Page 3 with a successful promotion (all components succeeded)
- The Deployment Target section is visible (hidden when any component fails)

**Flow:**
1. User scrolls to the Deployment Target section on Page 3
2. Two radio options are presented in card-style UI:
   - **"Deploy to Test" (default, pre-selected)** — green "(Recommended)" badge; sets `targetEnvironment="TEST"`, `isHotfix="false"`
   - **"Deploy to Production (Emergency Hotfix)"** — red "⚠ Emergency" badge; sets `targetEnvironment="PRODUCTION"`, `isHotfix="true"`
3. If user selects the Emergency Hotfix option:
   - A red warning banner slides in: "Emergency hotfixes bypass the test environment. This action will be logged for leadership review. Both peer review and admin review are still required."
   - A required "Hotfix Justification" textarea appears (max 1000 chars, with character counter)
   - User must provide justification text before continuing
4. If user selects Deploy to Test (or returns to it):
   - The warning banner and justification textarea disappear
5. User clicks "Continue to Deployment" to proceed to Page 4

**Acceptance Criteria:**
- [ ] "Deploy to Test" is pre-selected by default
- [ ] Emergency Hotfix selection reveals the warning banner and required justification textarea
- [ ] The "Continue to Deployment" button is blocked with a validation error if Emergency Hotfix is selected but `hotfixJustification` is empty
- [ ] Returning to "Deploy to Test" from "Emergency Hotfix" clears the warning and justification requirement
- [ ] `targetEnvironment` and `isHotfix` Flow values are correctly set before Page 4 loads

**Triggered API Calls:**
- None (UI-only state changes on Page 3)

**Error Scenarios:**
- `HOTFIX_JUSTIFICATION_REQUIRED`: Caught by client-side validation before API call; user sees inline error on the justification textarea

---

## C-07: Deploy Directly to Test Environment

**As a** Contributor, **I want to** deploy my promoted components directly to a test Integration Pack without requiring peer or admin review, **so that** I can validate the changes in a safe environment before requesting production approval.

**Preconditions:**
- User is on Page 4 in Test mode (`targetEnvironment="TEST"`)
- Promotion was successful (all components on branch); `branchId` is present
- Required form fields are filled: Package Version, Integration Pack (filtered to test packs), Target Account Group

**Flow:**
1. Page 4 loads with the header "Deploy to Test Environment" and a blue info banner: "Components will be deployed to your Test Integration Pack. No reviews required."
2. On page load, `listIntegrationPacks` fires with `packPurpose="TEST"` to populate the Integration Pack combobox with test packs only
3. If a suggested pack is found (most recently used for this process in test), it is pre-selected in the combobox
4. User fills in or confirms: Package Version, Integration Pack (select existing or create new), Target Account Group, optional Deployment Notes
5. User clicks "Deploy to Test"
6. Client-side validation runs; if any required field is empty, errors are shown and execution stops
7. `packageAndDeploy` fires with `deploymentTarget="TEST"`, `isHotfix=false`, the form data, and `branchId`
8. Process D merges the promotion branch to main (OVERRIDE), creates a PackagedComponent, creates/updates the Test Integration Pack, releases it, deploys to the test environment, and **preserves the branch** for future production review
9. On success, inline results appear: green banner "Successfully deployed to Test Integration Pack: {testIntegrationPackName}", branch-preserved message, and navigation buttons
10. A "Test Deployed" email notification is sent to the submitter only
11. `status` is updated to `TEST_DEPLOYED` in PromotionLog

**Acceptance Criteria:**
- [ ] Integration Pack combobox is filtered to test packs only (packs with "- TEST" suffix)
- [ ] Suggested pack is auto-selected if available from PromotionLog history
- [ ] "Deploy to Test" button triggers `packageAndDeploy` with `deploymentTarget="TEST"` — no swimlane transition occurs
- [ ] On success, branch is preserved (`branchPreserved=true` in response) and user is informed
- [ ] "View in Production Readiness" button navigates to Page 9
- [ ] "Return to Dashboard" button navigates to Page 1
- [ ] Submitter receives a "Test Deployed" email notification

**Triggered API Calls:**
- `listIntegrationPacks` → Process J (page load)
- `packageAndDeploy` → Process D (on submit)

**Error Scenarios:**
- `TEST_DEPLOY_FAILED`: Test environment deployment failed — red inline banner with error details and "Retry" button
- `MERGE_FAILED`: Branch merge failed — red inline banner; user should retry or contact admin
- `MERGE_TIMEOUT`: Merge did not complete within 60 seconds — red inline banner with timeout message
- `PROMOTION_NOT_COMPLETED`: PromotionLog status gate failed — Error Page shown

---

## C-08: Submit Promotion for Peer Review (Standard Path)

**As a** Contributor, **I want to** submit my promotion for peer review after a successful test deployment, **so that** a qualified team member can validate the changes before they are deployed to production.

**Preconditions:**
- User is on Page 4 in Production-from-Test mode (`targetEnvironment="PRODUCTION"`, `testPromotionId` populated)
- The promotion has `TEST_DEPLOYED` status in PromotionLog
- `branchId` is present (preserved from the test phase)

**Flow:**
1. Page 4 loads from Page 9 (Production Readiness) with the header "Submit for Production Deployment"
2. A green info banner states: "This deployment was previously validated in the test environment."
3. A read-only "Previously Tested Deployment" panel shows: test deployed date, test Integration Pack name, promotion ID, and component counts
4. On page load, `listIntegrationPacks` fires with `packPurpose="PRODUCTION"` to populate the Integration Pack combobox with production packs only
5. User fills in or confirms: Package Version, Integration Pack (select existing production pack or create new), Target Account Group, optional Deployment Notes
6. User clicks "Submit for Peer Review"
7. Client-side validation runs; if any required field is empty, errors are shown and execution stops
8. A "Peer Review Needed" email is sent to the Dev + Admin distribution lists; submitter is CC'd
9. Flow transitions to the Peer Review swimlane (pauses at the swimlane boundary)
10. Developer sees a confirmation message: "Submitted for peer review! You will receive email notifications as the review progresses." with the Promotion ID displayed
11. Developer clicks "Close" to end their part of the flow

**Acceptance Criteria:**
- [ ] Integration Pack combobox shows only production packs (no "- TEST" packs)
- [ ] Test deployment summary panel is shown (read-only)
- [ ] Submitting triggers a "Peer Review Needed" email notification to dev + admin groups
- [ ] Flow pauses at the Developer-to-Peer-Review swimlane boundary
- [ ] Confirmation message displays the Promotion ID for reference
- [ ] "Close" button ends the developer's session cleanly

**Triggered API Calls:**
- `listIntegrationPacks` → Process J (page load)
- Flow swimlane transition (built-in Flow mechanism, no additional FSS call)

**Error Scenarios:**
- Form validation failure: Required fields highlighted; user cannot proceed until resolved
- `PROMOTION_NOT_COMPLETED`: PromotionLog gate fails (promotion not in TEST_DEPLOYED status) — Error Page

---

## C-09: Submit Emergency Hotfix for Peer Review

**As a** Contributor, **I want to** submit an emergency hotfix for peer and admin review, skipping the test environment, **so that** critical production issues can be resolved quickly while still maintaining the required approval chain.

**Preconditions:**
- User has completed a successful promotion (Page 3)
- User selected "Deploy to Production (Emergency Hotfix)" on Page 3 and provided a hotfix justification
- `targetEnvironment="PRODUCTION"`, `isHotfix="true"`, `hotfixJustification` is non-empty

**Flow:**
1. Page 4 loads with the header "Submit Emergency Hotfix for Peer Review"
2. A prominent red warning banner is displayed: "⚠ EMERGENCY HOTFIX: This deployment bypasses the test environment. Both peer review and admin review are required."
3. A read-only "Emergency Hotfix Justification" panel shows the justification text entered on Page 3 (with a red left border)
4. On page load, `listIntegrationPacks` fires with `packPurpose="PRODUCTION"`; the combobox is populated with production packs
5. User fills in: Package Version, Integration Pack, Target Account Group, optional additional Deployment Notes
6. User clicks "Submit Emergency Hotfix for Peer Review" (red/danger styled button)
7. Form validation runs; errors shown if required fields are missing
8. A special "⚠ EMERGENCY HOTFIX — Peer Review Needed" email is sent to the Dev + Admin distribution lists (CC: submitter), including the hotfix justification
9. Flow transitions to the Peer Review swimlane
10. Developer sees a confirmation message and clicks "Close"

**Acceptance Criteria:**
- [ ] The hotfix justification from Page 3 is displayed read-only on Page 4
- [ ] The submit button is labeled "Submit Emergency Hotfix for Peer Review" with danger styling
- [ ] Emergency hotfix email subject includes "⚠ EMERGENCY HOTFIX"
- [ ] Email body includes the full hotfix justification text
- [ ] `isHotfix="true"` is carried through to the `packageAndDeploy` call at the admin approval stage
- [ ] `hotfixJustification` is logged in PromotionLog (`isHotfix="true"`, `hotfixJustification` field)

**Triggered API Calls:**
- `listIntegrationPacks` → Process J (page load)
- Flow swimlane transition (built-in Flow mechanism)

**Error Scenarios:**
- `HOTFIX_JUSTIFICATION_REQUIRED`: Caught at Page 3 before reaching Page 4; user must provide justification before proceeding
- Form validation failure on Page 4: Required fields highlighted

---

## C-10: View Test Deployments Ready for Production

**As a** Contributor, **I want to** see all my test deployments that have been validated and are ready to promote to production, **so that** I can track which components are waiting for the next step in the workflow.

**Preconditions:**
- User is authenticated as Contributor or Admin
- At least one promotion exists in `TEST_DEPLOYED` status that has not yet been promoted to production

**Flow:**
1. User navigates to Page 9 (Production Readiness) — accessible from the dashboard menu, from Page 4 after a test deployment, or from Page 1 via a "Tested Deployments" link
2. On load, `queryTestDeployments` fires (optionally filtered by `devAccountId` or `initiatedBy`)
3. The Production Readiness Data Grid populates with all TEST_DEPLOYED promotions not yet promoted to production, sorted by `testDeployedAt` descending (most recent first)
4. Each row shows: Process Name, Package Version, Test Deployed timestamp, Branch Age (color-coded: green 0–14d, amber 15–30d, red > 30d), Component counts, Test Integration Pack name, Submitted By
5. If any deployment has Branch Age > 30 days, a stale branch warning banner appears at the top of the page
6. User can click "Refresh" to re-execute `queryTestDeployments` and see the latest data
7. User selects a row; the row highlights and an expandable detail panel appears below the grid
8. The detail panel shows: Promotion ID (copyable), Process Name, Package Version, Submitted by, Submitted at, Test Deployed timestamp, Test Integration Pack, Branch Name (active), component counts

**Acceptance Criteria:**
- [ ] Only TEST_DEPLOYED promotions that have NOT been promoted to production are shown
- [ ] Grid is sorted by test deployment date descending by default
- [ ] Branch Age column uses correct color coding (green/amber/red thresholds)
- [ ] Stale branch warning appears when any entry has Branch Age > 30 days
- [ ] Selecting a row reveals the full detail panel
- [ ] Refresh button re-queries the API and updates the grid
- [ ] Empty state message appears when no test deployments are ready

**Triggered API Calls:**
- `queryTestDeployments` → Process E4

**Error Scenarios:**
- `DATAHUB_ERROR`: PromotionLog query fails — Error Page shown
- `AUTH_FAILED`: API error — Error Page shown

---

## C-11: Promote a Tested Deployment to Production

**As a** Contributor, **I want to** initiate the production promotion for a test-validated deployment, **so that** I can start the peer review and admin approval process for moving components to the production environment.

**Preconditions:**
- User is on Page 9 with a test deployment selected
- The selected deployment is in `TEST_DEPLOYED` status
- `branchId` is preserved from the test deployment phase

**Flow:**
1. User selects a test deployment row on Page 9
2. The detail panel expands showing test deployment info, including the preserved branch name
3. User clicks "Promote to Production"
4. Flow values are set: `testPromotionId`, `targetEnvironment="PRODUCTION"`, `isHotfix="false"`, `branchId`, `branchName`, `testIntegrationPackId`, `testIntegrationPackName`, plus carried-forward `promotionId`, `processName`, `packageVersion`, `componentsTotal`, `componentsCreated`, `componentsUpdated`
5. Flow navigates to Page 4 (Deployment Submission) in Production-from-Test mode
6. Page 4 shows the "Submit for Production Deployment" header, a test deployment summary panel, and the production pack selector
7. User fills in deployment details and submits for peer review (see C-08)

**Acceptance Criteria:**
- [ ] "Promote to Production" button is only enabled when a row is selected
- [ ] All required Flow values (especially `testPromotionId`, `branchId`) are set before navigating to Page 4
- [ ] Page 4 correctly enters Production-from-Test mode (not Test mode or Hotfix mode)
- [ ] The test deployment summary panel on Page 4 reflects the selected deployment's details
- [ ] Integration Pack combobox on Page 4 shows only production packs (not test packs)

**Triggered API Calls:**
- None on Page 9 click; `listIntegrationPacks` and swimlane transition occur on Page 4

**Error Scenarios:**
- `TEST_PROMOTION_NOT_FOUND`: `testPromotionId` references a non-existent or non-TEST_DEPLOYED record — Error Page on Page 4

---

## C-12: Cancel a Stale Test Deployment

**As a** Contributor, **I want to** cancel a stale test deployment that I no longer intend to promote to production, **so that** the associated promotion branch is cleaned up and the branch slot is freed for other promotions.

**Preconditions:**
- User is on Page 9 with a test deployment selected
- The selected deployment is in `TEST_DEPLOYED` status (not already cancelled or deployed)

**Flow:**
1. User selects a stale test deployment row on Page 9 (typically shown in red due to Branch Age > 30 days)
2. A "Cancel Test Deployment" button is available in the footer action bar or detail panel
3. User clicks "Cancel Test Deployment"
4. A confirmation dialog appears: "This will cancel the test deployment for **{processName}** and delete the test branch. This action cannot be undone."
5. User confirms the cancellation
6. `cancelTestDeployment` fires with `promotionId` from the selected deployment
7. Process E4 validates the promotion is in `TEST_DEPLOYED` status, deletes the preserved test branch (idempotent — 404 treated as success), and updates PromotionLog to `TEST_CANCELLED`
8. On success, the row is removed from the grid and a toast notification: "Test deployment cancelled successfully"
9. On failure, an error toast is shown with `errorMessage` and the row remains in place

**Acceptance Criteria:**
- [ ] Cancel button is available for any selected TEST_DEPLOYED row
- [ ] Confirmation dialog prevents accidental cancellation
- [ ] On success, the row is removed from the grid and a success toast is shown
- [ ] On success, the promotion branch is deleted and the branch slot is freed
- [ ] PromotionLog status is updated to `TEST_CANCELLED`
- [ ] If the branch was already absent (404), the cancellation still succeeds

**Triggered API Calls:**
- `cancelTestDeployment` → Process E4

**Error Scenarios:**
- `PROMOTION_NOT_FOUND`: Invalid `promotionId` — error toast shown
- `INVALID_PROMOTION_STATUS`: Promotion is not in `TEST_DEPLOYED` status (may have been promoted or already cancelled) — error toast shown with current status; grid refresh recommended

---

## C-13: Withdraw a Pending Promotion

**As a** Contributor, **I want to** withdraw one of my pending promotions (awaiting peer or admin review), **so that** I can retract a submission I no longer want to proceed with and free the associated branch slot.

**Preconditions:**
- User has at least one active promotion in `PENDING_PEER_REVIEW` or `PENDING_ADMIN_REVIEW` status
- The user is the original initiator of the promotion (`initiatedBy` matches `$User/Email`)

**Flow:**
1. User arrives at Page 1 (Package Browser) and sees the "Your Active Promotions" collapsible panel (shown only when `activePromotions` is non-empty)
2. Page 1 load queries `queryStatus` for `PENDING_PEER_REVIEW` and `PENDING_ADMIN_REVIEW`, filters results to records where `initiatedBy.toLowerCase() == $User/Email.toLowerCase()`, and stores them as `activePromotions`
3. The panel shows a grid with: Package Name, Dev Account, Status badge (amber for PENDING_PEER_REVIEW, blue for PENDING_ADMIN_REVIEW), Submitted (relative time), Components, Withdraw button
4. User clicks "Withdraw" on a promotion row
5. A confirmation dialog appears:
   - Title: "Withdraw Promotion?"
   - Message: "This will cancel the promotion for **{processName}** and delete the promotion branch. This action cannot be undone."
   - Optional textarea: "Reason for withdrawal (optional)" — max 500 characters
   - Buttons: "Cancel" | "Withdraw" (destructive/red)
6. User fills in an optional reason and clicks "Withdraw"
7. `withdrawPromotion` fires with `promotionId`, `initiatorEmail` from `$User/Email`, and the optional reason
8. Process E5 validates the status is `PENDING_PEER_REVIEW` or `PENDING_ADMIN_REVIEW`, validates the initiator email matches (case-insensitive), deletes the promotion branch, and updates PromotionLog to `WITHDRAWN`
9. On success: the row is removed from the `activePromotions` panel, a success toast appears: "Promotion withdrawn successfully"
10. On failure: an error toast appears with `errorMessage`; the row remains in place

**Acceptance Criteria:**
- [ ] The "Your Active Promotions" panel is shown only when the user has at least one pending promotion
- [ ] Only the user's own promotions appear in the panel (filtered by `initiatedBy`)
- [ ] Confirmation dialog shows the process name and warns the action is irreversible
- [ ] The reason field is optional (up to 500 characters)
- [ ] On success, the row is removed from the panel and a success toast is shown
- [ ] On success, the promotion branch is deleted and PromotionLog status is `WITHDRAWN`
- [ ] On failure, the row remains and an error toast is shown
- [ ] If the user is not the initiator (e.g., navigating directly via API), Process E5 rejects with `NOT_PROMOTION_INITIATOR`

**Triggered API Calls:**
- `queryStatus` (×2, parallelized) → Process E (page 1 load)
- `withdrawPromotion` → Process E5 (on withdraw confirm)

**Error Scenarios:**
- `NOT_PROMOTION_INITIATOR`: The user's email does not match `initiatedBy` — error toast
- `INVALID_PROMOTION_STATUS`: Promotion is not in a withdrawable state (e.g., already peer-approved or deployed) — error toast with current status
- `PROMOTION_NOT_FOUND`: Invalid `promotionId` — error toast

---

## C-14: Handle Errors and Recover

**As a** Contributor, **I want to** be shown clear error information when something goes wrong, with options to retry, go back, or start over, **so that** I am not stranded on a dead-end screen with no path forward.

**Preconditions:**
- A Message step has returned `success=false`
- OR a permanent error (e.g., `MISSING_CONNECTION_MAPPINGS`, `BRANCH_LIMIT_REACHED`) has occurred

**Flow:**
1. A Message step (e.g., `executePromotion`) returns `success=false`
2. A Decision step evaluates `responseObject.success == true`; the false path leads to the Error Page
3. The Error Page displays:
   - A large error icon
   - "An error occurred" heading
   - The `errorMessage` from the response (human-readable)
   - A collapsible "Technical Details" section with the full error code and stack trace (for debugging/support)
4. Three action buttons are available:
   - **Back:** Returns to the previous page using Flow history navigation
   - **Retry:** Re-executes the failed Message step with the same input values
   - **Home:** Returns to Page 1 (Package Browser)
5. For specific errors, contextual guidance is also shown:
   - `MISSING_CONNECTION_MAPPINGS`: "Ask an admin to seed the missing mappings in the Mapping Viewer"
   - `BRANCH_LIMIT_REACHED`: "Wait for pending reviews to complete or withdraw a promotion to free a branch slot"
   - `DATAHUB_ERROR`: "Contact your platform administrator"
6. For transient errors (network timeout, HTTP 429), an inline retry banner is shown rather than a full redirect to the Error Page

**Acceptance Criteria:**
- [ ] All failed Message steps route to the Error Page via Decision steps
- [ ] The Error Page shows the `errorMessage` from the failed step
- [ ] "Back", "Retry", and "Home" buttons are all functional
- [ ] The Technical Details section is collapsed by default
- [ ] Transient errors (429, 5xx) show an inline retry banner rather than the Error Page
- [ ] Permanent errors (4xx except 429) route to the Error Page
- [ ] Every error state offers at least one navigation path so the user is never stranded

**Triggered API Calls:**
- Retry re-executes the specific failed Message step

**Error Scenarios:**
- All error codes listed in the Flow Service error contract can appear on this page; see `integration/flow-service/flow-service-spec.md` for the full list

---

## C-15: Receive Email Notifications About Promotion Lifecycle

**As a** Contributor, **I want to** receive email notifications at key stages of my promotion's lifecycle, **so that** I always know the current status of my submission without having to constantly check the dashboard.

**Preconditions:**
- User has submitted a promotion for peer review or test deployment
- Email distribution lists are configured in the Boomi Flow application

**Flow:**
1. **On test deployment completion (Test path):**
   - Submitter receives "Test Deployed: {processName} v{packageVersion}" email
   - Includes: Promotion ID, test Integration Pack name, deployed timestamp, branch name, and a note to return to Production Readiness when ready
2. **On peer review submission (standard or hotfix):**
   - Dev + Admin distribution lists receive "Peer Review Needed" (or "⚠ EMERGENCY HOTFIX — Peer Review Needed") email
   - Submitter is CC'd for confirmation
3. **On peer review rejection:**
   - Submitter receives "Peer Review Rejected: {processName} v{packageVersion}" email
   - Includes: reviewer name/email, decision (REJECTED), and the rejection reason (required for rejections)
4. **On admin approval and deployment:**
   - Submitter receives "Approved & Deployed: {processName} v{packageVersion}" email
   - Includes: Promotion ID, Deployment ID, prod package ID, peer reviewer info, admin approver info, admin comments
5. **On admin denial:**
   - Submitter receives "Admin Denied: {processName} v{packageVersion}" email
   - Includes: Promotion ID, admin denier info, denial reason

**Acceptance Criteria:**
- [ ] Test deployment email is sent only to the submitter (not to distribution lists)
- [ ] Peer review submission email is sent to dev + admin distribution lists; submitter is CC'd
- [ ] Peer rejection email is sent to the submitter only and includes the rejection reason
- [ ] Admin approval email includes the Deployment ID and prod package ID
- [ ] Admin denial email includes the denial reason
- [ ] Emergency hotfix submission email subject includes "⚠ EMERGENCY HOTFIX" and body includes the hotfix justification
- [ ] No email is sent when `withdrawPromotion` completes (withdrawal is a silent operation from the reviewer's perspective)

**Triggered API Calls:**
- Emails are sent by Flow at swimlane boundaries and by Process D at deployment completion

**Error Scenarios:**
- Email delivery failure is non-blocking — the workflow continues even if email notification fails; the failure should be logged in Boomi Process Reporting

---

## C-16: Re-run a Failed Promotion

**As a** Contributor, **I want to** easily navigate back to the Package Browser and re-run a promotion after fixing the root cause of a failure, **so that** I don't have to manually hunt for the package again.

**Preconditions:**
- User is on Page 3 (Promotion Status) and `componentsFailed > 0`

**Flow:**
1. The Promotion Failed Banner is displayed above the Results Data Grid (red background, "Promotion Failed" heading)
2. The banner shows the failure count, explains that the promotion branch has been deleted and no changes were applied
3. A "Common Failure Causes" collapsible section is available for self-service diagnosis
4. A "Return to Package Browser" button is shown in the banner
5. User addresses the root cause (e.g., fixes the component in the dev account, asks admin to seed missing mappings)
6. User clicks "Return to Package Browser" and navigates back to Page 1
7. User re-selects the same package and runs through the promotion flow again

**Acceptance Criteria:**
- [ ] The Promotion Failed Banner appears when `componentsFailed > 0`
- [ ] The banner accurately reports how many components failed out of the total
- [ ] The banner explicitly states that the branch was deleted and no prod changes occurred
- [ ] The "Return to Package Browser" button correctly navigates to Page 1
- [ ] The "Submit for Deployment" button is disabled (grayed out) when `componentsFailed > 0`
- [ ] The "Done" button remains accessible at all times as an alternative exit

**Triggered API Calls:**
- None (navigation action only)

**Error Scenarios:**
- N/A (this story is the recovery path for failed promotions)

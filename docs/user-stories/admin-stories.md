# Admin User Stories

These user stories cover the Admin role (`ABC_BOOMI_FLOW_ADMIN`) in the Boomi Dev-to-Prod Component Promotion System. Admins serve as the final approval gate in the 2-layer approval workflow and are also responsible for managing component mappings and system configuration. Admins inherit full access to the Developer and Peer Review swimlanes in addition to their Admin-exclusive capabilities.

---

## Admin Approval Queue (Page 7)

### A-01: View Pending Approval Queue

**As an** Admin, **I want to** see all promotions that have passed peer review and are awaiting my final approval, **so that** I can prioritize and process deployment requests efficiently.

**Preconditions:**
- User is authenticated with `ABC_BOOMI_FLOW_ADMIN` SSO group membership
- At least one promotion has `peerReviewStatus = PEER_APPROVED` and `adminReviewStatus = PENDING_ADMIN_REVIEW`

**Flow:**
1. Admin receives email notification: "Peer Approved — Admin Review Needed: {processName} v{packageVersion}"
2. Admin authenticates via SSO — `ABC_BOOMI_FLOW_ADMIN` group membership is validated
3. Admin navigates to Page 7 (Admin Approval Queue)
4. System calls `queryStatus` with `status = "COMPLETED"`, `deployed = false`, `reviewStage = "PENDING_ADMIN_REVIEW"`
5. Page loads the Approval Queue Data Grid, sorted newest first
6. Each row shows: Submitter, Process Name, Components count, Created/Updated breakdown, Peer Reviewed By, Submitted timestamp, Environment badge, Hotfix badge (if applicable), Notes (truncated)
7. If no items are pending, the grid shows "No pending approvals — All deployment requests have been processed."

**Acceptance Criteria:**
- [ ] Page 7 is only accessible to users with `ABC_BOOMI_FLOW_ADMIN` group membership; non-admins see "Access denied. This page requires admin privileges."
- [ ] Grid only shows promotions with `peerReviewStatus = PEER_APPROVED` and `adminReviewStatus = PENDING_ADMIN_REVIEW`
- [ ] Rows are sorted by `initiatedAt` descending by default
- [ ] Emergency hotfix rows display a prominent red "EMERGENCY HOTFIX" badge
- [ ] Empty state shows the "No pending approvals" message with a descriptive sub-message
- [ ] Grid paginates at 25 rows per page when more than 25 items exist

**Triggered API Calls:**
- `queryStatus` → Process E (with `reviewStage = "PENDING_ADMIN_REVIEW"` filter)

**Error Scenarios:**
- `queryStatus` failure: Navigate to Error Page with error message

---

### A-02: Review Promotion Details Before Approving

**As an** Admin, **I want to** view full submission details, peer review information, and component-level results for a pending promotion, **so that** I can make an informed approval decision.

**Preconditions:**
- Admin is on Page 7 with at least one pending approval visible in the queue

**Flow:**
1. Admin clicks on a row in the Approval Queue Data Grid
2. The row highlights and the Promotion Detail Panel expands below the grid
3. Admin reviews Section 1 — Submission Details:
   - Submitted by (email), submitted at (timestamp), Promotion ID (with copy button)
   - Package version, Integration Pack name, target account group
   - Deployment notes from the submitter
4. Admin reviews Section 2 — Peer Review Information:
   - Reviewer name and email, review timestamp, PEER_APPROVED badge
   - Peer review comments
5. Admin reviews Section 2b — Environment / Hotfix Information (if applicable):
   - For hotfix promotions: large red "EMERGENCY HOTFIX" banner with the submitter's justification text
   - For production-from-test: "Test Environment Validation" panel showing test promotion ID, test deployed date, and test Integration Pack name
6. Admin reviews Section 3 — Promotion Results:
   - Component-level table (name, action CREATE/UPDATE, status, config stripped indicator, "View Diff" / "View New" link)
   - Summary: Total, Created, Updated, Failed counts
7. Admin reviews Section 4 — Credential Warning (if any components have `configStripped = true`):
   - List of components requiring credential reconfiguration after deployment
8. Admin reviews Section 5 — Source Account (dev account name and ID)

**Acceptance Criteria:**
- [ ] Detail panel expands upon row selection and collapses when deselected
- [ ] All submission details fields are populated from `selectedPromotion` data
- [ ] Peer review section shows reviewer identity, timestamp, decision badge, and comments
- [ ] Hotfix banner (red, with justification) is displayed only when `isHotfix = "true"`
- [ ] Test environment validation panel is displayed only when `testPromotionId` is populated
- [ ] Component results table includes "View Diff" and "View New" links per component
- [ ] Credential warning section appears when any component has `configStripped = true`
- [ ] Promotion ID field includes a copy-to-clipboard button

**Triggered API Calls:**
- (No new API call — detail panel populates from data already loaded by `queryStatus`)

**Error Scenarios:**
- If `selectedPromotion` is missing expected fields, surface a UI warning rather than silently omitting sections

---

### A-03: View Component XML Diff Before Approving

**As an** Admin, **I want to** see a side-by-side XML diff of each changed component (branch vs. main), **so that** I can review the exact code changes before authorizing the merge and deployment.

**Preconditions:**
- Admin has selected a promotion on Page 7 and the detail panel is expanded
- The component results table shows at least one component with a "View Diff" or "View New" link

**Flow:**
1. Admin clicks "View Diff" (for an UPDATE component) or "View New" (for a CREATE component) in the component results table
2. System displays a loading spinner
3. System calls `generateComponentDiff` with `branchId`, `prodComponentId`, `componentName`, and `componentAction`
4. On success: the XmlDiffViewer custom component renders inline below Section 3
   - Left panel: main branch XML (empty for CREATE)
   - Right panel: promotion branch XML
   - Line-by-line diff highlighting (added/removed/changed lines)
   - Max height 500px with scroll; close button (X) in top-right
5. Admin reads the diff to understand what will be merged to main
6. Admin closes the diff panel by clicking X before proceeding to approve or deny
7. Only one diff panel is open at a time; clicking another "View Diff" replaces the current panel

**Acceptance Criteria:**
- [ ] Clicking "View Diff" triggers `generateComponentDiff` with the correct `branchId` from the promotion record
- [ ] XmlDiffViewer renders with branch XML on the right, main XML on the left
- [ ] For CREATE actions, `diffMainXml` is empty and the viewer shows only the new component XML
- [ ] Only one diff panel is open at a time; opening a second closes the first
- [ ] The diff panel is scrollable and capped at 500px height
- [ ] The close button (X) collapses the diff panel
- [ ] `branchVersion` and `mainVersion` are displayed (mainVersion shows "0" for CREATE)

**Triggered API Calls:**
- `generateComponentDiff` → Process G

**Error Scenarios:**
- `COMPONENT_NOT_FOUND`: Display "Component not found in branch" error inline in the diff panel
- `generateComponentDiff` network/API failure: Show error inline in the diff panel without blocking the rest of the page

---

### A-04: Approve and Deploy a Promotion

**As an** Admin, **I want to** approve a peer-reviewed promotion and trigger the full merge-package-deploy pipeline, **so that** promoted components are deployed to the production Integration Pack.

**Preconditions:**
- Admin has selected a promotion on Page 7 and reviewed the details
- The promotion is not submitted by the same admin (self-approval prevention)
- Admin Comments textarea is optionally filled

**Flow:**
1. Admin (optionally) enters comments in the "Admin Comments" textarea (max 500 characters)
2. Admin clicks "Approve and Deploy" (green button, right-aligned in footer)
3. Confirmation modal appears:
   - Shows: Process name, Package version, Target Account Group, Total Components
   - For hotfix promotions: additional red warning text and a mandatory acknowledgment checkbox
4. Admin clicks "Confirm Approval" (hotfix: must check the acknowledgment checkbox first)
5. Modal closes; system begins the approval pipeline:
   - Step 1: `POST /MergeRequest` with `strategy = "OVERRIDE"` and `priorityBranch = branchId`; store `mergeRequestId`
   - Step 2: `POST /MergeRequest/execute/{mergeRequestId}` with `action = "MERGE"`; poll until `stage = "MERGED"`; spinner shows "Merging branch to main..."
   - Step 3: Message step `packageAndDeploy` runs from main (creates PackagedComponent, Integration Pack, deploys to target account group)
   - Step 4: `DELETE /Branch/{branchId}`; PromotionLog `branchId` set to null
6. On success:
   - Success message: "Branch merged, packaged, and deployed successfully!"
   - Deployment ID and prod package ID displayed
   - Email notification sent to submitter and peer reviewer
   - Approval queue refreshes; approved item removed; detail panel cleared
7. "Approve and Deploy" and "Deny" buttons are enabled only when a promotion is selected

**Acceptance Criteria:**
- [ ] "Approve and Deploy" button is disabled when no promotion is selected
- [ ] Confirmation modal is shown before any action is taken
- [ ] For hotfix promotions, the modal includes a mandatory acknowledgment checkbox that must be checked before "Confirm Approval" is enabled
- [ ] Merge uses OVERRIDE strategy with `priorityBranch` set to the promotion branch
- [ ] `packageAndDeploy` is called after a successful merge (not before)
- [ ] Branch is deleted after successful deployment; PromotionLog `branchId` set to null
- [ ] Email notification is sent to submitter + peer reviewer on successful deployment
- [ ] Approval queue refreshes after successful deployment
- [ ] On `packageAndDeploy` failure, an error message is shown and the branch may persist for retry

**Triggered API Calls:**
- `POST /MergeRequest` (Platform API — OVERRIDE merge)
- `POST /MergeRequest/execute/{mergeRequestId}` (Platform API — execute merge)
- `packageAndDeploy` → Process D
- `DELETE /Branch/{branchId}` (Platform API — branch cleanup)

**Error Scenarios:**
- Merge request failure (`POST /MergeRequest` returns error): Show error message; no deployment occurs; branch preserved
- Merge execution timeout: Show "Merge is taking longer than expected" warning with retry option
- `packageAndDeploy` failure: Show error with details; branch may still exist; admin can retry
- Branch deletion failure: Log warning; proceed as deployment is already complete

---

### A-05: Deny a Promotion with Reason

**As an** Admin, **I want to** deny a peer-reviewed promotion and provide a written reason, **so that** the submitter understands what needs to change before resubmitting.

**Preconditions:**
- Admin has selected a promotion on Page 7
- The promotion is not submitted by the same admin (self-approval prevention)

**Flow:**
1. Admin clicks "Deny" (red button, left-aligned in footer)
2. A denial modal appears with a required "Reason for Denial" textarea (max 500 characters)
3. Admin types a clear explanation of why the promotion was denied
4. Admin clicks "Confirm Denial"
5. System:
   - Updates PromotionLog `adminReviewStatus` to "DENIED"
   - Records denial reason, `adminUserEmail`, and denial timestamp
   - Calls `DELETE /Branch/{branchId}` to clean up the promotion branch (main is untouched)
   - Updates PromotionLog: `branchId` set to null
   - Sends email notification to submitter and peer reviewer with subject "Admin Denied: {processName} v{packageVersion}" and full denial reason
6. Queue refreshes; denied item is removed; confirmation toast: "Deployment request denied. Submitter has been notified."

**Acceptance Criteria:**
- [ ] "Deny" button is disabled when no promotion is selected
- [ ] The denial modal requires a non-empty reason text before "Confirm Denial" is enabled
- [ ] Reason text is limited to 500 characters with a character counter
- [ ] Branch is deleted on denial; main is never modified
- [ ] PromotionLog `branchId` is set to null after branch deletion
- [ ] Email notification sent to submitter and peer reviewer includes the full denial reason
- [ ] Approval queue refreshes after denial; denied item is removed

**Triggered API Calls:**
- `DELETE /Branch/{branchId}` (Platform API — branch cleanup)
- (Status update to PromotionLog is handled internally by `packageAndDeploy` process or a direct DH write)

**Error Scenarios:**
- Branch deletion failure: Log warning; still mark PromotionLog as DENIED and notify submitter
- Email notification failure: Log warning; display confirmation to admin that denial was recorded even if email was not sent

---

### A-06: Self-Approval Prevention

**As an** Admin, **I want to** be blocked from approving promotions that I personally submitted, **so that** the independence of the 2-layer approval workflow is maintained.

**Preconditions:**
- Admin is on Page 7 and selects a promotion row where `initiatedBy` matches their own email

**Flow:**
1. Admin selects a row in the Approval Queue Data Grid
2. System evaluates a Decision step: `LOWERCASE($User/Email)` == `LOWERCASE(selectedPromotion.initiatedBy)`
3. If match (same person): Display inline error banner: "You cannot approve your own promotion. Please ask another admin to review."
4. "Approve and Deploy" and "Deny" buttons remain disabled
5. The Promotion Detail Panel may still be shown in read-only mode for informational purposes
6. Admin must ask a different admin to process this promotion

**Acceptance Criteria:**
- [ ] Decision step comparison is case-insensitive
- [ ] "Approve and Deploy" and "Deny" buttons are disabled when self-approval would occur
- [ ] Inline error banner is clearly visible when the rule triggers
- [ ] Detail panel (read-only) is still accessible for informational purposes
- [ ] Self-approval prevention applies to both "Approve and Deploy" and "Deny" actions

**Triggered API Calls:**
- None — Decision step uses client-side comparison of `$User/Email` vs `selectedPromotion.initiatedBy`

**Error Scenarios:**
- If `$User/Email` is unavailable from SSO context: Treat as potential self-approval risk and disable buttons with a warning to contact an administrator

---

### A-07: Approve an Emergency Hotfix with Acknowledgment

**As an** Admin, **I want to** acknowledge the test-bypass when approving an emergency hotfix, **so that** there is a deliberate, auditable sign-off that this deployment skipped the test environment.

**Preconditions:**
- Admin has selected a promotion on Page 7 where `isHotfix = "true"`
- Admin has reviewed the hotfix justification and peer reviewer comments

**Flow:**
1. Admin selects a hotfix promotion row — the row shows a red "EMERGENCY HOTFIX" badge
2. The Promotion Detail Panel expands and shows Section 2b with a prominent red "EMERGENCY HOTFIX" banner containing the submitter's `hotfixJustification` text
3. Warning text: "This deployment bypassed the test environment. Please review carefully."
4. Admin optionally enters comments in the "Admin Comments" textarea
5. Admin clicks "Approve and Deploy"
6. Confirmation modal includes extra hotfix warning text: "This is an emergency hotfix that bypassed the test environment."
7. Modal also requires checking the acknowledgment checkbox: "I acknowledge this is an emergency hotfix that bypassed testing" — "Confirm Approval" is disabled until checked
8. Admin checks the checkbox and clicks "Confirm Approval"
9. Standard approval pipeline executes (merge → packageAndDeploy → branch delete)
10. PromotionLog records `isHotfix = "true"` and `hotfixJustification`

**Acceptance Criteria:**
- [ ] The "EMERGENCY HOTFIX" banner is displayed prominently in the detail panel for hotfix promotions
- [ ] Hotfix justification text is displayed in the banner
- [ ] The confirmation modal includes the mandatory acknowledgment checkbox for hotfix promotions
- [ ] "Confirm Approval" button remains disabled until the acknowledgment checkbox is checked
- [ ] PromotionLog preserves `isHotfix = "true"` and `hotfixJustification` for audit purposes
- [ ] The hotfix audit trail is queryable (filter by `isHotfix = "true"`) for leadership review

**Triggered API Calls:**
- Same as A-04: OVERRIDE merge → `packageAndDeploy` → branch delete

**Error Scenarios:**
- Admin attempts to approve without checking acknowledgment checkbox: "Confirm Approval" button remains disabled; no bypass possible

---

## Component Mapping Management (Page 8)

### A-08: View All Component Mappings

**As an** Admin, **I want to** view all dev-to-prod component ID mappings in a searchable, filterable grid, **so that** I can audit the promotion history and verify that mappings are correct.

**Preconditions:**
- Admin is authenticated with `ABC_BOOMI_FLOW_ADMIN` group membership
- ComponentMapping DataHub model contains records

**Flow:**
1. Admin navigates to Page 8 (Mapping Viewer) — either from Page 7's "View Component Mappings" link or directly
2. System calls `manageMappings` with `operation = "list"`
3. Mapping Data Grid loads with all ComponentMapping records, sorted by `lastPromotedAt` descending
4. Grid shows columns: Component Name, Type (badge), Dev Account (truncated GUID), Dev Component ID, Prod Component ID, Prod Version, Last Promoted, Promoted By, Mapping Source (badge)
5. Admin uses the Filter Bar to narrow results:
   - Type dropdown (All / process / connection / map / profile / operation)
   - Dev Account dropdown (All / per accessible dev account)
   - Source dropdown (All / PROMOTION_ENGINE / ADMIN_SEEDING)
   - Text search box (partial match on component name, debounced 300ms)
6. Admin clicks "Apply Filters" to apply selections
7. Admin clicks "Clear" to reset all filters
8. Pagination shows 50 rows per page with row count ("Showing 1-50 of 234 mappings")

**Acceptance Criteria:**
- [ ] Page 8 is only accessible to `ABC_BOOMI_FLOW_ADMIN` users
- [ ] Grid loads all ComponentMapping records via `manageMappings (operation = "list")`
- [ ] Default sort is `lastPromotedAt` descending
- [ ] Component type column renders color-coded badges (process=blue, connection=green, map=purple, profile=orange, operation=teal)
- [ ] PROMOTION_ENGINE source badge displays as "Engine" (blue); ADMIN_SEEDING as "Admin Seeded" (purple)
- [ ] Dev Component ID and Prod Component ID are truncated with full GUID on tooltip hover
- [ ] Text search filters by `componentName` (partial match, case-insensitive) with 300ms debounce
- [ ] Pagination shows 50 rows per page with Previous/Next and page number controls

**Triggered API Calls:**
- `manageMappings` → Process F (with `operation = "list"`)

**Error Scenarios:**
- `manageMappings` failure: Navigate to Error Page

---

### A-09: Export Component Mappings to CSV

**As an** Admin, **I want to** download the current filtered mapping view as a CSV file, **so that** I can audit mappings offline or share them with team members.

**Preconditions:**
- Admin is on Page 8 with mappings loaded (possibly filtered)

**Flow:**
1. Admin optionally applies filters to narrow the export scope
2. Admin clicks "Export to CSV" button (top-right of grid, with a download icon)
3. System generates a CSV file from the current filtered/sorted view
4. File downloads to the browser as `component-mappings-{date}.csv` (e.g., `component-mappings-2026-02-17.csv`)
5. CSV includes all grid columns: Component Name, Type, Dev Account, Dev Component ID, Prod Component ID, Prod Version, Last Promoted, Promoted By

**Acceptance Criteria:**
- [ ] "Export to CSV" button triggers a file download without navigating away from the page
- [ ] Exported CSV reflects the current filtered view (not all records if filters are active)
- [ ] Filename follows the pattern `component-mappings-{YYYY-MM-DD}.csv`
- [ ] All grid columns are included in the CSV with appropriate headers
- [ ] Full GUIDs are exported (not truncated values shown in the grid)

**Triggered API Calls:**
- None — export is generated from data already loaded in the grid

**Error Scenarios:**
- If no mappings match the current filters, the exported CSV contains only the header row with a note or is empty

---

### A-10: Seed Connection Mappings for a Dev Account

**As an** Admin, **I want to** create connection mappings between dev account connection IDs and the parent account's pre-configured canonical connections, **so that** the promotion engine can rewrite connection references during component promotion.

**Preconditions:**
- Admin knows the dev account's connection component ID (obtained from the dev account's Build tab)
- Admin knows the parent account's canonical connection component ID (from the `#Connections` folder)
- Admin is on Page 8

**Flow:**
1. Admin clicks "Seed Connection Mapping" button (collapsible section, collapsed by default)
2. The "Connection Mapping Seeding" form expands with an explanatory header:
   > "Connections are shared resources pre-configured once in the parent account's #Connections folder. Each dev account has its own connection component IDs that must be mapped to the parent's canonical connection IDs."
3. Admin fills in the form:
   - Dev Account: select from dropdown of accessible dev accounts
   - Dev Connection Component ID: GUID from the dev account (validated as GUID format)
   - Connection Name: human-readable name (e.g., "SFTP - Orders Server")
   - Parent Account Connection ID: canonical GUID from the `#Connections` folder
4. Admin clicks "Seed Connection Mapping"
5. System calls `manageMappings` with `operation = "create"` and `mappingSource = "ADMIN_SEEDING"`, `componentType = "connection"` (auto-set)
6. On success: form collapses, grid refreshes, success toast: "Mapping saved successfully"
7. The seeded mapping appears at the top of the grid (most recently promoted = now)
8. Clicking "Cancel" collapses the form without saving

**Acceptance Criteria:**
- [ ] Seed form is collapsed by default; expands via "Seed Connection Mapping" button
- [ ] All required fields are validated before enabling "Seed Connection Mapping" button
- [ ] Dev Connection ID and Parent Connection ID are validated as GUID format
- [ ] `componentType` is auto-set to `"connection"` — not editable by admin in this form
- [ ] `mappingSource` is set to `ADMIN_SEEDING`
- [ ] On success: form collapses, grid refreshes, success message shown
- [ ] The same parent connection ID can be mapped from multiple dev accounts
- [ ] Duplicate mapping (same `devComponentId` + `devAccountId`) is rejected with an error

**Triggered API Calls:**
- `manageMappings` → Process F (with `operation = "create"`, `mappingSource = "ADMIN_SEEDING"`)

**Error Scenarios:**
- `DUPLICATE_MAPPING`: Mapping already exists for this dev component ID + dev account ID — show error inline, keep form open
- Invalid GUID format: Inline validation error on the relevant field; save button disabled
- `manageMappings` API failure: Show error inline; keep form open for correction

---

### A-11: Manually Create or Update a Component Mapping

**As an** Admin, **I want to** manually create or correct a component mapping in the system, **so that** I can fix incorrect mappings or register components promoted outside the standard Flow workflow.

**Preconditions:**
- Admin is on Page 8
- Admin has the dev component ID, dev account ID, and prod component ID available

**Flow:**
1. Admin clicks "Add/Edit Mapping" button (Manual Mapping Form section, collapsed by default)
2. Manual Mapping Form expands
3. Admin fills in all required fields:
   - Dev Component ID (GUID, required)
   - Dev Account ID (GUID or dropdown, required)
   - Prod Component ID (GUID, required)
   - Component Name (text, required, max 200 chars)
   - Component Type (dropdown: process / connection / map / profile / operation, required)
   - Prod Account ID (read-only, pre-populated with the primary account ID)
4. Admin clicks "Save Mapping"
5. System validates all required fields and GUID formats
6. System calls `manageMappings` with `operation = "create"` (new mapping) or `operation = "update"` (editing existing)
7. On success: form collapses, grid refreshes, success toast: "Mapping saved successfully"
8. Clicking "Cancel" collapses the form without saving

**Acceptance Criteria:**
- [ ] Manual Mapping Form is collapsed by default
- [ ] All required fields are validated before allowing save
- [ ] Dev/Prod Component IDs are validated as GUID format
- [ ] Prod Account ID is pre-populated and read-only (always primary account)
- [ ] On success: form collapses, grid refreshes, success message shown
- [ ] Uniqueness constraint: Dev Component ID + Dev Account ID must not duplicate an existing mapping
- [ ] `manageMappings` is called with `operation = "create"` for new mappings

**Triggered API Calls:**
- `manageMappings` → Process F (with `operation = "create"` or `"update"`)

**Error Scenarios:**
- `DUPLICATE_MAPPING`: Show inline error; keep form open
- Invalid GUID: Inline field validation error; save disabled
- `manageMappings` API failure: Show error inline; keep form open

---

### A-12: Delete a Component Mapping

**As an** Admin, **I want to** delete an incorrect or obsolete component mapping, **so that** the mapping table stays accurate and does not cause incorrect reference rewrites during future promotions.

**Preconditions:**
- Admin is on Page 8 with mappings loaded
- Admin has identified the mapping to delete (e.g., from filtering by dev account or component name)

**Flow:**
1. Admin selects the mapping row in the Mapping Data Grid
2. Admin opens the Manual Mapping Form for the selected row (or uses a per-row "Delete" action)
3. System displays a confirmation dialog: "Are you sure you want to delete this mapping? This cannot be undone."
4. Admin confirms deletion
5. System calls `manageMappings` with `operation = "delete"` and `mappingId`
6. On success: success toast shown; grid refreshes; deleted row removed
7. Clicking "Cancel" on the confirmation dialog cancels the operation

**Acceptance Criteria:**
- [ ] Delete action requires a confirmation dialog before executing
- [ ] After confirmation, `manageMappings (operation = "delete")` is called with the correct `mappingId`
- [ ] Deleted mapping is removed from the grid on success
- [ ] A success toast is shown after deletion
- [ ] Deletion is irreversible; there is no undo mechanism

**Triggered API Calls:**
- `manageMappings` → Process F (with `operation = "delete"`)

**Error Scenarios:**
- `manageMappings` API failure: Show error toast; mapping remains in grid
- Mapping not found: Show error "Mapping no longer exists — it may have been deleted by another session"; refresh grid

---

## Account Access and System Configuration

### A-13: View All Dev Accounts (Admin Bypass of Team Check)

**As an** Admin, **I want to** see all dev sub-accounts regardless of my team group memberships, **so that** I can manage and review promotions from any team without needing to be a member of every team group.

**Preconditions:**
- Admin is authenticated with `ABC_BOOMI_FLOW_ADMIN` SSO group membership

**Flow:**
1. Admin navigates to Page 1 (Package Browser) in the Developer Swimlane
2. System calls `getDevAccounts` with the admin's `userSsoGroups`
3. Process A0 detects `ABC_BOOMI_FLOW_ADMIN` in `userSsoGroups`
4. Tier resolution algorithm returns `effectiveTier = "ADMIN"` — team group check is bypassed
5. Process A0 returns ALL active DevAccountAccess records (not filtered by team groups)
6. `accessibleAccounts` Flow value is populated with all accounts
7. Admin sees all dev accounts in the account selector dropdown, not just their team's accounts

**Acceptance Criteria:**
- [ ] `getDevAccounts` returns all active DevAccountAccess records for `ABC_BOOMI_FLOW_ADMIN` users
- [ ] Admin does NOT need to belong to any `ABC_BOOMI_FLOW_DEVTEAM*` group to see dev accounts
- [ ] `effectiveTier` is set to `"ADMIN"` in the response for admin users
- [ ] `userEffectiveTier` Flow value is set to "ADMIN" on page load
- [ ] Contributors from teams not the admin's own team are invisible unless the admin also has the team group

**Triggered API Calls:**
- `getDevAccounts` → Process A0

**Error Scenarios:**
- `INSUFFICIENT_TIER`: Should never occur for an authenticated admin; if reached (e.g., direct API call without proper groups), return `success = false` with error code

---

### A-14: Receive Email Notification When Peer Approval Is Complete

**As an** Admin, **I want to** receive an email notification when a promotion has passed peer review, **so that** I know when a new item is waiting in my approval queue without having to check the dashboard continuously.

**Preconditions:**
- A peer reviewer has approved a promotion on Page 6 (`submitPeerReview` with `decision = "APPROVED"`)
- Admin distribution list is configured (e.g., `boomi-admins@company.com`)

**Flow:**
1. Peer reviewer clicks "Approve" on Page 6
2. `submitPeerReview` succeeds and PromotionLog `peerReviewStatus` is updated to `PEER_APPROVED`
3. System sends email notification:
   - To: Admin distribution list (`boomi-admins@company.com`) + submitter email
   - Subject: "Peer Approved — Admin Review Needed: {processName} v{packageVersion}"
   - Body includes: process name, package version, promotion ID, submitter info, peer reviewer decision and comments
4. Admin sees the email and clicks the link to navigate to the Promotion Dashboard
5. Admin authenticates and lands on Page 7 where the newly approved promotion is visible

**Acceptance Criteria:**
- [ ] Email is sent automatically upon successful `submitPeerReview` with `decision = "APPROVED"` — no manual trigger required
- [ ] Email is sent to the admin distribution list, not to individual admin users
- [ ] Submitter is also included in the "To:" or "CC:" of the email
- [ ] Email subject follows the pattern "Peer Approved — Admin Review Needed: {processName} v{packageVersion}"
- [ ] Email body includes peer reviewer name/email, decision, and any peer review comments
- [ ] For emergency hotfix promotions, the email subject includes "EMERGENCY HOTFIX"

**Triggered API Calls:**
- (Email is sent as part of `submitPeerReview` → Process E3 execution — not a separate API call)

**Error Scenarios:**
- Email delivery failure: Log warning; flow continues normally; admin must check the dashboard directly

---

### A-15: Receive Email Notification When Deployment Is Complete

**As an** Admin, **I want to** be informed when a deployment I approved has completed successfully, and for the submitter and peer reviewer to also receive confirmation, **so that** all stakeholders know the promotion outcome.

**Preconditions:**
- Admin has approved a promotion and `packageAndDeploy` has completed successfully

**Flow:**
1. `packageAndDeploy` (Process D) completes successfully
2. System sends email notification:
   - To: Submitter email + peer reviewer email
   - Subject: "Approved & Deployed: {processName} v{packageVersion}"
   - Body includes:
     - Promotion ID, process name, package version
     - Deployment ID, prod package ID
     - Peer reviewer name/email
     - Admin name/email, approval date, admin comments
     - Status: "Successfully deployed"
3. Admin can also see the deployment result inline on Page 7 (success message with deployment ID)

**Acceptance Criteria:**
- [ ] Email is sent to the submitter and peer reviewer upon successful deployment
- [ ] Email subject follows the pattern "Approved & Deployed: {processName} v{packageVersion}"
- [ ] Email body includes the deployment ID and prod package ID
- [ ] Admin approval metadata (who approved, when, comments) is included in the email body
- [ ] Success message is shown inline on Page 7 with deployment ID

**Triggered API Calls:**
- (Email is sent as part of `packageAndDeploy` → Process D execution)

**Error Scenarios:**
- Email delivery failure: Log warning; deployment is still considered complete; admin sees success inline

---

## Inherited Contributor Capabilities

### A-16: Access Developer Swimlane as Admin

**As an** Admin, **I want to** access all Developer Swimlane pages (Package Browser, Promotion Review, Promotion Status, Deployment Submission, Production Readiness), **so that** I can submit promotions, perform test deployments, and manage the full promotion lifecycle without switching accounts.

**Preconditions:**
- Admin is authenticated with `ABC_BOOMI_FLOW_ADMIN` group membership

**Flow:**
1. Admin navigates to Page 1 (Package Browser) in the Developer Swimlane
2. Authorization check passes: `ABC_BOOMI_FLOW_ADMIN` satisfies the "CONTRIBUTOR OR ADMIN" swimlane authorization
3. Admin sees all dev accounts (full account visibility, bypassing team group check)
4. Admin follows the standard contributor workflow: select account → select package → review dependencies → execute promotion → choose deployment path
5. Admin can submit for peer review (flows to Peer Review swimlane), submit a test deployment, or select Emergency Hotfix

**Acceptance Criteria:**
- [ ] `ABC_BOOMI_FLOW_ADMIN` group membership grants access to all Developer Swimlane pages
- [ ] Admin sees all dev accounts in the account selector (not just team-filtered accounts)
- [ ] Admin can complete all contributor workflows: package selection, dependency review, promotion execution, deployment submission
- [ ] Admin can initiate emergency hotfix deployments with mandatory justification
- [ ] Admin's own promotions will be blocked from self-approval on Page 7 (see A-06)

**Triggered API Calls:**
- Same as contributor workflow: `getDevAccounts` → `listDevPackages` → `resolveDependencies` → `executePromotion` → `packageAndDeploy` (test) or peer review submission

**Error Scenarios:**
- Same error scenarios as Contributor stories (see contributor-stories.md)

---

### A-17: Access Peer Review Swimlane as Admin

**As an** Admin, **I want to** participate in peer review of other developers' promotions, **so that** I can contribute to the first approval layer even when regular contributors are unavailable.

**Preconditions:**
- Admin is authenticated with `ABC_BOOMI_FLOW_ADMIN` group membership
- There are promotions in `PENDING_PEER_REVIEW` status not submitted by the admin

**Flow:**
1. Admin navigates to Page 5 (Peer Review Queue) in the Peer Review Swimlane
2. Authorization check passes: `ABC_BOOMI_FLOW_ADMIN` satisfies the "CONTRIBUTOR OR ADMIN" swimlane authorization
3. System calls `queryPeerReviewQueue` with `requesterEmail = $User/Email`; admin's own promotions are excluded from the results
4. Admin selects a pending review and follows the standard peer review workflow on Page 6
5. Admin can approve or reject promotions (with the same self-review prevention that applies to contributors)
6. When an admin approves a promotion on Page 6, flow transitions to the Admin Swimlane → Page 7 (but a different admin must handle the final approval)

**Acceptance Criteria:**
- [ ] `ABC_BOOMI_FLOW_ADMIN` group membership grants access to both Peer Review Swimlane pages
- [ ] Admin's own submissions are excluded from the peer review queue (same exclusion logic as contributors)
- [ ] Admin can approve and reject promotions on Page 6 using `submitPeerReview`
- [ ] When admin approves a peer review, the promotion advances to `PENDING_ADMIN_REVIEW` for a different admin to process

**Triggered API Calls:**
- `queryPeerReviewQueue` → Process E2
- `generateComponentDiff` → Process G (for diff viewing)
- `submitPeerReview` → Process E3

**Error Scenarios:**
- Same error scenarios as Peer Reviewer stories (see peer-reviewer-stories.md)

---

## Story Index

| Story ID | Title | Page | Process |
|----------|-------|------|---------|
| A-01 | View Pending Approval Queue | 7 | E (queryStatus) |
| A-02 | Review Promotion Details | 7 | — (data from A-01) |
| A-03 | View Component XML Diff | 7 | G (generateComponentDiff) |
| A-04 | Approve and Deploy | 7 | D (packageAndDeploy) |
| A-05 | Deny with Reason | 7 | Branch DELETE |
| A-06 | Self-Approval Prevention | 7 | — (Decision step) |
| A-07 | Approve Emergency Hotfix | 7 | D (packageAndDeploy) |
| A-08 | View All Component Mappings | 8 | F (manageMappings list) |
| A-09 | Export Mappings to CSV | 8 | — (client-side) |
| A-10 | Seed Connection Mappings | 8 | F (manageMappings create/ADMIN_SEEDING) |
| A-11 | Manually Create/Update Mapping | 8 | F (manageMappings create/update) |
| A-12 | Delete a Mapping | 8 | F (manageMappings delete) |
| A-13 | View All Dev Accounts (Bypass) | 1 | A0 (getDevAccounts) |
| A-14 | Email: Peer Approval Notification | — | E3 (submitPeerReview) |
| A-15 | Email: Deployment Complete Notification | 7 | D (packageAndDeploy) |
| A-16 | Access Developer Swimlane | 1–4, 9 | Inherited contributor |
| A-17 | Access Peer Review Swimlane | 5–6 | Inherited peer reviewer |

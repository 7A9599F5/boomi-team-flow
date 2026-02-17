# Peer Reviewer User Stories

**Role:** Peer Reviewer — any authenticated user with `ABC_BOOMI_FLOW_CONTRIBUTOR` OR `ABC_BOOMI_FLOW_ADMIN` SSO group membership, **excluding the promotion's original submitter**.

**Swimlane:** Peer Review Swimlane (Pages 5–6)

**Summary:** The peer reviewer is the first approval gate in the 2-layer approval workflow. After a contributor submits a promotion for peer review, any qualified colleague (not the submitter) reviews the component changes and either approves (advancing to admin review) or rejects (deleting the branch and notifying the submitter).

---

## Stories

### PR-01: View the Peer Review Queue (Excluding Own Submissions)

**As a** Peer Reviewer, **I want to** see all promotions awaiting peer review that were not submitted by me, **so that** I can select one to review without accidentally reviewing my own work.

**Preconditions:**
- User is authenticated with `ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN` SSO group
- At least one promotion exists in `PENDING_PEER_REVIEW` status submitted by a different user

**Flow:**
1. User navigates to the Peer Review swimlane (via email link or direct navigation)
2. System authenticates the user via Azure AD SSO and validates group membership
3. Page 5 loads and triggers the `queryPeerReviewQueue` message step with `requesterEmail = $User/Email`
4. Backend (Process E2) queries PromotionLog for all `PENDING_PEER_REVIEW` records, applying a case-insensitive filter to exclude records where `initiatedBy.toLowerCase() == requesterEmail.toLowerCase()`
5. System populates `pendingPeerReviews` Flow value with the filtered results
6. Page displays the Peer Review Queue data grid with columns: Submitter, Process Name, Components, Created/Updated, Submitted, Status, Environment, Hotfix badge, Notes
7. Rows are sorted by `initiatedAt` descending (newest first)
8. If no eligible reviews exist, the grid shows empty state: "No pending peer reviews"

**Acceptance Criteria:**
- [ ] Own submissions do not appear in the queue (backend-filtered via `requesterEmail`)
- [ ] Queue loads automatically on page entry without manual refresh
- [ ] Rows are sorted newest-first by default
- [ ] All columns display correct data from `pendingReviews` array
- [ ] Empty state message displays when no eligible reviews exist
- [ ] EMERGENCY HOTFIX badge displays in red for promotions where `isHotfix = "true"`
- [ ] Environment badge always shows "PRODUCTION" (test deployments never reach peer review)
- [ ] Notes column truncates to 50 characters with tooltip for full text

**Triggered API Calls:**
- `queryPeerReviewQueue` → Process E2 (Query Peer Review Queue)

**Error Scenarios:**
- `AUTH_FAILED`: SSO authentication failure — user sees "Access denied. This page requires developer or admin privileges."
- `DATAHUB_ERROR`: DataHub query failure — navigate to Error Page with error message

---

### PR-02: Select a Pending Promotion to Review

**As a** Peer Reviewer, **I want to** click on a promotion in the queue to open its full details, **so that** I can examine everything I need before making an approve or reject decision.

**Preconditions:**
- User is on Page 5 (Peer Review Queue)
- `pendingPeerReviews` is populated with at least one entry
- Selected promotion was not submitted by the current user

**Flow:**
1. User scans the queue and identifies a promotion to review
2. User clicks (or taps on mobile) the desired row
3. System highlights the selected row with accent color
4. System stores the selected record in `selectedPeerReview` Flow value
5. System performs a UI-level self-review check: `LOWERCASE($User/Email) != LOWERCASE(selectedPeerReview.initiatedBy)`
6. If the check fails (edge case bypass attempt): system shows inline error banner "You cannot review your own submission. Please ask another team member to review." and navigation is blocked
7. If the check passes: system navigates to Page 6 (Peer Review Detail)
8. Page 6 populates all detail sections from `selectedPeerReview` — no additional API call required

**Acceptance Criteria:**
- [ ] Single-row selection mode (only one row selected at a time)
- [ ] Row highlights visually on selection
- [ ] `selectedPeerReview` Flow value is populated before navigation
- [ ] UI-level self-review check runs before navigation to Page 6
- [ ] Self-review attempt shows inline error banner and blocks navigation
- [ ] Page 6 loads with all details from the selected promotion without an extra API call
- [ ] Back button on Page 6 returns user to Page 5

**Triggered API Calls:**
- None (data already loaded from `queryPeerReviewQueue` response)

**Error Scenarios:**
- Self-review bypass attempt: inline banner displayed, navigation blocked

---

### PR-03: Review Full Promotion Details Before Deciding

**As a** Peer Reviewer, **I want to** see all metadata about a promotion (submitter, process, version, components, deployment notes, hotfix flag, test history), **so that** I have full context to make an informed approve or reject decision.

**Preconditions:**
- User has navigated to Page 6 (Peer Review Detail)
- `selectedPeerReview` is populated

**Flow:**
1. Page 6 renders the Promotion Detail Panel with the following sections:
   - **Submission Details:** Submitted by (email/name), submitted at, Promotion ID (with copy button), Process Name, Package Version, Dev Package ID
   - **Deployment Information:** Integration Pack name, Target Account Group, Deployment Notes
   - **Environment & Hotfix Information:** Target Environment badge ("PRODUCTION"), plus hotfix panel if `isHotfix = "true"`
   - **Test Deployment History:** Shown when `testPromotionId` is populated — displays Test Promotion ID, test deployed date, and Test Integration Pack name
   - **Promotion Results:** Summary counts (total, created, updated, failed) and component results table with per-row detail
   - **Credential Warning:** Shown when any component has `configStripped = true` — lists components needing reconfiguration
   - **Source Account:** Dev account name and ID
2. User reads through all sections to understand what changed and why
3. If viewing a hotfix, user sees a prominent "⚠ EMERGENCY HOTFIX" red badge, justification text, and warning "This deployment bypasses the test environment. Please review carefully."
4. If viewing a production-from-test promotion, user sees a green "Previously Tested" panel with the test deployment history

**Acceptance Criteria:**
- [ ] All metadata sections render correctly from `selectedPeerReview` object fields
- [ ] EMERGENCY HOTFIX panel is visible and prominently styled (red background) when `isHotfix = "true"`
- [ ] Test deployment history panel is visible (green background) when `testPromotionId` is populated
- [ ] Credential warning section appears when any component has `configStripped = true`
- [ ] Component results table shows per-component action (CREATE/UPDATE), status, config stripped flag, and diff links
- [ ] Promotion ID has a functional copy-to-clipboard button
- [ ] Deployment notes render in full (not truncated on detail page)

**Triggered API Calls:**
- None (data already loaded from `queryPeerReviewQueue` response)

**Error Scenarios:**
- None (display only; errors handled at previous step)

---

### PR-04: View Component XML Diffs During Review

**As a** Peer Reviewer, **I want to** see a side-by-side XML diff of what changed in each promoted component, **so that** I can verify the actual code changes are safe and correct before approving.

**Preconditions:**
- User is on Page 6 (Peer Review Detail)
- At least one component has `componentAction = "UPDATE"` or `"CREATE"`
- `selectedPeerReview.branchId` is populated

**Flow:**
1. User locates a component row in the component results table
2. User clicks "View Diff" (for UPDATE) or "View New" (for CREATE) link in that row
3. System shows a loading spinner in the inline diff panel
4. System triggers `generateComponentDiff` message step with:
   - `branchId` from `selectedPeerReview.branchId`
   - `prodComponentId` from the selected component row
   - `componentName` from the selected component row
   - `componentAction` from the selected component row
5. Process G fetches component XML from both the promotion branch (`Component/{id}~{branchId}`) and main branch (`Component/{id}`), normalizes both via the `normalize-xml.groovy` script, and returns normalized XML strings
6. System stores results in `diffBranchXml` and `diffMainXml` Flow values
7. System renders the `XmlDiffViewer` custom React component with branch vs main XML for side-by-side comparison
8. For CREATE actions: `diffMainXml` is empty — diff view shows only the new component XML
9. Diff panel expands inline below the component results table with a close button (X)
10. Only one diff panel is open at a time (closing previous if another is opened)
11. Diff panel has a max-height of 500px with scroll

**Acceptance Criteria:**
- [ ] "View Diff" link triggers `generateComponentDiff` API call
- [ ] Loading spinner displays during API call
- [ ] XmlDiffViewer renders with branch XML and main XML side by side
- [ ] For CREATE actions, main XML panel shows empty/placeholder state
- [ ] `branchVersion` and `mainVersion` are displayed in the diff panel header
- [ ] Only one diff panel is open at a time
- [ ] Close button (X) dismisses the diff panel
- [ ] Diff panel is scrollable within 500px max-height
- [ ] API errors show a failure message within the diff panel (not a full page error)

**Triggered API Calls:**
- `generateComponentDiff` → Process G (Generate Component Diff)

**Error Scenarios:**
- `COMPONENT_NOT_FOUND`: Component not found on branch or main — show error message in diff panel area
- `AUTH_FAILED`: API authentication error — show error in diff panel area

---

### PR-05: Approve a Promotion and Advance to Admin Review

**As a** Peer Reviewer, **I want to** approve a promotion that looks correct and safe, **so that** it advances to the Admin Approval Queue for final deployment authorization.

**Preconditions:**
- User is on Page 6 (Peer Review Detail) and has reviewed the promotion
- Promotion is in `PENDING_PEER_REVIEW` status
- Current user is not the promotion submitter

**Flow:**
1. User optionally adds comments in the "Peer Review Comments" textarea (up to 500 characters)
2. User clicks "Approve — Send to Admin Review" button
3. System shows a confirmation modal:
   - Title: "Confirm Peer Approval"
   - Content: Process name, version, total components, submitter
   - Buttons: "Cancel" (secondary) and "Confirm Approval" (green primary)
4. User clicks "Confirm Approval"
5. System triggers `submitPeerReview` message step with:
   - `promotionId` from `selectedPeerReview.promotionId`
   - `decision = "APPROVED"`
   - `reviewerEmail` from `$User/Email`
   - `reviewerName` from `$User/First Name` + `$User/Last Name`
   - `comments` from `peerReviewComments` (optional)
6. Process E3 validates: reviewer is not the submitter (case-insensitive), promotion is in `PENDING_PEER_REVIEW`, promotion has not already been reviewed
7. On success: Process E3 updates PromotionLog `peerReviewStatus = PEER_APPROVED`, `adminReviewStatus = PENDING_ADMIN_REVIEW`
8. System sends email notifications:
   - **To admin distribution list and submitter:** Subject: "Peer Approved — Admin Review Needed: {processName} v{packageVersion}"
   - Body includes peer reviewer name/email, promotion details, and comments
9. System shows success message: "Peer review approved! This promotion has been forwarded to the Admin Approval Queue."
10. Flow transitions to Admin swimlane — admin must authenticate with `ABC_BOOMI_FLOW_ADMIN` to continue

**Acceptance Criteria:**
- [ ] Confirmation modal appears before submitting (no accidental approvals)
- [ ] "Cancel" in modal dismisses without taking action
- [ ] `submitPeerReview` is called with `decision = "APPROVED"`
- [ ] Comments (if provided) are included in the API request
- [ ] Success message is displayed after approval
- [ ] Email notifications are sent to admin distribution list and submitter
- [ ] Flow transitions to Admin swimlane after approval
- [ ] PromotionLog `peerReviewStatus` is updated to `PEER_APPROVED`
- [ ] PromotionLog `adminReviewStatus` is updated to `PENDING_ADMIN_REVIEW`

**Triggered API Calls:**
- `submitPeerReview` → Process E3 (Submit Peer Review)

**Error Scenarios:**
- `SELF_REVIEW_NOT_ALLOWED`: Backend catches a self-review attempt — show error "You cannot review your own submission"
- `ALREADY_REVIEWED`: Promotion was already reviewed by another peer reviewer — show error "This promotion has already been reviewed"
- `INVALID_REVIEW_STATE`: Promotion is no longer in a reviewable state — show error with current status
- `DATAHUB_ERROR`: DataHub update failure — show error page

---

### PR-06: Reject a Promotion with Required Reason

**As a** Peer Reviewer, **I want to** reject a promotion that has issues and provide a mandatory rejection reason, **so that** the submitter receives actionable feedback to fix and resubmit.

**Preconditions:**
- User is on Page 6 (Peer Review Detail) and has identified an issue with the promotion
- Promotion is in `PENDING_PEER_REVIEW` status
- Current user is not the promotion submitter

**Flow:**
1. User clicks the "Reject" button (red/danger)
2. System shows a rejection reason modal:
   - Title: "Reject Promotion"
   - Field: Required textarea "Reason for Rejection" (up to 500 characters)
   - Placeholder: "Explain why this promotion should not proceed..."
   - Buttons: "Cancel" (secondary) and "Confirm Rejection" (red/danger primary)
3. User types the rejection reason (required — "Confirm Rejection" disabled until text is entered)
4. User clicks "Confirm Rejection"
5. System triggers `submitPeerReview` message step with:
   - `promotionId` from `selectedPeerReview.promotionId`
   - `decision = "REJECTED"`
   - `reviewerEmail` from `$User/Email`
   - `reviewerName` from peer reviewer display name
   - `comments` from modal rejection reason textarea (required)
6. Process E3 validates: reviewer is not the submitter, promotion is in `PENDING_PEER_REVIEW`, promotion has not already been reviewed
7. On success: Process E3 updates PromotionLog `peerReviewStatus = PEER_REJECTED`
8. System triggers branch deletion: `DELETE /Branch/{branchId}` — main branch remains untouched
9. System sends email notification to submitter:
   - Subject: "Peer Review Rejected: {processName} v{packageVersion}"
   - Body includes reviewer name/email, rejection reason, and instructions to address feedback
10. System shows confirmation: "Promotion rejected. The submitter has been notified with your feedback."
11. Flow ends

**Acceptance Criteria:**
- [ ] Rejection reason modal appears on "Reject" button click
- [ ] Rejection reason textarea is required (cannot confirm rejection without text)
- [ ] "Cancel" in modal dismisses without taking action
- [ ] `submitPeerReview` is called with `decision = "REJECTED"` and non-empty `comments`
- [ ] Promotion branch is deleted after rejection
- [ ] Main branch is not modified
- [ ] Email notification is sent to the submitter with the rejection reason
- [ ] Confirmation message is displayed after rejection
- [ ] Flow ends (no further swimlane transitions)
- [ ] PromotionLog `peerReviewStatus` is updated to `PEER_REJECTED`

**Triggered API Calls:**
- `submitPeerReview` → Process E3 (Submit Peer Review)
- Branch deletion: `DELETE /Branch/{branchId}` (internal, via Process E3 on REJECTED decision)

**Error Scenarios:**
- `SELF_REVIEW_NOT_ALLOWED`: Backend catches a self-review attempt — show error "You cannot review your own submission"
- `ALREADY_REVIEWED`: Promotion was already reviewed — show error with current status
- `INVALID_REVIEW_STATE`: Promotion is no longer in a reviewable state — show error
- `DATAHUB_ERROR`: DataHub update failure — show error page

---

### PR-07: Self-Review Prevention — Cannot Review Own Submission

**As a** Peer Reviewer, **I want to** be prevented from reviewing my own promotion submission at both the queue and detail levels, **so that** the peer review process maintains its integrity and independence.

**Preconditions:**
- User is authenticated with `ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN`
- The user has at least one promotion in `PENDING_PEER_REVIEW` status

**Flow:**

*Scenario A — Backend Prevention (primary):*
1. User navigates to Page 5 (Peer Review Queue)
2. System calls `queryPeerReviewQueue` with `requesterEmail = $User/Email`
3. Process E2 applies case-insensitive filter: excludes all records where `initiatedBy.toLowerCase() == requesterEmail.toLowerCase()`
4. User's own submissions are silently absent from the queue
5. User sees only promotions submitted by others

*Scenario B — UI-Level Fallback (defense-in-depth):*
1. A promotion somehow appears in the queue where `initiatedBy` matches `$User/Email` (edge case)
2. User clicks the row
3. System runs Decision step: `LOWERCASE($User/Email) != LOWERCASE(selectedPeerReview.initiatedBy)`
4. Check fails — system shows inline error banner: "You cannot review your own submission. Please ask another team member to review."
5. Navigation to Page 6 is blocked

*Scenario C — Backend Validation (API-level):*
1. Even if a reviewer bypasses the UI and calls `submitPeerReview` directly
2. Process E3 compares `reviewerEmail.toLowerCase()` with `initiatedBy.toLowerCase()`
3. If they match: returns `success = false`, `errorCode = SELF_REVIEW_NOT_ALLOWED`
4. UI Decision step routes to error display

**Acceptance Criteria:**
- [ ] Own submissions are excluded from `queryPeerReviewQueue` results (backend filter)
- [ ] Case-insensitive comparison used in both UI and backend checks (handles Azure AD capitalization variations)
- [ ] UI-level Decision step blocks navigation to Page 6 if `initiatedBy` matches `$User/Email`
- [ ] Inline error banner is displayed for UI-level self-review attempt
- [ ] Backend Process E3 returns `SELF_REVIEW_NOT_ALLOWED` if self-review is attempted via API
- [ ] Error is surfaced to the user, not silently ignored

**Triggered API Calls:**
- `queryPeerReviewQueue` → Process E2 (with `requesterEmail` filter)
- `submitPeerReview` → Process E3 (validates `reviewerEmail != initiatedBy`)

**Error Scenarios:**
- `SELF_REVIEW_NOT_ALLOWED`: Displayed as "You cannot review your own submission"

---

### PR-08: Review Emergency Hotfix Submissions with Justification Visibility

**As a** Peer Reviewer, **I want to** see a clear emergency hotfix indicator and the submitter's justification when reviewing a hotfix promotion, **so that** I understand it bypasses the test environment and can evaluate the justification before approving.

**Preconditions:**
- User is on Page 5 (Peer Review Queue) or Page 6 (Peer Review Detail)
- A promotion exists with `isHotfix = "true"` and a non-empty `hotfixJustification`

**Flow:**

*Queue View (Page 5):*
1. User sees the Peer Review Queue data grid
2. Hotfix row displays a red "EMERGENCY HOTFIX" badge in the Hotfix column
3. User clicks the row to open the detail view

*Detail View (Page 6):*
1. Page 6 shows a prominent "⚠ EMERGENCY HOTFIX" red badge at the top of the Environment & Hotfix Information section
2. Below the badge, the submitter's justification text is displayed in full
3. A warning message reads: "This deployment bypasses the test environment. Please review carefully."
4. The section has a red background panel with a red left border and warning icon
5. User reads the justification and reviews the component changes carefully (including XML diff)
6. User proceeds to approve or reject using the standard flow (PR-05 or PR-06)

**Acceptance Criteria:**
- [ ] Red "EMERGENCY HOTFIX" badge appears in the queue grid when `isHotfix = "true"`
- [ ] Non-hotfix rows do not show the badge (hidden/absent)
- [ ] Page 6 shows the EMERGENCY HOTFIX red panel when `isHotfix = "true"`
- [ ] Full `hotfixJustification` text is displayed (not truncated) on Page 6
- [ ] Warning text about bypassing test environment is visible
- [ ] Red background styling is applied to the hotfix panel
- [ ] Approve and Reject buttons function the same as standard promotions
- [ ] Hotfix flag is preserved and echoed in the approval email to admins

**Triggered API Calls:**
- `queryPeerReviewQueue` → Process E2 (queue load)
- `generateComponentDiff` → Process G (optional, on "View Diff" click)
- `submitPeerReview` → Process E3 (on approve or reject)

**Error Scenarios:**
- Same as PR-05 (approve) and PR-06 (reject)

---

### PR-09: Receive Email Notification When a Promotion Needs Peer Review

**As a** Peer Reviewer, **I want to** receive an email when a new promotion is submitted for peer review, **so that** I know to go to the dashboard and review it without having to manually check the queue.

**Preconditions:**
- A developer or admin has submitted a promotion for peer review (standard or emergency hotfix)
- Email distribution lists are configured: `boomi-developers@company.com`, `boomi-admins@company.com`

**Flow:**

*Standard Submission:*
1. Contributor completes Page 4 and clicks "Submit for Peer Review"
2. System sends email to dev distribution list and admin distribution list (CC: submitter)
3. Subject: "Peer Review Needed: {processName} v{packageVersion}"
4. Body includes: submitter name/email, process name, version, total components, created count, updated count, Promotion ID, deployment notes, and link to Promotion Dashboard
5. Reviewer receives the email in their inbox
6. Reviewer clicks the dashboard link in the email to navigate directly to Page 5

*Emergency Hotfix Submission:*
1. Developer submits with `isHotfix = "true"` and justification
2. System sends email with subject: "⚠ EMERGENCY HOTFIX — Peer Review Needed: {processName} v{packageVersion}"
3. Body includes: prominent EMERGENCY HOTFIX heading, hotfix justification, submitter info, promotion details, and note "⚠ This hotfix requires both peer review AND admin review"
4. Email recipients are same as standard submission

**Acceptance Criteria:**
- [ ] Email is sent to dev and admin distribution lists when a promotion is submitted for peer review
- [ ] Submitter is CC'd for confirmation
- [ ] Email subject follows the pattern "Peer Review Needed: {processName} v{packageVersion}"
- [ ] Email body contains submitter info, promotion metadata, Promotion ID, and deployment notes
- [ ] Emergency hotfix emails have a distinct subject with "⚠ EMERGENCY HOTFIX" prefix
- [ ] Hotfix email body includes the `hotfixJustification` text
- [ ] Email includes a link to the Promotion Dashboard
- [ ] Email is sent before the flow pauses at the swimlane boundary (i.e., before reviewer authentication)

**Triggered API Calls:**
- (Email is triggered by the Developer swimlane on Page 4 submission — no peer reviewer action required)

**Error Scenarios:**
- Email delivery failure: System should log the failure but not block the workflow — promotion still enters the peer review queue

---

### PR-10: Receive Email Notification When Admin Acts on a Reviewed Promotion

**As a** Peer Reviewer, **I want to** receive an email when an admin approves or denies a promotion I reviewed, **so that** I can close the loop on my review and stay informed about the outcome.

**Preconditions:**
- Peer reviewer has approved a promotion (PR-05)
- An admin has since acted on the promotion in the Admin Approval Queue (Page 7)

**Flow:**

*Admin Approval:*
1. Admin approves and deploys the promotion on Page 7
2. System sends email to both the original submitter AND the peer reviewer who approved
3. Subject: "Approved & Deployed: {processName} v{packageVersion}"
4. Body includes: Promotion ID, process name, package version, deployment ID, prod package ID, peer reviewer name/email, admin approver name/email, admin approval timestamp, admin comments
5. Peer reviewer receives email confirming the promotion was successfully deployed

*Admin Denial:*
1. Admin denies the promotion on Page 7
2. System sends email to both the original submitter AND the peer reviewer who approved
3. Subject: "Admin Denied: {processName} v{packageVersion}"
4. Body includes: Promotion ID, process name, version, peer reviewer name/email, admin denier name/email, denial reason, admin comments
5. Peer reviewer receives email explaining why the promotion was ultimately denied despite passing peer review

**Acceptance Criteria:**
- [ ] Peer reviewer email is included in the "Admin Approved and Deployed" notification
- [ ] Peer reviewer email is included in the "Admin Denied" notification
- [ ] "Approved & Deployed" email subject follows "Approved & Deployed: {processName} v{packageVersion}"
- [ ] "Admin Denied" email subject follows "Admin Denied: {processName} v{packageVersion}"
- [ ] "Approved" email body includes deployment ID and prod package ID
- [ ] "Denied" email body includes the denial reason
- [ ] Both emails include the peer reviewer's name/email in the body (as part of the audit trail)
- [ ] Emails are sent to both submitter and peer reviewer (not only submitter)

**Triggered API Calls:**
- (Email is triggered by the Admin swimlane on Page 7 actions — no peer reviewer action required)

**Error Scenarios:**
- Email delivery failure: Should be logged but not block the admin workflow

---

### PR-11: Navigate Back to Queue Without Losing State

**As a** Peer Reviewer, **I want to** return to the Peer Review Queue from the detail page without losing the queue data, **so that** I can select a different promotion if I change my mind.

**Preconditions:**
- User is on Page 6 (Peer Review Detail)
- No approve or reject action has been taken yet

**Flow:**
1. User clicks "Back to Peer Review Queue" navigation link in the top-left of Page 6
2. System navigates back to Page 5 (Peer Review Queue)
3. The `pendingPeerReviews` Flow value is still populated from the initial `queryPeerReviewQueue` load
4. Queue grid re-displays with the same data — no additional API call is required
5. User can select a different promotion from the queue

**Acceptance Criteria:**
- [ ] "Back to Peer Review Queue" button is visible at the top-left of Page 6
- [ ] Clicking back returns user to Page 5 without triggering a new `queryPeerReviewQueue` call
- [ ] Queue data persists in `pendingPeerReviews` Flow value between page navigations
- [ ] User can select any other queue item after returning
- [ ] No partial review state is written to the backend when using the back button

**Triggered API Calls:**
- None (queue data already in Flow state)

**Error Scenarios:**
- None for this navigation action

---

## Summary

| Story | Action | API Call | Process |
|-------|--------|----------|---------|
| PR-01 | View peer review queue | `queryPeerReviewQueue` | E2 |
| PR-02 | Select a promotion to review | None (state navigation) | — |
| PR-03 | View promotion details | None (state display) | — |
| PR-04 | View component XML diffs | `generateComponentDiff` | G |
| PR-05 | Approve promotion | `submitPeerReview` (APPROVED) | E3 |
| PR-06 | Reject promotion with reason | `submitPeerReview` (REJECTED) | E3 |
| PR-07 | Self-review prevention | `queryPeerReviewQueue`, `submitPeerReview` | E2, E3 |
| PR-08 | Review emergency hotfix | `submitPeerReview` | E3 |
| PR-09 | Receive submission email | (triggered by Dev swimlane) | — |
| PR-10 | Receive admin outcome email | (triggered by Admin swimlane) | — |
| PR-11 | Navigate back to queue | None | — |

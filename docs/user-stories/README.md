# User Stories — Boomi Dev-to-Prod Component Promotion System

## Summary

| Category | Count | File |
|----------|------:|------|
| Contributor (C-01 to C-16) | 16 | [contributor-stories.md](contributor-stories.md) |
| Peer Reviewer (PR-01 to PR-11) | 11 | [peer-reviewer-stories.md](peer-reviewer-stories.md) |
| Admin (A-01 to A-18) | 18 | [admin-stories.md](admin-stories.md) |
| Cross-Cutting (X-01 to X-07) | 7 | This file (below) |
| **Total** | **52** | |

---

## Story Index

### Contributor Stories

| ID | Story | Pages | Message Action(s) |
|----|-------|-------|-------------------|
| C-01 | View accessible dev accounts on login | 1 | `getDevAccounts` |
| C-02 | Browse packages in a selected dev account | 1 | `listDevPackages` |
| C-03 | Review dependency tree before promotion | 2 | `resolveDependencies` |
| C-04 | Execute promotion to create a branch | 2→3 | `executePromotion` |
| C-05 | View component XML diff after promotion | 3 | `generateComponentDiff` |
| C-06 | Choose a deployment target (Test / Hotfix) | 3 | — (UI state) |
| C-07 | Deploy directly to test environment | 4 | `packageAndDeploy` |
| C-08 | Submit for peer review (standard path) | 4 | — (swimlane transition) |
| C-09 | Submit emergency hotfix for peer review | 4 | — (swimlane transition) |
| C-10 | View test deployments ready for production | 9 | `queryTestDeployments`, `checkReleaseStatus` |
| C-11 | Promote a tested deployment to production | 9→4 | — (navigation) |
| C-12 | Cancel a stale test deployment | 9 | `cancelTestDeployment` |
| C-13 | Withdraw a pending promotion | 1 | `queryStatus`, `withdrawPromotion` |
| C-14 | Handle errors and recover | Error | — (Decision routing) |
| C-15 | Receive email notifications | — | — (Flow emails) |
| C-16 | Re-run a failed promotion | 3→1 | — (navigation) |

### Peer Reviewer Stories

| ID | Story | Pages | Message Action(s) |
|----|-------|-------|-------------------|
| PR-01 | View peer review queue (excluding own) | 5 | `queryPeerReviewQueue` |
| PR-02 | Select a pending promotion to review | 5→6 | — (navigation) |
| PR-03 | Review full promotion details | 6 | — (display) |
| PR-04 | View component XML diffs | 6 | `generateComponentDiff` |
| PR-05 | Approve a promotion → admin review | 6 | `submitPeerReview` (APPROVED) |
| PR-06 | Reject a promotion with required reason | 6 | `submitPeerReview` (REJECTED) |
| PR-07 | Self-review prevention (3-layer) | 5, 6 | `queryPeerReviewQueue`, `submitPeerReview` |
| PR-08 | Review emergency hotfix with justification | 5, 6 | `submitPeerReview` |
| PR-09 | Receive email: promotion needs peer review | — | — (Flow email) |
| PR-10 | Receive email: admin acted on reviewed promo | — | — (Flow email) |
| PR-11 | Navigate back to queue without losing state | 6→5 | — (navigation) |

### Admin Stories

| ID | Story | Pages | Message Action(s) |
|----|-------|-------|-------------------|
| A-01 | View pending approval queue (+ Pack Assignment tab) | 7 | `queryStatus`, `listIntegrationPacks` |
| A-02 | Review promotion details before approving | 7 | — (display) |
| A-03 | View component XML diff before approving | 7 | `generateComponentDiff` |
| A-04 | Approve and deploy (with IP selection) | 7 | `listIntegrationPacks`, `packageAndDeploy` + Platform API merge |
| A-05 | Deny a promotion with reason | 7 | Platform API branch DELETE |
| A-06 | Self-approval prevention | 7 | — (Decision step) |
| A-07 | Approve emergency hotfix with acknowledgment | 7 | `packageAndDeploy` |
| A-08 | View all component mappings | 8 | `manageMappings` (list) |
| A-09 | Export component mappings to CSV | 8 | — (client-side) |
| A-10 | Seed connection mappings for dev accounts | 8 | `manageMappings` (create) |
| A-11 | Manually create/update a mapping | 8 | `manageMappings` (create/update) |
| A-12 | Delete a component mapping | 8 | `manageMappings` (delete) |
| A-13 | View all dev accounts (admin bypass) | 1 | `getDevAccounts` |
| A-14 | Email: peer approval notification | — | — (Flow email) |
| A-15 | Email: deployment complete notification | — | — (Flow email) |
| A-16 | Access Developer swimlane (inherited) | 1–4, 9 | All contributor actions |
| A-17 | Access Peer Review swimlane (inherited) | 5–6 | All peer reviewer actions |
| A-18 | Assign Integration Pack (Pack Assignment) | 7 | `packageAndDeploy` (Mode 4) |

### Cross-Cutting Stories

| ID | Story | Affects |
|----|-------|---------|
| X-01 | SSO authentication and tier resolution | All roles |
| X-02 | Email notification lifecycle | All roles |
| X-03 | Branch lifecycle management | All roles |
| X-04 | Error handling and recovery | All roles |
| X-05 | State persistence across browser sessions | All roles |
| X-06 | Concurrent promotion prevention | Contributor |
| X-07 | API token rotation and graceful failure | System-wide |

---

## Cross-Cutting User Stories

### X-01: SSO Authentication and Tier Resolution

**As a** user of any role, **I want** the system to resolve my effective dashboard tier from my SSO group memberships at login, **so that** I am granted the correct level of access without manual configuration.

**Preconditions:**
- Azure AD/Entra SSO is configured for the Boomi Flow application
- User belongs to at least one recognized SSO group

**Flow:**
1. User opens the Promotion Dashboard URL
2. Azure AD SSO authenticates the user and passes group claims to Boomi Flow
3. Flow stores `userSsoGroups` from the SSO context
4. Page 1 calls `getDevAccounts`, which passes `userSsoGroups` to Process A0
5. Process A0 applies the tier resolution algorithm:
   - Contains `ABC_BOOMI_FLOW_ADMIN` → `effectiveTier = "ADMIN"`
   - Contains `ABC_BOOMI_FLOW_CONTRIBUTOR` → `effectiveTier = "CONTRIBUTOR"`
   - Neither → `effectiveTier = "READONLY"` (no dashboard access)
6. For ADMIN: all active DevAccountAccess records returned (team check bypassed)
7. For CONTRIBUTOR: only DevAccountAccess records matching the user's `ABC_BOOMI_FLOW_DEVTEAM*` groups
8. For READONLY/OPERATOR: `success=false`, `errorCode=INSUFFICIENT_TIER`
9. Defense-in-depth: Process C re-validates `userSsoGroups` before executing promotion

**Acceptance Criteria:**
- [ ] Tier is resolved at runtime from SSO claims — not stored in any database
- [ ] ADMIN tier bypasses the team group check for account visibility
- [ ] CONTRIBUTOR tier filters accounts by team group membership
- [ ] READONLY/OPERATOR tiers cannot access the dashboard at all
- [ ] Process C re-validates tier from `userSsoGroups` before promotion (defense-in-depth)
- [ ] Case-insensitive group name matching throughout

**Affected Stories:** C-01, A-13, A-16, A-17

---

### X-02: Email Notification Lifecycle

**As a** stakeholder in the promotion process, **I want** to receive email notifications at every significant state change, **so that** all parties stay informed without polling the dashboard.

**Preconditions:**
- Distribution lists configured: `boomi-developers@company.com`, `boomi-admins@company.com`
- SMTP or email service configured in the Boomi Flow application

**Notification Matrix:**

| # | Trigger | Subject Pattern | To | CC |
|---|---------|----------------|----|----|
| 1 | Peer review submitted | "Peer Review Needed: {process} v{version}" | Dev + Admin DLs | Submitter |
| 2 | Peer approved | "Peer Approved — Admin Review Needed: {process} v{version}" | Admin DL + Submitter | — |
| 3 | Peer rejected | "Peer Review Rejected: {process} v{version}" | Submitter | — |
| 4 | Admin approved + deployed | "Approved & Deployed: {process} v{version}" | Submitter + Peer Reviewer | — |
| 5 | Admin denied | "Admin Denied: {process} v{version}" | Submitter + Peer Reviewer | — |
| 6 | Test deployment complete | "Test Deployed: {process} v{version}" | Submitter | — |
| 7 | Emergency hotfix submitted | "EMERGENCY HOTFIX — Peer Review Needed: {process} v{version}" | Dev + Admin DLs | Submitter |

**Acceptance Criteria:**
- [ ] All 7 notification types fire at the correct workflow stage
- [ ] Email delivery failure is non-blocking — workflow continues; failure logged
- [ ] Hotfix emails include the justification text in the body
- [ ] Withdrawal does NOT generate an email (silent operation)
- [ ] All emails include the Promotion ID for cross-reference

**Affected Stories:** C-09, C-15, PR-09, PR-10, A-14, A-15

---

### X-03: Branch Lifecycle Management

**As a** system, **I want** every promotion branch to reach a terminal state (merged+deleted or deleted), **so that** no orphaned branches consume the 20-branch limit.

**Preconditions:**
- Boomi Branching is enabled on the primary account
- Branch hard limit: 20; operational threshold: 15

**Branch Terminal Paths:**

| Path | Trigger | Branch Outcome |
|------|---------|----------------|
| Promotion failure | Process C: any component fails | Branch DELETED immediately |
| Peer rejection | PR-06: reviewer rejects | Branch DELETED |
| Admin denial | A-05: admin denies | Branch DELETED |
| Admin approval (standard) | A-04: admin approves | Branch MERGED to main, then DELETED |
| Admin approval (hotfix) | A-07: admin approves hotfix | Branch MERGED to main, then DELETED |
| Test deployment | C-07: test deploy | Branch DELETED after packaging (Mode 1) |
| Production from test | A-04: admin approves prod-from-test | New branch created from packageId, MERGED to main, then DELETED |
| Test cancellation | C-12: cancel stale test | No branch to delete (already deleted in Mode 1) |
| Initiator withdrawal | C-13: initiator withdraws | Branch DELETED |
| Branch limit reached | Process C pre-check | Branch NEVER CREATED |

**Key Invariant:** Every branch is either actively in review or has been deleted. `PromotionLog.branchId` is set on creation and cleared (null) after deletion.

**Acceptance Criteria:**
- [ ] Process C checks branch count before creation; fails with `BRANCH_LIMIT_REACHED` if >= 15
- [ ] Every terminal workflow path deletes the branch (or skips creation)
- [ ] `DELETE /Branch/{branchId}` is idempotent — 404 is treated as success
- [ ] `PromotionLog.branchId` is cleared after branch deletion
- [ ] Test deployment branches are deleted immediately after packaging (Mode 1); production promotion recreates a branch from the PackagedComponent
- [ ] Page 9 shows deployment age with amber (15-30d) and red (>30d) warnings

**Affected Stories:** C-04, C-07, C-12, C-13, PR-06, A-04, A-05, A-07

---

### X-04: Error Handling and Recovery

**As a** user of any role, **I want** every failed operation to display a clear error with recovery options, **so that** I am never stranded on a dead-end screen.

**Preconditions:**
- All Message steps are followed by Decision steps checking `success == true`

**Error Handling Contract:**
- Every FSS response includes `success` (boolean), `errorCode` (conditional), `errorMessage` (conditional)
- Decision step routes: `success == true` → continue; `success == false` → Error Page or inline error
- Transient errors (HTTP 429, 5xx) → inline retry banner (auto-retry with backoff)
- Permanent errors (HTTP 4xx except 429) → Error Page with Back/Retry/Home buttons

**Error Page Components:**
1. Error icon + "An error occurred" heading
2. `errorMessage` (human-readable)
3. Collapsible "Technical Details" (errorCode, stack trace)
4. Context-specific guidance for known errors (e.g., `MISSING_CONNECTION_MAPPINGS` → "Ask admin to seed mappings")
5. Action buttons: Back, Retry, Home

**Acceptance Criteria:**
- [ ] Every Message step is followed by a Decision step
- [ ] Error Page shows `errorMessage` and `errorCode`
- [ ] Back, Retry, and Home buttons are always functional
- [ ] Inline retry for transient errors uses exponential backoff (1s, 2s, 4s; max 3 retries)
- [ ] Known error codes trigger contextual guidance text
- [ ] No dead-end screens exist in the application

**Affected Stories:** C-14, and error scenarios in all other stories

---

### X-05: State Persistence Across Browser Sessions

**As a** user of any role, **I want** my workflow state to persist if I close the browser during a long-running operation, **so that** I can return later and see the results without restarting.

**Preconditions:**
- Boomi Flow's built-in state persistence is enabled (IndexedDB caching)

**Flow:**
1. User initiates a long-running operation (e.g., `executePromotion` — 30–120s)
2. Flow Service sends async wait responses if processing exceeds ~30s
3. Flow UI shows a spinner/progress indicator
4. User closes the browser tab
5. State is persisted via IndexedDB (auto-cached every 30 seconds)
6. User returns to the same URL later
7. Flow resumes from the persisted state — either showing results or still waiting
8. On completion, the callback from the Flow Service updates the UI

**Acceptance Criteria:**
- [ ] IndexedDB caching persists state every 30 seconds
- [ ] Closing the browser during `executePromotion` does not lose progress
- [ ] Returning to the same URL resumes the flow at the correct state
- [ ] No manual polling is required — Flow Service callbacks update the UI automatically
- [ ] All Flow values are preserved across browser sessions

**Affected Stories:** C-04, C-07, A-04

---

### X-06: Concurrent Promotion Prevention

**As a** Contributor, **I want** the system to prevent two simultaneous promotions from the same dev account, **so that** duplicate components and conflicting branches are not created.

**Preconditions:**
- Process C implements the concurrency guard

**Flow:**
1. Contributor A starts a promotion for DevAccountX — Process C creates `PromotionLog` with `status=IN_PROGRESS`
2. Contributor B attempts to start a promotion for the same DevAccountX
3. Process C queries PromotionLog for existing `IN_PROGRESS` records on `devAccountId = DevAccountX`
4. Record found → Process C returns `success=false`, `errorCode=CONCURRENT_PROMOTION`
5. Contributor B sees the Error Page: "Another promotion is currently in progress for this account. Please wait and try again."

**Acceptance Criteria:**
- [ ] Process C checks for `IN_PROGRESS` promotions on the same `devAccountId` before creating a branch
- [ ] `CONCURRENT_PROMOTION` error is returned with a clear message
- [ ] The check is per-dev-account, not global (different dev accounts can promote simultaneously)
- [ ] The lock is released when the first promotion completes (status changes from `IN_PROGRESS`)
- [ ] If a promotion crashes mid-run, the IN_PROGRESS record may need manual cleanup (admin task)

**Affected Stories:** C-04

---

### X-07: API Token Rotation and Graceful Failure

**As an** administrator of the Boomi platform, **I want** the system to handle API token expiration gracefully, **so that** users see a clear error message (not cryptic failures) and no data corruption occurs.

**Preconditions:**
- Platform API token is configured in the `PROMO - HTTP Client - Platform API` connection
- Token rotation is recommended every 90 days (reminder at 75 days)

**Flow:**
1. API token expires or is revoked
2. All Platform API calls return HTTP 401 Unauthorized
3. Retry logic does NOT retry 401 (it is not transient)
4. Every affected process returns `success=false`, `errorCode=AUTH_FAILED`, `errorMessage="API token may be expired. Contact admin for token rotation."`
5. Users see the Error Page with the AUTH_FAILED guidance
6. No data corruption occurs — all API writes fail before execution on 401

**Token Rotation Procedure:**
1. Create new API token in AtomSphere
2. Update HTTP Client connection with new token
3. Test with a read-only call (e.g., `listDevPackages`)
4. Verify end-to-end with a low-risk process (e.g., `queryStatus`)
5. Revoke old token only after new token is confirmed working

**Acceptance Criteria:**
- [ ] HTTP 401 is never retried (permanent error)
- [ ] `AUTH_FAILED` error code is returned with clear guidance
- [ ] No data corruption can occur on token expiration (writes fail before execution)
- [ ] Token rotation can be performed with zero downtime (overlap window)
- [ ] 75-day reminder calendar event is recommended in ops runbook

**Affected Stories:** All stories that invoke Platform API calls

---

## Traceability Matrix

### Stories by Page

| Page | Stories |
|------|---------|
| 1 — Package Browser | C-01, C-02, C-13, A-13, A-16 |
| 2 — Promotion Review | C-03, A-16 |
| 3 — Promotion Status | C-04, C-05, C-06, C-16, A-16 |
| 4 — Deployment Submission | C-07, C-08, C-09, A-16 |
| 5 — Peer Review Queue | PR-01, PR-02, PR-07, A-17 |
| 6 — Peer Review Detail | PR-03, PR-04, PR-05, PR-06, PR-07, PR-08, PR-11, A-17 |
| 7 — Admin Approval Queue | A-01, A-02, A-03, A-04, A-05, A-06, A-07, A-18 |
| 8 — Mapping Viewer | A-08, A-09, A-10, A-11, A-12 |
| 9 — Production Readiness | C-10, C-11, C-12, A-16 |
| Error Page | C-14, X-04 |
| No specific page (email/system) | C-15, PR-09, PR-10, A-14, A-15, X-01, X-02, X-03, X-05, X-06, X-07 |

### Stories by Integration Process

| Process | Letter | Stories |
|---------|--------|---------|
| Get Dev Accounts | A0 | C-01, A-13, X-01 |
| List Dev Packages | A | C-02 |
| Resolve Dependencies | B | C-03 |
| Execute Promotion | C | C-04, X-03, X-06 |
| Package and Deploy | D | C-07, A-04, A-07, A-18, X-03 |
| Query Status | E | C-13, A-01 |
| Query Peer Review Queue | E2 | PR-01, PR-07 |
| Submit Peer Review | E3 | PR-05, PR-06, PR-07, PR-08 |
| Query Test Deployments | E4 | C-10 |
| Cancel Test Deployment | E4 | C-12, X-03 |
| Withdraw Promotion | E5 | C-13, X-03 |
| Manage Mappings | F | A-08, A-09, A-10, A-11, A-12 |
| Generate Component Diff | G | C-05, PR-04, A-03 |
| List Integration Packs | J | A-01, A-04, A-18 |
| Check Release Status | P | C-10 |

### Stories by Message Action

| Message Action | Stories |
|----------------|---------|
| `getDevAccounts` | C-01, A-13 |
| `listDevPackages` | C-02 |
| `resolveDependencies` | C-03 |
| `executePromotion` | C-04 |
| `packageAndDeploy` | C-07, A-04, A-07, A-18 |
| `queryStatus` | C-13, A-01 |
| `queryPeerReviewQueue` | PR-01, PR-07 |
| `submitPeerReview` | PR-05, PR-06, PR-07, PR-08 |
| `queryTestDeployments` | C-10 |
| `cancelTestDeployment` | C-12 |
| `withdrawPromotion` | C-13 |
| `manageMappings` | A-08, A-09, A-10, A-11, A-12 |
| `generateComponentDiff` | C-05, PR-04, A-03 |
| `listIntegrationPacks` | A-01, A-04, A-18 |
| `checkReleaseStatus` | C-10 |

# Promotion Dashboard - Flow Application Structure

## Overview

The Promotion Dashboard is a single Flow application with three swimlanes designed to facilitate component promotion from developer accounts to production via a 2-layer approval workflow (peer review + admin review). The application uses the Boomi Integration Service connector for all backend communication and Azure AD/Entra SSO for authentication.

**Key Facts:**
- 1 Flow application
- 3 Swimlanes (Developer, Peer Review, Admin)
- 8 pages total (4 developer pages, 2 peer review pages, 2 admin pages)
- All backend calls via Boomi Integration Service connector
- SSO-based authorization via Azure AD groups
- 2-layer approval: peer review gate (any dev or admin except submitter) → admin review gate (admin only)

## Swimlanes

### Developer Swimlane
- **Authorization:** SSO group "Boomi Developers"
- **Pages:**
  1. Package Browser
  2. Promotion Review
  3. Promotion Status
  4. Deployment Submission
- **Purpose:** Browse packages, review dependencies, execute promotion, submit for peer review

### Peer Review Swimlane
- **Authorization:** SSO groups "Boomi Developers" OR "Boomi Admins" (any listed group grants access)
- **Pages:**
  5. Peer Review Queue
  6. Peer Review Detail
- **Purpose:** Review and approve/reject promotion submissions from other developers. Self-review prevention: submitter cannot review their own submission (enforced at backend + UI level)

### Admin Swimlane
- **Authorization:** SSO group "Boomi Admins"
- **Pages:**
  7. Admin Approval Queue
  8. Mapping Viewer
- **Purpose:** Final approval gate — approve/deny deployments after peer review passes, view/manage component mappings

## Flow Values (State Variables)

Flow values are used to maintain state across pages and message steps.

| Variable Name | Type | Purpose |
|--------------|------|---------|
| `selectedDevAccountId` | String | Currently selected developer account ID |
| `selectedDevAccountName` | String | Display name for selected developer account |
| `selectedPackage` | Object | Selected package from browser (includes componentId, packageId, componentName, packageVersion, createdBy) |
| `dependencyTree` | List | Resolved dependency tree from resolveDependencies API call |
| `promotionResults` | Object | Results from executePromotion API call |
| `promotionId` | String | UUID of current promotion run (for audit trail) |
| `deploymentRequest` | Object | Deployment submission data (version, pack, notes, devAccountId, devPackageId, devPackageCreator, devPackageVersion, etc.) |
| `userSsoGroups` | List | User's Azure AD group memberships (from SSO context) |
| `accessibleAccounts` | List | Dev accounts user can access based on SSO groups |
| `componentsCreated` | Integer | Count of components created in promotion |
| `componentsUpdated` | Integer | Count of components updated in promotion |
| `componentsFailed` | Integer | Count of components that failed in promotion |
| `totalComponents` | Integer | Total count of components in promotion |
| `sharedConnections` | List | Connections with pre-seeded mappings (from resolveDependencies); displayed as shared/pre-mapped in UI |
| `unmappedConnections` | List | Connections missing mappings (from resolveDependencies); blocks promotion if non-empty |
| `connectionsSkipped` | Integer | Count of shared connections not promoted (from executePromotion response) |
| `peerReviewerEmail` | String | Email of authenticated peer reviewer (from `$User/Email` in Peer Review swimlane) |
| `peerReviewerName` | String | Display name of peer reviewer (from `$User/First Name` + `$User/Last Name`) |
| `peerReviewComments` | String | Peer reviewer's comments on the promotion |
| `peerReviewStatus` | String | Current peer review status (PENDING_PEER_REVIEW, PEER_APPROVED, PEER_REJECTED) |
| `pendingPeerReviews` | List | Peer review queue data from queryPeerReviewQueue (excludes own submissions) |
| `selectedPeerReview` | Object | Currently selected promotion in the peer review queue |
| `branchId` | String | Promotion branch ID returned by executePromotion — used for diff API calls and branch cleanup |
| `branchName` | String | Promotion branch name (e.g., "promo-{promotionId}") |
| `diffBranchXml` | String | Normalized XML from promotion branch (from generateComponentDiff response) |
| `diffMainXml` | String | Normalized XML from main branch (from generateComponentDiff response) |
| `selectedDiffComponent` | Object | Currently selected component for diff viewing (prodComponentId, componentName, componentAction) |
| `availableIntegrationPacks` | List | Integration Packs from listIntegrationPacks (Process J) for Page 4 combobox |
| `suggestedPackId` | String | Suggested Integration Pack ID for current process (from listIntegrationPacks) |

## Flow Navigation (Step-by-Step)

### Developer Flow Path

1. **START** → Developer Swimlane → **Page 1 (Package Browser)**
   - On load: Message step → `getDevAccounts`
   - Store accessible accounts, display account selector and package list

2. **Page 1** → "Review for Promotion" button → **Page 2 (Promotion Review)**
   - On load: Message step → `resolveDependencies`
   - Display dependency tree and summary

3. **Page 2** → "Promote" button → Message step (`executePromotion`) → **Page 3 (Promotion Status)**
   - Process C creates promotion branch, promotes components to branch (not main) via tilde syntax
   - Shows spinner during execution
   - On completion: display results grid, summary, and branchId/branchName
   - "View Diff" links in each component row call `generateComponentDiff` on demand

4. **Page 2** → "Cancel" button → **Page 1**

5. **Page 3** → "Submit for Integration Pack Deployment" → **Page 4 (Deployment Submission)**
   - Only enabled if all components succeeded
   - Carries forward `branchId` and `branchName` Flow values

6. **Page 3** → "Done" → **End flow**

7. **Page 4** → "Submit for Peer Review" → Email notification → **Peer Review Swimlane** → **Page 5**
   - Flow pauses at swimlane boundary
   - Requires peer reviewer authentication (Boomi Developers OR Boomi Admins) to continue

### Peer Review Flow Path

8. **Page 5 (Peer Review Queue)** → Select pending review → **Page 6 (Peer Review Detail)**
   - On load: Message step → `queryPeerReviewQueue` (excludes own submissions via `$User/Email`)
   - Decision step: compare `$User/Email` with `selectedPeerReview.initiatedBy` — if equal, block with error "You cannot review your own submission"

9. **Page 6 (Peer Review Detail)** → "Approve" → Message step (`submitPeerReview` with decision=APPROVED) → Email to admins + submitter → **Admin Swimlane** → **Page 7**
   - "View Diff" links call `generateComponentDiff` for branch-vs-main comparison
   - Flow pauses at swimlane boundary
   - Requires admin authentication to continue

10. **Page 6** → "Reject" → Modal with required rejection reason → Message step (`submitPeerReview` with decision=REJECTED) → `DELETE /Branch/{branchId}` → Email to submitter → **End flow**
    - Branch deleted — main remains untouched

### Admin Flow Path

11. **Page 7 (Admin Approval Queue)** → "Approve" → Merge branch → main → Message step (`packageAndDeploy`) → Delete branch → Show results → **End**
    - On load: Message step → `queryStatus` with `adminReviewStatus` = "PENDING_ADMIN_REVIEW"
    - "View Diff" links call `generateComponentDiff` for branch-vs-main comparison
    - Approve workflow: `POST /MergeRequest` (OVERRIDE) → execute merge → `packageAndDeploy` (from main) → `DELETE /Branch/{branchId}`
    - Email notification sent to submitter + peer reviewer

12. **Page 7** → "Deny" → `DELETE /Branch/{branchId}` → Notification to submitter + peer reviewer → **End**
    - Branch deleted — main remains untouched

13. **Page 8 (Mapping Viewer)** accessible from Admin swimlane navigation
    - Independent page for viewing/managing component mappings

## Message Steps (Integration Calls)

All Message steps use the Boomi Integration Service connector. Each generates Request/Response types automatically.

### 1. Get Dev Accounts
- **Step name:** `Get Dev Accounts`
- **Message Action:** `getDevAccounts`
- **Used in:** Page 1 load
- **Request Type:** `GetDevAccountsRequest` (auto-generated)
- **Response Type:** `GetDevAccountsResponse` (auto-generated)
- **Input values:**
  - `userSsoGroups` (from authorization context)
- **Output values:**
  - `accessibleAccounts` (list of dev accounts)

### 2. List Packages
- **Step name:** `List Packages`
- **Message Action:** `listDevPackages`
- **Used in:** Page 1, on account selection change
- **Request Type:** `ListDevPackagesRequest` (auto-generated)
- **Response Type:** `ListDevPackagesResponse` (auto-generated)
- **Input values:**
  - `selectedDevAccountId`
- **Output values:**
  - `packages` (array of package objects)

### 3. Resolve Dependencies
- **Step name:** `Resolve Dependencies`
- **Message Action:** `resolveDependencies`
- **Used in:** Page 2 load
- **Request Type:** `ResolveDependenciesRequest` (auto-generated)
- **Response Type:** `ResolveDependenciesResponse` (auto-generated)
- **Input values:**
  - `selectedPackage.componentId`
  - `selectedDevAccountId`
- **Output values:**
  - `dependencyTree` (list of components with metadata)
  - `totalComponents`
  - `newCount`
  - `updateCount`
  - `envConfigCount`

### 4. Execute Promotion
- **Step name:** `Execute Promotion`
- **Message Action:** `executePromotion`
- **Used in:** Between Page 2 and Page 3 (on "Promote" button)
- **Request Type:** `ExecutePromotionRequest` (auto-generated)
- **Response Type:** `ExecutePromotionResponse` (auto-generated)
- **Input values:**
  - `selectedPackage.componentId`
  - `selectedDevAccountId`
  - `dependencyTree`
- **Output values:**
  - `promotionId` (UUID)
  - `promotionResults` (array of component results)
  - `componentsCreated`
  - `componentsUpdated`
  - `componentsFailed`
  - `branchId` (promotion branch ID)
  - `branchName` (branch name, e.g., "promo-{promotionId}")

### 5. Query Status
- **Step name:** `Query Status`
- **Message Action:** `queryStatus`
- **Used in:** Page 7 load (admin approval queue)
- **Request Type:** `QueryStatusRequest` (auto-generated)
- **Response Type:** `QueryStatusResponse` (auto-generated)
- **Input values:**
  - `status` = "COMPLETED"
  - `deployed` = false
  - `reviewStage` = "PENDING_ADMIN_REVIEW" (optional filter for 2-layer approval)
- **Output values:**
  - `promotions` (array of pending approval requests)

### 6. Package and Deploy
- **Step name:** `Package and Deploy`
- **Message Action:** `packageAndDeploy`
- **Used in:** Page 5, on "Approve" button click
- **Request Type:** `PackageAndDeployRequest` (auto-generated)
- **Response Type:** `PackageAndDeployResponse` (auto-generated)
- **Input values:**
  - `promotionId`
  - `deploymentRequest` (version, pack, account group, notes)
  - `adminComments`
- **Output values:**
  - `deploymentResults` (success/failure status)
  - `deploymentId` (UUID)

### 7. Manage Mappings
- **Step name:** `Manage Mappings`
- **Message Action:** `manageMappings`
- **Used in:** Page 8 load and CRUD actions
- **Request Type:** `ManageMappingsRequest` (auto-generated)
- **Response Type:** `ManageMappingsResponse` (auto-generated)
- **Input values:**
  - `operation` ("list", "create", "update", "delete")
  - `mapping` (object with mapping data, for create/update)
- **Output values:**
  - `mappings` (array of ComponentMapping records)

### 8. Query Peer Review Queue
- **Step name:** `Query Peer Review Queue`
- **Message Action:** `queryPeerReviewQueue`
- **Used in:** Page 5 load (peer review queue)
- **Request Type:** `QueryPeerReviewQueueRequest` (auto-generated)
- **Response Type:** `QueryPeerReviewQueueResponse` (auto-generated)
- **Input values:**
  - `requesterEmail` (from `$User/Email` — used to exclude own submissions from results)
- **Output values:**
  - `pendingPeerReviews` (array of promotions awaiting peer review)

### 9. Submit Peer Review
- **Step name:** `Submit Peer Review`
- **Message Action:** `submitPeerReview`
- **Used in:** Page 6, on Approve/Reject button click
- **Request Type:** `SubmitPeerReviewRequest` (auto-generated)
- **Response Type:** `SubmitPeerReviewResponse` (auto-generated)
- **Input values:**
  - `promotionId` (from `selectedPeerReview.promotionId`)
  - `decision` ("APPROVED" or "REJECTED")
  - `reviewerEmail` (from `$User/Email`)
  - `reviewerName` (from `$User/First Name` + `$User/Last Name`)
  - `comments` (optional, from `peerReviewComments`)
- **Output values:**
  - `success` (boolean)
  - `promotionId` (string)
  - `newStatus` (string — PEER_APPROVED or PEER_REJECTED)

### 10. Generate Component Diff
- **Step name:** `Generate Component Diff`
- **Message Action:** `generateComponentDiff`
- **Used in:** Pages 3, 6, 7 — on-demand per component click ("View Diff" link)
- **Request Type:** `GenerateComponentDiffRequest` (auto-generated)
- **Response Type:** `GenerateComponentDiffResponse` (auto-generated)
- **Input values:**
  - `branchId` (from `branchId` Flow value or promotion record)
  - `prodComponentId` (from selected component row)
  - `componentName` (from selected component row)
  - `componentAction` ("CREATE" or "UPDATE")
- **Output values:**
  - `diffBranchXml` (normalized XML from promotion branch)
  - `diffMainXml` (normalized XML from main branch; empty for CREATE)
  - `branchVersion` (version on branch)
  - `mainVersion` (version on main; 0 for CREATE)

### 11. List Integration Packs
- **Step name:** `List Integration Packs`
- **Message Action:** `listIntegrationPacks`
- **Used in:** Page 4 load (Deployment Submission)
- **Request Type:** `ListIntegrationPacksRequest` (auto-generated)
- **Response Type:** `ListIntegrationPacksResponse` (auto-generated)
- **Input values:**
  - `suggestForProcess` (from `processName` — the promoted process name)
- **Output values:**
  - `availableIntegrationPacks` (array of Integration Pack objects)
  - `suggestedPackId` (most recently used pack for this process, if any)
  - `suggestedPackName` (name of the suggested pack)

## Decision Steps

After each Message step that can fail, add a Decision step to handle errors gracefully.

### Decision Logic
- **Condition:** `{responseObject.success} == true`
- **True path:** Continue normal flow to next page/step
- **False path:** Navigate to Error Page with `{responseObject.errorMessage}`

### Affected Message Steps
- Get Dev Accounts → Decision → (Success: Page 1 | Failure: Error Page)
- List Packages → Decision → (Success: Display grid | Failure: Error Page)
- Resolve Dependencies → Decision → (Success: Page 2 | Failure: Error Page)
- Execute Promotion → Decision → (Success: Page 3 | Failure: Error Page)
- Query Peer Review Queue → Decision → (Success: Page 5 | Failure: Error Page)
- Submit Peer Review → Decision → (Success: Transition to Admin swimlane or End | Failure: Error Page)
- Query Status → Decision → (Success: Page 7 | Failure: Error Page)
- Package and Deploy → Decision → (Success: Results display | Failure: Error Page)
- Manage Mappings → Decision → (Success: Update grid | Failure: Error Page)
- Generate Component Diff → Decision → (Success: Render XmlDiffViewer | Failure: Show error in panel)
- List Integration Packs → Decision → (Success: Populate combobox | Failure: Show error, allow manual entry)

## Email Notifications

The 2-layer approval workflow generates 5 email notifications at different stages.

### 1. Submission for Peer Review
- **Trigger:** Page 4 → "Submit for Peer Review" button click
- **To:** Dev + Admin distribution lists (e.g., boomi-developers@company.com, boomi-admins@company.com)
- **CC:** Submitter (for confirmation)
- **Subject:** `"Peer Review Needed: {processName} v{packageVersion}"`
- **Body:**
  ```
  A new promotion has been submitted for peer review.

  Submitter: {submitterName} ({submitterEmail})
  Process: {processName}
  Version: {packageVersion}
  Total Components: {totalComponents}
  Created: {componentsCreated}
  Updated: {componentsUpdated}
  Promotion ID: {promotionId}

  Deployment Notes:
  {deploymentRequest.notes}

  Please review in the Promotion Dashboard.
  ```

### 2. Peer Review Approved
- **Trigger:** Page 6 → Peer reviewer clicks "Approve"
- **To:** Admin distribution list (boomi-admins@company.com) + Submitter email
- **Subject:** `"Peer Approved — Admin Review Needed: {processName} v{packageVersion}"`
- **Body:**
  ```
  A promotion has passed peer review and is ready for admin approval.

  Process: {processName}
  Version: {packageVersion}
  Promotion ID: {promotionId}
  Submitted by: {submitterName} ({submitterEmail})

  PEER REVIEW:
  Reviewed by: {peerReviewerName} ({peerReviewerEmail})
  Decision: APPROVED
  Comments: {peerReviewComments or "No comments provided."}

  Please review and approve/deny deployment in the Promotion Dashboard.
  ```

### 3. Peer Review Rejected
- **Trigger:** Page 6 → Peer reviewer clicks "Reject"
- **To:** Submitter email
- **Subject:** `"Peer Review Rejected: {processName} v{packageVersion}"`
- **Body:**
  ```
  Your promotion request has been rejected during peer review.

  Process: {processName}
  Version: {packageVersion}
  Promotion ID: {promotionId}

  PEER REVIEW:
  Reviewed by: {peerReviewerName} ({peerReviewerEmail})
  Decision: REJECTED
  Reason: {peerReviewComments}

  Please address the feedback and resubmit if needed.
  ```

### 4. Admin Approved and Deployed
- **Trigger:** Page 7 → Admin clicks "Approve and Deploy"
- **To:** Submitter email + Peer reviewer email
- **Subject:** `"Approved & Deployed: {processName} v{packageVersion}"`
- **Body:**
  ```
  Your promotion request has been approved and deployed.

  PROMOTION DETAILS:
  Promotion ID: {promotionId}
  Process: {processName}
  Package Version: {packageVersion}
  Deployment ID: {deploymentId}
  Prod Package ID: {prodPackageId}

  PEER REVIEW:
  Reviewed by: {peerReviewerName} ({peerReviewerEmail})

  ADMIN APPROVAL:
  Approved by: {adminUserName} ({adminUserEmail})
  Date: {adminApprovedAt}
  Comments: {adminComments or "No comments provided."}

  Status: Successfully deployed
  ```

### 5. Admin Denied
- **Trigger:** Page 7 → Admin clicks "Deny"
- **To:** Submitter email + Peer reviewer email
- **Subject:** `"Admin Denied: {processName} v{packageVersion}"`
- **Body:**
  ```
  Your promotion request has been denied by admin review.

  PROMOTION DETAILS:
  Promotion ID: {promotionId}
  Process: {processName}
  Package Version: {packageVersion}

  PEER REVIEW:
  Reviewed by: {peerReviewerName} ({peerReviewerEmail})

  ADMIN DENIAL:
  Denied by: {adminUserName} ({adminUserEmail})
  Reason: {denialReason}
  Comments: {adminComments or "No additional comments."}

  Please address the issues mentioned and resubmit if needed.
  ```

## Error Page (Shared)

### Purpose
Display error messages from failed Message steps in a user-friendly way.

### Components
- **Error Icon:** Large warning/error icon
- **Error Title:** "An error occurred"
- **Error Message:** `{responseObject.errorMessage}` (from failed Message step)
- **Technical Details (collapsible):** Full error stack trace or details for debugging

### Actions
- **Back Button:** Returns to previous page (use Flow history navigation)
- **Retry Button:** Re-executes the failed Message step with same input values
- **Home Button:** Returns to Page 1 (Package Browser)

### Layout
- Centered error display
- Clear visual hierarchy (icon → title → message → actions)
- Buttons bottom-aligned

## State Persistence

Flow Service automatically handles state persistence:
- **IndexedDB caching:** State cached every 30 seconds
- **Browser close:** User can close browser during long operations
- **Resume capability:** User can return to same URL to see results
- **Async operations:** Flow Service sends wait responses during long-running operations (e.g., promotion execution)

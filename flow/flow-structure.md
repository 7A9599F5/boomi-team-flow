# Promotion Dashboard - Flow Application Structure

## Overview

The Promotion Dashboard is a single Flow application with two swimlanes designed to facilitate component promotion from developer accounts to production. The application uses the Boomi Integration Service connector for all backend communication and Azure AD/Entra SSO for authentication.

**Key Facts:**
- 1 Flow application
- 2 Swimlanes (Developer, Admin)
- 6 pages total (4 developer pages, 2 admin pages)
- All backend calls via Boomi Integration Service connector
- SSO-based authorization via Azure AD groups

## Swimlanes

### Developer Swimlane
- **Authorization:** SSO group "Boomi Developers"
- **Pages:**
  1. Package Browser
  2. Promotion Review
  3. Promotion Status
  4. Deployment Submission
- **Purpose:** Browse packages, review dependencies, execute promotion, submit for deployment

### Admin Swimlane
- **Authorization:** SSO group "Boomi Admins"
- **Pages:**
  1. Approval Queue
  2. Mapping Viewer
- **Purpose:** Approve/deny deployments, view/manage component mappings

## Flow Values (State Variables)

Flow values are used to maintain state across pages and message steps.

| Variable Name | Type | Purpose |
|--------------|------|---------|
| `selectedDevAccountId` | String | Currently selected developer account ID |
| `selectedDevAccountName` | String | Display name for selected developer account |
| `selectedPackage` | Object | Selected package from browser (includes componentId, packageId, componentName, packageVersion) |
| `dependencyTree` | List | Resolved dependency tree from resolveDependencies API call |
| `promotionResults` | Object | Results from executePromotion API call |
| `promotionId` | String | UUID of current promotion run (for audit trail) |
| `deploymentRequest` | Object | Deployment submission data (version, pack, notes, etc.) |
| `userSsoGroups` | List | User's Azure AD group memberships (from SSO context) |
| `accessibleAccounts` | List | Dev accounts user can access based on SSO groups |
| `componentsCreated` | Integer | Count of components created in promotion |
| `componentsUpdated` | Integer | Count of components updated in promotion |
| `componentsFailed` | Integer | Count of components that failed in promotion |
| `totalComponents` | Integer | Total count of components in promotion |
| `sharedConnections` | List | Connections with pre-seeded mappings (from resolveDependencies); displayed as shared/pre-mapped in UI |
| `unmappedConnections` | List | Connections missing mappings (from resolveDependencies); blocks promotion if non-empty |
| `connectionsSkipped` | Integer | Count of shared connections not promoted (from executePromotion response) |

## Flow Navigation (Step-by-Step)

### Developer Flow Path

1. **START** → Developer Swimlane → **Page 1 (Package Browser)**
   - On load: Message step → `getDevAccounts`
   - Store accessible accounts, display account selector and package list

2. **Page 1** → "Review for Promotion" button → **Page 2 (Promotion Review)**
   - On load: Message step → `resolveDependencies`
   - Display dependency tree and summary

3. **Page 2** → "Promote" button → Message step (`executePromotion`) → **Page 3 (Promotion Status)**
   - Shows spinner during execution
   - On completion: display results grid and summary

4. **Page 2** → "Cancel" button → **Page 1**

5. **Page 3** → "Submit for Integration Pack Deployment" → **Page 4 (Deployment Submission)**
   - Only enabled if all components succeeded

6. **Page 3** → "Done" → **End flow**

7. **Page 4** → "Submit for Approval" → Email notification → **Admin Swimlane** → **Page 5**
   - Flow pauses at swimlane boundary
   - Requires admin authentication to continue

### Admin Flow Path

8. **Page 5 (Approval Queue)** → "Approve" → Message step (`packageAndDeploy`) → Show results → **End**
   - Email notification sent to submitter

9. **Page 5** → "Deny" → Notification to submitter → **End**

10. **Page 6 (Mapping Viewer)** accessible from Admin swimlane navigation
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

### 5. Query Status
- **Step name:** `Query Status`
- **Message Action:** `queryStatus`
- **Used in:** Page 5 load (approval queue)
- **Request Type:** `QueryStatusRequest` (auto-generated)
- **Response Type:** `QueryStatusResponse` (auto-generated)
- **Input values:**
  - `status` = "COMPLETED"
  - `deployed` = false
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
- **Used in:** Page 6 load and CRUD actions
- **Request Type:** `ManageMappingsRequest` (auto-generated)
- **Response Type:** `ManageMappingsResponse` (auto-generated)
- **Input values:**
  - `operation` ("list", "create", "update", "delete")
  - `mapping` (object with mapping data, for create/update)
- **Output values:**
  - `mappings` (array of ComponentMapping records)

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
- Query Status → Decision → (Success: Page 5 | Failure: Error Page)
- Package and Deploy → Decision → (Success: Results display | Failure: Error Page)
- Manage Mappings → Decision → (Success: Update grid | Failure: Error Page)

## Email Notification

### Trigger
Page 4 → "Submit for Approval" button click

### Configuration
- **To:** Admin SSO group email distribution list (e.g., boomi-admins@company.com)
- **Subject:** `"Promotion Approval Needed: {processName} v{packageVersion}"`
- **Body:**
  ```
  A new promotion has been submitted for approval.

  Submitter: {submitterName} ({submitterEmail})
  Process: {processName}
  Version: {packageVersion}
  Total Components: {totalComponents}
  Created: {componentsCreated}
  Updated: {componentsUpdated}
  Promotion ID: {promotionId}

  Deployment Notes:
  {deploymentRequest.notes}

  Please review and approve/deny in the Promotion Dashboard.
  ```

### Response Notifications

**On Approval:**
- **To:** Submitter email
- **Subject:** `"Approved: {processName} v{packageVersion}"`
- **Body:**
  ```
  Your promotion request has been approved and deployed.

  Process: {processName}
  Approved by: {adminName}
  Deployment ID: {deploymentId}

  Admin Comments:
  {adminComments}
  ```

**On Denial:**
- **To:** Submitter email
- **Subject:** `"Denied: {processName} v{packageVersion}"`
- **Body:**
  ```
  Your promotion request has been denied.

  Process: {processName}
  Denied by: {adminName}

  Reason:
  {denialReason}

  Admin Comments:
  {adminComments}
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

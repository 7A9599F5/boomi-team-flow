# Promotion Dashboard Flow Patterns

This document provides project-specific Flow patterns for the Boomi Dev-to-Prod Component Promotion System.

---

## Application Structure

**Flow Application:** Boomi Promotion Dashboard

**Swimlanes (3):**
1. **Developer** (SSO group: "Boomi Developers")
2. **Peer Review** (SSO groups: "Boomi Developers" OR "Boomi Admins")
3. **Admin** (SSO group: "Boomi Admins")

**Pages (8):**
1. Package Browser (Developer)
2. Promotion Review (Developer)
3. Promotion Status (Developer)
4. Deployment (Developer)
5. Peer Review Queue (Peer Review)
6. Peer Review Detail (Peer Review)
7. Admin Approval Queue (Admin)
8. Mapping Viewer (Admin, read-only)

**Flow Service:**
- Path to Service: `/promotion-service`
- 11 Message Actions (A0, A-G, E2, E3, J)

---

## Flow Values

### Core Promotion Values

| Variable | Type | Set By | Used By |
|----------|------|--------|---------|
| `selectedDevAccountId` | String | Page 1 (dropdown selection) | All message steps |
| `selectedDevAccountName` | String | Page 1 (from getDevAccounts response) | Page headers |
| `packagesList` | List | Message: listDevPackages | Page 1 data grid |
| `selectedPackage` | Object | Page 1 (data grid selection) | Pages 2-4 |
| `dependencyTree` | List | Message: resolveDependencies | Pages 2-3 |
| `promotionResults` | Object | Message: executePromotion | Page 3 |
| `promotionId` | String | Message: executePromotion | Pages 3-6 |
| `branchId` | String | Message: executePromotion | Page 6 (diff view) |
| `deploymentRequest` | Object | Page 4 (form inputs) | Message: packageAndDeploy |

### Peer Review Values

| Variable | Type | Set By | Used By |
|----------|------|--------|---------|
| `peerReviewQueue` | List | Message: queryPeerReviewQueue | Page 5 data grid |
| `selectedPeerReview` | Object | Page 5 (data grid selection) | Page 6 |
| `peerReviewerEmail` | String | Page 6 (from `$User/Email`) | Message: submitPeerReview |
| `peerReviewerName` | String | Page 6 (from `$User/First Name + Last Name`) | Message: submitPeerReview |
| `reviewNotes` | String | Page 6 (text area input) | Message: submitPeerReview |
| `diffData` | Object | Message: generateComponentDiff | Page 6 (XmlDiffViewer component) |

### Admin Values

| Variable | Type | Set By | Used By |
|----------|------|--------|---------|
| `adminApprovalQueue` | List | Message: queryStatus (filter: APPROVED_FOR_DEPLOYMENT) | Page 7 data grid |
| `selectedAdminApproval` | Object | Page 7 (data grid selection) | Page 7 deployment |
| `integrationPacksList` | List | Message: listIntegrationPacks | Page 7 dropdown |
| `selectedIntegrationPack` | Object | Page 7 (dropdown selection) | Message: packageAndDeploy |

---

## Swimlane Patterns

### Pattern 1: Developer Swimlane (Submit Promotion)

**Authorization:** SSO group: "Boomi Developers"

**Flow:**

```
Page 1: Package Browser
  ↓ (User selects package)
Button: "Review and Promote"
  ↓
Page 2: Promotion Review
  ↓ (On page load)
Message Step: resolveDependencies
  Request: { componentId, devAccountId }
  Response: { dependencyTree: [...] }
  ↓ (User reviews dependencies, adds notes)
Button: "Promote"
  ↓
Message Step: executePromotion (async, 5+ minutes)
  Request: { componentId, devAccountId, dependencyTree }
  Response: Wait response → Final response
  ↓
Page 3: Promotion Status
  ↓ (User reviews results)
Button: "Submit for Peer Review"
  ↓ (Email notification sent to all Boomi Developers)
Swimlane Transition: Developer → Peer Review
```

**Key patterns:**
- **On page load message steps**: Page 2 calls `resolveDependencies` to populate dependency tree
- **Async operations**: `executePromotion` returns wait response, Flow shows spinner, user can close browser
- **State persistence**: Flow caches state to IndexedDB every 30 seconds
- **Swimlane transition**: Flow pauses until peer reviewer authenticates

### Pattern 2: Peer Review Swimlane (2-Layer Approval)

**Authorization:** SSO groups: "Boomi Developers" OR "Boomi Admins"

**Flow:**

```
(Flow paused until peer reviewer authenticates)
  ↓
Page 5: Peer Review Queue
  ↓ (On page load)
Message Step: queryPeerReviewQueue
  Request: { reviewStage: "PENDING_PEER_REVIEW", excludeSubmittedBy: $User/Email }
  Response: { promotions: [...] } (excludes own submissions)
  ↓ (User selects promotion to review)
Button: "Review"
  ↓
Decision Step: Check Self-Review
  Outcome A (Allow): selectedPeerReview.initiatedBy != $User/Email → Page 6
  Outcome B (Block): selectedPeerReview.initiatedBy == $User/Email → Error Page
  ↓
Page 6: Peer Review Detail
  ↓ (On page load)
Message Step: generateComponentDiff
  Request: { componentId, branchId, devAccountId }
  Response: { branchXml, mainXml, componentName, componentAction }
  ↓ (User reviews diff, adds notes)
Button: "Approve" or "Reject"
  ↓
Message Step: submitPeerReview
  Request: { promotionId, reviewAction, reviewedBy, reviewNotes }
  Response: { success: true }
  ↓ (Email notification sent to Boomi Admins)
Swimlane Transition: Peer Review → Admin
```

**Key patterns:**
- **Self-review prevention**: Backend filters out own submissions, frontend blocks access if user tries to review own promotion
- **Diff viewing**: Custom XmlDiffViewer component displays side-by-side XML diff
- **Audit trails**: Store `$User/Email` and `$User/First Name + Last Name` in review record

### Pattern 3: Admin Swimlane (Final Approval and Deployment)

**Authorization:** SSO group: "Boomi Admins"

**Flow:**

```
(Flow paused until admin authenticates)
  ↓
Page 7: Admin Approval Queue
  ↓ (On page load)
Message Step: queryStatus
  Request: { reviewStage: "APPROVED_FOR_DEPLOYMENT" }
  Response: { promotions: [...] }
  ↓
Message Step: listIntegrationPacks (on page load)
  Request: { devAccountId }
  Response: { integrationPacks: [...] }
  ↓ (User selects promotion, selects Integration Pack)
Button: "Deploy"
  ↓
Message Step: packageAndDeploy (async)
  Request: { promotionId, integrationPackId, deploymentNotes }
  Response: Wait response → Final response
  ↓
Page 7: Deployment Complete (results displayed)
```

**Key patterns:**
- **Smart Integration Pack suggestions**: Backend suggests most recent pack used for same dev account
- **Final deployment**: Creates Integration Pack, deploys to production, deletes promotion branch
- **Async deployment**: Similar wait state pattern as promotion execution

---

## Message Action Patterns

### Pattern 1: On Page Load Message Steps

**Use case:** Populate data grid or Flow Values when page loads.

**Example: Page 1 - Package Browser**

```
Page 1: Package Browser
  ↓ (On page load)
Message Step: getDevAccounts
  Request: { ssoGroupId: $User/Groups[0] }  // Assume first group is primary
  Response: { devAccounts: [...] }
  Output: devAccountsList ← response.devAccounts
  ↓ (Auto-select first account)
Flow Value: selectedDevAccountId = devAccountsList[0].accountId
Flow Value: selectedDevAccountName = devAccountsList[0].accountName
  ↓ (Trigger second message step)
Message Step: listDevPackages
  Request: { devAccountId: selectedDevAccountId }
  Response: { packages: [...] }
  Output: packagesList ← response.packages
```

**Implementation:**
- **Page load outcome**: Automatically triggered when page renders
- **Sequential message steps**: Second step depends on first step's response
- **Auto-selection**: First account auto-selected for convenience

### Pattern 2: User-Triggered Message Steps

**Use case:** Call API when user clicks button.

**Example: Page 2 - Promotion Review**

```
Page 2: Promotion Review
  ↓ (User reviews dependency tree)
Button: "Promote"
  ↓ (Button click triggers outcome)
Outcome: "Promote"
  ↓
Message Step: executePromotion
  Request:
  {
    "componentId": selectedPackage.componentId,
    "devAccountId": selectedDevAccountId,
    "dependencyTree": dependencyTree
  }
  Response (wait):
  {
    "status": "WAIT",
    "message": "Promoting components to primary account...",
    "progress": 0
  }
  Response (final):
  {
    "status": "SUCCESS",
    "success": true,
    "promotionId": "uuid",
    "branchId": "uuid",
    "results": [...]
  }
  Output:
    promotionId ← response.promotionId
    branchId ← response.branchId
    promotionResults ← response
  ↓
Page 3: Promotion Status
```

**Implementation:**
- **Outcome binding**: Button click triggers outcome
- **Async handling**: Flow shows wait state, caches state to IndexedDB
- **Result display**: Page 3 displays results from Flow Value

### Pattern 3: Conditional Message Steps (Decision Step)

**Use case:** Call different APIs based on conditions.

**Example: Error Handling After Promotion**

```
Message Step: executePromotion
  Response: promotionResults
  ↓
Decision Step: Check Success
  ↓                              ↓
Outcome A                      Outcome B
(success == true)              (success == false)
  ↓                              ↓
Message Step: queryStatus      Error Page
  Request: { promotionId }       - Display: promotionResults.errorMessage
  Response: { promotionLog }     - Button: "Retry" → Page 2
  ↓
Page 3: Promotion Status
```

**Implementation:**
- **Decision step**: Routes based on message step response
- **Error handling**: Dedicated error page with retry option
- **Success path**: Additional API call to fetch latest status

---

## Custom Component Patterns

### Pattern 1: XmlDiffViewer (Page 6: Peer Review Detail)

**Purpose:** Display side-by-side diff of component XML (branch vs. main).

**Setup:**

```
Page 6: Peer Review Detail
  ↓ (On page load)
Message Step: generateComponentDiff
  Request:
  {
    "componentId": selectedPeerReview.componentId,
    "branchId": selectedPeerReview.branchId,
    "devAccountId": selectedPeerReview.devAccountId
  }
  Response:
  {
    "branchXml": "<bns:Component ...>...</bns:Component>",
    "mainXml": "<bns:Component ...>...</bns:Component>",
    "componentName": "Orders Process",
    "componentAction": "UPDATE",
    "branchVersion": 11,
    "mainVersion": 10
  }
  Output: diffData ← response
  ↓
Page Layout:
  Custom Component: XmlDiffViewer
    - Object Data: diffData
    - Component renders diff when diffData populated
```

**ObjectData binding:**

```tsx
const data = props.getObjectData<DiffData>();
const branchXml = data[0]?.branchXml || '';
const mainXml = data[0]?.mainXml || '';
const componentName = data[0]?.componentName || '';
const componentAction = data[0]?.componentAction || 'CREATE';
```

**Responsive behavior:**
- **Desktop**: Side-by-side diff view
- **Tablet**: Side-by-side with reduced font size
- **Mobile**: Unified diff view only

---

## Wait State Patterns

### Pattern 1: Promotion Execution (Page 2 → Page 3)

**Scenario:** Promoting 50 components takes 5+ minutes.

**Flow:**

```
Page 2: Promotion Review
  ↓
Button: "Promote"
  ↓
Message Step: executePromotion (async)
  ↓
Integration Process C:
  - Count components: 50
  - Return wait response:
    {
      "status": "WAIT",
      "message": "Promoting components to primary account...",
      "progress": 0
    }
  ↓
Flow shows wait state overlay:
  - Spinner animation
  - "Promoting components to primary account..."
  - "This may take several minutes. You can safely close this window."
  ↓
Flow caches state to IndexedDB (every 30 seconds)
  ↓
User closes browser (optional)
  ↓
Integration Process C continues:
  - For-each loop: Promote each component
  - Send progress updates:
    {
      "status": "WAIT",
      "message": "Processing component 10 of 50...",
      "progress": 20
    }
  ↓
Process completes:
  - Return final response:
    {
      "status": "SUCCESS",
      "success": true,
      "promotionId": "uuid",
      "results": [...]
    }
  ↓
User returns to browser, Flow resumes
  ↓
Page 3: Promotion Status (results displayed)
```

**Wait State Overlay (Page 3):**

```
Wait State Overlay (conditional, shown when promotionResults.status == "WAIT"):
  - Spinner animation
  - Message: promotionResults.message
  - Progress bar: promotionResults.progress (if available)
  - Subtext: "This may take several minutes. You can safely close this window."

Results Section (conditional, shown when promotionResults.status == "SUCCESS"):
  - Data Grid: promotionResults.results
  - Summary: componentsPassed, componentsFailed
  - Button: "Submit for Deployment" (enabled if componentsFailed == 0)
```

### Pattern 2: Deployment (Page 7)

**Scenario:** Creating Integration Pack and deploying to production takes 2-3 minutes.

**Flow:**

```
Page 7: Admin Approval Queue
  ↓
Button: "Deploy"
  ↓
Message Step: packageAndDeploy (async)
  ↓
Integration Process D:
  - Merge branch → main
  - Create PackagedComponent
  - Create Integration Pack
  - Deploy Integration Pack
  - Delete promotion branch
  - Return wait response (if > 30 seconds)
  ↓
Flow shows wait state overlay:
  - "Deploying components to production..."
  - "Creating Integration Pack and deploying..."
  ↓
Process completes, returns final response
  ↓
Page 7: Deployment Complete (results displayed)
```

---

## Best Practices from Project

### 1. Self-Review Prevention

**Implementation:**
- **Backend filtering**: `queryPeerReviewQueue` excludes promotions where `initiatedBy == $User/Email`
- **Frontend validation**: Decision step blocks access if user tries to review own promotion
- **Double-check**: Integration process `submitPeerReview` validates `initiatedBy != peerReviewerEmail`

### 2. State Persistence for Long Operations

**Pattern:**
- All async operations (promotion, deployment) use wait responses
- Flow caches state to IndexedDB every 30 seconds
- User messaging: "You can safely close this window"
- Flow resumes automatically when user returns to URL

### 3. Audit Trails

**Pattern:**
- Store `$User/Email`, `$User/First Name + Last Name` in all review/approval steps
- Pass to Integration processes for DataHub logging
- PromotionLog records include full audit trail (initiated by, reviewed by, approved by)

### 4. Smart Suggestions

**Pattern:**
- `listIntegrationPacks` suggests most recent pack used for same dev account
- Auto-select suggested pack in dropdown for convenience
- User can override suggestion if needed

### 5. Error Handling

**Pattern:**
- All message steps have success/failure responses
- Decision steps after message steps route to error page on failure
- Error page displays user-friendly error message with "Retry" and "Home" buttons

### 6. Responsive Design

**Pattern:**
- All pages support mobile, tablet, desktop breakpoints
- Data grids convert to card-based layouts on mobile
- XmlDiffViewer switches to unified-only view on mobile

---

## Sources

- `/home/glitch/code/boomi_team_flow/flow/flow-structure.md` — Full Flow application structure
- `/home/glitch/code/boomi_team_flow/flow/page-layouts/` — Individual page layout specifications
- `/home/glitch/code/boomi_team_flow/flow/custom-components/xml-diff-viewer.md` — XmlDiffViewer specification
- `/home/glitch/code/boomi_team_flow/integration/flow-service/flow-service-spec.md` — Message Action API contract

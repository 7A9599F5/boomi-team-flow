# End-to-End Promotion Workflow

This document provides a complete walkthrough of a promotion from start to finish.

---

## Scenario

**Dev Team A** has created a process called "Order Processor" in their dev sub-account. They package it and request promotion to production.

**Actors:**
- **Dev User:** Jane (DevTeamA sub-account user)
- **Peer Reviewer:** Bob (DevTeamB sub-account user)
- **Admin:** Alice (Primary account admin)

---

## Phase 1: List and Select (Process A)

### Flow Dashboard: Package Browser Page

**Jane navigates to Package Browser page.**

**Flow executes Message Action: `getDevAccounts`**
- Input: `$User.ssoGroupId`
- Process A0 queries DataHub `DevAccountAccess` table
- Output: `[{ devAccountId: "dev-team-a-456", accountName: "DevTeamA" }]`

**Jane selects "DevTeamA" from dropdown.**

**Flow executes Message Action: `listDevPackages`**
- Input: `{ devAccountId: "dev-team-a-456" }`
- Process A queries PackagedComponents via Platform API:
  ```http
  POST /PackagedComponent/query?overrideAccount=dev-team-a-456
  ```
- Output: `[{ packageId: "pkg-123", componentId: "order-processor", packageVersion: "1.0" }]`

**Jane sees list of packages and selects "Order Processor v1.0".**

**Jane clicks "Promote" button.**

---

## Phase 2: Resolve Dependencies (Process B)

**Flow executes Message Action: `resolveDependencies`**
- Input: `{ devPackageId: "pkg-123", devAccountId: "dev-team-a-456" }`

**Process B performs recursive BFS traversal:**

1. **Start with root process** — `order-processor`
2. **Query ComponentReference:**
   ```http
   POST /ComponentReference/query?overrideAccount=dev-team-a-456
   ```
   Returns: `[{ componentId: "sap-conn-789" }, { componentId: "order-map-012" }]`
3. **Add to queue:** `["sap-conn-789", "order-map-012"]`
4. **Repeat for each queued component** until queue is empty
5. **Build visited set:** `["order-processor", "sap-conn-789", "order-map-012", "xml-profile-345"]`

**Sort by type hierarchy:**
```json
[
  { "type": "profile", "devComponentId": "xml-profile-345" },
  { "type": "connection", "devComponentId": "sap-conn-789" },
  { "type": "map", "devComponentId": "order-map-012" },
  { "type": "process", "devComponentId": "order-processor" }
]
```

**Output:** Sorted dependency tree (4 components)

---

## Phase 3: Execute Promotion (Process C)

**Flow executes Message Action: `executePromotion`**
- Input: Sorted dependency tree + promotion metadata

### Step 1: Pre-Check Branch Count

```http
POST /Branch/query
```
**Result:** 12 branches exist (< 18 soft limit) — proceed

---

### Step 2: Create Branch

```http
POST /Branch
Body: { "name": "promo-abc123" }
```

**Response:**
```json
{
  "branchId": "branch-uuid-456",
  "ready": false
}
```

---

### Step 3: Poll for Ready State

```http
GET /Branch/branch-uuid-456
```

**Loop until `ready: true` (takes 3 seconds).**

---

### Step 4: Promote Components to Branch

**For each component in dependency order:**

#### Component 1: XML Profile

**Fetch dev component XML:**
```http
GET /Component/xml-profile-345?overrideAccount=dev-team-a-456
```

**Strip environment config:**
- No passwords/hosts in profiles — skip

**Rewrite references:**
- No dependencies in profiles — skip

**Create on branch:**
```http
POST /Component/prod-profile-678~branch-uuid-456
Body: <Profile XML>
```

**Record mapping in DataHub:**
```json
{
  "devComponentId": "xml-profile-345",
  "prodComponentId": "prod-profile-678",
  "mappingSource": "PROMOTION_ENGINE"
}
```

---

#### Component 2: SAP Connection

**Fetch dev component XML:**
```http
GET /Component/sap-conn-789?overrideAccount=dev-team-a-456
```

**Validate connection mapping:**
- Query DataHub for `devComponentId = "sap-conn-789"`
- **Found:** `prodComponentId = "prod-conn-#connections-abc"`

**Connection is NOT promoted** — filter out.

**Add to mapping cache for reference rewriting:**
```json
{
  "sap-conn-789": "prod-conn-#connections-abc"
}
```

---

#### Component 3: Order Map

**Fetch dev component XML:**
```http
GET /Component/order-map-012?overrideAccount=dev-team-a-456
```

**Strip environment config:**
- No passwords/hosts in maps — skip

**Rewrite references:**
- Map references profile `xml-profile-345`
- Replace with `prod-profile-678` (from mapping cache)

**Create on branch:**
```http
POST /Component/prod-map-901~branch-uuid-456
Body: <Map XML with rewritten references>
```

**Record mapping:**
```json
{
  "devComponentId": "order-map-012",
  "prodComponentId": "prod-map-901",
  "mappingSource": "PROMOTION_ENGINE"
}
```

---

#### Component 4: Order Processor (Root Process)

**Fetch dev component XML:**
```http
GET /Component/order-processor?overrideAccount=dev-team-a-456
```

**Strip environment config:**
- Strip `<password>`, `<host>`, `<url>` fields

**Rewrite references:**
- Process references:
  - Connection: `sap-conn-789` → `prod-conn-#connections-abc`
  - Map: `order-map-012` → `prod-map-901`
  - Profile: `xml-profile-345` → `prod-profile-678`

**Create on branch:**
```http
POST /Component/prod-process-234~branch-uuid-456
Body: <Process XML with rewritten references>
```

**Record mapping:**
```json
{
  "devComponentId": "order-processor",
  "prodComponentId": "prod-process-234",
  "mappingSource": "PROMOTION_ENGINE"
}
```

---

### Step 5: Record PromotionLog

**Create PromotionLog in DataHub:**
```json
{
  "promotionId": "promo-abc123",
  "devPackageId": "pkg-123",
  "devAccountId": "dev-team-a-456",
  "branchId": "branch-uuid-456",
  "status": "PENDING_PEER_REVIEW",
  "reviewStage": "PENDING_PEER_REVIEW",
  "submittedBy": "jane@company.com",
  "submittedDate": "2026-02-16T10:10:00Z"
}
```

**Output:** `{ promotionId: "promo-abc123", branchId: "branch-uuid-456", status: "PENDING_PEER_REVIEW" }`

---

## Phase 4: Peer Review

### Peer Review Queue (Bob)

**Bob navigates to Peer Review Queue page.**

**Flow executes Message Action: `queryPeerReviewQueue`**
- Input: `{ reviewerUserId: "bob@company.com" }`
- Process E2 queries PromotionLog with filter:
  - `reviewStage = "PENDING_PEER_REVIEW"`
  - `submittedBy != "bob@company.com"` (exclude own)
- Output: `[{ promotionId: "promo-abc123", componentName: "Order Processor" }]`

**Bob selects promotion and clicks "View Diff".**

---

### Component Diff (Process G)

**Flow executes Message Action: `generateComponentDiff`**
- Input: `{ componentId: "prod-process-234", branchId: "branch-uuid-456" }`

**Fetch branch version:**
```http
GET /Component/prod-process-234~branch-uuid-456
```

**Fetch main version (if exists):**
```http
GET /Component/prod-process-234
```
**Result:** 404 (component doesn't exist on main yet)

**Normalize branch XML:**
```groovy
def root = new XmlSlurper(false, false).parseText(branchXml)
String normalizedBranch = XmlUtil.serialize(root)
```

**Output:** `{ branchXml: "...", mainXml: "" }`

**Flow renders diff in XmlDiffViewer custom component** — shows all changes as additions (green).

**Bob reviews diff and approves.**

---

### Submit Peer Review (Process E3)

**Flow executes Message Action: `submitPeerReview`**
- Input: `{ promotionId: "promo-abc123", reviewerUserId: "bob@company.com", decision: "APPROVE" }`

**Process E3 validates:**
- Self-review prevention: `submittedBy != reviewerUserId` ✓

**Update PromotionLog:**
```json
{
  "promotionId": "promo-abc123",
  "reviewStage": "PENDING_ADMIN_APPROVAL",
  "peerReviewedBy": "bob@company.com",
  "peerReviewedDate": "2026-02-16T10:15:00Z",
  "peerReviewDecision": "APPROVE"
}
```

---

## Phase 5: Admin Approval

### Admin Approval Queue (Alice)

**Alice navigates to Admin Approval Queue page (Admin swimlane).**

**Flow executes Message Action: `queryStatus`**
- Input: `{ reviewStage: "PENDING_ADMIN_APPROVAL" }`
- Output: `[{ promotionId: "promo-abc123", componentName: "Order Processor" }]`

**Alice selects promotion and approves.**

**Flow executes Message Action: `packageAndDeploy`** (Process D)

---

## Phase 6: Package and Deploy (Process D)

### Step 1: Merge Branch to Main

**Create Merge Request:**
```http
POST /MergeRequest
Body: {
  "sourceBranchId": "branch-uuid-456",
  "destinationBranchId": "main",
  "strategy": "OVERRIDE",
  "priorityBranch": "branch-uuid-456"
}
```

**Execute Merge:**
```http
POST /MergeRequest/execute/{mergeRequestId}
```

**Result:** All components from branch are now on main.

---

### Step 2: Create PackagedComponent

```http
POST /PackagedComponent
Body: {
  "componentId": "prod-process-234",
  "packageVersion": "1.0.0",
  "shareable": true,
  "notes": "Promoted from DevTeamA - Order Processor"
}
```

**Response:** `{ packageId: "prod-pkg-567" }`

---

### Step 3: Create Integration Pack (New)

```http
POST /IntegrationPack
Body: {
  "name": "DevTeamA Order Processing Pack",
  "installationType": "MULTI"
}
```

**Response:** `{ integrationPackId: "prod-pack-890" }`

---

### Step 4: Add to Integration Pack

```http
POST /IntegrationPack/prod-pack-890/PackagedComponent/prod-pkg-567
```

---

### Step 5: Release Integration Pack

```http
POST /ReleaseIntegrationPack
Body: {
  "integrationPackId": "prod-pack-890",
  "version": "1.0.0"
}
```

---

### Step 6: Deploy to Environments

**For Production environment:**
```http
POST /DeployedPackage
Body: {
  "packageId": "prod-pack-890",
  "environmentId": "prod-env-111"
}
```

---

### Step 7: Delete Branch

```http
DELETE /Branch/branch-uuid-456
```

**Update PromotionLog:**
```json
{
  "promotionId": "promo-abc123",
  "status": "COMPLETED",
  "branchId": null,  // Cleared after deletion
  "completedDate": "2026-02-16T10:20:00Z"
}
```

---

## Summary

**Timeline:**
- 10:00 — Jane selects package
- 10:05 — Process B resolves dependencies
- 10:10 — Process C creates branch and promotes components
- 10:15 — Bob peer reviews and approves
- 10:20 — Alice admin approves, Process D packages and deploys

**Components Promoted:** 3 (profile, map, process)
**Connections Skipped:** 1 (SAP connection — admin-seeded mapping)
**Branch Lifecycle:** Created → Ready → Promoted → Merged → Deleted

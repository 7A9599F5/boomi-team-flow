# Boomi Branching and Merge Lifecycle

## Complete Branch Lifecycle

### Step 1: Pre-Check Branch Count

**Constraint:** Boomi enforces a **maximum of 20 branches per account**.

**Pre-Check Query:**
```http
POST /partner/api/rest/v1/{primaryAccountId}/Branch/query
Body: <QueryFilter xmlns='http://api.platform.boomi.com/'/>
```

**If count >= 18, abort:**
```json
{
  "errorCode": "BRANCH_LIMIT_REACHED",
  "errorMessage": "Too many active promotions. Please wait for pending reviews to complete."
}
```

**Why 18, not 20?** Leave buffer for other operations (manual branches, concurrent promotions).

---

### Step 2: Create Branch

```http
POST /partner/api/rest/v1/{primaryAccountId}/Branch
Content-Type: application/json

{
  "name": "promo-abc123"
}
```

**Response:**
```json
{
  "@type": "Branch",
  "branchId": "branch-uuid-456",
  "name": "promo-abc123",
  "ready": false,
  "createdDate": "2026-02-16T10:00:00Z",
  "createdBy": "admin@company.com"
}
```

**Key Field:** `ready: false` — branch is NOT immediately writable.

---

### Step 3: Poll for Ready State

New branches start with `ready: false`. You MUST poll until `ready: true` before writing components.

```http
GET /partner/api/rest/v1/{primaryAccountId}/Branch/{branchId}
```

**Poll every 2-5 seconds:**
```javascript
let ready = false;
while (!ready) {
    const response = await GET `/Branch/${branchId}`;
    ready = response.ready;
    if (!ready) await sleep(2000);  // Wait 2 seconds
}
```

**Typical wait time:** 1-5 seconds, but can be longer under load.

---

### Step 4: Promote Components to Branch (Tilde Syntax)

**Tilde Syntax:** `{componentId}~{branchId}`

**Create/Update Component on Branch:**
```http
POST /partner/api/rest/v1/{primaryAccountId}/Component/{componentId}~{branchId}
Content-Type: application/xml

<bns:Component ...>
  <bns:componentId>{componentId}</bns:componentId>
  <bns:name>Order Processor</bns:name>
  <!-- ... component configuration ... -->
</bns:Component>
```

**Effect:** Creates or updates component on the specified branch, not main.

**Reading from Branch:**
```http
GET /partner/api/rest/v1/{primaryAccountId}/Component/{componentId}~{branchId}
```

**Without tilde syntax:**
```http
GET /partner/api/rest/v1/{primaryAccountId}/Component/{componentId}
```
Returns the main version.

---

### Step 5: Create Merge Request

```http
POST /partner/api/rest/v1/{primaryAccountId}/MergeRequest
Content-Type: application/json

{
  "sourceBranchId": "branch-uuid-456",
  "destinationBranchId": "main",
  "strategy": "OVERRIDE",
  "priorityBranch": "branch-uuid-456"
}
```

**Fields:**
- `sourceBranchId`: Branch to merge from (promotion branch)
- `destinationBranchId`: Branch to merge into (typically `"main"`)
- `strategy`: `OVERRIDE` or `CONFLICT_RESOLVE`
- `priorityBranch`: Which branch wins in conflicts (for OVERRIDE strategy)

**Merge Strategies:**
- **OVERRIDE:** Priority branch completely overwrites destination. No conflict resolution needed.
- **CONFLICT_RESOLVE:** Manual conflict resolution required (not used in this project).

**Why OVERRIDE?** Process C is the sole writer to the promotion branch. There are no conflicts — branch always wins.

**Response:**
```json
{
  "@type": "MergeRequest",
  "id": "merge-request-uuid",
  "sourceBranchId": "branch-uuid-456",
  "destinationBranchId": "main",
  "strategy": "OVERRIDE",
  "stage": "DRAFTED",
  "createdDate": "2026-02-16T10:05:00Z"
}
```

**Merge Stages:**
- `DRAFTING` → `DRAFTED` → `REVIEWING` → `MERGING` → `MERGED` or `FAILED_TO_MERGE`

---

### Step 6: Execute Merge

```http
POST /partner/api/rest/v1/{primaryAccountId}/MergeRequest/execute/{mergeRequestId}
```

**No request body required.**

**Response:**
```json
{
  "@type": "MergeRequest",
  "id": "merge-request-uuid",
  "stage": "MERGED"
}
```

**Merge Flow:**
1. CREATE MergeRequest → `stage: DRAFTED`
2. EXECUTE MergeRequest → `stage: MERGING` → `stage: MERGED`
3. Components from branch are now on main

---

### Step 7: Delete Branch

**CRITICAL:** Always delete branch to free up branch slots.

```http
DELETE /partner/api/rest/v1/{primaryAccountId}/Branch/{branchId}
```

**When to Delete:**
- **Peer approval** → (continue to admin review, don't delete yet)
- **Peer rejection** → delete immediately
- **Admin approval** → merge → delete
- **Admin denial** → delete immediately
- **Process C failure** → delete immediately

**Tracking:** `branchId` field in PromotionLog. Set to `null` after deletion.

---

## Terminal Path Cleanup

All terminal paths MUST delete the branch:

```
Approve Path (Admin):
  Peer Approve → Admin Approve → Merge → Delete Branch

Reject Path (Peer):
  Peer Reject → Delete Branch

Deny Path (Admin):
  Admin Deny → Delete Branch

Failure Path:
  Process C Failure → Delete Branch
```

**Failure to delete branches** will exhaust the 20-branch limit and block all future promotions.

---

## Branch Versioning

### Version Divergence

When you write to a branch, the branch version diverges from main:

**Before Promotion:**
- Main: `version: 3`, `currentVersion: true`

**After Promotion to Branch:**
- Main: `version: 3`, `currentVersion: true` (unchanged)
- Branch: `version: 4`, `currentVersion: true` (on branch)

**After Merge (OVERRIDE):**
- Main: `version: 4`, `currentVersion: true` (adopted branch version)
- Old main version: `version: 3`, `currentVersion: false` (historical)

**Key Point:** Pre-merge main version is lost (overwritten, not merged).

---

## Pitfalls

### Pitfall 1: Not Polling for Ready

```javascript
// BAD
const branch = await createBranch("promo-123");
await promoteComponent(componentId, branch.branchId);  // FAILS — branch not ready
```

```javascript
// GOOD
const branch = await createBranch("promo-123");
await pollUntilReady(branch.branchId);  // Wait for ready: true
await promoteComponent(componentId, branch.branchId);  // Now works
```

---

### Pitfall 2: Forgetting to Delete Branch

```javascript
// BAD
if (reviewResult == "REJECTED") {
    updatePromotionLog(promotionId, "REJECTED");
    // Branch still exists — leaks!
}
```

```javascript
// GOOD
if (reviewResult == "REJECTED") {
    updatePromotionLog(promotionId, "REJECTED");
    deleteBranch(branchId);  // Cleanup
    updatePromotionLog(promotionId, "REJECTED", branchId: null);
}
```

---

### Pitfall 3: Tilde Syntax Only Works with Component ID

```http
# BAD — Tilde syntax not supported for folder paths
GET /ComponentMetadata/query~{branchId}
```

```http
# GOOD — Use tilde syntax with specific component ID
GET /Component/{componentId}~{branchId}
```

---

### Pitfall 4: Main is Named "main", Not "master"

```json
// BAD
{
  "destinationBranchId": "master"
}
```

```json
// GOOD
{
  "destinationBranchId": "main"
}
```

---

## Example: Full Branch Lifecycle (Pseudocode)

```javascript
// Step 1: Check branch count
const branches = await queryBranches();
if (branches.length >= 18) {
    throw new Error("BRANCH_LIMIT_REACHED");
}

// Step 2: Create branch
const branch = await createBranch(`promo-${promotionId}`);
const branchId = branch.branchId;

try {
    // Step 3: Poll for ready
    await pollUntilReady(branchId);

    // Step 4: Promote components (in dependency order)
    for (const comp of sortedComponents) {
        const devXml = await getComponent(comp.devComponentId, devAccountId);
        const strippedXml = stripEnvConfig(devXml);
        const rewrittenXml = rewriteReferences(strippedXml, mappingCache);
        await createComponentOnBranch(comp.prodComponentId, branchId, rewrittenXml);
    }

    // Step 5: Create merge request
    const mergeRequest = await createMergeRequest(branchId, "main", "OVERRIDE", branchId);

    // Step 6: Execute merge (on admin approval)
    await executeMergeRequest(mergeRequest.id);

    // Step 7: Delete branch
    await deleteBranch(branchId);

} catch (error) {
    // Cleanup on failure
    await deleteBranch(branchId);
    throw error;
}
```

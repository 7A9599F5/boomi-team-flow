# Branch Operations Reference

Complete reference for Branch and MergeRequest operations, tilde syntax, and the 20-branch limit.

---

## Branch Lifecycle Overview

```
1. Pre-Check → 2. CREATE → 3. Poll Ready → 4. Promote → 5. Merge → 6. DELETE
```

**Critical:** Always delete branches after merge or rejection to free up branch slots (20-branch limit).

---

## 1. Pre-Check Branch Count

Before creating a new branch, check the current branch count to enforce soft limit.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/Branch/query
```

**Request Body:**
```xml
<QueryFilter xmlns='http://api.platform.boomi.com/'/>
```

**Response:**
```json
{
  "@type": "QueryResult",
  "numberOfResults": 15,
  "result": [
    {"@type": "Branch", "branchId": "...", "name": "promo-12345", "ready": true},
    {"@type": "Branch", "branchId": "...", "name": "promo-12346", "ready": false}
  ]
}
```

**Soft Limit Enforcement:**
```javascript
if (response.numberOfResults >= 15) {
  throw new Error({
    errorCode: "BRANCH_LIMIT_REACHED",
    errorMessage: "Too many active promotions. Please wait for pending reviews to complete."
  });
}
```

**Why Soft Limit = 15 (not 20):**
- Hard limit is 20 branches per account
- Reserve 5 slots for buffer (avoid race conditions with concurrent promotions)
- Prevent blocking all promotions if limit is reached

---

## 2. CREATE Branch

Create a new development branch in the primary account.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/Branch
```

**Request Body:**
```json
{
  "name": "promo-{promotionId}",
  "description": "Promotion branch for {promotionId}"
}
```

**Optional Fields (not used in this project):**
- `packageId`: Branch from a specific PackagedComponent version (mutually exclusive with `parentId`)
- `parentId`: Branch from a specific component version by componentId (mutually exclusive with `packageId`)
- `deploymentId`: Branch from a specific deployment snapshot

**Response:**
```json
{
  "@type": "Branch",
  "branchId": "branch-uuid-abc123",
  "name": "promo-12345",
  "ready": false,
  "stage": "CREATING",
  "createdDate": "2024-11-20T10:00:00Z",
  "createdBy": "user@boomi.com"
}
```

**Key Fields:**
- `branchId`: UUID to use in tilde syntax operations
- `ready`: Initially `false` — must poll until `true` before promoting
- `stage`: Starts as `CREATING`, transitions to `NORMAL` when `ready=true`

**Branch Naming Convention:**
```
promo-{promotionId}
```
Uniquely identifies the promotion, makes cleanup easier.

---

## 3. Poll for Ready State

After creation, branch is not immediately ready for operations. Poll until `ready: true`.

**Endpoint:**
```http
GET /partner/api/rest/v1/{accountId}/Branch/{branchId}
```

**Response (Not Ready):**
```json
{
  "@type": "Branch",
  "branchId": "branch-uuid-abc123",
  "name": "promo-12345",
  "ready": false,
  "stage": "CREATING"
}
```

**Response (Ready):**
```json
{
  "@type": "Branch",
  "branchId": "branch-uuid-abc123",
  "name": "promo-12345",
  "ready": true,
  "stage": "NORMAL"
}
```

**Polling Pattern:**
```javascript
async function waitForBranchReady(branchId, maxAttempts = 12, delayMs = 5000) {
  for (let i = 0; i < maxAttempts; i++) {
    const branch = await getBranch(branchId);

    if (branch.ready) {
      return branch;
    }

    await sleep(delayMs);
  }

  throw new Error("Branch did not become ready within timeout (60s)");
}
```

**Typical Ready Time:**
- 5-30 seconds after creation
- Poll every 5 seconds
- Timeout after 60 seconds (12 attempts × 5s)

---

## 4. Promote Components to Branch (Tilde Syntax)

Use **tilde syntax** to create/update components on a specific branch.

### Tilde Syntax Format

```
{componentId}~{branchId}
```

**Example:**
```
component-uuid-456~branch-uuid-abc123
```

### CREATE/UPDATE Component on Branch

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/Component/{componentId}~{branchId}
```

**Headers:**
```http
Accept: application/xml
Content-Type: application/xml
Authorization: Basic {credentials}
```

**Request Body:**
```xml
<bns:Component
  xmlns:bns="http://api.platform.boomi.com/"
  componentId="{prodComponentId}"
  version="{version}"
  name="Order Processor"
  type="process"
  folderFullPath="/Promoted/DevTeamA/Orders/Process">
  <bns:object>
    <!-- Stripped and rewritten component configuration -->
  </bns:object>
</bns:Component>
```

**Use Case in Process C:**
1. Create branch
2. Wait for `ready: true`
3. For each component in dependency order:
   - POST to `/Component/{prodComponentId}~{branchId}`
4. After all components promoted, proceed to merge

### GET Component from Branch

**Endpoint:**
```http
GET /partner/api/rest/v1/{accountId}/Component/{componentId}~{branchId}
```

**Use Case in Process G:**
Fetch branch version of component for diff comparison.

---

## 5. Merge Branch to Main

### Step 1: Create MergeRequest

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/MergeRequest
```

**Request Body:**
```json
{
  "sourceBranchId": "{branchId}",
  "destinationBranchId": "main",
  "strategy": "OVERRIDE",
  "priorityBranch": "{branchId}"
}
```

**Fields:**
- `sourceBranchId` (required): Branch to merge from (promotion branch)
- `destinationBranchId` (required): Branch to merge into (typically `"main"`)
- `strategy` (required): `OVERRIDE` or `CONFLICT_RESOLVE`
- `priorityBranch` (required for OVERRIDE): Which branch wins in conflicts

**Response:**
```json
{
  "@type": "MergeRequest",
  "id": "merge-request-uuid",
  "sourceBranchId": "branch-uuid-abc123",
  "destinationBranchId": "main",
  "strategy": "OVERRIDE",
  "priorityBranch": "branch-uuid-abc123",
  "stage": "DRAFTED",
  "createdDate": "2024-11-20T10:05:00Z"
}
```

### Step 2: Execute MergeRequest

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/MergeRequest/execute/{mergeRequestId}
```

**Request Body:** (empty or minimal)

**Response:**
```json
{
  "@type": "MergeRequest",
  "id": "merge-request-uuid",
  "stage": "MERGED"
}
```

**Merge Stages:**
```
DRAFTING → DRAFTED → REVIEWING → MERGING → MERGED
                                          ↘ FAILED_TO_MERGE
```

### Step 3: Check Merge Status

If merge is asynchronous, poll for completion:

**Endpoint:**
```http
GET /partner/api/rest/v1/{accountId}/MergeRequest/{mergeRequestId}
```

**Response:**
```json
{
  "@type": "MergeRequest",
  "id": "merge-request-uuid",
  "stage": "MERGED"
}
```

---

## 6. DELETE Branch (Cleanup)

**CRITICAL:** Always delete branch after merge or rejection.

**Endpoint:**
```http
DELETE /partner/api/rest/v1/{accountId}/Branch/{branchId}
```

**Response:**
```http
HTTP/1.1 200 OK
```

**Note:** DELETE returns `200` on success (not `204`). A `404` response (branch already deleted) should also be treated as success for idempotent cleanup.

**When to Delete:**

**Approve Path (Process D):**
1. Create MergeRequest
2. Execute MergeRequest
3. **DELETE Branch** ← After successful merge

**Reject Path (Peer Review):**
1. **DELETE Branch** ← No merge needed

**Deny Path (Admin Review):**
1. **DELETE Branch** ← No merge needed

**Failure to Delete:**
- Exhausts 20-branch limit
- Blocks all future promotions
- Requires manual cleanup in AtomSphere UI

---

## Merge Strategies

### OVERRIDE (Recommended)

**When to Use:**
- Single writer to the branch (Process C is sole promoter)
- No manual edits on the branch
- Want deterministic, predictable merges

**Behavior:**
- Priority branch components **completely overwrite** destination
- No conflict resolution needed
- All components from priority branch win

**Configuration:**
```json
{
  "strategy": "OVERRIDE",
  "priorityBranch": "{branchId}"
}
```

**For This Project:**
Use `OVERRIDE` with `priorityBranch = sourceBranchId` (promotion branch).

### CONFLICT_RESOLVE (Not Recommended)

**When to Use:**
- Multiple writers to source and destination branches
- Manual edits on both branches
- Need to resolve conflicts manually

**Behavior:**
- Merge identifies conflicting components
- Requires manual conflict resolution
- More complex, error-prone

**Why Not Used in This Project:**
- Process C is the **sole writer** to promotion branch
- No manual edits on promotion branch
- OVERRIDE is simpler and deterministic

---

## Branch Limit (20 Branches)

### Hard Limit

Boomi enforces a **hard limit of 20 branches** per account.

**What Happens at Limit:**
```json
{
  "@type": "Error",
  "statusCode": 400,
  "errorMessage": "Branch limit reached. Cannot create more branches."
}
```

### Soft Limit Enforcement (15 Branches)

**Check Before Creating:**
```javascript
const branchCount = await queryBranches();

if (branchCount >= 15) {
  return {
    errorCode: "BRANCH_LIMIT_REACHED",
    errorMessage: "Too many active promotions. Please wait for pending reviews to complete."
  };
}
```

**Why 15:**
- Reserve 5 slots for buffer (hard limit is 20)
- Avoid race conditions (multiple promotions starting simultaneously)
- Graceful degradation (user sees friendly error, not hard failure)

### Cleanup Requirements

**All Terminal Paths MUST Delete Branch:**

| Path | Action |
|------|--------|
| **Peer Review → Approve** | Merge → DELETE Branch |
| **Peer Review → Reject** | DELETE Branch (no merge) |
| **Admin Review → Approve** | Merge → DELETE Branch |
| **Admin Review → Deny** | DELETE Branch (no merge) |
| **Any Failure** | DELETE Branch (rollback) |

**Implementation:**
- Use try/catch/finally in Process C, D
- DELETE branch in `finally` block
- Log deletion for audit trail

---

## Error Handling

### 400 Bad Request (Branch Limit)

```json
{
  "@type": "Error",
  "statusCode": 400,
  "errorMessage": "Branch limit reached. Cannot create more branches."
}
```

**Resolution:**
- Query existing branches
- Delete stale or orphaned branches
- Wait for pending promotions to complete

---

### 404 Not Found (Invalid Branch ID)

```json
{
  "@type": "Error",
  "statusCode": 404,
  "errorMessage": "Branch not found."
}
```

**Causes:**
- Invalid `branchId`
- Branch was already deleted
- Typo in branch ID

**Resolution:**
- Verify `branchId` from CREATE Branch response
- Check if branch was deleted prematurely
- Query all branches to find correct ID

---

### 409 Conflict (Merge Conflict)

```json
{
  "@type": "Error",
  "statusCode": 409,
  "errorMessage": "Merge conflict detected. Manual resolution required."
}
```

**Causes:**
- Using `CONFLICT_RESOLVE` strategy with conflicting changes
- Components modified on both source and destination branches

**Resolution:**
- Switch to `OVERRIDE` strategy (if sole writer to branch)
- Manually resolve conflicts in AtomSphere UI
- Re-execute merge after resolution

---

## Tilde Syntax Cheat Sheet

| Operation | Endpoint | Effect |
|-----------|----------|--------|
| **CREATE on Branch** | `POST /Component/{id}~{branchId}` | Create/update component on branch |
| **GET from Branch** | `GET /Component/{id}~{branchId}` | Fetch component version from branch |
| **CREATE on Main** | `POST /Component/{id}` | Create/update component on main |
| **GET from Main** | `GET /Component/{id}` | Fetch current main version |

**Key Point:**
- Tilde syntax targets **specific branch**
- Without tilde, targets **main branch**

---

## Complete Branch Workflow (Process C + D)

### Process C: executePromotion

```javascript
// 1. Pre-check branch count
const branchCount = await queryBranches();
if (branchCount >= 15) {
  throw new Error("BRANCH_LIMIT_REACHED");
}

// 2. Create branch
const branch = await createBranch({name: `promo-${promotionId}`});
const branchId = branch.branchId;

try {
  // 3. Wait for ready
  await waitForBranchReady(branchId);

  // 4. Promote components (in dependency order)
  for (const component of componentsInOrder) {
    const strippedXml = stripEnvConfig(component.xml);
    const rewrittenXml = rewriteReferences(strippedXml, mappingCache);
    await createComponentOnBranch(component.prodId, branchId, rewrittenXml);
  }

  // Return success (Process D will merge)
  return {branchId, status: "PROMOTED"};

} catch (error) {
  // Cleanup on failure
  await deleteBranch(branchId);
  throw error;
}
```

### Process D: packageAndDeploy

```javascript
// 1. Create merge request
const mergeRequest = await createMergeRequest({
  sourceBranchId: branchId,
  destinationBranchId: "main",
  strategy: "OVERRIDE",
  priorityBranch: branchId
});

// 2. Execute merge
await executeMergeRequest(mergeRequest.id);

try {
  // 3. Package component
  const pkg = await createPackagedComponent({
    componentId: prodComponentId,
    packageVersion: version,
    shareable: true
  });

  // 4. Create/update Integration Pack
  const pack = await createOrUpdateIntegrationPack({name, packages: [pkg.packageId]});

  // 5. Deploy to environments
  await deployPackage({environmentId, packageId: pkg.packageId});

  // Return success
  return {packageId: pkg.packageId, integrationPackId: pack.id};

} finally {
  // 6. ALWAYS delete branch (success or failure)
  await deleteBranch(branchId);
}
```

---

## Best Practices

### Branch Management

**DO:**
- ✅ Check branch count before creating (enforce soft limit: 15)
- ✅ Use unique, identifiable branch names (`promo-{promotionId}`)
- ✅ Poll `ready` state before promoting components
- ✅ Delete branches immediately after merge or rejection
- ✅ Use `OVERRIDE` strategy for deterministic merges

**DON'T:**
- ❌ Assume branches are immediately ready after creation
- ❌ Leave branches orphaned after failures
- ❌ Create branches without cleanup logic in `finally` blocks
- ❌ Use `CONFLICT_RESOLVE` unless absolutely necessary

### Error Recovery

**DO:**
- ✅ Use try/catch/finally for branch operations
- ✅ Delete branch in `finally` block
- ✅ Log branch operations for audit trail
- ✅ Surface friendly errors to users (BRANCH_LIMIT_REACHED)

**DON'T:**
- ❌ Swallow errors and leave branches orphaned
- ❌ Retry branch creation on limit error (will never succeed)
- ❌ Skip cleanup on errors

---

## Related References

- **`component-crud.md`** — Tilde syntax usage for component operations
- **`query-patterns.md`** — Branch query patterns
- **`error-handling.md`** — Retry strategies and error codes

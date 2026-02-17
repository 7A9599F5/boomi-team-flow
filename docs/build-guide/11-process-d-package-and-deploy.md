### Process D: Package and Deploy (`PROMO - Package and Deploy`)

> **API Alternative:** This process can be created programmatically via `POST /Component` with `type="process"`. Due to the complexity of process canvas XML (shapes, routing, DPP mappings, script references), the recommended workflow is: (1) build the process manually following the steps below, (2) use `GET /Component/{processId}` to export the XML, (3) store the XML as a template for automated recreation. See [Appendix D: API Automation Guide](22-api-automation-guide.md) for the full workflow.

This process creates a PackagedComponent from a promoted component, optionally creates or updates an Integration Pack, and deploys to target environments.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - PackageAndDeployRequest` | `/integration/profiles/packageAndDeploy-request.json` |
| `PROMO - Profile - PackageAndDeployResponse` | `/integration/profiles/packageAndDeploy-response.json` |

The request JSON contains:
- `prodComponentId` (string): the promoted root process component in the primary account
- `prodAccountId` (string): the primary account ID
- `branchId` (string): promotion branch ID from Process C (to merge before packaging)
- `promotionId` (string): promotion run ID (for PromotionLog updates)
- `packageVersion` (string): version label for the package (e.g., `"1.2.0"`)
- `integrationPackId` (string): existing Integration Pack ID (used when `createNewPack = false`)
- `createNewPack` (boolean): `true` to create a new Integration Pack, `false` to add to existing
- `newPackName` (string): name for new pack (required if `createNewPack = true`)
- `newPackDescription` (string): description for new pack
- `targetAccountGroupId` (string): account group to deploy to
- `deploymentTarget` (string): `"TEST"` or `"PRODUCTION"` — determines deployment mode
- `isHotfix` (string): `"true"` / `"false"` — flags emergency production bypass
- `hotfixJustification` (string): required when isHotfix=`"true"` (up to 1000 chars)
- `testPromotionId` (string): for production-from-test mode, links back to the TEST promotion
- `testIntegrationPackId` (string): Test Integration Pack ID from the test deployment
- `testIntegrationPackName` (string): Test Integration Pack name from the test deployment

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `packagedComponentId` (string): ID of the created PackagedComponent
- `integrationPackId` (string): ID of the Integration Pack (new or existing)
- `integrationPackName` (string): name of the Integration Pack
- `releaseVersion` (string): the released pack version
- `deploymentStatus` (string): overall deployment status
- `deployedEnvironments` (array): each entry has `environmentId`, `environmentName`, `status`
- `deploymentTarget` (string): echoes the deployment mode used
- `branchPreserved` (string): `"true"` if branch was kept (test mode), `"false"` if deleted
- `isHotfix` (string): `"true"` if this was an emergency hotfix deployment

#### FSS Operation

Create `PROMO - FSS Op - PackageAndDeploy` per Section 3.B, using `PROMO - Profile - PackageAndDeployRequest` and `PROMO - Profile - PackageAndDeployResponse`.

#### DPP Initialization

| DPP Name | Initial Value | Purpose |
|----------|--------------|---------|
| `branchId` | (from request) | Promotion branch to merge before packaging |
| `promotionId` | (from request) | Promotion run ID for PromotionLog updates |
| `mergeRequestId` | (set in step 2.5) | Merge request ID for merge execute and polling |
| `adminEmail` | (from request context) | Admin user's email for self-approval check |
| `packagedComponentId` | (set in step 3) | Created PackagedComponent ID |
| `deploymentTarget` | (from request) | `"TEST"` or `"PRODUCTION"` |
| `isHotfix` | (from request) | Emergency hotfix flag |
| `hotfixJustification` | (from request) | Hotfix justification text |
| `testPromotionId` | (from request) | Links production to preceding test deployment |
| `cacheRefreshFailed` | "false" | Tracks whether ExtensionAccessMapping cache refresh succeeded |
| `extensionAccessMappingCount` | "0" | Count of ExtensionAccessMapping records created/updated |

#### Canvas — Shape by Shape

1. **Start shape** — Operation = `PROMO - FSS Op - PackageAndDeploy`

2. **Set Properties — Read Request**
   - DPP `prodComponentId` = document path: `prodComponentId`
   - DPP `prodAccountId` = document path: `prodAccountId`
   - DPP `branchId` = document path: `branchId`
   - DPP `promotionId` = document path: `promotionId`
   - DPP `packageVersion` = document path: `packageVersion`
   - DPP `createNewPack` = document path: `createNewPack`
   - DPP `integrationPackId` = document path: `integrationPackId`
   - DPP `newPackName` = document path: `newPackName`
   - DPP `newPackDescription` = document path: `newPackDescription`
   - DPP `targetAccountGroupId` = document path: `targetAccountGroupId`
   - DPP `deploymentTarget` = document path: `deploymentTarget`
   - DPP `isHotfix` = document path: `isHotfix`
   - DPP `hotfixJustification` = document path: `hotfixJustification`
   - DPP `testPromotionId` = document path: `testPromotionId`
   - DPP `testIntegrationPackId` = document path: `testIntegrationPackId`
   - DPP `testIntegrationPackName` = document path: `testIntegrationPackName`

2.0. **Promotion Status Gate**
   - Query PromotionLog from DataHub for the given `promotionId`.
   - Validate that the `status` field is one of:
     - `"COMPLETED"` — promotion succeeded, ready for packaging
     - `"TEST_DEPLOYED"` — test deployment succeeded, ready for production promotion
   - If the status is anything else (e.g., `"FAILED"`, `"PENDING_PEER_REVIEW"`, `"PENDING_ADMIN_APPROVAL"`), return an error response immediately:
     - `success = false`
     - `errorCode = "PROMOTION_NOT_COMPLETED"`
     - `errorMessage = "Promotion {promotionId} has status '{status}' — packaging requires COMPLETED or TEST_DEPLOYED status"`
   - **Why this gate exists**: Process D merges the promotion branch to main. Without this gate, a direct API call to the Flow Service could bypass the UI and merge a partially-promoted or unapproved branch. This is a defense-in-depth measure.

2.1. **Admin Self-Approval Prevention**
   - Before proceeding to any deployment mode, validate that the admin submitting the deployment did not initiate the original promotion.
   - Query PromotionLog for the `promotionId` to retrieve the `initiatedBy` field.
   - Compare: `adminEmail.toLowerCase() != initiatedBy.toLowerCase()`.
   - If the same person: return error with `errorCode = "SELF_APPROVAL_NOT_ALLOWED"`, `errorMessage = "Admin cannot approve and deploy their own promotion"`. Do not proceed.
   - This is a backend enforcement in addition to the UI-level Decision step on Page 7.

2.2. **Decision — Deployment Mode**
   - The process supports 3 deployment modes based on `deploymentTarget`, `testPromotionId`, and `isHotfix`:
     - **Mode 1 — TEST** (`deploymentTarget = "TEST"`): Merge → package → deploy to test, preserve branch, update PromotionLog with test status
     - **Mode 2 — PRODUCTION from test** (`deploymentTarget = "PRODUCTION"` AND `testPromotionId` is non-empty): Skip merge (content already on main from test), package from main → deploy to production, delete branch
     - **Mode 3 — PRODUCTION hotfix** (`deploymentTarget = "PRODUCTION"` AND `isHotfix = "true"`): Merge → package → deploy to production, delete branch, flag as hotfix
   - Use a Decision shape on DPP `deploymentTarget`:
     - **`TEST`** branch → step 2.3 (test-specific pre-processing)
     - **`PRODUCTION`** branch → Decision on DPP `testPromotionId`:
       - Non-empty → step 2.4 (skip merge, jump to step 3)
       - Empty (hotfix) → step 2.5 (merge as normal)

2.3. **TEST Mode Pre-Processing**
   - No additional pre-processing needed — proceed to step 2.5 (merge) as normal
   - After merge + package + deploy, the process will:
     - Preserve the branch (skip step 8.5 DELETE)
     - Update PromotionLog: `status = "TEST_DEPLOYED"`, `testDeployedAt` = current timestamp, `testIntegrationPackId`, `testIntegrationPackName`

2.4. **PRODUCTION from Test — Skip Merge**
   - Content is already on main from the test deployment merge
   - Skip steps 2.5-2.7 (merge) entirely
   - Jump directly to step 3 (PackagedComponent creation)

2.5. **HTTP Client Send — POST MergeRequest (Create)**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - POST MergeRequest`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - Request body: `source` = DPP `branchId`, `strategy` = `"OVERRIDE"`, `priorityBranch` = DPP `branchId`. See `/integration/api-requests/create-merge-request.json`
   - OVERRIDE strategy ensures promotion branch content wins (no conflict resolution needed — Process C is the sole writer to the branch)
   - Extract `mergeRequestId` from the response; store in DPP `mergeRequestId`

2.6. **HTTP Client Send — POST MergeRequest Execute**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - POST MergeRequest Execute`
   - URL parameter `{1}` = DPP `primaryAccountId`, `{2}` = DPP `mergeRequestId`
   - Request body: `action` = `"MERGE"`. See `/integration/api-requests/execute-merge-request.json`
   - After execution, poll using `PROMO - HTTP Op - GET MergeRequest` (operation 19) with URL parameter `{2}` = DPP `mergeRequestId` until `stage = MERGED`. See `/integration/api-requests/get-merge-request.json` for merge stages.
   - On merge failure (`stage = FAILED_TO_MERGE`): error with `errorCode = "MERGE_FAILED"`, attempt `DELETE /Branch/{branchId}`, return error

2.7. **Note**: After a successful merge, the promoted components now exist on main. Packaging (step 3) reads from main, so the merge must complete before proceeding.

3. **HTTP Client Send — POST PackagedComponent**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - POST PackagedComponent`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - Request body: JSON containing `componentId` = DPP `prodComponentId`, `packageVersion` = DPP `packageVersion`, `notes` = promotion metadata, `shareable` = `true`
   - Build the request JSON with a Map shape before this connector:
     - Source: DPPs
     - Destination: PackagedComponent create JSON
   - Response returns the new `packagedComponentId`
   - Extract `packagedComponentId` into a DPP

4. **Decision — Create New Pack?**
   - Condition: DPP `createNewPack` **EQUALS** `"true"`
   - **YES** branch: step 5 (create new Integration Pack)
   - **NO** branch: step 6 (add to existing pack)

5. **YES Branch — HTTP Client Send — POST IntegrationPack**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - POST IntegrationPack`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - Request body: JSON with `name` = DPP `newPackName`, `description` = DPP `newPackDescription`
   - Response returns the new `integrationPackId`
   - Set DPP `integrationPackId` from the response
   - After creating the pack, add the PackagedComponent to it using `PROMO - HTTP Op - POST Add To IntegrationPack` (operation 17) with URL parameters `{2}` = DPP `integrationPackId`, `{3}` = DPP `packagedComponentId`. See `/integration/api-requests/add-to-integration-pack.json`.
   - Continue to step 7

6. **NO Branch — Add to Existing Pack**
   - The `integrationPackId` DPP already holds the existing pack ID
   - Add the PackagedComponent (from step 3) to the existing Integration Pack using `PROMO - HTTP Op - POST Add To IntegrationPack` (operation 17) with URL parameters `{2}` = DPP `integrationPackId`, `{3}` = DPP `packagedComponentId`. See `/integration/api-requests/add-to-integration-pack.json`.
   - Continue to step 7

7. **HTTP Client Send — Release Integration Pack**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - POST ReleaseIntegrationPack` (operation 18)
   - URL parameter `{1}` = DPP `primaryAccountId`
   - Request body: JSON with `integrationPackId` = DPP `integrationPackId`, `version` = DPP `packageVersion`, `notes` = promotion metadata. See `/integration/api-requests/release-integration-pack.json`.
   - Response returns the released `packageId` used for deployment in step 8

8. **For Each Target Environment — Deploy**
   - If `targetAccountGroupId` is provided, deploy the released pack:
   - **HTTP Client Send** — POST DeployedPackage
     - Connector: `PROMO - Partner API Connection`
     - Operation: `PROMO - HTTP Op - POST DeployedPackage`
     - URL parameter `{1}` = DPP `primaryAccountId`
     - Request body: JSON with `packageId`, `environmentId`, and deployment parameters
   - Accumulate deployment results for each environment (success/failure per environment)
   - Add 120ms gap between deployment calls

8.3. **ExtensionAccessMapping Cache Refresh (Post-Deployment)**
   - After successful deployment to target environments, refresh the extension access mapping cache for each deployed environment
   - This step enables the Extension Editor feature to provide fast, process-level access control for extension editing

   **Sub-steps for each deployed environment:**
   1. **HTTP Client Send — GET EnvironmentExtensions**
      - Connector: `PROMO - Partner API Connection`
      - Operation: `PROMO - HTTP Op - GET EnvironmentExtensions`
      - URL parameter `{1}` = DPP `primaryAccountId`
      - Query: `environmentId = {targetEnvironmentId}` (from deployment results)
      - Response: Full EnvironmentExtensions object with all extension components

   2. **DataHub Query — ComponentMapping Lookup**
      - For each component found in the EnvironmentExtensions response (connections, operations, processProperties, etc.):
        - Query ComponentMapping: `prodComponentId = {componentId}` to find the originating `devAccountId`(s)
        - If multiple devAccountIds map to the same prodComponentId → component is shared

   3. **DataHub Query — DevAccountAccess Lookup**
      - For each unique `devAccountId` found:
        - Query DevAccountAccess: `devAccountId = {devAccountId}` AND `isActive = "true"`
        - Collect authorized SSO group IDs

   4. **Groovy Script — Build Extension Access Cache**
      - Script: `build-extension-access-cache.groovy` (from `/integration/scripts/`)
      - Input: Combined JSON containing extensions, componentMappings, and devAccountAccessRecords
      - For each extension component:
        - Determine `isConnectionExtension` (component is in `connections` section → "true")
        - Determine `isSharedComponent` (multiple devAccountIds → "true")
        - Compute `authorizedSsoGroups` as union of all matching SSO groups
        - Set `ownerProcessId` and `ownerProcessName` from deployment context
      - Output: Array of ExtensionAccessMapping records

   5. **DataHub Upsert — Store ExtensionAccessMapping Records**
      - Operation: `PROMO - DH Op - Upsert ExtensionAccessMapping`
      - Upsert each record to DataHub (match on `environmentId` + `prodComponentId`)
      - Records that already exist are updated; new records are created

   **Error Handling:** Cache refresh failures MUST NOT fail the overall deployment. If the cache refresh fails:
   - Log the error with `logger.warning("ExtensionAccessMapping cache refresh failed for environment {environmentId}: {error}")`
   - Set DPP `cacheRefreshFailed` = `"true"` for downstream reporting
   - Continue to step 8.5 (branch deletion) — the deployment was successful even if the cache refresh failed
   - Admin can trigger a manual cache refresh later via the Extension Editor's refresh action

   **DPP additions:**
   - `cacheRefreshFailed` (set in step 8.3 error handler) — `"true"` if any environment's cache refresh failed, `"false"` otherwise
   - `extensionAccessMappingCount` (set by Groovy script) — total records upserted across all environments

8.5. **Decision — Delete or Preserve Branch**
   - **TEST mode** (`deploymentTarget = "TEST"`): **SKIP branch deletion** — branch is preserved for future production promotion and diff review
   - **PRODUCTION mode** (both from-test and hotfix): **DELETE branch**

8.6. **HTTP Client Send — DELETE Branch (Cleanup)** (PRODUCTION modes only)
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - DELETE Branch`
   - URL parameter `{1}` = DPP `primaryAccountId`, `{2}` = DPP `branchId`
   - See `/integration/api-requests/delete-branch.json`
   - Idempotent: both `200` (deleted) and `404` (already deleted) are success
   - **Ignore delete failures** — log the error but do not fail the process (the merge and deployment already succeeded)
   - Update PromotionLog: set `branchId` = `null` (branch no longer exists)

9. **Map — Build Response JSON**
   - Source: accumulated results and DPPs
   - Destination: `PROMO - Profile - PackageAndDeployResponse`
   - Map:
     - `packagedComponentId` from DPP
     - `integrationPackId` from DPP
     - `integrationPackName` = DPP `newPackName` (or queried name for existing pack)
     - `releaseVersion` from step 7 response
     - `deploymentStatus` = `"DEPLOYED"` if all succeeded, `"PARTIAL"` if some failed
     - `deployedEnvironments` array from step 8 results
     - `deploymentTarget` = DPP `deploymentTarget`
     - `branchPreserved` = `"true"` if TEST mode, `"false"` if PRODUCTION mode
     - `isHotfix` = DPP `isHotfix`
     - `success` = `true`

10. **Return Documents** — same as Process F

#### Error Handling

Wrap the entire process (steps 2.5-8.5) in a **Try/Catch**:
- **Promotion status gate failure** (step 2.0): return error immediately with `errorCode = "PROMOTION_NOT_COMPLETED"` — PromotionLog status is not `COMPLETED` or `TEST_DEPLOYED`. The promotion must complete successfully (and pass any required reviews) before packaging. This gate prevents merging incomplete branches to main.
- **Merge failure** (step 2.6): attempt `DELETE /Branch/{branchId}`, return error with `errorCode = "MERGE_FAILED"`
- **PackagedComponent creation failure**: attempt `DELETE /Branch/{branchId}`, return error with `errorCode = "PROMOTION_FAILED"`
- **Integration Pack failure**: attempt `DELETE /Branch/{branchId}`, return error with `errorCode = "PROMOTION_FAILED"`
- **Deployment failure**: per-environment — mark individual environments as failed in the `deployedEnvironments` array, but continue deploying to remaining environments. Set `deploymentStatus = "PARTIAL"`. Branch is still deleted in step 8.5 (after the deployment loop).
- **Catch block**: In all catastrophic failure cases, attempt `DELETE /Branch/{branchId}` before returning the error response. Log delete failures but do not mask the original error.

#### Branch Deletion on Rejection/Denial

Promotion branches must be cleaned up not only on successful deployment but also when a promotion is rejected or denied. Without cleanup, rejected promotions leave orphaned branches that count against the platform branch limit (15 operational threshold, 20 hard limit).

**Peer Rejection Path (Process E3 records PEER_REJECTED):**

When Process E3 records a `PEER_REJECTED` decision:
1. After updating the PromotionLog with `peerReviewStatus = "PEER_REJECTED"`, retrieve the `branchId` from the PromotionLog record.
2. Call `DELETE /Branch/{branchId}` using `PROMO - HTTP Op - DELETE Branch` with URL parameter `{1}` = DPP `primaryAccountId`, `{2}` = the promotion's `branchId`.
3. Handle responses: `200` = deleted successfully, `404` = branch already deleted (both are success).
4. Update PromotionLog: set `branchId` = `null` to reflect that the branch no longer exists.
5. Log delete failures but do not fail the peer review response — the review decision has already been recorded.

**Admin Denial Path (Page 7 denial):**

When an admin denies the deployment at Page 7:
1. Before marking the promotion as `ADMIN_REJECTED`, retrieve the `branchId` from the PromotionLog record.
2. Call `DELETE /Branch/{branchId}` using `PROMO - HTTP Op - DELETE Branch` with URL parameter `{1}` = DPP `primaryAccountId`, `{2}` = the promotion's `branchId`.
3. Handle responses: `200` = deleted successfully, `404` = branch already deleted (both are success).
4. Update PromotionLog: set `status = "ADMIN_REJECTED"`, `branchId` = `null`, `adminComments` = denial reason.
5. Log delete failures but do not fail the denial response — the rejection decision takes priority.

---

**Verify — 3 deployment modes:**

**Test deployment (Mode 1):**
- Promote a component (Process C), then send a Package and Deploy request with `deploymentTarget = "TEST"`, `createNewPack = true`, `newPackName = "Orders - TEST"`
- **Expected**: `success = true`, `branchPreserved = "true"`, `deploymentTarget = "TEST"`, branch still exists (GET `/Branch/{branchId}` returns `200`)
- **Expected PromotionLog**: `status = "TEST_DEPLOYED"`, `testDeployedAt` populated, `testIntegrationPackId`/`testIntegrationPackName` populated, `branchId` still set

**Production from test (Mode 2):**
- Using the test deployment from Mode 1, send a Package and Deploy request with `deploymentTarget = "PRODUCTION"`, `testPromotionId = "{testPromotionId}"`, existing production `integrationPackId`
- **Expected**: `success = true`, `branchPreserved = "false"`, merge is skipped, branch is deleted (GET `/Branch/{branchId}` returns `404`)
- **Expected PromotionLog**: `status = "DEPLOYED"`, `testPromotionId` links back to test record

**Hotfix (Mode 3):**
- Promote a component (Process C), then send a Package and Deploy request with `deploymentTarget = "PRODUCTION"`, `isHotfix = "true"`, `hotfixJustification = "Critical API fix"`
- **Expected**: `success = true`, `isHotfix = "true"`, `branchPreserved = "false"`, branch is deleted
- **Expected PromotionLog**: `status = "DEPLOYED"`, `isHotfix = "true"`, `hotfixJustification` populated

---

---
Prev: [Process C: Execute Promotion](10-process-c-execute-promotion.md) | Next: [Process J: List Integration Packs](12-process-j-list-integration-packs.md) | [Back to Index](index.md)

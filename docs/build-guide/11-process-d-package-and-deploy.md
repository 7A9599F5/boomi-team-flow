### Process D: Package and Deploy (`PROMO - Package and Deploy`)

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
| `mergeRequestId` | (set in step 2.5) | Merge request ID for execute and polling |
| `packagedComponentId` | (set in step 3) | Created PackagedComponent ID |
| `deploymentTarget` | (from request) | `"TEST"` or `"PRODUCTION"` |
| `isHotfix` | (from request) | Emergency hotfix flag |
| `hotfixJustification` | (from request) | Hotfix justification text |
| `testPromotionId` | (from request) | Links production to preceding test deployment |

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

2.1. **Decision — Deployment Mode**
   - The process supports 3 deployment modes based on `deploymentTarget`, `testPromotionId`, and `isHotfix`:
     - **Mode 1 — TEST** (`deploymentTarget = "TEST"`): Merge → package → deploy to test, preserve branch, update PromotionLog with test status
     - **Mode 2 — PRODUCTION from test** (`deploymentTarget = "PRODUCTION"` AND `testPromotionId` is non-empty): Skip merge (content already on main from test), package from main → deploy to production, delete branch
     - **Mode 3 — PRODUCTION hotfix** (`deploymentTarget = "PRODUCTION"` AND `isHotfix = "true"`): Merge → package → deploy to production, delete branch, flag as hotfix
   - Use a Decision shape on DPP `deploymentTarget`:
     - **`TEST`** branch → step 2.2 (test-specific pre-processing)
     - **`PRODUCTION`** branch → Decision on DPP `testPromotionId`:
       - Non-empty → step 2.4 (skip merge, jump to step 3)
       - Empty (hotfix) → step 2.5 (merge as normal)

2.2. **TEST Mode Pre-Processing**
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
   - After execution, poll `GET /MergeRequest/{mergeRequestId}` until `stage = MERGED`
   - On merge failure: error with `errorCode = "MERGE_FAILED"`, attempt `DELETE /Branch/{branchId}`, return error

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
   - After creating the pack, add the PackagedComponent to it (Platform API call to add component to pack)
   - Continue to step 7

6. **NO Branch — Add to Existing Pack**
   - The `integrationPackId` DPP already holds the existing pack ID
   - Add the PackagedComponent (from step 3) to the existing Integration Pack via the Platform API
   - Continue to step 7

7. **HTTP Client Send — Release Integration Pack**
   - POST to release the Integration Pack (makes it deployable)
   - This may use an existing HTTP operation or a generic HTTP Client Send with the release endpoint
   - URL: `/partner/api/rest/v1/{primaryAccountId}/IntegrationPackRelease`
   - Request body includes `integrationPackId` and release notes
   - Response returns the `releaseVersion`

8. **For Each Target Environment — Deploy**
   - If `targetAccountGroupId` is provided, deploy the released pack:
   - **HTTP Client Send** — POST DeployedPackage
     - Connector: `PROMO - Partner API Connection`
     - Operation: `PROMO - HTTP Op - POST DeployedPackage`
     - URL parameter `{1}` = DPP `primaryAccountId`
     - Request body: JSON with `packageId`, `environmentId`, and deployment parameters
   - Accumulate deployment results for each environment (success/failure per environment)
   - Add 120ms gap between deployment calls

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
- **Merge failure** (step 2.6): attempt `DELETE /Branch/{branchId}`, return error with `errorCode = "MERGE_FAILED"`
- **PackagedComponent creation failure**: attempt `DELETE /Branch/{branchId}`, return error with `errorCode = "PROMOTION_FAILED"`
- **Integration Pack failure**: attempt `DELETE /Branch/{branchId}`, return error with `errorCode = "PROMOTION_FAILED"`
- **Deployment failure**: per-environment — mark individual environments as failed in the `deployedEnvironments` array, but continue deploying to remaining environments. Set `deploymentStatus = "PARTIAL"`. Branch is still deleted in step 8.5 (after the deployment loop).
- **Catch block**: In all catastrophic failure cases, attempt `DELETE /Branch/{branchId}` before returning the error response. Log delete failures but do not mask the original error.

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

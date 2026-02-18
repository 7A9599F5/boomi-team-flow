# Flow Service Component Specification

## Component Overview

**Component Name**: `PROMO - Flow Service`
**Component Type**: Flow Service
**Path to Service**: `/fs/PromotionService`
**External Name**: `PromotionService`
**Deployment Target**: Public Boomi Cloud Atom
**Purpose**: Backend API for Boomi Team Promotion Flow application

> **Diagram:** See the [Promotion Sequence Diagram](../../docs/diagrams/promotion-sequence.md) for a visual end-to-end flow of all message actions.

---

## Message Actions

The Flow Service exposes 21 message actions, each linked to a corresponding Integration process.

### 1. getDevAccounts

**Action Name**: `getDevAccounts`
**Linked Process**: Process A0 - Get Dev Accounts
**Flow Service Operation**: `PROMO - FSS Op - GetDevAccounts`
**Request Profile**: `PROMO - Profile - GetDevAccountsRequest`
**Response Profile**: `PROMO - Profile - GetDevAccountsResponse`
**Service Type**: Message Action

**Description**: Retrieves the list of development sub-accounts available for package selection. Called when the Flow application first loads to populate the dev account dropdown.

**Request Fields**:
- `userSsoGroups` (array of strings, required) — the authenticated user's Azure AD/Entra SSO group names. Used for both team group resolution (which dev accounts to return) and tier group resolution (CONTRIBUTOR vs ADMIN)

**Response Fields**:
- `success` (boolean)
- `effectiveTier` (string: `"CONTRIBUTOR"` | `"ADMIN"`) — the user's resolved dashboard tier, derived from `userSsoGroups`
- `devAccounts` (array)
  - `accountId` (string)
  - `accountName` (string)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

#### Tier Resolution Algorithm

Process A0 determines the user's effective tier from their SSO group names:

```
if userSsoGroups contains "ABC_BOOMI_FLOW_ADMIN" → effectiveTier = "ADMIN"
else if userSsoGroups contains "ABC_BOOMI_FLOW_CONTRIBUTOR" → effectiveTier = "CONTRIBUTOR"
else → effectiveTier = "READONLY" (no dashboard access — should not reach this in normal flow)
```

**Account resolution by tier:**
- **ADMIN**: Bypasses team group check. Returns ALL active DevAccountAccess records.
- **CONTRIBUTOR**: Extracts team groups matching `ABC_BOOMI_FLOW_DEVTEAM*` from `userSsoGroups`, queries DataHub for DevAccountAccess records where `ssoGroupId` matches and `isActive='true'`.
- **READONLY / OPERATOR**: These tiers have no dashboard access. If reached (e.g., direct API call), Process A0 returns `success=false` with `errorCode=INSUFFICIENT_TIER`.

---

### 2. listDevPackages

**Action Name**: `listDevPackages`
**Linked Process**: Process A - List Dev Packages
**Flow Service Operation**: `PROMO - FSS Op - ListDevPackages`
**Request Profile**: `PROMO - Profile - ListDevPackagesRequest`
**Response Profile**: `PROMO - Profile - ListDevPackagesResponse`
**Service Type**: Message Action

**Description**: Queries PackagedComponents from the specified dev account and returns a filtered/sorted list for the UI selection grid.

**Request Fields**:
- `devAccountId` (string, required)

**Response Fields**:
- `success` (boolean)
- `packages` (array)
  - `packageId` (string)
  - `packageVersion` (string)
  - `componentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `createdDate` (datetime)
  - `createdBy` (string) — Boomi user who created the package
  - `notes` (string)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 3. resolveDependencies

**Action Name**: `resolveDependencies`
**Linked Process**: Process B - Resolve Dependencies
**Flow Service Operation**: `PROMO - FSS Op - ResolveDependencies`
**Request Profile**: `PROMO - Profile - ResolveDependenciesRequest`
**Response Profile**: `PROMO - Profile - ResolveDependenciesResponse`
**Service Type**: Message Action

**Description**: Recursively traverses component references starting from the selected process, builds a visited set, and returns the full dependency tree for review.

**Request Fields**:
- `devAccountId` (string, required)
- `rootComponentId` (string, required)

**Response Fields**:
- `success` (boolean)
- `dependencies` (array)
  - `componentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `dependencyType` (string: "DEPENDENT" | "INDEPENDENT")
  - `depth` (integer)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 4. executePromotion

**Action Name**: `executePromotion`
**Linked Process**: Process C - Execute Promotion
**Flow Service Operation**: `PROMO - FSS Op - ExecutePromotion`
**Request Profile**: `PROMO - Profile - ExecutePromotionRequest`
**Response Profile**: `PROMO - Profile - ExecutePromotionResponse`
**Service Type**: Message Action

**Description**: Creates a promotion branch in the primary account, then promotes all components from dev to the branch (not main) via tilde syntax. For each component: checks DataHub for existing prod mapping, strips credentials, rewrites references, creates/updates component on branch, and stores mapping. Returns branchId for downstream diff viewing and merge operations. On failure, cleans up the branch. Defense-in-depth: re-validates the user's tier from `userSsoGroups` before proceeding — rejects with `INSUFFICIENT_TIER` if below CONTRIBUTOR.

**Request Fields**:
- `devAccountId` (string, required)
- `components` (array)
  - `componentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `folderFullPath` (string)
- `promotionMetadata` (object)
  - `processName` (string)
  - `requestedBy` (string)
  - `requestDate` (datetime)
- `userSsoGroups` (array of strings, required) — the authenticated user's SSO group names, passed through from the Flow authorization context. Process C re-runs the tier resolution algorithm as defense-in-depth to ensure the caller is at least CONTRIBUTOR tier before executing promotion

**Response Fields**:
- `success` (boolean) — `false` if any component fails during promotion (partial failure is treated as overall failure)
- `promotionResults` (array)
  - `devComponentId` (string)
  - `prodComponentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `action` (string: "created" | "updated" | "SKIPPED") — `SKIPPED` is set on dependent components when a prerequisite component fails during promotion. Prevents broken references from partially-promoted dependency chains.
  - `version` (integer)
- `connectionsSkipped` (integer) — count of shared connections not promoted
- `branchId` (string) — promotion branch ID for downstream diff/merge operations. **Only present when `success = true`** — on failure, the branch is deleted and this field is absent.
- `branchName` (string) — branch name (e.g., "promo-{promotionId}"). **Only present when `success = true`** — on failure, the branch is deleted and this field is absent.
- `missingConnectionMappings` (array, conditional) — present when errorCode=MISSING_CONNECTION_MAPPINGS
  - `devComponentId` (string)
  - `name` (string)
  - `type` (string)
  - `devAccountId` (string)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 5. packageAndDeploy

**Action Name**: `packageAndDeploy`
**Linked Process**: Process D - Package and Deploy
**Flow Service Operation**: `PROMO - FSS Op - PackageAndDeploy`
**Request Profile**: `PROMO - Profile - PackageAndDeployRequest`
**Response Profile**: `PROMO - Profile - PackageAndDeployResponse`
**Service Type**: Message Action

**Description**: Creates a shareable PackagedComponent, adds it to an admin-owned Integration Pack, releases it. Before executing, Process D validates the PromotionLog status is `COMPLETED`, `TEST_DEPLOYED`, `ADMIN_APPROVED`, or `PENDING_PACK_ASSIGNMENT` — returns `PROMOTION_NOT_COMPLETED` otherwise. This gate prevents merging incomplete or unapproved branches to main. Supports 4 deployment modes:
- **Mode 1 — TEST**: Package from branch (`branchName` field on POST /PackagedComponent — main is NOT touched), delete branch immediately. Auto-detect test IP from PromotionLog history; if no prior IP found, set status to `PENDING_PACK_ASSIGNMENT` and return `needsPackAssignment=true`.
- **Mode 2 — PRODUCTION from test**: Create a new branch from the test PackagedComponent (`packageId` on POST /Branch), merge that branch to main (first time main is touched), package from main, release to admin-selected prod IP, delete branch.
- **Mode 3 — HOTFIX**: Merge promotion branch to main, package from main, release to admin-selected prod IP, release to admin-selected test IP (non-blocking failure), delete branch.
- **Mode 4 — PACK_ASSIGNMENT**: Resume from `PENDING_PACK_ASSIGNMENT` — retrieve existing `prodPackageId` from PromotionLog, add to admin-selected IP, release. No branch operations (branch was deleted in Mode 1).

**Request Fields**:

*Process-derived (set by upstream steps, not user-supplied):*
- `prodComponentId` (string, required) — root process component in primary account
- `branchId` (string, required) — promotion branch ID from Process C
- `deploymentTarget` (string, required: "TEST" | "PRODUCTION") — determines the deployment mode
- `isHotfix` (boolean, default false) — flags emergency production bypass
- `hotfixJustification` (string, conditional — required when isHotfix=true) — justification text (up to 1000 characters)
- `testPromotionId` (string, optional) — populated when deploying from a completed test deployment; links back to the TEST PromotionLog record

*Developer-supplied (from Page 4):*
- `promotionId` (string, required) — promotion run ID for PromotionLog updates
- `packageVersion` (string, required) — version label (e.g., "1.2.0")
- `deploymentNotes` (string) — notes for the PackagedComponent
- `devAccountId` (string) — source dev account ID (for audit)
- `devPackageId` (string) — source dev package ID (for audit)
- `devPackageCreator` (string) — Boomi user who created the dev package
- `devPackageVersion` (string) — version of the dev package

*Admin-supplied (from Page 7 — IP assignment fields):*
- `integrationPackId` (string, conditional) — existing Integration Pack ID (used when createNewPack=false)
- `createNewPack` (boolean) — true to create a new Integration Pack
- `newPackName` (string, conditional — required if createNewPack=true) — name for new pack
- `newPackDescription` (string, conditional) — description for new pack
- `hotfixTestPackId` (string, optional) — Test Integration Pack ID for hotfix test release (Mode 3)
- `hotfixCreateNewTestPack` (boolean, optional) — create new test pack for hotfix (Mode 3)
- `hotfixNewTestPackName` (string, conditional) — name for new test pack
- `hotfixNewTestPackDescription` (string, conditional) — description for new test pack

**Response Fields**:
- `success` (boolean)
- `packageId` (string)
- `prodPackageId` (string) — Package ID of the created prod PackagedComponent
- `integrationPackId` (string)
- `integrationPackName` (string) — name of the Integration Pack
- `releaseId` (string) — ReleaseIntegrationPack response ID for status polling
- `releaseVersion` (string) — released pack version
- `testIntegrationPackId` (string, optional) — Test Integration Pack ID (hotfix mode)
- `testIntegrationPackName` (string, optional) — Test Integration Pack name (hotfix mode)
- `testReleaseId` (string, optional) — Test release ID (hotfix mode)
- `testReleaseVersion` (string, optional) — Test release version (hotfix mode)
- `deploymentTarget` (string) — echoed from request
- `branchPreserved` (boolean) — always `false`; all modes delete the promotion branch
- `isHotfix` (boolean) — echoed from request
- `needsPackAssignment` (boolean) — `true` when Mode 1 auto-detect found no Integration Pack; status is set to `PENDING_PACK_ASSIGNMENT` and admin must assign an IP via Mode 4
- `autoDetectedPackId` (string, optional) — the auto-detected Integration Pack ID (for audit/logging); empty string if not found
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

#### Admin Self-Approval Prevention (MUST implement)

Process D MUST validate that the admin submitting the deployment is not the same user who initiated the promotion (Modes 2 and 3 only). Reject with error code `SELF_APPROVAL_NOT_ALLOWED` if `adminEmail.toLowerCase() == initiatedBy.toLowerCase()`. This enforces the independence of the 2-layer approval workflow and prevents any single user from promoting and deploying their own code. Mode 1 (TEST) is developer-driven; Mode 4 (PACK_ASSIGNMENT) is IP assignment, not promotion approval — neither requires this check.

#### Deployment Modes

**Mode 1: TEST deployment** (`deploymentTarget="TEST"`):
1. Package from branch using `branchName` field on POST /PackagedComponent — main is NOT touched
2. Delete branch immediately after packaging (frees slot early regardless of IP outcome)
3. Set `prodPackageId` in PromotionLog
4. Auto-detect test Integration Pack from PromotionLog history (most recent TEST_DEPLOYED for same processName)
5. **If IP found**: Add to IP (query IP state first for multi-package safety), release IP. Status → `TEST_DEPLOYED`. Response: `needsPackAssignment=false`
6. **If IP not found**: Status → `PENDING_PACK_ASSIGNMENT`. Response: `needsPackAssignment=true`
7. No ExtensionAccessMapping cache refresh (test environment — not needed)

**Mode 2: PRODUCTION deployment from test** (`deploymentTarget="PRODUCTION"`, `testPromotionId` populated):
1. Self-approval check (admin != initiator)
2. Create new branch from test PackagedComponent: POST /Branch with `packageId` = PromotionLog's `prodPackageId`
3. Merge new branch to main (MergeRequest OVERRIDE) — **first time main is touched**
4. Package from main (standard — no branchName)
5. Delete branch
6. Add to admin-selected prod IP (query IP state first for multi-package safety), release IP
7. ExtensionAccessMapping cache refresh
8. Status → `DEPLOYED`. Response: `branchPreserved=false`

**Mode 3: PRODUCTION hotfix** (`deploymentTarget="PRODUCTION"`, `isHotfix=true`):
1. Self-approval check (admin != initiator)
2. Merge promotion branch to main (MergeRequest OVERRIDE)
3. Package from main
4. Add to admin-selected prod IP (query IP state first), release prod IP
5. Add to admin-selected test IP (query IP state first), release test IP (non-blocking — failure logged, does not fail the operation)
6. Delete branch
7. ExtensionAccessMapping cache refresh
8. Status → `DEPLOYED` with `isHotfix=true`. Response: `branchPreserved=false`, `testIntegrationPackId`, `testReleaseId`

**Mode 4: PACK_ASSIGNMENT** (status=`PENDING_PACK_ASSIGNMENT`):
1. No self-approval check (admin is assigning IP, not approving promotion)
2. Retrieve `prodPackageId` from PromotionLog (PackagedComponent already created in Mode 1)
3. Add to admin-selected IP (query IP state first for multi-package safety), release IP
4. Status → `TEST_DEPLOYED`. Response: `needsPackAssignment=false`
5. No branch operations (branch already deleted in Mode 1)

---

### 6. queryStatus

**Action Name**: `queryStatus`
**Linked Process**: Process E - Query Status
**Flow Service Operation**: `PROMO - FSS Op - QueryStatus`
**Request Profile**: `PROMO - Profile - QueryStatusRequest`
**Response Profile**: `PROMO - Profile - QueryStatusResponse`
**Service Type**: Message Action

**Description**: Queries the promotion history DataHub for a specific process or component to retrieve past promotion records. Supports filtering by review stage for the 2-layer approval workflow.

**Request Fields**:
- `queryType` (string: "byProcess" | "byComponent")
- `processName` (string, conditional)
- `componentId` (string, conditional)
- `startDate` (datetime, optional)
- `endDate` (datetime, optional)
- `reviewStage` (string, optional: "PENDING_PEER_REVIEW" | "PENDING_ADMIN_REVIEW" | "ALL") — filters by approval workflow stage. When set, Process E filters DataHub queries by `peerReviewStatus` and/or `adminReviewStatus` fields. Default: "ALL" (no filtering)

**Response Fields**:
- `success` (boolean)
- `promotions` (array)
  - `promotionId` (string)
  - `processName` (string)
  - `devAccountId` (string)
  - `initiatedAt` (datetime)
  - `initiatedBy` (string)
  - `componentsTotal` (integer)
  - `packageVersion` (string, optional) — not stored in PromotionLog model; populated from PackagedComponent lookup at query time
  - `integrationPackId` (string, optional)
  - `prodPackageId` (string, optional) — Package ID of the prod PackagedComponent (populated after packageAndDeploy)
  - `peerReviewStatus` (string, optional) — PENDING_PEER_REVIEW, PEER_APPROVED, PEER_REJECTED
  - `peerReviewedBy` (string, optional) — email of peer reviewer
  - `peerReviewedAt` (datetime, optional) — timestamp of peer review
  - `peerReviewComments` (string, optional) — peer reviewer comments
  - `adminReviewStatus` (string, optional) — PENDING_ADMIN_REVIEW, ADMIN_APPROVED, ADMIN_REJECTED
  - `adminApprovedBy` (string, optional) — email of admin reviewer
  - `adminApprovedAt` (datetime, optional) — timestamp of admin review
  - `adminComments` (string, optional) — admin reviewer comments
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 7. manageMappings

**Action Name**: `manageMappings`
**Linked Process**: Process F - Manage Mappings
**Flow Service Operation**: `PROMO - FSS Op - ManageMappings`
**Request Profile**: `PROMO - Profile - ManageMappingsRequest`
**Response Profile**: `PROMO - Profile - ManageMappingsResponse`
**Service Type**: Message Action

**Description**: Allows querying and manual editing of dev-to-prod component ID mappings stored in the DataHub (admin/troubleshooting feature).

**Connection Seeding Workflow:**
Connections are shared resources pre-configured in the parent account's `#Connections` folder. Admins use the `manageMappings` action with `operation = "create"` to seed ComponentMapping records that link each dev account's connection IDs to the parent's canonical connection IDs. The same parent connection can be mapped from multiple dev accounts (each dev account has its own connection component IDs, but they all map to the same parent `#Connections` component).

**Request Fields**:
- `action` (string: "query" | "update" | "delete")
- `devComponentId` (string, conditional)
- `prodComponentId` (string, conditional)
- `componentName` (string, conditional)

**Response Fields**:
- `success` (boolean)
- `mappings` (array)
  - `devComponentId` (string)
  - `prodComponentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `lastPromoted` (datetime)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 8. queryPeerReviewQueue

**Action Name**: `queryPeerReviewQueue`
**Linked Process**: Process E2 - Query Peer Review Queue
**Flow Service Operation**: `PROMO - FSS Op - QueryPeerReviewQueue`
**Request Profile**: `PROMO - Profile - QueryPeerReviewQueueRequest`
**Response Profile**: `PROMO - Profile - QueryPeerReviewQueueResponse`
**Service Type**: Message Action

**Description**: Queries PromotionLog records that are in PENDING_PEER_REVIEW status, excluding promotions initiated by the requesting user (self-review prevention). Returns promotions ready for peer review along with deployment metadata.

**Self-Review Exclusion Filter (MUST implement)**:
Process E2 MUST apply `toLowerCase()` to both sides when filtering out the requester's own submissions: `initiatedBy.toLowerCase() != requesterEmail.toLowerCase()`. This prevents case-sensitive bypass when Azure AD returns email addresses with varying capitalization.

**Request Fields**:
- `requesterEmail` (string, required) — the authenticated user's email; used to exclude their own submissions from the results (compared case-insensitively against `initiatedBy`)

**Response Fields**:
- `success` (boolean)
- `pendingReviews` (array)
  - `promotionId` (string)
  - `processName` (string)
  - `devAccountId` (string)
  - `initiatedBy` (string) — submitter email
  - `initiatedAt` (datetime) — submission timestamp
  - `componentsTotal` (integer)
  - `componentsCreated` (integer)
  - `componentsUpdated` (integer)
  - `notes` (string) — deployment notes from submitter
  - `packageVersion` (string)
  - `devPackageId` (string)
  - `resultDetail` (string) — JSON per-component results for review
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 9. submitPeerReview

**Action Name**: `submitPeerReview`
**Linked Process**: Process E3 - Submit Peer Review
**Flow Service Operation**: `PROMO - FSS Op - SubmitPeerReview`
**Request Profile**: `PROMO - Profile - SubmitPeerReviewRequest`
**Response Profile**: `PROMO - Profile - SubmitPeerReviewResponse`
**Service Type**: Message Action

**Description**: Records a peer review decision (approve or reject) against a PromotionLog record. Validates that the reviewer is not the submitter (self-review prevention), that the promotion is in the correct state, and that it hasn't already been reviewed. On approval, updates peerReviewStatus to PEER_APPROVED and adminReviewStatus to PENDING_ADMIN_REVIEW. On rejection, updates peerReviewStatus to PEER_REJECTED.

**Request Fields**:
- `promotionId` (string, required) — the promotion to review
- `decision` (string, required: "APPROVED" | "REJECTED") — the peer review decision
- `reviewerEmail` (string, required) — email of the peer reviewer
- `reviewerName` (string, required) — display name of the peer reviewer
- `comments` (string, optional) — reviewer comments (up to 500 characters)

**Response Fields**:
- `success` (boolean)
- `promotionId` (string) — echoed back for confirmation
- `newStatus` (string) — the resulting peerReviewStatus (PEER_APPROVED or PEER_REJECTED)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

**Self-Review Prevention (MUST implement)**:
Process E3 MUST compare `reviewerEmail.toLowerCase()` with `initiatedBy.toLowerCase()` to prevent case-sensitive bypass of self-review prevention. Azure AD may return email addresses with varying capitalization; case-insensitive comparison is mandatory.

**Error Codes (specific to this action)**:
- `SELF_REVIEW_NOT_ALLOWED` — `reviewerEmail.toLowerCase()` matches `initiatedBy.toLowerCase()`
- `ALREADY_REVIEWED` — promotion has already been peer-reviewed (peerReviewStatus is not PENDING_PEER_REVIEW)
- `INVALID_REVIEW_STATE` — promotion is not in PENDING_PEER_REVIEW state (may be IN_PROGRESS, FAILED, etc.)

---

### 10. generateComponentDiff

**Action Name**: `generateComponentDiff`
**Linked Process**: Process G - Generate Component Diff
**Flow Service Operation**: `PROMO - FSS Op - GenerateComponentDiff`
**Request Profile**: `PROMO - Profile - GenerateComponentDiffRequest`
**Response Profile**: `PROMO - Profile - GenerateComponentDiffResponse`
**Service Type**: Message Action

**Description**: Fetches component XML from both the promotion branch and main branch, normalizes both for consistent formatting, and returns them to the UI for client-side diff rendering. For UPDATE actions, fetches both versions; for CREATE actions, returns empty mainXml. Uses Boomi Branching tilde syntax (`Component/{id}~{branchId}`) to read from the promotion branch.

**Request Fields**:
- `branchId` (string, required) — promotion branch ID
- `prodComponentId` (string, required) — production component ID to diff
- `componentName` (string, required) — component name for display
- `componentAction` (string, required: "CREATE" | "UPDATE") — determines whether to fetch main version

**Response Fields**:
- `success` (boolean)
- `prodComponentId` (string) — echoed back
- `componentName` (string) — echoed back
- `componentAction` (string) — echoed back
- `branchXml` (string) — normalized XML from promotion branch
- `mainXml` (string) — normalized XML from main branch (empty string for CREATE)
- `branchVersion` (integer) — component version on branch
- `mainVersion` (integer) — component version on main (0 for CREATE)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 11. listIntegrationPacks

**Action Name**: `listIntegrationPacks`
**Linked Process**: Process J - List Integration Packs
**Flow Service Operation**: `PROMO - FSS Op - ListIntegrationPacks`
**Request Profile**: `PROMO - Profile - ListIntegrationPacksRequest`
**Response Profile**: `PROMO - Profile - ListIntegrationPacksResponse`
**Service Type**: Message Action

**Description**: Queries the primary account for existing MULTI-type Integration Packs and returns them for the admin IP selector on Page 7 (Admin Approval Queue). Supports filtering by pack purpose (TEST or PRODUCTION) based on naming convention (packs with "- TEST" suffix are test packs). Optionally suggests the most recently used pack for a given process name and target environment by querying PromotionLog for the latest DEPLOYED or TEST_DEPLOYED record matching `processName`. Integration Pack selection is admin-driven — developers no longer interact with IP fields.

**Request Fields**:
- `suggestForProcess` (string, optional) — process name to look up suggestion for
- `packPurpose` (string, optional: "TEST" | "PRODUCTION" | "ALL", default "ALL") — filters Integration Packs by purpose. TEST returns packs with "- TEST" suffix. PRODUCTION returns packs without "- TEST" suffix. ALL returns all packs.

**Response Fields**:
- `success` (boolean)
- `integrationPacks` (array)
  - `packId` (string)
  - `packName` (string)
  - `packDescription` (string)
  - `installationType` (string)
- `suggestedPackId` (string, optional) — most recently used pack ID for this process
- `suggestedPackName` (string, optional) — name of the suggested pack
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 12. queryTestDeployments

**Action Name**: `queryTestDeployments`
**Linked Process**: Process E4 - Query Test Deployments
**Flow Service Operation**: `PROMO - FSS Op - QueryTestDeployments`
**Request Profile**: `PROMO - Profile - QueryTestDeploymentsRequest`
**Response Profile**: `PROMO - Profile - QueryTestDeploymentsResponse`
**Service Type**: Message Action

**Description**: Queries PromotionLog records that have been deployed to test (`targetEnvironment="TEST"` AND `status="TEST_DEPLOYED"`) and have not yet been promoted to production (no matching PRODUCTION record with the same `testPromotionId`). Returns test deployments ready for production promotion.

**Request Fields**:
- `devAccountId` (string, optional) — filter by source dev account
- `initiatedBy` (string, optional) — filter by submitter email

**Response Fields**:
- `success` (boolean)
- `testDeployments` (array)
  - `promotionId` (string)
  - `processName` (string)
  - `devAccountId` (string)
  - `initiatedBy` (string) — submitter email
  - `initiatedAt` (datetime) — original promotion timestamp
  - `packageVersion` (string)
  - `componentsTotal` (integer)
  - `componentsCreated` (integer)
  - `componentsUpdated` (integer)
  - `testDeployedAt` (datetime) — when test deployment completed
  - `testIntegrationPackId` (string) — Test Integration Pack ID
  - `testIntegrationPackName` (string) — Test Integration Pack name
  - `branchId` (string) — preserved promotion branch ID
  - `branchName` (string) — preserved branch name
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 13. cancelTestDeployment

**Action Name**: `cancelTestDeployment`
**Linked Process**: Process E4 - Cancel Test Deployment (reuses E4 process with cancellation path)
**Flow Service Operation**: `PROMO - FSS Op - CancelTestDeployment`
**Request Profile**: `PROMO - Profile - CancelTestDeploymentRequest`
**Response Profile**: `PROMO - Profile - CancelTestDeploymentResponse`
**Service Type**: Message Action

**Description**: Cancels a test deployment by cleaning up the preserved test branch and updating the PromotionLog status to `TEST_CANCELLED`. This prevents stale test branches from accumulating against the per-account branch limit. The branch DELETE is idempotent (both 200 and 404 responses are treated as success).

**Request Fields**:
- `promotionId` (string, required) — the promotion ID of the test deployment to cancel

**Response Fields**:
- `success` (boolean)
- `promotionId` (string) — echoed back for confirmation
- `previousStatus` (string) — the status before cancellation (should be `TEST_DEPLOYED`)
- `newStatus` (string) — always `TEST_CANCELLED` on success
- `branchDeleted` (boolean) — true if the branch was successfully deleted (or already absent)
- `message` (string) — human-readable confirmation message
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

**Validation**:
1. Query PromotionLog for the given `promotionId`
2. If not found: return `success=false`, `errorCode=PROMOTION_NOT_FOUND`
3. If status is not `TEST_DEPLOYED`: return `success=false`, `errorCode=INVALID_PROMOTION_STATUS`, `errorMessage="Cannot cancel promotion with status {currentStatus}; expected TEST_DEPLOYED"`

**Logic**:
1. Query PromotionLog for the `promotionId` and extract `branchId` and current `status`
2. Verify status is `TEST_DEPLOYED` (validation above)
3. DELETE the test branch using `DELETE /Branch/{branchId}` — idempotent: HTTP 200 (deleted) and HTTP 404 (already absent) are both treated as success
4. Update PromotionLog: set `status=TEST_CANCELLED`, clear `branchId` (set to empty string)
5. Return success response with `previousStatus`, `newStatus=TEST_CANCELLED`, `branchDeleted=true`

**Error Codes (specific to this action)**:
- `PROMOTION_NOT_FOUND` — `promotionId` references a non-existent PromotionLog record
- `INVALID_PROMOTION_STATUS` — promotion is not in `TEST_DEPLOYED` status (may be `DEPLOYED`, `TEST_CANCELLED`, `FAILED`, etc.)

---

### 14. withdrawPromotion

**Action Name**: `withdrawPromotion`
**Linked Process**: Process E5 - Withdraw Promotion
**Flow Service Operation**: `PROMO - FSS Op - WithdrawPromotion`
**Request Profile**: `PROMO - Profile - WithdrawPromotionRequest`
**Response Profile**: `PROMO - Profile - WithdrawPromotionResponse`
**Service Type**: Message Action

**Description**: Allows the original initiator to withdraw their promotion while it is in `PENDING_PEER_REVIEW` or `PENDING_ADMIN_REVIEW` status. Cleans up the promotion branch and updates the PromotionLog status to `WITHDRAWN`. This frees a branch slot and removes the promotion from reviewer queues.

**Request Fields**:
- `promotionId` (string, required) — the promotion ID to withdraw
- `initiatorEmail` (string, required) — email of the user requesting withdrawal; must match the promotion's `initiatedBy` field (case-insensitive)
- `reason` (string, optional) — reason for withdrawal (up to 500 characters)

**Response Fields**:
- `success` (boolean)
- `promotionId` (string) — echoed back for confirmation
- `previousStatus` (string) — the status before withdrawal (should be `PENDING_PEER_REVIEW` or `PENDING_ADMIN_REVIEW`)
- `newStatus` (string) — always `WITHDRAWN` on success
- `branchDeleted` (boolean) — true if the branch was successfully deleted (or already absent)
- `message` (string) — human-readable confirmation message
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

**Validation**:
1. Query PromotionLog for the given `promotionId`
2. If not found: return `success=false`, `errorCode=PROMOTION_NOT_FOUND`
3. If status is not `PENDING_PEER_REVIEW` or `PENDING_ADMIN_REVIEW`: return `success=false`, `errorCode=INVALID_PROMOTION_STATUS`, `errorMessage="Cannot withdraw promotion with status {currentStatus}; expected PENDING_PEER_REVIEW or PENDING_ADMIN_REVIEW"`
4. If `initiatorEmail.toLowerCase()` does not match `initiatedBy.toLowerCase()`: return `success=false`, `errorCode=NOT_PROMOTION_INITIATOR`, `errorMessage="Only the promotion initiator can withdraw this promotion"`

**Logic**:
1. Query PromotionLog for the `promotionId` and extract `branchId`, current `status`, and `initiatedBy`
2. Verify status is `PENDING_PEER_REVIEW` or `PENDING_ADMIN_REVIEW` (validation above)
3. Verify `initiatorEmail` matches `initiatedBy` (case-insensitive)
4. DELETE the promotion branch using `DELETE /Branch/{branchId}` — idempotent: HTTP 200 (deleted) and HTTP 404 (already absent) are both treated as success
5. Update PromotionLog: set `status=WITHDRAWN`, clear `branchId` (set to empty string), set `withdrawnAt` to current timestamp, set `withdrawalReason` to the provided reason (or empty string)
6. Return success response with `previousStatus`, `newStatus=WITHDRAWN`, `branchDeleted=true`

**Error Codes (specific to this action)**:
- `PROMOTION_NOT_FOUND` — `promotionId` references a non-existent PromotionLog record
- `INVALID_PROMOTION_STATUS` — promotion is not in `PENDING_PEER_REVIEW` or `PENDING_ADMIN_REVIEW` status
- `NOT_PROMOTION_INITIATOR` — `initiatorEmail` does not match the promotion's `initiatedBy` field (only the original initiator can withdraw)

---

### 15. listClientAccounts

**Action Name**: `listClientAccounts`
**Linked Process**: Process K - List Client Accounts
**Flow Service Operation**: `PROMO - FSS Op - ListClientAccounts`
**Request Profile**: `PROMO - Profile - ListClientAccountsRequest`
**Response Profile**: `PROMO - Profile - ListClientAccountsResponse`
**Service Type**: Message Action

**Description**: Retrieves the list of client accounts accessible to the authenticated user based on their SSO group memberships. Queries the ClientAccountConfig DataHub model, filtering by the user's SSO groups. Admins see all active client accounts. Returns client account details including Test and Production environment IDs.

**Request Fields**:
- `userSsoGroups` (array of strings, required) — the authenticated user's Azure AD/Entra SSO group names

**Response Fields**:
- `success` (boolean)
- `clientAccounts` (array)
  - `clientAccountId` (string)
  - `clientAccountName` (string)
  - `testEnvironmentId` (string)
  - `testEnvironmentName` (string)
  - `prodEnvironmentId` (string)
  - `prodEnvironmentName` (string)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 16. getExtensions

**Action Name**: `getExtensions`
**Linked Process**: Process L - Get Extensions
**Flow Service Operation**: `PROMO - FSS Op - GetExtensions`
**Request Profile**: `PROMO - Profile - GetExtensionsRequest`
**Response Profile**: `PROMO - Profile - GetExtensionsResponse`
**Service Type**: Message Action

**Description**: Reads environment extensions and map extension summaries for a specified client account environment, merges with ExtensionAccessMapping records for access control data, and returns a combined response. Extension data and access mappings are returned as JSON-serialized strings to avoid deeply nested profile complexity — the custom component parses them client-side. Uses Partner API `overrideAccount` to access sub-account environments.

**Request Fields**:
- `clientAccountId` (string, required) — target client sub-account ID
- `environmentId` (string, required) — target environment ID within the client account
- `userSsoGroups` (array of strings, required) — for access filtering
- `userEmail` (string, required) — for audit trail

**Response Fields**:
- `success` (boolean)
- `environmentId` (string)
- `extensionData` (string) — JSON-serialized EnvironmentExtensions response
- `accessMappings` (string) — JSON-serialized array of ExtensionAccessMapping records
- `mapExtensionSummaries` (string) — JSON-serialized EnvironmentMapExtensionsSummary results
- `componentCount` (integer) — total extension components
- `connectionCount` (integer) — count of connection extensions
- `processPropertyCount` (integer) — count of process property extensions
- `dynamicPropertyCount` (integer) — count of dynamic process property extensions
- `mapExtensionCount` (integer) — count of map extensions
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 17. updateExtensions

**Action Name**: `updateExtensions`
**Linked Process**: Process M - Update Extensions
**Flow Service Operation**: `PROMO - FSS Op - UpdateExtensions`
**Request Profile**: `PROMO - Profile - UpdateExtensionsRequest`
**Response Profile**: `PROMO - Profile - UpdateExtensionsResponse`
**Service Type**: Message Action

**Description**: Saves environment extension changes for a specified client account environment. Validates that the user has authorization for each modified component via ExtensionAccessMapping lookup. Connection extensions require ADMIN tier. Uses `partial="true"` to ensure only modified sections are updated — omitted sections retain their current values. Uses Partner API `overrideAccount` to write to sub-account environments.

**Request Fields**:
- `clientAccountId` (string, required) — target client sub-account ID
- `environmentId` (string, required) — target environment ID
- `extensionPayload` (string, required) — JSON-serialized partial EnvironmentExtensions update
- `userSsoGroups` (array of strings, required) — for access validation
- `userEmail` (string, required) — for audit trail

**Response Fields**:
- `success` (boolean)
- `updatedFieldCount` (integer) — count of fields successfully updated
- `environmentId` (string)
- `errors` (array, optional) — per-component errors
  - `componentId` (string)
  - `componentName` (string)
  - `errorCode` (string)
  - `errorMessage` (string)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

**Access Validation (MUST implement)**:
For each component in the `extensionPayload`:
1. Query ExtensionAccessMapping for `environmentId` + `prodComponentId`
2. If `isConnectionExtension = "true"` and user is not ADMIN → reject with `CONNECTION_EDIT_ADMIN_ONLY`
3. If user's SSO groups do not intersect `authorizedSsoGroups` and user is not ADMIN → reject with `UNAUTHORIZED_EXTENSION_EDIT`
4. If no ExtensionAccessMapping record exists → reject with `EXTENSION_NOT_FOUND` (conservative default)

---

### 18. copyExtensionsTestToProd

**Action Name**: `copyExtensionsTestToProd`
**Linked Process**: Process N - Copy Extensions Test to Prod
**Flow Service Operation**: `PROMO - FSS Op - CopyExtensionsTestToProd`
**Request Profile**: `PROMO - Profile - CopyExtensionsTestToProdRequest`
**Response Profile**: `PROMO - Profile - CopyExtensionsTestToProdResponse`
**Service Type**: Message Action

**Description**: Copies non-connection environment extensions from a Test environment to a Production environment within the same client account. Fetches extensions from the Test environment, strips connections and PGP certificates, sets `partial="true"`, swaps the environment ID, and posts to the Production environment. Encrypted values (passwords, API keys) are never returned in GET responses and cannot be copied. Uses Partner API `overrideAccount` for sub-account access.

**Request Fields**:
- `clientAccountId` (string, required) — target client sub-account ID
- `testEnvironmentId` (string, required) — source Test environment ID
- `prodEnvironmentId` (string, required) — target Production environment ID
- `userSsoGroups` (array of strings, required) — for access validation
- `userEmail` (string, required) — for audit trail

**Response Fields**:
- `success` (boolean)
- `sectionsExcluded` (string) — comma-separated list of excluded sections (e.g., "connections,PGPCertificates")
- `fieldsCopied` (integer) — count of extension fields successfully copied
- `encryptedFieldsSkipped` (integer) — count of encrypted fields that could not be copied
- `testEnvironmentId` (string) — echoed back
- `prodEnvironmentId` (string) — echoed back
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 19. updateMapExtension

**Action Name**: `updateMapExtension`
**Linked Process**: Process O - Update Map Extension
**Flow Service Operation**: `PROMO - FSS Op - UpdateMapExtension`
**Request Profile**: `PROMO - Profile - UpdateMapExtensionRequest`
**Response Profile**: `PROMO - Profile - UpdateMapExtensionResponse`
**Service Type**: Message Action

**Description**: Saves map extension changes for a specified client account environment. **Phase 2 feature — currently returns `MAP_EXTENSION_READONLY` error.** Map extension updates are destructive (omitted mappings/functions are deleted), so Phase 1 provides read-only access and Test-to-Prod copy only. Full editing will be enabled in Phase 2 with field-level granularity controls.

**Request Fields**:
- `clientAccountId` (string, required) — target client sub-account ID
- `environmentId` (string, required) — target environment ID
- `mapExtensionId` (string, required) — map extension ID from summary query
- `mapExtensionPayload` (string, required) — JSON-serialized map extension update
- `userSsoGroups` (array of strings, required) — for access validation
- `userEmail` (string, required) — for audit trail

**Response Fields**:
- `success` (boolean)
- `mapExtensionId` (string) — echoed back
- `mapName` (string) — name of the map extension
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

**Phase 1 Behavior**: Returns `success=false`, `errorCode=MAP_EXTENSION_READONLY`, `errorMessage="Map extension editing is not yet available. Use Test-to-Prod copy for map extensions."` for all requests.

---

### 20. `checkReleaseStatus` — Check Release Propagation Status

**Process**: PROMO - Process P - CheckReleaseStatus
**FSS Operation**: PROMO - FSS Op - CheckReleaseStatus

**Description**: Checks the propagation status of Integration Pack releases. Queries the PromotionLog for release IDs, then calls GET ReleaseIntegrationPackStatus for each. Supports checking production releases, test releases, or both. Releases can take up to 1 hour to propagate after ReleaseIntegrationPack is called.

**Request Fields**:
- `promotionId` (string, required) — PromotionLog record to check
- `releaseType` (string, required: "PRODUCTION" | "TEST" | "ALL") — which release(s) to check

**Response Fields**:
- `success` (boolean)
- `releases` (array):
  - `releaseId` (string) — the release ID from ReleaseIntegrationPack response
  - `releaseType` (string) — "PRODUCTION" or "TEST"
  - `integrationPackName` (string) — name of the Integration Pack
  - `status` (string) — "PENDING", "IN_PROGRESS", "COMPLETE", or "FAILED"
  - `startTime` (string) — when the release was initiated
  - `completionTime` (string) — when propagation completed (empty if not yet complete)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

**Process Logic**:
1. Query DataHub PromotionLog by `promotionId` to retrieve `releaseId` and `testReleaseId`
2. Based on `releaseType`:
   - "PRODUCTION": check `releaseId` only
   - "TEST": check `testReleaseId` only
   - "ALL": check both
3. For each release ID, call GET ReleaseIntegrationPackStatus (HTTP Op #8)
4. Map results to response format
5. If a release ID is empty/null (e.g., no test release for non-hotfix), skip it

**Error Codes**:
- `PROMOTION_NOT_FOUND` — no PromotionLog record found for the given `promotionId`
- `RELEASE_NOT_FOUND` — the requested release type has no release ID recorded

---

### 21. validateScript

**Action Name**: `validateScript`
**Linked Process**: Process Q - Validate Script
**Flow Service Operation**: `PROMO - FSS Op - ValidateScript`
**Request Profile**: `PROMO - Profile - ValidateScriptRequest`
**Response Profile**: `PROMO - Profile - ValidateScriptResponse`
**Service Type**: Message Action

**Description**: Validates the syntax and security of Groovy or JavaScript scripts used in map extension functions. Performs compile-time checking without executing the script. For Groovy, applies AST-level security validation blocking dangerous imports (Runtime, ProcessBuilder, File, Socket, reflection, GroovyShell/ClassLoader) and receivers. For JavaScript, uses Nashorn's compile-only mode. Entirely stateless — no HTTP API calls, no DataHub operations. Scoped to the extension management system (Phase 7); not integrated into the promotion workflow.

**Request Fields**:
- `clientAccountId` (string, required) — target client sub-account ID (context only, not used for API calls)
- `environmentId` (string, required) — target environment ID (context only)
- `mapExtensionId` (string, required) — map extension ID from summary query
- `functionName` (string, required) — name of the script function being validated
- `scriptContent` (string, required) — the full script source to validate
- `language` (string, required: "GROOVY" | "JAVASCRIPT") — script language (case-insensitive, normalized to uppercase)
- `userSsoGroups` (array of strings, required) — for audit trail
- `userEmail` (string, required) — for audit trail

**Response Fields**:
- `success` (boolean) — `true` if the validation engine ran (even if the script is invalid); `false` only on internal engine failure
- `errorCode` (string, optional) — set for input validation failures or internal errors
- `errorMessage` (string, optional) — human-readable error description
- `language` (string) — echoed (normalized to uppercase)
- `functionName` (string) — echoed
- `isValid` (boolean) — `true` if the script passed all validation checks; `false` if syntax or security errors were found
- `errors` (array) — detailed error list (empty when `isValid=true`)
  - `line` (integer) — source line number (0 if unavailable)
  - `column` (integer) — source column number (0 if unavailable)
  - `message` (string) — error description
  - `type` (string: "SYNTAX" | "SECURITY" | "SIZE") — error category
- `warningCount` (integer) — reserved for future rules (always 0)
- `validatedAt` (string) — ISO 8601 UTC timestamp of validation

**Process Logic**:
1. Parse request fields from FSS listener
2. Validate `language` is GROOVY or JAVASCRIPT → `INVALID_LANGUAGE` if not
3. Validate `scriptContent` is non-empty → `SCRIPT_EMPTY` if blank
4. Validate script size ≤ 10 KB → `SCRIPT_TOO_LARGE` if exceeded
5. **Groovy path**: Configure `SecureASTCustomizer` with blocked imports/receivers → `CompilerConfiguration` → `GroovyShell.parse()` (compile without execute). Catch `MultipleCompilationErrorsException` for syntax/security errors.
6. **JavaScript path**: `ScriptEngineManager.getEngineByName("nashorn")` → `Compilable.compile()` (parse without execute). Catch `ScriptException` for syntax errors.

**Error Codes (specific to this action)**:
- `INVALID_LANGUAGE` — `language` is not GROOVY or JAVASCRIPT
- `SCRIPT_EMPTY` — `scriptContent` is blank or whitespace only
- `SCRIPT_TOO_LARGE` — script exceeds 10 KB size limit
- `GROOVY_SYNTAX_ERROR` — Groovy compilation failed (details in `errors[]` with `type="SYNTAX"`)
- `GROOVY_SECURITY_VIOLATION` — blocked import or receiver detected (details in `errors[]` with `type="SECURITY"`)
- `JAVASCRIPT_SYNTAX_ERROR` — JavaScript parse failed (details in `errors[]` with `type="SYNTAX"`)
- `VALIDATION_INTERNAL_ERROR` — engine crash (top-level `success=false`)

**Security Model**: This action performs local validation only — no external API calls, no DataHub writes. The `clientAccountId`, `environmentId`, and `userSsoGroups` fields are accepted for context/audit but are not used for authorization checks. The script content never executes; only compile/parse operations are performed.

---

## Configuration Values

The Flow Service requires one configuration value to be set at deployment:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `primaryAccountId` | String | Yes | The primary Boomi account ID used in all Partner API calls. This ID is passed to every integration process via Dynamic Process Properties. |

**Setting Configuration Values**:
1. In AtomSphere, navigate to the deployed Flow Service component
2. Click "Configuration Values"
3. Add `primaryAccountId` with your primary account ID
4. Save and restart the listener if needed

---

## Deployment Steps

### Step 1: Create Packaged Component

1. In AtomSphere, navigate to the `PROMO - Flow Service` component
2. Select "Create Packaged Component"
3. Enter version (e.g., "1.0.0")
4. Add deployment notes
5. Mark as "shareable" if integrating into a pack

### Step 2: Deploy to Public Cloud Atom

1. Navigate to "Deploy" → "Deployments"
2. Select the packaged Flow Service component
3. Choose deployment target: **Public Boomi Cloud Atom**
4. Select environment (e.g., "Production")
5. Deploy

### Step 3: Verify Deployment

1. Navigate to "Runtime Management" → "Listeners"
2. Verify all 21 processes are visible and running:
   - `PROMO - FSS Op - GetDevAccounts`
   - `PROMO - FSS Op - ListDevPackages`
   - `PROMO - FSS Op - ResolveDependencies`
   - `PROMO - FSS Op - ExecutePromotion`
   - `PROMO - FSS Op - PackageAndDeploy`
   - `PROMO - FSS Op - QueryStatus`
   - `PROMO - FSS Op - ManageMappings`
   - `PROMO - FSS Op - QueryPeerReviewQueue`
   - `PROMO - FSS Op - SubmitPeerReview`
   - `PROMO - FSS Op - GenerateComponentDiff`
   - `PROMO - FSS Op - ListIntegrationPacks`
   - `PROMO - FSS Op - QueryTestDeployments`
   - `PROMO - FSS Op - CancelTestDeployment`
   - `PROMO - FSS Op - WithdrawPromotion`
   - `PROMO - FSS Op - ListClientAccounts`
   - `PROMO - FSS Op - GetExtensions`
   - `PROMO - FSS Op - UpdateExtensions`
   - `PROMO - FSS Op - CopyExtensionsTestToProd`
   - `PROMO - FSS Op - UpdateMapExtension`
   - `PROMO - FSS Op - CheckReleaseStatus`
   - `PROMO - FSS Op - ValidateScript`
3. Note the full service URL: `https://{cloud-base-url}/fs/PromotionService`

---

## Flow Connector Setup

After deploying the Flow Service, configure the Flow application to connect to it.

### Step 1: Create Boomi Integration Service Connector

1. In Flow, navigate to "Connectors"
2. Create new connector: **Boomi Integration Service**
3. Configure:
   - **Runtime Type**: Public Cloud
   - **Path to Service**: `/fs/PromotionService`
   - **Authentication**: Basic Auth
     - Username: (from Shared Web Server User Management)
     - API Token: (from API Token Management)

### Step 2: Retrieve Connector Configuration

1. Click "Retrieve Connector Configuration Data"
2. Flow will automatically discover all 21 message actions
3. Auto-generated Flow Types will be created (see below)

### Step 3: Set Configuration Value

1. In the connector configuration, locate "Configuration Values"
2. Set `primaryAccountId` to your primary Boomi account ID
3. Save connector

---

## Auto-Generated Flow Types

When you retrieve the connector configuration, Flow automatically generates request and response types for each message action.

**Naming Convention**: `{ActionName} {REQUEST|RESPONSE} - {ProfileEntryName}`

**Generated Types**:

1. `getDevAccounts REQUEST - getDevAccountsRequest`
2. `getDevAccounts RESPONSE - getDevAccountsResponse`
3. `listDevPackages REQUEST - listDevPackagesRequest`
4. `listDevPackages RESPONSE - listDevPackagesResponse`
5. `resolveDependencies REQUEST - resolveDependenciesRequest`
6. `resolveDependencies RESPONSE - resolveDependenciesResponse`
7. `executePromotion REQUEST - executePromotionRequest`
8. `executePromotion RESPONSE - executePromotionResponse`
9. `packageAndDeploy REQUEST - packageAndDeployRequest`
10. `packageAndDeploy RESPONSE - packageAndDeployResponse`
11. `queryStatus REQUEST - queryStatusRequest`
12. `queryStatus RESPONSE - queryStatusResponse`
13. `manageMappings REQUEST - manageMappingsRequest`
14. `manageMappings RESPONSE - manageMappingsResponse`
15. `queryPeerReviewQueue REQUEST - queryPeerReviewQueueRequest`
16. `queryPeerReviewQueue RESPONSE - queryPeerReviewQueueResponse`
17. `submitPeerReview REQUEST - submitPeerReviewRequest`
18. `submitPeerReview RESPONSE - submitPeerReviewResponse`
19. `generateComponentDiff REQUEST - generateComponentDiffRequest`
20. `generateComponentDiff RESPONSE - generateComponentDiffResponse`
21. `listIntegrationPacks REQUEST - listIntegrationPacksRequest`
22. `listIntegrationPacks RESPONSE - listIntegrationPacksResponse`
23. `queryTestDeployments REQUEST - queryTestDeploymentsRequest`
24. `queryTestDeployments RESPONSE - queryTestDeploymentsResponse`
25. `cancelTestDeployment REQUEST - cancelTestDeploymentRequest`
26. `cancelTestDeployment RESPONSE - cancelTestDeploymentResponse`
27. `withdrawPromotion REQUEST - withdrawPromotionRequest`
28. `withdrawPromotion RESPONSE - withdrawPromotionResponse`
29. `listClientAccounts REQUEST - listClientAccountsRequest`
30. `listClientAccounts RESPONSE - listClientAccountsResponse`
31. `getExtensions REQUEST - getExtensionsRequest`
32. `getExtensions RESPONSE - getExtensionsResponse`
33. `updateExtensions REQUEST - updateExtensionsRequest`
34. `updateExtensions RESPONSE - updateExtensionsResponse`
35. `copyExtensionsTestToProd REQUEST - copyExtensionsTestToProdRequest`
36. `copyExtensionsTestToProd RESPONSE - copyExtensionsTestToProdResponse`
37. `updateMapExtension REQUEST - updateMapExtensionRequest`
38. `updateMapExtension RESPONSE - updateMapExtensionResponse`
39. `checkReleaseStatus REQUEST - checkReleaseStatusRequest`
40. `checkReleaseStatus RESPONSE - checkReleaseStatusResponse`
41. `validateScript REQUEST - validateScriptRequest`
42. `validateScript RESPONSE - validateScriptResponse`

These types are used throughout the Flow application to ensure type safety when calling the Flow Service operations.

---

## Timeout and Async Behavior

The Flow Service leverages Boomi's built-in async processing for long-running operations:

1. **Initial Request**: Flow sends request to Flow Service operation
2. **Flow Service Processing**: Integration process begins execution
3. **Automatic Wait Response**: If processing exceeds threshold (typically 30s), Flow Service automatically returns a wait response
4. **Flow UI Spinner**: Flow displays spinner/progress indicator to user
5. **Callback on Completion**: When Integration process completes, Flow Service callbacks to Flow
6. **Result Display**: Flow receives final response and updates UI

**User Experience**:
- User can close the browser tab during long operations
- State is persisted via IndexedDB
- User can return later to check status
- No manual polling required

**Typical Operation Durations**:
- `getDevAccounts`: < 5 seconds
- `listDevPackages`: 10-30 seconds (depends on package count)
- `resolveDependencies`: 5-15 seconds (depends on dependency depth)
- `executePromotion`: 30-120 seconds (depends on component count)
- `packageAndDeploy`: 20-60 seconds (depends on target environment count)
- `queryStatus`: < 5 seconds
- `manageMappings`: < 5 seconds
- `generateComponentDiff`: 2-5 seconds (two API calls + Groovy normalization)
- `listIntegrationPacks`: < 5 seconds

---

## Error Handling Contract

All Flow Service responses follow a consistent error handling pattern.

**Standard Response Fields**:

| Field | Type | Always Present | Description |
|-------|------|----------------|-------------|
| `success` | boolean | Yes | `true` if operation succeeded, `false` if error occurred |
| `errorCode` | string | Conditional | Error code for programmatic handling (present when success=false) |
| `errorMessage` | string | Conditional | Human-readable error description (present when success=false) |

**Flow Decision Logic**:

In Flow, every operation response should be followed by a Decision step:

```
Decision: Check Success
  - If success = true → Continue to next step
  - If success = false → Branch to error handling path
```

**Common Error Codes**:

| Error Code | Description | User Action |
|------------|-------------|-------------|
| `AUTH_FAILED` | API authentication failed | Check API token configuration |
| `ACCOUNT_NOT_FOUND` | Dev account ID invalid | Verify account exists |
| `COMPONENT_NOT_FOUND` | Component ID not found | Check component exists in dev account |
| `DATAHUB_ERROR` | DataHub query/update failed | Contact administrator |
| `API_RATE_LIMIT` | Partner API rate limit exceeded | Retry after cooldown period |
| `DEPENDENCY_CYCLE` | Circular dependency detected | Review component references |
| `INVALID_REQUEST` | Request validation failed | Check required fields |
| `PROMOTION_FAILED` | One or more components failed during promotion — the promotion branch has been deleted and no component mappings were written | Re-run the promotion after resolving the underlying issue |
| `PROMOTION_NOT_COMPLETED` | Process D gate: PromotionLog status is not one of `COMPLETED`, `TEST_DEPLOYED`, `ADMIN_APPROVED`, or `PENDING_PACK_ASSIGNMENT` — the promotion must reach a valid packaging state before proceeding | Ensure the promotion has completed and passed all required reviews before attempting to package and deploy |
| `DEPLOYMENT_FAILED` | Environment deployment failed | Check target environment status |
| `MISSING_CONNECTION_MAPPINGS` | One or more connection mappings not found in DataHub | Admin must seed missing mappings via Mapping Viewer |
| `BRANCH_LIMIT_REACHED` | Too many active promotion branches (limit: 20 per account) | Wait for pending reviews to complete before starting new promotions |
| `SELF_REVIEW_NOT_ALLOWED` | Reviewer attempted to review their own promotion submission | A different team member must perform the peer review |
| `ALREADY_REVIEWED` | Promotion has already been peer-reviewed | No action needed; check current status |
| `INVALID_REVIEW_STATE` | Promotion is not in the expected state for this review action | Verify the promotion status before retrying |
| `INSUFFICIENT_TIER` | User's SSO groups do not include a dashboard-access tier (CONTRIBUTOR or ADMIN) | User must be assigned ABC_BOOMI_FLOW_CONTRIBUTOR or ABC_BOOMI_FLOW_ADMIN group |
| `TEST_DEPLOY_FAILED` | Test environment deployment failed | Check test environment status and retry |
| `HOTFIX_JUSTIFICATION_REQUIRED` | Emergency hotfix missing justification text | Provide hotfix justification before proceeding |
| `INVALID_DEPLOYMENT_TARGET` | deploymentTarget must be "TEST" or "PRODUCTION" | Correct the deployment target value |
| `TEST_PROMOTION_NOT_FOUND` | testPromotionId references a non-existent or non-TEST_DEPLOYED promotion | Verify the test promotion exists and is in TEST_DEPLOYED status |
| `SELF_APPROVAL_NOT_ALLOWED` | Admin attempted to approve/deploy their own promotion (`adminEmail` matches `initiatedBy`) | A different admin must approve the deployment |
| `MERGE_FAILED` | Branch merge request failed (MergeRequest status returned MERGE_FAILED) | Review merge error details; may indicate conflicting changes on main |
| `MERGE_TIMEOUT` | Branch merge request did not complete within 60 seconds (12 polling attempts) | Retry the deployment; if persistent, check branch status manually |
| `PROMOTION_NOT_FOUND` | promotionId references a non-existent PromotionLog record | Verify the promotion ID is correct |
| `INVALID_PROMOTION_STATUS` | Promotion is not in the expected status for the requested operation | Check current promotion status before retrying |
| `NOT_PROMOTION_INITIATOR` | Requester is not the original initiator of the promotion | Only the person who initiated the promotion can withdraw it |
| `EXTENSION_NOT_FOUND` | Extension component has no ExtensionAccessMapping record (unknown component) | Admin must rebuild extension access cache or verify component exists |
| `UNAUTHORIZED_EXTENSION_EDIT` | User's SSO groups do not authorize editing this extension component | Contact admin for access or request extension access mapping update |
| `CONNECTION_EDIT_ADMIN_ONLY` | Non-admin user attempted to edit a connection extension | Only ADMIN tier users can modify connection extensions |
| `COPY_FAILED` | Test-to-Prod extension copy failed during GET or UPDATE | Check environment accessibility and retry |
| `MAP_EXTENSION_READONLY` | Map extension editing is not yet available (Phase 2 feature) | Use Test-to-Prod copy for map extensions |
| `CLIENT_ACCOUNT_NOT_FOUND` | Client account ID not found in ClientAccountConfig | Verify the client account is registered in DataHub |
| `RELEASE_NOT_FOUND` | The requested release type has no release ID recorded in the PromotionLog | Verify the promotion was deployed and the correct releaseType is specified |
| `PACK_ASSIGNMENT_REQUIRED` | Mode 1 test deployment succeeded but no Integration Pack history was found for this process — admin must assign an IP via Mode 4 (PACK_ASSIGNMENT) | Admin selects an Integration Pack on Page 7 and submits via the pack assignment flow |
| `INVALID_LANGUAGE` | Q | Unsupported `language` value (must be GROOVY or JAVASCRIPT) | Correct the `language` field in the request |
| `SCRIPT_EMPTY` | Q | Script content is blank or whitespace only | Provide non-empty `scriptContent` |
| `SCRIPT_TOO_LARGE` | Q | Script exceeds 10 KB size limit | Reduce script size below 10,240 bytes |
| `GROOVY_SYNTAX_ERROR` | Q | Groovy compilation failed — syntax error in script | Review the `errors` array for line/column details and fix the script |
| `GROOVY_SECURITY_VIOLATION` | Q | Blocked import or receiver detected by security policy | Remove references to blocked classes (Runtime, ProcessBuilder, File, Socket, reflection, GroovyShell) |
| `JAVASCRIPT_SYNTAX_ERROR` | Q | JavaScript parse failed — syntax error in script | Review the `errors` array for line/column details and fix the script |
| `VALIDATION_INTERNAL_ERROR` | Q | Validation engine internal failure | Retry; if persistent, contact administrator |

**Error Handling Best Practices**:

1. Always check `success` field before processing response data
2. Log `errorCode` and `errorMessage` to Flow console for debugging
3. Display user-friendly error messages in the UI (translate errorCode to UI text)
4. Provide retry mechanism for transient errors (e.g., rate limits)
5. For critical errors, allow user to contact support with error details

---

## Platform API Retry and Polling Specification

### Retry Policy

All Platform API HTTP calls MUST implement retry logic with the following parameters:

| Parameter | Value |
|-----------|-------|
| Maximum retries | 3 |
| Backoff strategy | Exponential |
| Delay sequence | 1s, 2s, 4s |
| Retryable responses | HTTP 429 (rate limit), HTTP 5xx (server error) |
| Non-retryable responses | HTTP 4xx (except 429) — fail immediately |

**Critical retry points:**
- **Process C** (per-component loop): Each component promotion involves multiple API calls (GET Component, Create/Update Component). A 429 mid-loop must retry the failed call, not restart the entire loop.
- **Process D** (merge/deploy sequence): A 429 after a successful merge but before packaging leaves the system in a recoverable state — the merge is idempotent, so retrying the full sequence is safe.

### Merge Status Polling (Process D)

After creating a MergeRequest, Process D MUST poll the merge status until completion:

| Parameter | Value |
|-----------|-------|
| Polling endpoint | `GET /MergeRequest/{mergeRequestId}` |
| Check interval | 5 seconds |
| Maximum retries | 12 (60 seconds total) |
| Success status | `COMPLETED` — proceed to packaging |
| Failure status | `MERGE_FAILED` — set `errorCode=MERGE_FAILED`, include merge error details |
| Timeout | If status is still `PENDING` after 12 checks, set `errorCode=MERGE_TIMEOUT` with message "Merge request did not complete within 60 seconds" |

Process D MUST NOT proceed to Create PackagedComponent until the merge status is `COMPLETED`.

---

## Security Considerations

### Authentication

- Flow Service uses Basic Auth with Shared Web Server User credentials
- API tokens should be stored securely in Flow connector configuration
- Rotate API tokens periodically (recommended: every 90 days)

### Token Rotation Procedure

When rotating API tokens, follow this sequence to avoid service interruption:

1. **Create new API token** in Boomi AtomSphere → Settings → API Token Management
2. **Update HTTP Client connection** with the new token (username remains unchanged)
3. **Test with a read-only API call** (e.g., `GET Component` for a known component) to verify the new token works
4. **Revoke the old token** only after confirming the new token is functional
5. **Graceful 401 failure behavior**: If a token is revoked while in use, all Platform API calls will return HTTP 401. The Flow Service will return `errorCode=AUTH_FAILED` with `errorMessage` describing the authentication failure. No data corruption can occur — the API is read-only until promotion writes, which fail safely on 401.

### Authorization

- Partner API requires primary account privileges
- All sub-account access uses `overrideAccount` parameter
- Flow Service inherits permissions from API token owner

### userSsoGroups Accepted Risk

The `userSsoGroups` field is client-supplied from the Flow authorization context and is not independently verified against Azure AD at runtime. This is an accepted platform constraint: Boomi Flow does not provide a server-side mechanism to query the identity provider directly.

**Mitigation**: The API token serves as the true security boundary. The token is scoped to the primary account and its sub-accounts. Even if `userSsoGroups` were manipulated, the attacker could only access accounts already reachable by the API token.

**Future consideration**: If Boomi Flow adds support for server-side SSO group validation, implement direct Azure AD group membership verification to replace client-supplied claims.

### IDOR Protection Note

The `devAccountId` parameter in several actions (listDevPackages, executePromotion, etc.) is accepted from the client without backend authorization check against DevAccountAccess records. Currently, the API token's account scope provides the security boundary.

**Recommendation**: Process C SHOULD validate `devAccountId` against DevAccountAccess records for the requesting user before proceeding with promotion. This adds defense-in-depth beyond the API token scope.

### Data Privacy

- Credential values are stripped during promotion (Process C)
- No sensitive data persisted in DataHub mapping tables
- All API communication over HTTPS

---

## Monitoring and Troubleshooting

### Process Logs

1. Navigate to "Process Reporting" in AtomSphere
2. Filter by process names: `PROMO - FSS Op - *`
3. Review execution logs for errors or performance issues

### Common Issues

**Issue**: Flow Service operation times out
**Cause**: Component count too high, API rate limiting
**Solution**: Increase timeout threshold, add pagination

**Issue**: Dependency resolution returns incomplete tree
**Cause**: Circular dependencies or broken references
**Solution**: Review component references in dev account, check for orphaned components

**Issue**: Promotion creates duplicates
**Cause**: DataHub mapping not found, componentId mismatch
**Solution**: Query mappings via `manageMappings` action, verify dev/prod ID pairs

**Issue**: Deployment fails to target environment
**Cause**: Environment ID invalid, insufficient permissions
**Solution**: Verify environment exists in account group, check API token permissions

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-16 | Initial Flow Service specification |
| 1.1.0 | 2026-02-16 | Multi-environment deployment: 3 deployment modes (TEST, PRODUCTION from test, PRODUCTION hotfix), new queryTestDeployments action, packPurpose filter on listIntegrationPacks |
| 1.2.0 | 2026-02-16 | Added cancelTestDeployment action for test branch cleanup; added PROMOTION_NOT_FOUND and INVALID_PROMOTION_STATUS error codes |
| 1.3.0 | 2026-02-17 | Added withdrawPromotion action for initiator-driven withdrawal of pending promotions; added NOT_PROMOTION_INITIATOR error code |
| 2.0.0 | 2026-02-17 | Extension Editor: 5 new message actions (listClientAccounts, getExtensions, updateExtensions, copyExtensionsTestToProd, updateMapExtension), 6 new error codes, total actions 14→19 |
| 2.1.0 | 2026-02-18 | Added checkReleaseStatus action (Process P) for Integration Pack release propagation polling; added RELEASE_NOT_FOUND error code, total actions 19→20 |
| 2.2.0 | 2026-02-18 | Redesigned packageAndDeploy: 4 modes (added Mode 4 PACK_ASSIGNMENT), main branch protection (Mode 1 packages from branch), admin IP ownership (IP fields moved to admin/Page 7), new response fields needsPackAssignment and autoDetectedPackId, branchPreserved always false; listIntegrationPacks now called from Page 7 |
| 2.3.0 | 2026-02-18 | Added validateScript action (Process Q) for Groovy/JavaScript syntax and security validation; total actions 20→21 |

---

## Related Documentation

- Partner API Reference: https://help.boomi.com/docs/atomsphere/integration/api/r-atm-partner_api_5f0c0b46-e0b0-4a45-9437-4b8e66dd1c74/
- Flow Service Developer Guide: https://help.boomi.com/docs/flow/flow-configuration/t-flow-configure_flow_service_connector_77e89cc9-a02e-43fd-8c24-7b0c4b41a479/
- DataHub Usage: https://help.boomi.com/docs/atomsphere/integration/datahub/c-atm-datahub_overview_1b87a58b-5b9f-4b4e-9d0d-5d0e7b5e5e5e/

---

## Support

For issues or questions:
- Internal support: Contact Boomi platform team
- External support: Open ticket via Boomi Support Portal
- Community: Boomi Community Forums

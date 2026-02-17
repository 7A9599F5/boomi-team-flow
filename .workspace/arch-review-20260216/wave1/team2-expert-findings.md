# Team 2: Integration Engine Expert Review Findings

**Reviewer**: Boomi Integration Expert
**Date**: 2026-02-16
**Scope**: All integration process build guides (Processes A0, A, B, C, D, E, E2, E3, F, G, J, E4), DPP catalog, HTTP Client setup, process canvas fundamentals, flow service spec

---

## Critical Issues

### C1. Processes E2 and E3 Have No Dedicated Build Guide Sections
**Files**: `docs/build-guide/index.md`, `docs/build-guide/07-process-e-status-and-review.md`
**Impact**: Two of the 12 integration processes (E2: queryPeerReviewQueue, E3: submitPeerReview) are referenced throughout the system (flow service spec, flow dashboard pages 5-6, integration-patterns.md, architecture.md) but have **no dedicated build guide documentation**. File 07 (`process-e-status-and-review.md`) covers only Process E. The profiles exist (`queryPeerReviewQueue-*.json`, `submitPeerReview-*.json`) and the flow-service-spec.md defines the full contract, but there is zero guidance on process canvas construction, shape-by-shape layout, DataHub query patterns, or the self-review exclusion logic at the integration process level.

**Specific gaps**:
- E2: No documentation of how the DataHub query excludes the requester's own promotions (filter: `initiatedBy != requesterEmail`). The flow-service-spec describes the behavior, but the build guide does not show the implementation shapes.
- E3: No documentation of the state machine logic (validating `peerReviewStatus == PENDING_PEER_REVIEW` before allowing review), the self-review prevention check at the backend, or the DataHub update pattern for changing `peerReviewStatus` and `adminReviewStatus` fields.
- Neither process appears in the FSS Operation table in `04-process-canvas-fundamentals.md:107-115`, which only lists 7 operations.

### C2. Process Canvas Fundamentals Lists Only 7 FSS Operations; 5 Are Missing
**File**: `docs/build-guide/04-process-canvas-fundamentals.md:107-115`
**Impact**: The FSS Operation creation table lists only 7 operations (A0, A, B, C, D, E, F). Missing from the table: `QueryPeerReviewQueue` (E2), `SubmitPeerReview` (E3), `GenerateComponentDiff` (G), `ListIntegrationPacks` (J), and `QueryTestDeployments` (E4). Builders following the guide sequentially will not create these FSS Operations and will be unable to link the corresponding processes to the Flow Service.

### C3. Process Canvas Fundamentals Lists Only 14 Profiles; 10 Are Missing
**File**: `docs/build-guide/04-process-canvas-fundamentals.md:33-49`
**Impact**: The profile import table lists 14 profiles (7 request + 7 response for A0, A, B, C, D, E, F). Missing: profiles for E2, E3, G, J, and E4 (10 additional profiles). The repo has 24 profile JSON files total but the guide only instructs importing 14. Builders will discover missing profiles when they reach Processes G, J, E2, E3, and E4.

### C4. Branch Limit Inconsistency Across Documents
**Files**: `docs/build-guide/10-process-c-execute-promotion.md:79`, `docs/build-guide/22-phase7-multi-environment.md:151-152`, `docs/build-guide/02-http-client-setup.md:307`, `integration/flow-service/flow-service-spec.md:670`
**Impact**: The branch limit threshold is documented with conflicting values:
- Process C build guide (step 3.6): `activeBranchCount >= 15`
- Phase 7 (step 7.5): "Change the branch count threshold from 18 to 15" -- implying the original was 18
- HTTP Client setup (Op 11 description): "10-branch limit"
- Flow service spec error table: "limit: 20 per account"

Four different numbers (10, 15, 18, 20) appear across the docs for the same threshold. A builder cannot determine the correct value.

---

## Major Issues

### M1. Process E Build Guide Lacks `reviewStage` Filter Implementation
**File**: `docs/build-guide/07-process-e-status-and-review.md:31-41`
**Impact**: The flow-service-spec.md defines a `reviewStage` request field for `queryStatus` (line 261: `"PENDING_PEER_REVIEW" | "PENDING_ADMIN_REVIEW" | "ALL"`), and Page 7 (admin approval queue) calls `queryStatus` with `reviewStage = "PENDING_ADMIN_REVIEW"` (`16-flow-dashboard-review-admin.md:47`). However, the Process E build guide only shows simple filters (`promotionId`, `devAccountId`, `status`, `limit`) and does not document how `reviewStage` filtering maps to DataHub queries on `peerReviewStatus` and `adminReviewStatus` fields. The DataHub query logic is incomplete.

### M2. Process E Request/Response Profile Mismatch with Flow Service Spec
**Files**: `docs/build-guide/07-process-e-status-and-review.md:13-20` vs `integration/flow-service/flow-service-spec.md:256-283`
**Impact**: The build guide's Process E request defines fields `promotionId`, `devAccountId`, `status`, `limit` (line 13-16). The flow-service-spec defines `queryType`, `processName`, `componentId`, `startDate`, `endDate`, `reviewStage` (lines 256-261). These are fundamentally different field sets. Similarly, the build guide response has `promotionId`, `devAccountId`, `prodAccountId`, `devPackageId`, `initiatedBy`, etc., while the spec response has `processName`, `promotionDate`, `requestedBy`, `componentCount`, `peerReviewStatus`, `adminReviewStatus`, etc. A builder following the build guide will create a process that does not match the Flow Service contract.

### M3. Process A Response Profile Mismatch with Flow Service Spec
**Files**: `docs/build-guide/08-process-a-list-dev-packages.md:15-17` vs `integration/flow-service/flow-service-spec.md:70-84`
**Impact**: The build guide's Process A response includes `packages` with fields `packageId`, `packageVersion`, `componentId`, `componentName`, `componentType`, `createdDate`, `notes`. The flow-service-spec adds `createdBy` (line 81: "Boomi user who created the package") which is not in the build guide. Minor field but could cause mapping failures if the profile expects it.

### M4. Process A0 Response Profile Mismatch with Flow Service Spec
**Files**: `docs/build-guide/06-process-a0-get-dev-accounts.md:15-17` vs `integration/flow-service/flow-service-spec.md:32-39`
**Impact**: The build guide's Process A0 response contains `accounts` array (line 17). The flow-service-spec defines `devAccounts` array (not `accounts`) plus an `effectiveTier` field (line 34). The build guide does not document: (1) tier resolution logic, (2) the `effectiveTier` response field, (3) how `ADMIN` tier bypasses team group checks. The architecture doc and flow-service-spec describe the two-axis SSO model but the build guide implementation has not been updated to match.

### M5. Process B Response Field Names Mismatch
**Files**: `docs/build-guide/09-process-b-resolve-dependencies.md:19-20` vs `integration/flow-service/flow-service-spec.md:105-112`
**Impact**: The build guide response uses `components` array with fields including `devComponentId`, `name`, `type`, `devVersion`, `prodStatus`, etc. The flow-service-spec uses `dependencies` array with different fields: `componentId` (not `devComponentId`), `dependencyType` ("DEPENDENT" | "INDEPENDENT"), `depth`. These are structurally different representations of the same data.

### M6. Process D Build Guide Missing 3-Mode Decision Logic
**File**: `docs/build-guide/11-process-d-package-and-deploy.md`
**Impact**: The build guide describes Process D as a linear flow: merge -> package -> create/add to pack -> release -> deploy -> delete branch. Phase 7 (`22-phase7-multi-environment.md:73-105`) defines the 3-mode refactor (TEST / PRODUCTION from test / PRODUCTION hotfix) with different branch lifecycle behavior per mode, but these instructions are additive ("update the existing process") rather than providing a complete updated shape-by-shape guide. A builder must mentally merge two documents to construct the final process. The Decision shape on `deploymentTarget` is mentioned but not fully detailed with all branch paths.

### M7. Process D Missing MergeRequest Poll Loop
**File**: `docs/build-guide/11-process-d-package-and-deploy.md:75`
**Impact**: Step 2.6 says "After execution, poll `GET /MergeRequest/{mergeRequestId}` until `stage = MERGED`" but does not specify: (1) the poll interval, (2) the max retry count, (3) the HTTP operation to use for the GET, (4) the DPP to store the result. Compare with Process C step 3.8 which specifies 5-second delay, max 6 retries. Process D's merge poll is under-specified.

### M8. DPP Catalog Missing Processes D, E2, E3, E4, G, and J
**File**: `docs/build-guide/20-appendix-dpp-catalog.md`
**Impact**: The DPP catalog documents Global DPPs, Process B DPPs, and Process C DPPs. It omits DPPs for Processes D (`mergeRequestId`, `packagedComponentId`, `createNewPack`, `targetAccountGroupId`, `deploymentTarget`, `isHotfix`, etc.), E2 (none documented), E3 (none documented), E4 (none documented), G (`branchXml`, `mainXml`, `branchXmlNormalized`, `mainXmlNormalized`, `componentAction`, `branchVersion`, `mainVersion`), and J (`suggestForProcess`, `suggestedPackId`, `suggestedPackName`, `packList`). The catalog is roughly 40% complete.

### M9. Process E4 Incompletely Specified
**File**: `docs/build-guide/22-phase7-multi-environment.md:40-69`
**Impact**: Process E4 (Query Test Deployments) has minimal specification: 5 numbered steps with high-level instructions like "DataHub Connector (Query PromotionLog)" and "Exclude promotions that have a matching PRODUCTION record." Critical implementation details missing:
- How to implement the "exclude already promoted" logic (DataHub does not support NOT EXISTS or subquery joins natively -- this requires post-query Groovy filtering or a two-query approach)
- No shape-by-shape canvas guide (every other process has one)
- No DPP documentation
- No error handling specification beyond "wrap in Try/Catch" (implied)

---

## Minor Issues

### m1. Build Order Checklist Inconsistency
**File**: `docs/build-guide/13-process-g-component-diff.md:109-122`
**Impact**: The build order checklist at the end of file 13 lists a different order than `integration-patterns.md:43-54` and the actual file ordering in the build guide. The checklist puts F first, then A0, E, E2, E3, J, G, A, B, C, D (11 processes). The integration-patterns.md puts A0, A, B, C, E, E2, E3, F, G, J, D. These are intentionally different (build guide = simplest-first, integration-patterns = dependency-first) but could confuse builders who expect consistency.

### m2. Process A Missing Rate-Limit Retry Logic
**File**: `docs/build-guide/08-process-a-list-dev-packages.md:58`
**Impact**: Step 6 adds a 120ms `Thread.sleep()` between component metadata enrichment calls, but there is no retry logic for 429/503 responses. The error handling section (line 77-80) mentions `errorCode = "API_RATE_LIMIT"` as a catch case, but the build guide does not show how to implement retry (e.g., exponential backoff, re-queue failed calls). Other processes (C, D) also lack retry logic but Process A is the most likely to hit rate limits due to per-package metadata queries.

### m3. Process C Step 6 Contradicts Step 5.6
**File**: `docs/build-guide/10-process-c-execute-promotion.md:158-159`
**Impact**: Step 6 says "Set Properties -- Initialize Mapping Cache" and sets `componentMappingCache = {}`. However, step 5.6 (`validate-connection-mappings.groovy`) already writes found connection mappings into `componentMappingCache`. Resetting it to `{}` at step 6 would erase the pre-loaded connection mappings, breaking reference rewriting for operations and processes that reference connections. The step 6 description does say "now only needs non-connection mappings since connection mappings are pre-loaded" but the actual instruction `DPP componentMappingCache = {}` contradicts this.

### m4. Groovy Script `build-visited-set.groovy` Not Shown Inline
**File**: `docs/build-guide/09-process-b-resolve-dependencies.md:87-93`
**Impact**: Unlike Process A0 (which shows inline Groovy for steps 3 and 5), Process B step 7 says "Paste contents of `/integration/scripts/build-visited-set.groovy`" without showing the code. The script exists in the repo and is correct, but the build guide is inconsistent in its approach to Groovy code display. Some scripts are inlined, others are referenced. Minor readability issue.

### m5. Process C SKIPPED Status Implementation Underspecified
**File**: `docs/build-guide/10-process-c-execute-promotion.md:298`
**Impact**: Step 18 (Catch Block) says to "Mark dependent components as SKIPPED -- any component in the remaining loop that references `currentComponentId`" but does not specify how to identify dependents within the sorted array. The type priority order provides a heuristic (if a connection fails, operations/maps/processes are affected), but the actual implementation would need to check each remaining component's XML for references to the failed component, which is not documented.

### m6. Process D Missing HTTP Operation for QUERY IntegrationPack
**File**: `docs/build-guide/02-http-client-setup.md:36-53`
**Impact**: The HTTP Client operations table lists 15 operations. Process J references `PROMO - HTTP Op - QUERY IntegrationPack` (`12-process-j-list-integration-packs.md:21`), but this operation does not appear in the 15 operations listed in the HTTP Client setup. Similarly, Process D's step 7 references a "release" endpoint that may need a 16th HTTP operation. The BOM is incomplete.

### m7. Process G Stores XML in DPPs -- Potential Size Limitation
**File**: `docs/build-guide/13-process-g-component-diff.md:30-37`
**Impact**: Process G stores full component XML in DPPs (`branchXml`, `mainXml`, `branchXmlNormalized`, `mainXmlNormalized`). Boomi DPPs have a practical size limit (~1MB in some runtime configurations). Large component XML (particularly complex processes or maps) could exceed this limit. The document stream would be more appropriate for passing XML between shapes.

### m8. MergeRequest Create Template References Incorrect Field Names
**File**: `docs/build-guide/11-process-d-package-and-deploy.md:66`
**Impact**: Step 2.5 says the request body has fields `source`, `strategy`, `priorityBranch`. The Platform API MergeRequest create endpoint typically uses `sourceBranchId` and `targetBranchId` (as described in the HTTP operation 12 at `02-http-client-setup.md:350`). These field name inconsistencies between the build guide and the HTTP operation documentation could cause request failures.

---

## Observations

### O1. Strong Error Handling Architecture
Process C's dual Try/Catch pattern (outer for catastrophic failures with branch cleanup, inner per-component for graceful degradation) is a well-designed resilience pattern. The `MISSING_CONNECTION_MAPPINGS` pre-validation (step 5.5-5.7) catches errors before the expensive promotion loop begins.

### O2. Effective Use of DPP-Based State Machine
The `componentMappingCache` pattern in Process C elegantly solves the reference rewriting problem. Combined with the bottom-up sort order, it ensures all dependencies are in the cache before their dependents are processed. This is well-documented and well-reasoned.

### O3. Consistent Process Skeleton Pattern
The Start -> Set Properties -> Logic -> Map -> Return Documents skeleton is consistently applied across all processes. This makes the system predictable and maintainable.

### O4. Branch Lifecycle Management is Sound
The promotion-to-branch, diff-from-branch, merge-on-approval pattern provides good isolation and rollback capability. The TEST mode branch preservation for production-from-test is a thoughtful extension.

### O5. Thread.sleep() for Rate Limiting is Functional but Fragile
The 120ms `Thread.sleep()` calls between API requests are a simple rate-limit strategy. In production, bursty parallel executions (multiple users promoting simultaneously) could still hit rate limits. A more robust approach would use retry-with-backoff, but for a single-user-at-a-time Flow dashboard, the current approach is adequate.

---

## Multi-Environment Assessment

### Completeness of Phase 7 Specification
- **PromotionLog model update** (step 7.1): Well-specified with all 8 new fields documented.
- **Process E4** (step 7.2): Under-specified (see M9 above). The "exclude already promoted" logic is the hardest part and is hand-waved.
- **Process D 3-mode refactor** (step 7.3): Described at a behavioral level but lacks updated shape-by-shape guidance. The Decision shape on `deploymentTarget` introduces 3 parallel paths, significantly increasing process complexity.
- **Process J update** (step 7.4): Well-specified (filter by `packPurpose`).
- **Process C branch limit** (step 7.5): Simple threshold change but the target value is contradicted elsewhere (see C4).
- **Flow dashboard updates** (step 7.6): Described at a feature level, appropriate for Phase 7.
- **Cancel Test Deployment**: Referenced in `docs/architecture.md:287` as a "future consideration" and in `flow/page-layouts/page9-production-readiness.md:202,232` as UI text mentioning canceling, but there is no process, action, or build guide for this capability. Stale test branches will accumulate and eventually hit the branch limit.

### Missing Elements for Production Readiness
1. No `cancelTestDeployment` action or process exists to delete stale branches from abandoned test deployments
2. No branch age monitoring or cleanup automation
3. No documentation of how the `testPromotionId` exclusion works in DataHub (E4 implementation)
4. Process D Mode 2 (PRODUCTION from test) says "skip merge" but does not document how to verify that the branch content is still valid / has not drifted from main since the test deployment

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 4 |
| Major | 9 |
| Minor | 8 |
| Observations | 5 |

**Top 3 Recommendations**:
1. Create dedicated build guide sections for Processes E2, E3, and E4 with full shape-by-shape documentation
2. Reconcile all profile field name and structure mismatches between build guides and flow-service-spec.md (M2, M4, M5)
3. Standardize the branch limit to a single value and document it in one canonical location

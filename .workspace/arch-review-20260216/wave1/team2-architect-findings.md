# Team 2 — Systems Orchestration Architect Review

**Reviewer:** Systems Orchestration Architect
**Scope:** Integration processes (A0, A, B, C, D, E, E2, E3, F, G, J), inter-process data flow, profiles, scalability, failure modes, multi-env refactor
**Date:** 2026-02-16

---

## CRITICAL

### C1. No Concurrency Guard — Parallel Promotions Can Corrupt Shared State

**Files:** `docs/build-guide/10-process-c-execute-promotion.md:4`, `docs/architecture.md:216`

The architecture doc mentions "Concurrency lock via PromotionLog IN_PROGRESS check" but no build guide step implements this. Process C generates a UUID, creates a PromotionLog with IN_PROGRESS, then proceeds. If two users promote the same component tree simultaneously:

1. Both create branches and separate PromotionLog entries (different `promotionId` values, so no DataHub match conflict).
2. Both read the same `componentMappingCache` from DataHub at step 14.
3. Both CREATE new prod components for the same dev component (race on step 15b), resulting in duplicate prod components.
4. Both write conflicting ComponentMapping records to DataHub — last writer wins, orphaning the other prod component.

**Impact:** Duplicate components in production with broken mappings. No mechanism to detect or recover.

**Recommendation:** Add a pre-check in Process C that queries PromotionLog for any record with `devAccountId = {value} AND status IN ("IN_PROGRESS", "PENDING_PEER_REVIEW", "PENDING_ADMIN_REVIEW")` and aborts if found, or implement DataHub advisory locking per dev account. The branch name `promo-{promotionId}` is unique but does not prevent parallel promotions of overlapping components.

---

### C2. Process B BFS Scalability — Unbounded Queue with O(n) API Calls per Node

**Files:** `docs/build-guide/09-process-b-resolve-dependencies.md:78-114`, `integration/scripts/build-visited-set.groovy:42-54`

Each BFS iteration makes 2-3 HTTP API calls (GET ComponentReference, GET ComponentMetadata, DataHub Query ComponentMapping) with mandatory 120ms inter-call gaps. For a dependency tree of N components:

- **Minimum API calls:** 2N (reference + metadata)
- **DataHub calls:** N (one mapping check per component)
- **Minimum wall time:** N * (2 * 120ms + HTTP latency) ~ N * 0.5s conservatively

A moderately complex process with 50 dependencies would take ~25 seconds minimum. A large orchestration with 200+ components would exceed 100 seconds, risking Flow Service timeout. The build guide (`09-process-b-resolve-dependencies.md:117`) mentions sorting is "optional" at this stage, but the main issue is the serial traversal itself.

**Impact:** Process B will timeout for large dependency trees; no pagination, batching, or parallelism is possible within Boomi's single-threaded process execution model.

**Recommendation:**
- Document a hard component limit (e.g., max 100 components per promotion) and enforce it in the BFS loop.
- Consider batching GET ComponentReference calls using query API instead of individual GET calls.
- Add a DPP `maxComponents` with a configurable ceiling and an error code `COMPONENT_LIMIT_EXCEEDED`.

---

### C3. Process D — Missing `promotionId` in Request Profile

**Files:** `integration/profiles/packageAndDeploy-request.json`, `docs/build-guide/11-process-d-package-and-deploy.md:16`

The build guide specifies `promotionId` as a required request field for PromotionLog updates (step 2, DPP initialization table). However, the request profile JSON (`packageAndDeploy-request.json`) does not include a `promotionId` field. Without it, Process D cannot update the PromotionLog record created by Process C, severing the audit trail between promotion and deployment.

**Impact:** PromotionLog records will remain in `COMPLETED` status forever — never transitioning to `DEPLOYED` or `TEST_DEPLOYED`. The entire approval workflow and status tracking break down.

**Recommendation:** Add `"promotionId": "string"` to `packageAndDeploy-request.json`. This is likely a spec omission since the build guide clearly requires it.

---

## MAJOR

### M1. Profile-to-Build-Guide Field Mismatches Across Multiple Actions

**Files:** Multiple profile JSONs vs. build guide docs vs. flow-service-spec.md

Several profiles have structural differences from what the build guide and flow-service-spec describe:

| Action | Discrepancy | Build Guide | Profile JSON |
|--------|------------|-------------|--------------|
| `queryStatus` | Request field name | `status` (build guide:15) | `status` + extra `reviewStage` field (profile) |
| `queryStatus` | Response fields | 13 fields (build guide:47) | 13 fields + `peerReviewStatus/By/At/Comments` + `adminReviewStatus/By/At/Comments` + `prodPackageId` (profile) |
| `resolveDependencies` | Request field name | `componentId` (build guide:14) | `componentId` (matches, but flow-service-spec:101 says `rootComponentId`) |
| `getDevAccounts` | Response fields | `accounts` array only (build guide:17) | `accounts` array + `effectiveTier` (profile) |
| `manageMappings` | Request field name | `operation` with values `list/create/update` (build guide:19) | `operation` (matches, but flow-service-spec:303 says `action` with `query/update/delete`) |
| `generateComponentDiff` | Request field | `primaryAccountId` required (build guide G:16) | Not in profile (profile uses `branchId`, `prodComponentId`, `componentName`, `componentAction` only) |
| `listIntegrationPacks` | Request field | `primaryAccountId` required (build guide J:17) | Not in profile (profile has `suggestForProcess`, `packPurpose` only) |

**Impact:** Implementers will get conflicting instructions depending on which document they reference. The profile JSONs and build guide must be the single source of truth, and currently they diverge.

**Recommendation:** Reconcile all three documents (profiles, build guide, flow-service-spec) for every action. The `primaryAccountId` omission from generateComponentDiff and listIntegrationPacks profiles is by design (it comes from FSS configuration, not the request), but this should be explicitly stated.

---

### M2. Process E2 and E3 — No Dedicated Build Guide Files

**Files:** `docs/build-guide/index.md:16-17`, `docs/build-guide/07-process-e-status-and-review.md`

The build guide index lists Process E2 (queryPeerReviewQueue) and E3 (submitPeerReview) as part of the build order checklist in `13-process-g-component-diff.md:114-115`, but there are no dedicated build guide files with shape-by-shape instructions. File `07-process-e-status-and-review.md` only covers Process E. The flow-service-spec and profiles for E2/E3 exist, but without canvas-level build instructions, these processes are the least specified in the entire system.

**Impact:** Builder must reverse-engineer Process E2 and E3 from the profiles and flow-service-spec alone, with no guidance on DataHub query construction, self-review prevention implementation, or state validation logic. This is especially problematic for E3, which has complex validation (self-review check, state validation, dual status field updates).

**Recommendation:** Create dedicated build guide files for E2 and E3 following the same shape-by-shape pattern as other processes.

---

### M3. Orphaned Branch Risk on Peer/Admin Rejection

**Files:** `docs/architecture.md:302-307`, `docs/build-guide/16-flow-dashboard-review-admin.md:33-37`

The architecture doc states "REJECT: DELETE (peer)" and "DENY: DELETE (admin)" but neither the build guide for the Flow dashboard (Page 6 rejection, Page 7 denial) nor Process E3 includes branch deletion logic. The `submitPeerReview` action in the flow-service-spec updates `peerReviewStatus` to `PEER_REJECTED` but does not call `DELETE /Branch/{branchId}`.

- Page 6 rejection (`16-flow-dashboard-review-admin.md:36`): calls `submitPeerReview` with `decision=REJECTED`, then "End flow". No branch cleanup step.
- Page 7 denial (`16-flow-dashboard-review-admin.md:62`): "Update promotion status to ADMIN_REJECTED... refresh the queue". No branch cleanup step.

**Impact:** Every rejected/denied promotion leaks a branch. With the 20-branch Boomi limit (effective threshold 15 per Process C:79), this can exhaust branch capacity quickly in an active team.

**Recommendation:** Branch deletion must be triggered on rejection/denial. Options:
1. Add a `DELETE /Branch/{branchId}` call to Process E3 when `decision=REJECTED`, and add an admin denial process that also deletes the branch.
2. Or add a Flow message step after submitPeerReview rejection that calls a separate branch cleanup action.
3. Alternatively, update PromotionLog `branchId` to null after deletion for audit completeness.

---

### M4. `componentMappingCache` DPP Size Limit Risk

**Files:** `docs/build-guide/10-process-c-execute-promotion.md:271-287`, `docs/build-guide/20-appendix-dpp-catalog.md:28`

The `componentMappingCache` is stored as a JSON string in a Dynamic Process Property. Each entry adds ~85 bytes (two GUIDs + JSON syntax). For 200 components, the cache would be ~17KB. Boomi DPP size limits vary by atom type but typically cap around 100KB for public cloud atoms. The cache is read and re-serialized on every loop iteration (steps 12, 16), and `rewrite-references.groovy` also reads it.

For very large promotions or accumulated mappings over many promotion runs, the `connectionMappingCache` (step 5.5) could also grow large if a dev account has hundreds of connection mappings.

**Impact:** Silent truncation or process failure when DPP size limits are exceeded, with no graceful error handling.

**Recommendation:** Add a size check before `setDynamicProcessProperty` calls, and document the practical limit. Consider using Document Properties or an accumulating document instead of DPPs for large caches.

---

### M5. Process A — N+1 API Call Pattern for Package Enrichment

**Files:** `docs/build-guide/08-process-a-list-dev-packages.md:51-58`

Step 6 makes a separate `GET ComponentMetadata` API call for every PackagedComponent to enrich it with `componentName` and `componentType`. This is an N+1 query pattern. A dev account with 50 packages requires 50+ additional API calls (plus pagination calls), each with a 120ms gap.

**Minimum enrichment time for 50 packages:** 50 * 120ms = 6 seconds of mandatory sleep alone, plus HTTP round trips.

**Impact:** Slow response times for dev accounts with many packages. Combined with pagination calls, `listDevPackages` for a busy dev account could take 30+ seconds.

**Recommendation:** Investigate if the PackagedComponent query response already includes component metadata (some Boomi API endpoints return partial metadata inline). If not, consider using a `QUERY Component` API call with a filter to batch-fetch metadata for multiple component IDs.

---

### M6. `strip-env-config.groovy` — Overly Broad Element Matching

**Files:** `integration/scripts/strip-env-config.groovy:21-57`

The script strips ALL elements named `password`, `host`, `url`, `port`, and `EncryptedValue` regardless of their position in the XML tree. Boomi component XML may contain legitimate non-sensitive uses of these element names (e.g., a Map component that transforms data containing a `<url>` field, or a profile element named `host`).

The `depthFirst().findAll { it.name() == 'password' }` pattern matches any element at any depth with that local name, including inside profile definitions, map function configurations, or process property definitions.

**Impact:** Data corruption — legitimate component configuration elements could be emptied, causing promoted components to malfunction in production.

**Recommendation:** Scope the stripping to known sensitive paths within Boomi component XML. For example, only strip `password` elements that are direct children of connection configuration elements. The fix requires understanding Boomi's component XML schema structure and using path-based matching instead of name-based matching.

---

### M7. `rewrite-references.groovy` — Blind String Replacement Risk

**Files:** `integration/scripts/rewrite-references.groovy:27-33`

The script performs `xmlContent.replaceAll(Pattern.quote(devId), prodId)` across the entire XML content. While component IDs are GUIDs (low collision probability), this global string replacement operates on raw XML text, not on parsed XML structure. This means:

1. If a GUID appears in a CDATA section, comment, or text content (not as a reference), it will still be rewritten.
2. If a dev component ID appears as a substring of a larger string (unlikely for GUIDs but possible), partial matches could occur.
3. The replacement does not distinguish between `componentId` attribute values and other GUID-shaped values (e.g., execution IDs, tracking IDs).

**Impact:** Low probability but high severity — incorrect rewrites would create silent reference errors in promoted components.

**Recommendation:** Consider parsing the XML and only rewriting known reference fields (`componentId`, `overriddenComponentId`, `connectorComponentId`, etc.) instead of global string replacement. At minimum, add logging of the XML context around each replacement for post-promotion audit.

---

## MINOR

### m1. Inconsistent DPP Persistence Flags

**Files:** `docs/build-guide/10-process-c-execute-promotion.md:67-69`, `docs/build-guide/20-appendix-dpp-catalog.md`

Process C generates `promotionId` with `ExecutionUtil.setDynamicProcessProperty("promotionId", promotionId, false)` (non-persistent, step 3). However, the PromotionLog DataHub update at step 4 reads this DPP. The DPP catalog (`20-appendix-dpp-catalog.md`) does not specify persistence flags for any DPP. Per the Groovy standards rule (`groovy-standards.md`), the default should be `false` for most DPPs, and `true` only for values that "MUST survive process execution." Since all DPPs in Process C are consumed within the same execution, `false` is correct — but the catalog should document this explicitly to prevent future confusion.

---

### m2. Process J — Missing `primaryAccountId` in Request but Required in Build Guide

**Files:** `docs/build-guide/12-process-j-list-integration-packs.md:17`, `integration/profiles/listIntegrationPacks-request.json`

The build guide says the request contains `primaryAccountId` (string, required), but the profile JSON only has `suggestForProcess` and `packPurpose`. The `primaryAccountId` comes from the Flow Service configuration value, not the request. The build guide description is misleading — it implies the caller must provide this value.

**Recommendation:** Update the build guide to clarify that `primaryAccountId` comes from the FSS configuration, not the request payload.

---

### m3. Process G — `primaryAccountId` Similarly Missing from Profile

**Files:** `docs/build-guide/13-process-g-component-diff.md:16`, `integration/profiles/generateComponentDiff-request.json`

Same issue as m2. The build guide says `primaryAccountId` is in the request, but the profile JSON does not include it. The FSS configuration pattern is consistent but undocumented.

---

### m4. `sort-by-dependency.groovy` — Default Priority Placement

**Files:** `integration/scripts/sort-by-dependency.groovy:17`

Unknown component types default to priority 3 (same as `operation`). If a Boomi component type not covered by the priority map (e.g., `crossreference`, `certificate`, `processroute`) is encountered, it will be sorted with operations. This could place it before maps and processes that reference it, but after profiles and connections.

**Recommendation:** Either enumerate all known Boomi component types or default to priority 5 (after maps, before processes) to be safe. Log a warning for unrecognized types.

---

### m5. `build-visited-set.groovy` — O(n) List Lookups Instead of Set

**Files:** `integration/scripts/build-visited-set.groovy:17-33`

The `visitedSet` is stored as a JSON array (list) and uses `visitedSet.contains(currentId)` which is O(n) per check. Over a BFS with N nodes, this yields O(N^2) containment checks. Similarly, `queue.contains(childId)` at line 50 is O(n).

For small trees (< 50 components) this is negligible, but for larger trees it compounds with the already slow API-per-node pattern (see C2).

**Recommendation:** Convert to a HashSet in-memory for visited checks. The serialization to JSON array for DPP storage is fine, but in-memory operations should use O(1) lookups.

---

### m6. No Rate-Limit Retry Logic Documented for DataHub Operations

**Files:** `docs/architecture.md:215`, `docs/build-guide/10-process-c-execute-promotion.md:100`

The architecture doc mentions "Retry on 429/503: up to 3 retries with exponential backoff" but this is only documented for Platform API calls. DataHub connector operations (which are used extensively in Processes B, C, E, E2, E3, F) have no retry guidance in any build guide file. If DataHub returns transient errors under load, all DataHub-dependent processes will fail without retry.

---

### m7. `validate-connection-mappings.groovy` — Uses `new Properties()` Instead of Original

**Files:** `integration/scripts/validate-connection-mappings.groovy:73-74`

The script's final `dataContext.storeStream()` uses `new Properties()` instead of `dataContext.getProperties(0)`. This discards any document properties (tracking IDs, correlation data) that were attached to the input document. While unlikely to cause issues in the current flow (the output feeds directly into the promotion loop), it breaks the chain of document metadata.

---

## OBSERVATIONS

### O1. Elegant Bottom-Up Sort + Mapping Cache Design

The interplay between `sort-by-dependency.groovy` (Process C step 5) and the progressive `componentMappingCache` accumulation (step 16) is well-designed. By promoting dependencies first, the cache naturally contains all needed mappings when higher-level components are processed. The separation of connection validation (step 5.5-5.7) as a batch pre-check before the main loop is a good fail-fast pattern.

### O2. Branch Lifecycle Is Well-Defined

The branch lifecycle (CREATE -> POLL -> PROMOTE -> REVIEW -> TERMINAL) with mandatory deletion on all terminal paths (approve, reject, deny, error) is a clean state machine. The `branchId` tracking in PromotionLog with null-on-cleanup provides good auditability. The outer Try/Catch with branch cleanup in Process C (step 100) is a solid defensive pattern.

### O3. Connection Non-Promotion Is a Good Architectural Decision

Excluding connections from promotion and requiring admin-seeded mappings is the right call. Connections contain environment-specific credentials, and the `#Connections` folder convention with shared mappings across dev accounts is clean separation of concerns. The `validate-connection-mappings.groovy` pre-check with "report ALL missing, don't stop on first" is user-friendly.

### O4. Flow Service Async Behavior Leverages Boomi Platform Well

Using Boomi's built-in async callback mechanism for long-running operations (documented in flow-service-spec.md:604-630) avoids custom polling infrastructure. The documented typical durations are realistic for the API call patterns described.

### O5. Data Flow Between Processes Is Clean but Implicit

Process C outputs `branchId` and `promotionId`, which Process D and G consume. Process B outputs `components` array, which Process C consumes. This data flow is well-designed but entirely mediated through the Flow dashboard (each process is invoked independently via message actions). There's no direct process-to-process coupling, which is good for modularity but means the Flow layer is the sole orchestrator.

---

## MULTI-ENVIRONMENT ASSESSMENT

### Overall Integration Quality: Good with Gaps

Phase 7 (`22-phase7-multi-environment.md`) integrates cleanly with the existing architecture in concept but has implementation gaps:

**Strengths:**
1. The 3-mode Decision shape on `deploymentTarget` in Process D is a clean branching pattern.
2. Branch preservation for TEST deployments (merge to main but keep branch for diff) is smart — it avoids re-promotion while enabling production review.
3. The `testPromotionId` linkage between TEST and PRODUCTION PromotionLog records provides good traceability.
4. Pack naming convention ("- TEST" suffix) with `packPurpose` filter is pragmatic.

**Gaps:**

1. **Profile fields present but build guide incomplete:** The `packageAndDeploy-request.json` includes `deploymentTarget`, `isHotfix`, `hotfixJustification`, `testPromotionId`, `testIntegrationPackId`, and `testIntegrationPackName` — but the Process D build guide (`11-process-d-package-and-deploy.md`) does not reference these fields in its Set Properties step (step 2). The Phase 7 doc (`22-phase7-multi-environment.md:81-106`) describes the 3 modes but does not provide shape-by-shape canvas instructions for the Decision shape and mode-specific branches.

2. **Process E4 has no build guide:** Step 7.2 describes Process E4 (Query Test Deployments) at a high level but does not provide shape-by-shape instructions. The profiles exist (`queryTestDeployments-request.json`, `queryTestDeployments-response.json`) but the "exclude promotions that have a matching PRODUCTION record" logic is complex (requires a secondary DataHub query or join) and is not detailed.

3. **Branch age enforcement is UI-only:** Page 9's stale branch warning (30-day threshold) is a display concern, not a backend enforcement. There's no backend process to reap stale branches or escalate. If users ignore the warning, branches accumulate.

4. **TEST-to-PRODUCTION transition has no validation of test success:** Mode 2 (PRODUCTION from test) assumes the test deployment was successful based solely on `status=TEST_DEPLOYED`. There's no mechanism to verify actual test results, validate that the test environment is healthy, or confirm that the deployed test package functions correctly. The transition relies entirely on human judgment.

5. **Hotfix justification is validated client-side only:** The Phase 7 doc describes a required textarea for hotfix justification on Page 3 (`22-phase7-multi-environment.md:167`), but Process D's build guide does not include a server-side validation that `hotfixJustification` is non-empty when `isHotfix=true`. The flow-service-spec includes `HOTFIX_JUSTIFICATION_REQUIRED` as an error code, but no process implements this check.

---

## SUMMARY TABLE

| Severity | ID | Title |
|----------|----|-------|
| CRITICAL | C1 | No concurrency guard — parallel promotions corrupt shared state |
| CRITICAL | C2 | Process B BFS scalability — unbounded queue with O(n) API calls |
| CRITICAL | C3 | Process D missing `promotionId` in request profile |
| MAJOR | M1 | Profile-to-build-guide field mismatches across multiple actions |
| MAJOR | M2 | Process E2 and E3 have no dedicated build guide files |
| MAJOR | M3 | Orphaned branch risk on peer/admin rejection |
| MAJOR | M4 | `componentMappingCache` DPP size limit risk |
| MAJOR | M5 | Process A — N+1 API call pattern for package enrichment |
| MAJOR | M6 | `strip-env-config.groovy` overly broad element matching |
| MAJOR | M7 | `rewrite-references.groovy` blind string replacement risk |
| MINOR | m1 | Inconsistent DPP persistence flags documentation |
| MINOR | m2 | Process J missing `primaryAccountId` clarification |
| MINOR | m3 | Process G missing `primaryAccountId` clarification |
| MINOR | m4 | `sort-by-dependency.groovy` default priority placement |
| MINOR | m5 | `build-visited-set.groovy` O(n) list lookups instead of set |
| MINOR | m6 | No retry logic documented for DataHub operations |
| MINOR | m7 | `validate-connection-mappings.groovy` discards document properties |

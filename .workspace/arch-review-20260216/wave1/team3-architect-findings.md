# Team 3 - API Design Architect Findings

**Reviewer Role:** API Design Architect (general API design and distributed systems perspective)
**Date:** 2026-02-16
**Files Reviewed:**
- All 16 files in `integration/api-requests/`
- `docs/architecture.md`
- `integration/flow-service/flow-service-spec.md`
- `docs/build-guide/02-http-client-setup.md`
- `docs/build-guide/21-appendix-platform-api-reference.md`
- `docs/build-guide/10-process-c-execute-promotion.md`
- `docs/build-guide/11-process-d-package-and-deploy.md`
- `integration/profiles/manageMappings-request.json`
- `integration/profiles/manageMappings-response.json`

---

## Critical Findings

### C1. Branch Limit Threshold Inconsistency Across Documentation

The soft-limit threshold for branch count is inconsistent across the specification:

| Location | Threshold |
|----------|-----------|
| `docs/architecture.md:104` | `>= 15` |
| `docs/architecture.md:189` | `>= 15` |
| `docs/architecture.md:284` | "lowered from 18 to 15" |
| `docs/build-guide/10-process-c-execute-promotion.md:79` | `>= 15` |
| `integration/api-requests/query-branch.json:6` | `>= 15` |
| `integration/api-requests/create-branch.json:25` | `threshold: 15` |
| `docs/build-guide/02-http-client-setup.md:307` | references "10-branch limit" |
| `.claude/skills/boomi-platform-api/SKILL.md:259` | `>= 18` |
| `.claude/skills/boomi-platform-api/reference/branch-operations.md:398` | `>= 18` |
| `.claude/skills/boomi-platform-api/reference/error-handling.md:363` | `>= 18` |
| `.claude/skills/boomi-promotion-lifecycle/SKILL.md:97` | `>= 18` |
| `.claude/skills/boomi-promotion-lifecycle/reference/branching-merging.md:314` | `>= 18` |
| `.claude/skills/boomi-promotion-lifecycle/examples/promotion-workflow.md:86` | `< 18` |

**Impact:** The core specification (architecture.md, build guide, api-requests) has converged on `>= 15` after the multi-environment update lowered it from 18. However, multiple skill/reference files still reference the old `>= 18` threshold. Build guide step 2.2.11 at line 307 even references a "10-branch limit" which is a third value entirely.

**Recommendation:** Conduct a systematic sweep of all files referencing branch thresholds and normalize to `>= 15`. The "10-branch limit" in `docs/build-guide/02-http-client-setup.md:307` appears to be a drafting error and must be corrected.

### C2. Missing API Templates and HTTP Operations for Integration Pack Lifecycle

Process D references three API operations that have no template files and no HTTP Operation definitions in the build guide's operations table (`docs/build-guide/02-http-client-setup.md:36-53`):

1. **AddToIntegrationPack** (add PackagedComponent to an Integration Pack)
   - Referenced at `docs/build-guide/11-process-d-package-and-deploy.md:103,108`
   - No template in `integration/api-requests/`
   - No HTTP Operation in the 15-operation table

2. **ReleaseIntegrationPack** (release a pack for deployment)
   - Referenced at `docs/build-guide/11-process-d-package-and-deploy.md:111-116`
   - Also referenced at `integration/api-requests/create-integration-pack.json:6`
   - No template in `integration/api-requests/`
   - No HTTP Operation in the 15-operation table
   - **Naming inconsistency:** `docs/build-guide/11-process-d-package-and-deploy.md:114` uses `IntegrationPackRelease` while all other references use `ReleaseIntegrationPack`

3. **GET MergeRequest** (poll merge status)
   - Referenced at `docs/build-guide/11-process-d-package-and-deploy.md:75`
   - `execute-merge-request.json:6` says "Poll GET /MergeRequest/{mergeRequestId} until stage=MERGED"
   - No template in `integration/api-requests/`
   - No HTTP Operation in the 15-operation table

**Impact:** A builder following the specification cannot implement Process D without discovering these API endpoints independently. The 15-operation table in Step 2.2 is incomplete; it should contain at least 18 operations.

**Recommendation:** Create template files for all three missing operations. Add HTTP Operations 16-18 to the build guide table. Standardize the endpoint name to `ReleaseIntegrationPack` (matching the Boomi Platform API).

### C3. MergeRequest Template Field Name Mismatch with Build Guide

The `create-merge-request.json` template uses `"source"` as the field name for the source branch:

```json
// integration/api-requests/create-merge-request.json:11-12
"source": "{branchId}",
"strategy": "OVERRIDE",
```

But the build guide step 2.2.12 description says:

> `docs/build-guide/02-http-client-setup.md:350`: "Request body requires `sourceBranchId` and `targetBranchId` (usually main)."

These field names (`source` vs `sourceBranchId`, missing `target`/`targetBranchId`) are contradictory. The actual template has no `target` or `targetBranchId` field at all -- the Boomi API apparently defaults to merging into main when no target is specified, but this is undocumented in the template.

**Impact:** A builder following step 2.2.12 would construct a request body with `sourceBranchId` and `targetBranchId` fields, which would fail against the actual API. The template is likely correct (using `source`), but the build guide prose contradicts it.

**Recommendation:** Update `docs/build-guide/02-http-client-setup.md:350` to match the actual template: "Request body requires `source` (branch ID), `strategy` (OVERRIDE), and `priorityBranch` (same branch ID). Target defaults to main."

---

## Major Findings

### M1. manageMappings Field Name Discrepancy: `action` vs `operation`

The flow-service-spec defines the request field as `action`:

> `integration/flow-service/flow-service-spec.md:303`: `action` (string: "query" | "update" | "delete")

But the actual JSON profile uses `operation`:

> `integration/profiles/manageMappings-request.json:2`: `"operation": "string"`

Additionally, the Connection Seeding Workflow section references a `"create"` value:

> `integration/flow-service/flow-service-spec.md:300`: `operation = "create"` to seed ComponentMapping records

But the flow-service-spec's enum only allows `"query" | "update" | "delete"` -- no `"create"` value.

**Impact:** The profile (which is what Boomi actually uses) says `operation`, the spec says `action`, and the workflow text references a value (`create`) not in either's enum. This is a three-way inconsistency that will cause implementation confusion and runtime failures.

**Recommendation:** Standardize on `operation` (matching the profile) with values `"query" | "create" | "update" | "delete"`. Update the flow-service-spec field name and enum to match.

### M2. Concurrency Lock Mechanism Underdefined

`docs/architecture.md:216` states:

> "Concurrency lock via PromotionLog IN_PROGRESS check"

But nowhere in the specification is this lock mechanism defined in detail:

- **When is the lock checked?** Process C creates the PromotionLog with IN_PROGRESS status at step 4 (`docs/build-guide/10-process-c-execute-promotion.md:102`), but there is no preceding step that queries for existing IN_PROGRESS records.
- **What scope is the lock?** Per dev-account? Per component? Global?
- **What error code is returned?** No error code like `PROMOTION_IN_PROGRESS` or `CONCURRENT_PROMOTION` exists in the error contract (`integration/flow-service/flow-service-spec.md:656-678`).
- **TOCTOU vulnerability:** Even if a check existed, a Time-Of-Check-Time-Of-Use race condition is inherent -- two concurrent Process C invocations could both check, find no IN_PROGRESS, and both create IN_PROGRESS records.

**Impact:** Without a defined lock mechanism, two users could initiate concurrent promotions that write to the same branch or create conflicting branches. DataHub's match-rule UPSERT provides some protection against duplicate PromotionLog records, but cannot prevent concurrent branch-level conflicts.

**Recommendation:** Either (a) implement a proper advisory lock via DataHub (e.g., check for IN_PROGRESS records for the same devAccountId before creating a new one, with a defined error code), or (b) acknowledge that the system relies on the natural serialization of the Flow Service (single-threaded per listener) and document this assumption explicitly. Option (b) may be sufficient for typical Boomi Cloud Atom deployments but should be stated as a design constraint.

### M3. Merge Failure Recovery Path Lacks Polling Details

The merge lifecycle has a two-step pattern: create MergeRequest, then execute it. The execute step says:

> `docs/build-guide/11-process-d-package-and-deploy.md:75`: "poll `GET /MergeRequest/{mergeRequestId}` until `stage = MERGED`"

But no details are specified for:

1. **Polling interval** -- how long between polls?
2. **Maximum retries** -- how many polls before declaring failure?
3. **Intermediate stages** -- what stages exist between creation and MERGED? What about MERGING, FAILED, etc.?
4. **Failure recovery** -- `docs/build-guide/11-process-d-package-and-deploy.md:76` says "On merge failure: error with `errorCode = "MERGE_FAILED"`, attempt `DELETE /Branch/{branchId}`, return error" but what constitutes a "merge failure" when using OVERRIDE strategy?

The branch readiness polling in Process C has a clear specification (5-second delay, max 6 retries -- `docs/build-guide/10-process-c-execute-promotion.md:95`), but the merge polling has none.

**Impact:** Without defined polling parameters, implementers may use arbitrary values leading to timeout issues or excessive API calls. The MERGE_FAILED error code is referenced in the build guide but not in the error contract table (`integration/flow-service/flow-service-spec.md:656-678`).

**Recommendation:** Define merge polling parameters (suggested: 5-second delay, max 12 retries = 60 seconds). Add `MERGE_FAILED` and `MERGE_TIMEOUT` to the error contract table. Document expected intermediate MergeRequest stages from the Boomi API.

### M4. No QUERY IntegrationPack Template in API Reference Appendix

The Platform API Quick Reference (`docs/build-guide/21-appendix-platform-api-reference.md:18-28`) lists 9 endpoints but omits:

- QUERY IntegrationPack (`integration/api-requests/query-integration-packs.xml`)
- All branch operations (create, query, get, delete)
- MergeRequest operations (create, execute)
- ReleaseIntegrationPack
- AddToIntegrationPack

The appendix was likely written before the branching features were added but was never updated.

**Impact:** The appendix is incomplete and misleading for reference use. A builder relying on it would miss 7+ critical endpoints.

**Recommendation:** Update the appendix to include all 18+ endpoints used by the system, or add a note directing readers to the complete list in Step 2.2.

---

## Minor Findings

### m1. XML vs JSON Content-Type Boundary Not Cleanly Documented

Operations 1-6 use `application/xml`, operations 7-9 use `application/json`, but operations 10-15 (branch/merge) use `application/json`. The build guide notes at `docs/build-guide/02-http-client-setup.md:55` state:

> "Operations 1-6 use `application/xml` for both Content-Type and Accept headers. Operations 7-9 use `application/json`."

This note stops at operation 9 and doesn't mention operations 10-15. Operations 10-15 also use JSON, creating an implicit but unstated grouping.

**Recommendation:** Update the note to: "Operations 1-6 use `application/xml`. Operations 7-15 use `application/json`."

### m2. create-deployed-package.json Uses Non-Standard Field for Package Reference

The `create-deployed-package.json` template at line 10 uses `"packageId"` to reference what is described as a "released package ID from ReleaseIntegrationPack response":

```json
"packageId": "{releasedPackageId}"
```

But earlier in the flow, `packageId` refers to the PackagedComponent ID (e.g., in `create-packaged-component.json`). The same field name is overloaded to mean different things in different contexts.

**Recommendation:** Add a comment or rename the placeholder to clarify: the DeployedPackage's `packageId` is the released Integration Pack package ID, not the PackagedComponent ID.

### m3. Process E4 (queryTestDeployments) Missing from Build Guide Operations

Process E4 is fully specified in the flow-service-spec (`integration/flow-service/flow-service-spec.md:447-480`) and in the architecture (`docs/architecture.md:182`), but I did not find a dedicated build guide step for Process E4. The multi-environment build guide phase (`docs/build-guide/22-phase7-multi-environment.md`) may cover it, but it should be verified.

**Recommendation:** Ensure Process E4 has a complete build guide step, or verify that Phase 7 covers it sufficiently.

### m4. Retry Strategy Gaps for Branch Operations

The retry strategy is defined for API rate limits (429/503): "up to 3 retries with exponential backoff" at `docs/architecture.md:215`. The delete-branch template explicitly lists error codes 429 and 503 (`integration/api-requests/delete-branch.json:22`). However, the create-branch and query-branch templates do not list explicit error/retry codes, relying on the general error handling contract.

**Recommendation:** For consistency, add `errorCodes` or `retryableCodes` annotations to all API templates, not just delete-branch.

### m5. QUERY Branch Uses Empty Filter -- Returns All Branches Including Non-Promotion

The branch query (`integration/api-requests/query-branch.json:33-38`) uses an empty QueryFilter to return ALL branches in the account. This includes branches created by other users or tools (not just `promo-*` branches).

The threshold check (`>= 15`) counts ALL branches, not just promotion branches. This means non-promotion branches created through the Boomi UI or other tools reduce the available slots for promotions.

**Recommendation:** This is likely intentional (the hard limit is account-wide regardless of branch source), but document this explicitly. Consider adding a comment to the template: "Counts ALL branches, not just promotion branches -- this is correct because the hard limit is account-wide."

---

## Observations

### O1. Strong API Template Consistency

The API templates in `integration/api-requests/` follow a consistent pattern: XML comment header with full HTTP details, then a sample request/response body. The `_comment`, `_notes`, `_http_operation`, and `_response_structure` metadata conventions in JSON templates are well-designed and provide self-documentation. This is good API design practice.

### O2. Tilde Syntax Well-Documented

The tilde syntax (`Component/{id}~{branchId}`) for branch-scoped operations is consistently documented across templates, build guide, and architecture docs. The distinction between create (`Component~{branchId}`) and update (`Component/{id}~{branchId}`) is clear.

### O3. Idempotent DELETE Branch Design

The DELETE Branch operation treating both 200 and 404 as success (`integration/api-requests/delete-branch.json:21`) is excellent distributed systems practice. This ensures cleanup paths are safe to retry without error handling complexity.

### O4. Error Contract is Comprehensive

The flow-service-spec defines 18 error codes (`integration/flow-service/flow-service-spec.md:656-678`) covering authentication, rate limits, business logic failures, and workflow state violations. Each has a user action description. This is a well-structured error taxonomy. The only gap is the missing `MERGE_FAILED` and `MERGE_TIMEOUT` codes noted in M3.

### O5. Rate Limiting Strategy is Conservative and Appropriate

The 120ms gap between API calls (~8 req/s against a ~10 req/s limit) with exponential backoff retry on 429/503 (`docs/build-guide/21-appendix-platform-api-reference.md:34-37`) provides a 20% safety margin. This is a reasonable approach for a system that operates within a single API token's rate limit scope.

---

## Multi-Environment Assessment

The multi-environment deployment model (added in v0.6.0) introduces significant branch lifecycle complexity:

### Strengths
- Three clear deployment paths (test, production-from-test, hotfix) with well-defined branch lifecycle behavior
- Branch preservation for test deployments enables production-phase diffing without re-promotion
- Skip-merge optimization for production-from-test avoids redundant operations
- Hotfix audit trail (`isHotfix`, `hotfixJustification`) provides compliance-friendly tracking

### Concerns
1. **Branch slot pressure:** Test deployments preserve branches for days/weeks. With a 15-branch soft limit and 20-branch hard limit, only 15 concurrent test deployments can exist before blocking all new promotions. For organizations with multiple dev teams, this could become a bottleneck.

2. **Branch age monitoring is UI-only:** The 30-day branch warning is surfaced in the Flow UI (Page 9) but there is no automated cleanup or notification mechanism for stale test branches. An admin who doesn't check Page 9 regularly may not notice branch accumulation.

3. **Test-to-production state transition:** The `testPromotionId` linkage between TEST_DEPLOYED and PRODUCTION records relies on correct state management across multiple processes and user sessions. If the user's Flow state is lost between test deployment and production promotion, the `testPromotionId` may need to be recovered from DataHub.

---

## Summary

| Severity | Count | Key Themes |
|----------|-------|------------|
| Critical | 3 | Branch limit inconsistency, missing API templates, MergeRequest field mismatch |
| Major | 4 | manageMappings field name conflict, underdefined concurrency lock, merge polling gaps, incomplete API reference |
| Minor | 5 | Content-Type grouping, packageId overloading, Process E4 build guide, retry annotations, empty branch filter |
| Observations | 5 | Strong template consistency, tilde syntax, idempotent delete, comprehensive errors, conservative rate limiting |

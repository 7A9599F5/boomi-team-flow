# Team 3: Devil's Advocate Response — Platform API & API Design

**Reviewer Role**: Devil's Advocate (challenging/confirming expert and architect findings)
**Date**: 2026-02-16
**Findings Reviewed**:
- `team3-expert-findings.md` (Platform API Expert): 2 Critical, 7 Major, 6 Minor
- `team3-architect-findings.md` (API Design Architect): 3 Critical, 4 Major, 5 Minor

---

## Challenges to Expert Findings

### Challenge to Expert C1 (MergeRequest `source` vs `sourceBranchId`) — CONFIRMED CRITICAL

The expert identifies `"source"` in the template as incorrect, claiming the API uses `"sourceBranchId"`. The architect (C3) makes the opposite claim — that the template's `"source"` is "likely correct" and the build guide prose is wrong.

**Verdict**: Both reviewers agree there is a mismatch, but they disagree on which is correct. The research documents consistently use `sourceBranchId` (platform-api-research.md:713, gap-analysis-research.md:310, branch-operations.md:228). However, neither reviewer has verified this against the live Boomi API. This must be tested against a real Boomi environment before fixing.

**Confirmed**: This is a Critical issue regardless of which field name is correct — the template and build guide contradict each other. Severity: **CRITICAL**.

### Challenge to Expert C2 (Branch Limit Inconsistency) — CONFIRMED CRITICAL, MERGE WITH ARCHITECT C1

Both expert C2 and architect C1 identify the same issue with slightly different evidence tables. Merging for the consensus:

- The "10-branch limit" in `docs/build-guide/02-http-client-setup.md:307` is clearly a drafting error (no other document uses 10).
- The skills files using 18 are stale after the multi-environment update lowered it to 15.
- The architecture.md and Process C build guide have converged on 15.
- The create-branch.json says both "20 per account" (hard limit) and "threshold: 15" (soft limit) — these are not contradictory but should be stated more clearly.

**Confirmed**: **CRITICAL**. Standardize on 15 for the soft limit, 20 for the hard limit. Update skills files during next skills refresh.

### Challenge to Expert M1 (Naming Inventory Missing 3 Operations) — CONFIRMED, BUT DOWNGRADE TO MINOR

The naming inventory at `19-appendix-naming-and-inventory.md:39` lists "Phase 2 -- HTTP Client Operations (12)" which was written before operations 13-15 (MergeRequest Execute, GET Branch, DELETE Branch) were added. While the inventory is incomplete, it is an appendix checklist, not the authoritative definition. The authoritative list is the build guide Step 2.2 table which correctly lists all 15.

**Verdict**: The inventory should be updated for consistency, but this is a documentation drift issue, not a functional gap. Downgrade from **Major** to **Minor**.

### Challenge to Expert M2 (Missing QUERY IntegrationPack and ReleaseIntegrationPack Operations) — CONFIRMED MAJOR

The expert correctly identifies that Process J references `PROMO - HTTP Op - QUERY IntegrationPack` which has no build step. The architect's C2 finding provides additional context: `ReleaseIntegrationPack` and `AddToIntegrationPack` are also missing.

**However**, I challenge the scope: the build guide Step 2.2 says "Create 15 HTTP Client operations" and lists exactly 15. The additional operations (QUERY IntegrationPack, ReleaseIntegrationPack, AddToIntegrationPack, GET MergeRequest) were likely deferred to be documented inline within their respective process build guides. Process J's build guide at `docs/build-guide/12-process-j-list-integration-packs.md:7` references the operation by name, implying it should have been created.

**Counter-challenge**: Is there a pattern of operations being defined inline in process build guides rather than centralized? Checking... No. All other operations are defined centrally in Step 2.2. This is simply missing.

**Confirmed**: **MAJOR**. At least 3 operations are missing from the centralized operations list.

### Challenge to Expert M3 (Process G Reuses GET Component With Wrong Parameter Count) — PARTIALLY CHALLENGED

The expert claims GET Component cannot be reused because it has 2 URL parameters but branch reads need 3. However, the build guide at `docs/build-guide/13-process-g-component-diff.md:85` says:

> "The same HTTP Client Operation can be reused — just parameterize the URL with or without tilde"

This suggests the intent is to pass `{componentId}~{branchId}` as a single concatenated `{2}` parameter. In Boomi's HTTP Client operation, URL parameters are string substitutions — if `{2}` is set to `"abc123~branch456"`, the resulting URL would be `/Component/abc123~branch456`, which is valid.

**Verdict**: The expert's concern about parameter count may be invalid if concatenation is used. However, the build guide should be explicit about this concatenation requirement. Downgrade from **Major** to **Minor** if the concatenation approach is validated, but add a recommendation to document it clearly.

**Revised**: **MAJOR** remains because the build guide does not explain the concatenation mechanism. A builder would not know to concatenate without explicit instructions.

### Challenge to Expert M5 (Missing GET MergeRequest Template) — CONFIRMED, MERGE WITH ARCHITECT C2

Both reviewers independently identified this. The architect frames it as part of a broader "missing API templates" problem (C2), while the expert treats it as a standalone finding. Merging: the GET MergeRequest polling operation needs both a template file and an HTTP Client operation definition.

**Confirmed**: **MAJOR**.

### Challenge to Expert M6 (Appendix Missing Branch/Merge Operations) — CONFIRMED, MERGE WITH ARCHITECT M4

Both reviewers identified the incomplete appendix. The architect provides more detail on the full scope of missing endpoints (7+). Merging into a single finding.

**Confirmed**: **MAJOR**.

### Challenge to Expert m4 (DeployedPackage `componentType` Field) — NEEDS VERIFICATION

The expert flags `componentType: "process"` in the DeployedPackage template as potentially incorrect. The Boomi DeployedPackage API documentation should be consulted. The field may be required for the API to understand what type of component is being deployed. Without live API verification, this cannot be confirmed or denied.

**Verdict**: **Inconclusive**. Tag for API validation testing.

### Challenge to Expert m5 (120-Second Timeout) — PARTIALLY DISAGREE

The expert argues 120-second timeouts are excessive. However, in Boomi Cloud environments, API responses can be slow during peak hours or for large operations (e.g., creating a branch involves snapshotting all account components). The 120-second timeout is a safety net, not an expected response time. The polling logic (5-second intervals, 6 retries) already limits total wait time independently of the per-call timeout.

**Verdict**: Keep 120-second timeout as-is. The real protection is the polling retry logic, not the socket timeout. **Downgrade to observation-only**.

### Challenge to Expert m6 (Rate Limiting in Dependency Traversal) — PARTIALLY DISAGREE

The expert estimates 100 API calls for a 50-component dependency tree. However, Process B uses a BFS visited-set (`build-visited-set.groovy`) that prevents re-visiting components. Typical dependency trees are 10-30 components with 2-3 depth levels. A 50-component tree would be unusual.

The 120ms gap is enforced per consecutive call in the Boomi process (via process properties or flow control), not just for pagination. The real concern should be: what if the rate-limited calls cause Process B to exceed the Flow Service's async timeout?

**Verdict**: The rate limiting strategy is adequate for typical use cases. Add a note about very large dependency trees (50+ components) as an edge case that may require chunking. **Keep as Minor**.

---

## Challenges to Architect Findings

### Challenge to Architect C3 (MergeRequest Template Field Name) — MERGE WITH EXPERT C1

Addressed above. The architect and expert disagree on which field name is correct. The research evidence favors `sourceBranchId` but live API testing is required.

### Challenge to Architect M1 (manageMappings `action` vs `operation`) — CONFIRMED MAJOR

This is a clear spec-profile inconsistency that was not caught by the expert (who focused on Platform API rather than Flow Service contracts). The three-way mismatch (`action` in spec, `operation` in profile, `create` value missing from enum) is well-documented.

**Confirmed**: **MAJOR**.

### Challenge to Architect M2 (Concurrency Lock Underdefined) — CONFIRMED MAJOR, WITH NUANCE

The architect correctly identifies that the "concurrency lock via PromotionLog IN_PROGRESS check" is referenced but never implemented. However, I note that:

1. Each promotion creates a unique branch (`promo-{promotionId}`), so concurrent promotions would not write to the same branch.
2. The real risk is concurrent promotions for the same component — one could merge while the other is still writing to its branch. After both merge, the second merge would overwrite the first's changes (OVERRIDE strategy).
3. The branch limit check provides indirect concurrency control — with only 15 slots, the system naturally limits concurrency.

**Verdict**: The concurrency concern is valid but more nuanced than presented. The primary risk is not data corruption (branches are isolated) but lost updates (both promotions succeed, but only the last merge persists). This should be documented as a known limitation with the workaround of checking for IN_PROGRESS promotions of the same root component.

**Confirmed**: **MAJOR**.

### Challenge to Architect M3 (Merge Polling Details) — CONFIRMED MAJOR

The contrast with branch readiness polling (well-defined: 5s delay, 6 retries) vs merge polling (undefined) is stark. The missing `MERGE_FAILED` and `MERGE_TIMEOUT` error codes are also valid.

**Confirmed**: **MAJOR**.

### Challenge to Architect m5 (Empty Branch Query Filter) — AGREE, KEEP AS MINOR

The architect notes that the empty filter counts ALL branches, not just `promo-*`. This is correct behavior (the hard limit is account-wide) but the observation is worth documenting.

**Confirmed**: **MINOR**.

---

## Consolidated Severity Assessment for Consensus

### Confirmed Critical (2)

| ID | Finding | Sources |
|----|---------|---------|
| CC1 | MergeRequest field name mismatch (`source` vs `sourceBranchId`) — template and build guide contradict; requires live API testing | Expert C1 + Architect C3 |
| CC2 | Branch limit threshold inconsistency (10/15/18/20 across docs) — standardize on 15 soft, 20 hard | Expert C2 + Architect C1 |

### Confirmed Major (7)

| ID | Finding | Sources |
|----|---------|---------|
| CM1 | Missing HTTP operations: QUERY IntegrationPack, ReleaseIntegrationPack, AddToIntegrationPack, GET MergeRequest (4 operations missing from centralized build step) | Expert M2 + Architect C2 |
| CM2 | Process G GET Component with tilde syntax — unclear how URL parameter concatenation works; needs explicit documentation | Expert M3 |
| CM3 | IntegrationPackRelease vs ReleaseIntegrationPack naming — endpoint name inconsistent | Expert M4 + Architect C2 |
| CM4 | Appendix API reference missing all Branch, MergeRequest, and IntegrationPack query operations (7+ endpoints) | Expert M6 + Architect M4 |
| CM5 | manageMappings field name (`action` vs `operation`) and missing `create` enum value | Architect M1 |
| CM6 | Concurrency lock mechanism referenced but never implemented — risk of lost updates in concurrent promotions | Architect M2 |
| CM7 | Merge status polling parameters undefined (interval, max retries, failure stages, error codes) | Expert M5 + Architect M3 |

### Confirmed Minor (6)

| ID | Finding | Sources |
|----|---------|---------|
| Cm1 | Naming inventory lists 12 HTTP operations, should be 15+ | Expert M1 (downgraded) |
| Cm2 | create-branch.json missing `description` field | Expert m2 |
| Cm3 | Content-Type note stops at operation 9, should cover 10-15 | Architect m1 |
| Cm4 | `packageId` field name overloaded between PackagedComponent and DeployedPackage contexts | Architect m2 |
| Cm5 | Empty branch QueryFilter counts all branches — document explicitly | Architect m5 |
| Cm6 | Rate limiting for large dependency trees (50+ components) — add edge case documentation | Expert m6 |

### Dismissed/Downgraded

| Finding | Reason |
|---------|--------|
| Expert m5 (120-second timeout) | Not a real risk; polling logic provides the actual time bounds |
| Expert m4 (DeployedPackage componentType) | Inconclusive without API testing |
| Expert m3 (mixed XML/JSON in pre_check) | The `_pre_check` block is metadata documentation, not executable code |

---

## Recommendations for Consensus Document

1. **Highest priority**: Resolve the MergeRequest field name question with a live API test. This is a runtime failure waiting to happen.
2. **Create missing templates**: GET MergeRequest, ReleaseIntegrationPack, AddToIntegrationPack — these block Process D implementation.
3. **Standardize branch limit**: Global find-and-replace: all `>= 18` to `>= 15`, fix the "10-branch" reference.
4. **Update appendix**: The API reference appendix should be the single source of truth for all endpoints used by the system.
5. **Document Process G concatenation**: If `{componentId}~{branchId}` is passed as a single `{2}` parameter, say so explicitly.
6. **Define merge polling**: Match the branch readiness polling pattern (5s delay, 12 retries for merge = 60s total).

# Team 6 — Resilience Engineer Expert Findings

**Date:** 2026-02-16
**Reviewer:** Resilience Engineer
**Scope:** Error handling patterns, failure modes, retry strategy, partial failure handling, orphaned resource cleanup, error propagation across all Groovy scripts, Integration processes, and Flow Service spec.

---

## Critical Findings

### CRIT-1: 4 of 6 Groovy Scripts Missing Try/Catch Blocks (Mandatory Standard Violation)

**Files:**
- `integration/scripts/build-visited-set.groovy` — partial (inner XML parsing wrapped, outer loop unwrapped)
- `integration/scripts/sort-by-dependency.groovy` — **no try/catch at all**
- `integration/scripts/rewrite-references.groovy` — **no try/catch at all**
- `integration/scripts/strip-env-config.groovy` — **no try/catch at all**
- `integration/scripts/validate-connection-mappings.groovy` — **no try/catch at all**
- `integration/scripts/normalize-xml.groovy` — compliant (lines 37-63)

**Standard:** `.claude/rules/groovy-standards.md:45-61` mandates: "Use `try/catch` blocks for **all** Groovy scripts. Log errors with `logger.severe()` for visibility in Process Reporting. Throw meaningful exception messages."

**Impact by script:**

1. **`sort-by-dependency.groovy`** (Process C, step 5): If the JSON input is malformed or a component lacks a `type` field, the script throws an unhandled exception. The per-component Try/Catch (step 8) does NOT wrap step 5 — the sort runs before the loop. An outer Try/Catch at Process C step 100 (architecture doc) would catch it, but the error message would be a raw Groovy stack trace, not an actionable error code.

2. **`strip-env-config.groovy`** (Process C, step 11): If `XmlSlurper.parseText()` fails on malformed component XML, the unhandled exception kills the current loop iteration. The per-component Try/Catch (step 8) catches it, but the error message is a raw `SAXParseException` rather than a meaningful "Failed to strip environment config from component {id}" message.

3. **`rewrite-references.groovy`** (Process C, step 15a.1/15b.1): If `componentMappingCache` DPP is null/empty/malformed, `JsonSlurper.parseText()` throws. Same per-component Try/Catch mitigation, but raw exception.

4. **`validate-connection-mappings.groovy`** (Process C, step 5.6): Runs BEFORE the per-component loop and OUTSIDE the per-component Try/Catch. If `connectionMappingCache` DPP is null, line 30 (`parseText(connCacheJson ?: "{}")`) handles it, but if `componentMappingCache` DPP is absent and the `?: "{}"` fallback fails for some edge case, the entire process dies with no structured error.

5. **`build-visited-set.groovy`** (Process B, step 7): Has a partial try/catch around XML parsing (lines 43-57) but the outer loop body (lines 9-67) has no wrapping. If `JsonSlurper.parseText()` fails on `visitedJson` or `queueJson` DPPs (lines 19, 25), the entire BFS traversal crashes.

**Recommendation:** Add try/catch to all 5 non-compliant scripts following the groovy-standards.md pattern. Each catch block should: (a) `logger.severe()` with script name, component ID, and error message; (b) throw a new Exception with actionable context.

### CRIT-2: No Retry Logic Implemented for ANY Platform API Call

**Files:**
- `docs/architecture.md:215` — states "Retry on 429/503: up to 3 retries with exponential backoff"
- `docs/build-guide/18-troubleshooting.md:47-48` — documents "up to 3 retries with exponential backoff (1 second, 2 seconds, 4 seconds)"
- `docs/build-guide/10-process-c-execute-promotion.md` — NO retry shapes in canvas
- `docs/build-guide/11-process-d-package-and-deploy.md` — NO retry shapes in canvas
- `docs/build-guide/09-process-b-resolve-dependencies.md` — NO retry shapes in canvas

**Gap:** The architecture doc and troubleshooting guide both promise retry with exponential backoff for HTTP 429 (rate limit) and 503 (service unavailable), but NO build guide implements it. Not a single process canvas includes retry shapes, retry loops, or backoff logic.

**Impact:** Process C makes 2-4 API calls per component. A 20-component promotion = 40-80 API calls at 120ms intervals (~8 req/s). The Partner API limit is ~10 req/s. Any burst or concurrent user can trigger 429 errors that kill component promotion with no recovery. Process D makes 5-8 API calls in sequence (merge, package, create/add pack, release, deploy). A single 429 on the deploy call after a successful merge = data inconsistency (merged but not deployed).

**Recommendation:** Implement a reusable retry pattern. In Boomi, this requires a Try/Catch around each HTTP Client Send with a retry loop: on 429/503, wait (exponential: 1s, 2s, 4s), retry up to 3 times. The HTTP operations already define 429 and 503 as error codes (`02-http-client-setup.md:75,101,154` etc.), so Boomi will route these to the catch path.

---

## Major Findings

### MAJ-1: Partial Failure in Process C — SKIPPED Component Logic Under-Specified

**Files:**
- `docs/build-guide/10-process-c-execute-promotion.md:294-299` (step 18)
- `integration/flow-service/flow-service-spec.md:147` (action values)

**Gap:** Step 18.3 says "Mark dependent components as SKIPPED — any component in the remaining loop that references `currentComponentId`" but provides no mechanism for HOW to determine dependents at runtime. The loop processes components sequentially (bottom-up by type). If a profile at priority 1 fails, all operations (priority 3) and maps (priority 4) that reference it should be SKIPPED. But the build guide does not specify:
- How to build a reverse dependency index from the sorted component list
- How to propagate the "skip" flag to downstream components in the For Each loop
- Whether SKIPPED components still update the componentMappingCache (they should NOT)
- Whether `componentsFailed` includes both FAILED and SKIPPED, or only FAILED

**Impact:** Without this logic, a failed profile would still allow its dependent operation to be promoted — but `rewrite-references.groovy` would have no mapping for the profile, leaving broken references in the promoted component.

**Recommendation:** Add a `failedComponentIds` DPP (JSON array). In the catch block, add the failed ID. At step 9 (Set Properties — Current Component), add a check: if any of the current component's references are in `failedComponentIds`, immediately mark as SKIPPED and continue loop. Document that SKIPPED components are NOT added to `componentMappingCache`.

### MAJ-2: Orphaned Branch Risk — No Cleanup on Peer Rejection or Admin Denial

**Files:**
- `docs/architecture.md:302-307` — documents branch deletion on all terminal paths
- `integration/flow-service/flow-service-spec.md:355-384` (submitPeerReview) — NO branch deletion on REJECTED
- `docs/build-guide/` — no process implements branch deletion for rejection

**Gap:** The architecture doc states the key invariant: "Every branch is either actively in review or has been deleted. No orphaned branches." But the actual implementation has no mechanism to delete branches on rejection:

- **Process E3 (submitPeerReview):** On `decision=REJECTED`, updates `peerReviewStatus` to `PEER_REJECTED` but does NOT delete the branch. The `branchId` remains in PromotionLog but no process cleans it up.
- **Admin denial:** No admin denial action exists at all. There is no `submitAdminReview` or equivalent message action in the flow-service-spec.
- **Cancel/abandon:** No `cancelPromotion` action exists to clean up branches from abandoned workflows.

**Impact:** Each rejected/denied/abandoned promotion leaks one branch. With the 15-branch threshold (Process C step 3.6), this means 15 rejections without any approvals = `BRANCH_LIMIT_REACHED` for the entire account. Given that peer review is expected to catch issues, rejections are a normal workflow event — this is not an edge case.

**Cross-reference:** Confirmed by team2-consensus.md MAJ-4 and MAJ-5.

**Recommendation:**
1. Add branch deletion to Process E3 on `decision=REJECTED`
2. Create an `adminReview` message action (Process E5) that handles approve/reject/deny with branch deletion on reject/deny
3. Create a `cancelPromotion` action for abandoned workflows
4. All branch deletion should update PromotionLog `branchId` to null

### MAJ-3: Process D — No Rollback on Partial Deployment Failure

**Files:**
- `docs/build-guide/11-process-d-package-and-deploy.md:159-167` (step 8)
- `docs/build-guide/11-process-d-package-and-deploy.md:199-206` (error handling)

**Gap:** Process D deploys to potentially multiple target environments in a loop (step 8). If deployment succeeds for environment A but fails for environment B:
- The response shows `deploymentStatus = "PARTIAL"`
- The merge has already committed to main (step 2.6) — cannot be undone
- The branch is deleted (step 8.5 for PRODUCTION modes)
- No mechanism to retry the failed environment deployment
- No mechanism to undeploy from the successful environment

**Impact:** The system is now in an inconsistent state: environment A has the new version, environment B does not. The PromotionLog shows `DEPLOYED` status. If the user re-runs Process D, it would create a duplicate PackagedComponent.

**Mitigation noted:** Architecture doc states "No automated rollback — Boomi maintains version history" (`docs/architecture.md:217`). This is a conscious design decision, but the user-facing recovery path is undocumented.

**Recommendation:**
1. Document the manual recovery procedure for partial deployments
2. Add a `retryDeployment` action that takes a `promotionId` and retries only the failed environments (skipping merge and packaging since those succeeded)
3. Consider storing per-environment deployment status in PromotionLog rather than just a single `deploymentStatus`

### MAJ-4: Error Propagation Gap — Groovy Exceptions to Flow Dashboard Users

**Files:**
- `docs/build-guide/04-process-canvas-fundamentals.md:121-124` (error response pattern)
- `integration/flow-service/flow-service-spec.md:636-686` (error handling contract)

**Gap:** The error propagation chain has a weak link. When a Groovy script throws an exception (e.g., `sort-by-dependency.groovy` on malformed input), the exception flows to:
1. Per-component Try/Catch (step 8) — IF within the loop
2. Outer Try/Catch (step 100 note) — for catastrophic failures
3. Boomi process-level error handling → Return Documents

But the catch blocks in the build guide (steps 18, 100) only describe logging and result accumulation. They do NOT describe how to:
- Map raw Java/Groovy exceptions to the error code catalog (`flow-service-spec.md:656-678`)
- Build a structured error response JSON from a catch block
- Ensure the Return Documents shape receives a valid response profile document (not a raw exception string)

**Impact:** If the outer Try/Catch fires, the user may receive a generic Boomi error response rather than a structured `{success: false, errorCode: "...", errorMessage: "..."}` response. Flow Decision steps checking `success == false` would not trigger, and the error would be lost or displayed as a raw stack trace.

**Recommendation:** Add explicit error-to-response mapping in all catch blocks. Each catch should: (a) construct a valid response JSON document matching the response profile; (b) set `errorCode` from a mapping of exception types to error codes; (c) set `errorMessage` to a sanitized human-readable message (never raw stack traces); (d) set `success = false`; (e) route to Return Documents.

### MAJ-5: `validate-connection-mappings.groovy` — Single-Document Assumption

**Files:**
- `integration/scripts/validate-connection-mappings.groovy:25-26`

**Gap:** The script reads only `dataContext.getStream(0)` — the first document. It does not iterate over `dataContext.getDataCount()` like all other scripts. If step 5 (sort-by-dependency) somehow produces multiple documents (e.g., via a split shape or Boomi document batching), only the first document would be validated. Additionally, it creates `new Properties()` at line 74 instead of preserving the input document's properties.

**Mitigation:** In the current process flow, step 5 produces a single document (one JSON array). But this is fragile — any upstream change could introduce multi-document scenarios.

**Cross-reference:** Confirmed by team2-consensus.md MIN-8.

**Recommendation:** Add `dataContext.getDataCount()` loop and preserve input properties. Even if the current flow guarantees a single document, defensive coding prevents future regressions.

### MAJ-6: DPP Catalog Incomplete — Missing D, E2, E3, E4, G, J

**Files:**
- `docs/build-guide/20-appendix-dpp-catalog.md` — only Global, Process B, and Process C documented

**Gap:** The DPP catalog covers ~40% of the system. Missing process DPPs:
- **Process D:** `branchId`, `promotionId`, `mergeRequestId`, `packagedComponentId`, `deploymentTarget`, `isHotfix`, `hotfixJustification`, `testPromotionId`, `testIntegrationPackId`, `testIntegrationPackName`
- **Process G:** `branchId`, `prodComponentId`, `componentAction`
- **Process J:** `suggestForProcess`, `packPurpose`
- **Processes E2, E3, E4:** Completely undocumented

**Impact:** DPPs are the primary state mechanism in this system. Without a complete catalog, builders cannot debug DPP-related failures, verify persistence flags, or identify naming conflicts. This is an operational observability gap — when something fails, the troubleshooter has no reference for expected DPP state.

**Cross-reference:** Confirmed by team2-consensus.md MIN-1.

**Recommendation:** Complete the DPP catalog for all 12 processes. Include persistence flags per groovy-standards.md guidance.

---

## Minor Findings

### MIN-1: `build-visited-set.groovy` — O(n) Contains Checks on JSON Arrays

**Files:** `integration/scripts/build-visited-set.groovy:33,50`

**Gap:** Both `visitedSet.contains(currentId)` (line 33) and `queue.contains(childId)` (line 50) perform O(n) linear scans on JSON arrays deserialized from DPPs. For a tree of 100+ components, each iteration scans the full visited set and queue.

**Impact:** Negligible in practice — API latency (120ms per call) dominates. But compounds with the BFS loop for very large trees.

**Cross-reference:** Confirmed by team2-consensus.md MIN-7.

**Recommendation:** Use a Set data structure for `visitedSet` instead of a List. Convert to JSON array only for DPP storage.

### MIN-2: `normalize-xml.groovy` — Graceful Degradation on Parse Failure

**Files:** `integration/scripts/normalize-xml.groovy:58-62`

**Observation:** This is the ONLY script that correctly handles parse failures by falling back to the original content (line 62: pass through raw XML). This is good resilience engineering — the diff viewer still works with non-normalized XML, just with potentially more noise in the diff.

**Recommendation:** Adopt this pattern in `strip-env-config.groovy` — if XML parsing fails, pass through the original XML rather than killing the component promotion. The branch isolation (diff review) provides a safety net.

### MIN-3: SKIPPED / FAILED / PARTIAL Status Values Not in Error Code Catalog

**Files:**
- `integration/flow-service/flow-service-spec.md:147` — `action` only documents "created" | "updated"
- `docs/build-guide/10-process-c-execute-promotion.md:24` — documents "FAILED" and "SKIPPED"
- `docs/build-guide/10-process-c-execute-promotion.md:315` — documents "PARTIAL" status

**Gap:** Three status values used by the system are not documented in the flow-service-spec's error handling contract:
- `FAILED` (per-component action value)
- `SKIPPED` (per-component action value from dependency failure)
- `PARTIAL` (PromotionLog status when some components fail)

**Impact:** Flow Decision steps may not handle these values correctly. The UI may not display appropriate messages for partially failed promotions.

**Cross-reference:** Confirmed by team2-consensus.md MIN-3.

**Recommendation:** Add FAILED, SKIPPED to the documented `action` enum in flow-service-spec. Add PARTIAL to the PromotionLog status values.

### MIN-4: 120ms Inter-Call Gap — No Build Guide Shape Implementing It

**Files:**
- `docs/architecture.md:214` — "120ms gap between API calls"
- `docs/build-guide/10-process-c-execute-promotion.md` — no sleep/delay shape in canvas

**Gap:** The 120ms rate-limiting gap between API calls is documented in the architecture but no Process C canvas step implements it. Boomi provides a `Process Call` delay or a `Data Process` with `Thread.sleep()`, but neither is specified.

**Impact:** Without the gap, Process C fires API calls as fast as Boomi can process them. For a 20-component promotion, this could produce bursts of 3-4 rapid API calls (GET Component, strip, rewrite, POST Component) per iteration, exceeding the ~10 req/s limit.

**Recommendation:** Add a `Thread.sleep(120)` in a Data Process shape between each HTTP Client Send, or use Boomi's built-in connector throttling if available.

### MIN-5: No Health Check or Heartbeat for Long-Running Promotions

**Files:**
- `integration/flow-service/flow-service-spec.md:604-630` — async behavior documentation

**Observation:** The Flow Service spec documents that long-running operations (30-120s for executePromotion) are handled by Boomi's built-in async mechanism. But there is no intermediate status update mechanism — the user sees only a spinner until completion or failure. For a 120-second promotion, there is no way to know if the process is stuck at component 3/20 or progressing normally.

**Recommendation:** Consider updating the PromotionLog `resultDetail` field incrementally during the loop (not just at step 21). A separate `queryStatus` call could then show progress. Low priority — the async mechanism works, but observability during long operations is limited.

### MIN-6: Process C Step 6 — componentMappingCache Reset Erases Connection Mappings

**Files:**
- `docs/build-guide/10-process-c-execute-promotion.md:158-159` (step 6)
- `integration/scripts/validate-connection-mappings.groovy:67-69`

**Gap:** Step 5.6 (`validate-connection-mappings.groovy`) pre-loads connection mappings into `componentMappingCache` (line 68). Step 6 then resets `componentMappingCache = {}`, erasing those pre-loaded mappings.

**Impact:** When `rewrite-references.groovy` runs on downstream components, connection references are NOT rewritten (the cache no longer contains connection dev-to-prod mappings). This is a logic error that causes silent data corruption — promoted components reference dev connection IDs instead of prod connection IDs.

**Cross-reference:** Confirmed by team2-consensus.md MAJ-6 (cache reset bug).

**Recommendation:** Remove the `componentMappingCache = {}` reset at step 6. The cache should retain connection mappings loaded by step 5.6.

---

## Observations

### OBS-1: Process C Dual Try/Catch Architecture Is Sound

The outer Try/Catch (wrapping steps 4-22 with branch cleanup in catch) combined with the inner per-component Try/Catch (step 8, with continue-on-failure) is a solid resilience pattern. It provides both per-component graceful degradation and catastrophic failure protection with resource cleanup.

**Files:** `docs/build-guide/10-process-c-execute-promotion.md:100` (outer), `docs/build-guide/10-process-c-execute-promotion.md:164-165` (inner)

### OBS-2: Process D Branch Deletion Is Idempotent

The DELETE Branch operation correctly treats both `200` (deleted) and `404` (already deleted) as success (`docs/build-guide/02-http-client-setup.md:418`). This is correct idempotency handling — if a branch was already cleaned up by another path, the deletion does not fail.

### OBS-3: normalize-xml.groovy Is the Gold Standard for Script Resilience

This script demonstrates all the patterns the other scripts should follow: null/empty input check (line 31), try/catch with `logger.severe()` (lines 37-63), graceful degradation on failure (pass through original, line 62), and `dataContext.storeStream()` on all paths. It should be the template for fixing the other 4 non-compliant scripts.

### OBS-4: Connection Non-Promotion Is a Strong Resilience Decision

Excluding connections from promotion (with admin-seeded mappings) eliminates the most dangerous class of failure: accidentally promoting dev credentials to production. The `validate-connection-mappings.groovy` script's batch pre-check with fail-fast on missing mappings is an effective guard.

### OBS-5: DataHub Match Rules Provide Built-In Idempotency

The DataHub UPSERT behavior (match on `devComponentId + devAccountId` for ComponentMapping) means that re-running a failed promotion does not create duplicate mappings. This is a key resilience property — failed promotions can be safely retried.

---

## Multi-Environment Resilience Assessment

### Strengths

1. **Branch preservation for TEST mode** prevents the need to re-promote when transitioning from test to production
2. **Three-mode Decision shape** in Process D correctly isolates each deployment path
3. **Idempotent branch deletion** means concurrent cleanup attempts do not conflict
4. **testPromotionId linkage** maintains traceability across the test-to-production lifecycle

### Gaps

1. **No cancelTestDeployment action:** Stale test branches accumulate without cleanup mechanism. 30-day UI warning has no backend enforcement.
2. **Branch lifecycle extends days/weeks in test mode:** With branches persisting through test validation, the 15-branch threshold is reached faster. No automatic expiry.
3. **TEST mode merge-then-preserve creates an irreversible state:** Once test deployment merges to main (step 2.5), there is no "undo test" path. If test validation fails, the component is already on main.
4. **Hotfix justification is not validated server-side:** `HOTFIX_JUSTIFICATION_REQUIRED` error code exists in the spec (line 676) but no process canvas step checks for empty justification when `isHotfix=true`.
5. **No Process E5 (admin review) exists:** The 2-layer approval workflow has no backend action for admin review decisions. Admin approve/reject/deny would need a new message action.

### Risk Matrix

| Scenario | Likelihood | Impact | Mitigation Status |
|----------|-----------|--------|-------------------|
| Script crash from malformed input | Medium | High (process dies) | UNMITIGATED (4/6 scripts lack try/catch) |
| API rate limit (429) kills promotion | Medium | High (partial promotion) | UNMITIGATED (no retry logic) |
| Orphaned branches from rejections | High | High (branch exhaustion) | UNMITIGATED (no cleanup on reject) |
| Partial deployment (some envs fail) | Low | Medium (inconsistent state) | PARTIALLY MITIGATED (documented, no auto-recovery) |
| Connection mapping cache reset bug | Certain (if built as written) | Critical (broken refs) | UNMITIGATED (build guide bug) |
| Long promotion with no progress visibility | Medium | Low (user anxiety only) | PARTIALLY MITIGATED (async spinner) |
| Concurrent promotions (race condition) | Medium | High (duplicate components) | UNMITIGATED (architecture doc promises lock, none built) |

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Major | 6 |
| Minor | 6 |
| Observations | 5 |

## Top 5 Resilience Recommendations (Priority Order)

1. **Add try/catch to all Groovy scripts** per groovy-standards.md — 4 scripts are non-compliant, risking unstructured exceptions (CRIT-1)
2. **Implement retry with exponential backoff** for all Platform API calls — the architecture promises it but zero build guides implement it (CRIT-2)
3. **Add branch deletion to rejection/denial paths** — every rejection leaks a branch toward the 15-branch limit (MAJ-2)
4. **Fix step 6 cache reset bug** — connection mappings are erased before they can be used (MIN-6, cross-ref team2 MAJ-6)
5. **Specify SKIPPED component propagation mechanism** — the current build guide describes the intent but not the implementation (MAJ-1)

# Team 6 — Consensus: Error Handling & Resilience

**Date:** 2026-02-16
**Team:** Resilience Engineer (Expert) + Operations/Observability Architect + Devil's Advocate
**Scope:** Error handling patterns, retry logic, failure modes, observability, operational readiness

---

## Critical Findings

### CRIT-1: componentMappingCache Reset Bug — Silent Connection Reference Corruption

**Consensus severity:** Critical (upgraded from Expert MIN-6)
**Files:** `docs/build-guide/10-process-c-execute-promotion.md:158-159` (step 6), `integration/scripts/validate-connection-mappings.groovy:67-69`

**Finding:** Step 5.6 (`validate-connection-mappings.groovy`) pre-loads connection dev-to-prod mappings into `componentMappingCache` (line 68). Step 6 then resets `componentMappingCache = {}`, erasing those mappings. When `rewrite-references.groovy` runs later, connection references in promoted component XML are NOT rewritten — promoted operations and processes still reference dev connection IDs instead of prod connection IDs.

**Impact:** Silent data corruption. Promoted components contain broken connection references. The system does not report an error; it completes "successfully" with corrupted data.

**Recommendation:** Remove the `componentMappingCache = {}` reset at step 6. The cache should retain connection mappings pre-loaded by step 5.6, then accumulate component mappings during the loop.

**Cross-reference:** Wave 1 team2 MAJ-6.

---

### CRIT-2: No Retry Logic Implemented for Any Platform API Call

**Consensus severity:** Critical (unanimous)
**Files:** `docs/architecture.md:215`, `docs/build-guide/18-troubleshooting.md:47-48`, all process build guides (09, 10, 11)

**Finding:** The architecture document promises "Retry on 429/503: up to 3 retries with exponential backoff (1s, 2s, 4s)." The troubleshooting guide documents the same. Zero build guide process canvases implement any retry shape, retry loop, or backoff logic. This is a specification-to-implementation contradiction.

**Impact:** Process C makes 2-4 API calls per component. A 20-component promotion generates 40-80 calls at ~8 req/s. The Partner API limit is ~10 req/s. Concurrent users or burst traffic will trigger 429 errors that kill component promotion with no recovery. Process D is higher risk: a 429 after a successful merge creates an inconsistent state (merged but not deployed).

**Recommendation:** Implement a reusable retry pattern. In Boomi, wrap each HTTP Client Send in a Try/Catch with a loop: on 429/503, delay with exponential backoff (1s, 2s, 4s), retry up to 3 times. The HTTP operations already define 429 and 503 as error status codes, routing them to the catch path.

---

## Major Findings

### MAJ-1: 5 of 6 Groovy Scripts Non-Compliant with try/catch Standard

**Consensus severity:** Major (downgraded from Expert Critical by DA; consensus agrees)
**Files:** `integration/scripts/sort-by-dependency.groovy`, `strip-env-config.groovy`, `rewrite-references.groovy`, `validate-connection-mappings.groovy`, `build-visited-set.groovy` (partial)
**Standard:** `.claude/rules/groovy-standards.md:45-61`

**Finding:** Only `normalize-xml.groovy` fully complies with the mandatory try/catch standard. The other 5 scripts have either no try/catch or only partial wrapping. While Process C's outer and inner Try/Catch shapes provide a safety net, the scripts produce raw Java/Groovy stack traces instead of actionable error messages with component IDs and error codes.

**Impact:** Users and ops teams receive unstructured exception messages (e.g., `SAXParseException` or `NullPointerException`) instead of meaningful errors like "Failed to strip environment config from component {id}: malformed XML." Troubleshooting becomes significantly harder.

**Recommendation:** Add try/catch to all 5 scripts following `normalize-xml.groovy` as a template. Each catch should: (a) `logger.severe()` with script name, component ID, and exception message; (b) throw a new Exception with actionable context. Consider adopting `normalize-xml.groovy`'s graceful degradation pattern (pass through original content on failure) for `strip-env-config.groovy`.

---

### MAJ-2: Orphaned Branch Risk — Incomplete Branch Lifecycle on Rejection/Denial

**Consensus severity:** Major (unanimous)
**Files:** `docs/architecture.md:302-307`, `integration/flow-service/flow-service-spec.md:355-384`

**Finding:** The architecture doc specifies branch deletion on peer rejection and admin denial. However:
1. Process E3 (`submitPeerReview`) does NOT include branch deletion as an implementation step when `decision=REJECTED`
2. No admin review action (`submitAdminReview` or equivalent) exists in the flow-service-spec — there are zero message actions for admin approve/reject/deny
3. No `cancelPromotion` action exists for abandoned workflows

**Impact:** Each rejected/denied/abandoned promotion leaks one branch. With the 15-branch threshold (Process C step 3.6), 15 rejections without approvals = `BRANCH_LIMIT_REACHED`. Since peer review is expected to catch issues, rejections are a normal workflow event.

**Recommendation:**
1. Add branch deletion step to Process E3 on `decision=REJECTED` (implementation gap vs. architecture)
2. Define a new `submitAdminReview` message action (Process E5) handling admin approve/reject/deny with branch deletion on reject/deny
3. Define a `cancelPromotion` action for abandoned workflows
4. All branch deletions should update PromotionLog `branchId` to null

**Cross-reference:** Wave 1 team2 MAJ-4, MAJ-5.

---

### MAJ-3: SKIPPED Component Propagation Logic Unspecified

**Consensus severity:** Major (unanimous)
**Files:** `docs/build-guide/10-process-c-execute-promotion.md:294-299` (step 18)

**Finding:** Step 18.3 says "Mark dependent components as SKIPPED" but provides no implementation mechanism. The build guide does not specify: how to build a reverse dependency index, how to propagate skip flags in the For Each loop, whether SKIPPED components update the mapping cache (they should not), or whether `componentsFailed` includes SKIPPED counts.

**Impact:** Without SKIPPED propagation, a failed profile allows its dependent operation to be promoted, but `rewrite-references.groovy` has no mapping for the failed profile, leaving broken references in the promoted operation's XML.

**Recommendation:** Add a `failedComponentIds` DPP (JSON array). In the catch block, add the failed ID. At the start of each loop iteration (step 9), check if any of the current component's XML references are in `failedComponentIds`. If yes, mark as SKIPPED and continue.

---

### MAJ-4: Error Propagation Gap — Groovy Exceptions to Structured Responses

**Consensus severity:** Major (unanimous)
**Files:** `docs/build-guide/04-process-canvas-fundamentals.md`, `integration/flow-service/flow-service-spec.md:636-686`

**Finding:** When a Groovy script throws an exception caught by Process C's outer Try/Catch (step 100), the catch blocks do not describe how to: (a) map raw exceptions to the error code catalog, (b) build structured JSON matching the response profile, or (c) ensure the Return Documents shape receives a valid document (not a raw exception string).

**Impact:** Catastrophic failures may return raw Boomi error responses instead of structured `{success: false, errorCode, errorMessage}` JSON. Flow Decision steps checking `success == false` would not trigger correctly.

**Recommendation:** Add explicit error-to-response mapping in all catch blocks. Each catch should construct a valid response profile document with `success = false`, a mapped `errorCode`, and a sanitized `errorMessage`. Never expose raw stack traces to the Flow UI.

---

### MAJ-5: Troubleshooting Guide Has Zero Error Code Cross-References

**Consensus severity:** Major (downgraded from Architect Critical by DA; consensus settles on Major)
**Files:** `docs/build-guide/18-troubleshooting.md`, `integration/flow-service/flow-service-spec.md:656-678`

**Finding:** The troubleshooting guide (150 lines) uses natural language descriptions but references none of the 19 error codes from the flow-service-spec. An ops engineer receiving `MISSING_CONNECTION_MAPPINGS`, `BRANCH_LIMIT_REACHED`, or `SELF_REVIEW_NOT_ALLOWED` has no lookup path in the troubleshooting guide.

**Impact:** Ops teams cannot map runtime error codes to diagnostic steps. This breaks the primary incident response workflow.

**Recommendation:** Add an "Error Code Quick Reference" section to `18-troubleshooting.md` mapping each of the 19 error codes to: root cause, diagnostic steps, resolution actions.

---

### MAJ-6: No Monitoring Strategy, Alerting Rules, or SLAs Defined

**Consensus severity:** Major (downgraded from Architect Critical by DA)
**Files:** `integration/flow-service/flow-service-spec.md:712-737`, `docs/architecture.md`

**Finding:** The system has no defined monitoring strategy, alerting thresholds, dashboards, or SLAs. The flow-service-spec's monitoring section (4 paragraphs) points to Boomi Process Reporting with zero specifics. The architecture doc has no operational sections.

**Impact:** The system will launch without observability. Failures will only be discovered when users report them.

**Recommendation:** Create `docs/operations.md` covering: key metrics per process (execution time, failure rate, component count), alerting thresholds (e.g., >3 consecutive failures), saved Process Reporting views for each process, SLAs (availability, mean time to promote), and on-call escalation paths.

---

### MAJ-7: Testing Guide Missing Coverage for Processes G, J, F, E4

**Consensus severity:** Major (unanimous)
**Files:** `docs/build-guide/17-testing.md`

**Finding:** The testing guide has 10 tests covering 7 of 12 processes. Processes G (diff), J (pack listing), F (mapping CRUD), and E4 (test deployment query) have no dedicated test scenarios.

**Recommendation:** Add Tests 11-14 covering these processes individually.

---

### MAJ-8: No Negative/Security Test Scenarios

**Consensus severity:** Major (unanimous)
**Files:** `docs/build-guide/17-testing.md`

**Finding:** The testing guide focuses on happy-path scenarios with only one error-recovery test (Test 6). Seven error codes are completely untested: `SELF_REVIEW_NOT_ALLOWED`, `ALREADY_REVIEWED`, `INSUFFICIENT_TIER`, `MISSING_CONNECTION_MAPPINGS`, `BRANCH_LIMIT_REACHED`, `INVALID_DEPLOYMENT_TARGET`, `INVALID_REVIEW_STATE`.

**Recommendation:** Add a "Negative Test Suite" section covering each error code with explicit expected behavior and verification steps.

---

## Minor Findings

### MIN-1: BRANCH_LIMIT_REACHED Threshold Inconsistency (3 Conflicting Values)

**Files:** `10-process-c-execute-promotion.md:79` (15), `flow-service-spec.md:670` (20), `architecture.md:284` (15, 18)

Three different branch limit values appear across documents. Should be unified to one canonical value (15 per architecture.md's "lowered from 18 to 15 for early warning").

### MIN-2: FAILED/SKIPPED/PARTIAL Status Values Not in Flow-Service-Spec Enum

**Files:** `10-process-c-execute-promotion.md:24`, `flow-service-spec.md:147`

The `action` field in the response documents "created" | "updated" but Process C also produces "FAILED" and "SKIPPED". The PromotionLog `status` field produces "PARTIAL" but this is not in any documented enum.

### MIN-3: 120ms Inter-Call Gap Not Implemented in Build Guide

**Files:** `architecture.md:214`, `10-process-c-execute-promotion.md`

The 120ms API rate-limiting gap is documented in architecture but no process canvas step implements a delay between HTTP Client Send shapes.

### MIN-4: `validate-connection-mappings.groovy` Single-Document Assumption

**Files:** `integration/scripts/validate-connection-mappings.groovy:25-26,74`

The script reads only `dataContext.getStream(0)` (first document) and creates `new Properties()` instead of preserving input properties. Currently safe but fragile.

### MIN-5: DPP Catalog Covers Only ~40% of Processes

**Files:** `docs/build-guide/20-appendix-dpp-catalog.md`

Missing DPPs for Processes D, E2, E3, E4, G, J. Ops teams cannot troubleshoot DPP-related failures without knowing valid DPP names and persistence flags.

### MIN-6: Troubleshooting Guide References 11 Operations (Should Be 12)

**Files:** `18-troubleshooting.md:106,111`, `flow-service-spec.md:521-533`

Phase 7 addition of `QueryTestDeployments` not reflected in troubleshooting guide listener count.

### MIN-7: No Operational Runbook or Playbook

**Files:** All docs/ files

No documented procedures for: branch cleanup, DataHub record cleanup, API token rotation, capacity planning, or escalation paths.

### MIN-8: `manageMappings` Action Enum Missing "create"

**Files:** `flow-service-spec.md:303,299-300`

The `action` field lists "query" | "update" | "delete" but the connection seeding workflow narrative describes using `operation = "create"`. The create action is described but not formally enumerated.

### MIN-9: No Structured Logging Standard Across Scripts

No consistent log format across scripts. No correlation ID (promotionId) in log messages, no script identifier prefix, no structured key-value formatting.

---

## Observations

### OBS-1: Process C Dual Try/Catch Architecture Is Sound

The outer Try/Catch (steps 4-22 with branch cleanup in catch) combined with the inner per-component Try/Catch (step 8 with continue-on-failure) is a solid resilience pattern providing both per-component graceful degradation and catastrophic failure protection with resource cleanup.

### OBS-2: normalize-xml.groovy Is the Gold Standard for Script Resilience

This script demonstrates all patterns the other scripts should follow: null/empty input check, try/catch with `logger.severe()`, graceful degradation on failure (pass through original content), and `dataContext.storeStream()` on all paths.

### OBS-3: Connection Non-Promotion Is a Strong Design Decision

Excluding connections from promotion with admin-seeded mappings eliminates the most dangerous failure class: accidentally promoting dev credentials to production. The validate-connection-mappings batch pre-check with fail-fast on missing mappings is effective.

### OBS-4: DataHub Match Rules Provide Built-In Idempotency

The UPSERT behavior (match on devComponentId + devAccountId) means re-running a failed promotion does not create duplicate mappings. Failed promotions can be safely retried.

### OBS-5: Process D Branch Deletion Is Correctly Idempotent

DELETE Branch treats both 200 (deleted) and 404 (already deleted) as success. Correct idempotency handling.

### OBS-6: Process D Partial Deployment Is a Conscious Design Trade-off

The architecture explicitly chose "No automated rollback — Boomi maintains version history." Partial deployment (some environments succeed, others fail) is an accepted risk with manual recovery via version history. The gap is the undocumented manual recovery procedure.

### OBS-7: Multi-Environment Testing Coverage Is Solid (Tests 8-10)

Tests 8-10 cover dev-to-test-to-production happy path, emergency hotfix path, and rejection scenarios. These include specific PromotionLog field verification. This is the strongest section of the testing guide.

---

## Areas of Agreement (All Three Reviewers)

1. **The componentMappingCache reset at step 6 is a confirmed build guide bug** causing silent connection reference corruption (CRIT-1)
2. **Retry logic is completely unimplemented** despite being promised by architecture and troubleshooting docs (CRIT-2)
3. **5 of 6 Groovy scripts violate the mandatory try/catch standard** from groovy-standards.md (MAJ-1)
4. **Orphaned branches on rejection/denial** are a real risk due to missing Process E3 branch deletion and missing admin review action (MAJ-2)
5. **SKIPPED component propagation** is described conceptually but has no implementation mechanism (MAJ-3)
6. **Error code to troubleshooting cross-referencing** is completely absent (MAJ-5)
7. **normalize-xml.groovy** should be the template for fixing the other scripts (OBS-2)
8. **The dual Try/Catch pattern in Process C** is architecturally sound (OBS-1)

---

## Unresolved Debates

### Debate 1: Severity of Script try/catch Gap

- **Expert:** Critical (violations of mandatory standard; risk of unstructured exceptions)
- **DA:** Major (process-level Try/Catch provides safety net; gap is message quality not missing handling)
- **Consensus:** **Major** — The process-level Try/Catch does catch script exceptions, reducing the blast radius. The real gap is poor error messages, not unhandled crashes.

### Debate 2: Severity of Missing Monitoring/SLAs

- **Architect:** Critical (no observability = unacceptable for production)
- **DA:** Major (specification repo context; monitoring is deployment-time concern)
- **Consensus:** **Major** — The gap is real and should be addressed before production deployment, but for a specification repository the monitoring strategy is appropriately a separate deliverable.

### Debate 3: Partial Deployment Rollback

- **Expert:** Major (inconsistent state between environments with no recovery)
- **DA:** Minor (conscious design trade-off per architecture doc; Boomi versioning provides manual recovery)
- **Consensus:** **Observation** (OBS-6) — Documented as a conscious trade-off. Add recommendation to document the manual recovery procedure.

---

## Multi-Environment Assessment

### Resilience Strengths

1. **Branch preservation for TEST mode** prevents re-promotion when transitioning to production
2. **Three-mode Decision shape** in Process D correctly isolates each deployment path
3. **testPromotionId linkage** maintains traceability across test-to-production lifecycle
4. **Idempotent branch deletion** (200/404 both success) prevents concurrent cleanup conflicts
5. **Pack purpose filtering** (TEST/PRODUCTION) via naming convention prevents cross-deployment

### Resilience Gaps

1. **No cancelTestDeployment action:** Stale test branches accumulate with no cleanup mechanism. 30-day UI warning has no backend enforcement.
2. **Branch lifecycle extends days/weeks in test mode:** 15-branch threshold is reached faster with persisted branches. No automatic expiry or enforcement.
3. **Hotfix justification not validated server-side:** `HOTFIX_JUSTIFICATION_REQUIRED` error code exists but no process step checks for empty justification when `isHotfix=true`.
4. **No admin review action:** The 2-layer approval workflow has no backend message action for admin review decisions. This is a functional gap, not just an error handling gap.
5. **TEST mode merge creates irreversible state:** Once test deployment merges to main, there is no "undo test" path. If test validation fails after merge, the component is permanently on main.

### Risk Matrix

| Scenario | Likelihood | Impact | Mitigation Status |
|----------|-----------|--------|-------------------|
| Connection mapping cache reset bug | Certain (if built as spec'd) | Critical (broken refs) | UNMITIGATED — build guide bug |
| API rate limit (429) kills promotion | Medium | High (partial promotion) | UNMITIGATED — no retry logic |
| Orphaned branches from rejections | High | High (branch exhaustion) | UNMITIGATED — no cleanup on reject |
| Script crash with raw exception | Medium | Medium (poor error msgs) | PARTIALLY MITIGATED — process Try/Catch catches but message quality poor |
| Concurrent promotions (race) | Medium | High (duplicate components) | UNMITIGATED — architecture promises lock, none built |
| Partial deployment across envs | Low | Medium (inconsistent state) | PARTIALLY MITIGATED — documented trade-off, no auto-recovery |
| Stale test deployment branches | Medium | Medium (branch exhaustion) | UNMITIGATED — no cleanup mechanism |
| Long promotion no progress visibility | Medium | Low (user UX only) | PARTIALLY MITIGATED — async spinner |

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Major | 8 |
| Minor | 9 |
| Observations | 7 |

## Top 5 Consensus Recommendations (Priority Order)

1. **Fix componentMappingCache reset bug at step 6** — Remove the `{}` reset; connection mappings must persist from step 5.6 through the loop (CRIT-1)
2. **Implement retry with exponential backoff** for all Platform API calls — the architecture promises it but zero build guides implement it (CRIT-2)
3. **Add branch deletion to Process E3 rejection path** and define a new admin review action — every rejection leaks a branch toward the 15-branch limit (MAJ-2)
4. **Add try/catch to all Groovy scripts** per groovy-standards.md, using normalize-xml.groovy as the template (MAJ-1)
5. **Add error code cross-reference to troubleshooting guide** and define negative test scenarios covering all 19 error codes (MAJ-5, MAJ-8)

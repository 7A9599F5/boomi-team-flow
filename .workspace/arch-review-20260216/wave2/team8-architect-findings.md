# Team 8 -- E2E Testing & Operational Readiness Architect Findings

**Role:** E2E Testing & Operational Readiness Architect
**Date:** 2026-02-16
**Scope:** Testing strategy (`17-testing.md`), troubleshooting coverage (`18-troubleshooting.md`), multi-environment testing, operational readiness, cross-reference with Wave 1 findings

---

## Critical Findings

### CRIT-1: Testing Does Not Cover Processes E2, E3, or E4 as Isolated Units

**Files:** `docs/build-guide/17-testing.md` (entire file)

The testing guide contains 10 test scenarios (Tests 1-10). None of them test Processes E2 (`queryPeerReviewQueue`), E3 (`submitPeerReview`), or E4 (`queryTestDeployments`) as isolated message action calls. These processes are exercised only indirectly:

- **E2**: Implicitly triggered when a peer reviewer opens Page 5 (Tests 5, 8, 9, 10a), but the test never validates the E2 response structure, the self-review exclusion logic, or the `reviewStage` filter.
- **E3**: Implicitly triggered when peer reviewers approve/reject (Tests 5, 8, 9, 10a), but the test never validates the `submitPeerReview` request/response, self-review prevention error (`SELF_REVIEW_NOT_ALLOWED`), double-review prevention (`ALREADY_REVIEWED`), or invalid-state prevention (`INVALID_REVIEW_STATE`).
- **E4**: Not referenced anywhere in testing. No test validates `queryTestDeployments` which powers Page 9 (Production Readiness Queue). The exclusion-join logic (filtering out promotions already promoted to production) is untested.

This is compounded by Wave 1 Team 2 finding CRIT-4: E2 and E3 have no build guide content and no FSS operation creation instructions. Without either build instructions OR test scenarios, these processes are effectively unverifiable.

**Impact:** Three of the 12 processes have zero targeted test coverage. The most complex validation logic in the system (self-review prevention, state guards, exclusion joins) is tested only through happy-path UI flows.

**Recommendation:** Add dedicated test scenarios:
- **Test 11: Peer Review Queue (Process E2)** -- POST `queryPeerReviewQueue`, verify self-review exclusion, verify `reviewStage` filter, verify response includes `targetEnvironment`/`isHotfix` fields (per Wave 1 Team 1 CM-1).
- **Test 12: Submit Peer Review (Process E3)** -- POST `submitPeerReview` with approve/reject, verify `SELF_REVIEW_NOT_ALLOWED` when reviewer = initiator, verify `ALREADY_REVIEWED` on double-submit, verify `INVALID_REVIEW_STATE` when promotion not in `PENDING_PEER_REVIEW`.
- **Test 13: Query Test Deployments (Process E4)** -- POST `queryTestDeployments`, verify exclusion of already-promoted records, verify branch age calculation, verify `branchId` populated.

### CRIT-2: No Test Scenario for Self-Review Prevention

**Files:** `docs/build-guide/17-testing.md` (Test 5, lines 263-296)

Test 5 (Approval Workflow) says "Log in as a different developer or admin (peer reviewer)" at line 269 -- implying self-review is avoided by manual test procedure. But there is no test that:
1. Attempts self-review and verifies it is blocked.
2. Validates the `SELF_REVIEW_NOT_ALLOWED` error code is returned.
3. Confirms Process E2's backend exclusion (the promoter's submissions are filtered out of their queue).

Self-review prevention is a core security control (Wave 1 Team 4 Observation: "Defense-in-depth self-review prevention: Backend exclusion (Process E2) + UI Decision step fallback"). Both layers must be tested, not just the happy path where a different user is used.

**Impact:** A regression in either the backend exclusion logic or the UI Decision step would allow self-approval, bypassing the entire peer review gate.

**Recommendation:** Add a negative test: "Test 11b: Self-Review Prevention -- Log in as the same user who submitted the promotion. Verify Page 5 does not show the submission. Directly POST `submitPeerReview` with the submitter's credentials. Verify `SELF_REVIEW_NOT_ALLOWED` error response."

---

## Major Findings

### MAJ-1: Branch Limit Threshold Not Tested -- 4 Conflicting Values Unresolved

**Files:** `docs/build-guide/17-testing.md` (no branch limit test), `integration/flow-service/flow-service-spec.md:670`

Wave 1 Team 2 CRIT-2 and Team 3 CC2 independently identified 4 conflicting branch limit values (10, 15, 18, 20) across the codebase. The testing guide has no test scenario that:
1. Validates which branch limit threshold is actually enforced.
2. Verifies the `BRANCH_LIMIT_REACHED` error code when the threshold is exceeded.
3. Tests whether branch cleanup on rejection/denial (Wave 1 Team 2 MAJ-4) actually works to free up branch slots.

The troubleshooting guide (`18-troubleshooting.md`) also has no entry for `BRANCH_LIMIT_REACHED`.

**Impact:** Without a test, the 4-way inconsistency cannot be resolved empirically. Operators have no troubleshooting guidance when users hit this error.

**Recommendation:** Add "Test 14: Branch Limit Enforcement -- Create branches until the limit is reached. Verify `BRANCH_LIMIT_REACHED` error code and message. Verify rejection/denial branch cleanup frees a slot." Add a troubleshooting entry for `BRANCH_LIMIT_REACHED`.

### MAJ-2: Concurrency Not Tested

**Files:** `docs/build-guide/17-testing.md` (no concurrency test)

Wave 1 Team 2 CRIT-1 and Team 3 CM6 both identified that concurrent promotions of overlapping components are unguarded. The testing guide has no test for:
1. Two simultaneous promotions of the same package.
2. Two simultaneous promotions of different packages that share a dependency.
3. Behavior when the concurrency guard (if implemented) blocks the second promotion.

**Impact:** If a concurrency guard is implemented (as recommended by Wave 1), it must be tested. If it is not implemented, the potential for duplicate components and conflicting mappings should be documented as a known limitation with a test to characterize the behavior.

**Recommendation:** Add "Test 15: Concurrent Promotion -- Start two promotions of the same package simultaneously. Verify expected behavior (either blocked with `CONCURRENT_PROMOTION` error, or both succeed with correct versioning)."

### MAJ-3: Troubleshooting Guide Covers Only Phases 1-6, Missing Phase 7

**Files:** `docs/build-guide/18-troubleshooting.md` (entire file, 150 lines)

The troubleshooting guide has sections for Phase 1 (lines 3-33), Phase 2 (lines 36-66), Phase 3 (lines 69-97), Phase 4 (lines 100-112), Phase 5 (lines 115-133), and Phase 6 (lines 136-147). There is no Phase 7 section covering multi-environment deployment issues.

Issues that have no troubleshooting entry:
- Test deployment failure (`TEST_DEPLOY_FAILED`)
- Emergency hotfix workflow issues (`HOTFIX_JUSTIFICATION_REQUIRED`)
- Production-from-test linkage issues (`TEST_PROMOTION_NOT_FOUND`)
- Invalid deployment target (`INVALID_DEPLOYMENT_TARGET`)
- Page 9 data not loading (E4 query issues)
- Branch preserved after test deployment but stale (30+ days)
- Hotfix acknowledgment checkbox not appearing on Page 7

**Impact:** Operators encountering Phase 7 issues have no diagnostic guidance. Given that multi-environment deployment is the newest and most complex feature, it is the most likely area to produce support requests.

**Recommendation:** Add a "Phase 7 Issues" section to `18-troubleshooting.md` covering all Phase 7 error codes and common configuration issues.

### MAJ-4: 6 of 18 Error Codes Have No Corresponding Test Scenario

**Files:** `docs/build-guide/17-testing.md`, `integration/flow-service/flow-service-spec.md:656-678`

The flow-service-spec defines 18 error codes. Cross-referencing with test scenarios:

| Error Code | Tested? | Test # |
|---|---|---|
| `AUTH_FAILED` | No | -- |
| `ACCOUNT_NOT_FOUND` | No | -- |
| `COMPONENT_NOT_FOUND` | No | -- |
| `DATAHUB_ERROR` | No | -- |
| `API_RATE_LIMIT` | No | -- |
| `DEPENDENCY_CYCLE` | No | -- |
| `INVALID_REQUEST` | No | -- |
| `PROMOTION_FAILED` | Partially | Test 6 (error recovery) |
| `DEPLOYMENT_FAILED` | No | -- |
| `MISSING_CONNECTION_MAPPINGS` | No | -- |
| `BRANCH_LIMIT_REACHED` | No | -- |
| `SELF_REVIEW_NOT_ALLOWED` | No | -- |
| `ALREADY_REVIEWED` | No | -- |
| `INVALID_REVIEW_STATE` | No | -- |
| `INSUFFICIENT_TIER` | No | -- |
| `TEST_DEPLOY_FAILED` | Partially | Test 10c |
| `HOTFIX_JUSTIFICATION_REQUIRED` | No | -- |
| `INVALID_DEPLOYMENT_TARGET` | No | -- |
| `TEST_PROMOTION_NOT_FOUND` | No | -- |

Only 2 of 18 error codes are partially tested (via side effects, not explicit error code verification). Zero error codes are tested with explicit assertions on the `errorCode` field.

Additionally, Wave 1 teams identified error codes referenced in build guides but absent from the error contract: `MERGE_FAILED` (Team 3 CM7), `MERGE_TIMEOUT` (Team 3 CM7), `CONCURRENT_PROMOTION` (Team 3 CM6), `COMPONENT_LIMIT_EXCEEDED` (Team 2 MAJ-7). These are untestable until added to the spec.

**Impact:** Error handling paths are the most likely to contain bugs (rarely executed, complex state transitions). Without negative test coverage, error codes may return incorrect messages, wrong HTTP status codes, or fail to trigger proper Flow Decision branches.

**Recommendation:** Add a "Negative Testing" section with targeted tests for at least the 6 highest-risk error codes: `MISSING_CONNECTION_MAPPINGS`, `BRANCH_LIMIT_REACHED`, `SELF_REVIEW_NOT_ALLOWED`, `DEPENDENCY_CYCLE`, `INSUFFICIENT_TIER`, and `HOTFIX_JUSTIFICATION_REQUIRED`.

### MAJ-5: Troubleshooting Error Codes Not Aligned with Flow-Service-Spec

**Files:** `docs/build-guide/18-troubleshooting.md`, `integration/flow-service/flow-service-spec.md:656-678`

The troubleshooting guide uses natural-language symptom headings ("Groovy script error: property not found", "Promotion creates duplicate components") rather than error codes. A developer who sees `MISSING_CONNECTION_MAPPINGS` in the Flow dashboard error page has no way to search the troubleshooting guide for this code.

Error codes from the flow-service-spec with no troubleshooting entry:
- `MISSING_CONNECTION_MAPPINGS`
- `BRANCH_LIMIT_REACHED`
- `SELF_REVIEW_NOT_ALLOWED`
- `ALREADY_REVIEWED`
- `INVALID_REVIEW_STATE`
- `DEPENDENCY_CYCLE`
- `INSUFFICIENT_TIER`
- `TEST_DEPLOY_FAILED`
- `HOTFIX_JUSTIFICATION_REQUIRED`
- `INVALID_DEPLOYMENT_TARGET`
- `TEST_PROMOTION_NOT_FOUND`
- `MERGE_FAILED` (referenced in build guide `11-process-d-package-and-deploy.md:117`)

12 of 18+ error codes have no troubleshooting entry. The existing troubleshooting entries cover infrastructure issues (DataHub deployment, HTTP connections, Groovy scripts) but not business logic errors.

**Impact:** Support escalation for business logic errors that could be self-service resolved.

**Recommendation:** Add an "Error Code Reference" subsection to the troubleshooting guide mapping each error code to: cause, user action, and admin action (where applicable).

### MAJ-6: No Operational Runbook, Monitoring Checkpoints, or Escalation Paths

**Files:** `docs/build-guide/17-testing.md`, `docs/build-guide/18-troubleshooting.md`

The testing and troubleshooting guides cover build-time and debugging scenarios but contain no operational readiness content:

1. **No monitoring checkpoints** -- No guidance on what to monitor in production (e.g., PromotionLog error rates, branch count, DataHub record growth, API rate limit utilization, process execution duration).
2. **No escalation paths** -- When troubleshooting fails, there is no "Contact Boomi Support with..." guidance or L1/L2/L3 escalation matrix.
3. **No recovery procedures** -- For data corruption scenarios (duplicate ComponentMapping records, orphaned branches, stuck IN_PROGRESS PromotionLog records), there is no step-by-step recovery runbook.
4. **No capacity planning** -- No guidance on DataHub record limits, branch limits, API token expiration schedules, or process execution time bounds.
5. **No health check** -- The smoke test (lines 1-11) is a one-time build verification, not a recurring health check. No periodic validation procedure exists.

**Impact:** Production operations without runbooks lead to ad-hoc troubleshooting, inconsistent incident response, and longer mean time to recovery (MTTR).

**Recommendation:** Add a "Phase 7: Operational Readiness" section (or separate `23-operational-readiness.md` file) covering: monitoring dashboard setup, health check procedure (daily/weekly), escalation matrix, data recovery runbook for common corruption scenarios, and capacity planning guidelines.

### MAJ-7: Test 8 References Page 9 Which May Not Be Navigable

**Files:** `docs/build-guide/17-testing.md:392-407`, Wave 1 Team 4 MAJ-1

Test 8 (Dev -> Test -> Production Happy Path) step 5 says "Navigate to Page 9 (Production Readiness Queue)." Wave 1 Team 4 MAJ-1 identifies that Page 9 has only one documented entry point: the "View in Production Readiness" button on Page 4 after a successful test deployment. If the tester closes the browser between step 4 and step 5, they may not be able to reach Page 9.

Additionally, Test 8 step 5 says "Verify the test deployment appears in the queue with correct branch age" but does not specify how to verify branch age correctness or what the expected age should be (presumably <1 minute if tests are run sequentially).

**Impact:** Test 8 may be unexecutable if Page 9 navigation is not wired into the sidebar or accessible via direct URL.

**Recommendation:** (1) Update Test 8 to specify the navigation path to Page 9 (either via the Page 4 button or a direct URL). (2) Reference Wave 1 Team 4 MAJ-1 as a prerequisite for this test. (3) Add expected branch age assertion.

---

## Minor Findings

### MIN-1: Build Guide Index Says "7 Test Scenarios" But Testing Has 10 Tests

**Files:** `docs/build-guide/index.md:26`, `docs/build-guide/17-testing.md`

The index says "Smoke test + 7 test scenarios" but the testing file contains Tests 1-10 (10 tests plus a smoke test). Tests 8-10 were added for multi-environment coverage but the index was not updated.

**Recommendation:** Update index.md line 26 to "Smoke test + 10 test scenarios".

### MIN-2: Test 4 Dependency Order Verification Is Manual and Fragile

**Files:** `docs/build-guide/17-testing.md:259`

Test 4 (Full Dependency Tree) line 259 says: "Confirm by checking `lastPromotedAt` timestamps or the PromotionLog `resultDetail` field." This requires manual timestamp comparison across multiple DataHub records, which is error-prone and non-deterministic (timestamps could be equal if components are promoted within the same second).

**Recommendation:** Specify that the `resultDetail` JSON should contain an `order` field or index showing processing sequence, or provide a query that returns records sorted by `lastPromotedAt` for comparison.

### MIN-3: Test Scenarios Use Inconsistent SSO Group Names

**Files:** `docs/build-guide/17-testing.md:269`

Test 5 line 269 says 'member of "Boomi Developers" or "Boomi Admins" SSO group'. Wave 1 Team 4 CRIT-2 identifies that two naming conventions are mixed across the specification (`ABC_BOOMI_FLOW_CONTRIBUTOR` vs `"Boomi Developers"`). The testing guide should use the canonical format to avoid confusion during test execution.

**Recommendation:** Standardize to `ABC_BOOMI_FLOW_CONTRIBUTOR` / `ABC_BOOMI_FLOW_ADMIN` format, consistent with the flow-service-spec tier algorithm.

### MIN-4: No Test Data Cleanup Strategy

**Files:** `docs/build-guide/17-testing.md`

Test 1d (line 91-93) says "Delete the test record via the DataHub UI or API to avoid polluting production data." No other test specifies cleanup. Tests 2-10 create PromotionLog records, ComponentMapping records, promoted components, branches, and Integration Packs. There is no guidance on:
1. Whether tests should be run in a dedicated test account.
2. How to identify and clean up test artifacts.
3. Whether tests are idempotent (can be re-run without conflict).

**Recommendation:** Add a "Test Data Management" section specifying: (a) use a dedicated test dev account, (b) naming convention for test artifacts (e.g., `TEST-` prefix), (c) cleanup script or manual procedure after full suite.

### MIN-5: Test 7 (Browser Resilience) Has No Timing Guidance

**Files:** `docs/build-guide/17-testing.md:363-373`

Test 7 says "While the promotion is executing (before the status page loads), close the browser tab." The timing window depends on Process C execution speed, which varies with dependency tree size. For a simple package (1 component), the window may be <1 second, making this test unreliable.

**Recommendation:** Specify using a package with at least 5-10 components to ensure sufficient execution time for the browser close action.

### MIN-6: Integration Test Ordering vs Build Order

**Files:** `docs/build-guide/17-testing.md`, `.claude/rules/integration-patterns.md:43-54`

The testing guide orders tests by complexity (CRUD -> single promotion -> re-promotion -> full tree -> approval -> error -> resilience -> multi-env). The build order in `integration-patterns.md` specifies process creation order (A0, A, B, C, E, E2, E3, F, G, J, D). These are intentionally different orderings, but no documentation explains why the test order diverges from the build order or confirms that all processes built in Phase 3 are exercised by Phase 6 tests.

**Recommendation:** Add a cross-reference table showing which tests exercise which processes, confirming full coverage.

---

## Observations

### OBS-1: Strong Happy-Path Coverage for Core Promotion Flow

Tests 2-5 provide thorough end-to-end coverage of the core promotion pipeline (Process A -> B -> C -> D). The verification steps include both API-level checks (Component GET, DataHub queries) and UI-level checks (page rendering, status display). The dual Linux/PowerShell command examples are a practical touch for cross-platform teams.

### OBS-2: Multi-Environment Tests (8-10) Are Well-Structured

Tests 8-10 cover the three multi-environment paths (happy path, emergency hotfix, rejection scenarios) with appropriate verification steps. The PromotionLog field assertions (e.g., `targetEnvironment`, `isHotfix`, `testPromotionId` linkage, branch lifecycle) demonstrate deep understanding of the data model. These tests are the strongest multi-environment content in the entire specification.

### OBS-3: Troubleshooting Phase Organization Is Effective

The phase-by-phase organization of `18-troubleshooting.md` mirrors the build guide structure, making it natural for builders to find relevant guidance during each phase. The diagnostic commands (curl/PowerShell) are immediately actionable. Phase 3 troubleshooting is particularly strong, covering specific DPP name mismatches that would otherwise be hours-long debugging sessions.

### OBS-4: Test 6 (Error Recovery) Has Good Retry Semantics

Test 6 uniquely tests the retry/recovery path: promote -> fail -> fix underlying issue -> re-promote. The assertion that previously promoted components show as UPDATE (not duplicated) validates the idempotency guarantees of the ComponentMapping match rules. This is the only test that validates error recovery end-to-end.

---

## Multi-Environment Assessment

### Test Coverage Matrix for Multi-Environment Paths

| Path | Test # | Coverage Quality | Gaps |
|------|--------|-----------------|------|
| Dev -> Test -> Prod (happy path) | Test 8 | Good | Page 9 navigation uncertainty (MAJ-7), no branch age verification details |
| Emergency Hotfix (Dev -> Prod) | Test 9 | Good | No server-side hotfix justification validation test |
| Peer Rejection of Hotfix | Test 10a | Good | No branch cleanup verification on rejection failure |
| Admin Denial of Prod-from-Test | Test 10b | Good | No verification that test deployment record is preserved |
| Test Deployment Failure + Retry | Test 10c | Adequate | Branch preservation on test failure verified, but retry success not fully verified |
| Cancel Test Deployment | None | Missing | Wave 1 Team 2 MAJ-5: no `cancelTestDeployment` action exists |
| Stale Branch Cleanup | None | Missing | 30-day branch warning is UI-only, no backend enforcement or test |
| Process E4 Exclusion Logic | None | Missing | Already-promoted-to-production records should be excluded from Page 9 |

### Branch Lifecycle Testing

The multi-environment tests correctly verify branch lifecycle at key transitions:
- Branch created (Test 8 step 1, verified at step 4)
- Branch preserved after test deploy (Test 8 step 4, explicit `GET /Branch/{branchId}` returns 200)
- Branch deleted after production deploy (Test 8 step 10, explicit `GET /Branch/{branchId}` returns 404)
- Branch deleted on rejection (Test 10a, PromotionLog assertion)

**Gap:** No test verifies behavior when branch deletion fails (network error, API timeout). Wave 1 Team 4 MAJ-7 identifies this as a resource leak risk.

### Branch Limit Consistency

The testing guide does not reference any specific branch limit threshold. Given the 4 conflicting values identified by Wave 1 (10, 15, 18, 20), the testing guide sidesteps the issue entirely. This means:
- No test validates which threshold is enforced.
- No test verifies `BRANCH_LIMIT_REACHED` error behavior.
- No test verifies that branch cleanup (rejection, production deploy, cancel) decrements the count.

### Phase 7 Troubleshooting Gap

The troubleshooting guide ends at Phase 6. All Phase 7 error codes (`TEST_DEPLOY_FAILED`, `HOTFIX_JUSTIFICATION_REQUIRED`, `INVALID_DEPLOYMENT_TARGET`, `TEST_PROMOTION_NOT_FOUND`) and all Phase 7 configuration issues (Page 9 wiring, E4 query setup, hotfix acknowledgment checkbox, test-to-production linkage) have no troubleshooting coverage.

### Overall Multi-Environment Verdict

Multi-environment **test scenarios** are well-designed and cover the three primary paths with appropriate verification steps. The gaps are in **negative testing** (error code verification, self-review prevention, branch limit enforcement) and **operational readiness** (troubleshooting for Phase 7, monitoring, recovery procedures). The most significant testing gap is the complete absence of Process E4 testing, which powers the critical Page 9 (Production Readiness Queue) that serves as the entry point for production-from-test deployments.

---

## Cross-Team Issue Summary

Wave 1 findings that should be caught by tests but currently are not:

| Wave 1 Finding | Testing Gap |
|---|---|
| Team 1 CC-2: queryStatus field name mismatches (`promotionDate` vs `initiatedAt`) | No test validates queryStatus response field names against the model |
| Team 1 CC-3: Build guide lists 3 statuses but model has 11 | No test validates all 11 status transitions |
| Team 2 CRIT-1: No concurrency guard | No concurrency test |
| Team 2 CRIT-2: Branch limit 4 conflicting values | No branch limit test |
| Team 2 MAJ-4: Orphaned branches on rejection | Test 10a checks PromotionLog but not `DELETE /Branch` success |
| Team 2 MAJ-5: No cancel test deployment | No cancel test |
| Team 2 MAJ-6: Step 6 cache reset bug | No test isolates componentMappingCache behavior |
| Team 3 CC1: MergeRequest field name mismatch (`source` vs `sourceBranchId`) | No test validates merge request API call |
| Team 3 CM7: Merge polling parameters undefined | No test validates merge polling behavior |
| Team 4 CRIT-1: React Hook conditional in XmlDiffViewer | No automated UI test for diff viewer |
| Team 4 CRIT-2: SSO group name inconsistency | Tests use wrong SSO group names (MIN-3 above) |
| Team 4 MAJ-1: Page 9 navigation missing | Test 8 assumes Page 9 is reachable (MAJ-7 above) |

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Major | 7 |
| Minor | 6 |
| Observations | 4 |

## Top 5 Recommendations (Priority Order)

1. **Add targeted test scenarios for Processes E2, E3, E4** -- the only processes with zero test coverage (CRIT-1)
2. **Add negative testing section** with explicit error code verification for at least 6 high-risk codes (MAJ-4)
3. **Add Phase 7 troubleshooting section** covering multi-environment error codes and configuration issues (MAJ-3)
4. **Add operational readiness content** -- monitoring, escalation, recovery runbooks (MAJ-6)
5. **Add branch limit enforcement test** to resolve the 4-way inconsistency empirically (MAJ-1)

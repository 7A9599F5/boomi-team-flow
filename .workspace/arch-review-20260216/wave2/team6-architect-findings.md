# Team 6 — Operations/Observability Architect Findings

**Date:** 2026-02-16
**Reviewer:** Operations/Observability Architect
**Scope:** Testing strategy (17-testing.md), troubleshooting documentation (18-troubleshooting.md), flow-service-spec error codes and monitoring section, architecture.md operational considerations, cross-referenced with Team 2 and Team 3 wave-1 findings.

---

## Critical Findings

### CRIT-1: Zero Error Codes Referenced in Troubleshooting Guide

**Files:** `docs/build-guide/18-troubleshooting.md` (all), `integration/flow-service/flow-service-spec.md:656-678`

The troubleshooting guide (150 lines) describes failure scenarios using natural language ("overrideAccount not authorized", "Groovy script error") but does not reference a single `errorCode` from the flow-service-spec's 19-entry error code table. An ops engineer receiving `MISSING_CONNECTION_MAPPINGS`, `BRANCH_LIMIT_REACHED`, `SELF_REVIEW_NOT_ALLOWED`, `INSUFFICIENT_TIER`, `TEST_DEPLOY_FAILED`, `HOTFIX_JUSTIFICATION_REQUIRED`, or `INVALID_DEPLOYMENT_TARGET` has no lookup path in the troubleshooting guide. The two documents exist in parallel without any cross-referencing.

**Impact:** Ops teams will not be able to map runtime error codes to troubleshooting steps. This breaks the primary incident response workflow.

**Recommendation:** Add an "Error Code Quick Reference" section to 18-troubleshooting.md that maps each of the 19 error codes to: (1) root cause, (2) diagnostic steps, (3) resolution actions. Cross-link from the flow-service-spec error table back to the troubleshooting guide.

### CRIT-2: No Monitoring, Alerting, or SLA Specification

**Files:** `integration/flow-service/flow-service-spec.md:712-737` (monitoring section), `docs/architecture.md` (entire file)

The entire system has no defined monitoring strategy, no alerting rules, and no SLAs. The flow-service-spec's "Monitoring and Troubleshooting" section (lines 712-737) contains only 4 generic paragraphs pointing to Boomi's Process Reporting UI with zero specifics on:
- What metrics to track (execution time, failure rate, component count per promotion)
- What thresholds trigger alerts (e.g., >3 consecutive failures, execution time >5 minutes)
- What notification channels to use (email, Slack, PagerDuty)
- What SLAs the system should meet (availability, mean time to promote, branch cleanup SLA)
- What dashboards to build in Process Reporting

The architecture.md has zero operational sections — no "Operations" heading, no "Monitoring" heading, no "Runbooks" reference.

**Impact:** The system will launch without any observability. Failures will only be discovered when users report them via the Flow UI, which is unacceptable for a production promotion system.

**Recommendation:** Create a dedicated `docs/operations.md` or add an operations section to architecture.md covering: (1) key metrics per process, (2) alerting thresholds, (3) dashboards, (4) SLAs, (5) on-call playbook reference. At minimum, define Process Reporting filters and saved views for each of the 12 processes.

---

## Major Findings

### MAJ-1: Testing Guide Covers Only 7 of 12 Processes Explicitly

**Files:** `docs/build-guide/17-testing.md` (all 483 lines)

The testing guide defines 10 tests but only explicitly exercises these processes:
- Process A0/A: implicitly via Flow Dashboard smoke test (line 8-9)
- Process B: implicitly via dependency tree on Page 2 (Test 4, line 209)
- Process C: explicitly via promotion execution (Tests 2, 3, 4)
- Process D: implicitly via deployment (Test 5)
- Process E: implicitly via PromotionLog query (Test 6 verification)
- Process E2/E3: explicitly via peer review workflow (Test 5)
- Process G: NOT explicitly tested (no diff viewer test scenario)
- Process J: NOT explicitly tested (Integration Pack selection assumed but not verified)
- Process F: NOT explicitly tested (no mapping CRUD scenario)
- Process E4: NOT explicitly tested (Test 8 mentions Page 9 but doesn't verify the queryTestDeployments response)

**Missing test scenarios:**
1. **Process G test:** View diff for a CREATE action (expect empty mainXml) and an UPDATE action (expect both XML versions populated). Verify normalize-xml.groovy produces consistent output.
2. **Process J test:** Verify pack listing, packPurpose filter (TEST vs PRODUCTION), and suggestion logic for previously used packs.
3. **Process F test:** Verify mapping query, create (seed a connection mapping), update, and delete. This is critical for admin onboarding.
4. **Process E4 test:** Verify queryTestDeployments returns only TEST_DEPLOYED records with preserved branches, and excludes already-promoted-to-production records.

**Recommendation:** Add Tests 11-14 covering Processes G, J, F, and E4 individually.

### MAJ-2: No Negative/Security Test Scenarios

**Files:** `docs/build-guide/17-testing.md` (all)

The testing guide focuses almost exclusively on happy-path and a single error-recovery scenario (Test 6). Critical negative tests are missing:

1. **Self-review prevention test:** Verify that a user cannot peer-review their own promotion (error code `SELF_REVIEW_NOT_ALLOWED`)
2. **Double-review prevention test:** Submit a peer review on an already-reviewed promotion (error code `ALREADY_REVIEWED`)
3. **Tier enforcement test:** Call `executePromotion` with a READONLY-tier user's SSO groups (error code `INSUFFICIENT_TIER`)
4. **Missing connection mappings test:** Promote a component with an unmapped connection (error code `MISSING_CONNECTION_MAPPINGS`)
5. **Branch limit test:** Verify behavior when approaching the 15-branch threshold (error code `BRANCH_LIMIT_REACHED`)
6. **Invalid deployment target test:** Send `deploymentTarget="STAGING"` (error code `INVALID_DEPLOYMENT_TARGET`)
7. **Concurrent promotion test:** Team 2 CRIT-1 identified this gap — two simultaneous promotions of overlapping components

**Impact:** Without negative tests, the system's error handling and authorization enforcement are untested. Bugs in error paths will only surface in production.

**Recommendation:** Add a "Negative Test Suite" section (Tests 11+) covering each error code with explicit expected behavior.

### MAJ-3: Troubleshooting Guide Missing Entire Phases and Error Scenarios

**Files:** `docs/build-guide/18-troubleshooting.md` (all 150 lines)

The troubleshooting guide is organized by build phase (Phases 1-6) but has significant gaps:

**Missing scenarios:**
1. **Multi-environment deployment failures:** No troubleshooting for TEST_DEPLOY_FAILED, test-to-production transition failures, or hotfix-specific issues. These are Phase 7 features with zero troubleshooting coverage.
2. **Peer review workflow failures:** No guidance for SELF_REVIEW_NOT_ALLOWED, ALREADY_REVIEWED, or INVALID_REVIEW_STATE errors.
3. **Branch lifecycle failures:** No guidance for BRANCH_LIMIT_REACHED, orphaned branches (Team 2 MAJ-4), or stale test deployment branches.
4. **Concurrency errors:** No guidance for concurrent promotion conflicts (Team 2 CRIT-1).
5. **DataHub connector failures:** Generic mention of "DataHub error" but no specific diagnostic steps for DataHub connector timeout, auth failure, or model schema mismatch.
6. **Rate limiting cascading failures:** The 429 entry (line 47-48) mentions retry logic but doesn't cover cascading failure scenarios where a large promotion exceeds budget.

**Recommendation:** Add Phase 7 troubleshooting section and expand Phase 3/4/5 sections with the missing scenarios listed above.

### MAJ-4: No Runbook or Operational Playbook

**Files:** All docs/ files

There is no operational runbook or playbook document. Critical operational procedures are undocumented:

1. **Branch cleanup procedure:** How to identify and delete orphaned branches (requires Platform API query + manual delete)
2. **DataHub record cleanup:** How to delete duplicate or corrupted golden records
3. **API token rotation:** The spec mentions 90-day rotation (flow-service-spec.md:697) but no step-by-step procedure
4. **Atom restart procedure:** When and how to restart the Public Cloud Atom (if even possible for public cloud atoms)
5. **Capacity planning:** No guidance on how many concurrent promotions the system can handle, or branch slot forecasting
6. **Escalation path:** Who to contact for Boomi platform issues vs. application issues
7. **Backup and recovery:** No guidance on DataHub data backup or recovery from corrupted state

**Impact:** Without runbooks, operational support requires tribal knowledge. Handoff to a new ops team will be high-friction.

**Recommendation:** Create `docs/operations-runbook.md` with step-by-step procedures for the above scenarios.

### MAJ-5: Testing Guide Has No Performance/Load Validation

**Files:** `docs/build-guide/17-testing.md`

The testing guide has zero performance testing:

1. **No load test:** What happens when 5 developers promote simultaneously?
2. **No large dependency tree test:** Test 4 mentions "a process with dependencies" but doesn't specify a minimum complexity (e.g., 20+ components).
3. **No duration benchmarks:** The flow-service-spec documents typical operation durations (lines 621-629) — e.g., `executePromotion: 30-120 seconds` — but the testing guide doesn't validate these expectations.
4. **No branch slot stress test:** No test for approaching the 15-branch soft limit with multiple concurrent test deployments.

**Impact:** Performance issues will only surface under production load, when they are most costly.

**Recommendation:** Add a "Performance Validation" section with: (a) single-user large promotion test (50+ components), (b) concurrent promotion test (3+ simultaneous users), (c) branch slot saturation test.

### MAJ-6: Process Reporting Configuration Not Specified

**Files:** `integration/flow-service/flow-service-spec.md:716-718`, `docs/build-guide/18-troubleshooting.md:94`

The monitoring section says "Navigate to Process Reporting and filter by `PROMO - FSS Op - *`" but does not specify:

1. **Saved views:** No instructions for creating saved Process Reporting views for each process
2. **Retention settings:** No guidance on log retention for audit compliance
3. **Structured logging:** The Groovy scripts use `logger.info()` and `logger.severe()` but there is no standardized log format (no correlation ID/promotionId in log messages for tracing)
4. **Cross-process correlation:** No guidance on tracing a user's promotion flow across processes A->B->C->D (the `promotionId` is the natural correlation key but this is not documented as an ops practice)

**Recommendation:** (1) Add a "Monitoring Setup" section to the build guide or architecture doc. (2) Define a standard log format: `[PROMO] [{processCode}] [{promotionId}] {message}`. (3) Document saved view configurations for Process Reporting.

---

## Minor Findings

### MIN-1: Troubleshooting Diagnostic Commands Use Placeholder Credentials

**Files:** `docs/build-guide/18-troubleshooting.md:16-30`, `docs/build-guide/17-testing.md:23-29`

All curl/PowerShell commands use literal `BOOMI_TOKEN.user@company.com:your-api-token` placeholders. While understandable for documentation, there is no note about environment variable substitution or a secrets management practice for ops workflows. An ops engineer copy-pasting these commands will need to manually replace 4+ placeholders per command.

**Recommendation:** Add a note at the top of both files about setting environment variables (e.g., `export BOOMI_AUTH="BOOMI_TOKEN.user@company.com:$API_TOKEN"`) and use `$BOOMI_AUTH` in examples.

### MIN-2: Test Cleanup Not Enforced

**Files:** `docs/build-guide/17-testing.md:91-93`

Test 1d says "Delete the test record via the DataHub UI or API to avoid polluting production data" but provides no cleanup command. Tests 2-10 do not mention cleanup at all. Promoted test components, PromotionLog records, and ComponentMapping records from testing will persist.

**Recommendation:** Add a "Test Cleanup" section at the end of 17-testing.md with specific cleanup commands for each test artifact.

### MIN-3: Inconsistent Listener Count Between Documents

**Files:** `docs/build-guide/18-troubleshooting.md:106,111`, `integration/flow-service/flow-service-spec.md:521-533`

The troubleshooting guide at line 106 lists 11 FSS operations, and line 111 says "All 11 processes should appear as active listeners." The flow-service-spec at lines 521-533 lists 12 operations (including `QueryTestDeployments`). This is a Phase 7 desynchronization — the troubleshooting guide was not updated for the 12th message action.

**Recommendation:** Update line 106 and 111 to reference 12 operations and add `PROMO - FSS Op - QueryTestDeployments` to the list.

### MIN-4: No Health Check Endpoint

**Files:** `integration/flow-service/flow-service-spec.md` (absent)

There is no health check or ping endpoint defined in the Flow Service specification. A basic `healthCheck` message action returning `{success: true, version: "1.1.0", timestamp: "..."}` would enable basic availability monitoring without requiring end-to-end promotion.

**Recommendation:** Add a 13th message action `healthCheck` that returns system status, version, and basic DataHub/API connectivity status.

### MIN-5: Smoke Test Insufficient for Operational Validation

**Files:** `docs/build-guide/17-testing.md:3-11`

The "5-Minute Smoke Test" (3 steps) validates DataHub, Flow Service, and Flow Dashboard at a surface level but does not confirm:
1. All 12 listeners are active (only tests 1 of 12)
2. The `primaryAccountId` configuration value is set
3. DataHub models for all 3 models are deployed (only queries ComponentMapping)

**Recommendation:** Expand the smoke test to: (a) verify all 12 listeners via Runtime Management, (b) test at least one message action from each process category (data query, promotion, review), (c) verify all 3 DataHub models.

---

## Observations

### OBS-1: Strong Diagnostic Command Pattern
The troubleshooting guide provides curl/PowerShell diagnostic commands for Phases 1-2, which is excellent for cross-platform ops support. This pattern should be extended to Phases 3-6 and the multi-environment workflow.

### OBS-2: Testing Guide Multi-Environment Coverage is Solid (Tests 8-10)
Tests 8, 9, and 10 cover the dev->test->production happy path, emergency hotfix path, and rejection scenarios respectively. These are thorough for the multi-environment workflow and include specific PromotionLog field verification. This is the strongest section of the testing guide.

### OBS-3: Architecture's Error Handling Design is Ops-Friendly
The per-component failure isolation with SKIPPED/FAILED marking, the dual Try/Catch pattern in Process C, and the branch cleanup on failure are all good operational patterns that limit blast radius. The `componentsFailed` and `resultDetail` fields in PromotionLog enable precise failure diagnosis.

### OBS-4: Typical Operation Durations Documented
The flow-service-spec (lines 621-629) documents expected operation durations for each message action. This is a good baseline for SLA definition and alerting threshold configuration, once monitoring is actually implemented.

---

## Multi-Environment Assessment

### Testing Coverage for Multi-Env

| Path | Test Coverage | Gaps |
|------|--------------|------|
| Dev -> Test -> Production (happy path) | Test 8: Comprehensive | Test deployment verification is good; production transition well-covered |
| Emergency Hotfix (dev -> production) | Test 9: Comprehensive | Hotfix badge visibility, justification display, acknowledgment checkbox all verified |
| Peer rejection of hotfix | Test 10a: Good | Branch cleanup verified; rejection email check included |
| Admin denial of production from test | Test 10b: Good | Test deployment record preservation verified |
| Test deployment failure with retry | Test 10c: Good | Branch preservation on test failure verified |
| Stale test deployment cleanup | NOT TESTED | No test for branches >30 days or the cancel workflow |
| Branch slot exhaustion during multi-env | NOT TESTED | No test for what happens when 15+ branches exist from parallel test deployments |
| queryTestDeployments filtering | NOT TESTED | Test 8 mentions Page 9 but doesn't verify the E4 response shape or exclusion logic |

### Operational Readiness for Multi-Env

| Criteria | Status | Notes |
|----------|--------|-------|
| Troubleshooting for multi-env errors | MISSING | No Phase 7 troubleshooting section |
| Branch lifecycle monitoring | MISSING | UI-only (Page 9) with no backend enforcement or alerting |
| Test-to-production traceability | GOOD | `testPromotionId` linkage in PromotionLog |
| Hotfix audit trail | GOOD | `isHotfix` + `hotfixJustification` in PromotionLog |
| Stale branch cleanup automation | MISSING | Identified by Team 2 MAJ-5 and Team 3 architecture observations |

---

## Cross-Reference with Wave 1 Findings

### Team 2 (Integration Engine) Overlap

| Team 2 Finding | Ops Impact | This Review |
|----------------|-----------|-------------|
| CRIT-1: No concurrency guard | Concurrent promotions create data corruption; ops will see duplicate mappings with no diagnostic path | MAJ-2 (no negative test for concurrency) |
| CRIT-4: E2/E3 missing build guide | No build instructions means no operational knowledge of peer review internals | MAJ-1 (E2/E3 testing exists but process internals untested) |
| MAJ-4: Orphaned branches on rejection | Branch slot exhaustion; no cleanup procedure documented | MAJ-3 (no troubleshooting for branch lifecycle), MAJ-4 (no runbook) |
| MAJ-5: No cancelTestDeployment | Stale branches accumulate with no cleanup mechanism | Multi-env assessment gap |
| MIN-1: DPP catalog ~40% complete | Ops cannot troubleshoot DPP issues without knowing valid DPP names | Compounds MAJ-6 (structured logging gap) |

### Team 3 (Platform API) Overlap

| Team 3 Finding | Ops Impact | This Review |
|----------------|-----------|-------------|
| CC1: MergeRequest field name mismatch | Process D will fail at merge step; ops will see 400 errors with no specific troubleshooting entry | MAJ-3 (no troubleshooting for merge failures) |
| CM7: Merge polling parameters undefined | Merge could time out silently; no MERGE_TIMEOUT error code in troubleshooting | MAJ-3 (no merge-related troubleshooting) |
| CC2: Branch limit 4 conflicting values | Ops teams will not know the correct threshold for capacity planning | MAJ-5 (no performance/capacity testing) |

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Major | 6 |
| Minor | 5 |
| Observations | 4 |

## Top 5 Recommendations (Priority Order)

1. **Create error code cross-reference in troubleshooting guide** — Map all 19 error codes to diagnostic steps and resolutions (CRIT-1)
2. **Define monitoring strategy** — Metrics, alerting thresholds, dashboards, SLAs (CRIT-2)
3. **Add negative test scenarios** — Cover all error codes and authorization enforcement (MAJ-2)
4. **Create operations runbook** — Branch cleanup, token rotation, capacity planning, escalation (MAJ-4)
5. **Extend troubleshooting for multi-environment workflows** — Phase 7 scenarios, branch lifecycle, merge failures (MAJ-3)

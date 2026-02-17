# Team 8 Consensus: Build Guide & Operations

**Team**: Build Guide & Operations (Team 8)
**Reviewers**: Implementation Sequencing Expert, E2E Testing Architect, Devil's Advocate
**Date**: 2026-02-16
**Scope**: Build guide completeness, sequencing correctness, testing coverage, troubleshooting alignment, multi-environment integration

---

## Critical Findings

### CRIT-1: Processes E2 and E3 Have Zero Build Guide Content AND Zero Test Coverage

**Files**: `docs/build-guide/` (no dedicated content), `docs/build-guide/17-testing.md` (no isolated tests)

**Consensus**: Unanimous. Processes E2 (Query Peer Review Queue) and E3 (Submit Peer Review) are the only two processes in the system with neither build guide content nor targeted test scenarios. They appear in the build order checklist (`13-process-g-component-diff.md:114-115`), the Flow Service table (`14-flow-service.md:23-24`), the inventory (`19-appendix-naming-and-inventory.md:76-79`), and the process letter code reference (`integration-patterns.md`), confirming they are required components. E3 is particularly complex -- it must implement self-review prevention, state validation, and update 4+ PromotionLog fields.

The testing gap compounds the build gap: even if a developer improvises the build, they have no test scenarios to validate self-review prevention (`SELF_REVIEW_NOT_ALLOWED`), double-review prevention (`ALREADY_REVIEWED`), or invalid-state handling (`INVALID_REVIEW_STATE`). The self-review prevention mechanism is a core security control with defense-in-depth requirements (backend exclusion in E2 + UI Decision step fallback).

**Recommendation**: Create dedicated build guide sections for E2 and E3 with shape-by-shape instructions. Add test scenarios: (a) E2 query with self-review exclusion verification, (b) E3 approve/reject with error code assertions, (c) self-review prevention negative test.

**Impact**: The 2-layer approval workflow cannot be built or verified from the guide alone.

---

### CRIT-2: Central FSS Operations Table Lists 7 of 12, Process Build Order Checklist Lists 11 of 12

**Files**: `docs/build-guide/04-process-canvas-fundamentals.md:107-115`, `docs/build-guide/13-process-g-component-diff.md:109-122`, `docs/build-guide/00-overview.md:81`

**Consensus**: Confirmed by all three reviewers. Two related gaps:

1. The FSS operations table at `04-process-canvas-fundamentals.md:107-115` lists only 7 operations (through ManageMappings). Operations for QueryPeerReviewQueue, SubmitPeerReview, QueryTestDeployments, ListIntegrationPacks, and GenerateComponentDiff are missing from this central table. G, J, and E4 document their FSS operations inline in their respective build guide files, but E2 and E3 have no FSS operation instructions anywhere.

2. The build order checklist at `13-process-g-component-diff.md:109-122` lists 11 processes. Process E4 (Query Test Deployments) is missing, despite being listed in the overview build order (`00-overview.md:81`) and having build content at `07-process-e-status-and-review.md:68-131`. The checklist's footer says "all eleven processes" when the system has 12.

**Recommendation**: (a) Add all 12 FSS operations to the central table (or add cross-references for those documented inline). (b) Add E4 to the build order checklist. Update footer to "all twelve processes."

**Impact**: Builders following the checklist will skip E4 entirely. Builders using only the central FSS table will miss 5 operations.

---

## Major Findings

### MAJ-1: Branch Limit Threshold Inconsistency (10 vs 15)

**Files**: `docs/build-guide/10-process-c-execute-promotion.md:79`, `docs/build-guide/02-http-client-setup.md:307`, `docs/architecture.md:101-104,284`

**Consensus**: After DA review, the 4-way conflict reduces to one actual inconsistency: `02-http-client-setup.md:307` says "10-branch limit" while every other source uses 15 as the operational threshold. The 20 is the Boomi platform hard limit (a fact). The 18 in architecture.md is explicitly noted as a historical value that was changed to 15.

The testing guide has no test scenario for `BRANCH_LIMIT_REACHED`, and the troubleshooting guide has no entry for this error code.

**Recommendation**: (a) Fix `02-http-client-setup.md:307` from "10" to "15". (b) Document in one canonical location: platform limit = 20, operational threshold = 15. (c) Add a test scenario for branch limit enforcement. (d) Add a troubleshooting entry for `BRANCH_LIMIT_REACHED`.

### MAJ-2: Process C Step 6 Resets componentMappingCache, Erasing Connection Mappings

**Files**: `docs/build-guide/10-process-c-execute-promotion.md:158-159`

**Consensus**: Unanimous. Step 5.6 loads connection mappings into `componentMappingCache` via `validate-connection-mappings.groovy`. Step 6 then sets `componentMappingCache = {}`, erasing these pre-loaded mappings. Step 8's `rewrite-references.groovy` subsequently cannot find connection mappings to rewrite.

**Recommendation**: Remove the `componentMappingCache = {}` reset at step 6. The cache must retain connection mappings from step 5.6.

### MAJ-3: Profile and Component Count Inconsistencies Across Documents

**Files**: `docs/build-guide/00-overview.md:28-43`, `docs/build-guide/04-process-canvas-fundamentals.md:32-49`, `docs/build-guide/19-appendix-naming-and-inventory.md:27`, `docs/build-guide/03-datahub-connection-setup.md:160-168`

**Consensus**: Multiple confirmed count mismatches:

| Item | BOM (00-overview) | Canvas Fundamentals (04) | Inventory (19) | Actual Need |
|------|-------------------|--------------------------|-----------------|-------------|
| JSON Profiles | 24 | 14 (7 processes x 2) | 22 | 24 (12 processes x 2) |
| HTTP Client Ops | 12 | -- | 9 (Phase 2 checklist) | 19+ (per process audit) |
| Total Components | 67 | -- | 51 (title) / 71 (items) | Needs reconciliation |
| PromotionLog Fields | 34 | -- | -- | 35 (counted) |

The HTTP Client operations gap is the most impactful: the BOM says 12, the table in `02-http-client-setup.md` lists 15, but processes reference at least 4 additional operations (QUERY IntegrationPack, ReleaseIntegrationPack, AddToIntegrationPack, GET MergeRequest for polling).

**Recommendation**: Create one canonical BOM and ensure all reference counts match. Add the 4+ missing HTTP Client operation definitions.

### MAJ-4: Duplicate Navigation Wiring (Step 5.4) with Conflicting Content

**Files**: `docs/build-guide/15-flow-dashboard-developer.md:219-243`, `docs/build-guide/16-flow-dashboard-review-admin.md:109-130`

**Consensus**: Step 5.4 appears in both files with different content. Version 1 (developer file) has 18 rules including Page 9 wiring, test/production mode distinctions, and multi-environment navigation. Version 2 (review/admin file) has 16 rules, is missing Page 9, and uses different button text for step 5 ("Submit for Integration Pack Deployment" vs "Continue to Deployment").

**Recommendation**: Remove the duplicate from `16-flow-dashboard-review-admin.md`. Keep Version 1 in `15-flow-dashboard-developer.md` as the canonical navigation spec.

### MAJ-5: Testing Guide Has Zero Explicit Error Code Assertions

**Files**: `docs/build-guide/17-testing.md`, `integration/flow-service/flow-service-spec.md:656-678`

**Consensus**: Of 18+ defined error codes, zero are tested with explicit `errorCode` field assertions. Test 6 (error recovery) and Test 10c (test deploy failure) test error-adjacent scenarios but never assert the specific error code value. The highest-risk untested error codes are: `MISSING_CONNECTION_MAPPINGS`, `BRANCH_LIMIT_REACHED`, `SELF_REVIEW_NOT_ALLOWED`, `DEPENDENCY_CYCLE`, `HOTFIX_JUSTIFICATION_REQUIRED`, and `INSUFFICIENT_TIER`.

**Recommendation**: Add a "Negative Testing" section with targeted tests for at least the 6 highest-risk error codes.

### MAJ-6: Troubleshooting Guide Missing Phase 7 / Multi-Environment Coverage

**Files**: `docs/build-guide/18-troubleshooting.md`

**Consensus**: The troubleshooting guide covers Phases 1-6 (lines 3-147) with no Phase 7 section. Multi-environment error codes (`TEST_DEPLOY_FAILED`, `HOTFIX_JUSTIFICATION_REQUIRED`, `INVALID_DEPLOYMENT_TARGET`, `TEST_PROMOTION_NOT_FOUND`) and configuration issues (Page 9 wiring, E4 query setup, hotfix acknowledgment checkbox) have no troubleshooting entries. Additionally, the troubleshooting guide uses symptom-based headings rather than error codes, making it unsearchable when developers see error codes in the Flow UI.

**Recommendation**: (a) Add a Phase 7 troubleshooting section. (b) Add an error code quick-reference table mapping each code to its troubleshooting entry.

### MAJ-7: Troubleshooting Says "11 Operations" When System Has 12

**Files**: `docs/build-guide/18-troubleshooting.md:106`

**Consensus**: The troubleshooting section says "Verify all 11 operations are listed" and enumerates 11 FSS operations. `QueryTestDeployments` (E4) is missing. The Flow Service table at `14-flow-service.md:12-27` correctly lists 12.

**Recommendation**: Update to 12 and add `PROMO - FSS Op - QueryTestDeployments`.

---

## Minor Findings

### MIN-1: Process E4 Exclusion Groovy Script Missing

**Files**: `docs/build-guide/07-process-e-status-and-review.md:107-109`

Step 4 of Process E4's canvas guide describes the exclusion logic in prose only: "Groovy script that filters out test deployments where a matching PRODUCTION record already exists." The 6-step canvas guide, profiles, FSS operation, error handling, and verification steps are all present -- only the Groovy script body is missing. A competent developer could implement this from the description, but it is the most complex logic in E4.

**Recommendation**: Provide the Groovy script or detailed pseudocode for the exclusion-join logic.

### MIN-2: Build Order Inconsistencies Across 3 Locations

**Files**: `docs/build-guide/00-overview.md:80-81`, `docs/build-guide/13-process-g-component-diff.md:109-122`, `.claude/rules/integration-patterns.md:43-54`

Three different build orders exist: (a) `integration-patterns.md` uses dependency-based order (A0, A, B, C, E, E2, E3, F, G, J, D); (b) `00-overview.md` uses simplest-first pedagogical order including E4; (c) the checklist uses simplest-first order excluding E4. The pedagogical order (simplest-first, F as "hello world") is intentionally different from the dependency order, but this should be explicitly stated.

**Recommendation**: Add a note explaining the two orderings serve different purposes. Add E4 to the checklist.

### MIN-3: Index Says "7 Test Scenarios" but Testing Has 10

**Files**: `docs/build-guide/index.md:26`, `docs/build-guide/17-testing.md`

The index says "Smoke test + 7 test scenarios" but the testing file contains Tests 1-10. Tests 8-10 were added for multi-environment coverage.

**Recommendation**: Update to "Smoke test + 10 test scenarios."

### MIN-4: SSO Group Names Inconsistent Between Tests and Spec

**Files**: `docs/build-guide/17-testing.md:269`, `docs/build-guide/16-flow-dashboard-review-admin.md:100-101`

Tests and troubleshooting use "Boomi Developers"/"Boomi Admins" while the canonical SSO group format is `ABC_BOOMI_FLOW_CONTRIBUTOR`/`ABC_BOOMI_FLOW_ADMIN`. Both conventions appear in the codebase without explanation.

**Recommendation**: Either standardize to one format or explicitly note that "Boomi Developers" is the user-friendly display name for `ABC_BOOMI_FLOW_CONTRIBUTOR`.

### MIN-5: Page Count Ambiguity (8 vs 9 Pages)

**Files**: `docs/build-guide/00-overview.md:42`, `docs/build-guide/index.md:25-26`, `docs/build-guide/15-flow-dashboard-developer.md:197`

BOM says 9 pages. Index says "Pages 1-4" and "Pages 5-8, SSO config" (implying 8). Actual count is 9: Pages 1-4 + Page 9 in developer swimlane, Pages 5-6 in peer review, Pages 7-8 in admin.

**Recommendation**: Update index description to note Page 9 is in the developer swimlane file.

### MIN-6: DPP Catalog Covers Only 3 of 12 Processes

**Files**: `docs/build-guide/20-appendix-dpp-catalog.md`

The DPP catalog documents Global, Process B, and Process C DPPs. Nine processes (A0, A, D, E, E2, E3, E4, F, G, J) have no DPP documentation.

**Recommendation**: Add DPP tables for all processes.

### MIN-7: API Reference Appendix Covers Only 9 of 19+ Endpoints

**Files**: `docs/build-guide/21-appendix-platform-api-reference.md:18-28`

Missing: Branch operations (4), MergeRequest operations (3), QUERY IntegrationPack, ReleaseIntegrationPack, AddToIntegrationPack, tilde-syntax URL variants.

**Recommendation**: Complete the API reference.

### MIN-8: No Test Data Cleanup Strategy

**Files**: `docs/build-guide/17-testing.md`

Only Test 1d specifies cleanup. Tests 2-10 create PromotionLog records, ComponentMapping records, promoted components, branches, and Integration Packs with no cleanup guidance.

**Recommendation**: Add a "Test Data Management" section.

---

## Observations

### OBS-1: Process C Build Guide Is the Gold Standard

Process C at `10-process-c-execute-promotion.md` (375 lines, 23 numbered steps) is the most thorough build guide file. It covers the full promotion loop, branch lifecycle, connection validation, mapping cache, dual try/catch, and three verification scenarios. Other processes should aspire to this level of detail.

### OBS-2: Pedagogical Build Order (Simplest-First) Is Well-Chosen

Starting with Process F as a "hello world" template process is an excellent pedagogical decision. The dependency-based order in `integration-patterns.md` serves a different purpose (runtime dependencies). Both are valid.

### OBS-3: Dual-Format API Examples Are Practical

Every verification command appears in both curl (Linux/macOS) and PowerShell (Windows) format, making the guide accessible across platforms. This is consistently applied across all 10 test scenarios.

### OBS-4: Multi-Environment Tests (8-10) Are Well-Structured

Tests 8-10 cover the three primary multi-environment paths with appropriate PromotionLog field assertions and branch lifecycle verification. These are among the strongest tests in the guide.

### OBS-5: Phase 6 Testing Has Strong Happy-Path Coverage

Tests 2-5 provide thorough end-to-end coverage of the core promotion pipeline, including verification at both API and UI levels.

---

## Areas of Agreement (All 3 Reviewers)

1. **E2/E3 gap is the most critical issue**: Zero build content AND zero test coverage for two processes that implement the core security control (self-review prevention and 2-layer approval).
2. **Cache reset at Process C step 6 is a confirmed bug**: The `componentMappingCache = {}` reset erases pre-loaded connection mappings.
3. **Component counts need reconciliation**: Multiple conflicting counts across BOM, canvas fundamentals, inventory checklist, and Phase 2 checklist create confusion.
4. **Duplicate navigation wiring is harmful**: Two conflicting versions of Step 5.4 will confuse builders.
5. **Troubleshooting needs error code alignment**: Symptom-based headings make the guide unsearchable by error code.
6. **Negative testing is absent**: Zero of 18+ error codes are explicitly tested.

---

## Unresolved Debates

### Branch Limit Severity

- **Expert**: Rated CRITICAL (4 conflicting values)
- **DA**: Downgraded to MAJOR (actual conflict is "10 vs 15" only; 18 is historical, 20 is platform fact)
- **Resolution**: MAJOR. The "10" in HTTP client setup is clearly wrong and must be fixed. The 15/20 distinction is well-documented in architecture.md. The "18" is clearly labeled as a prior value. One document needs fixing, not a systemic inconsistency.

### Process E4 Severity

- **Expert**: Rated CRITICAL (missing from checklist + no Groovy script)
- **DA**: Downgraded to MAJOR (has 6-step canvas, profiles, FSS operation, verification -- only script body missing)
- **Resolution**: Split into two: checklist omission (MIN-2, folded in) + missing Groovy script (MIN-1). E4 has substantially more content than E2/E3.

### Operational Readiness Scope

- **Architect**: Rated MAJOR (no monitoring, escalation, recovery runbooks)
- **DA**: Downgraded to MINOR/Observation (out of scope for a build guide)
- **Resolution**: Observation. Valid recommendation for a future document but not a gap in the build guide per se. A build guide's scope is construction, not operations.

---

## Multi-Environment Assessment

### Strengths

1. **Process D 3-mode logic**: Complete at `11-process-d-package-and-deploy.md` with TEST, PRODUCTION-from-test, and HOTFIX branches fully documented with shape-by-shape instructions.
2. **PromotionLog model**: All 8 multi-env fields present in the model spec and Phase 1 build guide.
3. **Page 9**: Complete build guide at `15-flow-dashboard-developer.md:197-217` with data grid, branch age color coding, stale warning, and production promotion flow.
4. **Process E4**: 6-step canvas guide with profiles, FSS operation, error handling, and verification at `07-process-e-status-and-review.md:68-131`.
5. **Flow Service**: All 12 actions including `queryTestDeployments` listed at `14-flow-service.md:12-27`.
6. **Testing**: Tests 8-10 cover the three primary multi-env paths with PromotionLog field assertions and branch lifecycle verification.
7. **Branch lifecycle**: Branch preservation for TEST mode and deletion for PRODUCTION mode clearly documented in Process D.

### Gaps

1. **Process E4 exclusion script**: The Groovy script body for filtering already-promoted records is described in prose only (MIN-1).
2. **No Phase 7 troubleshooting**: Multi-env error codes have no troubleshooting entries (MAJ-6).
3. **Branch cleanup on rejection/denial**: Architecture doc says branches are deleted on all terminal paths, but no build guide step implements deletion on peer rejection or admin denial outside of Process D's merge flow.
4. **No cancelTestDeployment action**: Architecture doc calls it a "future consideration." Without it, stale test branches accumulate.
5. **Page 9 navigation**: Version 1 wiring includes it; Version 2 does not. Test 8 assumes Page 9 is reachable without specifying the path.
6. **E4 missing from build checklist**: A builder following the checklist would skip E4, which powers Page 9.

### Overall Verdict

Multi-environment functionality is **architecturally well-integrated** into the existing build guide files rather than isolated in a separate phase. The inline approach works well for Process D, Page 9, and the PromotionLog model. The main risks are: (a) a builder may miss E4 because it is absent from the checklist, (b) the E4 exclusion script requires implementation beyond what the guide provides, and (c) troubleshooting for multi-env error codes is absent. The testing coverage for multi-env paths (Tests 8-10) is strong for happy paths but lacks negative tests for multi-env-specific error codes.

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Major | 7 |
| Minor | 8 |
| Observations | 5 |

## Top 5 Recommendations (Priority Order)

1. **Create E2/E3 build guide content + test scenarios** (CRIT-1): The only processes with zero build instructions and zero test coverage. Blocks the 2-layer approval workflow and self-review prevention verification.
2. **Fix cache reset bug in Process C step 6** (MAJ-2): Remove `componentMappingCache = {}` at step 6. Connection mappings loaded by step 5.6 must persist into the promotion loop.
3. **Reconcile all component counts** (MAJ-3): Create one canonical BOM. Add the 4+ missing HTTP Client operations. Align profile counts, inventory totals, and field counts.
4. **Add negative testing + Phase 7 troubleshooting** (MAJ-5, MAJ-6): Test at least 6 high-risk error codes explicitly. Add troubleshooting entries for all multi-env error codes.
5. **Remove duplicate navigation wiring** (MAJ-4): Keep Version 1 (18 rules, includes Page 9) and remove Version 2 from the review/admin file.

# Team 8 -- Devil's Advocate Response: Build Guide & Operations

**Reviewer**: Devil's Advocate
**Date**: 2026-02-16
**Scope**: Challenge and verify findings from Implementation Sequencing Expert and E2E Testing Architect

---

## Methodology

Verified each finding against source files. Key verification areas:
1. Branch limit threshold values across documents
2. Process E2/E3 build guide coverage
3. Build order checklist completeness (E4 presence)
4. Process C step 6 cache reset
5. Troubleshooting "11 operations" claim
6. Phase 7 file existence and multi-env content distribution
7. Testing coverage for E2/E3/E4
8. Navigation wiring duplication

---

## Expert Findings Verification

### CRIT-1: E2 and E3 Have Zero Build Guide Content -- CONFIRMED

Verified: No dedicated build guide file exists for E2 or E3. The build order checklist at `13-process-g-component-diff.md:114-115` lists them as items #4 and #5 with FSS operation names, but no shape-by-shape build instructions exist anywhere. The Flow Service table at `14-flow-service.md:23-24` correctly lists their operations, confirming they are expected to exist. The `04-process-canvas-fundamentals.md:107-115` FSS operations table lists only 7 of 12 operations and does NOT include E2 or E3.

**DA verdict**: Fully confirmed. This is genuinely critical -- a builder cannot construct these processes from the guide.

### CRIT-2: Process E4 Build Guide Lacks Groovy Script -- CONFIRMED with NUANCE

Verified at `07-process-e-status-and-review.md:107-109`: Step 4 describes the exclusion logic in prose only ("Groovy script that filters out test deployments where a matching PRODUCTION record already exists"). The 6-step canvas instructions ARE present (lines 91-117), which is more than E2/E3 have.

**DA challenge**: The expert rates this as CRITICAL. I would downgrade to MAJOR. Unlike E2/E3 which have ZERO content, E4 has a complete 6-step canvas guide with profiles, FSS operation, error handling, and verification steps. The missing piece is a single Groovy script body. A competent Boomi developer could implement the exclusion logic from the prose description. The expert's claim that E4 is "missing from the checklist" is confirmed -- `13-process-g-component-diff.md:109-122` lists 11 processes, not 12; E4 is absent.

**DA verdict**: Downgrade to MAJOR. E4 has substantial build content; only the Groovy script body is missing. The checklist omission is a separate Minor issue.

### CRIT-3: Branch Limit -- 4 Conflicting Values -- CONFIRMED

Verified all 4 values:
- `10-process-c-execute-promotion.md:79`: `>= 15` (operational threshold)
- `02-http-client-setup.md:307`: "10-branch limit" (WRONG)
- `docs/architecture.md:284`: "lowered from 18 to 15" (historical context)
- `docs/architecture.md:101-104`: "20 branches" (Boomi hard limit), "if >= 15" (operational threshold)

**DA challenge**: This is 3 distinct values, not 4. The "20" is the Boomi platform hard limit (a fact, not a configuration choice). The "18" is a historical value that was explicitly changed to 15 (architecture.md says "lowered from 18 to 15"). The "15" is the current operational threshold, consistently used in the build guide and architecture doc. The ONLY actual inconsistency is the "10" in `02-http-client-setup.md:307`, which directly contradicts the intended 15. So the actual conflict is "10 vs 15" -- not a 4-way confusion.

**DA verdict**: Confirmed as a real issue but the severity is overstated. The actual bug is the single "10-branch limit" in the HTTP client doc. Recommend: fix the "10" to "15" in `02-http-client-setup.md` and note that 20 is the platform limit, 15 is the operational threshold. Downgrade from CRITICAL to MAJOR.

### CRIT-4: FSS Operations Table Lists Only 7 of 12 -- CONFIRMED

Verified at `04-process-canvas-fundamentals.md:107-115`: Only 7 operations listed. Cross-checked with `14-flow-service.md:14-27`: All 12 listed there. Process G (`12-process-j-list-integration-packs.md`, `13-process-g-component-diff.md`), J, and E4 define their FSS operations inline in their individual build guide files, so builders following the full guide will create them. But E2 and E3 are indeed missing from both the central table AND any individual guide.

**DA challenge**: The central table at Phase 3 fundamentals is explicitly a starter table for the first 7 processes. The individual process sections document their own FSS operations. The real gap is only E2 and E3 (which have no content at all -- already covered by CRIT-1). Downgrade to MAJOR as a documentation completeness issue, not a blocking build issue.

**DA verdict**: Downgrade to MAJOR. The FSS operations for G, J, and E4 are documented in their respective build guide files. Only E2/E3 are truly missing, and that's already captured by CRIT-1.

### MAJ-1: Profile Count Inconsistencies (14 vs 22 vs 24) -- CONFIRMED

Verified: BOM says 24 (`00-overview.md:36`), canvas fundamentals table lists 14 (`04-process-canvas-fundamentals.md:36-49`), inventory says 22. The canvas fundamentals table explicitly covers only the first 7 processes; the remaining profiles are documented in their respective process build guide files. This is a documentation structure issue, not a missing-content issue.

**DA verdict**: Confirmed as MAJOR. The counts should be reconciled even though the actual profiles are documented in individual sections.

### MAJ-4: Process C Step 6 Cache Reset Bug -- CONFIRMED

Verified at `10-process-c-execute-promotion.md:158-159`: Step 6 explicitly sets `componentMappingCache = {}`. Step 5.6 (`validate-connection-mappings.groovy`) loads connection mappings into this cache. Step 6 then resets it, erasing the connection mappings.

**DA challenge**: Is this actually a bug or intentional design? Reading the full context: Step 5.7 says connection mappings are "pre-loaded." If the intent is to have connection mappings pre-loaded, resetting the cache defeats that purpose. The subsequent step 8's `rewrite-references.groovy` needs these mappings. This IS a bug.

**DA verdict**: Confirmed as MAJOR. The cache reset at step 6 is clearly a bug that would cause connection references to not be rewritten.

### MAJ-7: Duplicate Navigation Wiring -- CONFIRMED with IMPORTANT DETAIL

Verified:
- Version 1 at `15-flow-dashboard-developer.md:219-243`: 18 rules, includes Page 9 wiring, test/production mode distinctions
- Version 2 at `16-flow-dashboard-review-admin.md:109-130`: 16 rules, missing Page 9 wiring, different button text at step 5

Key differences:
- Version 1 step 5: `"Continue to Deployment"` -> Page 4
- Version 2 step 5: `"Submit for Integration Pack Deployment"` -> Page 4
- Version 1 includes step 7 (test mode), step 9 (cancel to Page 9), step 18 (Page 9 -> Page 4)
- Version 2 lacks all three

**DA verdict**: Confirmed as MAJOR. Both versions are in Step 5.4, creating direct conflict. Version 1 is clearly more complete and should be the canonical version.

### MAJ-8: Phase 7 File Does Not Exist -- CONFIRMED

Verified: No file matching `22*.md` in the build guide. Multi-env content IS distributed across existing files:
- Process D 3-mode logic: `11-process-d-package-and-deploy.md`
- Process E4: `07-process-e-status-and-review.md:68-131`
- Page 9: `15-flow-dashboard-developer.md:197-217`
- Testing: `17-testing.md` Tests 8-10

**DA challenge**: The critical instruction note says: "The file `docs/build-guide/22-phase7-multi-environment.md` was REMOVED. Multi-env content was distributed into existing files." This was an intentional design decision, not a gap. The question is whether the distribution is complete and findable.

**DA verdict**: Downgrade from MAJOR to MINOR. The content exists; the issue is discoverability and indexing. A cross-reference table mapping Phase 7 concepts to their locations would resolve this.

---

## Architect Findings Verification

### CRIT-1: No Isolated Tests for E2, E3, E4 -- CONFIRMED

Verified: Searching `17-testing.md` for "queryPeerReviewQueue", "submitPeerReview", "queryTestDeployments" -- none appear as isolated test targets. E2 and E3 are exercised only indirectly through Test 5's approval workflow. E4 is exercised indirectly through Test 8 step 5 (Page 9 navigation) but not as an API-level test.

**DA verdict**: Confirmed as CRITICAL. The most complex validation logic (self-review prevention, state guards, exclusion joins) has zero targeted test coverage.

### CRIT-2: No Self-Review Prevention Test -- PARTIALLY CONFIRMED

Verified at `17-testing.md:269`: Test 5 says "Log in as a different developer" -- which avoids self-review but doesn't test the prevention mechanism.

**DA challenge**: This is a subset of CRIT-1 (E2/E3 have no isolated tests). It should be folded into CRIT-1 rather than standing as a separate CRITICAL. The recommendation for a self-review negative test is valid but doesn't warrant a second CRITICAL slot.

**DA verdict**: Merge into CRIT-1. The self-review prevention test is part of the broader E2/E3 test gap.

### MAJ-1: Branch Limit Not Tested -- CONFIRMED

No test in `17-testing.md` references branch limits, `BRANCH_LIMIT_REACHED`, or branch count thresholds. No troubleshooting entry exists for this error code. Confirmed.

### MAJ-3: No Phase 7 Troubleshooting -- CONFIRMED

Verified: `18-troubleshooting.md` has sections for Phases 1-6 only (lines 3-147). No coverage for `TEST_DEPLOY_FAILED`, `HOTFIX_JUSTIFICATION_REQUIRED`, `INVALID_DEPLOYMENT_TARGET`, `TEST_PROMOTION_NOT_FOUND`, or Page 9 issues.

**DA verdict**: Confirmed as MAJOR.

### MAJ-4: 6 of 18 Error Codes Untested -- CONFIRMED with CORRECTION

The architect says "Only 2 of 18 error codes are partially tested." Verified against `17-testing.md`: Test 6 covers `PROMOTION_FAILED`-like behavior (error recovery), Test 10c covers `TEST_DEPLOY_FAILED` (test deployment failure). Neither test explicitly asserts the `errorCode` field value. So the claim is accurate: zero error codes are explicitly tested.

**DA verdict**: Confirmed. The error code table is thorough and accurate.

### MAJ-5: Troubleshooting Error Codes Not Aligned -- CONFIRMED

Verified: `18-troubleshooting.md` uses symptom-based headings ("Groovy script error: property not found") not error code headings. A developer seeing `MISSING_CONNECTION_MAPPINGS` in the Flow UI cannot search the troubleshooting guide for this code. 12+ error codes have no troubleshooting entry.

**DA verdict**: Confirmed as MAJOR.

### MAJ-6: No Operational Runbook -- CONFIRMED but SCOPE QUESTION

**DA challenge**: This finding is valid but may be out of scope for a build guide. Build guides document how to build the system, not how to operate it in production. Operational runbooks, monitoring dashboards, and escalation matrices are separate documentation artifacts. The recommendation to create `23-operational-readiness.md` is good but should be flagged as an enhancement rather than a gap in the build guide.

**DA verdict**: Downgrade from MAJOR to MINOR/Observation. Valid recommendation but scope is beyond a build guide.

### MAJ-7: Test 8 Page 9 Navigation -- CONFIRMED

Test 8 step 5 says "Navigate to Page 9" but provides no navigation path. Page 9's documented entry point is the "View in Production Readiness" button on Page 4 after test deploy (Version 1 navigation step 7 in `15-flow-dashboard-developer.md:229`). If the tester is already on Page 4, they should see this button.

**DA verdict**: Confirmed but downgrade to MINOR. The navigation path exists; the test just doesn't specify it. Add a clarifying note.

### MIN-1: Index Says "7 Test Scenarios" but Has 10 -- CONFIRMED

Verified at `index.md:26`: "Smoke test + 7 test scenarios." Actual count in `17-testing.md`: Tests 1-10 = 10 tests. Off by 3 (Tests 8-10 were added for multi-environment).

**DA verdict**: Confirmed as MINOR.

### MIN-3: SSO Group Names Inconsistent in Tests -- CONFIRMED

Test 5 uses "Boomi Developers"/"Boomi Admins" while the canonical format is `ABC_BOOMI_FLOW_CONTRIBUTOR`/`ABC_BOOMI_FLOW_ADMIN`. The troubleshooting guide at `16-flow-dashboard-review-admin.md:100-101` also uses "Boomi Developers"/"Boomi Admins".

**DA verdict**: Confirmed. The natural-language names are used consistently in user-facing contexts (tests, troubleshooting) while the canonical SSO group IDs are used in the spec. This may be intentional (user-friendly vs technical), but should be explicitly noted.

---

## Troubleshooting "11 Operations" Verification

Verified at `18-troubleshooting.md:106`: "Verify all 11 operations are listed" followed by an enumeration. Counted: GetDevAccounts, ListDevPackages, ResolveDependencies, ExecutePromotion, PackageAndDeploy, QueryStatus, ManageMappings, QueryPeerReviewQueue, SubmitPeerReview, ListIntegrationPacks, GenerateComponentDiff = 11 operations. Missing: QueryTestDeployments (E4).

The Flow Service at `14-flow-service.md:12-27` lists 12 actions. The troubleshooting guide is off by one.

**DA verdict**: Expert's MIN-3 confirmed. Should say 12 and include QueryTestDeployments.

---

## Summary of DA Adjustments

| Finding | Original Severity | DA Recommendation | Reason |
|---------|------------------|-------------------|--------|
| Expert CRIT-1 (E2/E3 no content) | Critical | **Critical** | Fully confirmed |
| Expert CRIT-2 (E4 missing script) | Critical | **Major** | E4 has 6-step canvas; only Groovy body missing |
| Expert CRIT-3 (Branch limit 4 values) | Critical | **Major** | Actual conflict is "10 vs 15"; 18/20 are explainable |
| Expert CRIT-4 (FSS table 7/12) | Critical | **Major** | G/J/E4 documented inline; only E2/E3 truly missing (=CRIT-1) |
| Expert MAJ-4 (Cache reset bug) | Major | **Major** | Confirmed real bug |
| Expert MAJ-7 (Dup nav wiring) | Major | **Major** | Confirmed conflict |
| Expert MAJ-8 (No Phase 7 file) | Major | **Minor** | Intentional distribution; needs cross-ref |
| Architect CRIT-2 (Self-review test) | Critical | Merge into CRIT-1 | Subset of E2/E3 testing gap |
| Architect MAJ-6 (No ops runbook) | Major | **Minor/Obs** | Out of scope for build guide |
| Architect MAJ-7 (Test 8 Page 9) | Major | **Minor** | Navigation path exists, just unspecified |

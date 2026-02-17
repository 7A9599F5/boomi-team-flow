# Team 2 — Integration Engine Consensus

**Date:** 2026-02-16
**Reviewers:** Integration Expert, Systems Orchestration Architect, Devil's Advocate
**Scope:** All integration processes (A0, A, B, C, D, E, E2, E3, E4, F, G, J), Groovy scripts, profiles, flow-service-spec, build guides, multi-environment deployment

---

## Critical Findings (verified)

### CRIT-1: No Concurrency Guard for Parallel Promotions
**Source:** Architect C1, confirmed by DA
**Files:** `docs/architecture.md:216`, `docs/build-guide/10-process-c-execute-promotion.md`

The architecture doc mentions "Concurrency lock via PromotionLog IN_PROGRESS check" but no build guide step implements this. Two simultaneous promotions of overlapping components can create duplicate prod components and conflicting ComponentMapping records. Process C creates the PromotionLog at step 4 (after branch creation at step 3.7), leaving a race window.

**Recommendation:** Add a pre-check at Process C step 3 that queries PromotionLog for `devAccountId = {value} AND status IN ("IN_PROGRESS", "PENDING_PEER_REVIEW", "PENDING_ADMIN_REVIEW")` and aborts if found. Document this as a required step.

### CRIT-2: Branch Limit Threshold — 4 Conflicting Values
**Source:** Expert C4, confirmed by DA with all 4 values independently verified
**Files:** `10-process-c-execute-promotion.md:79` (15), `22-phase7-multi-environment.md:151` (18→15), `02-http-client-setup.md:307` (10), `flow-service-spec.md:670` (20)

Four different branch limit values across four documents. Phase 7 says "change from 18 to 15" but Process C already uses 15, creating internal contradiction. The Boomi Platform limit is likely 20; the operational threshold should be a single canonical value.

**Recommendation:** Standardize to one value (15 recommended) and document it in exactly one location with all others referencing it.

### CRIT-3: Process D Missing `promotionId` in Profile JSON and Flow-Service-Spec
**Source:** Architect C3, expanded by DA (DA-1)
**Files:** `integration/profiles/packageAndDeploy-request.json`, `integration/flow-service/flow-service-spec.md:173-193`, `docs/build-guide/11-process-d-package-and-deploy.md:16`

The build guide requires `promotionId` for PromotionLog updates, but it is missing from both the profile JSON and the flow-service-spec's request fields. Without it, Process D cannot update the PromotionLog, severing the audit trail. This is a triple-document mismatch.

**Recommendation:** Add `promotionId` to `packageAndDeploy-request.json` and the flow-service-spec's packageAndDeploy request fields.

### CRIT-4: Processes E2 and E3 — FSS Operations Missing from Central Table
**Source:** Expert C2, narrowed by DA
**Files:** `docs/build-guide/04-process-canvas-fundamentals.md:107-115`

The central FSS operation table lists only 7 of 12 operations. While Processes G, J, and E4 create their FSS operations inline in their build guides, E2 and E3 have NO build guide content and NO FSS operation creation instructions anywhere. A builder cannot create these operations.

**Recommendation:** Either add E2 and E3 to the central table with creation instructions, or create dedicated build guide files for both processes.

---

## Major Findings (verified)

### MAJ-1: Process E Build Guide vs. Flow-Service-Spec — Completely Different Contracts
**Source:** Expert M1 + M2, confirmed by DA
**Files:** `docs/build-guide/07-process-e-status-and-review.md:13-47` vs `integration/flow-service/flow-service-spec.md:256-283`

The build guide defines request fields `promotionId/devAccountId/status/limit`; the spec defines `queryType/processName/componentId/startDate/endDate/reviewStage`. Response fields also diverge completely. These are irreconcilable without a rewrite of one document. This is the most structurally significant mismatch across the entire system.

**Recommendation:** Reconcile to a single contract. The flow-service-spec's version is more feature-complete; update the build guide to match.

### MAJ-2: Process A0 Response — Missing `effectiveTier` and Field Name Mismatch
**Source:** Expert M4, confirmed by DA
**Files:** `docs/build-guide/06-process-a0-get-dev-accounts.md:15-17` vs `flow-service-spec.md:32-39`

Build guide uses `accounts` array; spec uses `devAccounts` array plus `effectiveTier`. The tier resolution algorithm (spec lines 41-54) is undocumented in the build guide. The two-axis SSO model is a key architectural feature that has no build implementation guide.

**Recommendation:** Update the build guide to include `effectiveTier`, rename the array to `devAccounts`, and document the tier resolution algorithm.

### MAJ-3: Process B Response — Structural Mismatch
**Source:** Expert M5, confirmed by DA
**Files:** `docs/build-guide/09-process-b-resolve-dependencies.md:19-20` vs `flow-service-spec.md:105-112`

Build guide uses `components` array with `devComponentId/name/type/devVersion/prodStatus`; spec uses `dependencies` array with `componentId/dependencyType/depth`. Different names, different structures, different fields.

**Recommendation:** Reconcile. The build guide version is more useful for downstream Process C; the spec version is better for UI display. Choose one and update the other.

### MAJ-4: Orphaned Branch Risk on Peer/Admin Rejection
**Source:** Architect M3, confirmed by DA
**Files:** `docs/architecture.md:302-307`, `integration/flow-service/flow-service-spec.md:355-384`

Branch deletion is documented as expected on rejection/denial in the architecture doc, but no build guide, process, or flow-service-spec action implements it. Every rejected promotion leaks a branch. Combined with the 15-branch limit, this is a resource exhaustion risk.

**Recommendation:** Add branch deletion logic to Process E3 for `decision=REJECTED`, and create an admin denial action that also deletes the branch. Update PromotionLog `branchId` to null after deletion.

### MAJ-5: No Cancel Test Deployment Action
**Source:** DA pre-discovered gap, confirmed by all
**Files:** `flow-service-spec.md` (absent), `docs/architecture.md:287`

There is no `cancelTestDeployment` message action. Stale test branches from abandoned or failed test deployments will accumulate without a way to clean them up. The 30-day stale warning on Page 9 is UI-only with no backend enforcement.

**Recommendation:** Add a `cancelTestDeployment` action that deletes the preserved branch and updates PromotionLog status to `CANCELLED`.

### MAJ-6: Process C Step 6 — Mapping Cache Reset Bug
**Source:** Expert m3 (originally minor), upgraded by DA
**Files:** `docs/build-guide/10-process-c-execute-promotion.md:158-159`, `integration/scripts/validate-connection-mappings.groovy:68-69`

Step 5.6 (`validate-connection-mappings.groovy`) writes connection mappings into `componentMappingCache` (line 68). Step 6 then resets `componentMappingCache = {}`, erasing those pre-loaded mappings. The parenthetical text at step 5.7 acknowledges connection mappings are pre-loaded, contradicting the reset instruction. This is a logic error that would cause connection reference rewrites to fail silently.

**Recommendation:** Remove the `componentMappingCache = {}` reset at step 6. The cache should retain the connection mappings loaded by step 5.6.

### MAJ-7: Process B BFS Scalability — Unbounded with O(n) API Calls
**Source:** Architect C2, downgraded from CRITICAL by DA
**Files:** `docs/build-guide/09-process-b-resolve-dependencies.md:78-114`

Each BFS node requires 2-3 API calls with 120ms gaps. Large dependency trees (100+ components) could take minutes. While Boomi's async mechanism prevents user-facing timeouts, there is no upper bound on component count.

**Recommendation:** Add a `maxComponents` limit (e.g., 100) with error code `COMPONENT_LIMIT_EXCEEDED`. Consider batch API calls for metadata enrichment.

### MAJ-8: Profile-to-Build-Guide Field Mismatches (Multiple Actions)
**Source:** Architect M1, confirmed by DA
**Files:** Multiple profile JSONs, build guide docs, and flow-service-spec

Seven actions have field name or structural mismatches between their profile JSON, build guide description, and flow-service-spec contract. Key examples: `manageMappings` uses `operation` (build guide) vs `action` (spec); `generateComponentDiff` and `listIntegrationPacks` include `primaryAccountId` in build guide but not in profiles (by design — it comes from FSS config, but this is not documented).

**Recommendation:** Create a reconciliation matrix and align all three documents. Add explicit notes where `primaryAccountId` comes from FSS configuration rather than the request.

### MAJ-9: strip-env-config.groovy — Overly Broad Element Matching
**Source:** Architect M6, confirmed by DA
**Files:** `integration/scripts/strip-env-config.groovy:21-57`

Script strips ALL elements named `password`, `host`, `url`, `port`, `EncryptedValue` at any depth. Legitimate non-sensitive uses of these element names in profile definitions, map functions, or process properties could be corrupted. Mitigated by branch isolation (damage visible during diff review) but still a data integrity risk.

**Recommendation:** Scope stripping to known sensitive paths within Boomi component XML (e.g., connection configuration elements only).

### MAJ-10: componentMappingCache DPP Size Limit Risk
**Source:** Architect M4
**Files:** `docs/build-guide/10-process-c-execute-promotion.md:271-287`

The mapping cache grows with each promoted component (~85 bytes per entry). Public Cloud Atom DPPs have practical limits (~100KB). For large promotions (200+ components) or accumulated mappings, silent truncation could occur.

**Recommendation:** Add size monitoring. Consider using Document Properties or accumulating documents instead of DPPs for large datasets.

### MAJ-11: Processes E2 and E3 — No Dedicated Build Guide Content
**Source:** Expert C1 (downgraded from CRITICAL by DA), Architect M2
**Files:** `docs/build-guide/` (absent for E2/E3)

Both processes are referenced throughout the system (flow-service-spec, flow pages 5-6, build order checklist) but have no shape-by-shape build instructions. A builder must reverse-engineer from the spec and profiles. E3 is especially complex (self-review check, state validation, dual status field updates).

**Recommendation:** Create dedicated build guide sections for E2 and E3 following the same pattern as other processes.

---

## Minor Findings (verified)

### MIN-1: DPP Catalog ~40% Complete
**Source:** Expert M8
**Files:** `docs/build-guide/20-appendix-dpp-catalog.md`

Missing DPPs for Processes D, E2, E3, E4, G, and J. The catalog only documents Global, Process B, and Process C DPPs.

### MIN-2: Process D MergeRequest Poll Loop Under-Specified
**Source:** Expert M7, downgraded from MAJOR by DA
**Files:** `docs/build-guide/11-process-d-package-and-deploy.md:116`

Poll interval and max retries not specified. Process C establishes the pattern (5s delay, max 6 retries) which builders would logically follow.

### MIN-3: SKIPPED/FAILED Action Values Undocumented in flow-service-spec
**Source:** DA-4 (new finding)
**Files:** `flow-service-spec.md:147`, `docs/build-guide/10-process-c-execute-promotion.md:298`

Process C's response includes `action` values "FAILED" and "SKIPPED" but the spec only documents "created" | "updated".

### MIN-4: rewrite-references.groovy — Global String Replacement
**Source:** Architect M7, confirmed with low practical risk
**Files:** `integration/scripts/rewrite-references.groovy:27-33`

Raw string replacement across entire XML text rather than parsed XML rewriting. Theoretically risky but practically safe because component IDs are GUIDs. Logging of each replacement provides audit trail.

### MIN-5: Process A Missing Rate-Limit Retry Logic
**Source:** Expert m2
**Files:** `docs/build-guide/08-process-a-list-dev-packages.md:58`

120ms sleep between calls but no 429/503 retry logic. The architecture doc mentions retry with exponential backoff, but build guides don't implement it.

### MIN-6: sort-by-dependency.groovy — Default Priority for Unknown Types
**Source:** Architect m4
**Files:** `integration/scripts/sort-by-dependency.groovy:17`

Unknown component types default to priority 3 (same as operations). Should default to priority 5 or log a warning.

### MIN-7: build-visited-set.groovy — O(n) List Lookups
**Source:** Architect m5
**Files:** `integration/scripts/build-visited-set.groovy:17-33`

Uses JSON array with O(n) `contains()` checks instead of HashSet for O(1) lookups. Negligible for small trees, compounds with API latency for large trees.

### MIN-8: validate-connection-mappings.groovy Discards Document Properties
**Source:** Architect m7, confirmed by DA
**Files:** `integration/scripts/validate-connection-mappings.groovy:73-74`

Uses `new Properties()` instead of preserving input document properties. No practical impact in current flow.

### MIN-9: Build Order Checklist Inconsistency
**Source:** Expert m1
**Files:** `docs/build-guide/13-process-g-component-diff.md:109-122` vs `integration-patterns.md:43-54`

Two different orderings (simplest-first vs dependency-first). Intentionally different but confusing.

### MIN-10: Inconsistent DPP Persistence Flags Documentation
**Source:** Architect m1
**Files:** `docs/build-guide/20-appendix-dpp-catalog.md`

DPP catalog does not document persistence flags. Per groovy-standards.md, default should be `false`.

### MIN-11: No Retry Logic for DataHub Operations
**Source:** Architect m6
**Files:** `docs/architecture.md:215`

Architecture doc mentions retry for Platform API but no guidance for DataHub connector operations.

---

## Observations

### OBS-1: Strong Error Handling Architecture
Process C's dual Try/Catch pattern (outer for catastrophic with branch cleanup, inner per-component for graceful degradation) is well-designed. The `MISSING_CONNECTION_MAPPINGS` pre-validation is an effective fail-fast pattern. (Expert O1, Architect O1)

### OBS-2: Elegant Bottom-Up Sort + Mapping Cache Design
The interplay between `sort-by-dependency.groovy` and progressive `componentMappingCache` accumulation ensures dependencies are in the cache before their dependents are processed. Separation of connection validation as a batch pre-check is sound. (Expert O2, Architect O1)

### OBS-3: Sound Branch Lifecycle Management
The promotion-to-branch, diff-from-branch, merge-on-approval pattern provides good isolation and rollback capability. The TEST mode branch preservation for production-from-test is a thoughtful extension. (Expert O4, Architect O2)

### OBS-4: Good Architectural Decision on Connection Non-Promotion
Excluding connections from promotion with admin-seeded mappings is correct. The `#Connections` folder convention with shared mappings is clean separation of concerns. (Architect O3)

### OBS-5: Clean Data Flow via Flow Dashboard Orchestration
Process C outputs `branchId/promotionId`, which D and G consume. Process B outputs components, which C consumes. No direct process-to-process coupling — the Flow layer is the sole orchestrator. Good modularity. (Architect O5)

### OBS-6: Process D Build Guide Already Has Complete 3-Mode Logic
Both the expert and architect incorrectly claimed the 3-mode Decision was incomplete or additive. The build guide (`11-process-d-package-and-deploy.md`) already includes the full 3-mode logic with Decision shape, mode-specific branches, and complete shape-by-shape instructions. This demonstrates the build guide is more current than reviewers initially assessed.

---

## Areas of Agreement

All three reviewers agree on:

1. **Profile/spec/build-guide mismatches are the most pervasive issue** — affecting 7+ actions with varying severity. A systematic reconciliation pass is needed.
2. **E2 and E3 are the least-documented processes** — build guide content is entirely missing for both.
3. **Branch lifecycle has a resource leak** — rejected/denied promotions do not delete branches, and there is no cancel/cleanup mechanism.
4. **Concurrency is unguarded** — the architecture describes a lock but no build guide implements it.
5. **The core promotion engine (Process C) is well-designed** — the bottom-up sort + mapping cache + dual try/catch pattern is architecturally sound.
6. **Multi-environment support is conceptually well-integrated** — the 3-mode Decision shape, branch preservation for TEST, and testPromotionId linkage are good design.

---

## Unresolved Debates

### 1. BFS Scalability Severity
- **Architect**: CRITICAL (timeout risk for large trees)
- **DA**: MAJOR (async behavior prevents user-facing timeouts; slow but not broken)
- **Consensus**: **MAJOR** — the system handles it gracefully via async, but a hard limit should be added for operational safety.

### 2. rewrite-references.groovy Risk Level
- **Architect**: MAJOR (blind string replacement could cause silent reference errors)
- **DA**: MAJOR but low practical risk (GUIDs have negligible collision probability)
- **Consensus**: **MAJOR** — theoretically correct but practically low-risk. Recommendation to use parsed XML rewriting stands but is not urgent.

### 3. Process E4 Completeness
- **Expert**: MAJOR (minimal specification, 5 steps)
- **DA**: MAJOR but more complete than claimed (build guide has 6 canvas steps)
- **Consensus**: **MAJOR** — the build guide exists at `07-process-e-status-and-review.md:68-131` but the Groovy exclusion script is missing. The "exclude already-promoted" logic is the hardest part and needs a script.

### 4. Step 6 Cache Reset
- **Expert**: MINOR (documentation contradiction)
- **DA**: MAJOR (logic error that silently breaks connection reference rewriting)
- **Consensus**: **MAJOR** — if a builder follows step 6 literally, connection mappings from step 5.6 are erased. This is a bug in the build guide, not just a documentation issue.

---

## Multi-Environment Coherence Assessment

### Strengths
1. **3-mode Decision shape** is already in the Process D build guide with complete shape-by-shape instructions
2. **Branch preservation** for TEST deployments enables efficient test-to-production transitions
3. **testPromotionId linkage** between TEST and PRODUCTION PromotionLog records provides full traceability
4. **Pack naming convention** ("- TEST" suffix) with `packPurpose` filter is pragmatic
5. **PromotionLog model update** (8 new fields) is well-specified in Phase 7

### Gaps
1. **No cancelTestDeployment action** — stale branches from abandoned tests will accumulate (MAJ-5)
2. **Process E4 exclusion script missing** — the most complex step is described but not implemented
3. **Branch age enforcement is UI-only** — 30-day warning on Page 9 has no backend automation
4. **TEST-to-PRODUCTION transition has no validation** — relies entirely on human judgment that the test deployment was successful
5. **Hotfix justification validated client-side only** — `HOTFIX_JUSTIFICATION_REQUIRED` error code exists in spec but no process implements the server-side check

### Overall Assessment
Multi-environment deployment is **conceptually sound and architecturally well-integrated** with the existing system. The main gaps are operational (branch cleanup, script implementation) rather than architectural. The 3-mode pattern in Process D is the strongest part — complete, well-documented, and logically coherent.

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 4 |
| Major | 11 |
| Minor | 11 |
| Observations | 6 |

**Top 5 Recommendations (Priority Order):**
1. **Reconcile profile/spec/build-guide mismatches** — systematic pass across all 12 actions (MAJ-1, MAJ-2, MAJ-3, MAJ-8, CRIT-3)
2. **Add concurrency guard** to Process C (CRIT-1)
3. **Create E2/E3 build guide content** — the only processes with zero implementation guidance (CRIT-4, MAJ-11)
4. **Implement branch cleanup** on rejection/denial and add cancelTestDeployment action (MAJ-4, MAJ-5)
5. **Fix step 6 cache reset bug** in Process C build guide (MAJ-6)

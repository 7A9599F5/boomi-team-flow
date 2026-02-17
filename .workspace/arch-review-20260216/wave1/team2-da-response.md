# Team 2 — Integration Engine Devil's Advocate Response

**Reviewer:** Devil's Advocate
**Date:** 2026-02-16
**Scope:** Challenge and verify findings from Integration Expert and Systems Orchestration Architect

---

## Verification of CRITICAL Findings

### Expert C1: Processes E2 and E3 Have No Dedicated Build Guide Sections
**Verdict: PARTIALLY OVERTURNED — Downgrade to MAJOR**

The expert claims E2 and E3 have "no dedicated build guide documentation." However, upon reading `07-process-e-status-and-review.md`, I found that **Process E4 is documented in that same file** (lines 68-131), with shape-by-shape instructions, DPPs, and verification steps. The expert missed this entirely. More importantly, the build order checklist at `13-process-g-component-diff.md:109-122` lists E2 and E3 as items 4 and 5 — implying the author intended them to be built as part of the process build phase, though instructions are indeed absent.

The finding is real: E2 and E3 lack dedicated build guide content. But calling it "critical" overstates the impact because:
1. The flow-service-spec (lines 321-384) provides a complete behavioral contract for both.
2. The profiles exist in `/integration/profiles/` with full field definitions.
3. E2 is structurally similar to Process E (DataHub query + filter + map + return).
4. E3 is structurally similar to Process F (DataHub read + validate + update + return).

A competent Boomi builder could construct these from the spec + profiles + the patterns established by E and F. This is a **documentation gap**, not a "system cannot be built" situation. **Downgrade to MAJOR.**

### Expert C2: Process Canvas Fundamentals Lists Only 7 FSS Operations
**Verdict: CONFIRMED CRITICAL, but with important nuance**

The FSS operation table at `04-process-canvas-fundamentals.md:107-115` lists only 7 operations. However, I note the text says "create all seven before building the process canvases, **or create each one just before its process**" (line 98). The individual process build guides (G at `13-process-g-component-diff.md:9-10`, J at `12-process-j-list-integration-packs.md`, E4 at `07-process-e-status-and-review.md:88-89`) do instruct creating their FSS operations inline. The table is incomplete but **the guides for G, J, and E4 compensate**. E2 and E3 remain the gap.

Adjusted: The table should list all 12 operations for completeness, but the real critical gap is E2 and E3 only (not 5 operations). **Maintain CRITICAL but narrow scope to E2/E3.**

### Expert C3: Process Canvas Fundamentals Lists Only 14 Profiles
**Verdict: CONFIRMED but nuance applies**

Same pattern as C2. The profile table lists 14, but individual build guides for G, J, and E4 instruct creating their profiles. E2/E3 profiles exist in the repo but are never referenced by any build guide. **Real gap is 4 profiles (E2 request/response, E3 request/response), not 10.** The severity remains valid because the central import table creates a false sense of completeness.

### Expert C4: Branch Limit Inconsistency (10, 15, 18, 20)
**Verdict: CONFIRMED CRITICAL — independently verified all 4 values**

I verified:
- `10-process-c-execute-promotion.md:79`: threshold `>= 15`
- `22-phase7-multi-environment.md:151`: "Change the branch count threshold from 18 to 15" (implying Phase 3 uses 18, which contradicts line 79)
- `02-http-client-setup.md:307`: "10-branch limit"
- `flow-service-spec.md:670`: "limit: 20 per account"

The Phase 7 doc says "change from 18 to 15" but Process C already says 15. This means either: (a) Process C was updated after Phase 7 was written but Phase 7 text was not updated, or (b) the values were never synchronized. Either way, **4 conflicting values across 4 documents is a genuine critical documentation error.** The Boomi Platform branch limit itself is likely 20, making 15 the effective operational threshold, but this needs explicit canonical documentation.

### Architect C1: No Concurrency Guard
**Verdict: CONFIRMED CRITICAL — independently verified**

`architecture.md:216` mentions "Concurrency lock via PromotionLog IN_PROGRESS check" but no build guide step implements this. Process C (`10-process-c-execute-promotion.md`) goes directly from UUID generation (step 3) to branch creation (step 3.7) with no concurrency check. The PromotionLog is created at step 4 (after branch creation), so there is a race window between steps 3 and 4 where parallel promotions could both proceed.

The architect's analysis of the race condition mechanics is sound: two parallel promotions would create separate branches and separate PromotionLog entries, leading to duplicate prod components. **This is a genuine architectural gap.**

### Architect C2: Process B BFS Scalability
**Verdict: DOWNGRADE TO MAJOR — severity overstated**

The architect claims this is critical, but:
1. The Flow Service has built-in async behavior (flow-service-spec.md:604-630) with automatic wait responses after 30s. Users see a spinner, not a timeout error.
2. `resolveDependencies` typical duration is listed as "5-15 seconds" (line 626), suggesting the spec authors designed for moderate trees.
3. Boomi processes on Public Cloud Atoms have a 30-minute execution timeout, not the "Flow Service timeout" the architect implies.
4. The N+1 pattern is a real performance concern but "scalability" failures would manifest as slow responses, not data corruption or system failure.

The unbounded nature is worth documenting (add `maxComponents` limit), but calling it CRITICAL implies system failure. Slow performance for edge cases is **MAJOR**, not CRITICAL. The typical use case (10-50 component trees) works fine within documented timings.

### Architect C3: Process D Missing `promotionId` in Request Profile
**Verdict: OVERTURNED — FINDING IS INCORRECT**

I read `packageAndDeploy-request.json` directly and it does NOT contain `promotionId`. However, I then read the **build guide** at `11-process-d-package-and-deploy.md:16` which lists `promotionId` as a request field, and the DPP table (line 51) shows `promotionId` coming "from request." The **profile JSON** is the one that is wrong — it is missing the field.

Wait — actually the architect is right that the profile JSON is missing `promotionId`. But re-reading more carefully: the build guide at line 16 says `promotionId (string): promotion run ID (for PromotionLog updates)` as a request field, and the DPP table at line 67 reads it from `document path: promotionId`. So the build guide DOES require it, but the profile JSON file omits it.

**This is a real finding but the framing is slightly off.** The architect says "the build guide specifies `promotionId` as required but the profile JSON does not include it." This is correct. The build guide compensates by instructing the builder to read `promotionId` from the request, which would fail if the profile doesn't define that field. **Confirm as MAJOR** (the profile JSON needs to be fixed, but the build guide is correct about requiring it — the mismatch is between the profile file and the build guide, not a missing concept).

Actually, wait. I re-read the flow-service-spec.md packageAndDeploy request (lines 173-193). The spec does NOT list `promotionId` as a request field either. So the build guide adds it but neither the spec nor the profile includes it. Looking at the build guide more carefully: the `promotionId` comes from Process C's response (which the Flow dashboard stores as a Flow value) and passes it to Process D's request. The profile and spec should include it but don't. **Confirm as CRITICAL** — without `promotionId`, Process D cannot update the PromotionLog. The architect is correct.

---

## Verification of MAJOR Findings

### Expert M1: Process E Lacks `reviewStage` Filter
**Verdict: CONFIRMED MAJOR**

The build guide (`07-process-e-status-and-review.md:31-41`) shows only `promotionId`, `devAccountId`, `status`, `limit` as filter fields. The flow-service-spec (line 261) defines `reviewStage` as a filter. These are completely different filter sets. A builder following the build guide alone would create a Process E that cannot serve Page 7's admin approval queue (which needs `reviewStage = "PENDING_ADMIN_REVIEW"`).

### Expert M2: Process E Request/Response Profile Mismatch
**Verdict: CONFIRMED MAJOR — the most structurally significant mismatch**

The build guide and flow-service-spec describe fundamentally different contracts for `queryStatus`. The build guide uses `promotionId/devAccountId/status/limit`; the spec uses `queryType/processName/componentId/startDate/endDate/reviewStage`. These are irreconcilable without a complete rewrite of one document. This is the most impactful profile mismatch because it affects the most-used query action.

### Expert M4: Process A0 Response Profile Mismatch
**Verdict: CONFIRMED MAJOR**

Build guide says `accounts` array; spec says `devAccounts` array plus `effectiveTier`. The tier resolution algorithm is fully documented in the spec (lines 41-54) but absent from the build guide. This is a significant gap because the two-axis SSO model is a key architectural feature.

### Expert M5: Process B Response Field Names Mismatch
**Verdict: CONFIRMED MAJOR**

Build guide uses `components` array with `devComponentId`, `prodStatus`, etc.; spec uses `dependencies` array with `componentId`, `dependencyType`, `depth`. These are different data structures. However, the build guide's version is arguably more useful for the downstream Process C (which needs `devComponentId`, `type`, `folderFullPath`). The spec's version seems designed for UI display. These may serve different purposes but should be reconciled.

### Expert M6: Process D Missing 3-Mode Decision Logic
**Verdict: OVERTURNED — THE BUILD GUIDE ALREADY INCLUDES 3-MODE LOGIC**

I read `11-process-d-package-and-deploy.md` and it ALREADY contains the 3-mode Decision at step 2.1 (lines 81-90), with Mode 1 (TEST), Mode 2 (PRODUCTION from test), and Mode 3 (PRODUCTION hotfix). The Phase 7 doc (`22-phase7-multi-environment.md:73-105`) describes the same logic. The expert claims the Phase 7 instructions are "additive" and the builder must "mentally merge two documents" — but this is wrong. The build guide at `11-process-d-package-and-deploy.md` IS the merged document. It already has the full 3-mode logic.

The expert was likely reading an older version of the build guide, or did not read the current `11-process-d-package-and-deploy.md` carefully enough. **Overturned.**

### Expert M7: Process D Missing MergeRequest Poll Loop
**Verdict: CONFIRMED but DOWNGRADE TO MINOR**

Step 2.6 says "poll until stage = MERGED" but doesn't specify interval or max retries. However, Process C step 3.8 establishes the pattern (5-second delay, max 6 retries), and Process D builders would logically follow the same pattern. This is a documentation omission, not a design flaw. **Downgrade to minor.**

### Expert M9: Process E4 Incompletely Specified
**Verdict: PARTIALLY OVERTURNED — it has more specification than claimed**

The expert says Process E4 has "minimal specification: 5 numbered steps." However, I found that `07-process-e-status-and-review.md:68-131` provides a more complete specification including: profiles, FSS operation, DPP initialization, shape-by-shape canvas (6 steps), Groovy filtering logic description, error handling, and verification steps. The expert may have only looked at the Phase 7 doc (`22-phase7-multi-environment.md:40-69`) and missed the build guide entry.

The "exclude already promoted" logic (step 4, line 107-109) IS underspecified — it says "Groovy script that filters out..." without providing the actual script. But the build guide does document the approach: check if another PromotionLog has `testPromotionId` equal to this record's `promotionId`. **Downgrade to MAJOR** — the build guide exists but the exclusion script is missing.

### Architect M3: Orphaned Branch Risk on Rejection
**Verdict: CONFIRMED MAJOR — independently verified**

I searched for branch deletion logic in the rejection/denial flow. The flow-service-spec's `submitPeerReview` action (lines 355-384) updates status fields but has no mention of branch deletion. The admin approval flow on Page 7 also has no branch deletion step. The architecture doc at line 302 mentions "REJECT: DELETE (peer)" and "DENY: DELETE (admin)" but this is aspirational, not implemented.

This is a genuine resource leak. With the 15-branch limit and no cleanup on rejection, a busy team could exhaust branch capacity in weeks. **Confirmed MAJOR.**

### Architect M6: strip-env-config.groovy Overly Broad Element Matching
**Verdict: CONFIRMED MAJOR — verified against source code**

I read `strip-env-config.groovy` (lines 21-57). The script indeed uses `root.depthFirst().findAll { it.name() == 'password' }` which matches ANY element named `password` at any depth in the XML tree. Boomi component XML for profile definitions, map functions, and process properties could contain elements with these names that are NOT sensitive configuration. The architect's concern about data corruption is valid.

However, I note a mitigating factor: Process C only runs strip-env-config on components that are being promoted to a branch, not on main. If data corruption occurs, it's isolated to the branch and can be detected during diff review (Process G). This reduces the severity slightly but does not eliminate the risk — a builder might not notice subtle data loss in a large XML diff. **Confirmed MAJOR.**

### Architect M7: rewrite-references.groovy Blind String Replacement
**Verdict: CONFIRMED MAJOR but with significant mitigation**

I read `rewrite-references.groovy` (lines 27-33). It does `xmlContent.replaceAll(Pattern.quote(devId), prodId)` as a raw string replacement. The architect's concerns are theoretically valid but practically low-risk because:
1. Component IDs are UUIDs (128-bit random), so collision probability is astronomically low.
2. The `Pattern.quote()` call ensures the UUID is treated as a literal string, not a regex.
3. UUIDs won't appear as substrings of other strings.
4. CDATA sections in Boomi component XML are rare.

The risk is real but the probability is negligible. The recommendation to use parsed XML rewriting is good practice but may not justify the implementation complexity for a Boomi Groovy sandbox (limited memory, no external libraries). **Confirm MAJOR but note low practical risk.**

---

## Verification of MINOR Findings

### Expert m3: Process C Step 6 Contradicts Step 5.6 (Mapping Cache Reset)
**Verdict: OVERTURNED — Not a contradiction**

The expert says step 6 resets `componentMappingCache = {}` which would erase connection mappings loaded by step 5.6. But re-reading `10-process-c-execute-promotion.md:158-159`:

> Step 6: "Set Properties — Initialize Mapping Cache" and sets `componentMappingCache = {}`

And step 5.7 says:
> "YES branch: continue to step 6 (Initialize Mapping Cache — now only needs non-connection mappings since connection mappings are pre-loaded)"

This IS a contradiction in the text — the parenthetical says connection mappings are pre-loaded, but the step resets the cache to `{}`. Looking at the DPP table (line 39), `componentMappingCache` is initialized to `{}`. If step 5.6 wrote connection mappings into it and step 6 resets it, those mappings ARE lost.

Wait — I need to re-read `validate-connection-mappings.groovy` more carefully. At line 68, the script writes: `ExecutionUtil.setDynamicProcessProperty("componentMappingCache", JsonOutput.toJson(compCache), false)`. So after step 5.6, `componentMappingCache` contains the connection mappings. Then step 6 says reset to `{}`. This IS a bug.

**Actually, UPGRADE to MAJOR** — this is not a documentation contradiction, it's a **logic error in the build guide**. If a builder follows step 6 literally, connection mapping rewrites will fail silently. The correct behavior should be: skip the reset at step 6 (the cache already contains connection mappings from step 5.6), or re-read it and merge. The parenthetical text acknowledges connection mappings are pre-loaded but the instruction contradicts this.

### Architect m7: validate-connection-mappings.groovy Uses `new Properties()`
**Verdict: CONFIRMED MINOR — verified against source code**

Line 73-74 of `validate-connection-mappings.groovy`:
```groovy
dataContext.storeStream(
    new ByteArrayInputStream(JsonOutput.toJson(nonConnections).getBytes("UTF-8")),
    new Properties()
)
```

This does discard document properties. In the current flow, this is unlikely to cause issues because the output feeds into the promotion loop which reads from DPPs, not document properties. But it violates the Groovy standards pattern of preserving properties. **Confirmed MINOR.**

---

## Pre-Discovered Gaps Verification

### No Cancel Test Deployment Action
**CONFIRMED** — There is no `cancelTestDeployment` message action in the flow-service-spec (12 actions listed, none for cancellation). The architecture doc mentions this as a "future consideration." Without it, stale branches from abandoned test deployments will accumulate and eventually hit the 15-branch limit. This should be added as a **MAJOR finding** that neither reviewer explicitly flagged at MAJOR severity.

### SKIPPED Status Undocumented in flow-service-spec
**CONFIRMED** — I searched the flow-service-spec for "SKIPPED" and found zero matches. Process C's build guide (step 18, line 298) says to mark dependent components as "SKIPPED" when a dependency fails, but this status value is not documented in the flow-service-spec's response fields. The `executePromotion` response (line 147) lists `action` values as `"created" | "updated"` — no "skipped" or "failed." **This is a MINOR gap in the spec.**

### Process E4 Implementation Incomplete
**PARTIALLY OVERTURNED** — The build guide at `07-process-e-status-and-review.md:68-131` has more detail than the Phase 7 doc alone. But the exclusion Groovy script is not provided (unlike other scripts in `/integration/scripts/`), making the most complex step unimplemented. **MAJOR, not CRITICAL.**

### Process D 3-Mode Refactor Completeness
**OVERTURNED** — The build guide (`11-process-d-package-and-deploy.md`) already contains the full 3-mode logic with Decision shape, mode-specific branches, and complete shape-by-shape instructions. Phase 7 is NOT a separate additive document for Process D — the build guide was already updated. The expert's finding M6 was based on an incorrect reading.

---

## Missed Issues (Not Caught by Either Reviewer)

### DA-1: `promotionId` Also Missing from flow-service-spec packageAndDeploy Request (MAJOR)
The architect caught that `promotionId` is missing from the profile JSON, but both reviewers missed that it's ALSO missing from the flow-service-spec's `packageAndDeploy` request fields (lines 173-193). The spec lists `devAccountId`, `prodComponentId`, `packageVersion`, etc., but not `promotionId`. This means 3 documents disagree: build guide says include it, spec omits it, profile omits it. The build guide is correct (Process D needs it); the other two must be updated.

### DA-2: `branchId` Missing from flow-service-spec packageAndDeploy Request (MAJOR)
Similarly, `branchId` is in the build guide (line 15) and the profile JSON (line 14), but NOT in the flow-service-spec's packageAndDeploy request fields. The spec is missing this critical field that Process D needs for merge operations.

Wait — I need to re-check. The spec at line 173 lists `prodComponentId` as first field. Let me look... No, `branchId` is not in the spec's request fields. But it IS in the profile JSON (line 14). So the spec is incomplete but the profile is correct for this field. **Only `promotionId` is missing from both spec and profile.**

### DA-3: Process C Outer Try/Catch Branch Cleanup May Race with PromotionLog (MINOR)
The outer Try/Catch (step 100) attempts `DELETE /Branch/{branchId}` before returning. But if the failure occurs between step 4 (PromotionLog creation) and the catch block, the PromotionLog will record `branchId` pointing to a deleted branch. The build guide at step 8.6 (Process D) says to set `branchId = null` after deletion, but Process C's outer catch does not mention updating PromotionLog's `branchId` to null. This leaves orphaned references.

### DA-4: No SKIPPED/FAILED Action Values in flow-service-spec (MINOR)
Process C's response includes `action` values of `"FAILED"` and `"SKIPPED"` (build guide steps 17-18), but the flow-service-spec only documents `"created" | "updated"` (line 147). The Flow dashboard needs these values to render status correctly.

---

## Contradictions Between Expert and Architect

### 1. Process D 3-Mode Documentation
- **Expert (M6)**: Claims the 3-mode refactor is incomplete and builders must "mentally merge two documents"
- **Architect (Multi-env assessment, gap #1)**: Claims "the Process D build guide does not reference these fields in its Set Properties step"
- **Reality**: The build guide DOES include the 3-mode Decision at step 2.1 AND reads all multi-env fields in Set Properties at step 2 (lines 74-79). **Both are wrong.** The build guide has been updated.

### 2. Process E4 Completeness
- **Expert (M9)**: "5 numbered steps with high-level instructions" — refers to Phase 7 doc only
- **Architect (Multi-env gap #2)**: "no build guide" for E4
- **Reality**: E4 has a build guide section in `07-process-e-status-and-review.md:68-131` with 6 canvas steps, profiles, FSS operation, and verification. **Both missed it.** The Groovy exclusion script is absent, making it incomplete but not undocumented.

### 3. DPP Size Limits
- **Expert (m7)**: Flags Process G storing XML in DPPs as a size concern (~1MB limit)
- **Architect (M4)**: Flags componentMappingCache in DPPs as a size concern (~100KB limit for public cloud)
- **No contradiction**, but they cite different limits. The expert's 1MB is for general DPPs; the architect's 100KB is more conservative and likely accurate for Public Cloud Atoms. Both concerns are valid but the thresholds differ.

---

## Summary

| Original Finding | Original Severity | DA Verdict | Adjusted Severity |
|-----------------|-------------------|------------|-------------------|
| Expert C1 (E2/E3 no build guide) | CRITICAL | Partially overturned | MAJOR |
| Expert C2 (FSS table incomplete) | CRITICAL | Confirmed, narrowed | CRITICAL (E2/E3 only) |
| Expert C3 (Profile table incomplete) | CRITICAL | Confirmed, narrowed | MAJOR (E2/E3 only) |
| Expert C4 (Branch limit inconsistency) | CRITICAL | Confirmed | CRITICAL |
| Architect C1 (No concurrency guard) | CRITICAL | Confirmed | CRITICAL |
| Architect C2 (BFS scalability) | CRITICAL | Downgraded | MAJOR |
| Architect C3 (D missing promotionId) | CRITICAL | Confirmed | CRITICAL |
| Expert M6 (D 3-mode logic) | MAJOR | Overturned | N/A (already in build guide) |
| Expert M9 (E4 incomplete) | MAJOR | Partially overturned | MAJOR (script missing) |
| Expert m3 (Step 6 cache reset) | MINOR | Upgraded | MAJOR (logic error) |
| Architect M7 (rewrite-references) | MAJOR | Confirmed with mitigation | MAJOR (low practical risk) |
| New: DA-1 (promotionId triple mismatch) | — | New finding | MAJOR |
| New: DA-4 (SKIPPED/FAILED undocumented) | — | New finding | MINOR |

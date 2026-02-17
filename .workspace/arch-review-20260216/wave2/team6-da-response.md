# Team 6 — Devil's Advocate Response: Error Handling & Resilience

**Date:** 2026-02-16
**Reviewer:** Devil's Advocate
**Inputs:** Resilience Engineer (Expert) + Operations/Observability Architect findings

---

## Verification of Pre-Discovered Gaps

### Gap 1: "4/6 Groovy scripts missing try/catch" — VERIFIED WITH NUANCE

**Source verification against actual scripts:**

| Script | try/catch? | Verified |
|--------|-----------|----------|
| `normalize-xml.groovy` | YES (lines 37-63, full outer wrap) | Compliant |
| `build-visited-set.groovy` | PARTIAL (lines 43-57, XML parsing only) | Non-compliant — outer loop body unwrapped |
| `sort-by-dependency.groovy` | NO | Non-compliant |
| `strip-env-config.groovy` | NO | Non-compliant |
| `rewrite-references.groovy` | NO | Non-compliant |
| `validate-connection-mappings.groovy` | NO | Non-compliant |

**DA challenge:** The Expert (CRIT-1) is correct that 5 of 6 scripts are non-compliant with `groovy-standards.md`. However, I want to challenge the **severity framing** for some of these:

1. **`strip-env-config.groovy` and `rewrite-references.groovy`** run INSIDE the per-component Try/Catch (Process C step 8). A failure in these scripts WILL be caught by the process-level error handler. The Expert acknowledges this (lines 27-29 of their findings), but the framing as "CRITICAL" overstates the production risk. The actual gap is **raw exception messages** instead of structured error codes — a Major issue, not Critical.

2. **`sort-by-dependency.groovy`** runs at step 5, OUTSIDE the per-component loop Try/Catch but INSIDE the outer Try/Catch (steps 4-22). A failure here triggers branch cleanup. The gap is the same: raw exceptions, not missing error handling entirely.

3. **`validate-connection-mappings.groovy`** runs at step 5.6, also inside the outer Try/Catch. Same mitigation applies.

4. **`build-visited-set.groovy`** runs in Process B's loop. Process B's build guide (`09-process-b-resolve-dependencies.md`) would need to be checked for its own Try/Catch architecture. The partial wrap around XML parsing (lines 43-57) is the right instinct — that's where the most likely failure is. The `JsonSlurper.parseText()` calls (lines 19, 25) have null guards (`if (visitedJson && visitedJson.trim())`), which reduces the risk somewhat.

**DA verdict on CRIT-1:** Downgrade to **MAJOR**. The scripts are genuinely non-compliant with the groovy-standards.md mandate, and raw stack traces reaching users is bad. But the process-level Try/Catch patterns in Process C DO provide a safety net. The gap is message quality, not missing error handling.

### Gap 2: "SKIPPED status unhandled in error flows" — VERIFIED

The Expert's MAJ-1 is well-evidenced. Step 18.3 of Process C says "Mark dependent components as SKIPPED" but provides zero implementation guidance. I verified:

- No `failedComponentIds` DPP exists in the DPP catalog (`20-appendix-dpp-catalog.md`)
- No mechanism to build a reverse dependency index is described
- The catch block at step 18 says what to DO conceptually but not HOW

**DA challenge:** The Expert recommends a `failedComponentIds` DPP with reference checking. This is viable but I'll note that the type-based priority system makes this simpler than it appears. If a profile (priority 1) fails, ALL operations (priority 3) and maps (priority 4) that reference it could be detected simply by checking if the current component's XML contains a dev ID that's in the `failedComponentIds` list. The `rewrite-references.groovy` already does a `xmlContent.contains(devId)` check — the SKIPPED logic could piggyback on this pattern.

**DA verdict:** Agree with MAJ-1. The gap is real and the recommendation is sound.

### Gap 3: "Retry specification completeness" — VERIFIED AS CRITICAL

The Expert's CRIT-2 is **understated** rather than overstated. I verified:

- `architecture.md:215` states: "Retry on 429/503: up to 3 retries with exponential backoff"
- `18-troubleshooting.md:47-48` documents: "up to 3 retries with exponential backoff (1 second, 2 seconds, 4 seconds)"
- Process C build guide (`10-process-c-execute-promotion.md`): I read all 349 lines. Zero retry shapes. Zero retry loops. Zero backoff logic.
- Process D build guide (`11-process-d-package-and-deploy.md`): Same. Zero retry shapes.
- HTTP client setup (`02-http-client-setup.md`): Defines 429/503 as error status codes, but no retry mechanism.

This is a **specification contradiction**: the architecture promises retry behavior that no build guide implements. A builder following the build guide would produce a system that does NOT retry on rate limits, contradicting the architecture document. This is Critical severity because:

1. Process C makes 2-4 API calls per component (GET, strip, rewrite, POST)
2. A 20-component promotion = 40-80 API calls
3. At 120ms gaps, that's ~8 req/s sustained for 5-10 seconds
4. The Partner API limit is ~10 req/s
5. Concurrent users would push over the limit
6. A single 429 during Process D after a merge = inconsistent state

**DA verdict:** Agree with CRIT-2. Maintain Critical severity.

### Gap 4: "Stale error code catalogs" — VERIFIED

The Architect's CRIT-1 is verified. I read `18-troubleshooting.md` (150 lines) and confirmed:

- Zero error codes referenced anywhere in the troubleshooting guide
- The troubleshooting guide uses natural language descriptions ("overrideAccount not authorized", "Groovy script error")
- The flow-service-spec has 19 error codes (lines 656-678)
- There is zero cross-referencing between the two documents

I also verified:
- Phase 4 troubleshooting (line 106) references "11 operations" when flow-service-spec lists 12 (including `QueryTestDeployments`)
- Phase 4 troubleshooting (line 111) says "All 11 processes should appear as active listeners" — should be 12

**DA verdict:** Agree with Architect's CRIT-1. The gap between error codes and troubleshooting is real.

---

## Challenges to Expert Findings

### Challenge 1: Expert CRIT-1 Severity — Overstated

As argued above, the script try/catch gap should be **Major, not Critical**. The process-level Try/Catch in Process C provides a safety net. The actual risk is poor error messages, not unhandled crashes. Downgrade to Major.

### Challenge 2: Expert MAJ-2 — Orphaned Branch Risk — PARTIALLY OVERSTATED

The Expert claims "NO branch deletion on REJECTED" for Process E3. I verified against the architecture doc:

- `architecture.md:302-307` (Branch Lifecycle) explicitly shows: `REJECT: DELETE (peer)` and `DENY: DELETE (admin)`
- `architecture.md:245`: "Peer rejection: Branch deleted, submitter notified with feedback."

So the **architectural intent** is clear. The gap is that Process E3's spec (`flow-service-spec.md:355-384`) does NOT include branch deletion as part of its described behavior. This is a build guide / spec gap, not an architectural gap.

**DA challenge:** The Expert is right that Process E3 as specified does NOT delete branches. But the architecture doc DOES specify branch deletion on rejection. The gap is a missing implementation step in Process E3, not a design oversight. This should be framed as "Process E3 build guide is incomplete" rather than "system has no branch cleanup on rejection."

**However**, the Expert is correct that no admin review action exists at all. There is no `submitAdminReview` or equivalent in the flow-service-spec. This IS a genuine architectural gap.

**DA verdict:** Agree with MAJ-2 but reframe. The peer rejection branch gap is a build guide incompleteness. The missing admin review action is a deeper gap.

### Challenge 3: Expert MAJ-3 — Partial Deployment Rollback — VALID BUT DESIGN-CONSISTENT

The Expert identifies that partial deployment (success for env A, failure for env B) leaves inconsistent state. This is true. But:

1. `architecture.md:217` explicitly states: "No automated rollback — Boomi maintains version history"
2. The merge to main is intentionally irreversible (it IS the mechanism for creating prod versions)
3. Boomi PackagedComponents are versioned — you can always re-deploy the previous version manually

**DA challenge:** The Expert's recommendation for a `retryDeployment` action is sound, but the current behavior is a **conscious design trade-off**, not an oversight. The architecture explicitly chose against automated rollback. The gap is the undocumented manual recovery path, not the lack of rollback.

**DA verdict:** Downgrade from Major to **Minor**. Add a recommendation to document the manual recovery procedure.

### Challenge 4: Expert MAJ-5 — validate-connection-mappings Single-Document — VALID

I verified `validate-connection-mappings.groovy` line 25: `def is = dataContext.getStream(0)`. It does indeed only read the first document. And line 74: `new Properties()` instead of preserving input properties.

The Expert notes this is currently safe because `sort-by-dependency.groovy` outputs a single JSON document. But I'll add:

- The `new Properties()` at line 74 is the more concerning issue. Properties carry metadata (document tracking, correlation IDs). Creating a new empty Properties object discards all upstream metadata.
- However, since the output is a filtered JSON array (non-connections only), the downstream consumer (the For Each loop at step 7) likely re-parses it anyway.

**DA verdict:** Agree with MAJ-5. Defensive coding is warranted.

### Challenge 5: Expert MIN-6 — componentMappingCache Reset Bug — SHOULD BE MAJOR

The Expert classified this as MIN-6, but the description is alarming:

- Step 5.6 (`validate-connection-mappings.groovy` line 67-69) pre-loads connection mappings into `componentMappingCache`
- Step 6 resets `componentMappingCache = {}`, wiping those pre-loaded mappings

I verified in `10-process-c-execute-promotion.md`:
- Step 5.6 (line 137-142): validate-connection-mappings writes to `componentMappingCache`
- Step 6 (line 158-159): `DPP componentMappingCache = {}`

This is indeed a bug. When `rewrite-references.groovy` runs later, it reads `componentMappingCache` to replace dev IDs with prod IDs. If connection mappings were wiped, connection references in promoted components would NOT be rewritten — promoted operations/processes would still reference dev connection IDs.

**DA challenge:** This is MORE severe than Minor. This is a logic bug that causes **silent data corruption** (promoted components reference wrong connection IDs). Upgrade to **MAJOR** or even **CRITICAL**.

**DA verdict:** Upgrade MIN-6 to **CRITICAL**. This is a confirmed build guide bug that causes silent reference corruption.

---

## Challenges to Architect Findings

### Challenge 6: Architect CRIT-2 — No Monitoring/SLA — VALID BUT CONTEXTUAL

The Architect identifies zero monitoring, alerting, or SLA specifications. This is true. But:

1. This is a specification repository, not a deployed system. Monitoring is typically configured at deployment time, not design time.
2. Boomi Process Reporting provides built-in monitoring — the spec references it.
3. SLAs depend on organizational requirements that may not be known at design time.

**DA challenge:** While the gap is real, framing it as Critical overstates the urgency for a specification repository. This is a **Major** operational readiness gap, not a Critical specification defect.

**DA verdict:** Downgrade from Critical to **Major**. The recommendation to create an operations.md is sound.

### Challenge 7: Architect MAJ-2 — No Negative Test Scenarios — VALID

The Architect correctly identifies that the testing guide has zero negative/security test scenarios. The 7 error codes specific to the peer review / multi-environment workflow are completely untested:
- `SELF_REVIEW_NOT_ALLOWED`
- `ALREADY_REVIEWED`
- `INVALID_REVIEW_STATE`
- `INSUFFICIENT_TIER`
- `MISSING_CONNECTION_MAPPINGS`
- `BRANCH_LIMIT_REACHED`
- `INVALID_DEPLOYMENT_TARGET`

**DA verdict:** Agree with MAJ-2 fully.

### Challenge 8: Architect MIN-3 — Listener Count (11 vs 12) — VERIFIED

I verified:
- `18-troubleshooting.md:106` says "all 11 operations"
- `18-troubleshooting.md:111` says "All 11 processes should appear as active listeners"
- `flow-service-spec.md:521-533` lists 12 operations (including QueryTestDeployments)

This is a real inconsistency caused by the Phase 7 additions.

**DA verdict:** Agree. Minor — document synchronization issue.

---

## Additional Findings from DA Verification

### DA-1: BRANCH_LIMIT_REACHED Threshold Inconsistency

I found conflicting branch limit values:
- `10-process-c-execute-promotion.md:79` (step 3.6): threshold is **15**
- `flow-service-spec.md:670`: error code table says "limit: **20** per account"
- `architecture.md:284`: "threshold lowered from 18 to **15** for early warning"

Three different numbers (15, 18, 20) for the same threshold. This is a specification inconsistency that will confuse builders.

**Severity:** Minor — but should be unified to one canonical value.

### DA-2: No Structured Logging Standard

Neither the Expert nor Architect explicitly called out the lack of a structured logging standard across scripts. The `normalize-xml.groovy` uses `logger.info()` and `logger.severe()`. Other scripts use `logger.info()` and `logger.warning()`. None include:
- A correlation ID (promotionId) in log messages
- A script identifier prefix
- Structured key-value formatting

**Severity:** Minor — compounds the troubleshooting difficulty identified by the Architect.

### DA-3: `manageMappings` Request Spec Inconsistency

The flow-service-spec (`line 303`) lists `action` values as "query" | "update" | "delete" but the description (line 297) says "querying and manual editing" and the connection seeding workflow (line 299-300) mentions `operation = "create"`. The `create` action is described in the narrative but not in the formal request field enum.

**Severity:** Minor — but could cause build confusion.

---

## Summary

### Severity Adjustments

| Finding | Original Severity | DA Severity | Rationale |
|---------|------------------|-------------|-----------|
| Expert CRIT-1 (script try/catch) | Critical | **Major** | Process-level Try/Catch provides safety net; gap is message quality |
| Expert CRIT-2 (no retry logic) | Critical | **Critical** | Verified: architecture promises it, zero build guides implement it |
| Expert MAJ-3 (partial deployment) | Major | **Minor** | Conscious design trade-off per architecture doc |
| Expert MIN-6 (cache reset bug) | Minor | **Critical** | Silent data corruption: connection references not rewritten |
| Architect CRIT-2 (no monitoring) | Critical | **Major** | Specification repo context; monitoring is deployment-time concern |
| All others | As stated | Agree | Evidence supports original severity |

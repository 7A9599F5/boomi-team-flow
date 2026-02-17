# Team 3: Platform API & API Design — Consensus

**Team**: Platform API Expert + API Design Architect + Devil's Advocate
**Date**: 2026-02-16
**Domain**: API request templates, HTTP client setup, Platform API reference, API design patterns

---

## Consensus Critical Findings (2)

### CC1. MergeRequest Template Field Name Mismatch — Runtime Failure

**Confidence**: High (all three reviewers agree)
**Impact**: Will cause 400 Bad Request when Process D attempts to create a merge request

The `integration/api-requests/create-merge-request.json` template uses `"source": "{branchId}"` but multiple authoritative references indicate the Boomi API field is `"sourceBranchId"`. The build guide at `docs/build-guide/02-http-client-setup.md:350` introduces a third variant (`sourceBranchId` and `targetBranchId`).

**Three-way inconsistency**:
| Source | Field Name |
|--------|-----------|
| Template (`create-merge-request.json:11`) | `source` |
| Build guide (`02-http-client-setup.md:350`) | `sourceBranchId` + `targetBranchId` |
| Research/skills references | `sourceBranchId` |

**Action Required**: Live API test to determine correct field name. Fix template and build guide to match. If `sourceBranchId`, also determine whether `targetBranchId` is required or defaults to main.

### CC2. Branch Limit Threshold — Four Values, One Truth

**Confidence**: High (all three reviewers agree)
**Impact**: Inconsistent enforcement could exhaust branch limit or reject valid promotions

The soft-limit threshold appears as 10, 15, 18, and 20 across the codebase. After the multi-environment update (CHANGELOG v0.6.0), the canonical value is **15** (soft limit) against a **20** (hard limit).

**Required fixes**:
- `docs/build-guide/02-http-client-setup.md:307`: "10-branch limit" --> "15-branch soft limit"
- All `.claude/skills/` references using `>= 18`: update to `>= 15`
- `integration/api-requests/create-branch.json`: clarify "20 = hard limit, 15 = enforcement threshold"

---

## Consensus Major Findings (7)

### CM1. Four Missing HTTP Client Operations

**Confidence**: High
**Affected Processes**: D, J

The centralized operations list (build guide Step 2.2) defines 15 operations. At least 4 additional operations are needed:

1. **PROMO - HTTP Op - QUERY IntegrationPack** — required by Process J (`docs/build-guide/12-process-j-list-integration-packs.md:7`). Template exists (`integration/api-requests/query-integration-packs.xml`) but no build step.
2. **PROMO - HTTP Op - POST ReleaseIntegrationPack** — required by Process D step 7. No template file. Endpoint name inconsistent: `IntegrationPackRelease` vs `ReleaseIntegrationPack`.
3. **PROMO - HTTP Op - POST AddToIntegrationPack** — required by Process D steps 5-6. No template file.
4. **PROMO - HTTP Op - GET MergeRequest** — required by Process D for merge status polling. No template file.

**Action Required**: Create template files for operations 2-4. Add all four as build steps 16-19 in the operations table. Standardize ReleaseIntegrationPack endpoint name.

### CM2. Process G GET Component With Tilde Syntax — URL Parameter Ambiguity

**Confidence**: Medium (devil's advocate notes concatenation may work, but it is undocumented)

Process G (`docs/build-guide/13-process-g-component-diff.md:23-28`) reuses `PROMO - HTTP Op - GET Component` (2 URL parameters) for branch reads that require the tilde syntax URL `/partner/api/rest/v1/{1}/Component/{2}~{3}` (3 URL parameters).

If the intended approach is to concatenate `{componentId}~{branchId}` into a single `{2}` parameter, this works but must be documented explicitly. A builder reading the build guide would see `{2} = prodComponentId, {3} = branchId` and expect 3 separate parameters.

**Action Required**: Either (a) document the concatenation approach with a Groovy/Map example showing `"{prodComponentId}~{branchId}"` being assembled as `{2}`, or (b) create a separate `PROMO - HTTP Op - GET Component (Branch)` operation with the 3-parameter URL.

### CM3. IntegrationPackRelease Endpoint Name Inconsistency

**Confidence**: High

Two different endpoint names appear:
- `docs/build-guide/11-process-d-package-and-deploy.md:120`: `/IntegrationPackRelease`
- `docs/build-guide/02-http-client-setup.md:278`: `/ReleaseIntegrationPack`

**Action Required**: Verify against Boomi API documentation. Standardize to the correct name in all references.

### CM4. Appendix API Reference Incomplete

**Confidence**: High

The API reference at `docs/build-guide/21-appendix-platform-api-reference.md:18-28` lists only 9 of 19+ endpoints. Missing: all Branch operations (4), MergeRequest operations (3), QUERY IntegrationPack, ReleaseIntegrationPack, AddToIntegrationPack. The tilde syntax URLs for Component Create/Update are also not shown.

**Action Required**: Update the appendix to include all endpoints, or add a prominent note redirecting to the complete list in Step 2.2.

### CM5. manageMappings Field Name and Enum Mismatch

**Confidence**: High (architect finding, confirmed by devil's advocate)

The flow-service-spec uses `action` with enum `"query" | "update" | "delete"`. The JSON profile uses `operation`. The Connection Seeding Workflow references a `"create"` value not in either enum.

**Action Required**: Standardize on `operation` (matching the profile) with values `"query" | "create" | "update" | "delete"`. Update `integration/flow-service/flow-service-spec.md:303`.

### CM6. Concurrency Lock Referenced But Not Implemented

**Confidence**: Medium (the risk is real but may be mitigated by natural system behavior)

`docs/architecture.md:216` references "concurrency lock via PromotionLog IN_PROGRESS check" but no query for existing IN_PROGRESS records exists in the Process C flow. The real risk is not data corruption (branches are isolated) but lost updates: two concurrent promotions for the same component could both succeed, with the last merge overwriting the first.

**Action Required**: Either (a) add a pre-check query in Process C for existing IN_PROGRESS promotions of the same root component, with error code `CONCURRENT_PROMOTION`, or (b) remove the architecture claim of concurrency locking and document this as a known limitation.

### CM7. Merge Status Polling Parameters Undefined

**Confidence**: High

The merge execute step says "poll GET /MergeRequest/{mergeRequestId} until stage=MERGED" but defines no polling parameters (interval, max retries, failure stages). The branch readiness polling is well-defined (5s delay, 6 retries = 30s), creating an inconsistency.

**Action Required**: Define merge polling parameters. Suggested: 5-second delay, 12 retries = 60 seconds. Add `MERGE_FAILED` and `MERGE_TIMEOUT` to the error contract at `integration/flow-service/flow-service-spec.md:656-678`.

---

## Consensus Minor Findings (6)

| ID | Finding | Action |
|----|---------|--------|
| Cm1 | Naming inventory lists 12 HTTP operations, should be 15+ (missing MergeRequest Execute, GET Branch, DELETE Branch) | Update `docs/build-guide/19-appendix-naming-and-inventory.md` |
| Cm2 | `create-branch.json` template missing `description` field referenced in Process C build guide | Add `"description": "Promotion branch for {promotionId}"` to template |
| Cm3 | Content-Type note at build guide line 55 stops at operation 9, should state "Operations 1-6 use XML, 7-15+ use JSON" | Update note |
| Cm4 | `packageId` field name overloaded: means PackagedComponent ID in one context, released pack ID in another | Add clarifying comments to both templates |
| Cm5 | Branch query empty filter counts ALL branches (not just promo-*) — correct but undocumented | Add comment to template explaining account-wide counting |
| Cm6 | Rate limiting for large dependency trees (50+ components) undocumented as edge case | Add note in architecture.md about expected dependency tree size bounds |

---

## Positive Observations (Consensus)

All three reviewers agree on the following strengths:

1. **Authentication model**: The `BOOMI_TOKEN.{email}` pattern with Partner API tokens is correct and well-documented.
2. **overrideAccount usage**: Properly identifies which operations need cross-account access (read ops) vs. which don't (write ops).
3. **Tilde syntax architecture**: Branch-scoped component operations via `~{branchId}` are architecturally sound and consistently documented where used.
4. **OVERRIDE merge strategy**: Well-justified by the single-writer-per-branch design. Eliminates conflict resolution complexity.
5. **Idempotent DELETE Branch**: Treating 200 and 404 as success is production-ready distributed systems practice.
6. **Rate limiting strategy**: 120ms gap (~8 req/s) with exponential backoff is conservative and appropriate.
7. **API template documentation pattern**: The `_comment`, `_notes`, `_http_operation` metadata conventions in JSON templates provide excellent self-documentation.

---

## Priority-Ordered Action Items

1. **[BLOCKING]** Live API test for MergeRequest field name (`source` vs `sourceBranchId`) — CC1
2. **[HIGH]** Create 4 missing HTTP operation templates and build steps — CM1
3. **[HIGH]** Standardize branch limit threshold to 15 across all documents — CC2
4. **[HIGH]** Define merge polling parameters and add error codes — CM7
5. **[MEDIUM]** Fix manageMappings field name to `operation` with `create` enum value — CM5
6. **[MEDIUM]** Document Process G tilde-syntax URL parameter approach — CM2
7. **[MEDIUM]** Update appendix API reference with all endpoints — CM4
8. **[MEDIUM]** Resolve concurrency lock claim in architecture — CM6
9. **[LOW]** Fix all minor documentation inconsistencies — Cm1-Cm6

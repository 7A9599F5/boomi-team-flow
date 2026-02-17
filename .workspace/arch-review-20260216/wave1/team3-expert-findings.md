# Team 3: Platform API Expert Review — Findings

**Reviewer Role**: Boomi Platform API Expert
**Scope**: API request templates, HTTP client setup, Platform API reference
**Files Reviewed**:
- All 16 files in `integration/api-requests/`
- `docs/build-guide/02-http-client-setup.md`
- `docs/build-guide/21-appendix-platform-api-reference.md`
- Cross-referenced with: `docs/architecture.md`, `docs/build-guide/10-process-c-execute-promotion.md`, `docs/build-guide/11-process-d-package-and-deploy.md`, `docs/build-guide/13-process-g-component-diff.md`, `docs/build-guide/19-appendix-naming-and-inventory.md`

---

## CRITICAL Findings

### C1. MergeRequest Template Uses Wrong Field Name — `source` vs `sourceBranchId`

**File**: `integration/api-requests/create-merge-request.json:11`
**Severity**: Critical — will cause 400 Bad Request at runtime

The template uses `"source": "{branchId}"` but the Boomi Platform API MergeRequest endpoint requires `"sourceBranchId"`. This field name is confirmed across multiple research documents:
- `.workspace/context-research-20260216/platform-api-research.md:713` uses `"sourceBranchId"`
- `.workspace/context-research-20260216/gap-analysis-research.md:310` uses `"sourceBranchId"`
- `.claude/skills/boomi-platform-api/reference/branch-operations.md:228` uses `"sourceBranchId"`

The build guide at `docs/build-guide/11-process-d-package-and-deploy.md:72` perpetuates this by referencing the template: `Request body: source = DPP branchId`.

Meanwhile, the build guide Step 2.2.12 at `docs/build-guide/02-http-client-setup.md:350-351` describes different field names entirely: `sourceBranchId` and `targetBranchId`, contradicting both the template and the actual API.

**Recommendation**: Fix template to use `"sourceBranchId": "{branchId}"` and determine whether `targetBranchId` is also required (defaults to main if omitted in some Boomi API versions).

### C2. Branch Limit Threshold Inconsistency — Four Different Values Across Documents

**Severity**: Critical — inconsistent enforcement could exhaust branch limit or reject valid promotions

The branch limit threshold appears as four different values across the codebase:

| Value | Location |
|-------|----------|
| **10** | `docs/build-guide/02-http-client-setup.md:307` — "enforce the 10-branch limit" |
| **15** | `docs/architecture.md:104` — "fails with BRANCH_LIMIT_REACHED if >= 15" |
| **15** | `docs/build-guide/10-process-c-execute-promotion.md:79` — "activeBranchCount >= 15" |
| **15** | `integration/api-requests/create-branch.json:25` — `"threshold": 15` |
| **15** | `integration/api-requests/query-branch.json:6` — "if >= 15, reject" |
| **18** | `.workspace/context-research-20260216/platform-api-research.md:641` — "threshold: 18" |
| **18** | `CHANGELOG.md:70` — "fail at >= 18" |
| **18** | `.claude/skills/boomi-platform-api/reference/branch-operations.md:398` — `branchCount >= 18` |
| **20** | `integration/api-requests/create-branch.json:7` — "Branch limit: 20 per account" |

The `create-branch.json` template itself is internally contradictory: line 7 says "Branch limit: 20 per account" while line 25 says `"threshold": 15`. The CHANGELOG at line 28 explicitly states "Branch limit threshold lowered from 18 to 15" suggesting an intentional change, but the build guide Step 2.2.11 still references "10-branch limit" which was never the intended value.

**Recommendation**: Standardize on **15** (the latest architectural decision per `docs/architecture.md:104` and the CHANGELOG). Fix `docs/build-guide/02-http-client-setup.md:307` from "10-branch" to "15-branch" or better yet, reference the threshold as "the branch count threshold (currently 15)".

---

## MAJOR Findings

### M1. Missing HTTP Operations in Build Guide — Operation Count Discrepancies

**Severity**: Major — builder will discover missing operations during process construction

Three separate counts disagree:

| Source | Count | Details |
|--------|-------|---------|
| Build guide header (`02-http-client-setup.md:3`) | 15 | "15 HTTP Client" operations |
| Build guide table (`02-http-client-setup.md:38-53`) | 15 | Numbered 1-15 |
| Naming inventory (`19-appendix-naming-and-inventory.md:39`) | 12 | Items 6-17 |

The naming inventory is missing:
- `PROMO - HTTP Op - POST MergeRequest Execute`
- `PROMO - HTTP Op - GET Branch`
- `PROMO - HTTP Op - DELETE Branch`

All three are actively used by Processes C and D and have full step-by-step definitions in the build guide. The inventory should list all 15.

### M2. Missing HTTP Operation for QUERY IntegrationPack

**Severity**: Major — Process J cannot be built as specified

Process J (`docs/build-guide/12-process-j-list-integration-packs.md:7,21`) references `PROMO - HTTP Op - QUERY IntegrationPack`, but this operation is not defined in the 15 operations listed in `docs/build-guide/02-http-client-setup.md`. There is a template file (`integration/api-requests/query-integration-packs.xml`) but no build step for the operation.

Additionally, a `ReleaseIntegrationPack` / `IntegrationPackRelease` operation is needed by Process D (step 7 at `docs/build-guide/11-process-d-package-and-deploy.md:117-122`) but is not defined as a build step either.

**Total missing operations**: At least 2 (QUERY IntegrationPack, ReleaseIntegrationPack), bringing the real count to 17+ HTTP Client operations, not 15.

### M3. Process G Reuses GET Component Operation With Incompatible URL Parameters

**Severity**: Major — GET Component operation has 2 URL parameters but branch read needs 3

`docs/build-guide/13-process-g-component-diff.md:23-28` states that Process G reuses `PROMO - HTTP Op - GET Component` for branch reads with URL `/partner/api/rest/v1/{1}/Component/{2}~{3}` (3 URL parameters). However, the GET Component operation is defined at `docs/build-guide/02-http-client-setup.md:70` with URL `/partner/api/rest/v1/{1}/Component/{2}` (2 URL parameters).

In Boomi HTTP Client operations, the URL pattern and parameter count are fixed at the operation level. You cannot dynamically add a `~{3}` suffix to an operation that was configured with only `{1}` and `{2}`.

**Options**:
1. Create a separate operation `PROMO - HTTP Op - GET Component (Branch)` with URL `/partner/api/rest/v1/{1}/Component/{2}~{3}`
2. Restructure to pass the full `{componentId}~{branchId}` as a single `{2}` parameter (concatenated before the connector call)

### M4. IntegrationPackRelease Endpoint Name Inconsistency

**Severity**: Major — incorrect endpoint URL will cause 404

Two different endpoint names appear for the same operation:
- `docs/build-guide/11-process-d-package-and-deploy.md:120`: `/IntegrationPackRelease`
- `docs/build-guide/02-http-client-setup.md:278`: `/ReleaseIntegrationPack`

Neither may be correct. The actual Boomi Platform API endpoint needs verification. The research documents at `.workspace/context-research-20260216/platform-api-research.md:560` reference `ReleaseIntegrationPack`, and the skills reference at `.claude/skills/boomi-promotion-lifecycle/reference/ipack-lifecycle.md:88` uses `POST /partner/api/rest/v1/{accountId}/ReleaseIntegrationPack`.

**Recommendation**: Verify against the official Boomi API documentation and standardize. Create a template file for this endpoint.

### M5. Missing Template for GET MergeRequest (Poll for Merge Status)

**Severity**: Major — merge polling cannot be built without this

Both `docs/build-guide/11-process-d-package-and-deploy.md:81` and `integration/api-requests/execute-merge-request.json:6` specify polling `GET /MergeRequest/{mergeRequestId}` until `stage=MERGED`. However:
- No template file exists for this GET operation
- No HTTP Client operation is defined for it in the build guide
- No step-by-step build instructions exist

The builder would need to construct this from scratch, risking incorrect implementation.

### M6. Appendix API Reference Missing Branch and Merge Operations

**Severity**: Major — incomplete reference for critical operations

The Partner API Endpoints table at `docs/build-guide/21-appendix-platform-api-reference.md:18-28` lists only 9 endpoints but the system uses at least 17. Missing from the reference:
- Branch operations (POST Branch, GET Branch, DELETE Branch, QUERY Branch)
- MergeRequest operations (POST MergeRequest, POST MergeRequest Execute, GET MergeRequest)
- IntegrationPack query
- ReleaseIntegrationPack

These are among the most complex operations in the system.

### M7. Appendix API Reference Missing Tilde Syntax in Component Create/Update URLs

**Severity**: Major — reference doesn't show how branch operations work

The Appendix table at `docs/build-guide/21-appendix-platform-api-reference.md:21-22` shows:
- POST Component (Create): `/partner/api/rest/v1/{accountId}/Component`
- POST Component (Update): `/partner/api/rest/v1/{accountId}/Component/{componentId}`

These are the base URLs without the tilde syntax. The actual system uses:
- Create: `/partner/api/rest/v1/{accountId}/Component~{branchId}`
- Update: `/partner/api/rest/v1/{accountId}/Component/{componentId}~{branchId}`

The tilde syntax is the entire foundation of the branch-based promotion model. Its absence from the reference table is misleading.

---

## MINOR Findings

### m1. QueryFilter XML — `<argument>` and `<property>` Element Naming

**File**: `integration/api-requests/query-packaged-components.xml:31-33`, `integration/api-requests/query-integration-packs.xml:30-32`

The Boomi Platform API QueryFilter uses the element names `<argument>` (for the field name) and `<property>` (for the value to match). While this naming is counterintuitive (one might expect `<field>` and `<value>`), this is the correct Boomi API syntax. No change needed, but the inverted naming convention should be documented to prevent confusion.

### m2. create-branch.json Template Missing `description` Field

**File**: `integration/api-requests/create-branch.json:28`

The template body shows only `"name": "promo-{promotionId}"` but the build guide at `docs/build-guide/10-process-c-execute-promotion.md:87` specifies both `name` and `description`. The template should include the description field for completeness.

### m3. create-branch.json Has Mixed `_pre_check` Syntax

**File**: `integration/api-requests/create-branch.json:20-27`

The `_pre_check` block uses `<QueryFilter xmlns='http://api.platform.boomi.com/'/>` (XML) embedded inside a JSON template, and the other branch query template (`query-branch.json`) uses a JSON `QueryFilter` object. The inconsistency between XML and JSON formats for the same query operation could confuse builders.

### m4. DeployedPackage Template Has `componentType` Field

**File**: `integration/api-requests/create-deployed-package.json:11`

The template includes `"componentType": "process"` but the Boomi DeployedPackage API typically requires `environmentId` and `packageId` only. The `componentType` field may be ignored or may cause an error depending on API version. Verify against the current Platform API specification.

### m5. Connection Timeout of 120 Seconds May Be Excessive

**File**: `docs/build-guide/02-http-client-setup.md:18-19`

Both `Connection Timeout` and `Read Timeout` are set to 120 seconds. While this provides robustness, most Boomi Platform API calls complete in under 10 seconds. For the branch polling operation (GET Branch with 5-second retry intervals), the read timeout being 120 seconds per retry could cause a single promotion to block for up to 720 seconds (6 retries x 120 seconds) in a worst case where the API is unresponsive but not timing out. Consider a lower read timeout (30-60 seconds) with faster retry behavior.

### m6. Rate Limiting Gap in Dependency Traversal

**File**: `docs/build-guide/21-appendix-platform-api-reference.md:34-37`

The rate limit strategy specifies "120ms gap between consecutive calls (yields ~8 req/s)". For dependency traversal in Process B, a process with 50 component dependencies would require ~50 GET ComponentReference calls + ~50 GET ComponentMetadata calls = ~100 API calls. At 8 req/s, this is ~12.5 seconds of API time alone. This is documented as feasible, but the build guide does not address:
- What happens if a dependency tree exceeds 200 components (very large composite processes)
- Whether the 120ms gap is enforced in the BFS traversal loop or only for pagination

---

## Observations

### O1. Well-Designed Authentication Model

The use of `BOOMI_TOKEN.{email}` with the Partner API token is the correct approach for service account authentication. The build guide provides clear instructions for token generation and troubleshooting. The single connection pattern (shared across all 15+ operations) is appropriate.

### O2. Correct Use of overrideAccount Pattern

The system correctly identifies which operations need `overrideAccount` (read operations from dev sub-accounts) and which do not (write operations to the primary account). This is documented both in the build guide (`02-http-client-setup.md:81`) and the appendix (`21-appendix-platform-api-reference.md:39-45`).

### O3. Tilde Syntax Usage Is Architecturally Sound

The tilde syntax (`~{branchId}`) for branch-scoped component operations is the correct Boomi API mechanism. The system uses it for:
- **Write to branch**: `POST /Component~{branchId}` (create) and `POST /Component/{id}~{branchId}` (update)
- **Read from branch**: `GET /Component/{id}~{branchId}` (Process G diff)

This enables true branch isolation without affecting main, which is the foundation of the review workflow.

### O4. OVERRIDE Merge Strategy Rationale Is Strong

The choice of `OVERRIDE` with `priorityBranch` set to the promotion branch is well-justified: since Process C is the sole writer to each promotion branch, there cannot be legitimate conflicts. The merge always takes the branch version. This eliminates the need for conflict resolution logic entirely.

### O5. Idempotent DELETE Branch Design

Treating both 200 and 404 as success for DELETE Branch (`integration/api-requests/delete-branch.json:21`) is a production-ready pattern. Combined with the documented lifecycle paths (approve/reject/deny/error all delete), this creates a robust cleanup mechanism.

### O6. Comprehensive Error Code Handling

The HTTP operations consistently define error response codes (400, 404, 429, 503) with the addition of 409 (Conflict) for MergeRequest operations. This covers the standard Boomi API error surface.

---

## Multi-Environment Assessment

### Branch Lifetime Concern

With the multi-environment (test + production) deployment model, branches persist longer:
- Test deployment: branch stays alive through peer review + admin approval + test verification (potentially days/weeks)
- Production deployment: branch may persist through a second round of review

The 15-branch threshold (lowered from 18 per CHANGELOG:28) provides a 5-slot buffer, but with long-lived branches, this could be exhausted by 15 concurrent promotions. For organizations with many dev teams, this may become a bottleneck.

### Missing Template for Add PackagedComponent to IntegrationPack

Process D steps 5-6 (`docs/build-guide/11-process-d-package-and-deploy.md:109,114`) reference adding a PackagedComponent to an Integration Pack, but no template file or HTTP operation exists for this API call. This is a separate API endpoint (`POST /IntegrationPackComponent` or similar) that must be called between pack creation and release.

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Major | 7 |
| Minor | 6 |
| Observations | 6 |

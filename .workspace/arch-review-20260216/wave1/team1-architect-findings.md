# Team 1 - Data Modeling Architect Findings

**Reviewer Role**: Data Modeling Architect
**Date**: 2026-02-16
**Focus**: Data coherence, scalability, schema evolution, separation of concerns, multi-env completeness, referential integrity

---

## Critical Issues

### CRIT-1: queryStatus Response Profile Missing Multi-Environment and Branch Fields
**File**: `integration/profiles/queryStatus-response.json:1-31`
**Model**: `datahub/models/PromotionLog-model-spec.json`

The `queryStatus-response.json` profile is missing **13 fields** that exist in the PromotionLog model and are needed for complete status reporting:

**Missing from queryStatus-response.json promotions array**:
- `branchId` (line 163-166 of model) -- needed to show branch lifecycle status
- `branchName` (line 168-172)
- `integrationPackId` (line 174-179)
- `integrationPackName` (line 181-186)
- `processName` (line 188-193)
- `targetEnvironment` (line 196-200) -- **critical for multi-env**: cannot distinguish TEST vs PRODUCTION records
- `isHotfix` (line 202-207)
- `hotfixJustification` (line 209-214)
- `testPromotionId` (line 216-222)
- `testDeployedAt` (line 224-228)
- `testIntegrationPackId` (line 230-235)
- `testIntegrationPackName` (line 237-242)
- `promotedFromTestBy` (line 244-249)

Without `targetEnvironment` in the queryStatus response, the Flow dashboard cannot render environment-specific status views. The flow-service-spec.md (line 267-268) defines the queryStatus response with `processName` and review fields but also omits `targetEnvironment`, `isHotfix`, branch fields, and test deployment fields. However, the FSS spec response is more of a high-level contract, while the JSON profile is the actual implementation schema -- both need updating.

**Impact**: Multi-environment deployment (Phase 7) is partially broken at the query layer. Status pages cannot differentiate TEST vs PRODUCTION promotions or show branch/hotfix context.

### CRIT-2: queryStatus Response Profile Field Name Mismatches with PromotionLog Model
**File**: `integration/profiles/queryStatus-response.json:6-28` vs `datahub/models/PromotionLog-model-spec.json`

Several field names in the queryStatus response profile do not align with the PromotionLog model field names:

| queryStatus-response.json | PromotionLog Model | Issue |
|---|---|---|
| `prodAccountId` (line 10) | `prodAccountId` | OK |
| `initiatedAt` (line 13) | `initiatedAt` | OK |
| `status` (line 14) | `status` | OK |
| `componentsTotal` (line 15) | `componentsTotal` | OK |
| `componentsCreated` (line 16) | `componentsCreated` | OK |
| `componentsUpdated` (line 17) | `componentsUpdated` | OK |
| `componentsFailed` (line 18) | `componentsFailed` | OK |
| `errorMessage` (line 19) | `errorMessage` | OK |
| `resultDetail` (line 20) | `resultDetail` | OK |

The profile aligns on existing fields -- but the **flow-service-spec.md** (lines 266-282) uses **different field names** for the same queryStatus response:

| flow-service-spec.md | PromotionLog Model | Issue |
|---|---|---|
| `promotionDate` (line 269) | `initiatedAt` | **MISMATCH** -- spec says `promotionDate`, model says `initiatedAt` |
| `requestedBy` (line 270) | `initiatedBy` | **MISMATCH** -- spec says `requestedBy`, model says `initiatedBy` |
| `componentCount` (line 271) | `componentsTotal` | **MISMATCH** -- spec says `componentCount`, model says `componentsTotal` |
| `packageVersion` (line 272) | (not in model) | **NOT IN MODEL** -- no `packageVersion` field in PromotionLog |

These mismatches will cause mapping errors when Process E reads from DataHub and maps to the response profile. The integration process must translate between DataHub field names and response field names -- but which set of names is canonical?

**Impact**: Ambiguous contract between DataHub model and API response. Developers building Process E face confusion over which field names to use.

---

## Major Issues

### MAJ-1: SKIPPED Status Not in PromotionLog Status Lifecycle
**File**: `datahub/models/PromotionLog-model-spec.json:58` (status field description)
**File**: `docs/architecture.md:207`

Architecture.md line 207 states: "On error: mark dependents as SKIPPED". However, the PromotionLog `status` field description (line 58) does not include SKIPPED in its lifecycle:

```
IN_PROGRESS -> COMPLETED -> TEST_DEPLOYING -> TEST_DEPLOYED (test path)
IN_PROGRESS -> COMPLETED -> PENDING_PEER_REVIEW -> PEER_APPROVED -> PENDING_ADMIN_REVIEW -> ADMIN_APPROVED -> DEPLOYED (prod path)
Rejection branches: PENDING_PEER_REVIEW -> PEER_REJECTED, PENDING_ADMIN_REVIEW -> ADMIN_REJECTED
Legacy/error: FAILED
```

The SKIPPED status appears to be a per-component status in `resultDetail` JSON, not a promotion-level status. But this is never clarified. If SKIPPED is only within `resultDetail`, the architecture.md language is misleading. If it should be a promotion-level status (e.g., partial promotion), then the model is incomplete.

**Impact**: Ambiguous status semantics. Implementers may incorrectly try to set promotion-level status to SKIPPED.

### MAJ-2: queryPeerReviewQueue Missing Multi-Environment Context Fields
**File**: `integration/profiles/queryPeerReviewQueue-response.json:1-21`
**Build Guide**: `docs/build-guide/22-phase7-multi-environment.md:181-186`

The queryPeerReviewQueue response profile is missing `targetEnvironment`, `isHotfix`, and `branchId` fields. Phase 7 build guide (lines 181-186) requires these fields for Pages 5-6 to display environment and hotfix badges:

> "Add `targetEnvironment` and `isHotfix` badges to queue grid"
> "Page 6 detail: Show hotfix justification when `isHotfix = 'true'`"

Without these fields in the profile, the UI cannot render the badges or hotfix context.

**Impact**: Peer review UI cannot distinguish test-only vs production vs hotfix promotions without a profile update.

### MAJ-3: Build Guide PromotionLog Field Count Inconsistency
**File**: `docs/build-guide/01-datahub-foundation.md:100`

The build guide says "Verify: Model shows 21 fields" but the PromotionLog model spec has **33 fields** (counting from the JSON array in `PromotionLog-model-spec.json`):

Fields 1-25 (base + review): promotionId, devAccountId, prodAccountId, devPackageId, prodPackageId, initiatedBy, initiatedAt, status, componentsTotal, componentsCreated, componentsUpdated, componentsFailed, errorMessage, resultDetail, peerReviewStatus, peerReviewedBy, peerReviewedAt, peerReviewComments, adminReviewStatus, adminApprovedBy, adminApprovedAt, adminComments, branchId, branchName, integrationPackId

Fields 26-33 (integration pack + multi-env): integrationPackName, processName, targetEnvironment, isHotfix, hotfixJustification, testPromotionId, testDeployedAt, testIntegrationPackId, testIntegrationPackName, promotedFromTestBy

That is **35 fields** including `id` (auto-generated). Excluding `id`, it's 34 data fields. The build guide's "21 fields" appears to be a pre-multi-env count that was never updated when Phase 7 added 8 fields (Step 7.1).

**Impact**: Misleading verification step. Builder may think they misconfigured the model if the field count doesn't match.

### MAJ-4: packageAndDeploy Request Profile Missing `targetEnvironments` Array
**File**: `integration/profiles/packageAndDeploy-request.json:1-21`
**Spec**: `integration/flow-service/flow-service-spec.md:181` (targetEnvironments)

The flow-service-spec defines `targetEnvironments` as an array with `environmentId` and `environmentName` objects (lines 181-183). But the JSON profile (`packageAndDeploy-request.json`) has `targetAccountGroupId` (line 9) instead.

These are semantically different:
- `targetEnvironments` = array of specific environment targets
- `targetAccountGroupId` = an account group containing environments

This inconsistency means either the FSS spec is wrong (and deployment targets account groups, not individual environments) or the profile is wrong. The profile also uses `integrationPackId` (line 4) for existing pack selection, while the spec uses `existingPackId` (line 180).

**Impact**: Request contract ambiguity between spec and profile. Implementers will hit mapping errors.

---

## Minor Issues

### MIN-1: DevAccountAccess `isActive` is String, Not Boolean
**File**: `datahub/models/DevAccountAccess-model-spec.json:37-39`

`isActive` is typed as `String` with values `"true"` or `"false"`. The datahub-patterns rule says boolean fields should "Prefix with `is` or verb", implying boolean type. Using String for what is semantically a boolean adds comparison complexity (must do string equals, not boolean check) and risks typos like `"True"` or `"TRUE"`.

This is a DataHub platform constraint (DataHub may not support Boolean type natively), so it's a minor issue with a design rationale -- but it should be documented as a known constraint.

**Impact**: Low. String comparison works but is fragile. Risk of case-sensitive mismatches.

### MIN-2: ComponentMapping `mappingSource` vs datahub-patterns `source` Field
**File**: `datahub/models/ComponentMapping-model-spec.json:77-81`
**Rule**: `.claude/rules/datahub-patterns.md:41`

The datahub-patterns rule states: "All models MUST include a `source` field to track record origin." ComponentMapping uses `mappingSource` instead of `source`. DevAccountAccess and PromotionLog have no explicit `source` field at all (they rely on the DataHub `<batch src="...">` attribute for source tracking, which is correct for DataHub).

The rule itself is misleading -- DataHub tracks source via the batch submission source attribute, not a model field. ComponentMapping added `mappingSource` as an extra metadata field, not as the DataHub source mechanism. The rule should be clarified.

**Impact**: Low. Naming inconsistency between rule guidance and implementation, but no functional impact.

### MIN-3: create-golden-record-test.xml Does Not Include `mappingSource` Field
**File**: `datahub/api-requests/create-golden-record-test.xml:1-14`
**Model**: `datahub/models/ComponentMapping-model-spec.json:77-81`

The test XML omits the `mappingSource` field, which is optional. However, since this is a test payload submitted with `src="PROMOTION_ENGINE"`, it would be good practice to include `mappingSource` to verify the field round-trips correctly during Step 1.5.

**Impact**: Low. Optional field, test still validates core functionality.

### MIN-4: query-golden-record-test.xml Missing `mappingSource` in View
**File**: `datahub/api-requests/query-golden-record-test.xml:3-13`

The query view requests 9 fields but omits `mappingSource`. Since this is a test query, it should request all model fields to fully validate the model configuration.

**Impact**: Low. Incomplete test coverage of optional field.

### MIN-5: queryTestDeployments Response Missing `prodAccountId`
**File**: `integration/profiles/queryTestDeployments-response.json:6-22`
**Model**: `datahub/models/PromotionLog-model-spec.json:18-22`

The queryTestDeployments response profile omits `prodAccountId` (a required field on PromotionLog). While not strictly needed for the Page 9 UI, it could be useful for multi-tenant scenarios where the production target differs.

**Impact**: Low. The primary account is a system constant, but omitting it reduces response self-descriptiveness.

---

## Observations

### OBS-1: PromotionLog is a Monolithic Audit Model
The PromotionLog model has grown to 34+ fields spanning multiple concerns:
- Core promotion metadata (promotionId, devAccountId, componentsTotal, etc.)
- Peer review workflow (peerReviewStatus, peerReviewedBy, etc.)
- Admin review workflow (adminReviewStatus, adminApprovedBy, etc.)
- Branch lifecycle (branchId, branchName)
- Integration Pack tracking (integrationPackId, integrationPackName)
- Multi-environment state (targetEnvironment, isHotfix, testPromotionId, etc.)

This is a pragmatic design choice for DataHub (avoiding complex joins across models), but it creates a wide, sparse record -- most fields will be null for any given record state. DataHub's single-model query pattern makes this acceptable, but the model is reaching complexity thresholds where documentation of which fields are populated at each lifecycle stage becomes essential.

**Recommendation**: Add a field-population matrix showing which fields are populated at each status stage (IN_PROGRESS, COMPLETED, TEST_DEPLOYED, PENDING_PEER_REVIEW, etc.).

### OBS-2: No Explicit Cascading Referential Integrity
Cross-model references exist but are not enforced:
- `PromotionLog.devAccountId` references a DevAccountAccess account
- `PromotionLog.testPromotionId` references another PromotionLog record
- ComponentMapping's `devAccountId` relates to DevAccountAccess entries

DataHub does not enforce foreign keys, so referential integrity depends entirely on the integration processes. This is expected for DataHub, but it means orphan records are possible (e.g., deleting a DevAccountAccess record does not cascade to PromotionLog or ComponentMapping records referencing that account).

### OBS-3: resultDetail Field as JSON-in-String
**File**: `datahub/models/PromotionLog-model-spec.json:98-103`

The `resultDetail` field stores structured JSON as a string (up to 5000 characters). This is a pragmatic compromise -- DataHub does not support nested objects. However:
- No schema definition for the JSON content exists in the repo
- The 5000-character limit could be exceeded for promotions with many components
- Querying within `resultDetail` is impossible via DataHub queries

**Recommendation**: Document the `resultDetail` JSON schema as a separate spec file.

### OBS-4: DataHub Query Pattern for Exclusion Joins
**File**: `integration/flow-service/flow-service-spec.md:451-457` (queryTestDeployments)

Process E4 must exclude test deployments that already have a matching PRODUCTION record (`testPromotionId` = this `promotionId`). DataHub does not support JOIN or NOT EXISTS queries natively. This means Process E4 must:
1. Query all TEST_DEPLOYED records
2. Query all PRODUCTION records
3. Perform the exclusion join in-process (Groovy or map logic)

This is a scalability concern -- as promotion volume grows, these two full queries could become expensive. No pagination or caching strategy is documented.

---

## Multi-Environment Assessment

### What Works Well
1. **PromotionLog model completeness**: The 8 multi-env fields (targetEnvironment, isHotfix, hotfixJustification, testPromotionId, testDeployedAt, testIntegrationPackId, testIntegrationPackName, promotedFromTestBy) cover the three deployment paths comprehensively.
2. **Status lifecycle**: The extended status enum (TEST_DEPLOYING, TEST_DEPLOYED, TEST_DEPLOY_FAILED) properly distinguishes test deployment states.
3. **Hotfix audit trail**: The isHotfix + hotfixJustification fields provide a clean audit mechanism for emergency bypasses.
4. **testPromotionId linkage**: Linking PRODUCTION records back to their TEST predecessors enables full traceability.
5. **queryTestDeployments query template**: The `query-test-deployed-promotions.xml` correctly filters on both `targetEnvironment=TEST` and `status=TEST_DEPLOYED`.
6. **Branch preservation model**: The branch lifecycle extension (preserve for test, delete for production) is well-documented.

### What Needs Attention
1. **CRITICAL**: queryStatus response profile missing all multi-env fields (CRIT-1) -- this blocks environment-aware status pages.
2. **CRITICAL**: queryStatus spec-to-model field name mismatches (CRIT-2) -- ambiguous contract.
3. **MAJOR**: queryPeerReviewQueue missing multi-env context (MAJ-2) -- peer reviewers cannot see environment/hotfix badges.
4. **MAJOR**: Build guide field count stale (MAJ-3) -- misleading verification.
5. **No `componentsSkipped` field**: Architecture mentions SKIPPED components but the model has no field to track skipped count (distinct from failed). The `resultDetail` JSON presumably captures this, but `componentsSkipped` as a top-level field would parallel `componentsCreated`/`componentsUpdated`/`componentsFailed`.
6. **No `cancelledAt` or `cancelledBy` field**: Test deployment cancellation is mentioned as a future consideration but the model has no fields to support it.
7. **packageAndDeploy request profile** does not include `promotionId` -- Process D needs to know which PromotionLog record to update, but it's not in the request profile. The process presumably derives it from the branchId or other context.

---

## Summary

| Severity | Count | Key Theme |
|----------|-------|-----------|
| Critical | 2 | Profile-to-model misalignment blocks multi-env features |
| Major | 4 | Missing fields in profiles, stale documentation, spec/profile contract conflicts |
| Minor | 5 | Naming inconsistencies, incomplete test payloads, String booleans |
| Observations | 4 | Monolithic model growth, no referential integrity, JSON-in-string, exclusion join scalability |

The data models themselves are well-designed for the DataHub platform constraints. The primary risk area is the **disconnect between updated DataHub models (which include multi-env fields) and response profiles (which do not)**. The queryStatus and queryPeerReviewQueue profiles need urgent updates to surface multi-environment context to the Flow dashboard.

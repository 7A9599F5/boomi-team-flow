# Team 1 — DataHub Expert Findings

## Critical Findings

### C1. `source` Field Missing from DevAccountAccess and PromotionLog Models

**Rule**: `datahub-patterns.md:41` states: "All models MUST include a `source` field to track record origin."

**Finding**: Neither the DevAccountAccess model (`datahub/models/DevAccountAccess-model-spec.json`) nor the PromotionLog model (`datahub/models/PromotionLog-model-spec.json`) define a `source` field in their field lists. ComponentMapping has `mappingSource` (`ComponentMapping-model-spec.json:77`) but it is named `mappingSource`, not `source`, and it is marked `required: false`.

- `DevAccountAccess-model-spec.json` — 5 fields, none named `source` or `mappingSource`
- `PromotionLog-model-spec.json` — 35 fields, none named `source`
- `ComponentMapping-model-spec.json:77` — has `mappingSource` (not `source`), `required: false`

**Impact**: Without a `source` field, DataHub cannot distinguish which source contributed a record when multiple sources are configured. The `batch src="..."` attribute in API requests identifies the source at ingest time, but having an explicit source field on the model provides auditability in golden record queries and DataHub UI. The inconsistent naming (`mappingSource` vs `source`) also violates the convention.

**Recommendation**: Add a `source` field (type: String, required: true) to all three models, or document that the `batch src` attribute is sufficient and update `datahub-patterns.md` to reflect the actual pattern. Rename `mappingSource` to `source` on ComponentMapping for consistency.

---

### C2. Build Guide PromotionLog `status` Field Description Incomplete

**File**: `docs/build-guide/01-datahub-foundation.md:67`

The build guide lists the `status` field values as only `IN_PROGRESS`, `COMPLETED`, or `FAILED`. However, the model spec (`PromotionLog-model-spec.json:58`) documents a much richer lifecycle:

- `IN_PROGRESS` -> `COMPLETED` -> `TEST_DEPLOYING` -> `TEST_DEPLOYED` (test path)
- `IN_PROGRESS` -> `COMPLETED` -> `PENDING_PEER_REVIEW` -> `PEER_APPROVED` -> `PENDING_ADMIN_REVIEW` -> `ADMIN_APPROVED` -> `DEPLOYED` (production path)
- `PENDING_PEER_REVIEW` -> `PEER_REJECTED` (rejection branch)
- `PENDING_ADMIN_REVIEW` -> `ADMIN_REJECTED` (rejection branch)
- `TEST_DEPLOYING` -> `TEST_DEPLOY_FAILED` (test failure branch)

**Impact**: A builder following only the build guide would configure the model with insufficient understanding of the status lifecycle, potentially leading to integration process errors or DataHub queries that miss valid statuses.

**Recommendation**: Update the build guide status field notes to reference the full lifecycle or link to the model spec for the complete list.

---

## Major Findings

### M1. Build Guide PromotionLog Field Count Discrepancy

**File**: `docs/build-guide/01-datahub-foundation.md:100`

The verification step says "Model shows 34 fields" but the table in the build guide lists 35 field rows (promotionId through promotedFromTestBy). The model spec JSON also lists 35 fields (without an `id` field, unlike ComponentMapping).

Counted fields in build guide table (lines 60-94): 35 rows.

**Impact**: Builder may think they have an error during verification when the actual count does not match the documented expected count.

**Recommendation**: Correct the verification count to 35.

---

### M2. Build Guide PromotionLog Field Count Says 21 Earlier

**File**: `docs/build-guide/01-datahub-foundation.md:87`

An earlier verification line ("Verify: Model shows 21 fields") appears in an older section that was presumably from before the multi-environment fields were added. This is actually at line 87 and says "21 fields" but there's a second verification at line 100 that says "34 fields". Wait — re-reading: line 87 says "**Verify:** Model shows 21 fields, 1 match rule, source `PROMOTION_ENGINE`." and line 100 says "**Verify:** Model shows 34 fields, 1 match rule, source `PROMOTION_ENGINE`."

Looking more carefully, line 87 is the verify for the original field list (lines 58-81 = 22 rows), and then the additional fields continue from lines 82-94 (13 more rows), with line 100 being the actual verify for the complete model.

**Re-analysis**: Actually, re-reading the build guide, there's only ONE verify block at line 100. Line 87 says "**Verify:** Model shows 21 fields..." — but wait, let me recount. Lines 58-81 have the original 22 fields (promotionId through adminComments = 22 fields), not 21. Then lines 82-94 add 13 more fields = 35 total. The verify at line 100 says 34.

**Conclusion**: The verification count of "34 fields" at line 100 is incorrect; the correct count is 35 fields. There is no separate verify at line 87 — that was my misread.

**Impact**: Moderate — builders may be confused by the count mismatch.

---

### M3. `errorMessage` and `resultDetail` Type Inconsistency

**Files**:
- `PromotionLog-model-spec.json:93-94` — `errorMessage` type: `"String"`, `resultDetail` type: `"String"`
- `docs/build-guide/01-datahub-foundation.md:72-73` — `errorMessage` type: `Long Text`, `resultDetail` type: `Long Text`

The model spec defines these as `"String"` type, but the build guide specifies `"Long Text"`. In Boomi DataHub, `String` fields have a default character limit (typically 255 characters), while `Long Text` fields support larger content (up to 5000+ characters). Both descriptions mention "up to 5000 characters", which requires Long Text in DataHub.

**Impact**: If a builder follows the model spec JSON literally and creates String fields, the 5000-character content will be truncated. The build guide is correct; the model spec JSON is wrong.

**Recommendation**: Update `PromotionLog-model-spec.json` to use `"type": "Long Text"` for `errorMessage` and `resultDetail` fields.

---

### M4. ComponentMapping Model Missing `id` Field in Build Guide

**File**: `docs/build-guide/01-datahub-foundation.md:12-23`

The ComponentMapping model spec (`ComponentMapping-model-spec.json:7-12`) includes an `id` field ("Auto-generated DataHub record ID"). However, the build guide table (lines 12-23) does not list the `id` field.

The verification at line 30 says "10 fields" which matches the 9 listed + the implicit `id`. But if `id` is auto-generated by DataHub, it shouldn't need to be manually added. This ambiguity could confuse builders.

**Impact**: The `id` field in the JSON spec is unusual — DataHub auto-generates record IDs, so listing it as a model field is misleading. Other models (DevAccountAccess, PromotionLog) don't include an `id` field.

**Recommendation**: Either remove the `id` field from `ComponentMapping-model-spec.json` (since DataHub auto-generates it) and update the verify count to 9, or add `id` to all models for consistency. The build guide's approach of omitting it is correct.

---

### M5. `create-golden-record-test.xml` Does Not Follow `datahub-patterns.md` Format

**File**: `datahub/api-requests/create-golden-record-test.xml:1-14`

The test XML uses `<batch src="PROMOTION_ENGINE">` format:
```xml
<batch src="PROMOTION_ENGINE">
  <ComponentMapping>
    <devComponentId>test-dev-comp-001</devComponentId>
    ...
  </ComponentMapping>
</batch>
```

But `datahub-patterns.md:46-54` specifies the golden record format as:
```xml
<bns:SourceRecords xmlns:bns="..." xmlns:xsi="...">
  <bns:SourceRecord>
    <bns:ModelFieldName1>value1</bns:ModelFieldName1>
    ...
  </bns:SourceRecord>
</bns:SourceRecords>
```

**Analysis**: The `<batch>` format is actually the correct format for the DataHub Repository API's batch record ingest endpoint (`/mdm/api/v1/repositories/{id}/models/{model}/records`). The `bns:SourceRecords` format is for the older DataHub SOAP/legacy API. The build guide at `01-datahub-foundation.md:98-106` also uses the `<batch>` format.

**Impact**: The `datahub-patterns.md` golden record format specification is wrong or outdated. It describes the legacy `bns:SourceRecords` format, but the actual API requests and build guide use the modern `<batch>` format.

**Recommendation**: Update `datahub-patterns.md` to document the `<batch src="SOURCE_NAME">` format as the standard, since that's what the codebase actually uses. Or document both formats with clear guidance on which API endpoint uses which format.

---

### M6. `isActive` Field Uses String Instead of Boolean Type

**File**: `datahub/models/DevAccountAccess-model-spec.json:36-39`

```json
{
  "name": "isActive",
  "type": "String",
  "description": "Enable/disable access without deleting record (values: 'true' or 'false')"
}
```

The field uses `"type": "String"` but stores boolean-like values (`"true"` / `"false"`). The `datahub-patterns.md:13` convention says boolean fields should "Prefix with `is` or verb", which this field does. However, using String type for boolean semantics is error-prone — queries must match exact string values and there's no type validation.

**Mitigating factor**: Boomi DataHub does not have a native Boolean field type, so using String with `"true"` / `"false"` is the standard Boomi pattern. The build guide correctly documents this: `"true"` or `"false"` (string, not boolean) at `01-datahub-foundation.md:44`.

**Impact**: Low — this is a known Boomi DataHub limitation. The documentation is clear about the string representation.

**Recommendation**: No action needed, but add a note to `datahub-patterns.md` explicitly documenting this DataHub limitation for future reference.

---

## Minor Findings

### m1. `mappingSource` Field on ComponentMapping is `required: false`

**File**: `datahub/models/ComponentMapping-model-spec.json:80`

The `mappingSource` field is optional. Since this is the only field that tracks record origin for ComponentMapping (replacing the missing `source` field per datahub-patterns convention), having it be optional means some records could lack provenance information.

**Recommendation**: Change to `required: true` with a default value determined by the source contributing the record, or ensure all Integration processes always populate this field.

---

### m2. Query Template Missing `mappingSource` Field in View

**File**: `datahub/api-requests/query-golden-record-test.xml:3-13`

The query view includes 9 fields but omits `mappingSource`. This means query results won't include the source of the mapping, which could be relevant for debugging and auditing.

**Recommendation**: Add `<fieldId>mappingSource</fieldId>` to the view.

---

### m3. `adminApprovedBy` / `adminApprovedAt` Naming Inconsistency with Peer Review Fields

**Files**: `PromotionLog-model-spec.json:140-151`

Peer review fields follow the pattern: `peerReviewedBy`, `peerReviewedAt`
Admin review fields use: `adminApprovedBy`, `adminApprovedAt`

The admin fields imply "approved" but the admin can also reject. More consistent naming would be `adminReviewedBy` / `adminReviewedAt` to mirror the peer review pattern.

**Impact**: Functional — no bug, but semantically misleading when an admin rejects and the rejection is recorded in a field called `adminApprovedBy`.

**Recommendation**: Rename to `adminReviewedBy` and `adminReviewedAt` for consistency and semantic accuracy.

---

### m4. No `componentsSkipped` Counter Field

**File**: `PromotionLog-model-spec.json` (fields section)

The model tracks `componentsTotal`, `componentsCreated`, `componentsUpdated`, and `componentsFailed`, but there is no `componentsSkipped` counter. According to `docs/architecture.md:207`, when a component fails, its dependents are marked as SKIPPED. The SKIPPED count is presumably derivable from `componentsTotal - componentsCreated - componentsUpdated - componentsFailed`, but having an explicit field would improve query clarity.

Additionally, the flow-service-spec response for `executePromotion` (`flow-service-spec.md:149`) includes `connectionsSkipped` (count of shared connections not promoted), but this is not tracked in PromotionLog either.

**Recommendation**: Consider adding `componentsSkipped` and `connectionsSkipped` fields for complete audit trail.

---

### m5. `hotfixJustification` Character Limit Not Enforced at Model Level

**File**: `PromotionLog-model-spec.json:213`

The description says "up to 1000 characters" but DataHub String fields don't enforce character limits at the model level — enforcement must happen in the Integration process.

**Impact**: Low — character limit is documented and should be enforced in Process C / Process D.

**Recommendation**: Add a note in the build guide or model spec that character limit enforcement is the responsibility of the Integration process, not the DataHub model.

---

### m6. Process E4 Not Listed in CLAUDE.md or integration-patterns.md

**File**: `CLAUDE.md` (project root) lists 11 processes (A0, A-G, J) but `architecture.md:43` and `flow-service-spec.md:450` document 12 processes including Process E4 (queryTestDeployments). Similarly, `.claude/rules/integration-patterns.md` lists only 11 processes in the build order.

**Impact**: Minor — CLAUDE.md and integration-patterns.md are out of date with the current architecture. Developers referencing these files will miss Process E4.

**Recommendation**: Update CLAUDE.md and integration-patterns.md to include Process E4 in process lists and build order.

---

## Observations

### O1. DataHub Field Count Growing Large

PromotionLog has 35 fields in the model spec. While this is within DataHub's capabilities, large models can impact:
- Query performance (especially with views that select all fields)
- DataHub UI usability (golden record detail views become unwieldy)
- API request payload size

The model is already organized logically (core fields, peer review block, admin review block, branch lifecycle block, multi-env block), which helps. Future field additions should be carefully evaluated.

### O2. No Data Quality Steps Defined

All three models have empty `dataQualitySteps` arrays:
- `ComponentMapping-model-spec.json:103`
- `DevAccountAccess-model-spec.json:56`
- `PromotionLog-model-spec.json:266`

The build guide at `01-datahub-foundation.md:27` explicitly says "Skip the Data Quality tab (data quality is controlled by the integration processes)." This is a valid architectural decision — Integration processes enforce data quality before writing to DataHub. However, DataHub data quality steps could provide defense-in-depth (e.g., validating that `targetEnvironment` is always "TEST" or "PRODUCTION").

### O3. No `updatedAt` Timestamp on PromotionLog

PromotionLog tracks `initiatedAt` (when promotion started) but has no general `updatedAt` or `lastModifiedAt` field. Status transitions (COMPLETED, PEER_APPROVED, ADMIN_APPROVED, DEPLOYED, etc.) update the record, but the only way to know when a status change happened is through the specific review timestamp fields (`peerReviewedAt`, `adminApprovedAt`, `testDeployedAt`). There is no timestamp for the `IN_PROGRESS -> COMPLETED` transition or the `ADMIN_APPROVED -> DEPLOYED` transition.

### O4. `promotedFromTestBy` Field Has No Corresponding Timestamp

**File**: `PromotionLog-model-spec.json:245-250`

The field `promotedFromTestBy` tracks who initiated the test-to-production promotion, but there's no `promotedFromTestAt` timestamp field. The `initiatedAt` field on the PRODUCTION record would capture when the production promotion started, so this may be redundant, but documenting the relationship would help.

### O5. Test XML Template Uses Hardcoded Test Values

**File**: `datahub/api-requests/create-golden-record-test.xml`

Test values like `test-dev-comp-001`, `TEST_DEV_ACCT`, `PRIMARY_ACCT` are hardcoded. This is appropriate for a test template, but the build guide should emphasize that these records must be cleaned up (`01-datahub-foundation.md:195-197` does document cleanup, which is good).

---

## Multi-Environment Assessment

### Strengths

1. **`targetEnvironment` field** (`PromotionLog-model-spec.json:197`): Cleanly separates TEST and PRODUCTION records. Required field ensures every promotion is tagged with its target.

2. **`testPromotionId` linkage** (`PromotionLog-model-spec.json:218`): Enables tracing a PRODUCTION deployment back to its TEST predecessor. This is essential for the Dev->Test->Production path.

3. **Test deployment tracking fields** (`testDeployedAt`, `testIntegrationPackId`, `testIntegrationPackName`): Provide complete audit trail for test deployments.

4. **`isHotfix` and `hotfixJustification`** (`PromotionLog-model-spec.json:204-215`): Emergency bypass path is well-modeled with mandatory justification.

5. **`query-test-deployed-promotions.xml`** template: Provides a ready-made query for finding test deployments ready for production promotion.

6. **Branch lifecycle tracking**: `branchId` and `branchName` fields with documented lifecycle (set on creation, cleared after cleanup) support the complex multi-environment branch management.

### Gaps

1. **No `completedAt` timestamp**: When a promotion transitions from `IN_PROGRESS` to `COMPLETED`, no timestamp is recorded for the completion. Only `initiatedAt` exists. This makes it impossible to calculate promotion duration from DataHub alone.

2. **No `deployedAt` timestamp**: When status transitions to `DEPLOYED` (production), there's no dedicated deployment timestamp. `testDeployedAt` exists for test deployments but there's no equivalent `prodDeployedAt` for production deployments.

3. **Status lifecycle not formally defined**: The status field description (`PromotionLog-model-spec.json:58`) documents the lifecycle in prose, but there's no formal state machine or transition diagram. Valid transitions are implied but not explicitly constrained. For example, can a record go from `TEST_DEPLOYED` directly to `FAILED`? Can `ADMIN_REJECTED` be reversed?

4. **No test environment identifier**: The model tracks that a deployment targets TEST but doesn't store which specific test environment (environment ID/name). If the organization has multiple test environments, the model can't distinguish between them. The `targetEnvironments` array is in the `packageAndDeploy` request but not persisted in PromotionLog.

5. **SKIPPED status not in PromotionLog status enum**: Per `docs/architecture.md:207`, components can be marked SKIPPED, but this is a per-component result status (in `resultDetail` JSON), not a promotion-level status. This distinction is correct but could be documented more clearly.

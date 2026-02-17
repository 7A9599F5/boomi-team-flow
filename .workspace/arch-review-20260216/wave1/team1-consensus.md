# Team 1 — Data Architecture Consensus

**Team**: DataHub Expert, Data Modeling Architect, Devil's Advocate
**Date**: 2026-02-16
**Scope**: DataHub models, API request templates, build guide Phase 1, datahub-patterns rules

---

## Consensus Critical Findings

### CC-1: queryStatus Response Profile Missing 13 Multi-Environment Fields
**Source**: Architect CRIT-1, DA Confirmed
**File**: `integration/profiles/queryStatus-response.json`

The queryStatus response profile is missing all multi-environment fields added in Phase 7:
`branchId`, `branchName`, `integrationPackId`, `integrationPackName`, `processName`, `targetEnvironment`, `isHotfix`, `hotfixJustification`, `testPromotionId`, `testDeployedAt`, `testIntegrationPackId`, `testIntegrationPackName`, `promotedFromTestBy`.

Without `targetEnvironment`, the Flow dashboard cannot distinguish TEST vs PRODUCTION records in any status view. This blocks Phase 7 multi-environment functionality at the query layer.

**Action**: Add all 13 fields to `queryStatus-response.json`.

---

### CC-2: Flow-Service-Spec queryStatus Field Name Mismatches
**Source**: Architect CRIT-2, DA Confirmed
**File**: `integration/flow-service/flow-service-spec.md:269-272`

Three field names in the flow-service-spec queryStatus response do not match the PromotionLog model or the JSON profile:

| flow-service-spec | PromotionLog model / JSON profile | Resolution |
|---|---|---|
| `promotionDate` | `initiatedAt` | Fix spec to `initiatedAt` |
| `requestedBy` | `initiatedBy` | Fix spec to `initiatedBy` |
| `componentCount` | `componentsTotal` | Fix spec to `componentsTotal` |

Additionally, `packageVersion` (spec line 272) does not exist in the PromotionLog model. Either add `packageVersion` to the model or remove it from the spec.

**Action**: Update `flow-service-spec.md` queryStatus response to use model field names. Decide on `packageVersion`.

---

### CC-3: Build Guide PromotionLog Status Field Incomplete
**Source**: Expert C2, DA Confirmed
**File**: `docs/build-guide/01-datahub-foundation.md:67`

The build guide lists only 3 status values (`IN_PROGRESS`, `COMPLETED`, `FAILED`) but the model spec documents 11 statuses across 5 lifecycle paths:
- Test path: `IN_PROGRESS` -> `COMPLETED` -> `TEST_DEPLOYING` -> `TEST_DEPLOYED`
- Production path: `IN_PROGRESS` -> `COMPLETED` -> `PENDING_PEER_REVIEW` -> `PEER_APPROVED` -> `PENDING_ADMIN_REVIEW` -> `ADMIN_APPROVED` -> `DEPLOYED`
- Rejection branches: `PEER_REJECTED`, `ADMIN_REJECTED`
- Test failure: `TEST_DEPLOY_FAILED`

**Action**: Update build guide status field notes to list all valid status values or reference the model spec.

---

## Consensus Major Findings

### CM-1: queryPeerReviewQueue Response Missing Multi-Environment Fields
**Source**: Architect MAJ-2, DA Confirmed
**File**: `integration/profiles/queryPeerReviewQueue-response.json`

Missing `targetEnvironment`, `isHotfix`, and `branchId`. Build guide Phase 7 (`docs/build-guide/22-phase7-multi-environment.md:181-186`) requires these for Pages 5-6 environment/hotfix badges.

**Action**: Add `targetEnvironment`, `isHotfix`, `hotfixJustification`, and `branchId` to the response profile.

---

### CM-2: `errorMessage` / `resultDetail` Type: String vs Long Text
**Source**: Expert M3, DA Confirmed
**File**: `datahub/models/PromotionLog-model-spec.json:93-102`

Model spec says `"type": "String"`. Build guide says `Long Text`. Both descriptions mention 5000 characters. Standard DataHub String fields truncate at ~255 characters. The build guide is correct.

**Action**: Update model spec to use `"type": "Long Text"` for `errorMessage` and `resultDetail`.

---

### CM-3: Build Guide PromotionLog Field Count Wrong
**Source**: Expert M1, Architect MAJ-3, DA Confirmed
**File**: `docs/build-guide/01-datahub-foundation.md:100`

Verify line says "34 fields" but the table lists 35 field rows (promotionId through promotedFromTestBy, lines 60-94).

**Action**: Change "34 fields" to "35 fields" at line 100.

---

### CM-4: datahub-patterns.md XML Format Outdated
**Source**: Expert M5, DA Confirmed
**File**: `.claude/rules/datahub-patterns.md:46-54`

The golden record XML format section documents the legacy `bns:SourceRecords` namespace format, but all actual API request templates and the build guide use the modern `<batch src="SOURCE_NAME">` format.

**Action**: Update datahub-patterns.md to document the `<batch>` format as standard.

---

### CM-5: packageAndDeploy Request Profile Naming Conflicts
**Source**: Architect MAJ-4, DA Partially Confirmed
**File**: `integration/profiles/packageAndDeploy-request.json`

Two naming mismatches between profile and flow-service-spec:
1. Profile `targetAccountGroupId` (line 9) vs spec `targetEnvironments` array — different concepts
2. Profile `integrationPackId` (line 4) vs spec `existingPackId` (line 180) — same concept, different name

**Action**: Align profile and spec. Determine whether deployment targets are account groups (simpler, profile approach) or individual environments (more flexible, spec approach) and update both documents to match.

---

### CM-6: `packageVersion` Missing from PromotionLog Model
**Source**: Architect CRIT-2 sub-finding, DA Confirmed
**File**: `datahub/models/PromotionLog-model-spec.json`, `integration/flow-service/flow-service-spec.md:272`

The queryStatus spec response includes `packageVersion` but no such field exists in PromotionLog. The `queryPeerReviewQueue-response.json` also includes `packageVersion` (line 16). Either the model needs the field or the spec/profiles are wrong.

**Action**: Add `packageVersion` (String, optional) to PromotionLog model, or remove from spec and profiles.

---

## Consensus Minor Findings

### Cm-1: `adminApprovedBy` / `adminApprovedAt` Naming Inconsistency
**Source**: Expert m3
**Files**: `PromotionLog-model-spec.json:140-151`

Admin review fields use "Approved" language (`adminApprovedBy`, `adminApprovedAt`) but these fields also store rejection data. Peer review uses neutral naming (`peerReviewedBy`, `peerReviewedAt`).

**Action**: Consider renaming to `adminReviewedBy` / `adminReviewedAt` for consistency. Low priority — functional code works regardless.

---

### Cm-2: `id` Field Inconsistency Across Models
**Source**: Expert M4 (downgraded by DA)
**File**: `datahub/models/ComponentMapping-model-spec.json:7-12`

ComponentMapping includes an `id` field; DevAccountAccess and PromotionLog do not. DataHub auto-generates record IDs, so this field is a documentation artifact.

**Action**: Remove `id` from ComponentMapping spec. Update build guide verify from "10 fields" to "9 fields" at line 30.

---

### Cm-3: datahub-patterns.md `source` Field Rule Incorrect
**Source**: Expert C1 (downgraded by DA), Architect MIN-2
**File**: `.claude/rules/datahub-patterns.md:41`

The rule says "All models MUST include a `source` field" but DataHub inherently tracks source via the `<batch src>` attribute. A model-level `source` field is redundant. ComponentMapping has `mappingSource` (optional, different name) while the other two models have no source field.

**Consensus**: Both the Architect and DA agree the rule is misleading. DataHub's built-in source tracking is sufficient.

**Action**: Update rule to: "All models MUST be configured with appropriate DataHub Sources via the Sources tab. Record origin is tracked automatically via the `batch src` attribute at ingest time. An explicit `source` model field is optional."

---

### Cm-4: No `componentsSkipped` Counter
**Source**: Expert m4, Architect multi-env assessment
**File**: `datahub/models/PromotionLog-model-spec.json`

Model tracks created/updated/failed but not skipped. Count is derivable (`total - created - updated - failed`) but an explicit field improves clarity.

**Action**: Consider adding `componentsSkipped` (Number, optional, default 0).

---

### Cm-5: Process E4 Missing from CLAUDE.md and integration-patterns.md
**Source**: Expert m6
**Files**: Root `CLAUDE.md`, `.claude/rules/integration-patterns.md`

Both files list 11 processes but architecture.md and flow-service-spec.md document 12 (including Process E4 — queryTestDeployments).

**Action**: Update both files to include Process E4.

---

### Cm-6: SKIPPED Status Scope Ambiguity
**Source**: Architect MAJ-1 (downgraded by DA), Expert multi-env assessment
**File**: `docs/architecture.md:207`

SKIPPED is a per-component action value within `resultDetail` JSON, not a promotion-level status. The architecture.md language is slightly ambiguous.

**Action**: Add clarification to architecture.md: "SKIPPED is a per-component action within the `resultDetail` JSON, not a promotion-level status value."

---

## Consensus Observations

### CO-1: PromotionLog Model Complexity
All three reviewers note the model has grown large (35 fields). This is pragmatic for DataHub (no joins) but approaching the threshold where a field-population matrix is needed to document which fields are populated at each status stage.

**Recommendation**: Create a state/field matrix document showing field population per status.

### CO-2: Missing Lifecycle Timestamps
No timestamp exists for: `IN_PROGRESS` -> `COMPLETED`, `COMPLETED` -> `PENDING_PEER_REVIEW`, or `ADMIN_APPROVED` -> `DEPLOYED` transitions. Only specific review timestamps (`peerReviewedAt`, `adminApprovedAt`, `testDeployedAt`) are tracked.

**Recommendation**: Consider adding `completedAt` and `deployedAt` fields for complete audit trail and duration calculation.

### CO-3: No Data Quality Steps
All models have empty `dataQualitySteps`. The build guide explicitly says "data quality is controlled by the integration processes." Valid architecture decision but DataHub data quality could provide defense-in-depth.

### CO-4: `resultDetail` JSON Schema Undocumented
The `resultDetail` field stores structured JSON as a string, but no formal schema for that JSON content exists. The build guide at `10-process-c-execute-promotion.md:24` lists expected fields but not in a schema format.

### CO-5: Exclusion Join Scalability (Process E4)
Process E4 must perform in-memory exclusion joins between TEST_DEPLOYED and PRODUCTION records. Small scale now but could grow.

---

## Multi-Environment Coherence Assessment

### Model Layer: Strong
The PromotionLog model comprehensively supports all three deployment paths (Dev->Test->Prod, hotfix, rejection). Key multi-env fields (`targetEnvironment`, `testPromotionId`, `isHotfix`, `hotfixJustification`, branch tracking, test Integration Pack tracking) are well-designed and cover the documented use cases.

### Profile Layer: Incomplete (Blocking)
Two response profiles (`queryStatus-response.json`, `queryPeerReviewQueue-response.json`) are missing multi-env fields required for Phase 7 UI rendering. The `queryTestDeployments-response.json` profile is complete.

### Spec Layer: Inconsistent
The flow-service-spec has field name mismatches with the model and profiles, plus references a field (`packageVersion`) that doesn't exist in the model.

### Documentation Layer: Stale
Build guide field counts, status field documentation, and reference documents (CLAUDE.md, integration-patterns.md) have not been updated for Phase 7 additions.

### Overall Verdict
The DataHub model architecture is sound and well-designed for the multi-environment workflow. The critical issues are all at the **profile and documentation layers**, not the model layer. Fixing the 3 critical and 6 major issues identified above would bring the system to full multi-environment readiness.

---

## Areas of Agreement (All Three Reviewers)

1. PromotionLog model design is comprehensive and appropriate for DataHub constraints
2. Match rules are correctly configured on all three models
3. Source configurations are appropriate (PROMOTION_ENGINE, ADMIN_SEEDING, ADMIN_CONFIG)
4. `isActive` as String is a DataHub platform limitation, not a design flaw
5. Branch lifecycle tracking (`branchId`/`branchName` with null-on-cleanup) is well-modeled
6. Test deployment tracking fields are complete in the model
7. The `<batch>` XML format is correct; `datahub-patterns.md` needs updating
8. SKIPPED is per-component, not promotion-level — documentation needs minor clarification

## Unresolved Debates

1. **`packageVersion` field**: Should it be added to PromotionLog, or removed from the spec and profiles? Arguments both ways — adding it improves the audit trail but grows the already-large model further.
2. **`completedAt` / `deployedAt` timestamps**: Useful for audit/duration tracking but adds 2 more fields to a 35-field model. Could alternatively rely on DataHub's internal record modification timestamps.
3. **`componentsSkipped` counter**: Explicit field vs derivable calculation. Pragmatism favors the derivable approach to avoid further model growth.

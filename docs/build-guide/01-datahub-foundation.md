## Phase 1: DataHub Foundation

DataHub stores the three models that power the promotion engine: component mappings, access control, and audit logs. Each model must be created, published, and deployed before any integration process can run.

### Step 1.1 -- Create ComponentMapping Model

1. Navigate to **Services --> DataHub --> Repositories** and select your repository (or create one).
2. Click **Models** in the left sidebar, then **New Model**.
3. Enter Model Name: `ComponentMapping`, Root Element: `ComponentMapping`.
4. Add each field per `/datahub/models/ComponentMapping-model-spec.json`:

| Field Name | Type | Required | Match Field | Notes |
|------------|------|----------|-------------|-------|
| `devComponentId` | String | Yes | Yes | Boomi component UUID from dev account |
| `devAccountId` | String | Yes | Yes | Dev sub-account identifier |
| `prodComponentId` | String | Yes | No | Corresponding component ID in primary account |
| `componentName` | String | Yes | No | Human-readable component name |
| `componentType` | String | Yes | No | e.g., `process`, `connection`, `map`, `profile.xml` |
| `prodAccountId` | String | Yes | No | Primary Boomi account ID |
| `prodLatestVersion` | Number | Yes | No | Latest version number in primary account |
| `lastPromotedAt` | Date | Yes | No | Format: `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'` |
| `lastPromotedBy` | String | Yes | No | SSO user email of promoter |
| `mappingSource` | String | No | No | `"PROMOTION_ENGINE"` or `"ADMIN_SEEDING"` |

5. Navigate to **Match Rules** tab. Add a compound **Exact** match on both `devComponentId` AND `devAccountId`.
6. Navigate to **Sources** tab. Click **Add Source** --> name: `PROMOTION_ENGINE`, type: **Contribute Only**. Add a second source --> name: `ADMIN_SEEDING`, type: **Contribute Only** (used by admins to seed connection mappings).
7. Skip the **Data Quality** tab (data quality is controlled by the integration processes).
8. Click **Save**, then **Publish**, then **Deploy** to the repository.

**Verify:** Confirm the model appears under **DataHub --> Repositories --> [your repo] --> Models** with status "Deployed". The model should show 10 fields, 1 match rule, and 2 sources in the summary.

### Step 1.2 -- Create DevAccountAccess Model

1. Navigate to **Services --> DataHub --> Repositories --> [your repo] --> Models --> New Model**.
2. Enter Model Name: `DevAccountAccess`, Root Element: `DevAccountAccess`.
3. Add fields per `/datahub/models/DevAccountAccess-model-spec.json`:

| Field Name | Type | Required | Match Field | Notes |
|------------|------|----------|-------------|-------|
| `ssoGroupId` | String | Yes | Yes | Azure AD group object ID |
| `ssoGroupName` | String | Yes | No | Display name of Azure AD group |
| `devAccountId` | String | Yes | Yes | Boomi dev sub-account ID |
| `devAccountName` | String | Yes | No | Human-readable dev account name |
| `isActive` | String | Yes | No | `"true"` or `"false"` (string, not boolean) |

4. Match rule: **Exact** compound match on `ssoGroupId` + `devAccountId`.
5. Source: `ADMIN_CONFIG` (Contribute Only).
6. Skip Data Quality. **Save --> Publish --> Deploy**.

**Verify:** Model shows 5 fields, 1 compound match rule, source `ADMIN_CONFIG`.

### Step 1.3 -- Create PromotionLog Model

1. Navigate to **Services --> DataHub --> Repositories --> [your repo] --> Models --> New Model**.
2. Enter Model Name: `PromotionLog`, Root Element: `PromotionLog`.
3. Add fields per `/datahub/models/PromotionLog-model-spec.json`:

| Field Name | Type | Required | Match Field | Notes |
|------------|------|----------|-------------|-------|
| `promotionId` | String | Yes | Yes | UUID for each promotion run |
| `devAccountId` | String | Yes | No | Source dev sub-account ID |
| `prodAccountId` | String | Yes | No | Target production account ID |
| `devPackageId` | String | Yes | No | PackagedComponent packageId |
| `prodPackageId` | String | No | No | PackagedComponent packageId created in production |
| `initiatedBy` | String | Yes | No | SSO user email |
| `initiatedAt` | Date | Yes | No | Format: `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'` |
| `status` | String | Yes | No | `IN_PROGRESS`, `COMPLETED`, or `FAILED` |
| `componentsTotal` | Number | Yes | No | Total components in dependency tree |
| `componentsCreated` | Number | Yes | No | New components created |
| `componentsUpdated` | Number | Yes | No | Existing components updated |
| `componentsFailed` | Number | Yes | No | Failed component count |
| `errorMessage` | Long Text | No | No | Up to 5000 chars; present when status=FAILED |
| `resultDetail` | Long Text | No | No | Up to 5000 chars; JSON per-component results |
| `peerReviewStatus` | String | No | No | `PENDING_PEER_REVIEW`, `PEER_APPROVED`, `PEER_REJECTED` |
| `peerReviewedBy` | String | No | No | Email of peer reviewer |
| `peerReviewedAt` | Date | No | No | Timestamp of peer review action |
| `peerReviewComments` | String | No | No | Peer reviewer comments (up to 500 chars) |
| `adminReviewStatus` | String | No | No | `PENDING_ADMIN_REVIEW`, `ADMIN_APPROVED`, `ADMIN_REJECTED` |
| `adminApprovedBy` | String | No | No | Email of admin reviewer |
| `adminApprovedAt` | Date | No | No | Timestamp of admin review action |
| `adminComments` | String | No | No | Admin reviewer comments (up to 500 chars) |
| `branchId` | String | No | No | Promotion branch ID — cleared after branch cleanup |
| `branchName` | String | No | No | Promotion branch name (e.g., `promo-{promotionId}`) |
| `integrationPackId` | String | No | No | Integration Pack ID — populated after deploy |
| `integrationPackName` | String | No | No | Human-readable Integration Pack name |
| `processName` | String | No | No | Root process name — used for pack suggestions |
| `targetEnvironment` | String | Yes | No | `"TEST"` or `"PRODUCTION"` |
| `isHotfix` | String | No | No | `"true"` / `"false"` — flags emergency production bypass |
| `hotfixJustification` | String | No | No | Required when isHotfix=`"true"` (up to 1000 chars) |
| `testPromotionId` | String | No | No | Links PRODUCTION record to its TEST predecessor |
| `testDeployedAt` | Date | No | No | When test deployment completed |
| `testIntegrationPackId` | String | No | No | Test Integration Pack ID |
| `testIntegrationPackName` | String | No | No | Test Integration Pack name |
| `promotedFromTestBy` | String | No | No | Email of user who initiated test→production promotion |

4. Match rule: **Exact** on `promotionId` (single field).
5. Source: `PROMOTION_ENGINE` (Contribute Only).
6. Skip Data Quality. **Save --> Publish --> Deploy**.

**Verify:** Model shows 34 fields, 1 match rule, source `PROMOTION_ENGINE`.

### Step 1.4 -- Seed DevAccountAccess Data

Create at least one golden record for each SSO group --> dev account mapping. Use the DataHub Repository API to POST a batch:

```bash
# Linux/macOS -- seed DevAccountAccess record
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/mdm/api/v1/repositories/{repositoryId}/models/DevAccountAccess/records" \
  -H "Content-Type: application/xml" \
  -d '<batch src="ADMIN_CONFIG">
  <DevAccountAccess>
    <ssoGroupId>YOUR_AZURE_AD_GROUP_ID</ssoGroupId>
    <ssoGroupName>Boomi Dev - Team Alpha</ssoGroupName>
    <devAccountId>YOUR_DEV_ACCOUNT_ID</devAccountId>
    <devAccountName>DevTeamAlpha</devAccountName>
    <isActive>true</isActive>
  </DevAccountAccess>
</batch>'
```

```powershell
# Windows -- seed DevAccountAccess record
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = @"
<batch src="ADMIN_CONFIG">
  <DevAccountAccess>
    <ssoGroupId>YOUR_AZURE_AD_GROUP_ID</ssoGroupId>
    <ssoGroupName>Boomi Dev - Team Alpha</ssoGroupName>
    <devAccountId>YOUR_DEV_ACCOUNT_ID</devAccountId>
    <devAccountName>DevTeamAlpha</devAccountName>
    <isActive>true</isActive>
  </DevAccountAccess>
</batch>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/v1/repositories/{repositoryId}/models/DevAccountAccess/records" `
  -Method POST -Headers $headers -Body $body
```

Repeat for each SSO group and dev account combination. One group can map to multiple dev accounts, and multiple groups can share the same dev account.

### Step 1.5 -- Test DataHub CRUD

Validate that all three models accept creates, queries, and upserts before moving on. Use the test payloads in `/datahub/api-requests/`.

#### 1.5a -- Create a Test Golden Record

POST the test payload from `/datahub/api-requests/create-golden-record-test.xml` to the ComponentMapping model:

```bash
# Linux/macOS -- create test golden record
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/mdm/api/v1/repositories/{repositoryId}/models/ComponentMapping/records" \
  -H "Content-Type: application/xml" \
  -d @datahub/api-requests/create-golden-record-test.xml
```

```powershell
# Windows -- create test golden record
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = Get-Content -Raw "datahub/api-requests/create-golden-record-test.xml"
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/v1/repositories/{repositoryId}/models/ComponentMapping/records" `
  -Method POST -Headers $headers -Body $body
```

**Verify:** Response returns HTTP 200 with a record ID. Check the DataHub UI: **DataHub --> Repositories --> [your repo] --> ComponentMapping --> Golden Records** -- the test record should appear.

#### 1.5b -- Query the Test Record

POST the query payload from `/datahub/api-requests/query-golden-record-test.xml`:

```bash
# Linux/macOS -- query test golden record
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/mdm/api/v1/repositories/{repositoryId}/models/ComponentMapping/records/query" \
  -H "Content-Type: application/xml" \
  -d @datahub/api-requests/query-golden-record-test.xml
```

```powershell
# Windows -- query test golden record
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = Get-Content -Raw "datahub/api-requests/query-golden-record-test.xml"
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/v1/repositories/{repositoryId}/models/ComponentMapping/records/query" `
  -Method POST -Headers $headers -Body $body
```

**Verify:** Response contains exactly one record with `devComponentId=test-dev-comp-001` and all fields populated.

#### 1.5c -- Test Upsert (Match Rule Validation)

POST the same create payload again from step 1.5a. Because the compound match rule matches on `devComponentId` + `devAccountId`, the existing record should be **updated** rather than duplicated.

**Verify:** Query again using step 1.5b. Confirm still exactly one record (no duplicate). The record's `lastPromotedAt` and other fields should reflect the second POST.

#### 1.5d -- Clean Up

Delete the test record from the DataHub UI: navigate to **DataHub --> Repositories --> [your repo] --> ComponentMapping --> Golden Records**, select the test record, and click **Delete**.

---

---
Prev: [Overview & Prerequisites](00-overview.md) | Next: [Phase 2a: HTTP Client Setup](02-http-client-setup.md) | [Back to Index](index.md)

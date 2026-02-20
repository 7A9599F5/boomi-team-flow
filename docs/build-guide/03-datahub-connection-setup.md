### Step 2.3 -- Create DataHub Connection

#### Via API

```bash
# Linux/macOS -- create DataHub Connection component
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - DataHub Connection" type="connector-settings" subType="datahub" folderFullPath="/Promoted/Connections">
  <bns:object>
    <bns:hubCloudName>US_EAST</bns:hubCloudName>
    <bns:authToken>{hubAuthToken}</bns:authToken>
    <bns:repositoryId>{repositoryId}</bns:repositoryId>
  </bns:object>
</bns:Component>'
```

```powershell
# Windows -- create DataHub Connection component
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
    Accept         = "application/xml"
}
$body = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - DataHub Connection" type="connector-settings" subType="datahub" folderFullPath="/Promoted/Connections">
  <bns:object>
    <bns:hubCloudName>US_EAST</bns:hubCloudName>
    <bns:authToken>{hubAuthToken}</bns:authToken>
    <bns:repositoryId>{repositoryId}</bns:repositoryId>
  </bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" `
  -Method POST -Headers $headers -Body $body
```

> **Note:** The Hub Authentication Token must still be retrieved from the DataHub UI: **Services --> DataHub --> Repositories --> [your repo] --> Configure** tab. There is no API to generate this token. Connection testing also has no API equivalent.

**Verify:** Capture the `componentId` from the response for use in operation creation.

#### Via UI (Manual Fallback)

1. Navigate to **Build --> New Component --> Connector --> Connection**.
2. Select connector type: **Boomi DataHub**.
3. Set component name: `PROMO - DataHub Connection`.
4. Configure:

| Setting | Value |
|---------|-------|
| **Hub Cloud Name** | Select your Boomi cloud region (e.g., `US East`, `EU West`) |
| **Hub Authentication Token** | From DataHub UI (see below) |
| **Repository** | Auto-detected after token entry; select your repository |

5. To find your Hub Auth Token: navigate to **Services --> DataHub --> Repositories --> [your repo] --> Configure** tab. Copy the **Authentication Token** value.
6. Click **Test Connection**. A successful test confirms the token is valid and the repository is accessible.
7. **Save**.

**Verify:** The connection test must succeed. If it fails:
- Confirm you copied the full token string (no trailing spaces).
- Confirm the selected Hub Cloud Name matches your DataHub deployment region.
- Confirm the repository is deployed (Step 1.1-1.3 completed the deploy step for each model).

### Step 2.4 -- Create DataHub Operations

Create 7 DataHub operations -- a Query and an Update for each of the 3 models, plus a Delete for ComponentMapping. Each operation uses the `PROMO - DataHub Connection` from Step 2.3.

#### Quick Reference Table

| # | Component Name | Model | Action | Profile Source |
|---|---------------|-------|--------|---------------|
| 1 | PROMO - DH Op - Query ComponentMapping | ComponentMapping | Query Golden Records | Import from model |
| 2 | PROMO - DH Op - Update ComponentMapping | ComponentMapping | Update Golden Records | Import from model |
| 3 | PROMO - DH Op - Delete ComponentMapping | ComponentMapping | Delete Golden Records | Import from model |
| 4 | PROMO - DH Op - Query DevAccountAccess | DevAccountAccess | Query Golden Records | Import from model |
| 5 | PROMO - DH Op - Update DevAccountAccess | DevAccountAccess | Update Golden Records | Import from model |
| 6 | PROMO - DH Op - Query PromotionLog | PromotionLog | Query Golden Records | Import from model |
| 7 | PROMO - DH Op - Update PromotionLog | PromotionLog | Update Golden Records | Import from model |

#### Step 2.4.1 -- PROMO - DH Op - Query ComponentMapping

##### Via API

```bash
# Linux/macOS -- create DataHub Query operation for ComponentMapping
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - DH Op - Query ComponentMapping" type="connector-action" subType="datahub" folderFullPath="/Promoted/Operations">
  <bns:object>
    <bns:connectorId>{dhConnectionComponentId}</bns:connectorId>
    <bns:action>QUERY</bns:action>
    <bns:modelName>ComponentMapping</bns:modelName>
  </bns:object>
</bns:Component>'
```

```powershell
# Windows -- create DataHub Query operation for ComponentMapping
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
    Accept         = "application/xml"
}
$body = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - DH Op - Query ComponentMapping" type="connector-action" subType="datahub" folderFullPath="/Promoted/Operations">
  <bns:object>
    <bns:connectorId>{dhConnectionComponentId}</bns:connectorId>
    <bns:action>QUERY</bns:action>
    <bns:modelName>ComponentMapping</bns:modelName>
  </bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" `
  -Method POST -Headers $headers -Body $body
```

**Verify:** Response returns HTTP 200 with the created component. Capture the `componentId` from the response.

##### Batch Creation Template for All 7 Operations

To create all 7 DataHub operations via API, use the same curl/PowerShell template above, substituting values from this table:

| Step | Operation Name | Action | Model |
|------|---------------|--------|-------|
| 2.4.1 | PROMO - DH Op - Query ComponentMapping | QUERY | ComponentMapping |
| 2.4.2 | PROMO - DH Op - Update ComponentMapping | UPDATE | ComponentMapping |
| 2.4.3 | PROMO - DH Op - Delete ComponentMapping | DELETE | ComponentMapping |
| 2.4.4 | PROMO - DH Op - Query DevAccountAccess | QUERY | DevAccountAccess |
| 2.4.5 | PROMO - DH Op - Update DevAccountAccess | UPDATE | DevAccountAccess |
| 2.4.6 | PROMO - DH Op - Query PromotionLog | QUERY | PromotionLog |
| 2.4.7 | PROMO - DH Op - Update PromotionLog | UPDATE | PromotionLog |

> **Note:** DataHub operations auto-generate request/response profiles when created via the UI's Import feature. When creating via API, the profile import step must be handled separately -- use the [API-First Discovery Workflow](22-api-automation-guide.md#api-first-discovery-workflow) to capture the exact XML structure from a UI-created operation.

##### Via UI (Manual Fallback)

1. Navigate to **Build --> New Component --> Connector --> Operation**.
2. Select connector type: **Boomi DataHub**. Name: `PROMO - DH Op - Query ComponentMapping`.
3. Connection: select `PROMO - DataHub Connection`.
4. Action: **Query Golden Records**.
5. Click **Import** on the Request/Response profile panel. Select model: `ComponentMapping`. Boomi auto-generates the XML request and response profiles based on the model fields.
6. **Save**.

#### Step 2.4.2 -- PROMO - DH Op - Update ComponentMapping

> **API Alternative:** Use the batch creation template above with this operation's values from the lookup table.

1. **Build --> New Component --> Connector --> Operation --> Boomi DataHub**.
2. Name: `PROMO - DH Op - Update ComponentMapping`.
3. Connection: `PROMO - DataHub Connection`.
4. Action: **Update Golden Records**.
5. Click **Import**, select model: `ComponentMapping`. The auto-generated profile includes the `<batch src="PROMOTION_ENGINE">` wrapper and all model fields.
6. **Save**.

#### Step 2.4.3 -- PROMO - DH Op - Delete ComponentMapping

> **API Alternative:** Use the batch creation template above with this operation's values from the lookup table.

1. **Build --> New Component --> Connector --> Operation --> Boomi DataHub**.
2. Name: `PROMO - DH Op - Delete ComponentMapping`.
3. Connection: `PROMO - DataHub Connection`.
4. Action: **Delete Golden Records**.
5. Click **Import**, select model: `ComponentMapping`. The auto-generated profile includes the match key fields needed to identify the record to delete.
6. **Save**.

#### Step 2.4.4 -- PROMO - DH Op - Query DevAccountAccess

> **API Alternative:** Use the batch creation template above with this operation's values from the lookup table.

Follows the same pattern as Step 2.4.1 with these differences:

1. Name: `PROMO - DH Op - Query DevAccountAccess`.
2. Action: **Query Golden Records**.
3. Import from model: `DevAccountAccess`.
4. **Save**.

#### Step 2.4.5 -- PROMO - DH Op - Update DevAccountAccess

> **API Alternative:** Use the batch creation template above with this operation's values from the lookup table.

Follows the same pattern as Step 2.4.2 with these differences:

1. Name: `PROMO - DH Op - Update DevAccountAccess`.
2. Action: **Update Golden Records**.
3. Import from model: `DevAccountAccess`. The auto-generated profile uses `<batch src="ADMIN_CONFIG">` as the source wrapper.
4. **Save**.

#### Step 2.4.6 -- PROMO - DH Op - Query PromotionLog

> **API Alternative:** Use the batch creation template above with this operation's values from the lookup table.

Follows the same pattern as Step 2.4.1 with these differences:

1. Name: `PROMO - DH Op - Query PromotionLog`.
2. Action: **Query Golden Records**.
3. Import from model: `PromotionLog`.
4. **Save**.

#### Step 2.4.7 -- PROMO - DH Op - Update PromotionLog

> **API Alternative:** Use the batch creation template above with this operation's values from the lookup table.

Follows the same pattern as Step 2.4.2 with these differences:

1. Name: `PROMO - DH Op - Update PromotionLog`.
2. Action: **Update Golden Records**.
3. Import from model: `PromotionLog`. The auto-generated profile uses `<batch src="PROMOTION_ENGINE">` as the source wrapper.
4. **Save**.

### Step 2.5 -- Verify Phase 2

Run two verification tests to confirm the connections and operations work end-to-end.

#### 2.5a -- Test HTTP Client Operation (GET ComponentMetadata)

Call the Platform API directly to verify the HTTP Client connection and one representative operation. Replace `{accountId}` with your primary account ID and `{componentId}` with any known component ID:

```bash
# Linux/macOS -- test GET ComponentMetadata
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/ComponentMetadata/{componentId}"
```

```powershell
# Windows -- test GET ComponentMetadata
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization = "Basic $cred"
    Accept        = "application/xml"
}
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/ComponentMetadata/{componentId}" `
  -Method GET -Headers $headers
```

**Verify:** Response returns HTTP 200 with a `<bns:ComponentMetadata>` element containing `componentId`, `name`, `type`, and `version` attributes. If you get a 401, recheck the API token. If you get a 404, confirm the component ID exists in the account.

#### 2.5b -- Test DataHub Query (ComponentMapping)

Query the ComponentMapping model to confirm the DataHub connection and operations are functional. If you deleted the test record from Step 1.5d, this query should return zero results (which still confirms the connection works):

```bash
# Linux/macOS -- test DataHub query
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/mdm/api/v1/repositories/{repositoryId}/models/ComponentMapping/records/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="10">
  <view>
    <fieldId>devComponentId</fieldId>
    <fieldId>componentName</fieldId>
  </view>
</RecordQueryRequest>'
```

```powershell
# Windows -- test DataHub query
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = @"
<RecordQueryRequest limit="10">
  <view>
    <fieldId>devComponentId</fieldId>
    <fieldId>componentName</fieldId>
  </view>
</RecordQueryRequest>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/v1/repositories/{repositoryId}/models/ComponentMapping/records/query" `
  -Method POST -Headers $headers -Body $body
```

**Verify:** Response returns HTTP 200 with a `<RecordQueryResponse>` element. Zero results is acceptable at this stage -- the key confirmation is that the query executes without authentication or model errors. If you get a 404, confirm the repository ID and model name are correct.

#### Phase 2 Component Checklist

Before proceeding to Phase 3, confirm all 18 components exist in **Build --> Component Explorer**:

| Type | Count | Components |
|------|-------|------------|
| HTTP Client Connection | 1 | `PROMO - Partner API Connection` |
| HTTP Client Operation | 9 | `PROMO - HTTP Op - GET Component` through `PROMO - HTTP Op - POST IntegrationPack` |
| DataHub Connection | 1 | `PROMO - DataHub Connection` |
| DataHub Operation | 7 | `PROMO - DH Op - Query ComponentMapping` through `PROMO - DH Op - Update PromotionLog` (incl. Delete ComponentMapping) |
| **Total** | **18** | |

---

---
Prev: [Phase 2a: HTTP Client Setup](02-http-client-setup.md) | Next: [Phase 3: Process Canvas Fundamentals](04-process-canvas-fundamentals.md) | [Back to Index](index.md)

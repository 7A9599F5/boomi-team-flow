### Step 2.3 -- Create DataHub Connection

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

Create 6 DataHub operations -- a Query and an Update for each of the 3 models. Each operation uses the `PROMO - DataHub Connection` from Step 2.3.

#### Quick Reference Table

| # | Component Name | Model | Action | Profile Source |
|---|---------------|-------|--------|---------------|
| 1 | PROMO - DH Op - Query ComponentMapping | ComponentMapping | Query Golden Records | Import from model |
| 2 | PROMO - DH Op - Update ComponentMapping | ComponentMapping | Update Golden Records | Import from model |
| 3 | PROMO - DH Op - Query DevAccountAccess | DevAccountAccess | Query Golden Records | Import from model |
| 4 | PROMO - DH Op - Update DevAccountAccess | DevAccountAccess | Update Golden Records | Import from model |
| 5 | PROMO - DH Op - Query PromotionLog | PromotionLog | Query Golden Records | Import from model |
| 6 | PROMO - DH Op - Update PromotionLog | PromotionLog | Update Golden Records | Import from model |

#### Step 2.4.1 -- PROMO - DH Op - Query ComponentMapping

1. Navigate to **Build --> New Component --> Connector --> Operation**.
2. Select connector type: **Boomi DataHub**. Name: `PROMO - DH Op - Query ComponentMapping`.
3. Connection: select `PROMO - DataHub Connection`.
4. Action: **Query Golden Records**.
5. Click **Import** on the Request/Response profile panel. Select model: `ComponentMapping`. Boomi auto-generates the XML request and response profiles based on the model fields.
6. **Save**.

#### Step 2.4.2 -- PROMO - DH Op - Update ComponentMapping

1. **Build --> New Component --> Connector --> Operation --> Boomi DataHub**.
2. Name: `PROMO - DH Op - Update ComponentMapping`.
3. Connection: `PROMO - DataHub Connection`.
4. Action: **Update Golden Records**.
5. Click **Import**, select model: `ComponentMapping`. The auto-generated profile includes the `<batch src="PROMOTION_ENGINE">` wrapper and all model fields.
6. **Save**.

#### Step 2.4.3 -- PROMO - DH Op - Query DevAccountAccess

Follows the same pattern as Step 2.4.1 with these differences:

1. Name: `PROMO - DH Op - Query DevAccountAccess`.
2. Action: **Query Golden Records**.
3. Import from model: `DevAccountAccess`.
4. **Save**.

#### Step 2.4.4 -- PROMO - DH Op - Update DevAccountAccess

Follows the same pattern as Step 2.4.2 with these differences:

1. Name: `PROMO - DH Op - Update DevAccountAccess`.
2. Action: **Update Golden Records**.
3. Import from model: `DevAccountAccess`. The auto-generated profile uses `<batch src="ADMIN_CONFIG">` as the source wrapper.
4. **Save**.

#### Step 2.4.5 -- PROMO - DH Op - Query PromotionLog

Follows the same pattern as Step 2.4.1 with these differences:

1. Name: `PROMO - DH Op - Query PromotionLog`.
2. Action: **Query Golden Records**.
3. Import from model: `PromotionLog`.
4. **Save**.

#### Step 2.4.6 -- PROMO - DH Op - Update PromotionLog

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

Before proceeding to Phase 3, confirm all 17 components exist in **Build --> Component Explorer**:

| Type | Count | Components |
|------|-------|------------|
| HTTP Client Connection | 1 | `PROMO - Partner API Connection` |
| HTTP Client Operation | 9 | `PROMO - HTTP Op - GET Component` through `PROMO - HTTP Op - POST IntegrationPack` |
| DataHub Connection | 1 | `PROMO - DataHub Connection` |
| DataHub Operation | 6 | `PROMO - DH Op - Query ComponentMapping` through `PROMO - DH Op - Update PromotionLog` |
| **Total** | **17** | |

---

---
Prev: [Phase 2a: HTTP Client Setup](02-http-client-setup.md) | Next: [Phase 3: Process Canvas Fundamentals](04-process-canvas-fundamentals.md) | [Back to Index](index.md)

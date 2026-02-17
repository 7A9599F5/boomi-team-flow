## Appendix C: Platform API Quick Reference

### Authentication

All Partner API and DataHub API calls use HTTP Basic Authentication.

| Parameter | Value |
|-----------|-------|
| Username | `BOOMI_TOKEN.{your_email}` (e.g., `BOOMI_TOKEN.user@company.com`) |
| Password | Your Platform API token |
| Header | `Authorization: Basic {base64(username:password)}` |
| Token generation | Settings, Account Information, Platform API Tokens |

### Partner API Endpoints

All endpoints use the base URL `https://api.boomi.com`.

| Endpoint Name | Method | URL Path | Content-Type | overrideAccount? | Template File |
|---------------|--------|----------|-------------|-------------------|---------------|
| GET Component | GET | `/partner/api/rest/v1/{accountId}/Component/{componentId}` | `application/xml` | Yes | `integration/api-requests/get-component.xml` |
| POST Component (Create) | POST | `/partner/api/rest/v1/{accountId}/Component` | `application/xml` | No | `integration/api-requests/create-component.xml` |
| POST Component (Update) | POST | `/partner/api/rest/v1/{accountId}/Component/{componentId}` | `application/xml` | No | `integration/api-requests/update-component.xml` |
| GET ComponentReference | GET | `/partner/api/rest/v1/{accountId}/ComponentReference/{componentId}` | `application/xml` | Yes | `integration/api-requests/query-component-reference.xml` |
| GET ComponentMetadata | GET | `/partner/api/rest/v1/{accountId}/ComponentMetadata/{componentId}` | `application/xml` | Yes | `integration/api-requests/query-component-metadata.xml` |
| QUERY PackagedComponent | POST | `/partner/api/rest/v1/{accountId}/PackagedComponent/query` | `application/xml` | Yes | `integration/api-requests/query-packaged-components.xml` |
| POST PackagedComponent | POST | `/partner/api/rest/v1/{accountId}/PackagedComponent` | `application/json` | No | `integration/api-requests/create-packaged-component.json` |
| POST DeployedPackage | POST | `/partner/api/rest/v1/{accountId}/DeployedPackage` | `application/json` | No | `integration/api-requests/create-deployed-package.json` |
| POST IntegrationPack | POST | `/partner/api/rest/v1/{accountId}/IntegrationPack` | `application/json` | No | `integration/api-requests/create-integration-pack.json` |

### Rate Limiting

| Parameter | Value |
|-----------|-------|
| Limit | ~10 requests/second |
| Strategy | 120ms gap between consecutive calls (yields ~8 req/s with safety margin) |
| Retry on 429/503 | Up to 3 retries with exponential backoff |
| Backoff schedule | 1st retry: 1 second, 2nd retry: 2 seconds, 3rd retry: 4 seconds |

### overrideAccount Parameter

The `overrideAccount` query parameter allows reading from sub-accounts using primary account credentials.

- Appended as a query parameter: `?overrideAccount={devAccountId}`
- Required for: GET Component, GET ComponentReference, GET ComponentMetadata, QUERY PackagedComponent
- Not used for: POST Component (Create/Update), POST PackagedComponent, POST DeployedPackage, POST IntegrationPack -- these always target the primary account

### Response Code Handling

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process the response body |
| 400 | Bad Request | Check request XML/JSON format; verify required fields are present |
| 401 | Unauthorized | Check API token and username format (`BOOMI_TOKEN.email:token`) |
| 403 | Forbidden | Verify Partner API is enabled; verify overrideAccount permissions |
| 404 | Not Found | Component or resource does not exist at the specified ID |
| 429 | Rate Limit Exceeded | Retry after 1 second (exponential backoff) |
| 503 | Service Unavailable | Retry after 2 seconds (exponential backoff) |

### XML Namespace

All Platform API XML uses the namespace:

```
xmlns:bns="http://api.platform.boomi.com/"
```

### Reusable API Call Templates

#### 1. GET Component (with overrideAccount)

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{componentId}?overrideAccount={devAccountId}"
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; Accept = "application/xml" }
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{componentId}?overrideAccount={devAccountId}" `
  -Method GET -Headers $headers
```

#### 2. POST Component (Create)

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{componentName}" type="{componentType}" folderFullPath="/Promoted{devFolderFullPath}">
  <bns:object><!-- component XML --></bns:object>
</bns:Component>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; "Content-Type" = "application/xml"; Accept = "application/xml" }
$body = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{componentName}" type="{componentType}" folderFullPath="/Promoted{devFolderFullPath}">
  <bns:object><!-- component XML --></bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" `
  -Method POST -Headers $headers -Body $body
```

#### 3. POST Component (Update)

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{prodComponentId}" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" componentId="{prodComponentId}" name="{componentName}" type="{componentType}" folderFullPath="/Promoted{devFolderFullPath}">
  <bns:object><!-- stripped, reference-rewritten component XML --></bns:object>
</bns:Component>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; "Content-Type" = "application/xml"; Accept = "application/xml" }
$body = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" componentId="{prodComponentId}" name="{componentName}" type="{componentType}" folderFullPath="/Promoted{devFolderFullPath}">
  <bns:object><!-- stripped, reference-rewritten component XML --></bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{prodComponentId}" `
  -Method POST -Headers $headers -Body $body
```

#### 4. POST PackagedComponent/query (with overrideAccount)

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/PackagedComponent/query?overrideAccount={devAccountId}" \
  -d '<QueryFilter xmlns="http://api.platform.boomi.com/">
  <expression operator="and">
    <nestedExpression>
      <argument>componentType</argument>
      <operator>EQUALS</operator>
      <property>process</property>
    </nestedExpression>
  </expression>
</QueryFilter>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; "Content-Type" = "application/xml"; Accept = "application/xml" }
$body = @"
<QueryFilter xmlns="http://api.platform.boomi.com/">
  <expression operator="and">
    <nestedExpression>
      <argument>componentType</argument>
      <operator>EQUALS</operator>
      <property>process</property>
    </nestedExpression>
  </expression>
</QueryFilter>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/PackagedComponent/query?overrideAccount={devAccountId}" `
  -Method POST -Headers $headers -Body $body
```

#### 5. DataHub Record Query

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -d '<RecordQueryRequest limit="200">
  <view>
    <fieldId>devComponentId</fieldId>
    <fieldId>devAccountId</fieldId>
    <fieldId>prodComponentId</fieldId>
    <fieldId>componentName</fieldId>
    <fieldId>componentType</fieldId>
    <fieldId>prodLatestVersion</fieldId>
    <fieldId>lastPromotedAt</fieldId>
  </view>
  <filter op="AND">
    <fieldValue>
      <fieldId>devComponentId</fieldId>
      <operator>EQUALS</operator>
      <value>{devComponentId}</value>
    </fieldValue>
    <fieldValue>
      <fieldId>devAccountId</fieldId>
      <operator>EQUALS</operator>
      <value>{devAccountId}</value>
    </fieldValue>
  </filter>
</RecordQueryRequest>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; "Content-Type" = "application/xml" }
$body = @"
<RecordQueryRequest limit="200">
  <view>
    <fieldId>devComponentId</fieldId>
    <fieldId>devAccountId</fieldId>
    <fieldId>prodComponentId</fieldId>
    <fieldId>componentName</fieldId>
    <fieldId>componentType</fieldId>
    <fieldId>prodLatestVersion</fieldId>
    <fieldId>lastPromotedAt</fieldId>
  </view>
  <filter op="AND">
    <fieldValue>
      <fieldId>devComponentId</fieldId>
      <operator>EQUALS</operator>
      <value>{devComponentId}</value>
    </fieldValue>
    <fieldValue>
      <fieldId>devAccountId</fieldId>
      <operator>EQUALS</operator>
      <value>{devAccountId}</value>
    </fieldValue>
  </filter>
</RecordQueryRequest>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body $body
```

#### 6. DataHub Record Update

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/create" \
  -d '<batch src="PROMOTION_ENGINE">
  <ComponentMapping>
    <devComponentId>{devComponentId}</devComponentId>
    <devAccountId>{devAccountId}</devAccountId>
    <prodComponentId>{prodComponentId}</prodComponentId>
    <componentName>{componentName}</componentName>
    <componentType>{componentType}</componentType>
    <prodAccountId>{primaryAccountId}</prodAccountId>
    <prodLatestVersion>{version}</prodLatestVersion>
    <lastPromotedAt>{timestamp}</lastPromotedAt>
    <lastPromotedBy>{userEmail}</lastPromotedBy>
  </ComponentMapping>
</batch>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; "Content-Type" = "application/xml" }
$body = @"
<batch src="PROMOTION_ENGINE">
  <ComponentMapping>
    <devComponentId>{devComponentId}</devComponentId>
    <devAccountId>{devAccountId}</devAccountId>
    <prodComponentId>{prodComponentId}</prodComponentId>
    <componentName>{componentName}</componentName>
    <componentType>{componentType}</componentType>
    <prodAccountId>{primaryAccountId}</prodAccountId>
    <prodLatestVersion>{version}</prodLatestVersion>
    <lastPromotedAt>{timestamp}</lastPromotedAt>
    <lastPromotedBy>{userEmail}</lastPromotedBy>
  </ComponentMapping>
</batch>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/create" `
  -Method POST -Headers $headers -Body $body

---
Prev: [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | [Back to Index](index.md)

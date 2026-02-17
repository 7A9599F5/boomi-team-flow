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
| GET Component | GET | `/partner/api/rest/v1/{accountId}/Component/{componentId}` | `application/xml` | Yes | `get-component.xml` |
| POST Component (Create) | POST | `/partner/api/rest/v1/{accountId}/Component` | `application/xml` | No | `create-component.xml` |
| POST Component (Update) | POST | `/partner/api/rest/v1/{accountId}/Component/{componentId}` | `application/xml` | No | `update-component.xml` |
| GET ComponentReference | GET | `/partner/api/rest/v1/{accountId}/ComponentReference/{componentId}` | `application/xml` | Yes | `query-component-reference.xml` |
| GET ComponentMetadata | GET | `/partner/api/rest/v1/{accountId}/ComponentMetadata/{componentId}` | `application/xml` | Yes | `query-component-metadata.xml` |
| QUERY PackagedComponent | POST | `/partner/api/rest/v1/{accountId}/PackagedComponent/query` | `application/xml` | Yes | `query-packaged-components.xml` |
| POST PackagedComponent | POST | `/partner/api/rest/v1/{accountId}/PackagedComponent` | `application/json` | No | `create-packaged-component.json` |
| POST DeployedPackage | POST | `/partner/api/rest/v1/{accountId}/DeployedPackage` | `application/json` | No | `create-deployed-package.json` |
| POST IntegrationPack | POST | `/partner/api/rest/v1/{accountId}/IntegrationPack` | `application/json` | No | `create-integration-pack.json` |
| POST Branch | POST | `/partner/api/rest/v1/{accountId}/Branch` | `application/json` | No | `create-branch.json` |
| QUERY Branch | POST | `/partner/api/rest/v1/{accountId}/Branch/query` | `application/json` | No | `query-branch.json` |
| GET Branch | GET | `/partner/api/rest/v1/{accountId}/Branch/{branchId}` | `application/json` | No | `get-branch.json` |
| DELETE Branch | DELETE | `/partner/api/rest/v1/{accountId}/Branch/{branchId}` | `application/json` | No | `delete-branch.json` |
| POST MergeRequest | POST | `/partner/api/rest/v1/{accountId}/MergeRequest` | `application/json` | No | `create-merge-request.json` |
| POST MergeRequest Execute | POST | `/partner/api/rest/v1/{accountId}/MergeRequest/execute/{mergeRequestId}` | `application/json` | No | `execute-merge-request.json` |
| GET MergeRequest | GET | `/partner/api/rest/v1/{accountId}/MergeRequest/{mergeRequestId}` | `application/json` | No | `get-merge-request.json` |
| QUERY IntegrationPack | POST | `/partner/api/rest/v1/{accountId}/IntegrationPack/query` | `application/xml` | No | `query-integration-packs.xml` |
| POST Add To IntegrationPack | POST | `/partner/api/rest/v1/{accountId}/IntegrationPack/{packId}/PackagedComponent/{packageId}` | `application/json` | No | `add-to-integration-pack.json` |
| POST ReleaseIntegrationPack | POST | `/partner/api/rest/v1/{accountId}/ReleaseIntegrationPack` | `application/json` | No | `release-integration-pack.json` |

> All template files are in `integration/api-requests/`.

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
- Not used for: POST Component (Create/Update), POST PackagedComponent, POST DeployedPackage, POST IntegrationPack, Branch/MergeRequest operations -- these always target the primary account

### Response Code Handling

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process the response body |
| 400 | Bad Request | Check request XML/JSON format; verify required fields are present |
| 401 | Unauthorized | Check API token and username format (`BOOMI_TOKEN.email:token`) |
| 403 | Forbidden | Verify Partner API is enabled; verify overrideAccount permissions |
| 404 | Not Found | Component or resource does not exist at the specified ID |
| 409 | Conflict | MergeRequest conflict (should not occur with OVERRIDE strategy) |
| 429 | Rate Limit Exceeded | Retry after 1 second (exponential backoff) |
| 503 | Service Unavailable | Retry after 2 seconds (exponential backoff) |

### XML Namespace

All Platform API XML uses the namespace:

```
xmlns:bns="http://api.platform.boomi.com/"
```

### QueryFilter Reference

All QUERY endpoints accept a `QueryFilter` body. The XML and JSON formats differ in field ordering.

#### Operators

| Operator | Description | Arguments | Example Use |
|----------|-------------|-----------|-------------|
| `EQUALS` | Exact match | 1 value | `componentType = "process"` |
| `NOT_EQUALS` | Not equal | 1 value | `deleted != "true"` |
| `LIKE` | Wildcard match (`%` = any chars) | 1 value | `name LIKE "%Order%"` |
| `STARTS_WITH` | Prefix match | 1 value | `name STARTS_WITH "PROMO"` |
| `IS_NULL` | Field is null | 0 values | `folderFullPath IS_NULL` |
| `IS_NOT_NULL` | Field is not null | 0 values | `prodComponentId IS_NOT_NULL` |
| `BETWEEN` | Range (inclusive) | 2 values | `createdDate BETWEEN "2024-01-01" AND "2024-12-31"` |
| `GREATER_THAN` | Greater than | 1 value | `version > 3` |
| `GREATER_THAN_OR_EQUAL` | Greater or equal | 1 value | `version >= 3` |
| `LESS_THAN` | Less than | 1 value | `version < 10` |
| `LESS_THAN_OR_EQUAL` | Less or equal | 1 value | `version <= 10` |

#### XML QueryFilter Syntax

```xml
<QueryFilter xmlns="http://api.platform.boomi.com/">
  <expression operator="and">
    <nestedExpression>
      <argument>componentType</argument>
      <operator>EQUALS</operator>
      <property>process</property>
    </nestedExpression>
    <nestedExpression>
      <argument>deleted</argument>
      <operator>EQUALS</operator>
      <property>false</property>
    </nestedExpression>
  </expression>
</QueryFilter>
```

> **XML field order**: `<argument>` (field name) comes before `<property>` (value). This is the reverse of JSON.

#### JSON QueryFilter Syntax

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {
          "operator": "EQUALS",
          "property": "componentType",
          "argument": ["process"]
        },
        {
          "operator": "EQUALS",
          "property": "deleted",
          "argument": ["false"]
        }
      ]
    }
  }
}
```

> **JSON field order**: `property` (field name) comes before `argument` (value array). This is the reverse of XML.

#### BETWEEN Operator (2 Values)

```json
{
  "operator": "BETWEEN",
  "property": "createdDate",
  "argument": ["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"]
}
```

#### IS_NULL Operator (No Value)

```json
{
  "operator": "IS_NULL",
  "property": "prodComponentId",
  "argument": []
}
```

#### Grouping Operators

Use `"and"` or `"or"` as the top-level `operator` with `nestedExpression` arrays to combine conditions.

### Pagination

All QUERY operations return a maximum of **100 results per page**.

#### How It Works

1. **Initial query** returns up to 100 results. If more exist, response includes a `queryToken`.
2. **Subsequent pages** use the `queryMore` endpoint with the token.
3. **Last page** has no `queryToken` in the response.

#### queryMore Endpoint

```
POST /partner/api/rest/v1/{accountId}/{ObjectType}/queryMore
```

Request body:
```json
{
  "queryToken": "EXAMPLE_QUERY_TOKEN"
}
```

#### Pagination Rules

| Rule | Value |
|------|-------|
| Max results per page | 100 |
| Gap between queryMore calls | 120ms minimum |
| Token expiry | Tokens expire after the session ends |
| Empty result set | `numberOfResults: 0`, no `queryToken` |

#### QueryResult Response Structure

**JSON:**
```json
{
  "@type": "QueryResult",
  "numberOfResults": 100,
  "queryToken": "EXAMPLE_QUERY_TOKEN",
  "result": [ { "@type": "...", ... } ]
}
```

**XML:**
```xml
<bns:QueryResult xmlns:bns="http://api.platform.boomi.com/"
    numberOfResults="100" queryToken="EXAMPLE_QUERY_TOKEN">
  <bns:result>
    <!-- result objects -->
  </bns:result>
</bns:QueryResult>
```

No `queryToken` attribute/field = last page reached.

### Component Type Catalog

The `type` field in Component and ComponentMetadata objects uses these values:

| Type Value | Description |
|------------|-------------|
| `process` | Integration process |
| `connection` | Connector connection |
| `connector` | Custom connector descriptor |
| `operation` | Connector operation |
| `map` | Data map |
| `profile.json` | JSON profile |
| `profile.xml` | XML profile |
| `profile.flatfile` | Flat file profile |
| `profile.edi` | EDI profile |
| `profile.database` | Database profile |
| `xslt` | XSLT stylesheet |
| `flowservice` | Flow Service |
| `certificate` | Certificate component |
| `crossreference` | Cross-reference table |
| `customlibrary` | Custom library |
| `tradingpartner` | Trading partner |

> When querying `componentType` in a QueryFilter, use the exact lowercase string (e.g., `"process"`, not `"Process"`).

### Error Response Format

**JSON:**
```json
{
  "@type": "Error",
  "statusCode": 403,
  "errorMessage": "Access denied due to insufficient permissions."
}
```

**XML:**
```xml
<Error>
  <statusCode>403</statusCode>
  <errorMessage>Access denied due to insufficient permissions.</errorMessage>
</Error>
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
```

#### 7. QUERY IntegrationPack

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/IntegrationPack/query" \
  -d '<QueryFilter xmlns="http://api.platform.boomi.com/">
  <expression operator="and">
    <nestedExpression>
      <argument>installationType</argument>
      <operator>EQUALS</operator>
      <property>MULTI</property>
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
      <argument>installationType</argument>
      <operator>EQUALS</operator>
      <property>MULTI</property>
    </nestedExpression>
  </expression>
</QueryFilter>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/IntegrationPack/query" `
  -Method POST -Headers $headers -Body $body
```

#### 8. POST Add To IntegrationPack

```bash
# Linux/macOS — no request body, linking via URL
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/IntegrationPack/{integrationPackId}/PackagedComponent/{packageId}"
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; Accept = "application/json"; "Content-Type" = "application/json" }
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/IntegrationPack/{integrationPackId}/PackagedComponent/{packageId}" `
  -Method POST -Headers $headers
```

#### 9. POST ReleaseIntegrationPack

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/ReleaseIntegrationPack" \
  -d '{
  "integrationPackId": "{integrationPackId}",
  "version": "{releaseVersion}",
  "notes": "Release notes for this version"
}'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; "Content-Type" = "application/json"; Accept = "application/json" }
$body = @"
{
  "integrationPackId": "{integrationPackId}",
  "version": "{releaseVersion}",
  "notes": "Release notes for this version"
}
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/ReleaseIntegrationPack" `
  -Method POST -Headers $headers -Body $body
```

#### 10. GET MergeRequest (Poll Status)

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/json" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/MergeRequest/{mergeRequestId}"
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; Accept = "application/json" }
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/MergeRequest/{mergeRequestId}" `
  -Method GET -Headers $headers
```

> Poll every 2 seconds until `stage` equals `MERGED` (success) or `FAILED_TO_MERGE` (failure). Merge stages: `DRAFTING` -> `DRAFTED` -> `REVIEWING` -> `MERGING` -> `MERGED`.

---
Prev: [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | [Back to Index](index.md)

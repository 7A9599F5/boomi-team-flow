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

#### Component Operations

| # | Endpoint Name | Method | URL Path | Content-Type | overrideAccount? | Used By | Template File |
|---|---------------|--------|----------|-------------|-------------------|---------|---------------|
| 1 | GET Component | GET | `/partner/api/rest/v1/{accountId}/Component/{componentId}` | `application/xml` | Yes | B, C, G | `get-component.xml` |
| 2 | POST Component (Create) | POST | `/partner/api/rest/v1/{accountId}/Component` | `application/xml` | No | C | `create-component.xml` |
| 3 | POST Component (Update) | POST | `/partner/api/rest/v1/{accountId}/Component/{componentId}` | `application/xml` | No | C | `update-component.xml` |
| 4 | GET ComponentReference | GET | `/partner/api/rest/v1/{accountId}/ComponentReference/{componentId}` | `application/xml` | Yes | B | `query-component-reference.xml` |
| 5 | GET ComponentMetadata | GET | `/partner/api/rest/v1/{accountId}/ComponentMetadata/{componentId}` | `application/xml` | Yes | A, B | `query-component-metadata.xml` |

**Notes:**
- **GET Component** with tilde syntax (`/Component/{id}~{branchId}`) reads from a specific branch (Process G)
- **POST Component Create** with tilde syntax (`/Component~{branchId}`) creates on a specific branch (Process C)
- **POST Component Update** with tilde syntax (`/Component/{id}~{branchId}`) updates on a specific branch (Process C)
- All create/update operations use `folderFullPath="/Promoted{devFolderFullPath}"` to mirror dev folder structure

#### Branch Operations

| # | Endpoint Name | Method | URL Path | Content-Type | Used By | Template File |
|---|---------------|--------|----------|-------------|---------|---------------|
| 6 | POST Branch (Create) | POST | `/partner/api/rest/v1/{accountId}/Branch` | `application/json` | C | `create-branch.json` |
| 7 | QUERY Branch | POST | `/partner/api/rest/v1/{accountId}/Branch/query` | `application/json` | C | `query-branch.json` |
| 8 | GET Branch | GET | `/partner/api/rest/v1/{accountId}/Branch/{branchId}` | `application/json` | C | `get-branch.json` |
| 9 | DELETE Branch | DELETE | `/partner/api/rest/v1/{accountId}/Branch/{branchId}` | `application/json` | C, D | `delete-branch.json` |

**Notes:**
- **POST Branch** accepts `name` (required) and `description` (optional). Optionally accepts `packageId` to branch from a specific PackagedComponent version (unused in this project — we always branch from HEAD). Returns `branchId`, `ready`, and `stage` fields. Poll with **GET Branch** until `ready = true` (5s intervals, max 6 retries)
- **GET Branch** response includes `stage` field: `CREATING` (initial) → `NORMAL` (ready). Use `ready=true` as the polling gate.
- **QUERY Branch** with empty filter returns all branches -- used for branch limit check (threshold: 15)
- **DELETE Branch** is idempotent: both `200` (deleted) and `404` (already deleted) are treated as success
- Branch limit: 15 soft threshold (checked before creation), 20 hard platform limit

#### Merge Operations

| # | Endpoint Name | Method | URL Path | Content-Type | Used By | Template File |
|---|---------------|--------|----------|-------------|---------|---------------|
| 10 | POST MergeRequest (Create) | POST | `/partner/api/rest/v1/{accountId}/MergeRequest` | `application/json` | D | `create-merge-request.json` |
| 11 | POST MergeRequest (Execute) | POST | `/partner/api/rest/v1/{accountId}/MergeRequest/execute/{mergeRequestId}` | `application/json` | D | `execute-merge-request.json` |
| 12 | GET MergeRequest (Poll Status) | GET | `/partner/api/rest/v1/{accountId}/MergeRequest/{mergeRequestId}` | `application/json` | D | `get-merge-request.json` |

**Notes:**
- **POST MergeRequest** uses `strategy = "OVERRIDE"` and `priorityBranch = "{branchId}"` to ensure promotion branch content wins
- **POST MergeRequest Execute** triggers the merge with `action = "MERGE"`
- **GET MergeRequest** is used for status polling: check every 5 seconds, max 12 retries (60 seconds)
- Merge stages: `DRAFTING` -> `DRAFTED` -> `REVIEWING` -> `MERGING` -> `MERGED` (success) or `FAILED_TO_MERGE` (failure)

#### Packaging Operations

| # | Endpoint Name | Method | URL Path | Content-Type | Used By | Template File |
|---|---------------|--------|----------|-------------|---------|---------------|
| 13 | QUERY PackagedComponent | POST | `/partner/api/rest/v1/{accountId}/PackagedComponent/query` | `application/xml` | A | `query-packaged-components.xml` |
| 14 | POST PackagedComponent (Create) | POST | `/partner/api/rest/v1/{accountId}/PackagedComponent` | `application/json` | D | `create-packaged-component.json` |
| 15 | QUERY DeployedPackage | POST | `/partner/api/rest/v1/{accountId}/DeployedPackage/query` | `application/json` | (future) | — |

**Notes:**
- **QUERY PackagedComponent** uses `overrideAccount` to read from dev sub-accounts (Process A)
- **POST PackagedComponent** creates a versioned package from a component on main; requires `componentId`, `packageVersion`, and `shareable = true`
- **QUERY DeployedPackage** can verify deployment status; not currently used in active processes but available for future troubleshooting

#### Integration Pack Operations

| # | Endpoint Name | Method | URL Path | Content-Type | Used By | Template File |
|---|---------------|--------|----------|-------------|---------|---------------|
| 16 | POST IntegrationPack (Create) | POST | `/partner/api/rest/v1/{accountId}/IntegrationPack` | `application/json` | D | `create-integration-pack.json` |
| 17 | QUERY IntegrationPack | POST | `/partner/api/rest/v1/{accountId}/IntegrationPack/query` | `application/xml` | J | `query-integration-packs.xml` |
| 18 | POST Add To IntegrationPack | POST | `/partner/api/rest/v1/{accountId}/IntegrationPack/{packId}/PackagedComponent/{packageId}` | `application/json` | D | `add-to-integration-pack.json` |
| 19 | POST ReleaseIntegrationPack | POST | `/partner/api/rest/v1/{accountId}/ReleaseIntegrationPack` | `application/json` | D | `release-integration-pack.json` |

**Notes:**
- **POST IntegrationPack** creates a new MULTI-type Integration Pack with `name` and `description`
- **QUERY IntegrationPack** filters by `installationType = "MULTI"` to get manageable packs
- **POST Add To IntegrationPack** links a PackagedComponent to an Integration Pack via URL path (no request body)
- **POST ReleaseIntegrationPack** creates a versioned release with `integrationPackId`, `version`, and `notes`

#### Deployment Operations

| # | Endpoint Name | Method | URL Path | Content-Type | Used By | Template File |
|---|---------------|--------|----------|-------------|---------|---------------|
| 20 | POST DeployedPackage (Create) | POST | `/partner/api/rest/v1/{accountId}/DeployedPackage` | `application/json` | D | `create-deployed-package.json` |
| 21 | GET Environment | GET | `/partner/api/rest/v1/{accountId}/Environment/{environmentId}` | `application/json` | (config) | — |

**Notes:**
- **POST DeployedPackage** deploys a released Integration Pack to a target environment
- **GET Environment** can be used to validate environment IDs during configuration; not called at runtime
- Deploy with 120ms gap between consecutive deployment calls to stay within rate limits

> All template files are in `integration/api-requests/`.

### Template File Inventory

Cross-reference of template files to endpoints:

| Template File | Endpoint | Format |
|---------------|----------|--------|
| `get-component.xml` | GET Component | XML |
| `create-component.xml` | POST Component (Create) | XML |
| `update-component.xml` | POST Component (Update) | XML |
| `query-component-reference.xml` | GET ComponentReference | XML |
| `query-component-metadata.xml` | GET ComponentMetadata | XML |
| `create-branch.json` | POST Branch | JSON |
| `query-branch.json` | QUERY Branch | JSON |
| `get-branch.json` | GET Branch | JSON |
| `delete-branch.json` | DELETE Branch | JSON |
| `create-merge-request.json` | POST MergeRequest | JSON |
| `execute-merge-request.json` | POST MergeRequest Execute | JSON |
| `get-merge-request.json` | GET MergeRequest | JSON |
| `query-packaged-components.xml` | QUERY PackagedComponent | XML |
| `create-packaged-component.json` | POST PackagedComponent | JSON |
| `create-integration-pack.json` | POST IntegrationPack | JSON |
| `query-integration-packs.xml` | QUERY IntegrationPack | XML |
| `add-to-integration-pack.json` | POST Add To IntegrationPack | JSON |
| `release-integration-pack.json` | POST ReleaseIntegrationPack | JSON |
| `create-deployed-package.json` | POST DeployedPackage | JSON |

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
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{componentId}?overrideAccount={devAccountId}"
```

#### 2. GET Component (from branch -- tilde syntax)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{componentId}~{branchId}"
```

#### 3. POST Component (Create on branch)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component~{branchId}" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{componentName}" type="{componentType}" folderFullPath="/Promoted{devFolderFullPath}">
  <bns:object><!-- component XML --></bns:object>
</bns:Component>'
```

#### 4. POST Component (Update on branch)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{prodComponentId}~{branchId}" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" componentId="{prodComponentId}" name="{componentName}" type="{componentType}" folderFullPath="/Promoted{devFolderFullPath}">
  <bns:object><!-- stripped, reference-rewritten component XML --></bns:object>
</bns:Component>'
```

#### 5. POST Branch (Create)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Branch" \
  -d '{"name": "promo-{promotionId}", "description": "Promotion branch for {promotionId}"}'
```

#### 6. GET Branch (Poll readiness)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/json" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/Branch/{branchId}"
```

> Poll every 5 seconds until `ready = true` (max 6 retries, 30 seconds).

#### 7. DELETE Branch

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X DELETE "https://api.boomi.com/partner/api/rest/v1/{accountId}/Branch/{branchId}"
```

> Idempotent: both `200` and `404` are success.

#### 8. POST MergeRequest (Create)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/MergeRequest" \
  -d '{"source": "{branchId}", "strategy": "OVERRIDE", "priorityBranch": "{branchId}"}'
```

#### 9. POST MergeRequest Execute

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/MergeRequest/execute/{mergeRequestId}" \
  -d '{"action": "MERGE"}'
```

#### 10. GET MergeRequest (Poll Status)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/json" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/MergeRequest/{mergeRequestId}"
```

> Poll every 5 seconds until `stage` equals `MERGED` (success) or `FAILED_TO_MERGE` (failure). Max 12 retries (60 seconds). Merge stages: `DRAFTING` -> `DRAFTED` -> `REVIEWING` -> `MERGING` -> `MERGED`.

#### 11. QUERY PackagedComponent (with overrideAccount)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
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

#### 12. POST PackagedComponent (Create)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/PackagedComponent" \
  -d '{
  "componentId": "{prodComponentId}",
  "packageVersion": "{version}",
  "notes": "Promotion package",
  "shareable": true
}'
```

#### 13. POST IntegrationPack (Create)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/IntegrationPack" \
  -d '{"name": "{packName}", "description": "{packDescription}"}'
```

#### 14. QUERY IntegrationPack

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
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

#### 15. POST Add To IntegrationPack

```bash
# No request body -- linking via URL path
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/json" -H "Content-Type: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/IntegrationPack/{integrationPackId}/PackagedComponent/{packageId}"
```

#### 16. POST ReleaseIntegrationPack

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/ReleaseIntegrationPack" \
  -d '{
  "integrationPackId": "{integrationPackId}",
  "version": "{releaseVersion}",
  "notes": "Release notes for this version"
}'
```

#### 17. POST DeployedPackage (Create)

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DeployedPackage" \
  -d '{
  "packageId": "{releasedPackageId}",
  "environmentId": "{environmentId}"
}'
```

#### 18. DataHub Record Query

```bash
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

#### 19. DataHub Record Update

```bash
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

### Process-to-Endpoint Matrix

Quick lookup: which processes call which endpoints.

| Endpoint | A0 | A | B | C | D | E | E2 | E3 | E4 | F | G | J |
|----------|----|---|---|---|---|---|----|----|----|---|---|---|
| GET Component | | | | X | | | | | | | X | |
| POST Component Create | | | | X | | | | | | | | |
| POST Component Update | | | | X | | | | | | | | |
| GET ComponentReference | | | X | | | | | | | | | |
| GET ComponentMetadata | | X | X | | | | | | | | | |
| POST Branch | | | | X | | | | | | | | |
| QUERY Branch | | | | X | | | | | | | | |
| GET Branch | | | | X | | | | | | | | |
| DELETE Branch | | | | X | X | | | | | | | |
| POST MergeRequest | | | | | X | | | | | | | |
| POST MergeRequest Execute | | | | | X | | | | | | | |
| GET MergeRequest | | | | | X | | | | | | | |
| QUERY PackagedComponent | | X | | | | | | | | | | |
| POST PackagedComponent | | | | | X | | | | | | | |
| POST IntegrationPack | | | | | X | | | | | | | |
| QUERY IntegrationPack | | | | | | | | | | | | X |
| POST Add To IntegrationPack | | | | | X | | | | | | | |
| POST ReleaseIntegrationPack | | | | | X | | | | | | | |
| POST DeployedPackage | | | | | X | | | | | | | |
| DH Query ComponentMapping | | | | X | | | | | | X | | |
| DH Update ComponentMapping | | | | X | | | | | | X | | |
| DH Query DevAccountAccess | X | | | | | | | | | | | |
| DH Query PromotionLog | | | | X | X | X | X | X | X | | | X |
| DH Update PromotionLog | | | | X | X | | | X | | | | |

---
Prev: [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | Next: [Appendix D: API Automation Guide](22-api-automation-guide.md) | [Back to Index](index.md)

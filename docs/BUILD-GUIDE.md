# Boomi Component Promotion System — Build Guide

This guide walks through building every component of the Promotion System step by step. Follow the phases in order — each phase builds on the previous.

## How to Use This Guide

- **Linear build**: Follow Phases 1-6 sequentially for a first-time build
- **Reference lookup**: Jump to a specific phase/step using the table of contents
- **Validation**: Every major step ends with a "**Verify:**" checkpoint — do not skip these
- **API examples**: All verification commands are shown in both `curl` (Linux/macOS) and PowerShell (Windows) formats
- **File references**: Templates, profiles, and scripts are in this repository — the guide shows HOW to use them, not duplicates of their content

---

## Prerequisites

- Primary Boomi account with Partner API enabled
- One or more dev sub-accounts (children of the primary account)
- Azure AD/Entra SSO configured in Boomi Flow
- Access to DataHub in your Boomi account
- A public Boomi cloud atom (or ability to provision one)
- API token generated at **Settings → Account Information → Platform API Tokens**

---

## Bill of Materials

The system comprises **51 components** across 6 phases:

| Phase | Category | Count | Components |
|-------|----------|-------|------------|
| 1 | DataHub Models | 3 | ComponentMapping, DevAccountAccess, PromotionLog |
| 2 | Connections | 2 | HTTP Client (Partner API), DataHub |
| 2 | HTTP Client Operations | 9 | GET/POST/QUERY for Component, Reference, Metadata, Package, Deploy, IntegrationPack |
| 2 | DataHub Operations | 6 | Query + Update for each of 3 models |
| 3 | JSON Profiles | 14 | Request + Response for each of 7 processes |
| 3 | Integration Processes | 7 | A0, A, B, C, D, E, F |
| 4 | FSS Operations | 7 | One per process |
| 4 | Flow Service | 1 | PROMO - Flow Service |
| 5 | Flow Connector | 1 | Promotion Service Connector |
| 5 | Flow Application | 1 | Promotion Dashboard |
| | **Total** | **51** | |

---

## Component Naming Convention

All Integration components use the `PROMO - ` prefix followed by a type-specific pattern:

| Type | Pattern | Example |
|------|---------|---------|
| Connection | `PROMO - {Description} Connection` | `PROMO - Partner API Connection` |
| HTTP Operation | `PROMO - HTTP Op - {Method} {Resource}` | `PROMO - HTTP Op - GET Component` |
| DataHub Operation | `PROMO - DH Op - {Action} {Model}` | `PROMO - DH Op - Query ComponentMapping` |
| JSON Profile | `PROMO - Profile - {Action}{Request\|Response}` | `PROMO - Profile - ExecutePromotionRequest` |
| Process | `PROMO - {Description}` | `PROMO - Execute Promotion` |
| FSS Operation | `PROMO - FSS Op - {ActionName}` | `PROMO - FSS Op - ExecutePromotion` |
| Flow Service | `PROMO - Flow Service` | |

DataHub models and Flow components use plain names without the prefix.

---

## Dependency Build Order

Build phases in order — each depends on the previous:

```
Phase 1: DataHub Models
    └── Phase 2: Connections & Operations (need DataHub for DH operations)
            └── Phase 3: Integration Processes (need connections, operations, profiles)
                    └── Phase 4: Flow Service (links processes to message actions)
                            └── Phase 5: Flow Dashboard (calls Flow Service via connector)
                                    └── Phase 6: Testing (validates entire stack)
```

Within Phase 3, build processes in this order (simplest → most complex):

```
F (Mapping CRUD) → A0 (Get Dev Accounts) → E (Query Status) → A (List Packages) → B (Resolve Dependencies) → C (Execute Promotion) → D (Package & Deploy)
```

---

## Repository File Reference

| Directory | Contents | Used In |
|-----------|----------|---------|
| `/datahub/models/` | DataHub model specifications (3 JSON files) | Phase 1 |
| `/datahub/api-requests/` | Test XML for DataHub CRUD validation (2 files) | Phase 1, 6 |
| `/integration/profiles/` | JSON request/response profiles (14 files) | Phase 3 |
| `/integration/scripts/` | Groovy scripts for XML manipulation (4 files) | Phase 3 |
| `/integration/api-requests/` | API request templates (9 files) | Phase 2, 3 |
| `/integration/flow-service/` | Flow Service component specification | Phase 4 |
| `/flow/` | Flow app structure and page layouts (7 files) | Phase 5 |
| `/docs/` | This guide and architecture reference | All |

---

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
| `initiatedBy` | String | Yes | No | SSO user email |
| `initiatedAt` | Date | Yes | No | Format: `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'` |
| `status` | String | Yes | No | `IN_PROGRESS`, `COMPLETED`, or `FAILED` |
| `componentsTotal` | Number | Yes | No | Total components in dependency tree |
| `componentsCreated` | Number | Yes | No | New components created |
| `componentsUpdated` | Number | Yes | No | Existing components updated |
| `componentsFailed` | Number | Yes | No | Failed component count |
| `errorMessage` | Long Text | No | No | Up to 5000 chars; present when status=FAILED |
| `resultDetail` | Long Text | No | No | Up to 5000 chars; JSON per-component results |

4. Match rule: **Exact** on `promotionId` (single field).
5. Source: `PROMOTION_ENGINE` (Contribute Only).
6. Skip Data Quality. **Save --> Publish --> Deploy**.

**Verify:** Model shows 13 fields, 1 match rule, source `PROMOTION_ENGINE`.

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

## Phase 2: Integration Connections & Operations

This phase creates the connection and operation components that all integration processes depend on. There are 2 connections and 15 operations total (9 HTTP Client + 6 DataHub).

### Step 2.1 -- Create HTTP Client Connection (Partner API)

1. Navigate to **Build --> New Component --> Connector --> Connection**.
2. Select connector type: **HTTP Client**.
3. Set component name: `PROMO - Partner API Connection`.
4. Configure the connection:

| Setting | Value |
|---------|-------|
| **URL** | `https://api.boomi.com` |
| **Authentication Type** | Basic |
| **Username** | `BOOMI_TOKEN.{your_email}` (e.g., `BOOMI_TOKEN.admin@company.com`) |
| **Password** | Your Platform API token |
| **Connection Timeout (ms)** | `120000` (120 seconds) |
| **Read Timeout (ms)** | `120000` (120 seconds) |
| **SSL Options** | Use default (TLS 1.2+) |

5. To generate a Platform API token: navigate to **Settings --> Account Information --> Platform API Tokens --> Generate New Token**. Copy the token immediately -- it is only shown once.
6. Click **Test Connection**. A successful test returns a green checkmark and "Connection successful" message.
7. **Save** the connection.

**Verify:** The connection test must succeed before proceeding. If it fails, confirm:
- The username follows the format `BOOMI_TOKEN.{email}` (not just the email).
- The API token was generated for the correct account.
- Partner API is enabled on your primary account (**Settings --> Account Information --> check "Partner API enabled"**).

### Step 2.2 -- Create HTTP Client Operations

Create 9 HTTP Client operations. Each uses the `PROMO - Partner API Connection` from Step 2.1.

#### Quick Reference Table

| # | Component Name | Method | Request URL | Content-Type | Template File |
|---|---------------|--------|-------------|-------------|---------------|
| 1 | PROMO - HTTP Op - GET Component | GET | `/partner/api/rest/v1/{1}/Component/{2}` | `application/xml` | `get-component.xml` |
| 2 | PROMO - HTTP Op - POST Component Create | POST | `/partner/api/rest/v1/{1}/Component` | `application/xml` | `create-component.xml` |
| 3 | PROMO - HTTP Op - POST Component Update | POST | `/partner/api/rest/v1/{1}/Component/{2}` | `application/xml` | `update-component.xml` |
| 4 | PROMO - HTTP Op - GET ComponentReference | GET | `/partner/api/rest/v1/{1}/ComponentReference/{2}` | `application/xml` | `query-component-reference.xml` |
| 5 | PROMO - HTTP Op - GET ComponentMetadata | GET | `/partner/api/rest/v1/{1}/ComponentMetadata/{2}` | `application/xml` | `query-component-metadata.xml` |
| 6 | PROMO - HTTP Op - QUERY PackagedComponent | POST | `/partner/api/rest/v1/{1}/PackagedComponent/query` | `application/xml` | `query-packaged-components.xml` |
| 7 | PROMO - HTTP Op - POST PackagedComponent | POST | `/partner/api/rest/v1/{1}/PackagedComponent` | `application/json` | `create-packaged-component.json` |
| 8 | PROMO - HTTP Op - POST DeployedPackage | POST | `/partner/api/rest/v1/{1}/DeployedPackage` | `application/json` | `create-deployed-package.json` |
| 9 | PROMO - HTTP Op - POST IntegrationPack | POST | `/partner/api/rest/v1/{1}/IntegrationPack` | `application/json` | `create-integration-pack.json` |

> Operations 1-6 use `application/xml` for both Content-Type and Accept headers (Platform API XML endpoints). Operations 7-9 use `application/json` for both headers (JSON-based endpoints).

#### Step 2.2.1 -- PROMO - HTTP Op - GET Component

This operation retrieves the full component XML (including configuration) from a dev sub-account.

1. Navigate to **Build --> New Component --> Connector --> Operation**.
2. Select connector type: **HTTP Client**. Name: `PROMO - HTTP Op - GET Component`.
3. Connection: select `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | GET |
| **Request URL** | `/partner/api/rest/v1/{1}/Component/{2}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `currentComponentId` |
| **Query Parameters** | `overrideAccount` = DPP `devAccountId` |
| **Request Headers** | `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400` (Bad Request), `404` (Not Found), `429` (Rate Limit), `503` (Service Unavailable) |
| **Timeout (ms)** | `120000` |

5. Reference: see `/integration/api-requests/get-component.xml` for the expected response structure.
6. **Save**.

> The `overrideAccount` query parameter allows reading from dev sub-accounts using the primary account's API credentials. This is required for operations 1, 4, 5, and 6 -- any operation that reads data from a dev account.

#### Step 2.2.2 -- PROMO - HTTP Op - POST Component Create

Creates a new component in the primary (production) account. Used when no existing prod mapping exists.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST Component Create`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/Component` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | (none -- creates in the primary account directly) |
| **Request Headers** | `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. The request body is the stripped and reference-rewritten component XML. See `/integration/api-requests/create-component.xml` for the template structure. Note: `componentId` must be omitted or empty for creation (the API assigns a new ID). The `folderFullPath` follows the convention `/Promoted{devFolderFullPath}` — mirroring the dev account's folder hierarchy under `/Promoted/`.
6. **Save**.

#### Step 2.2.3 -- PROMO - HTTP Op - POST Component Update

Updates an existing component in the primary account. Used when a DataHub mapping already exists.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST Component Update`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/Component/{2}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `prodComponentId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. The `{2}` parameter is the production component ID from the DataHub ComponentMapping record. The API auto-increments the version number. See `/integration/api-requests/update-component.xml` for the template structure.
6. **Save**.

#### Step 2.2.4 -- PROMO - HTTP Op - GET ComponentReference

Retrieves one level of component dependencies (references) from a dev account. The promotion engine calls this recursively via BFS to build the full dependency tree.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - GET ComponentReference`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | GET |
| **Request URL** | `/partner/api/rest/v1/{1}/ComponentReference/{2}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `currentComponentId` |
| **Query Parameters** | `overrideAccount` = DPP `devAccountId` |
| **Request Headers** | `Accept: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Response includes `DEPENDENT` and `INDEPENDENT` reference types. See `/integration/api-requests/query-component-reference.xml` for the response structure.
6. **Save**.

#### Step 2.2.5 -- PROMO - HTTP Op - GET ComponentMetadata

Retrieves lightweight metadata (name, type, version) without the full configuration XML. Faster than GET Component.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - GET ComponentMetadata`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | GET |
| **Request URL** | `/partner/api/rest/v1/{1}/ComponentMetadata/{2}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `currentComponentId` |
| **Query Parameters** | `overrideAccount` = DPP `devAccountId` |
| **Request Headers** | `Accept: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. See `/integration/api-requests/query-component-metadata.xml` for the response structure. Returns `componentId`, `name`, `type`, `version`, `currentVersion`, `modifiedDate`, `modifiedBy`, and `folderFullPath`.
6. **Save**.

#### Step 2.2.6 -- PROMO - HTTP Op - QUERY PackagedComponent

Queries packaged components from a dev sub-account. Returns paginated results (100 per page).

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - QUERY PackagedComponent`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/PackagedComponent/query` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | `overrideAccount` = DPP `devAccountId` |
| **Request Headers** | `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. The request body is a `QueryFilter` element. See `/integration/api-requests/query-packaged-components.xml` for the filter structure. Handle pagination using the `queryToken` from the response via `/PackagedComponent/queryMore` with a 120ms gap between pages to respect rate limits.
6. **Save**.

#### Step 2.2.7 -- PROMO - HTTP Op - POST PackagedComponent

Creates a new PackagedComponent in the primary account. This is a JSON endpoint.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST PackagedComponent`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/PackagedComponent` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json`, `Content-Type: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. The request body includes `shareable: true` (required for Integration Pack inclusion). See `/integration/api-requests/create-packaged-component.json` for the template.
6. **Save**.

> From this operation onward (operations 7-9), both Content-Type and Accept headers must be `application/json`, not `application/xml`.

#### Step 2.2.8 -- PROMO - HTTP Op - POST DeployedPackage

Deploys a released Integration Pack to a target environment. Called once per target environment.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST DeployedPackage`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/DeployedPackage` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json`, `Content-Type: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Request body requires `environmentId` and `packageId` from the released Integration Pack. See `/integration/api-requests/create-deployed-package.json` for the template.
6. **Save**.

#### Step 2.2.9 -- PROMO - HTTP Op - POST IntegrationPack

Creates a new Integration Pack when `createNewPack=true` in the deployment request.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST IntegrationPack`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/IntegrationPack` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json`, `Content-Type: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. After creation, add the PackagedComponent to the pack, then release via `POST /ReleaseIntegrationPack`. Set `installationType: "MULTI"` for multi-install packs. See `/integration/api-requests/create-integration-pack.json` for the template.
6. **Save**.

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

## Phase 3: Integration Processes

This phase builds the seven integration processes that power the Promotion System. Each process listens on a Flow Services Server (FSS) operation and performs a specific task — from simple DataHub CRUD to the full promotion engine. Build them in the order listed: simplest first, so each process reinforces patterns used in the next.

### 3.A — Process Canvas Fundamentals

Before building individual processes, understand the shape types and patterns used throughout this system.

#### Shape Types Used

| Shape | Icon | Purpose in This System |
|-------|------|----------------------|
| Start | Green circle | FSS Listen — receives request JSON from Flow Service |
| Set Properties | Gear | Reads JSON fields into Dynamic Process Properties (DPPs) |
| Data Process | Script icon | Runs Groovy scripts for XML/JSON manipulation |
| Decision | Diamond | Branches logic based on DPP values or document content |
| Map | Double arrows | Transforms data between profiles (XML to JSON, JSON to JSON) |
| For Each (Loop) | Circular arrows | Iterates over arrays or repeated documents |
| Try/Catch | Shield | Wraps risky steps; catch block handles per-component failures |
| Return Documents | Red circle | Sends response JSON back to the calling Flow Service |
| HTTP Client Send | Cloud arrow | Calls Boomi Platform API via HTTP Client connection + operation |

#### Importing JSON Profiles

Every process needs request and response JSON profiles. Import them once; all processes reference them.

1. Navigate to **Build --> New Component --> Profile --> JSON**
2. Name the profile using the exact name from the master component list (e.g., `PROMO - Profile - ManageMappingsRequest`)
3. Click **Import** and select the corresponding file from `/integration/profiles/` (e.g., `manageMappings-request.json`)
4. Boomi parses the JSON and creates the profile element tree automatically
5. Click **Save**
6. Repeat for each of the 14 profiles listed in the master component table:

| Profile Name | Source File |
|-------------|-------------|
| `PROMO - Profile - GetDevAccountsRequest` | `getDevAccounts-request.json` |
| `PROMO - Profile - GetDevAccountsResponse` | `getDevAccounts-response.json` |
| `PROMO - Profile - ListDevPackagesRequest` | `listDevPackages-request.json` |
| `PROMO - Profile - ListDevPackagesResponse` | `listDevPackages-response.json` |
| `PROMO - Profile - ResolveDependenciesRequest` | `resolveDependencies-request.json` |
| `PROMO - Profile - ResolveDependenciesResponse` | `resolveDependencies-response.json` |
| `PROMO - Profile - ExecutePromotionRequest` | `executePromotion-request.json` |
| `PROMO - Profile - ExecutePromotionResponse` | `executePromotion-response.json` |
| `PROMO - Profile - PackageAndDeployRequest` | `packageAndDeploy-request.json` |
| `PROMO - Profile - PackageAndDeployResponse` | `packageAndDeploy-response.json` |
| `PROMO - Profile - QueryStatusRequest` | `queryStatus-request.json` |
| `PROMO - Profile - QueryStatusResponse` | `queryStatus-response.json` |
| `PROMO - Profile - ManageMappingsRequest` | `manageMappings-request.json` |
| `PROMO - Profile - ManageMappingsResponse` | `manageMappings-response.json` |

#### Adding Groovy Scripts to Data Process Shapes

1. Drag a **Data Process** shape onto the canvas
2. Double-click to open configuration
3. Select the **Script** tab
4. Set Language to **Groovy 2.4**
5. Paste the contents of the script file from `/integration/scripts/` (do not modify the script)
6. Click **OK**, then **Save**

Groovy scripts in this system read and write DPPs using these two calls:

```groovy
// Read a DPP
String value = ExecutionUtil.getDynamicProcessProperty("propertyName")

// Write a DPP (third parameter = false means not persistent across executions)
ExecutionUtil.setDynamicProcessProperty("propertyName", "value", false)
```

#### DPP Usage Pattern

Every process follows the same data-flow pattern:

1. **Set Properties shape** (after Start) reads fields from the incoming request JSON document into DPPs — one property per field
2. **Groovy scripts** and **HTTP Client operations** read DPPs for input values and write DPPs with computed results
3. **Map shape** (before Return Documents) reads DPPs and accumulated documents to build the response JSON

This pattern keeps all intermediate state in DPPs rather than passing modified documents between shapes. The document stream carries the primary payload (e.g., component XML), while DPPs carry metadata (IDs, flags, counters).

---

### 3.B — General Pattern for All Processes

Every integration process in this system follows the same structural skeleton.

#### Start Shape Configuration

1. Drag the **Start** shape (already present on every new process canvas)
2. Double-click to configure
3. Connector: **Boomi Flow Services Server**
4. Action: **Listen**
5. Operation: select the FSS Operation component for this process (created below)

The Start shape receives the request JSON document from the Flow Service and places it on the document stream.

#### FSS Operation Creation Pattern

Each process requires a corresponding FSS Operation component that links it to a message action in the Flow Service. Create all seven before building the process canvases, or create each one just before its process.

1. **Build --> New Component --> Operation --> Flow Services Server**
2. Name: use the exact FSS Operation name from the master component list (see table below)
3. Service Type: **Message Action**
4. Import Request Profile: click **Import** and select the corresponding `PROMO - Profile - {Name}Request` profile
5. Import Response Profile: click **Import** and select the corresponding `PROMO - Profile - {Name}Response` profile
6. **Save**

| FSS Operation Name | Request Profile | Response Profile | Message Action |
|-------------------|-----------------|------------------|----------------|
| `PROMO - FSS Op - GetDevAccounts` | `PROMO - Profile - GetDevAccountsRequest` | `PROMO - Profile - GetDevAccountsResponse` | `getDevAccounts` |
| `PROMO - FSS Op - ListDevPackages` | `PROMO - Profile - ListDevPackagesRequest` | `PROMO - Profile - ListDevPackagesResponse` | `listDevPackages` |
| `PROMO - FSS Op - ResolveDependencies` | `PROMO - Profile - ResolveDependenciesRequest` | `PROMO - Profile - ResolveDependenciesResponse` | `resolveDependencies` |
| `PROMO - FSS Op - ExecutePromotion` | `PROMO - Profile - ExecutePromotionRequest` | `PROMO - Profile - ExecutePromotionResponse` | `executePromotion` |
| `PROMO - FSS Op - PackageAndDeploy` | `PROMO - Profile - PackageAndDeployRequest` | `PROMO - Profile - PackageAndDeployResponse` | `packageAndDeploy` |
| `PROMO - FSS Op - QueryStatus` | `PROMO - Profile - QueryStatusRequest` | `PROMO - Profile - QueryStatusResponse` | `queryStatus` |
| `PROMO - FSS Op - ManageMappings` | `PROMO - Profile - ManageMappingsRequest` | `PROMO - Profile - ManageMappingsResponse` | `manageMappings` |

#### Return Documents Shape

Every process ends with a **Return Documents** shape. This sends the final response JSON document back through the FSS listener to the Flow application. No special configuration is needed — drag it onto the canvas and connect the last shape to it.

#### Error Response Pattern

When a process encounters an error, build the error response JSON with `success = false`, an `errorCode`, and an `errorMessage`. Use a Map shape to construct this JSON from DPPs. The Flow application checks the `success` field in every response to decide whether to continue or show an error.

---

### 3.C — Individual Processes

Build in this order. Process F is fully detailed as the template; subsequent processes fully detail unique patterns but reference Process F for shared patterns (Start shape, Return Documents, profile import).

---

### Process F: Mapping CRUD (`PROMO - Mapping CRUD`)

This is the simplest process — a good "hello world" to validate the FSS-to-process pipeline before tackling complex logic.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - ManageMappingsRequest` | `/integration/profiles/manageMappings-request.json` |
| `PROMO - Profile - ManageMappingsResponse` | `/integration/profiles/manageMappings-response.json` |

The request JSON contains:
- `operation` (string): one of `"list"`, `"create"`, `"update"`
- `filters` (object): optional filter fields (`devAccountId`, `componentType`, `componentName`)
- `mapping` (object): the mapping record to create or update (used by create/update operations)

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `operation` (string): echoes the requested operation
- `mappings` (array): returned mapping records (for list operations)
- `totalCount` (number): count of returned records

#### FSS Operation

1. Create `PROMO - FSS Op - ManageMappings` per the pattern in Section 3.B
2. Service Type: Message Action
3. Request Profile: `PROMO - Profile - ManageMappingsRequest`
4. Response Profile: `PROMO - Profile - ManageMappingsResponse`

#### Canvas — Shape by Shape

1. **Start shape**
   - Double-click the Start shape on the new process canvas
   - Connector: **Boomi Flow Services Server**
   - Action: **Listen**
   - Operation: select `PROMO - FSS Op - ManageMappings`
   - This receives the request JSON from the Flow Service

2. **Set Properties** (read request fields into DPPs)
   - Drag a **Set Properties** shape onto the canvas; connect Start to it
   - Add property: DPP `operation` = read from document using JSON profile `PROMO - Profile - ManageMappingsRequest`, path: `operation`
   - Add property: DPP `filterDevAccountId` = read from document path: `filters/devAccountId`
   - Add property: DPP `filterComponentType` = read from document path: `filters/componentType`
   - Add property: DPP `filterComponentName` = read from document path: `filters/componentName`

3. **Decision** (branch on operation type)
   - Drag a **Decision** shape; connect Set Properties to it
   - First branch condition: DPP `operation` **EQUALS** `"list"`
   - Name this branch: `List`
   - Default (else) branch handles create and update operations

4. **List branch — DataHub Query**
   - From the Decision `List` branch, add a **Connector** shape (DataHub)
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query ComponentMapping`
   - The query applies filters from the DPPs set in step 2 (configure filter parameters in the operation to read from DPPs `filterDevAccountId`, `filterComponentType`, `filterComponentName`)
   - If all filters are empty, the query returns all records (up to the limit)

5. **List branch — Map to response**
   - Add a **Map** shape after the DataHub Query on the List branch
   - Source profile: DataHub ComponentMapping query response (XML)
   - Destination profile: `PROMO - Profile - ManageMappingsResponse` (JSON)
   - Map fields:
     - Each `ComponentMapping` record maps to an entry in the `mappings` array
     - Map `devComponentId`, `devAccountId`, `prodComponentId`, `componentName`, `componentType`, `prodAccountId`, `prodLatestVersion`, `lastPromotedAt`, `lastPromotedBy`
     - Set `success` = `true`
     - Set `operation` = DPP `operation`
     - Set `totalCount` = count of records returned

6. **List branch — Return Documents**
   - Add a **Return Documents** shape after the Map; connect to it
   - No configuration needed — this sends the mapped response JSON back to Flow

7. **Create/Update branch — DataHub Update**
   - From the Decision default branch, add a **Connector** shape (DataHub)
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Update ComponentMapping`
   - The incoming document must be transformed to the DataHub XML update format before this shape
   - Add a **Map** shape between the Decision and the DataHub Update connector:
     - Source: `PROMO - Profile - ManageMappingsRequest` (JSON) — specifically the `mapping` object
     - Destination: DataHub ComponentMapping update request (XML)
     - Map `mapping.devComponentId`, `mapping.devAccountId`, `mapping.prodComponentId`, `mapping.componentName`, `mapping.componentType`, `mapping.prodAccountId`, `mapping.prodLatestVersion`

8. **Create/Update branch — Map to response**
   - Add a **Map** shape after the DataHub Update connector
   - Source: DataHub update response (XML)
   - Destination: `PROMO - Profile - ManageMappingsResponse` (JSON)
   - Set `success` = `true`
   - Set `operation` = DPP `operation`
   - Set `totalCount` = `1`

9. **Create/Update branch — Return Documents**
   - Add a **Return Documents** shape; connect to it

#### Error Handling

Add a **Try/Catch** around the DataHub connector shapes (both branches). In the Catch block:
1. Add a **Map** shape that builds the error response JSON:
   - `success` = `false`
   - `errorCode` = `"DATAHUB_ERROR"`
   - `errorMessage` = the caught exception message
2. Connect to a **Return Documents** shape

**Verify:**

- Deploy the process to your public cloud atom
- Send a test request through the Flow Service with `operation = "list"` and empty filters
- **Expected**: response with `success = true`, `operation = "list"`, `mappings = []` (empty array, since no records exist yet), `totalCount = 0`
- Send a test request with `operation = "create"` and a populated `mapping` object
- **Expected**: response with `success = true`, `operation = "create"`, `totalCount = 1`
- Send another `operation = "list"` request
- **Expected**: the mapping you just created appears in the `mappings` array

---

### Process A0: Get Dev Accounts (`PROMO - Get Dev Accounts`)

This process retrieves development sub-accounts accessible to the current user based on their SSO group memberships.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - GetDevAccountsRequest` | `/integration/profiles/getDevAccounts-request.json` |
| `PROMO - Profile - GetDevAccountsResponse` | `/integration/profiles/getDevAccounts-response.json` |

The request JSON contains:
- `userSsoGroups` (array of strings): the user's Azure AD group IDs

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `accounts` (array): each entry has `devAccountId` and `devAccountName`

#### FSS Operation

Create `PROMO - FSS Op - GetDevAccounts` per the pattern in Section 3.B, using `PROMO - Profile - GetDevAccountsRequest` and `PROMO - Profile - GetDevAccountsResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — same as Process F: Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - GetDevAccounts`

2. **Set Properties** (read request fields)
   - DPP `userSsoGroups` = read from document path: `userSsoGroups` (this is a JSON array; store it as a string for later parsing)

3. **Data Process — Parse SSO Groups**
   - Add a **Data Process** shape with a short Groovy script that splits the `userSsoGroups` JSON array into individual documents — one document per SSO group ID:
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import groovy.json.JsonSlurper

   String groupsJson = ExecutionUtil.getDynamicProcessProperty("userSsoGroups")
   def groups = new JsonSlurper().parseText(groupsJson)

   for (int i = 0; i < dataContext.getDataCount(); i++) {
       Properties props = dataContext.getProperties(i)
       groups.each { groupId ->
           dataContext.storeStream(
               new ByteArrayInputStream(groupId.getBytes("UTF-8")), props)
       }
   }
   ```
   - This produces N documents, one per SSO group

4. **For Each SSO Group — DataHub Query**
   - The multiple documents flow naturally into the next connector shape (Boomi processes each document)
   - Add a **Connector** shape (DataHub):
     - Connector: `PROMO - DataHub Connection`
     - Operation: `PROMO - DH Op - Query DevAccountAccess`
     - Filter: `ssoGroupId EQUALS` the current document content, `AND isActive EQUALS "true"`
   - Each query returns the DevAccountAccess records for that SSO group

5. **Data Process — Deduplicate Accounts**
   - Add a **Data Process** shape with Groovy that collects all results and deduplicates by `devAccountId`:
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import groovy.json.JsonOutput
   import groovy.xml.XmlSlurper

   def seen = new HashSet()
   def uniqueAccounts = []

   for (int i = 0; i < dataContext.getDataCount(); i++) {
       InputStream is = dataContext.getStream(i)
       Properties props = dataContext.getProperties(i)
       String xml = is.getText("UTF-8")
       def root = new XmlSlurper(false, false).parseText(xml)
       root.depthFirst().findAll { it.name() == 'DevAccountAccess' }.each { rec ->
           String accId = rec.devAccountId?.text()?.trim()
           if (accId && seen.add(accId)) {
               uniqueAccounts << [
                   devAccountId: accId,
                   devAccountName: rec.devAccountName?.text()?.trim() ?: ''
               ]
           }
       }
   }

   String output = JsonOutput.toJson(uniqueAccounts)
   dataContext.storeStream(
       new ByteArrayInputStream(output.getBytes("UTF-8")),
       dataContext.getProperties(0))
   ```
   - A user who belongs to multiple SSO groups may have access to the same dev account through more than one group. The `HashSet` on `devAccountId` eliminates these duplicates.

6. **Map — Build Response JSON**
   - Source: the deduplicated JSON array from step 5
   - Destination: `PROMO - Profile - GetDevAccountsResponse`
   - Map the `uniqueAccounts` array to the `accounts` array in the response
   - Set `success` = `true`

7. **Return Documents** — same as Process F

#### Error Handling

Wrap steps 4 and 5 in a **Try/Catch**. Catch block builds an error response with `errorCode = "DATAHUB_ERROR"`.

**Verify:**

- Seed at least one DevAccountAccess golden record in DataHub (see Phase 1, Step 1.4)
- Send a request with `userSsoGroups` containing the SSO group ID you seeded
- **Expected**: response with `success = true` and an `accounts` array containing the matching dev account
- Send a request with an SSO group ID that has no matching records
- **Expected**: response with `success = true` and `accounts = []` (empty array)

---

### Process E: Query Status (`PROMO - Query Status`)

This process queries the PromotionLog DataHub model for past promotion records, with optional filtering.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - QueryStatusRequest` | `/integration/profiles/queryStatus-request.json` |
| `PROMO - Profile - QueryStatusResponse` | `/integration/profiles/queryStatus-response.json` |

The request JSON contains:
- `promotionId` (string, optional): filter by specific promotion
- `devAccountId` (string, optional): filter by dev account
- `status` (string, optional): filter by status (e.g., `"COMPLETED"`, `"FAILED"`, `"IN_PROGRESS"`)
- `limit` (number): maximum records to return (default 50)

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `promotions` (array): each entry contains `promotionId`, `devAccountId`, `prodAccountId`, `devPackageId`, `initiatedBy`, `initiatedAt`, `status`, `componentsTotal`, `componentsCreated`, `componentsUpdated`, `componentsFailed`, `errorMessage`, `resultDetail`

#### FSS Operation

Create `PROMO - FSS Op - QueryStatus` per Section 3.B, using `PROMO - Profile - QueryStatusRequest` and `PROMO - Profile - QueryStatusResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - QueryStatus`

2. **Set Properties** (read request fields)
   - DPP `promotionId` = document path: `promotionId`
   - DPP `filterDevAccountId` = document path: `devAccountId`
   - DPP `filterStatus` = document path: `status`
   - DPP `queryLimit` = document path: `limit`

3. **DataHub Query**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query PromotionLog`
   - Build filters dynamically from DPPs: if `promotionId` is non-empty, add filter `promotionId EQUALS {value}`; if `filterDevAccountId` is non-empty, add filter `devAccountId EQUALS {value}`; if `filterStatus` is non-empty, add filter `status EQUALS {value}`
   - Set query limit from DPP `queryLimit` (default 50)
   - Combine multiple filters with `AND` operator

4. **Map — Build Response JSON**
   - Source: DataHub PromotionLog query response (XML)
   - Destination: `PROMO - Profile - QueryStatusResponse`
   - Map each PromotionLog record to a `promotions` array entry
   - Map all fields: `promotionId`, `devAccountId`, `prodAccountId`, `devPackageId`, `initiatedBy`, `initiatedAt`, `status`, `componentsTotal`, `componentsCreated`, `componentsUpdated`, `componentsFailed`, `errorMessage`, `resultDetail`
   - Set `success` = `true`

5. **Return Documents** — same as Process F

#### Error Handling

Wrap the DataHub Query in a **Try/Catch**. Catch block builds error response with `errorCode = "DATAHUB_ERROR"`.

**Verify:**

- First, run Process C (Execute Promotion) to create a PromotionLog record, or manually seed one via the DataHub API
- Send a Query Status request with the `promotionId` of that record
- **Expected**: response with `success = true` and the `promotions` array containing that single record
- Send a request with `status = "COMPLETED"` and no other filters
- **Expected**: all completed promotion records returned (up to the limit)
- Send a request with a non-existent `promotionId`
- **Expected**: `success = true`, `promotions = []`

---

### Process A: List Dev Packages (`PROMO - List Dev Packages`)

This process queries the Boomi Platform API for PackagedComponents in a specified dev account, handles pagination, and enriches each package with its component name.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - ListDevPackagesRequest` | `/integration/profiles/listDevPackages-request.json` |
| `PROMO - Profile - ListDevPackagesResponse` | `/integration/profiles/listDevPackages-response.json` |

The request JSON contains:
- `devAccountId` (string): the dev sub-account to query

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `packages` (array): each entry has `packageId`, `packageVersion`, `componentId`, `componentName`, `componentType`, `createdDate`, `notes`

#### FSS Operation

Create `PROMO - FSS Op - ListDevPackages` per Section 3.B, using `PROMO - Profile - ListDevPackagesRequest` and `PROMO - Profile - ListDevPackagesResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — same pattern as Process F: Operation = `PROMO - FSS Op - ListDevPackages`

2. **Set Properties** (read request fields)
   - DPP `devAccountId` = document path: `devAccountId`

3. **HTTP Client Send — Query PackagedComponents (first page)**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - QUERY PackagedComponent`
   - The operation URL includes `{1}` for account ID. In the operation's Parameters tab, set `{1}` = DPP `primaryAccountId`
   - Add query parameter: `overrideAccount` = DPP `devAccountId`
   - This sends a POST to `/partner/api/rest/v1/{primaryAccountId}/PackagedComponent/query` with `overrideAccount` targeting the dev sub-account
   - The response is XML containing `<PackagedComponent>` elements and optionally a `queryToken` for pagination

4. **Decision — Pagination Check**
   - Check the response XML for a `queryToken` element
   - Condition: document content contains `<queryToken>` (use a Decision shape with document property check, or a preceding Data Process that extracts the token into a DPP)
   - **YES** branch: continue to pagination loop
   - **NO** branch: skip to step 6 (enrich packages)

5. **Pagination Loop**
   - Add a **Data Process** shape with Groovy that extracts the `queryToken` from the response and sets DPP `queryToken`
   - Add a **Set Properties** shape or Groovy snippet with `Thread.sleep(120)` to enforce the 120ms rate-limit gap between API calls
   - Add another **HTTP Client Send** — POST to `/partner/api/rest/v1/{primaryAccountId}/PackagedComponent/queryMore` with the `queryToken` value and `overrideAccount` = DPP `devAccountId`
   - Loop back to the Decision in step 4: check for another `queryToken` in the new response
   - Accumulate all `<PackagedComponent>` elements across pages

6. **For Each Package — Enrich with Component Name**
   - For each `<PackagedComponent>` in the accumulated results:
   - Add an **HTTP Client Send** shape:
     - Operation: `PROMO - HTTP Op - GET ComponentMetadata`
     - URL parameter `{2}` = the `componentId` from the current PackagedComponent
     - Query parameter: `overrideAccount` = DPP `devAccountId`
   - This returns the component's `name` and `type` metadata
   - Add a 120ms gap between calls (Data Process with `Thread.sleep(120)`)

7. **Map — Build Response JSON**
   - Source: accumulated XML data (PackagedComponent + ComponentMetadata results)
   - Destination: `PROMO - Profile - ListDevPackagesResponse`
   - Map each package to a `packages` array entry:
     - `packageId` from PackagedComponent response
     - `packageVersion` from PackagedComponent response
     - `componentId` from PackagedComponent response
     - `componentName` from ComponentMetadata response
     - `componentType` from ComponentMetadata response
     - `createdDate` from PackagedComponent response
     - `notes` from PackagedComponent response
   - Set `success` = `true`

8. **Return Documents** — same as Process F

#### Error Handling

Wrap the entire HTTP Client sequence (steps 3-6) in a **Try/Catch**. Catch block handles:
- API authentication failures (`errorCode = "AUTH_FAILED"`)
- Rate limit errors on 429/503 (`errorCode = "API_RATE_LIMIT"`)
- Invalid account (`errorCode = "ACCOUNT_NOT_FOUND"`)

**Verify:**

- Ensure you have at least one PackagedComponent in a dev sub-account (create one manually if needed: Build --> Packaged Components --> Create)
- Send a request with `devAccountId` set to that sub-account's ID
- **Expected**: response with `success = true` and a `packages` array containing the packaged component with its `componentName` populated
- Send a request with a `devAccountId` that has no packages
- **Expected**: `success = true`, `packages = []`
- If the dev account has more than 100 packages, verify pagination works by checking that all packages appear in the response

---

### Process B: Resolve Dependencies (`PROMO - Resolve Dependencies`)

This process performs a breadth-first traversal of component references starting from a root component. It builds a complete dependency tree and checks each component against the DataHub for existing prod mappings (marking components as NEW or UPDATE).

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - ResolveDependenciesRequest` | `/integration/profiles/resolveDependencies-request.json` |
| `PROMO - Profile - ResolveDependenciesResponse` | `/integration/profiles/resolveDependencies-response.json` |

The request JSON contains:
- `devAccountId` (string): the dev sub-account
- `componentId` (string): the root component ID to resolve from

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `rootProcessName` (string): name of the root component
- `totalComponents` (number): total count of resolved components
- `components` (array): each entry has `devComponentId`, `name`, `type`, `devVersion`, `prodStatus` (`"NEW"` or `"UPDATE"`), `prodComponentId`, `prodCurrentVersion`, `hasEnvConfig`, `folderFullPath` (string, the component's folder path in dev), `isSharedConnection` (boolean, `true` if type is `connection`)

#### FSS Operation

Create `PROMO - FSS Op - ResolveDependencies` per Section 3.B, using `PROMO - Profile - ResolveDependenciesRequest` and `PROMO - Profile - ResolveDependenciesResponse`.

#### DPP Initialization

This process uses the following DPPs. Initialize them in a Set Properties shape immediately after reading request fields:

| DPP Name | Initial Value | Purpose |
|----------|--------------|---------|
| `rootComponentId` | (from request `componentId`) | Root component being resolved |
| `devAccountId` | (from request `devAccountId`) | Dev sub-account for API calls |
| `visitedComponentIds` | `[]` | JSON array tracking visited IDs |
| `componentQueue` | `["{rootComponentId}"]` | BFS queue; seeded with root ID |
| `visitedCount` | `0` | Counter for visited components |
| `queueCount` | `1` | Counter for remaining queue items |
| `currentComponentId` | (empty) | Set during each loop iteration |
| `alreadyVisited` | `false` | Flag set by `build-visited-set.groovy` |

#### Canvas — Shape by Shape

1. **Start shape** — Operation = `PROMO - FSS Op - ResolveDependencies`

2. **Set Properties — Read Request**
   - DPP `devAccountId` = document path: `devAccountId`
   - DPP `rootComponentId` = document path: `componentId`

3. **Set Properties — Initialize BFS State**
   - DPP `visitedComponentIds` = `[]`
   - DPP `componentQueue` = construct JSON array containing `rootComponentId` (use a Groovy Data Process if needed to build `["<rootComponentId value>"]`)
   - DPP `visitedCount` = `0`
   - DPP `queueCount` = `1`
   - DPP `alreadyVisited` = `false`

4. **Decision — Loop Condition: Queue Not Empty?**
   - Condition: DPP `queueCount` **GREATER THAN** `0`
   - **YES** branch: enter loop body (step 5)
   - **NO** branch: exit loop, skip to step 11

5. **Data Process — Pop Next from Queue**
   - Groovy script that reads the `componentQueue` DPP, removes the first item, sets it as `currentComponentId`, and updates `componentQueue` and `queueCount`:
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import groovy.json.JsonSlurper
   import groovy.json.JsonOutput

   def queue = new JsonSlurper().parseText(
       ExecutionUtil.getDynamicProcessProperty("componentQueue"))
   String nextId = queue.remove(0)
   ExecutionUtil.setDynamicProcessProperty("currentComponentId", nextId, false)
   ExecutionUtil.setDynamicProcessProperty("componentQueue",
       JsonOutput.toJson(queue), false)
   ExecutionUtil.setDynamicProcessProperty("queueCount",
       queue.size().toString(), false)
   ```

6. **HTTP Client Send — GET ComponentReference**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - GET ComponentReference`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - URL parameter `{2}` = DPP `currentComponentId`
   - Query parameter: `overrideAccount` = DPP `devAccountId`
   - Returns XML listing all component IDs referenced by the current component

7. **Data Process — `build-visited-set.groovy`**
   - Paste contents of `/integration/scripts/build-visited-set.groovy`
   - This script:
     - Reads DPPs: `visitedComponentIds`, `componentQueue`, `currentComponentId`
     - Checks if `currentComponentId` is already in the visited set
     - If visited: sets DPP `alreadyVisited` = `"true"` and skips
     - If not visited: adds to visited set, parses the ComponentReference XML to extract child component IDs, adds unvisited children to the queue
     - Writes DPPs: `visitedComponentIds`, `componentQueue`, `alreadyVisited`, `visitedCount`, `queueCount`

8. **Decision — Already Visited?**
   - Condition: DPP `alreadyVisited` **EQUALS** `"true"`
   - **YES** branch: skip this component, loop back to step 4
   - **NO** branch: continue to step 9

9. **HTTP Client Send — GET ComponentMetadata**
   - Operation: `PROMO - HTTP Op - GET ComponentMetadata`
   - URL parameter `{2}` = DPP `currentComponentId`
   - Query parameter: `overrideAccount` = DPP `devAccountId`
   - Returns component `name`, `type`, `version`, and other metadata
   - Extract `folderFullPath` from the metadata response and include it in the accumulated results JSON for each component. This path is passed through to Process C to construct the mirrored promotion target folder.

10. **DataHub Query — Check Existing Mapping**
    - Connector: `PROMO - DataHub Connection`
    - Operation: `PROMO - DH Op - Query ComponentMapping`
    - Filter: `devComponentId EQUALS` DPP `currentComponentId` `AND devAccountId EQUALS` DPP `devAccountId`
    - If a record is returned: this component has been promoted before; mark `prodStatus = "UPDATE"` and extract `prodComponentId` and `prodCurrentVersion` from the mapping
    - If no record: mark `prodStatus = "NEW"`, `prodComponentId = ""`, `prodCurrentVersion = 0`
    - Store these values as DPPs or accumulate into a results JSON document
    - **Loop back** to step 4 (the Decision on queue count)

11. **Data Process — Sort Results**
    - After the loop exits (queue is empty), use the `sort-by-dependency.groovy` logic or simply pass the accumulated results. The sort here is optional (Process C does the actual sort before promotion), but sorting in the response helps the UI display dependencies in logical order.

12. **Map — Build Response JSON**
    - Source: accumulated component results
    - Destination: `PROMO - Profile - ResolveDependenciesResponse`
    - Map each component to a `components` array entry
    - Set `rootProcessName` from the root component's metadata (captured during the first iteration)
    - Set `totalComponents` = DPP `visitedCount`
    - Set `success` = `true`

13. **Return Documents** — same as Process F

#### Error Handling

Wrap the loop body (steps 5-10) in a **Try/Catch**. In the Catch block:
- Log the error with `currentComponentId` for diagnostics
- Mark the component as having `prodStatus = "ERROR"` in the results
- Continue the loop (do not abort the entire traversal for one failed component)

For fatal errors (e.g., authentication failure), catch at the outer process level and return the standard error response.

**Verify:**

- In a dev sub-account, create a simple process that references at least one connection and one profile
- Package that process
- Send a Resolve Dependencies request with the process's `componentId` and the `devAccountId`
- **Expected**: response with `success = true`, `totalComponents >= 3` (the process + at least 1 connection + at least 1 profile), each entry showing `prodStatus = "NEW"` (since nothing has been promoted yet)
- Verify no duplicates: each `devComponentId` appears exactly once in the `components` array
- Verify the root process appears in the results with its correct `name` and `type = "process"`

---

### Process C: Execute Promotion (`PROMO - Execute Promotion`)

This is the core engine of the system. It promotes components from a dev sub-account to the primary account, handling XML retrieval, credential stripping, reference rewriting, and component creation or update via the Platform API. This is the most detailed process.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - ExecutePromotionRequest` | `/integration/profiles/executePromotion-request.json` |
| `PROMO - Profile - ExecutePromotionResponse` | `/integration/profiles/executePromotion-response.json` |

The request JSON contains:
- `devAccountId` (string): source dev sub-account
- `prodAccountId` (string): target primary account (usually same as `primaryAccountId`)
- `components` (array): list of components to promote, each with `devComponentId`, `name`, `type`, `folderFullPath`
- `initiatedBy` (string): username of the person initiating

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `promotionId` (string): unique ID for this promotion run
- `componentsCreated` (number), `componentsUpdated` (number), `componentsFailed` (number)
- `results` (array): each entry has `devComponentId`, `name`, `action` (`"CREATED"`, `"UPDATED"`, `"FAILED"`, `"SKIPPED"`), `prodComponentId`, `prodVersion`, `status`, `errorMessage`, `configStripped`
- `connectionsSkipped` (number): count of shared connections not promoted (filtered out)
- `missingConnectionMappings` (array, conditional): present when errorCode=MISSING_CONNECTION_MAPPINGS; each entry has `devComponentId`, `name`, `type`, `devAccountId`

#### FSS Operation

Create `PROMO - FSS Op - ExecutePromotion` per Section 3.B, using `PROMO - Profile - ExecutePromotionRequest` and `PROMO - Profile - ExecutePromotionResponse`.

#### DPP Initialization

| DPP Name | Initial Value | Purpose |
|----------|--------------|---------|
| `devAccountId` | (from request) | Source sub-account |
| `rootComponentId` | (from first component with type `process`, or first item) | Used by sort script |
| `promotionId` | (UUID generated at start) | Unique run ID |
| `componentMappingCache` | `{}` | JSON object accumulating dev-to-prod ID mappings |
| `currentComponentId` | (set per loop iteration) | Component being processed |
| `prodComponentId` | (set per iteration from DataHub or API response) | Prod ID for current component |
| `configStripped` | `"false"` | Set by `strip-env-config.groovy` |
| `strippedElements` | `""` | Set by `strip-env-config.groovy` |
| `referencesRewritten` | `"0"` | Set by `rewrite-references.groovy` |
| `connectionMappingCache` | `{}` | JSON object of connection mappings batch-queried from DataHub |
| `missingConnectionMappings` | `[]` | JSON array of missing connection mapping objects |
| `missingConnectionCount` | `"0"` | Count of missing connection mappings |
| `connectionMappingsValid` | `"true"` | Whether all connection mappings exist |
| `currentFolderFullPath` | (set per loop iteration) | Dev folder path for mirrored promotion target |

#### Canvas — Shape by Shape

1. **Start shape** — Operation = `PROMO - FSS Op - ExecutePromotion`

2. **Set Properties — Read Request**
   - DPP `devAccountId` = document path: `devAccountId`
   - DPP `initiatedBy` = document path: `initiatedBy`
   - DPP `rootComponentId` = identify the root process component from the `components` array (the component with `type = "process"` that matches the originally selected package)

3. **Data Process — Generate Promotion ID**
   - Groovy script:
   ```groovy
   import com.boomi.execution.ExecutionUtil
   String promotionId = UUID.randomUUID().toString()
   ExecutionUtil.setDynamicProcessProperty("promotionId", promotionId, false)
   ```

4. **DataHub Update — Create PromotionLog (IN_PROGRESS)**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Update PromotionLog`
   - Build the update XML from DPPs:
     - `promotionId` = DPP `promotionId`
     - `devAccountId` = DPP `devAccountId`
     - `prodAccountId` = DPP `primaryAccountId`
     - `initiatedBy` = DPP `initiatedBy`
     - `initiatedAt` = current timestamp
     - `status` = `"IN_PROGRESS"`
     - `componentsTotal` = count of components in request array
   - Use a **Map** shape before the DataHub connector to transform the request data into the PromotionLog update XML format

5. **Data Process — Sort Components (`sort-by-dependency.groovy`)**
   - Paste contents of `/integration/scripts/sort-by-dependency.groovy`
   - Input: the `components` array from the request (must be in JSON format on the document stream)
   - Reads DPP: `rootComponentId` (to identify the root process for priority 6 vs. 5)
   - Output: the same array sorted by type priority:
     1. `profile` (priority 1 — promoted first)
     2. `connection` (priority 2)
     3. `operation` (priority 3)
     4. `map` (priority 4)
     5. `process` — sub-processes (priority 5)
     6. `process` — root process (priority 6 — promoted last)
   - **Why bottom-up order matters**: each component's XML may reference other components by their IDs. Profiles and connections have no internal references. Operations reference connections. Maps reference profiles. Processes reference operations, maps, connections, and sub-processes. By promoting dependencies first, `rewrite-references.groovy` has all necessary dev-to-prod ID mappings in the cache when it processes each component.

5.5. **DataHub Batch Query — Load Connection Mappings**
    - Connector: `PROMO - DataHub Connection`
    - Operation: `PROMO - DH Op - Query ComponentMapping`
    - Filter: `componentType EQUALS "connection" AND devAccountId EQUALS` DPP `devAccountId`
    - Store the results in DPP `connectionMappingCache` as a JSON object (keys = dev connection IDs, values = prod connection IDs)
    - This single batch query replaces per-connection lookups during the promotion loop

5.6. **Data Process — `validate-connection-mappings.groovy`**
    - Paste contents of `/integration/scripts/validate-connection-mappings.groovy`
    - Input: the sorted components array from step 5
    - Reads DPPs: `connectionMappingCache`, `componentMappingCache`, `devAccountId`
    - Writes DPPs: `missingConnectionMappings`, `missingConnectionCount`, `connectionMappingsValid`, `componentMappingCache` (updated with found connection mappings)
    - Output: JSON array of NON-connection components only (connections filtered out)

5.7. **Decision — Connection Mappings Valid?**
    - Condition: DPP `connectionMappingsValid` **EQUALS** `"true"`
    - **YES** branch: continue to step 6 (Initialize Mapping Cache — now only needs non-connection mappings since connection mappings are pre-loaded)
    - **NO** branch: proceed to step 5.8

5.8. **Error Response — Missing Connection Mappings (NO branch)**
    - Build error response with:
      - `success` = `false`
      - `errorCode` = `"MISSING_CONNECTION_MAPPINGS"`
      - `errorMessage` = `"One or more connection mappings not found in DataHub. Admin must seed missing mappings via Mapping Viewer."`
      - `missingConnectionMappings` = DPP `missingConnectionMappings`
    - Update PromotionLog to `FAILED` with error details
    - **Return Documents** — skip the entire promotion loop

6. **Set Properties — Initialize Mapping Cache**
   - DPP `componentMappingCache` = `{}`

7. **For Each Component — Begin Loop**
   - The sorted components flow as individual documents. For each document:

8. **Try Block Start**
   - Wrap steps 9-17 in a **Try/Catch** shape

9. **Set Properties — Current Component**
   - DPP `currentComponentId` = the `devComponentId` of the current component from the document
   - DPP `currentComponentName` = the `name` field
   - DPP `currentComponentType` = the `type` field
   - DPP `currentFolderFullPath` = the `folderFullPath` field from the current component
   - Reset per-iteration DPPs: `configStripped` = `"false"`, `strippedElements` = `""`, `referencesRewritten` = `"0"`

10. **HTTP Client Send — GET Component XML from Dev**
    - Connector: `PROMO - Partner API Connection`
    - Operation: `PROMO - HTTP Op - GET Component`
    - URL parameter `{1}` = DPP `primaryAccountId`
    - URL parameter `{2}` = DPP `currentComponentId`
    - Query parameter: `overrideAccount` = DPP `devAccountId`
    - Returns the full component XML from the dev sub-account

11. **Data Process — `strip-env-config.groovy`**
    - Paste contents of `/integration/scripts/strip-env-config.groovy`
    - Input: component XML from step 10
    - This script strips environment-specific values from the XML:
      - `password` elements: emptied (connection credentials)
      - `host` elements: emptied (server hostnames)
      - `url` elements: emptied (endpoint URLs)
      - `port` elements: emptied (port numbers)
      - `EncryptedValue` elements: emptied (encrypted secrets)
    - Writes DPPs:
      - `configStripped` = `"true"` if any elements were stripped, `"false"` otherwise
      - `strippedElements` = comma-separated list of stripped element names (e.g., `"password,host,url"`)
    - The stripped XML is passed on the document stream (environment values must be reconfigured manually in the primary account after promotion)

12. **Data Process — Check Mapping Cache**
    - Groovy script that checks if `currentComponentId` already has a mapping in `componentMappingCache`:
    ```groovy
    import com.boomi.execution.ExecutionUtil
    import groovy.json.JsonSlurper

    String cacheJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
    def cache = new JsonSlurper().parseText(cacheJson ?: "{}")
    String currentId = ExecutionUtil.getDynamicProcessProperty("currentComponentId")

    if (cache.containsKey(currentId)) {
        ExecutionUtil.setDynamicProcessProperty("prodComponentId",
            cache[currentId], false)
        ExecutionUtil.setDynamicProcessProperty("mappingExists", "true", false)
    } else {
        ExecutionUtil.setDynamicProcessProperty("mappingExists", "false", false)
    }
    ```

13. **Decision — Mapping in Cache?**
    - Condition: DPP `mappingExists` **EQUALS** `"true"`
    - **YES**: skip DataHub query, proceed to step 15 (the component was promoted earlier in this same run)
    - **NO**: proceed to step 14

14. **DataHub Query — Check Existing Mapping in DataHub**
    - Connector: `PROMO - DataHub Connection`
    - Operation: `PROMO - DH Op - Query ComponentMapping`
    - Filter: `devComponentId EQUALS` DPP `currentComponentId` `AND devAccountId EQUALS` DPP `devAccountId`
    - If a record is returned: set DPP `prodComponentId` from the query result, set DPP `mappingExists` = `"true"`
    - If no record: DPP `mappingExists` remains `"false"`

15. **Decision — Mapping Exists? (Create vs. Update)**
    - Condition: DPP `mappingExists` **EQUALS** `"true"`
    - **YES branch (UPDATE path)**: proceed to step 15a
    - **NO branch (CREATE path)**: proceed to step 15b

#### 15a. UPDATE Path

    1. **Data Process — `rewrite-references.groovy`**
       - Paste contents of `/integration/scripts/rewrite-references.groovy`
       - Input: the stripped component XML from step 11
       - Reads DPP: `componentMappingCache` (the accumulated dev-to-prod ID mapping JSON object)
       - For each key-value pair in the cache, the script does a global find-and-replace in the XML: every occurrence of a dev component ID is replaced with the corresponding prod component ID
       - Writes DPP: `referencesRewritten` = count of IDs replaced
       - Output: the rewritten XML on the document stream

    2. **HTTP Client Send — POST Component Update**
       - Connector: `PROMO - Partner API Connection`
       - Operation: `PROMO - HTTP Op - POST Component Update`
       - URL parameter `{1}` = DPP `primaryAccountId`
       - URL parameter `{2}` = DPP `prodComponentId`
       - Request body: the rewritten component XML
       - The request XML uses `folderFullPath="/Promoted{currentFolderFullPath}"` per the updated template in `/integration/api-requests/update-component.xml`
       - Response returns the updated component with its new version number

    3. Extract `prodVersion` from the API response; set action = `"UPDATED"`

#### 15b. CREATE Path

    1. **Data Process — `rewrite-references.groovy`** — same as step 15a.1 above

    2. **HTTP Client Send — POST Component Create**
       - Connector: `PROMO - Partner API Connection`
       - Operation: `PROMO - HTTP Op - POST Component Create`
       - URL parameter `{1}` = DPP `primaryAccountId`
       - Request body: the rewritten component XML
       - The request XML uses `folderFullPath="/Promoted{currentFolderFullPath}"` per the updated template in `/integration/api-requests/create-component.xml`
       - The Platform API creates a new component in the primary account and returns the new `prodComponentId` and `version = 1`

    3. Extract `prodComponentId` from the API response; set DPP `prodComponentId`, set action = `"CREATED"`, `prodVersion = 1`

16. **Data Process — Update Mapping Cache**
    - After either the CREATE or UPDATE path, update the in-memory cache:
    ```groovy
    import com.boomi.execution.ExecutionUtil
    import groovy.json.JsonSlurper
    import groovy.json.JsonOutput

    String cacheJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
    def cache = new JsonSlurper().parseText(cacheJson ?: "{}")
    String devId = ExecutionUtil.getDynamicProcessProperty("currentComponentId")
    String prodId = ExecutionUtil.getDynamicProcessProperty("prodComponentId")

    cache[devId] = prodId

    ExecutionUtil.setDynamicProcessProperty("componentMappingCache",
        JsonOutput.toJson(cache), false)
    ```
    - This ensures that when the next component in the loop runs `rewrite-references.groovy`, it can replace the current component's dev ID with its prod ID in any XML that references it.

17. **Accumulate Result**
    - Add the current component's result to an accumulating JSON array (use a Data Process or DPP to collect):
      - `devComponentId`, `name` (from DPP `currentComponentName`), `action` (`"CREATED"` or `"UPDATED"`), `prodComponentId`, `prodVersion`, `status = "SUCCESS"`, `errorMessage = ""`, `configStripped` (from DPP `configStripped`)

18. **Catch Block** (from the Try/Catch in step 8)
    - When any step in the Try block fails for a component:
    1. Log the error with `currentComponentId` and exception message
    2. Add the component to the results array with `action = "FAILED"`, `status = "FAILED"`, `errorMessage = ` the exception message
    3. Mark dependent components as `"SKIPPED"` — any component in the remaining loop that references `currentComponentId` cannot be promoted correctly because its reference cannot be rewritten. Identify dependents by checking if their type is higher in the priority order (e.g., if a connection fails, its operations, maps, and processes are affected).
    4. **Continue the loop** — do not abort the entire promotion

19. **End of Loop** — after processing all components, continue to step 20

20. **DataHub Batch Update — Write All Mappings**
    - Connector: `PROMO - DataHub Connection`
    - Operation: `PROMO - DH Op - Update ComponentMapping`
    - Build a batch update XML containing all new and updated mappings from the promotion run
    - For each successfully promoted component, include:
      - `devComponentId`, `devAccountId`, `prodComponentId`, `componentName`, `componentType`, `prodAccountId` = DPP `primaryAccountId`, `prodLatestVersion`, `lastPromotedAt` = current timestamp, `lastPromotedBy` = DPP `initiatedBy`
    - This single batch write is more efficient than individual writes during the loop

21. **DataHub Update — Update PromotionLog (Final Status)**
    - Connector: `PROMO - DataHub Connection`
    - Operation: `PROMO - DH Op - Update PromotionLog`
    - Update the record created in step 4:
      - `status` = `"COMPLETED"` if no failures, `"PARTIAL"` if some failed, `"FAILED"` if all failed
      - `componentsCreated` = count of CREATED results
      - `componentsUpdated` = count of UPDATED results
      - `componentsFailed` = count of FAILED results
      - `resultDetail` = JSON string summarizing the results

22. **Map — Build Response JSON**
    - Source: accumulated results and DPPs
    - Destination: `PROMO - Profile - ExecutePromotionResponse`
    - Map:
      - `promotionId` = DPP `promotionId`
      - `componentsCreated`, `componentsUpdated`, `componentsFailed` = computed counts
      - `results` array = all accumulated component results
      - `success` = `true` (even if some components failed — the promotion operation itself succeeded)
      - `errorCode`, `errorMessage` = empty (set only if the entire process failed catastrophically)

23. **Return Documents** — same as Process F

#### Key Detail: componentMappingCache and Bottom-Up Sort

The `componentMappingCache` DPP is the linchpin of this process. It accumulates `devComponentId --> prodComponentId` mappings as components are promoted one by one. The `rewrite-references.groovy` script reads this cache and performs global find-and-replace in each component's XML, swapping dev IDs for prod IDs.

This is why the bottom-up sort order in step 5 is essential:

1. **Profiles** are promoted first. They have no internal component references. Their dev-to-prod mapping is added to the cache.
2. **Connections** are promoted next. They also have no references to other components. Mappings added to cache.
3. **Operations** reference connections. When `rewrite-references.groovy` runs on an operation's XML, the cache already contains the connection's dev-to-prod mapping, so the connection reference is rewritten correctly.
4. **Maps** reference profiles. Same logic — profile mappings are already in the cache.
5. **Sub-processes** reference operations, maps, connections. All those mappings are in the cache.
6. **Root process** is promoted last. All dependencies are in the cache. Every internal reference is rewritten to point at the prod components.

If you promote in the wrong order (e.g., process first), its XML would still contain dev IDs for dependencies not yet promoted, and the resulting prod component would have broken references.

**Verify:**

- In a dev sub-account, create a minimal dependency tree:
  - One HTTP Client Connection
  - One process that uses that connection
- Resolve dependencies first (Process B) to confirm the tree
- Send an Execute Promotion request with both components
- **Expected**:
  - Response with `success = true`
  - `componentsCreated = 2` (both are new, since this is the first promotion)
  - The connection result appears first in the `results` array (promoted before the process)
  - The process result shows `configStripped = false` (processes typically have no passwords)
  - The connection result may show `configStripped = true` (if it had password/host/url values)
  - In the primary Boomi account, verify the two new components exist
  - In DataHub, query ComponentMapping and verify two new golden records
  - In DataHub, query PromotionLog and verify one record with `status = "COMPLETED"`
- Re-run the same promotion
- **Expected**:
  - `componentsCreated = 0`, `componentsUpdated = 2` (both now exist, so they get updated)
  - Version numbers increment by 1

---

### Process D: Package and Deploy (`PROMO - Package and Deploy`)

This process creates a PackagedComponent from a promoted component, optionally creates or updates an Integration Pack, and deploys to target environments.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - PackageAndDeployRequest` | `/integration/profiles/packageAndDeploy-request.json` |
| `PROMO - Profile - PackageAndDeployResponse` | `/integration/profiles/packageAndDeploy-response.json` |

The request JSON contains:
- `prodComponentId` (string): the promoted root process component in the primary account
- `prodAccountId` (string): the primary account ID
- `packageVersion` (string): version label for the package (e.g., `"1.2.0"`)
- `integrationPackId` (string): existing Integration Pack ID (used when `createNewPack = false`)
- `createNewPack` (boolean): `true` to create a new Integration Pack, `false` to add to existing
- `newPackName` (string): name for new pack (required if `createNewPack = true`)
- `newPackDescription` (string): description for new pack
- `targetAccountGroupId` (string): account group to deploy to

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `packagedComponentId` (string): ID of the created PackagedComponent
- `integrationPackId` (string): ID of the Integration Pack (new or existing)
- `integrationPackName` (string): name of the Integration Pack
- `releaseVersion` (string): the released pack version
- `deploymentStatus` (string): overall deployment status
- `deployedEnvironments` (array): each entry has `environmentId`, `environmentName`, `status`

#### FSS Operation

Create `PROMO - FSS Op - PackageAndDeploy` per Section 3.B, using `PROMO - Profile - PackageAndDeployRequest` and `PROMO - Profile - PackageAndDeployResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Operation = `PROMO - FSS Op - PackageAndDeploy`

2. **Set Properties — Read Request**
   - DPP `prodComponentId` = document path: `prodComponentId`
   - DPP `prodAccountId` = document path: `prodAccountId`
   - DPP `packageVersion` = document path: `packageVersion`
   - DPP `createNewPack` = document path: `createNewPack`
   - DPP `integrationPackId` = document path: `integrationPackId`
   - DPP `newPackName` = document path: `newPackName`
   - DPP `newPackDescription` = document path: `newPackDescription`
   - DPP `targetAccountGroupId` = document path: `targetAccountGroupId`

3. **HTTP Client Send — POST PackagedComponent**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - POST PackagedComponent`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - Request body: JSON containing `componentId` = DPP `prodComponentId`, `packageVersion` = DPP `packageVersion`, `notes` = promotion metadata, `shareable` = `true`
   - Build the request JSON with a Map shape before this connector:
     - Source: DPPs
     - Destination: PackagedComponent create JSON
   - Response returns the new `packagedComponentId`
   - Extract `packagedComponentId` into a DPP

4. **Decision — Create New Pack?**
   - Condition: DPP `createNewPack` **EQUALS** `"true"`
   - **YES** branch: step 5 (create new Integration Pack)
   - **NO** branch: step 6 (add to existing pack)

5. **YES Branch — HTTP Client Send — POST IntegrationPack**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - POST IntegrationPack`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - Request body: JSON with `name` = DPP `newPackName`, `description` = DPP `newPackDescription`
   - Response returns the new `integrationPackId`
   - Set DPP `integrationPackId` from the response
   - After creating the pack, add the PackagedComponent to it (Platform API call to add component to pack)
   - Continue to step 7

6. **NO Branch — Add to Existing Pack**
   - The `integrationPackId` DPP already holds the existing pack ID
   - Add the PackagedComponent (from step 3) to the existing Integration Pack via the Platform API
   - Continue to step 7

7. **HTTP Client Send — Release Integration Pack**
   - POST to release the Integration Pack (makes it deployable)
   - This may use an existing HTTP operation or a generic HTTP Client Send with the release endpoint
   - URL: `/partner/api/rest/v1/{primaryAccountId}/IntegrationPackRelease`
   - Request body includes `integrationPackId` and release notes
   - Response returns the `releaseVersion`

8. **For Each Target Environment — Deploy**
   - If `targetAccountGroupId` is provided, deploy the released pack:
   - **HTTP Client Send** — POST DeployedPackage
     - Connector: `PROMO - Partner API Connection`
     - Operation: `PROMO - HTTP Op - POST DeployedPackage`
     - URL parameter `{1}` = DPP `primaryAccountId`
     - Request body: JSON with `packageId`, `environmentId`, and deployment parameters
   - Accumulate deployment results for each environment (success/failure per environment)
   - Add 120ms gap between deployment calls

9. **Map — Build Response JSON**
   - Source: accumulated results and DPPs
   - Destination: `PROMO - Profile - PackageAndDeployResponse`
   - Map:
     - `packagedComponentId` from DPP
     - `integrationPackId` from DPP
     - `integrationPackName` = DPP `newPackName` (or queried name for existing pack)
     - `releaseVersion` from step 7 response
     - `deploymentStatus` = `"DEPLOYED"` if all succeeded, `"PARTIAL"` if some failed
     - `deployedEnvironments` array from step 8 results
     - `success` = `true`

10. **Return Documents** — same as Process F

#### Error Handling

Wrap the entire process (steps 3-8) in a **Try/Catch**:
- **PackagedComponent creation failure**: return error with `errorCode = "PROMOTION_FAILED"`
- **Integration Pack failure**: return error with `errorCode = "PROMOTION_FAILED"`
- **Deployment failure**: per-environment — mark individual environments as failed in the `deployedEnvironments` array, but continue deploying to remaining environments. Set `deploymentStatus = "PARTIAL"`.

**Verify:**

- First, promote a component using Process C so you have a `prodComponentId` in the primary account
- Send a Package and Deploy request with `createNewPack = true`, a `newPackName`, and a `targetAccountGroupId`
- **Expected**:
  - Response with `success = true`
  - `packagedComponentId` is populated (new PackagedComponent created)
  - `integrationPackId` is populated (new Integration Pack created)
  - `releaseVersion` is populated
  - `deployedEnvironments` shows each target with `status = "DEPLOYED"`
- Verify in Boomi AtomSphere:
  - The PackagedComponent appears under the promoted component
  - The Integration Pack exists with the component included
  - The deployment appears in Deploy --> Deployments

---

### Summary: Process Build Order Checklist

Use this checklist to track your progress. Build and verify each process before moving to the next.

| Order | Process | Component Name | FSS Operation | Status |
|-------|---------|---------------|---------------|--------|
| 1 | F | `PROMO - Mapping CRUD` | `PROMO - FSS Op - ManageMappings` | [ ] |
| 2 | A0 | `PROMO - Get Dev Accounts` | `PROMO - FSS Op - GetDevAccounts` | [ ] |
| 3 | E | `PROMO - Query Status` | `PROMO - FSS Op - QueryStatus` | [ ] |
| 4 | A | `PROMO - List Dev Packages` | `PROMO - FSS Op - ListDevPackages` | [ ] |
| 5 | B | `PROMO - Resolve Dependencies` | `PROMO - FSS Op - ResolveDependencies` | [ ] |
| 6 | C | `PROMO - Execute Promotion` | `PROMO - FSS Op - ExecutePromotion` | [ ] |
| 7 | D | `PROMO - Package and Deploy` | `PROMO - FSS Op - PackageAndDeploy` | [ ] |

After completing all seven processes, proceed to Phase 4 to create the Flow Service component that ties them together.

---

## Phase 4: Flow Service Component

### Step 4.1 -- Create Flow Service

Reference: `/integration/flow-service/flow-service-spec.md`

1. Navigate to **Build -> New Component -> Flow Service**.
2. Name: `PROMO - Flow Service`.
3. On the **General** tab, configure:
   - **Path to Service**: `/fs/PromotionService`
   - **External Name**: `PromotionService`
4. Open the **Message Actions** tab. Add 7 actions, linking each to its FSS Operation, Request Profile, and Response Profile:

| # | Action Name | FSS Operation | Request Profile | Response Profile |
|---|-------------|---------------|-----------------|------------------|
| 1 | `getDevAccounts` | `PROMO - FSS Op - GetDevAccounts` | `PROMO - Profile - GetDevAccountsRequest` | `PROMO - Profile - GetDevAccountsResponse` |
| 2 | `listDevPackages` | `PROMO - FSS Op - ListDevPackages` | `PROMO - Profile - ListDevPackagesRequest` | `PROMO - Profile - ListDevPackagesResponse` |
| 3 | `resolveDependencies` | `PROMO - FSS Op - ResolveDependencies` | `PROMO - Profile - ResolveDependenciesRequest` | `PROMO - Profile - ResolveDependenciesResponse` |
| 4 | `executePromotion` | `PROMO - FSS Op - ExecutePromotion` | `PROMO - Profile - ExecutePromotionRequest` | `PROMO - Profile - ExecutePromotionResponse` |
| 5 | `packageAndDeploy` | `PROMO - FSS Op - PackageAndDeploy` | `PROMO - Profile - PackageAndDeployRequest` | `PROMO - Profile - PackageAndDeployResponse` |
| 6 | `queryStatus` | `PROMO - FSS Op - QueryStatus` | `PROMO - Profile - QueryStatusRequest` | `PROMO - Profile - QueryStatusResponse` |
| 7 | `manageMappings` | `PROMO - FSS Op - ManageMappings` | `PROMO - Profile - ManageMappingsRequest` | `PROMO - Profile - ManageMappingsResponse` |

5. Open the **Configuration Values** tab. Add a configuration value:
   - **Name**: `primaryAccountId`
   - **Type**: String
   - **Required**: Yes
   - **Description**: Primary Boomi account ID passed to every integration process via Dynamic Process Properties
6. Save the component.

### Step 4.2 -- Deploy Flow Service

1. Open the `PROMO - Flow Service` component in Build.
2. Select **Create Packaged Component**.
3. Enter a version label (e.g., `1.0.0`) and add deployment notes.
4. Navigate to **Deploy -> Deployments**.
5. Select the packaged `PROMO - Flow Service` component.
6. Choose deployment target: **Public Boomi Cloud Atom**.
7. Select the target environment and deploy.
8. After deployment, set the `primaryAccountId` configuration value:
   - Navigate to the deployed component in **Manage -> Atom Management**.
   - Open **Properties -> Configuration Values**.
   - Set `primaryAccountId` to your primary Boomi account ID.
   - Save.
9. Navigate to **Runtime Management -> Listeners**. All 7 FSS Operations should appear and show a running status:
   - `PROMO - FSS Op - GetDevAccounts`
   - `PROMO - FSS Op - ListDevPackages`
   - `PROMO - FSS Op - ResolveDependencies`
   - `PROMO - FSS Op - ExecutePromotion`
   - `PROMO - FSS Op - PackageAndDeploy`
   - `PROMO - FSS Op - QueryStatus`
   - `PROMO - FSS Op - ManageMappings`
10. Note the full service URL: `https://{cloud-base-url}/fs/PromotionService`

### Phase 4 Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Operation not found" error when calling an action | FSS Operation not linked on the Message Actions tab | Open the Flow Service, verify each action row references the correct `PROMO - FSS Op - *` component |
| No listeners appear after deployment | Atom not running, or Flow Service not deployed to the correct atom | Confirm the atom is a public cloud atom, redeploy the packaged component, and restart the atom if needed |
| Requests time out with no response | Atom health degraded, or the linked Integration process has an error | Check **Process Reporting** for the target process; increase atom timeout settings if the process is long-running |
| "Configuration value not set" in process logs | `primaryAccountId` not configured post-deployment | Set the value in **Atom Management -> Properties -> Configuration Values** and restart the listener |

**Verify:**

Send a test request directly to the deployed Flow Service. Use the `getDevAccounts` action because it requires no input parameters beyond authentication.

```bash
# Linux/macOS
curl -s -X POST \
  -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://{cloud-base-url}/fs/PromotionService" \
  -d '{
    "action": "getDevAccounts",
    "request": {
      "userSsoGroups": ["YOUR_SSO_GROUP_ID"]
    }
  }'
```

```powershell
# Windows (PowerShell)
$cred = [Convert]::ToBase64String(
  [Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token")
)
$headers = @{
    Authorization  = "Basic $cred"
    Accept         = "application/json"
    "Content-Type" = "application/json"
}
$body = @'
{
  "action": "getDevAccounts",
  "request": {
    "userSsoGroups": ["YOUR_SSO_GROUP_ID"]
  }
}
'@
Invoke-RestMethod -Uri "https://{cloud-base-url}/fs/PromotionService" `
  -Method POST -Headers $headers -Body $body
```

A successful response contains `"success": true` and an `accounts` array. If you receive an error, consult the troubleshooting table above.

---

## Phase 5: Flow Dashboard

### Step 5.1 -- Install Connector

1. In Boomi Flow, navigate to **Services -> Connectors -> New Connector**.
2. Select connector type: **Boomi Integration Service**.
3. Configure the connection:
   - **Runtime Type**: Public Cloud
   - **Path to Service**: `/fs/PromotionService`
   - **Authentication**: Basic
     - **Username**: the shared web server user (from **Shared Web Server User Management** in AtomSphere)
     - **Password**: the API token for that user
4. Click **"Retrieve Connector Configuration Data"**. Flow contacts the deployed Flow Service and auto-discovers all 7 message actions. Wait for the operation to complete.
5. Verify the auto-generated Flow Types. You should see exactly 14 types (one request and one response for each action):
   1. `getDevAccounts REQUEST - getDevAccountsRequest`
   2. `getDevAccounts RESPONSE - getDevAccountsResponse`
   3. `listDevPackages REQUEST - listDevPackagesRequest`
   4. `listDevPackages RESPONSE - listDevPackagesResponse`
   5. `resolveDependencies REQUEST - resolveDependenciesRequest`
   6. `resolveDependencies RESPONSE - resolveDependenciesResponse`
   7. `executePromotion REQUEST - executePromotionRequest`
   8. `executePromotion RESPONSE - executePromotionResponse`
   9. `packageAndDeploy REQUEST - packageAndDeployRequest`
   10. `packageAndDeploy RESPONSE - packageAndDeployResponse`
   11. `queryStatus REQUEST - queryStatusRequest`
   12. `queryStatus RESPONSE - queryStatusResponse`
   13. `manageMappings REQUEST - manageMappingsRequest`
   14. `manageMappings RESPONSE - manageMappingsResponse`
6. Open the **Configuration Values** section of the connector. Set `primaryAccountId` to your primary Boomi account ID.
7. Click **Install**, then **Save**.

**Verify:** Open the connector and confirm all 14 types appear under **Types**. If any are missing, click "Retrieve Connector Configuration Data" again and check that the Flow Service is deployed and all 7 listeners are running.

### Step 5.2 -- Create Flow Application

1. Navigate to **Flow -> Build -> New Flow**.
2. Name: `Promotion Dashboard`.
3. Add **Developer Swimlane**:
   - Authorization: SSO group `Boomi Developers`
   - This swimlane is the entry point for the application
4. Add **Admin Swimlane**:
   - Authorization: SSO group `Boomi Admins`
   - This swimlane receives control after the developer submits for approval

Build the 6 pages in order. Each page uses Message steps to call Flow Service actions and Decision steps to handle the `success` field in responses.

#### Page 1: Package Browser (Developer Swimlane)

Reference: `/flow/page-layouts/page1-package-browser.md` for full UI specification.

This is the developer entry point. Users select a dev account and browse available packages.

**Page load -- Message step configuration:**

1. Add a **Message** step on the page load event.
   - **Action**: `getDevAccounts`
   - **Connector**: `Promotion Service Connector`
   - **Input values**: Bind `userSsoGroups` from the SSO authorization context (the user's Azure AD group memberships)
   - **Output values**: Bind response to `accessibleAccounts` Flow value (list of dev accounts with `devAccountId` and `devAccountName` fields)
2. Add a **Decision** step immediately after the Message step.
   - **Condition**: `{getDevAccountsResponse.success} == true`
   - **True path**: Continue to render page UI
   - **False path**: Navigate to Error Page with `{getDevAccountsResponse.errorMessage}`

**UI components:**

3. Add an **Account Selector** combobox:
   - Data source: `accessibleAccounts`
   - Display field: `devAccountName`
   - Value field: `devAccountId`
   - On change: Store selected value in `selectedDevAccountId` and `selectedDevAccountName` Flow values, then trigger a second Message step
4. Add the on-change **Message** step for the combobox:
   - **Action**: `listDevPackages`
   - **Input values**: `selectedDevAccountId`
   - **Output values**: `packages` (array of package objects)
   - **Decision**: Check `{listDevPackagesResponse.success} == true`; on failure, show error
5. Add a **Packages Data Grid** bound to the `packages` output. Columns: Package Name, Version, Type, Created (default sort descending), Notes.
6. On row select: Store the entire row object in `selectedPackage` Flow value (contains `componentId`, `packageId`, `componentName`, `packageVersion`).
7. Add a **"Review for Promotion"** button:
   - Enabled when `selectedPackage` is not null
   - On click: Navigate to Page 2

**Flow values set on this page:** `selectedDevAccountId`, `selectedDevAccountName`, `selectedPackage`, `accessibleAccounts`.

#### Page 2: Promotion Review (Developer Swimlane)

Reference: `/flow/page-layouts/page2-promotion-review.md` for full UI specification.

Displays the resolved dependency tree and allows the developer to execute promotion.

**Page load:**

1. Message step: action = `resolveDependencies`, inputs = `selectedPackage.componentId` + `selectedDevAccountId`, outputs = `dependencyTree` (list), `totalComponents`, `newCount`, `updateCount`, `envConfigCount`.
2. Decision step: check `{resolveDependenciesResponse.success} == true`. Failure path goes to Error Page.

**UI components:**

3. **Summary labels**: Root Process name, Total Components count, badges for "X to create", "Y to update", "Z with credentials to reconfigure" (conditional on `envConfigCount > 0`).
4. **Dependency Tree Data Grid** bound to `dependencyTree`. Columns: Component Name (bold for root), Type (badge), Dev Version, Prod Status (NEW/UPDATE badge), Prod Component ID (truncated GUID), Prod Version, Env Config (warning icon). Grid is pre-sorted by dependency order (profiles first, root process last) and not user-sortable.
5. **"Promote to Primary Account"** button:
   - On click: Show confirmation modal summarizing counts
   - On confirm: Message step with action = `executePromotion`, inputs = `selectedPackage.componentId` + `selectedDevAccountId` + `dependencyTree`, outputs = `promotionId`, `promotionResults`, `componentsCreated`, `componentsUpdated`, `componentsFailed`
   - Decision step: check success. On true: navigate to Page 3. On false: navigate to Error Page
   - The Flow Service handles async wait responses automatically; the user sees a spinner during execution
6. **"Cancel"** button: Navigate back to Page 1.

#### Page 3: Promotion Status (Developer Swimlane)

Reference: `/flow/page-layouts/page3-promotion-status.md` for full UI specification.

Displays results after `executePromotion` completes. The Flow Service returns wait responses during long-running promotion; the user sees a spinner and can safely close the browser.

**UI components (after completion):**

1. **Summary section**: Promotion ID (copyable), badges for Created/Updated/Failed counts.
2. **Results Data Grid** bound to `promotionResults`. Columns: Component Name, Action (CREATE/UPDATE badge), Status (SUCCESS/FAILED badge), Prod Component ID, Prod Version, Config Stripped (warning icon if true), Error message (red text, truncated with tooltip).
3. **Credential Warning box** (conditional): Shown when any component has `configStripped = true`. Lists affected component names and instructions for reconfiguration in the primary account Build tab.
4. **"Submit for Integration Pack Deployment"** button:
   - Enabled only when `componentsFailed == 0`
   - On click: Navigate to Page 4
5. **"Done"** button: End flow.

#### Page 4: Deployment Submission (Developer to Admin Transition)

Reference: `/flow/page-layouts/page4-deployment-submission.md` for full UI specification.

The developer fills out deployment details and submits for admin approval. This page marks the transition between the Developer and Admin swimlanes.

**Form components:**

1. **Package Version** text input: Pre-populated from `selectedPackage.packageVersion`. Required.
2. **Integration Pack Selector** combobox: Options include "Create New Integration Pack" (special value) and existing packs. On "Create New" selection, show conditional fields below.
3. **New Pack Name** text input (conditional): Shown when "Create New" is selected. Required when visible.
4. **New Pack Description** textarea (conditional): Shown when "Create New" is selected. Optional.
5. **Target Account Group** combobox: Populated from available account groups. Required.
6. **Deployment Notes** textarea: Optional, max 500 characters.

**Submit behavior:**

7. **"Submit for Approval"** button:
   - Validates all required fields
   - Builds the `deploymentRequest` object with `promotionId`, `packageVersion`, `integrationPackId` (or `createNewPack` + `newPackName`), `targetAccountGroupId`, `notes`, `submittedBy`, `processName`, `componentsTotal`
   - Sends email notification to admin distribution list:
     - **To**: admin group email (e.g., `boomi-admins@company.com`)
     - **Subject**: `"Promotion Approval Needed: {processName} v{packageVersion}"`
     - **Body**: Promotion ID, process name, package version, component counts, deployment details, submitter info, and a link to the approval queue
   - Transitions to the **Admin swimlane** -- the flow pauses at the swimlane boundary
   - Developer sees a confirmation message ("Submitted for approval!") with the Promotion ID, then the flow ends for them
8. **"Cancel"** button: Navigate back to Page 3.

#### Page 5: Approval Queue (Admin Swimlane)

Reference: `/flow/page-layouts/page5-approval-queue.md` for full UI specification.

Admin authenticates via SSO ("Boomi Admins" group) and reviews pending deployment requests.

**Page load:**

1. Message step: action = `queryStatus`, inputs = `status` = "COMPLETED" and `deployed` = false, output = `pendingApprovals` array.
2. Decision step: check success.

**UI components:**

3. **Approval Queue Data Grid** bound to `pendingApprovals`. Columns: Submitter, Process Name, Components count, Created/Updated counts, Submitted date (default sort descending), Status badge, Notes (truncated).
4. On row select: Expand **Promotion Detail Panel** below the grid. Panel sections: Submission Details (submitter, promotion ID, package version, integration pack, target account group, notes), Promotion Results (component results mini-table with summary badges), Credential Warning (conditional, lists components needing reconfiguration), Source Account info.
5. **Admin Comments** textarea below the detail panel. Optional, max 500 characters.
6. **"Approve and Deploy"** button (green, enabled when a row is selected):
   - Confirmation modal summarizing process name, version, target, component count
   - On confirm: Message step with action = `packageAndDeploy`, inputs = `promotionId` + `deploymentRequest` + `adminComments` + `approvedBy`, outputs = `deploymentResults` + `deploymentId`
   - Decision step: check success; display results or error
   - On success: Send approval email to submitter (subject: `"Approved: {processName} v{packageVersion}"`), refresh the approval queue
7. **"Deny"** button (red, enabled when a row is selected):
   - Denial reason modal with required textarea
   - On confirm: Update promotion status to DENIED, send denial email to submitter (subject: `"Denied: {processName} v{packageVersion}"`, body includes denial reason and admin comments), refresh the queue
8. **"View Component Mappings"** link in the page header: Navigate to Page 6.

#### Page 6: Mapping Viewer (Admin Swimlane)

Reference: `/flow/page-layouts/page6-mapping-viewer.md` for full UI specification.

Admin views and manages dev-to-prod component ID mappings stored in the DataHub.

**Page load:**

1. Message step: action = `manageMappings`, input = `operation` = "list", output = `mappings` array.
2. Decision step: check success.

**UI components:**

3. **Filter bar** above the grid:
   - Component Type dropdown (All / process / connection / map / profile / operation)
   - Dev Account dropdown (All / list of accessible accounts)
   - Text search input (filters by component name, case-insensitive, 300ms debounce)
   - Apply and Clear buttons
4. **Mapping Data Grid** bound to `mappings`. 8 columns: Component Name, Type (badge), Dev Account (truncated GUID with tooltip), Dev Component ID (truncated GUID), Prod Component ID (truncated GUID), Prod Version, Last Promoted (default sort descending), Promoted By. Pagination at 50 rows per page.
5. **"Export to CSV"** button (top right): Exports the current filtered view to `component-mappings-{date}.csv`.
6. **Manual Mapping Form** (collapsible, collapsed by default): Expand via "Add/Edit Mapping" toggle. Fields: Dev Component ID, Dev Account ID, Prod Component ID, Component Name, Component Type dropdown. CRUD operations use the `manageMappings` action:
   - Create: `operation` = "create" with mapping object
   - Update: `operation` = "update" with mapping ID and changed fields
   - Delete: `operation` = "delete" with mapping ID
   - Each operation followed by a Decision step checking success. On success, refresh the grid and collapse the form. On failure, display the error and keep the form open.
7. **"Back to Approval Queue"** link: Navigate to Page 5.

### Step 5.3 -- Configure SSO

1. In Azure AD (Entra), create or verify two security groups:
   - `Boomi Developers` -- contains all developer users who will browse packages and submit promotions
   - `Boomi Admins` -- contains administrators who approve or deny deployment requests
2. In Boomi Flow, open the Identity connector (Azure AD / Entra).
3. Map each group to the corresponding swimlane:
   - `Boomi Developers` -> Developer Swimlane
   - `Boomi Admins` -> Admin Swimlane
4. Save the Identity connector configuration.

### Step 5.4 -- Wire Navigation

Connect all pages via Outcome elements on the Flow canvas.

1. **Flow start** -> Page 1 (Package Browser) in the Developer swimlane.
2. **Page 1** "Review for Promotion" button outcome -> Page 2 (Promotion Review).
3. **Page 2** "Promote" button (after `executePromotion` Message step + success Decision) -> Page 3 (Promotion Status).
4. **Page 2** "Cancel" button outcome -> Page 1.
5. **Page 3** "Submit for Integration Pack Deployment" button outcome -> Page 4 (Deployment Submission).
6. **Page 3** "Done" button outcome -> End flow.
7. **Page 4** "Submit for Approval" button outcome -> Swimlane transition (Developer -> Admin) -> Page 5 (Approval Queue).
8. **Page 4** "Cancel" button outcome -> Page 3.
9. **Page 5** "Approve and Deploy" (after `packageAndDeploy` success) -> Refresh queue / End flow.
10. **Page 5** "Deny" (after denial confirmation) -> Refresh queue / End flow.
11. **Page 5** "View Component Mappings" link outcome -> Page 6 (Mapping Viewer).
12. **Page 6** "Back to Approval Queue" link outcome -> Page 5.

For every Decision step, wire the **failure outcome** to a shared Error Page that displays `{responseObject.errorMessage}` with Back, Retry, and Home buttons.

**Verify:**

1. Open the published Flow application URL in a browser.
2. **Developer flow**: Authenticate as a user in the `Boomi Developers` SSO group. Select a dev account, browse packages, select a package, click "Review for Promotion", review the dependency tree, click "Promote to Primary Account", confirm, wait for results on the status page, and click "Submit for Integration Pack Deployment". Fill out the deployment form and submit. Confirm you see the "Submitted for approval!" message and receive a confirmation email.
3. **Admin flow**: Authenticate as a user in the `Boomi Admins` SSO group (or follow the link from the notification email). Verify the pending request appears in the Approval Queue. Select it, review the detail panel, add admin comments, and click "Approve and Deploy". Confirm the deployment succeeds and the submitter receives an approval email. Repeat with a denial to verify the denial flow and email.
4. **Mapping Viewer**: From the Approval Queue, click "View Component Mappings". Verify mappings load in the grid, filters work, CSV export downloads, and manual mapping create/update/delete operations succeed.

---

## Phase 6: Testing

### Smoke Test Sequence (5-Minute Check)

Before running the full test suite, perform this quick end-to-end validation:

1. **DataHub** -- Query the ComponentMapping model for any existing records. Expect either an empty result set or known seed data. If the query fails, stop and resolve Phase 1 issues before proceeding.
2. **Flow Service** -- POST a `getDevAccounts` request to `https://{your-cloud-base-url}/fs/PromotionService`. Expect a JSON response with `success: true` and a list of accessible dev accounts (or an empty list if no DevAccountAccess records are seeded).
3. **Flow Dashboard** -- Open the Promotion Dashboard URL in a browser. Verify the page loads, the Package Browser (Page 1) renders, and the dev account dropdown populates.

If all three checks pass, proceed to the full test suite below.

---

### Test 1 -- DataHub CRUD

Validate that the DataHub models accept records, enforce match rules, and support upsert behavior.

#### 1a. Create a Test Record

POST a test ComponentMapping record using the template at `datahub/api-requests/create-golden-record-test.xml`:

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/create" \
  -H "Content-Type: application/xml" \
  -d @datahub/api-requests/create-golden-record-test.xml
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = Get-Content -Raw datahub/api-requests/create-golden-record-test.xml
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/create" `
  -Method POST -Headers $headers -Body $body
```

#### 1b. Query the Test Record

Query the record back using the template at `datahub/api-requests/query-golden-record-test.xml`:

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d @datahub/api-requests/query-golden-record-test.xml
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = Get-Content -Raw datahub/api-requests/query-golden-record-test.xml
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body $body
```

**Expected output** (truncated):

```xml
<RecordQueryResponse totalCount="1">
  <record>
    <field name="devComponentId">test-dev-comp-001</field>
    <field name="devAccountId">TEST_DEV_ACCT</field>
    <field name="prodComponentId">test-prod-comp-001</field>
    <field name="componentName">Test Connection</field>
    <field name="componentType">connection</field>
    <field name="prodLatestVersion">1</field>
    ...
  </record>
</RecordQueryResponse>
```

**Pass criteria:** `totalCount="1"`, `devComponentId` and `devAccountId` match the values from the create request.

#### 1c. Upsert Test (No Duplicate)

POST the same `create-golden-record-test.xml` a second time. Then query again using step 1b.

**Pass criteria:** `totalCount` is still `1`. The record ID is unchanged. The match rule on `devComponentId` + `devAccountId` prevented a duplicate.

#### 1d. Clean Up

Delete the test record via the DataHub UI or API to avoid polluting production data.

---

### Test 2 -- Single Component Promotion

Run the Flow Dashboard and promote a simple package with no dependencies (a single connection or profile).

1. Open the Promotion Dashboard.
2. Select a dev account from the dropdown (Page 1).
3. Select a package containing a single component (no child references).
4. Proceed to Promotion Review (Page 2) and click Promote.
5. Wait for the Promotion Status (Page 3) to show COMPLETED.

#### Verification: Component Exists in Primary Account

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{prodComponentId}"
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    Accept         = "application/xml"
}
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{prodComponentId}" `
  -Method GET -Headers $headers
```

**Expected output** (truncated):

```xml
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId="{prodComponentId}" version="1"
    name="{componentName}" type="{componentType}"
    folderFullPath="/Promoted{devFolderFullPath}">
  <bns:object>...</bns:object>
</bns:Component>
```

**Pass criteria:** Component exists, `version="1"`, `folderFullPath` starts with `/Promoted/`.

#### Verification: DataHub Mapping Created

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="10">
  <view><fieldId>devComponentId</fieldId><fieldId>prodComponentId</fieldId><fieldId>prodLatestVersion</fieldId></view>
  <filter op="AND">
    <fieldValue><fieldId>devComponentId</fieldId><operator>EQUALS</operator><value>{devComponentId}</value></fieldValue>
    <fieldValue><fieldId>devAccountId</fieldId><operator>EQUALS</operator><value>{devAccountId}</value></fieldValue>
  </filter>
</RecordQueryRequest>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = @"
<RecordQueryRequest limit="10">
  <view><fieldId>devComponentId</fieldId><fieldId>prodComponentId</fieldId><fieldId>prodLatestVersion</fieldId></view>
  <filter op="AND">
    <fieldValue><fieldId>devComponentId</fieldId><operator>EQUALS</operator><value>{devComponentId}</value></fieldValue>
    <fieldValue><fieldId>devAccountId</fieldId><operator>EQUALS</operator><value>{devAccountId}</value></fieldValue>
  </filter>
</RecordQueryRequest>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body $body
```

**Pass criteria:** `totalCount="1"`, `prodComponentId` is populated, `prodLatestVersion` is `1`.

**Verify:** PromotionLog shows `status=COMPLETED`, `componentsCreated=1`, `componentsFailed=0`.

---

### Test 3 -- Re-Promote (Version Increment)

Promote the same package from Test 2 a second time.

1. Repeat the flow steps from Test 2 with the same package.
2. On Page 2 (Promotion Review), the dependency tree should show the component as UPDATE (not NEW).

#### Verification: Version Incremented

Run the same GET Component command from Test 2.

**Pass criteria:** Same `componentId`, `version` is now greater than `1` (API auto-increments).

#### Verification: DataHub Mapping Updated

Run the same DataHub query from Test 2.

**Pass criteria:**
- Same record ID (no duplicate created)
- `prodLatestVersion` incremented (now `2` or higher)
- `lastPromotedAt` updated to a more recent timestamp than Test 2

---

### Test 4 -- Full Dependency Tree

Select a package containing a process with dependencies (process references connections, profiles, maps, and/or sub-processes).

1. Open the Promotion Dashboard and select the complex package.
2. On Page 2 (Promotion Review), verify the dependency tree shows all components with correct types.
3. Click Promote and wait for COMPLETED status.

#### Verification: All Components Promoted

Query ComponentMapping for all components in the tree:

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="200">
  <view>
    <fieldId>devComponentId</fieldId><fieldId>componentName</fieldId>
    <fieldId>componentType</fieldId><fieldId>prodComponentId</fieldId>
  </view>
  <filter op="AND">
    <fieldValue><fieldId>devAccountId</fieldId><operator>EQUALS</operator><value>{devAccountId}</value></fieldValue>
  </filter>
</RecordQueryRequest>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = @"
<RecordQueryRequest limit="200">
  <view>
    <fieldId>devComponentId</fieldId><fieldId>componentName</fieldId>
    <fieldId>componentType</fieldId><fieldId>prodComponentId</fieldId>
  </view>
  <filter op="AND">
    <fieldValue><fieldId>devAccountId</fieldId><operator>EQUALS</operator><value>{devAccountId}</value></fieldValue>
  </filter>
</RecordQueryRequest>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body $body
```

**Pass criteria:**
- `totalCount` matches the `totalComponents` value from the promotion response
- Every component in the tree has a `prodComponentId` populated
- Bottom-up processing order was respected: profiles (priority 1) created before connections (priority 2) before operations (priority 3) before maps (priority 4) before sub-processes (priority 5) before root process (priority 6). Confirm by checking `lastPromotedAt` timestamps or the PromotionLog `resultDetail` field.

---

### Test 5 -- Approval Workflow

After a successful promotion (Test 2 or Test 4), submit for deployment.

1. On Page 4 (Deployment Submission), fill in the package version and deployment notes.
2. Click Submit -- the flow transitions to the Admin swimlane and sends an email notification.
3. Log in as an admin user (member of "Boomi Admins" SSO group).
4. Open Page 5 (Approval Queue), locate the pending request, and click Approve.
5. Verify the deployment completes.

#### Verification: Integration Pack Exists

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/json" \
  "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/IntegrationPack/{integrationPackId}"
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization = "Basic $cred"
    Accept        = "application/json"
}
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/IntegrationPack/{integrationPackId}" `
  -Method GET -Headers $headers
```

**Pass criteria:** Integration Pack exists, contains the promoted component, deployment status shows success.

---

### Test 6 -- Error Recovery

Simulate a failure by promoting a component that will fail mid-tree (for example, temporarily revoke API access to a referenced component, or corrupt a component reference).

1. Trigger the promotion and wait for the FAILED/PARTIAL status on Page 3.

#### Verification: PromotionLog Shows Failure

Query the PromotionLog model:

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="10">
  <view>
    <fieldId>promotionId</fieldId><fieldId>status</fieldId>
    <fieldId>componentsFailed</fieldId><fieldId>errorMessage</fieldId>
  </view>
  <filter op="AND">
    <fieldValue><fieldId>promotionId</fieldId><operator>EQUALS</operator><value>{promotionId}</value></fieldValue>
  </filter>
</RecordQueryRequest>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = @"
<RecordQueryRequest limit="10">
  <view>
    <fieldId>promotionId</fieldId><fieldId>status</fieldId>
    <fieldId>componentsFailed</fieldId><fieldId>errorMessage</fieldId>
  </view>
  <filter op="AND">
    <fieldValue><fieldId>promotionId</fieldId><operator>EQUALS</operator><value>{promotionId}</value></fieldValue>
  </filter>
</RecordQueryRequest>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body $body
```

**Pass criteria:**
- `status` is `FAILED`
- `componentsFailed` is `>= 1`
- `errorMessage` describes the failure
- The failed component's dependents are marked SKIPPED in the `resultDetail` field

2. Fix the underlying issue (restore API access, correct the reference).
3. Re-run the same promotion.

**Pass criteria for re-run:**
- Previously promoted components show as UPDATE (not duplicated)
- Previously SKIPPED components now succeed (become CREATE or UPDATE)
- PromotionLog for the new run shows `status=COMPLETED`

---

### Test 7 -- Browser Resilience

1. Start a promotion via the Flow Dashboard (click Promote on Page 2).
2. While the promotion is executing (before the status page loads), close the browser tab.
3. Reopen the same Flow Dashboard URL.

**Pass criteria:**
- The Flow state is restored from IndexedDB -- the user returns to Page 3 (Promotion Status) or the current step in the flow
- The promotion completed successfully in the background (the Integration process continues regardless of browser state)
- Verify the PromotionLog shows `status=COMPLETED` using the query from Test 6

---

## Troubleshooting

### Phase 1 Issues

**"Model not visible after creation"**
The model must be Published AND Deployed to the repository. Creating and saving the model is not sufficient. Navigate to DataHub, open the model, click Publish, then click Deploy and select the target repository.

**"Match rule not working (duplicates created)"**
Verify the compound match rule uses the correct fields. ComponentMapping must match on `devComponentId` AND `devAccountId` (both fields). DevAccountAccess must match on `ssoGroupId` AND `devAccountId`. PromotionLog must match on `promotionId`. If the match rule is missing a field, records that should upsert will instead create duplicates. Delete duplicates manually and re-publish the corrected model.

**"Source name rejected when posting records"**
The source must be registered on the model before posting records. ComponentMapping and PromotionLog use source `PROMOTION_ENGINE`. DevAccountAccess uses source `ADMIN_CONFIG`. Add the source on the model's Sources tab, then Publish and Deploy again.

**Diagnostic -- check model state:**

```bash
# Linux/macOS -- query to verify model accepts records
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="1"><view><fieldId>devComponentId</fieldId></view></RecordQueryRequest>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; "Content-Type" = "application/xml" }
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body '<RecordQueryRequest limit="1"><view><fieldId>devComponentId</fieldId></view></RecordQueryRequest>'
```

If this returns a valid response (even with `totalCount="0"`), the model is deployed correctly. If it returns an error, the model is not deployed.

---

### Phase 2 Issues

**"Test connection fails for HTTP Client"**
Verify the URL is exactly `https://api.boomi.com` with no trailing path segments. The path is set on each operation, not the connection. Verify the username follows the format `BOOMI_TOKEN.user@company.com` and the API token is current (tokens can expire or be revoked in Settings, Account Information, Platform API Tokens).

**"overrideAccount not authorized"**
Three conditions must be met: (1) Partner API must be enabled on the primary account (Settings, Account Information, Partner API section). (2) The API token user must have Partner-level access or higher. (3) The dev account must be a sub-account of the primary account. If any condition is missing, the API returns HTTP 403.

**"HTTP 404 on operation execution"**
Verify the URL pattern uses `{1}` and `{2}` placeholder syntax correctly. `{1}` maps to `primaryAccountId` DPP. `{2}` maps to the component-specific ID DPP (e.g., `currentComponentId` or `prodComponentId`). Verify the DPP names match EXACTLY (case-sensitive) in the operation's Parameters tab. Also verify the operation names match the convention: `PROMO - HTTP Op - GET Component`, `PROMO - HTTP Op - POST Component Create`, etc.

**"HTTP 429 Too Many Requests"**
The Partner API enforces approximately 10 requests per second. Add a 120ms gap between consecutive API calls (yields approximately 8 requests per second with safety margin). Implement retry logic: up to 3 retries with exponential backoff (1 second, 2 seconds, 4 seconds). If 429 errors persist, reduce the call rate further.

**Diagnostic -- test an operation with curl:**

```bash
# Linux/macOS -- test GET Component with overrideAccount
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}"
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; Accept = "application/xml" }
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}" `
  -Method GET -Headers $headers
```

---

### Phase 3 Issues

**"Groovy script error: property not found"**
Verify the DPP name matches EXACTLY (case-sensitive) in both the Set Properties shape and the Groovy script. The canonical names are:
- `visitedComponentIds` (not `visitedIds` or `visited_component_ids`)
- `componentQueue` (not `queue` or `component_queue`)
- `componentMappingCache` (not `mappingCache` or `component_mapping_cache`)
- `alreadyVisited` (not `already_visited`)
- `currentComponentId` (not `current_component_id`)
- `rootComponentId` (not `root_component_id`)
- `configStripped` (not `config_stripped`)
- `strippedElements` (not `stripped_elements`)
- `referencesRewritten` (not `references_rewritten`)
- `prodComponentId` (not `prod_component_id`)
- `promotionId` (not `promotion_id`)

**"Component references not rewritten"**
The `rewrite-references.groovy` script reads the `componentMappingCache` DPP and replaces each dev component ID with its corresponding prod component ID in the XML. If references are not being rewritten: (1) Verify `componentMappingCache` is being populated -- add a temporary logger.info statement to print its contents. (2) Verify that `sort-by-dependency.groovy` places dependencies before dependents in the processing order (profiles first, root process last). If a parent is processed before its dependency, the cache will not yet contain the mapping.

**"Infinite loop in dependency resolution"**
The `build-visited-set.groovy` script has cycle detection via the `visitedComponentIds` set. If a component has already been visited, the `alreadyVisited` DPP is set to `"true"` and the component is skipped. Check that the `visitedCount` DPP is growing with each iteration. If `visitedCount` stalls and `queueCount` does not decrease, there may be a self-referencing component. Inspect the `componentQueue` DPP to identify the repeating ID.

**"strip-env-config removes too much or too little"**
The `strip-env-config.groovy` script strips these elements by clearing their text content: `password`, `host`, `url`, `port`, `EncryptedValue`. Review the `strippedElements` DPP output after execution to see which elements were stripped. If additional elements need stripping, add them to the script. If an element is being stripped incorrectly, verify the element name is not colliding with a legitimate configuration element.

**Debugging tip:** Enable process logging in Boomi (Manage, Process Reporting). The Groovy scripts use `logger.info()` to write diagnostic messages. Check these logs to trace DPP values and processing steps.

**Debugging tip:** Add temporary Set Properties shapes between process steps to write DPP values to document properties. This makes them visible in Process Reporting without modifying Groovy code.

---

### Phase 4 Issues

**"No listeners found after deployment"**
Three conditions must be met: (1) The atom must be running (check Runtime Management, Atom Status). (2) The `PROMO - Flow Service` must be deployed as a Packaged Component to the atom. (3) The atom must be a public Boomi cloud atom (not a private cloud or local atom). Private atoms cannot receive inbound Flow Service requests.

**"Operation not found in Flow Service"**
Each FSS Operation must be linked in the Message Actions tab of the `PROMO - Flow Service` component. Verify all 7 operations are listed: `PROMO - FSS Op - GetDevAccounts`, `PROMO - FSS Op - ListDevPackages`, `PROMO - FSS Op - ResolveDependencies`, `PROMO - FSS Op - ExecutePromotion`, `PROMO - FSS Op - PackageAndDeploy`, `PROMO - FSS Op - QueryStatus`, `PROMO - FSS Op - ManageMappings`. If an operation is missing from the list, add it, re-save, re-package, and re-deploy.

**"Configuration value not set"**
The `primaryAccountId` configuration value must be set after deployment via component configuration (Manage, Deployed Components, select the Flow Service, Configuration tab). This value is NOT set at build time -- it is set per deployment. If this value is empty, all HTTP operations using `{1}` in their URL will fail.

**Diagnostic:** Check Runtime Management, Listeners tab. All 7 processes should appear as active listeners. If fewer than 7 appear, verify each FSS Operation is correctly linked and the deployment is current.

---

### Phase 5 Issues

**"Retrieve Connector Configuration Data fails"**
Verify all of the following: (1) The atom is running. (2) The `PROMO - Flow Service` is deployed to the atom. (3) The Path to Service is exactly `/fs/PromotionService` (case-sensitive, no trailing slash). (4) Basic Auth credentials match the Shared Web Server User Management settings on the atom. If any of these are wrong, the retrieval will fail silently or return an error.

**"Flow Types not generated (fewer than 14)"**
After a successful "Retrieve Connector Configuration Data," Flow should auto-generate 14 types (2 per message action: request and response). If fewer than 14 appear, the Flow Service may have fewer than 7 message actions linked. Fix the Flow Service (Phase 4), re-deploy, then re-retrieve connector configuration data in Flow.

**"Message step returns empty response"**
Check the Flow value bindings on the Message step. Both input values (request type) and output values (response type) must be bound. The connector action name must match the message action name exactly (e.g., `executePromotion`, not `ExecutePromotion`). Verify the Flow Value type matches the auto-generated type name (e.g., `executePromotion REQUEST - executePromotionRequest`).

**"Swimlane transition fails (unauthorized)"**
Verify SSO groups are configured correctly in Azure AD/Entra. The Developer swimlane requires membership in "Boomi Developers." The Admin swimlane requires membership in "Boomi Admins." If the user does not belong to the correct group, the swimlane transition is blocked. Check the Identity connector configuration in Flow.

**"Email notification not sent at deployment submission"**
Check the email step configuration on the transition from Page 4 to Page 5. Verify the distribution list or recipient address is correct. Verify the Flow environment has email sending enabled. Test with a direct email address before using a distribution list.

**Debugging tip:** Use the Flow canvas Debug mode (Run, Debug) to trace step execution. Each step shows its inputs, outputs, and any errors. This is the fastest way to identify binding mismatches or connector failures.

---

### Phase 6 Issues

**"Promotion creates duplicate components instead of updating"**
The DataHub match rule on ComponentMapping is not functioning correctly, or the `devComponentId` and `devAccountId` fields are not populated in the promotion request. Verify the match rule is an exact compound match on both fields. Verify that Process C reads from the DataHub cache before creating -- if it skips the DataHub lookup, it will always create new components.

**"Version not incrementing on re-promotion"**
Verify Process C uses POST Component Update (`PROMO - HTTP Op - POST Component Update`) and not POST Component Create for existing components. The update URL includes the `{prodComponentId}` in the path: `/partner/api/rest/v1/{1}/Component/{2}`. Verify `prodComponentId` is correctly read from the `componentMappingCache` DPP or DataHub query result.

**"State not restored after browser close"**
Flow uses IndexedDB for client-side state caching. Verify the browser allows IndexedDB (some privacy modes disable it). The Integration process continues executing regardless of browser state -- the Flow Service is asynchronous. Reopening the same Flow URL should restore state. If it does not, check that the Flow is using the correct state ID in the URL hash.

---

## Appendix A: Naming Conventions

### Component Naming Patterns

| Component Type | Pattern | Example |
|---------------|---------|---------|
| DataHub Model | `{ModelName}` | `ComponentMapping` |
| HTTP Client Connection | `PROMO - {Description} Connection` | `PROMO - Partner API Connection` |
| DataHub Connection | `PROMO - DataHub Connection` | `PROMO - DataHub Connection` |
| HTTP Client Operation | `PROMO - HTTP Op - {METHOD} {Resource}` | `PROMO - HTTP Op - GET Component` |
| DataHub Operation | `PROMO - DH Op - {Action} {Model}` | `PROMO - DH Op - Query ComponentMapping` |
| JSON Profile | `PROMO - Profile - {ActionName}{Request\|Response}` | `PROMO - Profile - ExecutePromotionRequest` |
| Integration Process | `PROMO - {Description}` | `PROMO - Execute Promotion` |
| FSS Operation | `PROMO - FSS Op - {ActionName}` | `PROMO - FSS Op - ExecutePromotion` |
| Flow Service | `PROMO - Flow Service` | `PROMO - Flow Service` |
| Flow Connector | `Promotion Service Connector` | `Promotion Service Connector` |
| Flow Application | `Promotion Dashboard` | `Promotion Dashboard` |

### Folder Structure for Promoted Components

```
/Promoted/{DevAccountName}/{ProcessName}/
```

All components promoted by the system are placed in this folder hierarchy. Boomi auto-creates folders that do not exist.

### Complete 51-Component Inventory Checklist

```
Phase 1 -- DataHub Models (3):
[ ] 1. ComponentMapping
[ ] 2. DevAccountAccess
[ ] 3. PromotionLog

Phase 2 -- Connections (2):
[ ] 4. PROMO - Partner API Connection
[ ] 5. PROMO - DataHub Connection

Phase 2 -- HTTP Client Operations (9):
[ ] 6.  PROMO - HTTP Op - GET Component
[ ] 7.  PROMO - HTTP Op - POST Component Create
[ ] 8.  PROMO - HTTP Op - POST Component Update
[ ] 9.  PROMO - HTTP Op - GET ComponentReference
[ ] 10. PROMO - HTTP Op - GET ComponentMetadata
[ ] 11. PROMO - HTTP Op - QUERY PackagedComponent
[ ] 12. PROMO - HTTP Op - POST PackagedComponent
[ ] 13. PROMO - HTTP Op - POST DeployedPackage
[ ] 14. PROMO - HTTP Op - POST IntegrationPack

Phase 2 -- DataHub Operations (6):
[ ] 15. PROMO - DH Op - Query ComponentMapping
[ ] 16. PROMO - DH Op - Update ComponentMapping
[ ] 17. PROMO - DH Op - Query DevAccountAccess
[ ] 18. PROMO - DH Op - Update DevAccountAccess
[ ] 19. PROMO - DH Op - Query PromotionLog
[ ] 20. PROMO - DH Op - Update PromotionLog

Phase 3 -- JSON Profiles (14):
[ ] 21. PROMO - Profile - GetDevAccountsRequest
[ ] 22. PROMO - Profile - GetDevAccountsResponse
[ ] 23. PROMO - Profile - ListDevPackagesRequest
[ ] 24. PROMO - Profile - ListDevPackagesResponse
[ ] 25. PROMO - Profile - ResolveDependenciesRequest
[ ] 26. PROMO - Profile - ResolveDependenciesResponse
[ ] 27. PROMO - Profile - ExecutePromotionRequest
[ ] 28. PROMO - Profile - ExecutePromotionResponse
[ ] 29. PROMO - Profile - PackageAndDeployRequest
[ ] 30. PROMO - Profile - PackageAndDeployResponse
[ ] 31. PROMO - Profile - QueryStatusRequest
[ ] 32. PROMO - Profile - QueryStatusResponse
[ ] 33. PROMO - Profile - ManageMappingsRequest
[ ] 34. PROMO - Profile - ManageMappingsResponse

Phase 3 -- Integration Processes (7):
[ ] 35. PROMO - Get Dev Accounts
[ ] 36. PROMO - List Dev Packages
[ ] 37. PROMO - Resolve Dependencies
[ ] 38. PROMO - Execute Promotion
[ ] 39. PROMO - Package and Deploy
[ ] 40. PROMO - Query Status
[ ] 41. PROMO - Mapping CRUD

Phase 4 -- Flow Service Components (8):
[ ] 42. PROMO - FSS Op - GetDevAccounts
[ ] 43. PROMO - FSS Op - ListDevPackages
[ ] 44. PROMO - FSS Op - ResolveDependencies
[ ] 45. PROMO - FSS Op - ExecutePromotion
[ ] 46. PROMO - FSS Op - PackageAndDeploy
[ ] 47. PROMO - FSS Op - QueryStatus
[ ] 48. PROMO - FSS Op - ManageMappings
[ ] 49. PROMO - Flow Service

Phase 5 -- Flow Dashboard (2):
[ ] 50. Promotion Service Connector
[ ] 51. Promotion Dashboard
```

---

## Appendix B: Dynamic Process Properties (DPP) Catalog

### Global DPPs

These properties are used across multiple integration processes.

| DPP Name | Type | Process(es) | Read/Write | Initial Value | Description |
|----------|------|-------------|------------|---------------|-------------|
| `primaryAccountId` | String | All (A0, A, B, C, D, E, F) | Read | (set via Flow Service component configuration) | Primary Boomi account ID used in all Partner API URLs |
| `devAccountId` | String | A0, A, B, C, D | Read | (from request JSON) | Dev sub-account ID; used for `overrideAccount` parameter |
| `currentComponentId` | String | B, C | Read/Write | (from loop iteration) | Component ID being processed in the current loop iteration |
| `rootComponentId` | String | B, C | Read | (from request JSON) | Root process component ID that initiated the dependency traversal |

### Process B DPPs (Resolve Dependencies)

| DPP Name | Type | Read/Write | Initial Value | Description |
|----------|------|------------|---------------|-------------|
| `visitedComponentIds` | String (JSON array) | Read/Write | `[]` | JSON array of component IDs already visited during BFS traversal |
| `componentQueue` | String (JSON array) | Read/Write | `[]` | BFS queue of component IDs remaining to visit |
| `alreadyVisited` | String | Write | `"false"` | Flag set by `build-visited-set.groovy`; `"true"` if current component was already in the visited set |
| `visitedCount` | String | Write | `"0"` | Count of components visited so far; used for progress tracking and loop diagnostics |
| `queueCount` | String | Write | `"0"` | Count of components remaining in the queue; reaches `"0"` when traversal is complete |

### Process C DPPs (Execute Promotion)

| DPP Name | Type | Read/Write | Initial Value | Description |
|----------|------|------------|---------------|-------------|
| `componentMappingCache` | String (JSON object) | Read/Write | `{}` | In-memory dev-to-prod ID mapping cache; keys are dev component IDs, values are prod component IDs |
| `configStripped` | String | Write | `"false"` | Flag set by `strip-env-config.groovy`; `"true"` if any environment elements were stripped |
| `strippedElements` | String | Write | `""` | Comma-separated list of element names stripped (e.g., `password,host,EncryptedValue`) |
| `referencesRewritten` | String | Write | `"0"` | Count of component references rewritten by `rewrite-references.groovy` |
| `prodComponentId` | String | Read/Write | (from DataHub query) | Prod component ID for the current component; empty if component is new |
| `promotionId` | String | Read/Write | (UUID generated at start) | Unique ID for this promotion run; written to PromotionLog |
| `connectionMappingCache` | String (JSON object) | Read/Write | `{}` | Connection mappings batch-queried from DataHub; keys are dev connection IDs, values are prod connection IDs |
| `missingConnectionMappings` | String (JSON array) | Write | `[]` | JSON array of objects for connections without mappings; each has devComponentId, name, type, devAccountId |
| `missingConnectionCount` | String | Write | `"0"` | Count of connections without mappings |
| `connectionMappingsValid` | String | Write | `"true"` | `"true"` if all connections have mappings, `"false"` otherwise |
| `currentFolderFullPath` | String | Read/Write | (from component) | Dev account folder path for current component; used to construct `/Promoted{currentFolderFullPath}` target path |

### Groovy Script to DPP Cross-Reference

| Script | File | Process | DPPs Read | DPPs Written |
|--------|------|---------|-----------|--------------|
| Build Visited Set | `integration/scripts/build-visited-set.groovy` | B (Resolve Dependencies) | `visitedComponentIds`, `componentQueue`, `currentComponentId` | `visitedComponentIds`, `componentQueue`, `alreadyVisited`, `visitedCount`, `queueCount` |
| Sort by Dependency | `integration/scripts/sort-by-dependency.groovy` | C (Execute Promotion) | `rootComponentId` | (none -- sorts document in-place) |
| Strip Env Config | `integration/scripts/strip-env-config.groovy` | C (Execute Promotion) | (none -- reads XML from document stream) | `configStripped`, `strippedElements` |
| Rewrite References | `integration/scripts/rewrite-references.groovy` | C (Execute Promotion) | `componentMappingCache` | `referencesRewritten` |
| Validate Connection Mappings | `integration/scripts/validate-connection-mappings.groovy` | C (Execute Promotion) | `connectionMappingCache`, `componentMappingCache`, `devAccountId` | `missingConnectionMappings`, `missingConnectionCount`, `connectionMappingsValid`, `componentMappingCache` |

### Type Priority Order (sort-by-dependency.groovy)

Components are sorted by type for bottom-up promotion. Lower priority number means promoted first.

| Priority | Type | Notes |
|----------|------|-------|
| 1 | `profile` | Promoted first -- no dependencies on other promoted components |
| 2 | `connection` | May reference profiles |
| 3 | `operation` | References connections and profiles |
| 4 | `map` | References profiles and operations |
| 5 | `process` (sub-process) | References all of the above |
| 6 | `process` (root) | Promoted last -- depends on everything; identified by matching `rootComponentId` |

---

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
```

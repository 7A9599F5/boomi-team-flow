## Phase 2: Integration Connections & Operations

This phase creates the connection and operation components that all integration processes depend on. There are 2 connections and 26 operations total (20 HTTP Client + 6 DataHub).

### Step 2.1 -- Create HTTP Client Connection (Partner API)

#### Via API

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Partner API Connection" type="connector-settings" subType="http" folderFullPath="/Promoted/Connections">
  <bns:object>
    <bns:url>https://api.boomi.com</bns:url>
    <bns:authType>BASIC</bns:authType>
    <bns:user>BOOMI_TOKEN.user@company.com</bns:user>
    <bns:password>your-api-token</bns:password>
    <bns:connectionTimeout>120000</bns:connectionTimeout>
    <bns:readTimeout>120000</bns:readTimeout>
  </bns:object>
</bns:Component>'
```

```powershell
$cred = "BOOMI_TOKEN.user@company.com:your-api-token"
$base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($cred))
$headers = @{
    "Authorization"  = "Basic $base64"
    "Content-Type"   = "application/xml"
    "Accept"         = "application/xml"
}
$body = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Partner API Connection" type="connector-settings" subType="http" folderFullPath="/Promoted/Connections">
  <bns:object>
    <bns:url>https://api.boomi.com</bns:url>
    <bns:authType>BASIC</bns:authType>
    <bns:user>BOOMI_TOKEN.user@company.com</bns:user>
    <bns:password>your-api-token</bns:password>
    <bns:connectionTimeout>120000</bns:connectionTimeout>
    <bns:readTimeout>120000</bns:readTimeout>
  </bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" `
    -Method POST -Headers $headers -Body $body
```

> **Note:** Password is supplied in plaintext and encrypted on save by the Boomi platform. Connection testing has no API equivalent -- verify connectivity with a direct curl call to `https://api.boomi.com/partner/api/rest/v1/{accountId}/Account/{accountId}` using the same credentials instead.

**Verify:** Capture the `componentId` from the response for use in operation creation.

#### Via UI (Manual Fallback)

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

### Understanding HTTP Client Replacement Variables

Before creating operations, it's important to understand how Boomi HTTP Client operations construct URLs at runtime.

#### How URL Path Construction Works

HTTP Client operations store URL paths as **named path elements** — a sequence of static segments and replacement variables. In the Boomi UI, you see a simple URL like `/partner/api/rest/v1/{1}/Component/{2}`, but internally Boomi stores this as:

```xml
<pathElements>
    <element key="2000000" name="/partner/api/rest/v1/"/>
    <element isVariable="true" key="2000001" name="primaryAccountId"/>
    <element key="2000002" name="/Component/"/>
    <element isVariable="true" key="2000003" name="currentComponentId"/>
</pathElements>
```

Each replacement variable (`{1}`, `{2}`, etc.) maps to a **named variable** whose value is supplied at runtime via **Dynamic Process Properties (DPPs)**. The variable name in the operation matches the DPP name exactly — so DPP `primaryAccountId` fills the `primaryAccountId` path element.

#### The POST/PUT Parameters Tab Bug

> **Known Issue:** When using POST or PUT operations, supplying URL parameters via the connector shape's **Parameters tab** sends a **blank request payload**. The payload is silently dropped.

**Workaround for POST/PUT operations:**
1. Use a **Set Properties** shape *before* the HTTP Client connector shape
2. Set **Dynamic Document Properties** (DDPs) with the same names as the operation's replacement variables
3. The connector reads these DDPs and substitutes them into the URL path

**Example** (for POST Component Create with URL `/{1}/Component~{2}`):
```
Set Properties shape:
  - DDP "primaryAccountId" = [value from process context]
  - DDP "branchId" = [value from process context]
    ↓
HTTP Client connector shape (POST Component Create)
  → URL resolved: /partner/api/rest/v1/{accountId}/Component~{branchId}
```

**GET and DELETE operations** can safely use either the Parameters tab or Set Properties + DDPs. We recommend using Set Properties + DDPs consistently across all operations for uniformity.

### Step 2.2 -- Create HTTP Client Operations

Create 20 HTTP Client operations. Each uses the `PROMO - Partner API Connection` from Step 2.1.

#### Quick Reference Table

| # | Component Name | Method | Request URL | Content-Type | Template File |
|---|---------------|--------|-------------|-------------|---------------|
| 1 | PROMO - HTTP Op - GET Component | GET | `/partner/api/rest/v1/{1}/Component/{2}` | `application/xml` | `get-component.xml` |
| 2 | PROMO - HTTP Op - POST Component Create | POST | `/partner/api/rest/v1/{1}/Component~{2}` | `application/xml` | `create-component.xml` |
| 3 | PROMO - HTTP Op - POST Component Update | POST | `/partner/api/rest/v1/{1}/Component/{2}~{3}` | `application/xml` | `update-component.xml` |
| 4 | PROMO - HTTP Op - GET ComponentReference | GET | `/partner/api/rest/v1/{1}/ComponentReference/{2}` | `application/xml` | `query-component-reference.xml` |
| 5 | PROMO - HTTP Op - GET ComponentMetadata | GET | `/partner/api/rest/v1/{1}/ComponentMetadata/{2}` | `application/xml` | `query-component-metadata.xml` |
| 6 | PROMO - HTTP Op - QUERY PackagedComponent | POST | `/partner/api/rest/v1/{1}/PackagedComponent/query` | `application/xml` | `query-packaged-components.xml` |
| 7 | PROMO - HTTP Op - POST PackagedComponent | POST | `/partner/api/rest/v1/{1}/PackagedComponent` | `application/json` | `create-packaged-component.json` |
| 8 | PROMO - HTTP Op - POST DeployedPackage | POST | `/partner/api/rest/v1/{1}/DeployedPackage` | `application/json` | `create-deployed-package.json` |
| 9 | PROMO - HTTP Op - POST IntegrationPack | POST | `/partner/api/rest/v1/{1}/IntegrationPack` | `application/json` | `create-integration-pack.json` |
| 10 | PROMO - HTTP Op - POST Branch | POST | `/partner/api/rest/v1/{1}/Branch` | `application/json` | `create-branch.json` |
| 11 | PROMO - HTTP Op - QUERY Branch | POST | `/partner/api/rest/v1/{1}/Branch/query` | `application/json` | `query-branch.json` |
| 12 | PROMO - HTTP Op - POST MergeRequest | POST | `/partner/api/rest/v1/{1}/MergeRequest` | `application/json` | `create-merge-request.json` |
| 13 | PROMO - HTTP Op - POST MergeRequest Execute | POST | `/partner/api/rest/v1/{1}/MergeRequest/execute/{2}` | `application/json` | `execute-merge-request.json` |
| 14 | PROMO - HTTP Op - GET Branch | GET | `/partner/api/rest/v1/{1}/Branch/{2}` | `application/json` | `get-branch.json` |
| 15 | PROMO - HTTP Op - DELETE Branch | DELETE | `/partner/api/rest/v1/{1}/Branch/{2}` | `application/json` | `delete-branch.json` |
| 16 | PROMO - HTTP Op - QUERY IntegrationPack | POST | `/partner/api/rest/v1/{1}/IntegrationPack/query` | `application/xml` | `query-integration-packs.xml` |
| 17 | PROMO - HTTP Op - POST Add To IntegrationPack | POST | `/partner/api/rest/v1/{1}/IntegrationPack/{2}/PackagedComponent/{3}` | `application/json` | `add-to-integration-pack.json` |
| 18 | PROMO - HTTP Op - POST ReleaseIntegrationPack | POST | `/partner/api/rest/v1/{1}/ReleaseIntegrationPack` | `application/json` | `release-integration-pack.json` |
| 19 | PROMO - HTTP Op - GET MergeRequest | GET | `/partner/api/rest/v1/{1}/MergeRequest/{2}` | `application/json` | `get-merge-request.json` |
| 20 | PROMO - HTTP Op - GET ReleaseIntegrationPackStatus | GET | `/partner/api/rest/v1/{1}/ReleaseIntegrationPackStatus/{2}` | `application/json` | `get-release-integration-pack-status.json` |

> Operations 1-6 use `application/xml` for both Content-Type and Accept headers (Platform API XML endpoints). Operations 7-9 use `application/json` for both headers (JSON-based endpoints). Operation 16 uses `application/xml` (query endpoint). Operations 17-20 use `application/json`.

#### Step 2.2.1 -- PROMO - HTTP Op - GET Component

This operation retrieves the full component XML (including configuration) from a dev sub-account.

##### Via API (API-First Discovery)

The internal XML structure for HTTP Client operations is complex (`<Operation>` → `<Http{Method}Action>` → `<pathElements>`) and cannot be reliably hand-authored. **Use the API-First Discovery workflow:**

1. Create this operation manually in the Boomi UI (see "Via UI" below).
2. Export its XML via `GET /Component/{operationComponentId}` (see [API-First Discovery Workflow](#api-first-discovery-workflow) below).
3. Use the exported XML as the template for batch-creating the remaining 27 operations — the setup script automates this in Steps 2.2-2.3.

> **Why not hand-author?** HTTP Client operation XML uses named `<pathElements>` with auto-generated keys, connector-specific action elements (`<HttpGetAction>`, `<HttpPostAction>`), and multiple configuration attributes. Fabricating this XML risks silent misconfiguration. The API-First Discovery pattern captures the exact validated structure.

**Verify:** Response returns HTTP 200 with the new component ID.

##### Via UI (Manual Fallback)

1. Navigate to **Build --> New Component --> Connector --> Operation**.
2. Select connector type: **HTTP Client**. Name: `PROMO - HTTP Op - GET Component`.
3. Connection: select `PROMO - Partner API Connection`.
4. Configure the **Operation** tab:

| Setting | Value |
|---------|-------|
| **Action** | Send |
| **HTTP Method** | GET |
| **Resource Path** | `/partner/api/rest/v1/{1}/Component/{2}` |

5. Configure the **Parameters** tab (replacement variables):
   - Click **Add** for each `{N}` placeholder in the Resource Path
   - For `{1}`: Name = `primaryAccountId`, Type = `Process Property`, Process Property = `primaryAccountId`
   - For `{2}`: Name = `currentComponentId`, Type = `Process Property`, Process Property = `currentComponentId`
   - **CRITICAL:** The **Name** field MUST match the DPP name exactly (case-sensitive)

6. Configure the **Request/Response** tab:

| Setting | Value |
|---------|-------|
| **Request Headers** | Add: `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400` (Bad Request), `404` (Not Found), `429` (Rate Limit), `503` (Service Unavailable) |

7. Configure the **Options** tab:

| Setting | Value |
|---------|-------|
| **Timeout (ms)** | `120000` |
| **Query Parameters** | Add: Name = `overrideAccount`, Type = `Process Property`, Process Property = `devAccountId` |

8. Reference: see `/integration/api-requests/get-component.xml` for the expected response structure.
9. **Save**.

> The `overrideAccount` query parameter allows reading from dev sub-accounts using the primary account's API credentials. This is required for operations 1, 4, 5, and 6 -- any operation that reads data from a dev account.

#### Batch API Creation for Operations 2.2.2–2.2.20

The remaining 19 operations follow the same structure as the template captured in Step 2.2.1, with different names, HTTP methods, URLs, and content types. The setup script (`setup/steps/phase2a_http.py`) automates this — it takes the captured template XML, replaces the action element, method, content type, and path elements for each operation.

**If creating manually via API**, use the [API-First Discovery Workflow](#api-first-discovery-workflow) to capture one operation per HTTP method (GET, POST, DELETE), then clone and modify the XML for similar operations.

**Lookup Table:**

| Step | Operation Name | HTTP Method | Resource Path | Content-Type | Replacement Variables |
|------|---------------|-------------|---------------|--------------|----------------------|
| 2.2.2 | PROMO - HTTP Op - POST Component Create | POST | `/partner/api/rest/v1/{1}/Component~{2}` | `application/xml` | `{1}` = `primaryAccountId`, `{2}` = `branchId` |
| 2.2.3 | PROMO - HTTP Op - POST Component Update | POST | `/partner/api/rest/v1/{1}/Component/{2}~{3}` | `application/xml` | `{1}` = `primaryAccountId`, `{2}` = `prodComponentId`, `{3}` = `branchId` |
| 2.2.4 | PROMO - HTTP Op - GET ComponentReference | GET | `/partner/api/rest/v1/{1}/ComponentReference/{2}` | `application/xml` | `{1}` = `primaryAccountId`, `{2}` = `currentComponentId` + Query: `overrideAccount` = `devAccountId` |
| 2.2.5 | PROMO - HTTP Op - GET ComponentMetadata | GET | `/partner/api/rest/v1/{1}/ComponentMetadata/{2}` | `application/xml` | `{1}` = `primaryAccountId`, `{2}` = `currentComponentId` + Query: `overrideAccount` = `devAccountId` |
| 2.2.6 | PROMO - HTTP Op - QUERY PackagedComponent | POST | `/partner/api/rest/v1/{1}/PackagedComponent/query` | `application/xml` | `{1}` = `primaryAccountId` + Query: `overrideAccount` = `devAccountId` |
| 2.2.7 | PROMO - HTTP Op - POST PackagedComponent | POST | `/partner/api/rest/v1/{1}/PackagedComponent` | `application/json` | `{1}` = `primaryAccountId` |
| 2.2.8 | PROMO - HTTP Op - POST DeployedPackage | POST | `/partner/api/rest/v1/{1}/DeployedPackage` | `application/json` | `{1}` = `primaryAccountId` |
| 2.2.9 | PROMO - HTTP Op - POST IntegrationPack | POST | `/partner/api/rest/v1/{1}/IntegrationPack` | `application/json` | `{1}` = `primaryAccountId` |
| 2.2.10 | PROMO - HTTP Op - POST Branch | POST | `/partner/api/rest/v1/{1}/Branch` | `application/json` | `{1}` = `primaryAccountId` |
| 2.2.11 | PROMO - HTTP Op - QUERY Branch | POST | `/partner/api/rest/v1/{1}/Branch/query` | `application/json` | `{1}` = `primaryAccountId` |
| 2.2.12 | PROMO - HTTP Op - POST MergeRequest | POST | `/partner/api/rest/v1/{1}/MergeRequest` | `application/json` | `{1}` = `primaryAccountId` |
| 2.2.13 | PROMO - HTTP Op - POST MergeRequest Execute | POST | `/partner/api/rest/v1/{1}/MergeRequest/execute/{2}` | `application/json` | `{1}` = `primaryAccountId`, `{2}` = `mergeRequestId` |
| 2.2.14 | PROMO - HTTP Op - GET Branch | GET | `/partner/api/rest/v1/{1}/Branch/{2}` | `application/json` | `{1}` = `primaryAccountId`, `{2}` = `branchId` |
| 2.2.15 | PROMO - HTTP Op - DELETE Branch | DELETE | `/partner/api/rest/v1/{1}/Branch/{2}` | `application/json` | `{1}` = `primaryAccountId`, `{2}` = `branchId` |
| 2.2.16 | PROMO - HTTP Op - QUERY IntegrationPack | POST | `/partner/api/rest/v1/{1}/IntegrationPack/query` | `application/xml` | `{1}` = `primaryAccountId` |
| 2.2.17 | PROMO - HTTP Op - POST Add To IntegrationPack | POST | `/partner/api/rest/v1/{1}/IntegrationPack/{2}/PackagedComponent/{3}` | `application/json` | `{1}` = `primaryAccountId`, `{2}` = `integrationPackId`, `{3}` = `packagedComponentId` |
| 2.2.18 | PROMO - HTTP Op - POST ReleaseIntegrationPack | POST | `/partner/api/rest/v1/{1}/ReleaseIntegrationPack` | `application/json` | `{1}` = `primaryAccountId` |
| 2.2.19 | PROMO - HTTP Op - GET MergeRequest | GET | `/partner/api/rest/v1/{1}/MergeRequest/{2}` | `application/json` | `{1}` = `primaryAccountId`, `{2}` = `mergeRequestId` |
| 2.2.20 | PROMO - HTTP Op - GET ReleaseIntegrationPackStatus | GET | `/partner/api/rest/v1/{1}/ReleaseIntegrationPackStatus/{2}` | `application/json` | `{1}` = `primaryAccountId`, `{2}` = `releaseId` |

> **Note on URL notation:** The `{1}`, `{2}`, `{3}` placeholders in the table above are display shorthand. Internally, these map to named replacement variables: `{1}` = `primaryAccountId` (always), `{2}` and `{3}` vary by operation (e.g., `currentComponentId`, `branchId`, `mergeRequestId`). See [Understanding HTTP Client Replacement Variables](#understanding-http-client-replacement-variables) above.

> **UI Creation Pattern:** For each operation, follow the same UI workflow as Step 2.2.1, using the values from the lookup table. Configure replacement variables on the **Parameters** tab with names matching DPP names (case-sensitive). For POST operations with request bodies, use document property reference `{doc:requestBody}` in the Request Body field (see [The POST/PUT Parameters Tab Bug](#the-postput-parameters-tab-bug) for the DDP workaround).

##### API-First Discovery Workflow

If the template above does not produce the exact operation configuration you need, follow this workflow:

1. Create one operation manually in the Boomi UI (e.g., Step 2.2.2).
2. Note the component ID from the URL bar after saving.
3. Export the full component XML via API:

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{operationComponentId}"
```

```powershell
$cred = "BOOMI_TOKEN.user@company.com:your-api-token"
$base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($cred))
$headers = @{
    "Authorization" = "Basic $base64"
    "Accept"        = "application/xml"
}
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{operationComponentId}" `
    -Method GET -Headers $headers
```

4. Use the returned XML as the definitive template for the remaining 17 operations, substituting the operation-specific values from the lookup table.

#### Step 2.2.2 -- PROMO - HTTP Op - POST Component Create

Creates a new component in the primary (production) account. Used when no existing prod mapping exists.

> **API Alternative:** Use the [API-First Discovery Workflow](#api-first-discovery-workflow) with this operation's values from the lookup table.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST Component Create`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure the **Operation** tab:

| Setting | Value |
|---------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Resource Path** | `/partner/api/rest/v1/{1}/Component~{2}` |

5. Configure the **Parameters** tab (replacement variables):
   - For `{1}`: Name = `primaryAccountId`, Type = `Process Property`, Process Property = `primaryAccountId`
   - For `{2}`: Name = `branchId`, Type = `Process Property`, Process Property = `branchId`

6. Configure the **Request/Response** tab:

| Setting | Value |
|---------|-------|
| **Request Body** | `{doc:requestBody}` (references document property set in Set Properties shape) |
| **Request Headers** | Add: `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `429`, `503` |

7. Configure the **Options** tab:

| Setting | Value |
|---------|-------|
| **Timeout (ms)** | `120000` |

8. The request body is the stripped and reference-rewritten component XML. See `/integration/api-requests/create-component.xml` for the template structure. Note: `componentId` must be omitted or empty for creation (the API assigns a new ID). The `folderFullPath` follows the convention `/Promoted{devFolderFullPath}` — mirroring the dev account's folder hierarchy under `/Promoted/`.

> **Tilde syntax**: The `~{2}` suffix (DPP `branchId`) writes the new component to the promotion branch instead of main. The component will only exist on the branch until merged via MergeRequest.

> **POST body workaround**: Because HTTP Client operations don't support parameterized request bodies via the Parameters tab, the body MUST be built as a string in a Set Properties shape and stored in a document property (`{doc:requestBody}`). See Step 2.1.1 for details.

9. **Save**.

#### Step 2.2.3 -- PROMO - HTTP Op - POST Component Update

Updates an existing component in the primary account. Used when a DataHub mapping already exists.

> **API Alternative:** Use the [API-First Discovery Workflow](#api-first-discovery-workflow) with this operation's values from the lookup table.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST Component Update`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure the **Operation** tab:

| Setting | Value |
|---------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Resource Path** | `/partner/api/rest/v1/{1}/Component/{2}~{3}` |

5. Configure the **Parameters** tab (replacement variables):
   - For `{1}`: Name = `primaryAccountId`, Type = `Process Property`, Process Property = `primaryAccountId`
   - For `{2}`: Name = `prodComponentId`, Type = `Process Property`, Process Property = `prodComponentId`
   - For `{3}`: Name = `branchId`, Type = `Process Property`, Process Property = `branchId`

6. Configure the **Request/Response** tab:

| Setting | Value |
|---------|-------|
| **Request Body** | `{doc:requestBody}` (references document property set in Set Properties shape) |
| **Request Headers** | Add: `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |

7. Configure the **Options** tab:

| Setting | Value |
|---------|-------|
| **Timeout (ms)** | `120000` |

8. The `{2}` parameter is the production component ID from the DataHub ComponentMapping record. The API auto-increments the version number. See `/integration/api-requests/update-component.xml` for the template structure.

> **Tilde syntax**: The `~{3}` suffix (DPP `branchId`) writes the update to the promotion branch instead of main. The update will only exist on the branch until merged via MergeRequest.

> **POST body workaround**: Use `{doc:requestBody}` for the request body. See Step 2.1.1 for the DDP workaround pattern.

9. **Save**.

#### Step 2.2.4 -- PROMO - HTTP Op - GET ComponentReference

Retrieves one level of component dependencies (references) from a dev account. The promotion engine calls this recursively via BFS to build the full dependency tree.

> **API Alternative:** Use the [API-First Discovery Workflow](#api-first-discovery-workflow) with this operation's values from the lookup table.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - GET ComponentReference`.
3. Connection: `PROMO - Partner API Connection`.
4. Follow the same UI pattern as Step 2.2.1 with these values:
   - **Resource Path**: `/partner/api/rest/v1/{1}/ComponentReference/{2}`
   - **Parameters**: `{1}` = `primaryAccountId`, `{2}` = `currentComponentId`
   - **Query Parameters**: `overrideAccount` = `devAccountId`
   - **Request Headers**: `Accept: application/xml`
   - **Success Codes**: `200` | **Error Codes**: `400`, `404`, `429`, `503`
5. Response includes `DEPENDENT` and `INDEPENDENT` reference types. See `/integration/api-requests/query-component-reference.xml` for the response structure.
6. **Save**.

#### Step 2.2.5 -- PROMO - HTTP Op - GET ComponentMetadata

Retrieves lightweight metadata (name, type, version) without the full configuration XML. Faster than GET Component.

Follow the same UI pattern as Step 2.2.1 with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/ComponentMetadata/{2}`
- **Parameters**: `{1}` = `primaryAccountId`, `{2}` = `currentComponentId`
- **Query Parameters**: `overrideAccount` = `devAccountId`
- **Success Codes**: `200` | **Error Codes**: `400`, `404`, `429`, `503`

See `/integration/api-requests/query-component-metadata.xml` for the response structure.

#### Step 2.2.6 -- PROMO - HTTP Op - QUERY PackagedComponent

Queries packaged components from a dev sub-account. Returns paginated results (100 per page).

Follow the same UI pattern as Step 2.2.2 (POST operation) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/PackagedComponent/query`
- **Parameters**: `{1}` = `primaryAccountId`
- **Query Parameters**: `overrideAccount` = `devAccountId`
- **Request Body**: `{doc:requestBody}` (QueryFilter XML)
- **Content-Type**: `application/xml`
- **Success Codes**: `200` | **Error Codes**: `400`, `429`, `503`

See `/integration/api-requests/query-packaged-components.xml` for the filter structure. Handle pagination using `queryToken` via `/PackagedComponent/queryMore` with 120ms gap between pages.

#### Step 2.2.7 -- PROMO - HTTP Op - POST PackagedComponent

Creates a new PackagedComponent in the primary account. This is a JSON endpoint.

Follow the same UI pattern as Step 2.2.2 (POST operation) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/PackagedComponent`
- **Parameters**: `{1}` = `primaryAccountId`
- **Request Body**: `{doc:requestBody}` (JSON with `shareable: true`)
- **Content-Type**: `application/json`
- **Success Codes**: `200` | **Error Codes**: `400`, `429`, `503`

See `/integration/api-requests/create-packaged-component.json` for the template.

> From this operation onward (operations 7-20), both Content-Type and Accept headers must be `application/json`, not `application/xml`.

#### Step 2.2.8 -- PROMO - HTTP Op - POST DeployedPackage

Deploys a released Integration Pack to a target environment. Called once per target environment.

Follow the same UI pattern as Step 2.2.7 (POST/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/DeployedPackage`
- **Parameters**: `{1}` = `primaryAccountId`
- **Request Body**: `{doc:requestBody}` (JSON with `environmentId` and `packageId`)
- **Success Codes**: `200` | **Error Codes**: `400`, `404`, `429`, `503`

See `/integration/api-requests/create-deployed-package.json` for the template.

#### Step 2.2.9 -- PROMO - HTTP Op - POST IntegrationPack

Creates a new Integration Pack when `createNewPack=true` in the deployment request.

Follow the same UI pattern as Step 2.2.7 (POST/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/IntegrationPack`
- **Parameters**: `{1}` = `primaryAccountId`
- **Request Body**: `{doc:requestBody}` (JSON with `installationType: "MULTI"`)
- **Success Codes**: `200` | **Error Codes**: `400`, `429`, `503`

After creation, add the PackagedComponent (operation 17), then release (operation 18). See `/integration/api-requests/create-integration-pack.json` for the template.

#### Step 2.2.10 -- PROMO - HTTP Op - POST Branch

Creates a promotion branch for isolated component changes before merging to main.

Follow the same UI pattern as Step 2.2.7 (POST/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/Branch`
- **Parameters**: `{1}` = `primaryAccountId`
- **Request Body**: `{doc:requestBody}` (JSON with `name` and `description`)
- **Success Codes**: `200` | **Error Codes**: `400`, `429`, `503`

Response includes `branchId`. See `/integration/api-requests/create-branch.json` for the template.

#### Step 2.2.11 -- PROMO - HTTP Op - QUERY Branch

Queries existing branches to enforce the 15-branch operational limit and check for existing promotion branches. The platform hard limit is 20 branches per account. The operational threshold of 15 provides buffer for manual branches.

Follow the same UI pattern as Step 2.2.7 (POST/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/Branch/query`
- **Parameters**: `{1}` = `primaryAccountId`
- **Request Body**: `{doc:requestBody}` (JSON with optional filter expressions like `name LIKE 'promo-%'`)
- **Success Codes**: `200` | **Error Codes**: `400`, `429`, `503`

Returns paginated results. See `/integration/api-requests/query-branch.json` for the template.

#### Step 2.2.12 -- PROMO - HTTP Op - POST MergeRequest

Creates a merge request to merge promotion branch changes back to main after admin approval.

Follow the same UI pattern as Step 2.2.7 (POST/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/MergeRequest`
- **Parameters**: `{1}` = `primaryAccountId`
- **Request Body**: `{doc:requestBody}` (JSON with `sourceBranchId` and `targetBranchId`)
- **Success Codes**: `200` | **Error Codes**: `400`, `409` (Conflict), `429`, `503`

Automatically merges if no conflicts exist. See `/integration/api-requests/create-merge-request.json` for the template.

#### Step 2.2.13 -- PROMO - HTTP Op - POST MergeRequest Execute

Executes a previously created merge request to merge the promotion branch into main.

Follow the same UI pattern as Step 2.2.7 (POST/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/MergeRequest/execute/{2}`
- **Parameters**: `{1}` = `primaryAccountId`, `{2}` = `mergeRequestId`
- **Request Body**: `{doc:requestBody}` (JSON with `action: "MERGE"`)
- **Success Codes**: `200` | **Error Codes**: `400`, `409` (Conflict), `429`, `503`

After execution, poll `GET /MergeRequest/{mergeRequestId}` until `stage=MERGED`. See `/integration/api-requests/execute-merge-request.json` for the template.

#### Step 2.2.14 -- PROMO - HTTP Op - GET Branch

Retrieves a single branch by ID. Used to poll for branch readiness after creation.

Follow the same UI pattern as Step 2.2.1 (GET/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/Branch/{2}`
- **Parameters**: `{1}` = `primaryAccountId`, `{2}` = `branchId`
- **Request Headers**: `Accept: application/json` (no Content-Type for GET)
- **Success Codes**: `200` | **Error Codes**: `400`, `404`, `429`, `503`

Response includes `ready` (boolean). Poll with 5-second delay until `ready=true`, max 6 retries. See `/integration/api-requests/get-branch.json` for the response structure.

#### Step 2.2.15 -- PROMO - HTTP Op - DELETE Branch

Deletes a promotion branch. Called on all terminal paths (approve, reject, deny, error).

Follow the same UI pattern as Step 2.2.1 (GET operation, but DELETE method) with these values:
- **HTTP Method**: DELETE
- **Resource Path**: `/partner/api/rest/v1/{1}/Branch/{2}`
- **Parameters**: `{1}` = `primaryAccountId`, `{2}` = `branchId`
- **Request Headers**: `Accept: application/json`
- **Success Codes**: `200`, `404` (both treated as success — idempotent)
- **Error Codes**: `429`, `503`

See `/integration/api-requests/delete-branch.json` for lifecycle paths.

#### Step 2.2.16 -- PROMO - HTTP Op - QUERY IntegrationPack

Queries Integration Packs in the primary account. Used by Process J to populate the Integration Pack selector.

Follow the same UI pattern as Step 2.2.6 (POST/XML query) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/IntegrationPack/query`
- **Parameters**: `{1}` = `primaryAccountId`
- **Request Body**: `{doc:requestBody}` (QueryFilter XML with `installationType = MULTI`)
- **Content-Type**: `application/xml` (NOTE: XML, not JSON)
- **Success Codes**: `200` | **Error Codes**: `400`, `429`, `503`

See `/integration/api-requests/query-integration-packs.xml` for the filter structure. Handle pagination using `queryToken` via `/IntegrationPack/queryMore`.

#### Step 2.2.17 -- PROMO - HTTP Op - POST Add To IntegrationPack

Adds a PackagedComponent to an Integration Pack. No request body -- the linking is done via URL parameters.

Follow the same UI pattern as Step 2.2.1 (but POST method) with these values:
- **HTTP Method**: POST
- **Resource Path**: `/partner/api/rest/v1/{1}/IntegrationPack/{2}/PackagedComponent/{3}`
- **Parameters**: `{1}` = `primaryAccountId`, `{2}` = `integrationPackId`, `{3}` = `packagedComponentId`
- **Request Body**: (empty — linking done via URL)
- **Request Headers**: `Accept: application/json`, `Content-Type: application/json`
- **Success Codes**: `200` | **Error Codes**: `400`, `404`, `429`, `503`

See `/integration/api-requests/add-to-integration-pack.json` for documentation.

#### Step 2.2.18 -- PROMO - HTTP Op - POST ReleaseIntegrationPack

Releases an Integration Pack, creating a deployable snapshot. Must be called after adding all PackagedComponents.

Follow the same UI pattern as Step 2.2.7 (POST/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/ReleaseIntegrationPack`
- **Parameters**: `{1}` = `primaryAccountId`
- **Request Body**: `{doc:requestBody}` (JSON with `integrationPackId`, `version`, `notes`)
- **Success Codes**: `200` | **Error Codes**: `400`, `404`, `429`, `503`

Response returns `packageId` used for subsequent deployment. See `/integration/api-requests/release-integration-pack.json` for the template.

#### Step 2.2.19 -- PROMO - HTTP Op - GET MergeRequest

Retrieves the status of a merge request. Used to poll after executing a merge until `stage=MERGED`.

Follow the same UI pattern as Step 2.2.14 (GET/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/MergeRequest/{2}`
- **Parameters**: `{1}` = `primaryAccountId`, `{2}` = `mergeRequestId`
- **Success Codes**: `200` | **Error Codes**: `400`, `404`, `429`, `503`

Poll with 2-second delay until `stage=MERGED` or `stage=FAILED_TO_MERGE`. Stages progress: `DRAFTING` → `DRAFTED` → `REVIEWING` → `MERGING` → `MERGED`. See `/integration/api-requests/get-merge-request.json` for documentation.

#### Step 2.2.20 -- PROMO - HTTP Op - GET ReleaseIntegrationPackStatus

Retrieves the status of a released Integration Pack. Used to poll after release until propagation completes.

Follow the same UI pattern as Step 2.2.14 (GET/JSON) with these values:
- **Resource Path**: `/partner/api/rest/v1/{1}/ReleaseIntegrationPackStatus/{2}`
- **Parameters**: `{1}` = `primaryAccountId`, `{2}` = `releaseId`
- **Success Codes**: `200` | **Error Codes**: `400`, `404`, `429`, `503`

Response includes `status` field indicating propagation state. See `/integration/api-requests/get-release-integration-pack-status.json` for the response structure.

---
Prev: [Phase 1: DataHub Foundation](01-datahub-foundation.md) | Next: [Phase 2b: DataHub Connection Setup](03-datahub-connection-setup.md) | [Back to Index](index.md)

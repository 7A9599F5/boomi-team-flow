## Phase 2: Integration Connections & Operations

This phase creates the connection and operation components that all integration processes depend on. There are 2 connections and 25 operations total (19 HTTP Client + 6 DataHub).

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

Create 19 HTTP Client operations. Each uses the `PROMO - Partner API Connection` from Step 2.1.

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

> Operations 1-6 use `application/xml` for both Content-Type and Accept headers (Platform API XML endpoints). Operations 7-9 use `application/json` for both headers (JSON-based endpoints). Operation 16 uses `application/xml` (query endpoint). Operations 17-19 use `application/json`.

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
| **Request URL** | `/partner/api/rest/v1/{1}/Component~{2}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `branchId` |
| **Query Parameters** | (none -- creates in the primary account directly) |
| **Request Headers** | `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. The request body is the stripped and reference-rewritten component XML. See `/integration/api-requests/create-component.xml` for the template structure. Note: `componentId` must be omitted or empty for creation (the API assigns a new ID). The `folderFullPath` follows the convention `/Promoted{devFolderFullPath}` — mirroring the dev account's folder hierarchy under `/Promoted/`.

> **Tilde syntax**: The `~{2}` suffix (DPP `branchId`) writes the new component to the promotion branch instead of main. The component will only exist on the branch until merged via MergeRequest.
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
| **Request URL** | `/partner/api/rest/v1/{1}/Component/{2}~{3}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `prodComponentId`; `{3}` = DPP `branchId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. The `{2}` parameter is the production component ID from the DataHub ComponentMapping record. The API auto-increments the version number. See `/integration/api-requests/update-component.xml` for the template structure.

> **Tilde syntax**: The `~{3}` suffix (DPP `branchId`) writes the update to the promotion branch instead of main. The update will only exist on the branch until merged via MergeRequest.
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

5. After creation, add the PackagedComponent to the pack (operation 17), then release via `PROMO - HTTP Op - POST ReleaseIntegrationPack` (operation 18). Set `installationType: "MULTI"` for multi-install packs. See `/integration/api-requests/create-integration-pack.json` for the template.
6. **Save**.

#### Step 2.2.10 -- PROMO - HTTP Op - POST Branch

Creates a promotion branch for isolated component changes before merging to main.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST Branch`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/Branch` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json`, `Content-Type: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Request body requires `name` and `description` fields. Response includes `branchId`.
6. **Save**.

#### Step 2.2.11 -- PROMO - HTTP Op - QUERY Branch

Queries existing branches to enforce the 10-branch limit and check for existing promotion branches.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - QUERY Branch`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/Branch/query` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json`, `Content-Type: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Supports filter expressions (e.g., `name LIKE 'promo-%'`). Returns paginated results.
6. **Save**.

#### Step 2.2.12 -- PROMO - HTTP Op - POST MergeRequest

Creates a merge request to merge promotion branch changes back to main after admin approval.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST MergeRequest`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/MergeRequest` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json`, `Content-Type: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `409` (Conflict), `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Request body requires `sourceBranchId` and `targetBranchId` (usually main). Automatically merges if no conflicts exist.
6. **Save**.

#### Step 2.2.13 -- PROMO - HTTP Op - POST MergeRequest Execute

Executes a previously created merge request to merge the promotion branch into main.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST MergeRequest Execute`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/MergeRequest/execute/{2}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `mergeRequestId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json`, `Content-Type: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `409` (Conflict), `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Request body includes `action: "MERGE"`. After execution, poll `GET /MergeRequest/{mergeRequestId}` until `stage=MERGED`. See `/integration/api-requests/execute-merge-request.json` for the template.
6. **Save**.

#### Step 2.2.14 -- PROMO - HTTP Op - GET Branch

Retrieves a single branch by ID. Used to poll for branch readiness after creation.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - GET Branch`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | GET |
| **Request URL** | `/partner/api/rest/v1/{1}/Branch/{2}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `branchId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Response includes `ready` (boolean). Poll with 5-second delay until `ready=true`, max 6 retries. See `/integration/api-requests/get-branch.json` for the response structure.
6. **Save**.

#### Step 2.2.15 -- PROMO - HTTP Op - DELETE Branch

Deletes a promotion branch. Called on all terminal paths (approve, reject, deny, error).

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - DELETE Branch`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | DELETE |
| **Request URL** | `/partner/api/rest/v1/{1}/Branch/{2}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `branchId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json` |
| **Response Codes - Success** | `200`, `404` |
| **Response Codes - Error** | `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Idempotent: both `200` (deleted) and `404` (already deleted) are treated as success. See `/integration/api-requests/delete-branch.json` for lifecycle paths.
6. **Save**.

#### Step 2.2.16 -- PROMO - HTTP Op - QUERY IntegrationPack

Queries Integration Packs in the primary account. Used by Process J to populate the Integration Pack selector.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - QUERY IntegrationPack`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/IntegrationPack/query` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/xml`, `Content-Type: application/xml` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. The request body is a `QueryFilter` element. See `/integration/api-requests/query-integration-packs.xml` for the filter structure. Filters by `installationType = MULTI`. Handle pagination using `queryToken` via `/IntegrationPack/queryMore`.
6. **Save**.

#### Step 2.2.17 -- PROMO - HTTP Op - POST Add To IntegrationPack

Adds a PackagedComponent to an Integration Pack. No request body — the linking is done via URL parameters.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST Add To IntegrationPack`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/IntegrationPack/{2}/PackagedComponent/{3}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `integrationPackId`; `{3}` = DPP `packagedComponentId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json`, `Content-Type: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. No request body required. The URL itself links the PackagedComponent to the Integration Pack. See `/integration/api-requests/add-to-integration-pack.json` for documentation.
6. **Save**.

#### Step 2.2.18 -- PROMO - HTTP Op - POST ReleaseIntegrationPack

Releases an Integration Pack, creating a deployable snapshot. Must be called after adding all PackagedComponents.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - POST ReleaseIntegrationPack`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | POST |
| **Request URL** | `/partner/api/rest/v1/{1}/ReleaseIntegrationPack` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json`, `Content-Type: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Request body includes `integrationPackId`, `version`, and `notes`. See `/integration/api-requests/release-integration-pack.json` for the template. The response returns a `packageId` used for subsequent deployment.
6. **Save**.

#### Step 2.2.19 -- PROMO - HTTP Op - GET MergeRequest

Retrieves the status of a merge request. Used to poll after executing a merge until `stage=MERGED`.

1. **Build --> New Component --> Connector --> Operation --> HTTP Client**.
2. Name: `PROMO - HTTP Op - GET MergeRequest`.
3. Connection: `PROMO - Partner API Connection`.
4. Configure:

| Tab / Setting | Value |
|---------------|-------|
| **Action** | Send |
| **HTTP Method** | GET |
| **Request URL** | `/partner/api/rest/v1/{1}/MergeRequest/{2}` |
| **Request URL Parameters** | `{1}` = DPP `primaryAccountId`; `{2}` = DPP `mergeRequestId` |
| **Query Parameters** | (none) |
| **Request Headers** | `Accept: application/json` |
| **Response Codes - Success** | `200` |
| **Response Codes - Error** | `400`, `404`, `429`, `503` |
| **Timeout (ms)** | `120000` |

5. Poll with 2-second delay until `stage=MERGED` (success) or `stage=FAILED_TO_MERGE` (failure). Merge stages progress: `DRAFTING` → `DRAFTED` → `REVIEWING` → `MERGING` → `MERGED`. See `/integration/api-requests/get-merge-request.json` for documentation.
6. **Save**.

---
Prev: [Phase 1: DataHub Foundation](01-datahub-foundation.md) | Next: [Phase 2b: DataHub Connection Setup](03-datahub-connection-setup.md) | [Back to Index](index.md)

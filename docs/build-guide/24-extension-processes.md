## Phase 7: Extension Editor Processes (K–O)

This section documents the 5 integration processes that power the Extension Editor feature. Build them in order: K → L → M → N → O. Process K has no dependencies; the remaining processes build on K's context.

> **API Alternative:** Each of these processes can be created programmatically via `POST /Component` with `type="process"`. Due to the complexity of process canvas XML (shapes, routing, DPP mappings, script references), the recommended workflow is: (1) build the process manually following the steps below, (2) use `GET /Component/{processId}` to export the XML, (3) store the XML as a template for automated recreation. See [Appendix D: API Automation Guide](22-api-automation-guide.md) for the full workflow.

---

### Process K: List Client Accounts (`PROMO - List Client Accounts`)

This process retrieves client accounts accessible to the authenticated user based on their SSO group memberships. It queries the `ClientAccountConfig` DataHub model and enriches each account with Test and Production environment names fetched via the Platform API.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - ListClientAccountsRequest` | `/integration/profiles/listClientAccounts-request.json` |
| `PROMO - Profile - ListClientAccountsResponse` | `/integration/profiles/listClientAccounts-response.json` |

The request JSON contains:
- `userSsoGroups` (array of strings): the authenticated user's Azure AD/Entra SSO group names

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `clientAccounts` (array): each entry has `clientAccountId`, `clientAccountName`, `testEnvironmentId`, `testEnvironmentName`, `prodEnvironmentId`, `prodEnvironmentName`

#### FSS Operation

Create `PROMO - FSS Op - ListClientAccounts` per the pattern in Section 3.B, using `PROMO - Profile - ListClientAccountsRequest` and `PROMO - Profile - ListClientAccountsResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - ListClientAccounts`

2. **Set Properties** (read request fields)
   - DPP `userSsoGroups` = read from document path: `userSsoGroups` (JSON array; store as string for downstream parsing)
   - DPP `primaryAccountId` = read from Flow Service configuration value `primaryAccountId`

3. **Decision — Validate SSO Groups**
   - Condition: `userSsoGroups` DPP is empty or null
   - **True path (error)**: Go to step 3a
   - **False path (continue)**: Go to step 4
   - **3a. Map — Build Error Response**: Set `success = false`, `errorCode = "UNAUTHORIZED"`, `errorMessage = "No SSO groups provided; cannot determine client account access"`. Connect to Return Documents.

4. **Data Process — Query ClientAccountConfig**
   - Add a **Connector** shape (DataHub):
     - Connector: `PROMO - DataHub Connection`
     - Operation: `PROMO - DH Op - Query ClientAccountConfig`
     - Filter: `isActive EQUALS "true"` — admins (SSO group `ABC_BOOMI_FLOW_ADMIN`) receive all active records; contributors receive only records where `authorizedSsoGroups` intersects the user's groups
   - The SSO group filtering logic mirrors the tier resolution in Process A0: parse `userSsoGroups`, check for `ABC_BOOMI_FLOW_ADMIN` to determine admin bypass

5. **For Each Client Account** — the DataHub query returns one document per matching ClientAccountConfig record; each flows into the next shape individually

   **5a. HTTP Client Send — Get Test Environment Name**
   - Connector: `PROMO - HTTP Connection`
   - Operation: `PROMO - HTTP Op - QUERY Environment`
   - Add query parameter `overrideAccount = {clientAccountId}` (read from current document)
   - Filter response to extract the `testEnvironmentId` matching environment record and capture `environmentName`

   **5b. HTTP Client Send — Get Prod Environment Name**
   - Same connector and operation as 5a
   - Filter to the `prodEnvironmentId` environment record and capture `environmentName`

   **5c. Map — Merge Environment Names**
   - Source: combined data from DataHub record + environment name responses
   - Destination: interim client account object with all six fields populated: `clientAccountId`, `clientAccountName`, `testEnvironmentId`, `testEnvironmentName`, `prodEnvironmentId`, `prodEnvironmentName`

6. **Data Process — Collect Results**
   - Add a **Data Process** shape with Groovy to accumulate all per-account documents into a single JSON array:
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import groovy.json.JsonSlurper
   import groovy.json.JsonOutput

   def accounts = []
   for (int i = 0; i < dataContext.getDataCount(); i++) {
       InputStream is = dataContext.getStream(i)
       Properties props = dataContext.getProperties(i)
       String json = is.getText("UTF-8")
       def account = new JsonSlurper().parseText(json)
       accounts << account
   }
   ExecutionUtil.setDynamicProcessProperty("clientAccountCount", accounts.size().toString(), false)
   String output = JsonOutput.prettyPrint(JsonOutput.toJson(accounts))
   dataContext.storeStream(new ByteArrayInputStream(output.getBytes("UTF-8")), dataContext.getProperties(0))
   ```

7. **Map — Build Response JSON**
   - Source: the collected accounts array from step 6
   - Destination: `PROMO - Profile - ListClientAccountsResponse`
   - Map the accounts array to `clientAccounts`
   - Set `success = true`

8. **Return Documents** — same as Process A0

#### Dynamic Process Properties

| Name | Type | Persist | Purpose |
|------|------|---------|---------|
| `userSsoGroups` | String (JSON array) | false | SSO groups from request; used to determine admin vs contributor access |
| `primaryAccountId` | String | false | Primary account ID from Flow Service config; passed to `overrideAccount` HTTP calls |
| `clientAccountCount` | String | false | Count of returned client accounts; used for logging |

#### Error Codes

| Error Code | Trigger Condition |
|------------|-------------------|
| `UNAUTHORIZED` | `userSsoGroups` is empty or null in the request |
| `DATAHUB_ERROR` | ClientAccountConfig query fails |
| `CLIENT_ACCOUNT_NOT_FOUND` | ClientAccountConfig record references an environment ID not found via the Platform API |

#### Verify

- Seed at least one ClientAccountConfig golden record in DataHub with a valid `clientAccountId`, `testEnvironmentId`, and `prodEnvironmentId`
- Send a `listClientAccounts` request with an SSO group that matches the seeded record
- **Expected**: response with `success = true` and a `clientAccounts` array containing the matching account with both environment names populated
- Send a request with an SSO group that has no matching ClientAccountConfig record
- **Expected**: response with `success = true` and `clientAccounts = []` (empty array)
- Send a request with an empty `userSsoGroups` array
- **Expected**: response with `success = false` and `errorCode = "UNAUTHORIZED"`

---

### Process L: Get Extensions (`PROMO - Get Extensions`)

This process reads environment extensions and map extension summaries for a specified client account environment, merges them with ExtensionAccessMapping records from DataHub, and returns a combined response. Extension data is returned as JSON-serialized strings to avoid deeply nested profile complexity — the custom component parses them client-side.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - GetExtensionsRequest` | `/integration/profiles/getExtensions-request.json` |
| `PROMO - Profile - GetExtensionsResponse` | `/integration/profiles/getExtensions-response.json` |

The request JSON contains:
- `clientAccountId` (string): target client sub-account ID
- `environmentId` (string): target environment ID within the client account
- `userSsoGroups` (array of strings): for access filtering
- `userEmail` (string): for audit trail

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `environmentId`, `extensionData`, `accessMappings`, `mapExtensionSummaries` (JSON strings)
- `componentCount`, `connectionCount`, `processPropertyCount`, `dynamicPropertyCount`, `mapExtensionCount` (integers)

#### FSS Operation

Create `PROMO - FSS Op - GetExtensions` per the pattern in Section 3.B, using `PROMO - Profile - GetExtensionsRequest` and `PROMO - Profile - GetExtensionsResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - GetExtensions`

2. **Set Properties** (read request fields)
   - DPP `clientAccountId` = read from document path: `clientAccountId`
   - DPP `environmentId` = read from document path: `environmentId`
   - DPP `userSsoGroups` = read from document path: `userSsoGroups`
   - DPP `userEmail` = read from document path: `userEmail`

3. **Decision — Validate Required Fields**
   - Condition: `clientAccountId` or `environmentId` DPP is empty or null
   - **True path (error)**: Map error response with `success = false`, `errorCode = "INVALID_REQUEST"`, `errorMessage = "clientAccountId and environmentId are required"`. Connect to Return Documents.
   - **False path (continue)**: Go to step 4

4. **HTTP Client Send — GET EnvironmentExtensions**
   - Connector: `PROMO - HTTP Connection`
   - Operation: `PROMO - HTTP Op - GET EnvironmentExtensions`
   - Add header/parameter `overrideAccount = {clientAccountId}` DPP
   - URL path includes `{environmentId}` DPP
   - Store the raw JSON response in DPP `rawExtensionData`

5. **HTTP Client Send — QUERY EnvironmentMapExtensionsSummary**
   - Connector: `PROMO - HTTP Connection`
   - Operation: `PROMO - HTTP Op - QUERY EnvironmentMapExtensionsSummary`
   - Same `overrideAccount` override as step 4
   - URL path includes `{environmentId}` DPP
   - Store the raw JSON response in DPP `rawMapSummaryData`

6. **Connector — DataHub Query ExtensionAccessMapping**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query ExtensionAccessMapping`
   - Filter: `environmentId EQUALS {environmentId}` DPP
   - This returns all ExtensionAccessMapping records for the requested environment, which the Groovy script will use to determine per-component access rights

7. **Data Process — merge-extension-data.groovy**
   - Add a **Data Process** shape referencing `merge-extension-data.groovy` (from `/integration/scripts/`)
   - The script expects a combined JSON input containing three datasets: `envExtensions` (from step 4 raw JSON), `mapSummaries` (from step 5 raw JSON), and `accessMappings` (from step 6 DataHub query)
   - Assemble the combined input using a **Map** shape before this step that builds the three-key structure from DPPs and the DataHub document
   - The script:
     - Serializes `envExtensions` as a JSON string for `extensionData`
     - Serializes `accessMappings` as a JSON string
     - Serializes `mapSummaries` as a JSON string for `mapExtensionSummaries`
     - Counts components by type (connections, processProperties, dynamic properties, map extensions)
     - Emits a single document with the merged response structure
   - Sets DPP `extensionCount` = total component count from script output
   - Sets DPP `mapExtensionCount` = map extension count from script output

8. **Map — Build getExtensionsResponse JSON**
   - Source: output from step 7
   - Destination: `PROMO - Profile - GetExtensionsResponse`
   - Map all fields: `success`, `environmentId`, `extensionData`, `accessMappings`, `mapExtensionSummaries`, `componentCount`, `connectionCount`, `processPropertyCount`, `dynamicPropertyCount`, `mapExtensionCount`
   - Set `success = true`

9. **Return Documents**

#### Dynamic Process Properties

| Name | Type | Persist | Purpose |
|------|------|---------|---------|
| `clientAccountId` | String | false | Target client sub-account ID; passed to `overrideAccount` |
| `environmentId` | String | false | Target environment ID; used in API URL path and DataHub filter |
| `userSsoGroups` | String (JSON array) | false | SSO groups for access filtering; passed to merge script |
| `userEmail` | String | false | Requesting user email; for audit trail in merge script |
| `rawExtensionData` | String (JSON) | false | Raw EnvironmentExtensions GET response; fed into merge script |
| `rawMapSummaryData` | String (JSON) | false | Raw MapExtensionsSummary response; fed into merge script |
| `extensionCount` | String | false | Total extension component count from merge script |
| `mapExtensionCount` | String | false | Map extension count from merge script |

#### Error Codes

| Error Code | Trigger Condition |
|------------|-------------------|
| `INVALID_REQUEST` | `clientAccountId` or `environmentId` missing from request |
| `EXTENSION_NOT_FOUND` | Environment ID not found in the Platform API (HTTP 404 on GET EnvironmentExtensions) |
| `DATAHUB_ERROR` | ExtensionAccessMapping query fails |
| `AUTH_FAILED` | Platform API authentication failure on HTTP calls |

#### Verify

- Seed an ExtensionAccessMapping record in DataHub for a known `environmentId` and `prodComponentId`
- Send a `getExtensions` request with a valid `clientAccountId` and `environmentId`
- **Expected**: response with `success = true`, non-empty `extensionData` string (parseable JSON), `accessMappings` string, and non-zero counts where the environment has extensions
- Send a request with an invalid `environmentId`
- **Expected**: response with `success = false` and `errorCode = "EXTENSION_NOT_FOUND"`

---

### Process M: Update Extensions (`PROMO - Update Extensions`)

This process saves environment extension changes for a specified client account environment. It validates that the requesting user has authorization for each modified component via ExtensionAccessMapping lookup, rejects connection edits for non-admin users, and uses `partial="true"` to ensure only modified sections are updated.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - UpdateExtensionsRequest` | `/integration/profiles/updateExtensions-request.json` |
| `PROMO - Profile - UpdateExtensionsResponse` | `/integration/profiles/updateExtensions-response.json` |

The request JSON contains:
- `clientAccountId` (string): target client sub-account ID
- `environmentId` (string): target environment ID
- `extensionPayload` (string): JSON-serialized partial EnvironmentExtensions update
- `userSsoGroups` (array of strings): for access validation
- `userEmail` (string): for audit trail

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `updatedFieldCount` (integer), `environmentId` (string)
- `errors` (array, optional): per-component errors

#### FSS Operation

Create `PROMO - FSS Op - UpdateExtensions` per the pattern in Section 3.B, using `PROMO - Profile - UpdateExtensionsRequest` and `PROMO - Profile - UpdateExtensionsResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - UpdateExtensions`

2. **Set Properties** (read request fields)
   - DPP `clientAccountId` = read from document path: `clientAccountId`
   - DPP `environmentId` = read from document path: `environmentId`
   - DPP `extensionPayload` = read from document path: `extensionPayload`
   - DPP `userSsoGroups` = read from document path: `userSsoGroups`
   - DPP `userEmail` = read from document path: `userEmail`

3. **Decision — Validate Required Fields**
   - Condition: `clientAccountId`, `environmentId`, or `extensionPayload` DPP is empty or null
   - **True path (error)**: Map error response with `success = false`, `errorCode = "INVALID_REQUEST"`. Connect to Return Documents.
   - **False path (continue)**: Go to step 4

4. **Connector — DataHub Query ExtensionAccessMapping**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query ExtensionAccessMapping`
   - Filter: `environmentId EQUALS {environmentId}` DPP
   - Returns all access mappings for the environment, used for authorization checking in step 5

5. **Data Process — Validate Access Scope**
   - Add a **Data Process** shape with inline Groovy that:
     1. Parses the `extensionPayload` DPP (JSON) to extract the set of component IDs being modified
     2. For each component in the payload, looks up its ExtensionAccessMapping record from step 4
     3. Checks `isConnectionExtension`: if `"true"` and user is not ADMIN tier → sets DPP `unauthorizedFields` with the component name, sets DPP `unauthorizedReason = "CONNECTION_EDIT_ADMIN_ONLY"`
     4. Checks `authorizedSsoGroups`: if user's SSO groups do not intersect the authorized groups and user is not ADMIN → sets DPP `unauthorizedFields`, sets DPP `unauthorizedReason = "UNAUTHORIZED_EXTENSION_EDIT"`
     5. If no ExtensionAccessMapping record exists for a component → sets DPP `unauthorizedReason = "EXTENSION_NOT_FOUND"` (conservative default — unknown components are rejected)
     6. Sets DPP `updatedFieldCount` = count of authorized fields being changed
   - Admin tier detection: check if `userSsoGroups` contains `"ABC_BOOMI_FLOW_ADMIN"`
   - Pass the document through unchanged (`dataContext.storeStream(is, props)`)

6. **Decision — Check Authorization Result**
   - Condition: DPP `unauthorizedFields` is non-empty
   - **True path (error)**: Map error response with `success = false`, `errorCode` = DPP `unauthorizedReason`. Connect to Return Documents.
   - **False path (authorized)**: Go to step 7

7. **HTTP Client Send — UPDATE EnvironmentExtensions**
   - Connector: `PROMO - HTTP Connection`
   - Operation: `PROMO - HTTP Op - UPDATE EnvironmentExtensions`
   - Add header/parameter `overrideAccount = {clientAccountId}` DPP
   - **Critical**: Always use `partial="true"` on the UPDATE request. Omitting this flag will wipe all extension values not present in the payload. The `extensionPayload` DPP already contains the partial JSON body to send.
   - URL path includes `{environmentId}` DPP

8. **Map — Build updateExtensionsResponse JSON**
   - Source: HTTP response from step 7
   - Destination: `PROMO - Profile - UpdateExtensionsResponse`
   - Map `updatedFieldCount` from DPP `updatedFieldCount`
   - Map `environmentId` from DPP
   - Set `success = true`

9. **Return Documents**

#### Dynamic Process Properties

| Name | Type | Persist | Purpose |
|------|------|---------|---------|
| `clientAccountId` | String | false | Target client sub-account ID; passed to `overrideAccount` |
| `environmentId` | String | false | Target environment ID; used in API URL and DataHub filter |
| `extensionPayload` | String (JSON) | false | Partial EnvironmentExtensions payload to send to Platform API |
| `userSsoGroups` | String (JSON array) | false | User's SSO groups for tier and access validation |
| `userEmail` | String | false | Requesting user email; for audit trail |
| `updatedFieldCount` | String | false | Count of authorized fields being changed; set by validation Groovy |
| `unauthorizedFields` | String | false | Comma-separated list of unauthorized component names (empty = authorized) |
| `unauthorizedReason` | String | false | Error code to return when unauthorized fields are detected |

#### Key Detail: Always Use `partial="true"`

The Platform API `UPDATE EnvironmentExtensions` endpoint is **not a merge** — it is a replace operation on each section included in the payload. Sections omitted from the payload are left unchanged only when `partial="true"` is set. Without this flag, omitted sections are cleared. The `extensionPayload` from the request already contains only the changed sections, but the `partial` flag must still be explicitly set on the HTTP call.

#### Error Codes

| Error Code | Trigger Condition |
|------------|-------------------|
| `INVALID_REQUEST` | Required fields missing from request |
| `UNAUTHORIZED_EXTENSION_EDIT` | User's SSO groups do not authorize editing this extension component |
| `CONNECTION_EDIT_ADMIN_ONLY` | Non-admin user attempted to edit a connection extension |
| `EXTENSION_NOT_FOUND` | No ExtensionAccessMapping record exists for a component in the payload |
| `AUTH_FAILED` | Platform API authentication failure on the UPDATE call |

#### Verify

- As a CONTRIBUTOR user, attempt to update a connection extension
- **Expected**: response with `success = false` and `errorCode = "CONNECTION_EDIT_ADMIN_ONLY"`
- As a CONTRIBUTOR user, update a process property extension that is in their `authorizedSsoGroups`
- **Expected**: response with `success = true` and `updatedFieldCount > 0`
- Verify that unmodified extensions retain their values by calling `getExtensions` before and after — only the targeted fields should change

---

### Process N: Copy Extensions Test to Prod (`PROMO - Copy Extensions Test to Prod`)

This process copies non-connection environment extensions from a Test environment to a Production environment within the same client account. It fetches the Test environment extensions, strips connection and PGP certificate sections, swaps the environment ID, and posts to Production with `partial="true"`. Encrypted values cannot be copied (they are not returned by the GET endpoint).

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - CopyExtensionsTestToProdRequest` | `/integration/profiles/copyExtensionsTestToProd-request.json` |
| `PROMO - Profile - CopyExtensionsTestToProdResponse` | `/integration/profiles/copyExtensionsTestToProd-response.json` |

The request JSON contains:
- `clientAccountId` (string): target client sub-account ID
- `testEnvironmentId` (string): source Test environment ID
- `prodEnvironmentId` (string): target Production environment ID
- `userSsoGroups` (array of strings): for access validation
- `userEmail` (string): for audit trail

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `sectionsExcluded` (string): comma-separated list of excluded sections
- `fieldsCopied` (integer): count of extension fields successfully copied
- `encryptedFieldsSkipped` (integer): count of encrypted fields that could not be copied
- `testEnvironmentId`, `prodEnvironmentId` (strings): echoed back

#### FSS Operation

Create `PROMO - FSS Op - CopyExtensionsTestToProd` per the pattern in Section 3.B, using `PROMO - Profile - CopyExtensionsTestToProdRequest` and `PROMO - Profile - CopyExtensionsTestToProdResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - CopyExtensionsTestToProd`

2. **Set Properties** (read request fields)
   - DPP `clientAccountId` = read from document path: `clientAccountId`
   - DPP `testEnvironmentId` = read from document path: `testEnvironmentId`
   - DPP `prodEnvironmentId` = read from document path: `prodEnvironmentId`
   - DPP `userSsoGroups` = read from document path: `userSsoGroups`
   - DPP `userEmail` = read from document path: `userEmail`
   - DPP `targetEnvironmentId` = same value as `prodEnvironmentId` (required by `strip-connections-for-copy.groovy`)

3. **Decision — Validate Admin Tier**
   - Condition: `userSsoGroups` DPP does NOT contain `"ABC_BOOMI_FLOW_ADMIN"`
   - **True path (error)**: Map error response with `success = false`, `errorCode = "UNAUTHORIZED"`, `errorMessage = "Only ADMIN tier users can copy extensions across environments"`. Connect to Return Documents.
   - **False path (authorized)**: Go to step 4
   - Rationale: copying extensions from Test to Prod is a high-impact operation that modifies all non-connection extension values in the production environment; admin-only gate is mandatory

4. **HTTP Client Send — GET EnvironmentExtensions from Test**
   - Connector: `PROMO - HTTP Connection`
   - Operation: `PROMO - HTTP Op - GET EnvironmentExtensions`
   - Add header/parameter `overrideAccount = {clientAccountId}` DPP
   - URL path uses `{testEnvironmentId}` DPP (the source)
   - The response is the full EnvironmentExtensions JSON for the Test environment

5. **Data Process — strip-connections-for-copy.groovy**
   - Add a **Data Process** shape referencing `strip-connections-for-copy.groovy` (from `/integration/scripts/`)
   - The script reads the DPP `targetEnvironmentId` (prod environment ID) before processing
   - The script performs these transformations on the GET response:
     - Removes the `connections` section entirely — connections are environment-specific and admin-managed
     - Removes the `PGPCertificates` section — certificate bindings are environment-specific
     - Counts encrypted fields with `encryptedValueSet = true` that cannot be copied (their values are not returned by the GET API)
     - Swaps `extensions.environmentId` and `extensions.id` to `targetEnvironmentId` (prod)
     - Sets `extensions.partial = true` on the output object
     - Sets DPPs: `sectionsExcluded` (comma-separated), `fieldsCopied` (count), `encryptedFieldsSkipped` (count)
   - Output is the cleaned, prod-targeted JSON body ready for the UPDATE call

6. **HTTP Client Send — UPDATE EnvironmentExtensions to Prod**
   - Connector: `PROMO - HTTP Connection`
   - Operation: `PROMO - HTTP Op - UPDATE EnvironmentExtensions`
   - Add header/parameter `overrideAccount = {clientAccountId}` DPP
   - URL path uses `{prodEnvironmentId}` DPP (the target)
   - The request body is the output from step 5 (connections stripped, `partial=true` set)
   - Wrap in a Try/Catch; if HTTP error → set DPP `copyFailed = true`

7. **Decision — Check Copy Result**
   - Condition: DPP `copyFailed` is `"true"`
   - **True path (error)**: Map error response with `success = false`, `errorCode = "COPY_FAILED"`. Connect to Return Documents.
   - **False path (success)**: Go to step 8

8. **Map — Build copyExtensionsTestToProdResponse JSON**
   - Destination: `PROMO - Profile - CopyExtensionsTestToProdResponse`
   - Map `sectionsExcluded` from DPP
   - Map `fieldsCopied` from DPP (integer)
   - Map `encryptedFieldsSkipped` from DPP (integer)
   - Map `testEnvironmentId` from DPP
   - Map `prodEnvironmentId` from DPP
   - Set `success = true`

9. **Return Documents**

#### Dynamic Process Properties

| Name | Type | Persist | Purpose |
|------|------|---------|---------|
| `clientAccountId` | String | false | Target client sub-account ID; passed to `overrideAccount` |
| `testEnvironmentId` | String | false | Source Test environment ID for the GET call |
| `prodEnvironmentId` | String | false | Target Production environment ID for the UPDATE call |
| `targetEnvironmentId` | String | false | Must match `prodEnvironmentId`; read by `strip-connections-for-copy.groovy` |
| `userSsoGroups` | String (JSON array) | false | SSO groups for admin tier validation |
| `userEmail` | String | false | Requesting user email; for audit trail |
| `sectionsExcluded` | String | false | Set by strip script: comma-separated excluded sections (e.g., "connections,PGPCertificates") |
| `fieldsCopied` | String | false | Set by strip script: count of copyable fields in the payload |
| `encryptedFieldsSkipped` | String | false | Set by strip script: count of encrypted fields that could not be copied |
| `copyFailed` | String | false | Set to "true" if the UPDATE HTTP call fails |

#### Error Codes

| Error Code | Trigger Condition |
|------------|-------------------|
| `UNAUTHORIZED` | User is not ADMIN tier (SSO group `ABC_BOOMI_FLOW_ADMIN` not present) |
| `EXTENSION_NOT_FOUND` | Test environment ID not found in the Platform API (HTTP 404 on GET) |
| `COPY_FAILED` | UPDATE to production environment fails (HTTP error on step 6) |
| `AUTH_FAILED` | Platform API authentication failure on GET or UPDATE |

#### Verify

- As an ADMIN user, trigger a copy from a Test environment that has process property extensions configured
- **Expected**: response with `success = true`, `sectionsExcluded` containing `"connections"` and `"PGPCertificates"`, `fieldsCopied > 0`
- Verify the Production environment now has the same process property values as Test (via `getExtensions` on the prod environment)
- As a CONTRIBUTOR user, attempt the same copy
- **Expected**: response with `success = false` and `errorCode = "UNAUTHORIZED"`
- If the Test environment has encrypted fields (passwords set), verify `encryptedFieldsSkipped > 0` in the response

---

### Process O: Update Map Extension (`PROMO - Update Map Extension`)

This process saves map extension changes for a specified client account environment. **Phase 2 feature — currently returns `MAP_EXTENSION_READONLY` for all requests.** Map extension updates are destructive (omitted mappings and functions are deleted), so Phase 1 provides read-only access and Test-to-Prod copy only. Full editing is enabled in Phase 2 with field-level granularity controls.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - UpdateMapExtensionRequest` | `/integration/profiles/updateMapExtension-request.json` |
| `PROMO - Profile - UpdateMapExtensionResponse` | `/integration/profiles/updateMapExtension-response.json` |

The request JSON contains:
- `clientAccountId` (string): target client sub-account ID
- `environmentId` (string): target environment ID
- `mapExtensionId` (string): map extension ID from the summary query (Process L)
- `mapExtensionPayload` (string): JSON-serialized map extension update
- `userSsoGroups` (array of strings): for access validation
- `userEmail` (string): for audit trail

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `mapExtensionId` (string): echoed back
- `mapName` (string): name of the map extension

#### FSS Operation

Create `PROMO - FSS Op - UpdateMapExtension` per the pattern in Section 3.B, using `PROMO - Profile - UpdateMapExtensionRequest` and `PROMO - Profile - UpdateMapExtensionResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - UpdateMapExtension`

2. **Set Properties** (read request fields)
   - DPP `clientAccountId` = read from document path: `clientAccountId`
   - DPP `environmentId` = read from document path: `environmentId`
   - DPP `mapExtensionId` = read from document path: `mapExtensionId`
   - DPP `mapExtensionPayload` = read from document path: `mapExtensionPayload`

3. **Decision — Phase 2 Feature Flag**
   - Condition: Phase 2 is not enabled (always true in Phase 1 — implement as a hardcoded Decision that always routes to the error path)
   - **True path (Phase 1 — always)**: Go to step 3a
   - **False path (Phase 2 — future)**: Go to step 4
   - **3a. Map — Return MAP_EXTENSION_READONLY**:
     - Set `success = false`
     - Set `errorCode = "MAP_EXTENSION_READONLY"`
     - Set `errorMessage = "Map extension editing is not yet available. Use Test-to-Prod copy for map extensions."`
     - Map `mapExtensionId` from DPP
     - Connect to Return Documents

4. **(Phase 2 — future) HTTP Client Send — UPDATE EnvironmentMapExtension**
   - Connector: `PROMO - HTTP Connection`
   - Operation: `PROMO - HTTP Op - UPDATE EnvironmentMapExtension`
   - Add header/parameter `overrideAccount = {clientAccountId}` DPP
   - URL path includes `{environmentId}` and `{mapExtensionId}` DPPs
   - Request body = `mapExtensionPayload` DPP content

5. **(Phase 2 — future) Map — Build updateMapExtensionResponse JSON**
   - Destination: `PROMO - Profile - UpdateMapExtensionResponse`
   - Map `mapExtensionId` from DPP
   - Map `mapName` from HTTP response
   - Set `success = true`

6. **Return Documents**

#### Dynamic Process Properties

| Name | Type | Persist | Purpose |
|------|------|---------|---------|
| `clientAccountId` | String | false | Target client sub-account ID; passed to `overrideAccount` in Phase 2 |
| `environmentId` | String | false | Target environment ID; used in Phase 2 API URL |
| `mapExtensionId` | String | false | Map extension ID from request; echoed in error response |

#### Phase 1 Behavior

In Phase 1, the Decision shape at step 3 always routes to the error path. The process canvas still defines steps 4 and 5 as documented (for Phase 2 readiness), but they are unreachable. When enabling Phase 2:
1. Update the Decision shape condition to check a configuration flag (e.g., an environment extension value or a hardcoded DPP)
2. Route the false path to step 4
3. Re-deploy the process

#### Error Codes

| Error Code | Trigger Condition |
|------------|-------------------|
| `MAP_EXTENSION_READONLY` | Always returned in Phase 1 (feature not yet enabled) |
| `INVALID_REQUEST` | (Phase 2) Required fields missing from request |
| `AUTH_FAILED` | (Phase 2) Platform API authentication failure |

#### Verify

- Send any `updateMapExtension` request in Phase 1
- **Expected**: response with `success = false`, `errorCode = "MAP_EXTENSION_READONLY"`, and `mapExtensionId` echoed back
- Confirm that `getExtensions` still returns map extension summaries correctly (read path unaffected by Phase 1 write restriction)

---

Prev: [Phase 7 Overview](23-phase7-extension-editor-overview.md) | Next: [Extension Flow Service & Dashboard](25-extension-flow-service-and-dashboard.md) | [Back to Index](index.md)

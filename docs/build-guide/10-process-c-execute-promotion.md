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

---
Prev: [Process B: Resolve Dependencies](09-process-b-resolve-dependencies.md) | Next: [Process D: Package and Deploy](11-process-d-package-and-deploy.md) | [Back to Index](index.md)

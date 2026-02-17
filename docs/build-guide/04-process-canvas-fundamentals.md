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

##### Via API

JSON profiles can be created programmatically via `POST /Component` with `type="profile.json"`. However, there is no API equivalent for the UI's "Import from JSON" feature — the profile element XML must be constructed manually.

**Recommended workflow:** Create one profile in the UI using the import steps below, then export it via `GET /Component/{profileId}` to capture the internal XML structure. Use that XML as a template for the remaining 25 profiles by modifying field names and types.

**Template** (after capturing XML from a UI-created profile):

```bash
# Linux/macOS — create a JSON profile from exported XML template
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Profile - {ProfileName}" type="profile.json" folderFullPath="/Promoted/Profiles">
  <bns:object>
    <!-- Paste exported profile element XML here -->
  </bns:object>
</bns:Component>'
```

```powershell
# Windows — create a JSON profile from exported XML template
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
    Accept         = "application/xml"
}
$body = @'
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Profile - {ProfileName}" type="profile.json" folderFullPath="/Promoted/Profiles">
  <bns:object>
    <!-- Paste exported profile element XML here -->
  </bns:object>
</bns:Component>
'@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" `
  -Method POST -Headers $headers -Body $body
```

See [Appendix D: API Automation Guide](22-api-automation-guide.md#api-first-discovery-workflow) for the complete export/import workflow and a batch creation script.

##### Via UI (Manual Fallback)

1. Navigate to **Build --> New Component --> Profile --> JSON**
2. Name the profile using the exact name from the master component list (e.g., `PROMO - Profile - ManageMappingsRequest`)
3. Click **Import** and select the corresponding file from `/integration/profiles/` (e.g., `manageMappings-request.json`)
4. Boomi parses the JSON and creates the profile element tree automatically
5. Click **Save**
6. Repeat for each of the 26 profiles listed in the master component table:

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
| `PROMO - Profile - QueryPeerReviewQueueRequest` | `queryPeerReviewQueue-request.json` |
| `PROMO - Profile - QueryPeerReviewQueueResponse` | `queryPeerReviewQueue-response.json` |
| `PROMO - Profile - SubmitPeerReviewRequest` | `submitPeerReview-request.json` |
| `PROMO - Profile - SubmitPeerReviewResponse` | `submitPeerReview-response.json` |
| `PROMO - Profile - GenerateComponentDiffRequest` | `generateComponentDiff-request.json` |
| `PROMO - Profile - GenerateComponentDiffResponse` | `generateComponentDiff-response.json` |
| `PROMO - Profile - ListIntegrationPacksRequest` | `listIntegrationPacks-request.json` |
| `PROMO - Profile - ListIntegrationPacksResponse` | `listIntegrationPacks-response.json` |
| `PROMO - Profile - QueryTestDeploymentsRequest` | `queryTestDeployments-request.json` |
| `PROMO - Profile - QueryTestDeploymentsResponse` | `queryTestDeployments-response.json` |
| `PROMO - Profile - CancelTestDeploymentRequest` | `cancelTestDeployment-request.json` |
| `PROMO - Profile - CancelTestDeploymentResponse` | `cancelTestDeployment-response.json` |

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

Each process requires a corresponding FSS Operation component that links it to a message action in the Flow Service. Create all 13 before building the process canvases, or create each one just before its process.

##### Via API

FSS Operations can be created via `POST /Component` with `type="connector-action"` and `subType="flowservicesserver"`.

**Template:**

```bash
# Linux/macOS — create an FSS Operation
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{FSS_OPERATION_NAME}" type="connector-action" subType="flowservicesserver" folderFullPath="/Promoted/Operations">
  <bns:object>
    <bns:serviceType>MESSAGE_ACTION</bns:serviceType>
    <bns:requestProfileId>{requestProfileComponentId}</bns:requestProfileId>
    <bns:responseProfileId>{responseProfileComponentId}</bns:responseProfileId>
  </bns:object>
</bns:Component>'
```

```powershell
# Windows — create an FSS Operation
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
    Accept         = "application/xml"
}
$body = @'
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{FSS_OPERATION_NAME}" type="connector-action" subType="flowservicesserver" folderFullPath="/Promoted/Operations">
  <bns:object>
    <bns:serviceType>MESSAGE_ACTION</bns:serviceType>
    <bns:requestProfileId>{requestProfileComponentId}</bns:requestProfileId>
    <bns:responseProfileId>{responseProfileComponentId}</bns:responseProfileId>
  </bns:object>
</bns:Component>
'@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" `
  -Method POST -Headers $headers -Body $body
```

Replace `{requestProfileComponentId}` and `{responseProfileComponentId}` with the component IDs returned when creating the corresponding profiles. Use the lookup table below to match FSS operations to their profiles.

> **Note:** The exact XML structure for FSS operation configuration may vary — use the [API-First Discovery Workflow](22-api-automation-guide.md#api-first-discovery-workflow) to capture precise XML from a UI-created operation if the template above does not work directly.

See [Appendix D: API Automation Guide](22-api-automation-guide.md) for a batch creation script covering all 13 operations.

##### Via UI (Manual Fallback)

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
| `PROMO - FSS Op - QueryPeerReviewQueue` | `PROMO - Profile - QueryPeerReviewQueueRequest` | `PROMO - Profile - QueryPeerReviewQueueResponse` | `queryPeerReviewQueue` |
| `PROMO - FSS Op - SubmitPeerReview` | `PROMO - Profile - SubmitPeerReviewRequest` | `PROMO - Profile - SubmitPeerReviewResponse` | `submitPeerReview` |
| `PROMO - FSS Op - GenerateComponentDiff` | `PROMO - Profile - GenerateComponentDiffRequest` | `PROMO - Profile - GenerateComponentDiffResponse` | `generateComponentDiff` |
| `PROMO - FSS Op - ListIntegrationPacks` | `PROMO - Profile - ListIntegrationPacksRequest` | `PROMO - Profile - ListIntegrationPacksResponse` | `listIntegrationPacks` |
| `PROMO - FSS Op - QueryTestDeployments` | `PROMO - Profile - QueryTestDeploymentsRequest` | `PROMO - Profile - QueryTestDeploymentsResponse` | `queryTestDeployments` |
| `PROMO - FSS Op - CancelTestDeployment` | `PROMO - Profile - CancelTestDeploymentRequest` | `PROMO - Profile - CancelTestDeploymentResponse` | `cancelTestDeployment` |

#### Return Documents Shape

Every process ends with a **Return Documents** shape. This sends the final response JSON document back through the FSS listener to the Flow application. No special configuration is needed — drag it onto the canvas and connect the last shape to it.

#### Error Response Pattern

When a process encounters an error, build the error response JSON with `success = false`, an `errorCode`, and an `errorMessage`. Use a Map shape to construct this JSON from DPPs. The Flow application checks the `success` field in every response to decide whether to continue or show an error.

---

### 3.D — API-First Discovery Workflow

When creating components programmatically, the internal XML structure is often undocumented or varies by connector type. The recommended approach — endorsed by Boomi documentation — is the "GET first" pattern:

1. **Create a skeleton component in the UI** — build one representative component (e.g., one profile, one operation) using the manual steps above
2. **Export via API** — call `GET /Component/{componentId}` to retrieve the full internal XML:

```bash
# Linux/macOS — export a component's full XML
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{componentId}" > component-template.xml
```

```powershell
# Windows — export a component's full XML
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization = "Basic $cred"
    Accept        = "application/xml"
}
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component/{componentId}" `
  -Method GET -Headers $headers -OutFile "component-template.xml"
```

3. **Use as template** — modify the exported XML (change `name`, remove `componentId` and `version`, adjust fields) and POST it to create new components
4. **Batch create** — loop through a list of component definitions, substituting unique values into the template

This workflow is especially valuable for:
- **26 JSON profiles** — create one, export, template the remaining 25
- **19 HTTP Client operations** — create one, export, template the remaining 18
- **13 FSS operations** — create one, export, template the remaining 12
- **Cross-account migration** — export all components from one account, recreate in another

See [Appendix D: API Automation Guide](22-api-automation-guide.md) for complete batch creation scripts and the dependency-ordered workflow.

---

---
Prev: [Phase 2b: DataHub Connection Setup](03-datahub-connection-setup.md) | Next: [Process F: Mapping CRUD](05-process-f-mapping-crud.md) | [Back to Index](index.md)

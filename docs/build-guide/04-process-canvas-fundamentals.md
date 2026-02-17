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

---
Prev: [Phase 2b: DataHub Connection Setup](03-datahub-connection-setup.md) | Next: [Process F: Mapping CRUD](05-process-f-mapping-crud.md) | [Back to Index](index.md)

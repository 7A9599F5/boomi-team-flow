## Phase 4: Flow Service Component

### Step 4.1 -- Create Flow Service

Reference: `/integration/flow-service/flow-service-spec.md`

#### Via API

The Flow Service component can be created via `POST /Component` with `type="flowservice"`. The component XML includes the service path, external name, message actions (referencing FSS operations and profiles by component ID), and configuration values.

> **Note:** All FSS operations and profiles must exist before creating the Flow Service, because the component XML references them by component ID. If you built Phase 3 components via API and captured their IDs, you can construct the Flow Service XML programmatically.

```bash
# Linux/macOS — create Flow Service component
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Flow Service" type="flowservice" folderFullPath="/Promoted">
  <bns:object>
    <bns:pathToService>/fs/PromotionService</bns:pathToService>
    <bns:externalName>PromotionService</bns:externalName>
    <bns:messageActions>
      <!-- 20 message actions, each referencing FSS operation + profiles by component ID -->
      <!-- Use GET /Component on a UI-created Flow Service to capture exact XML structure -->
    </bns:messageActions>
    <bns:configurationValues>
      <bns:configValue name="primaryAccountId" type="String" required="true" />
    </bns:configurationValues>
  </bns:object>
</bns:Component>'
```

```powershell
# Windows — create Flow Service component
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
    Accept         = "application/xml"
}
$body = @'
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Flow Service" type="flowservice" folderFullPath="/Promoted">
  <bns:object>
    <bns:pathToService>/fs/PromotionService</bns:pathToService>
    <bns:externalName>PromotionService</bns:externalName>
    <bns:messageActions>
      <!-- 20 message actions — use API-First Discovery Workflow to capture exact XML -->
    </bns:messageActions>
    <bns:configurationValues>
      <bns:configValue name="primaryAccountId" type="String" required="true" />
    </bns:configurationValues>
  </bns:object>
</bns:Component>
'@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/Component" `
  -Method POST -Headers $headers -Body $body
```

> **Recommended:** Flow Service XML is complex (20 message actions with cross-references). Use the [API-First Discovery Workflow](22-api-automation-guide.md#api-first-discovery-workflow): create the Flow Service in the UI, export via `GET /Component/{flowServiceId}`, and store the XML as a template for future recreation.

#### Via UI (Manual Fallback)

1. Navigate to **Build -> New Component -> Flow Service**.
2. Name: `PROMO - Flow Service`.
3. On the **General** tab, configure:
   - **Path to Service**: `/fs/PromotionService`
   - **External Name**: `PromotionService`
4. Open the **Message Actions** tab. Add 20 actions, linking each to its FSS Operation, Request Profile, and Response Profile:

| # | Action Name | FSS Operation | Request Profile | Response Profile |
|---|-------------|---------------|-----------------|------------------|
| 1 | `getDevAccounts` | `PROMO - FSS Op - GetDevAccounts` | `PROMO - Profile - GetDevAccountsRequest` | `PROMO - Profile - GetDevAccountsResponse` |
| 2 | `listDevPackages` | `PROMO - FSS Op - ListDevPackages` | `PROMO - Profile - ListDevPackagesRequest` | `PROMO - Profile - ListDevPackagesResponse` |
| 3 | `resolveDependencies` | `PROMO - FSS Op - ResolveDependencies` | `PROMO - Profile - ResolveDependenciesRequest` | `PROMO - Profile - ResolveDependenciesResponse` |
| 4 | `executePromotion` | `PROMO - FSS Op - ExecutePromotion` | `PROMO - Profile - ExecutePromotionRequest` | `PROMO - Profile - ExecutePromotionResponse` |
| 5 | `packageAndDeploy` | `PROMO - FSS Op - PackageAndDeploy` | `PROMO - Profile - PackageAndDeployRequest` | `PROMO - Profile - PackageAndDeployResponse` |
| 6 | `queryStatus` | `PROMO - FSS Op - QueryStatus` | `PROMO - Profile - QueryStatusRequest` | `PROMO - Profile - QueryStatusResponse` |
| 7 | `manageMappings` | `PROMO - FSS Op - ManageMappings` | `PROMO - Profile - ManageMappingsRequest` | `PROMO - Profile - ManageMappingsResponse` |
| 8 | `queryPeerReviewQueue` | `PROMO - FSS Op - QueryPeerReviewQueue` | `PROMO - Profile - QueryPeerReviewQueueRequest` | `PROMO - Profile - QueryPeerReviewQueueResponse` |
| 9 | `submitPeerReview` | `PROMO - FSS Op - SubmitPeerReview` | `PROMO - Profile - SubmitPeerReviewRequest` | `PROMO - Profile - SubmitPeerReviewResponse` |
| 10 | `listIntegrationPacks` | `PROMO - FSS Op - ListIntegrationPacks` | `PROMO - Profile - ListIntegrationPacksRequest` | `PROMO - Profile - ListIntegrationPacksResponse` |
| 11 | `generateComponentDiff` | `PROMO - FSS Op - GenerateComponentDiff` | `PROMO - Profile - GenerateComponentDiffRequest` | `PROMO - Profile - GenerateComponentDiffResponse` |
| 12 | `queryTestDeployments` | `PROMO - FSS Op - QueryTestDeployments` | `PROMO - Profile - QueryTestDeploymentsRequest` | `PROMO - Profile - QueryTestDeploymentsResponse` |
| 13 | `cancelTestDeployment` | `PROMO - FSS Op - CancelTestDeployment` | `PROMO - Profile - CancelTestDeploymentRequest` | `PROMO - Profile - CancelTestDeploymentResponse` |
| 14 | `withdrawPromotion` | `PROMO - FSS Op - WithdrawPromotion` | `PROMO - Profile - WithdrawPromotionRequest` | `PROMO - Profile - WithdrawPromotionResponse` |

5. Open the **Configuration Values** tab. Add a configuration value:
   - **Name**: `primaryAccountId`
   - **Type**: String
   - **Required**: Yes
   - **Description**: Primary Boomi account ID passed to every integration process via Dynamic Process Properties
6. Save the component.

### Step 4.2 -- Deploy Flow Service

#### Via API

Packaging and deployment can be performed entirely via the Platform API:

**Step 1: Create PackagedComponent**

```bash
# Linux/macOS — package the Flow Service
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/PackagedComponent" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{
  "componentId": "{flowServiceComponentId}",
  "packageVersion": "1.0.0",
  "notes": "Initial Flow Service deployment",
  "shareable": true
}'
```

```powershell
# Windows — package the Flow Service
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/json"
    Accept         = "application/json"
}
$body = @'
{
  "componentId": "{flowServiceComponentId}",
  "packageVersion": "1.0.0",
  "notes": "Initial Flow Service deployment",
  "shareable": true
}
'@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/PackagedComponent" `
  -Method POST -Headers $headers -Body $body
```

Capture the `packageId` from the response.

**Step 2: Deploy to environment**

```bash
# Linux/macOS — deploy to target environment
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DeployedPackage" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{
  "packageId": "{packageId}",
  "environmentId": "{environmentId}"
}'
```

```powershell
# Windows — deploy to target environment
$body = @'
{
  "packageId": "{packageId}",
  "environmentId": "{environmentId}"
}
'@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DeployedPackage" `
  -Method POST -Headers $headers -Body $body
```

**Step 3: Set configuration value**

> **Note:** Configuration value setting after deployment is done via the Atom Management API. Navigate to the Atom Management UI to set `primaryAccountId`, or use the Atom Management API if available in your environment.

#### Via UI (Manual Fallback)

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
9. Navigate to **Runtime Management -> Listeners**. All 20 FSS Operations should appear and show a running status:
   - `PROMO - FSS Op - GetDevAccounts`
   - `PROMO - FSS Op - ListDevPackages`
   - `PROMO - FSS Op - ResolveDependencies`
   - `PROMO - FSS Op - ExecutePromotion`
   - `PROMO - FSS Op - PackageAndDeploy`
   - `PROMO - FSS Op - QueryStatus`
   - `PROMO - FSS Op - ManageMappings`
   - `PROMO - FSS Op - QueryPeerReviewQueue`
   - `PROMO - FSS Op - SubmitPeerReview`
   - `PROMO - FSS Op - ListIntegrationPacks`
   - `PROMO - FSS Op - GenerateComponentDiff`
   - `PROMO - FSS Op - QueryTestDeployments`
   - `PROMO - FSS Op - CancelTestDeployment`
   - `PROMO - FSS Op - WithdrawPromotion`
   - `PROMO - FSS Op - ListClientAccounts`
   - `PROMO - FSS Op - GetExtensions`
   - `PROMO - FSS Op - UpdateExtensions`
   - `PROMO - FSS Op - CopyExtensionsTestToProd`
   - `PROMO - FSS Op - UpdateMapExtension`
   - `PROMO - FSS Op - CheckReleaseStatus`
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

---
Prev: [Process G: Component Diff & Build Order](13-process-g-component-diff.md) | Next: [Phase 5a: Flow Dashboard — Developer Swimlane](15-flow-dashboard-developer.md) | [Back to Index](index.md)

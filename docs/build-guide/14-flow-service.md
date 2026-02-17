## Phase 4: Flow Service Component

### Step 4.1 -- Create Flow Service

Reference: `/integration/flow-service/flow-service-spec.md`

1. Navigate to **Build -> New Component -> Flow Service**.
2. Name: `PROMO - Flow Service`.
3. On the **General** tab, configure:
   - **Path to Service**: `/fs/PromotionService`
   - **External Name**: `PromotionService`
4. Open the **Message Actions** tab. Add 11 actions, linking each to its FSS Operation, Request Profile, and Response Profile:

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
9. Navigate to **Runtime Management -> Listeners**. All 11 FSS Operations should appear and show a running status:
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

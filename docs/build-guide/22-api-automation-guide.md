## Appendix D: API Automation Guide

This appendix consolidates all API-based creation commands into a dependency-ordered workflow for automated or semi-automated system setup. Each step includes ready-to-use `curl` (Linux/macOS) and PowerShell (Windows) commands.

> **Relationship to the Build Guide:** Each build phase (01-14) documents "Via UI" creation instructions with detailed screenshots and configuration tables. This appendix provides the complete automation sequence and batch scripts for teams that prefer programmatic setup. Use the phase-specific files for first-time understanding; use this appendix for repeatable, scriptable provisioning.

---

### Prerequisites

| Requirement | How to Obtain |
|-------------|---------------|
| Primary Boomi Account ID | Settings -> Account Information -> Account ID |
| Platform API Token | Settings -> Account Information -> Platform API Tokens -> Generate New Token |
| DataHub Repository ID | Services -> DataHub -> Repositories -> select repo -> URL contains repository ID |
| Partner API Enabled | Settings -> Account Information -> verify "Partner API enabled" checkbox |
| MDM API Privileges | Account must have DataHub/MDM license and API access |
| Public Cloud Atom | Manage -> Atom Management -> verify a public cloud atom is provisioned |

---

### Authentication Setup

#### Environment Variables (Recommended)

Set these once per session to avoid repeating credentials in every command.

**Linux/macOS (bash):**

```bash
export BOOMI_USER="BOOMI_TOKEN.user@company.com"
export BOOMI_TOKEN="your-api-token"
export BOOMI_ACCOUNT="your-primary-account-id"
export BOOMI_REPO="your-repository-id"
export BOOMI_AUTH="$BOOMI_USER:$BOOMI_TOKEN"
```

**Windows (PowerShell):**

```powershell
$env:BOOMI_USER = "BOOMI_TOKEN.user@company.com"
$env:BOOMI_TOKEN = "your-api-token"
$env:BOOMI_ACCOUNT = "your-primary-account-id"
$env:BOOMI_REPO = "your-repository-id"
$BoomiCred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$env:BOOMI_USER`:$env:BOOMI_TOKEN"))
$BoomiHeaders = @{ Authorization = "Basic $BoomiCred"; "Content-Type" = "application/json" }
$BoomiHeadersXml = @{ Authorization = "Basic $BoomiCred"; "Content-Type" = "application/xml" }
```

> All commands in this appendix use these environment variables. Replace with literal values if not using variables. The username format is always `BOOMI_TOKEN.{email}`, not the email alone.

---

### Dependency-Ordered Creation Workflow

The complete system can be created in this order. Each step depends on all previous steps completing successfully.

```
Step 1:  DataHub Repository
Step 2:  DataHub Sources (3)
Step 3:  DataHub Models (5) -> Publish -> Deploy
Step 4:  Folder Structure
Step 5:  JSON Profiles (42)
Step 6:  HTTP Client Connection
Step 7:  HTTP Client Operations (28)
Step 8:  DataHub Connection
Step 9:  DataHub Operations (11)
Step 10: FSS Operations (21)
Step 11: Integration Processes (20)
Step 12: Flow Service
Step 13: Package + Deploy Flow Service
Step 14: Phase 7 DataHub Models (2) -> Publish -> Deploy
Step 15: Phase 7 HTTP Client Operations (8)
Step 16: Phase 7 DataHub Operations (4)
Step 17: Phase 7 JSON Profiles (10)
Step 18: Phase 7 FSS Operations (5)
Step 19: Phase 7 Integration Processes (5)
Step 20: Redeploy Flow Service (v2.0.0)
```

---

#### Step 1 -- Create DataHub Repository (if needed)

> Skip this step if your account already has a DataHub repository. The repository ID is visible in the browser URL when viewing a repository in the DataHub UI.

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/mdm/api/rest/v1/$BOOMI_ACCOUNT/repositories" \
  -H "Content-Type: application/json" \
  -d '{"name": "PromotionHub", "description": "Promotion engine data store"}'
```

```powershell
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/rest/v1/$env:BOOMI_ACCOUNT/repositories" `
  -Method POST -Headers $BoomiHeaders `
  -Body '{"name": "PromotionHub", "description": "Promotion engine data store"}'
```

Capture the `repositoryId` from the response and set it in your environment:

```bash
export BOOMI_REPO="returned-repository-id"
```

```powershell
$env:BOOMI_REPO = "returned-repository-id"
```

---

#### Step 2 -- Create DataHub Sources

Create the 3 sources used across all models. Each source is "contribute-only" (data flows in from integration processes, not out).

```bash
# Create PROMOTION_ENGINE source
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/mdm/api/rest/v1/$BOOMI_ACCOUNT/repositories/$BOOMI_REPO/sources" \
  -H "Content-Type: application/json" \
  -d '{"name": "PROMOTION_ENGINE", "type": "contribute-only"}'

# Create ADMIN_SEEDING source
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/mdm/api/rest/v1/$BOOMI_ACCOUNT/repositories/$BOOMI_REPO/sources" \
  -H "Content-Type: application/json" \
  -d '{"name": "ADMIN_SEEDING", "type": "contribute-only"}'

# Create ADMIN_CONFIG source
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/mdm/api/rest/v1/$BOOMI_ACCOUNT/repositories/$BOOMI_REPO/sources" \
  -H "Content-Type: application/json" \
  -d '{"name": "ADMIN_CONFIG", "type": "contribute-only"}'
```

```powershell
# Create PROMOTION_ENGINE source
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/rest/v1/$env:BOOMI_ACCOUNT/repositories/$env:BOOMI_REPO/sources" `
  -Method POST -Headers $BoomiHeaders `
  -Body '{"name": "PROMOTION_ENGINE", "type": "contribute-only"}'

# Create ADMIN_SEEDING source
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/rest/v1/$env:BOOMI_ACCOUNT/repositories/$env:BOOMI_REPO/sources" `
  -Method POST -Headers $BoomiHeaders `
  -Body '{"name": "ADMIN_SEEDING", "type": "contribute-only"}'

# Create ADMIN_CONFIG source
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/rest/v1/$env:BOOMI_ACCOUNT/repositories/$env:BOOMI_REPO/sources" `
  -Method POST -Headers $BoomiHeaders `
  -Body '{"name": "ADMIN_CONFIG", "type": "contribute-only"}'
```

**Source-to-Model Mapping:**

| Source | Used By Models |
|--------|---------------|
| `PROMOTION_ENGINE` | ComponentMapping, PromotionLog |
| `ADMIN_SEEDING` | ComponentMapping |
| `ADMIN_CONFIG` | DevAccountAccess |

---

#### Step 3 -- Create 5 DataHub Models, Publish, and Deploy

Reference: [Phase 1: DataHub Foundation](01-datahub-foundation.md)

Each model follows a 3-step lifecycle: **Create** (POST with fields, match rules, and sources) -> **Publish** -> **Deploy**. The full field definitions, match rules, and source assignments are documented in Phase 1 and in the model spec files under `/datahub/models/`.

**Lifecycle commands (repeat for each model):**

```bash
# 1. Create model (POST with full field definitions)
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/mdm/api/rest/v1/$BOOMI_ACCOUNT/repositories/$BOOMI_REPO/models" \
  -H "Content-Type: application/json" \
  -d @datahub/models/ComponentMapping-model-spec.json

# 2. Publish model
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/mdm/api/rest/v1/$BOOMI_ACCOUNT/repositories/$BOOMI_REPO/models/{modelId}/publish" \
  -H "Content-Type: application/json"

# 3. Deploy model
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/mdm/api/rest/v1/$BOOMI_ACCOUNT/repositories/$BOOMI_REPO/models/{modelId}/deploy" \
  -H "Content-Type: application/json"
```

```powershell
# 1. Create model
$modelBody = Get-Content -Raw "datahub/models/ComponentMapping-model-spec.json"
$result = Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/rest/v1/$env:BOOMI_ACCOUNT/repositories/$env:BOOMI_REPO/models" `
  -Method POST -Headers $BoomiHeaders -Body $modelBody
$modelId = $result.id

# 2. Publish model
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/rest/v1/$env:BOOMI_ACCOUNT/repositories/$env:BOOMI_REPO/models/$modelId/publish" `
  -Method POST -Headers $BoomiHeaders

# 3. Deploy model
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/rest/v1/$env:BOOMI_ACCOUNT/repositories/$env:BOOMI_REPO/models/$modelId/deploy" `
  -Method POST -Headers $BoomiHeaders
```

**Models to create:**

| # | Model Name | Spec File | Fields | Match Fields | Sources |
|---|-----------|-----------|--------|-------------|---------|
| 1 | ComponentMapping | `datahub/models/ComponentMapping-model-spec.json` | 10 | `devComponentId` + `devAccountId` | PROMOTION_ENGINE, ADMIN_SEEDING |
| 2 | DevAccountAccess | `datahub/models/DevAccountAccess-model-spec.json` | 5 | `ssoGroupId` + `devAccountId` | ADMIN_CONFIG |
| 3 | PromotionLog | `datahub/models/PromotionLog-model-spec.json` | 34 | `promotionId` | PROMOTION_ENGINE |
| 4 | ExtensionAccessMapping | `datahub/models/ExtensionAccessMapping-model-spec.json` | 6 | `environmentId` + `prodComponentId` | PROMOTION_ENGINE |
| 5 | ClientAccountConfig | `datahub/models/ClientAccountConfig-model-spec.json` | 7 | `clientAccountId` + `ssoGroupId` | ADMIN_CONFIG |

> Capture the `modelId` from each create response. You will need it for the publish and deploy calls.

---

#### Step 4 -- Create Folder Structure

Create the `/Promoted/` folder hierarchy in the primary account. All promoted components are stored under this root, mirroring the dev account folder structure.

```bash
# Create /Promoted/ root folder
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Folder" \
  -H "Content-Type: application/json" \
  -d '{"name": "Promoted", "parentId": "0"}'

# Create /Promoted/Profiles subfolder
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Folder" \
  -H "Content-Type: application/json" \
  -d '{"name": "Profiles", "parentId": "{promotedFolderId}"}'

# Create /Promoted/Connections subfolder
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Folder" \
  -H "Content-Type: application/json" \
  -d '{"name": "Connections", "parentId": "{promotedFolderId}"}'
```

```powershell
# Create /Promoted/ root folder
$result = Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Folder" `
  -Method POST -Headers $BoomiHeaders `
  -Body '{"name": "Promoted", "parentId": "0"}'
$promotedFolderId = $result.id

# Create /Promoted/Profiles subfolder
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Folder" `
  -Method POST -Headers $BoomiHeaders `
  -Body "{`"name`": `"Profiles`", `"parentId`": `"$promotedFolderId`"}"

# Create /Promoted/Connections subfolder
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Folder" `
  -Method POST -Headers $BoomiHeaders `
  -Body "{`"name`": `"Connections`", `"parentId`": `"$promotedFolderId`"}"
```

> Replace `{promotedFolderId}` with the folder ID returned from the first call. Additional dev-team subfolders (e.g., `/Promoted/DevTeamAlpha/`) are created automatically by Process C during promotion.

---

#### Step 5 -- Create 42 JSON Profiles (Batch)

Reference: [Phase 3: Process Canvas Fundamentals](04-process-canvas-fundamentals.md) for profile import instructions.

Each profile is a `profile.json` type component. The source schema files are in `/integration/profiles/`.

**Template (single profile):**

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Profile - {ProfileName}" type="profile.json" folderFullPath="/Promoted/Profiles">
  <bns:object>
    <!-- Profile JSON schema elements from source file -->
  </bns:object>
</bns:Component>'
```

```powershell
$profileXml = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Profile - {ProfileName}" type="profile.json" folderFullPath="/Promoted/Profiles">
  <bns:object>
    <!-- Profile JSON schema elements from source file -->
  </bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component" `
  -Method POST -Headers $BoomiHeadersXml -Body $profileXml
```

**Complete Profile Inventory (42 profiles):**

| # | Profile Component Name | Source File |
|---|----------------------|-------------|
| 1 | `PROMO - Profile - GetDevAccountsRequest` | `getDevAccounts-request.json` |
| 2 | `PROMO - Profile - GetDevAccountsResponse` | `getDevAccounts-response.json` |
| 3 | `PROMO - Profile - ListDevPackagesRequest` | `listDevPackages-request.json` |
| 4 | `PROMO - Profile - ListDevPackagesResponse` | `listDevPackages-response.json` |
| 5 | `PROMO - Profile - ResolveDependenciesRequest` | `resolveDependencies-request.json` |
| 6 | `PROMO - Profile - ResolveDependenciesResponse` | `resolveDependencies-response.json` |
| 7 | `PROMO - Profile - ExecutePromotionRequest` | `executePromotion-request.json` |
| 8 | `PROMO - Profile - ExecutePromotionResponse` | `executePromotion-response.json` |
| 9 | `PROMO - Profile - PackageAndDeployRequest` | `packageAndDeploy-request.json` |
| 10 | `PROMO - Profile - PackageAndDeployResponse` | `packageAndDeploy-response.json` |
| 11 | `PROMO - Profile - QueryStatusRequest` | `queryStatus-request.json` |
| 12 | `PROMO - Profile - QueryStatusResponse` | `queryStatus-response.json` |
| 13 | `PROMO - Profile - ManageMappingsRequest` | `manageMappings-request.json` |
| 14 | `PROMO - Profile - ManageMappingsResponse` | `manageMappings-response.json` |
| 15 | `PROMO - Profile - QueryPeerReviewQueueRequest` | `queryPeerReviewQueue-request.json` |
| 16 | `PROMO - Profile - QueryPeerReviewQueueResponse` | `queryPeerReviewQueue-response.json` |
| 17 | `PROMO - Profile - SubmitPeerReviewRequest` | `submitPeerReview-request.json` |
| 18 | `PROMO - Profile - SubmitPeerReviewResponse` | `submitPeerReview-response.json` |
| 19 | `PROMO - Profile - ListIntegrationPacksRequest` | `listIntegrationPacks-request.json` |
| 20 | `PROMO - Profile - ListIntegrationPacksResponse` | `listIntegrationPacks-response.json` |
| 21 | `PROMO - Profile - GenerateComponentDiffRequest` | `generateComponentDiff-request.json` |
| 22 | `PROMO - Profile - GenerateComponentDiffResponse` | `generateComponentDiff-response.json` |
| 23 | `PROMO - Profile - QueryTestDeploymentsRequest` | `queryTestDeployments-request.json` |
| 24 | `PROMO - Profile - QueryTestDeploymentsResponse` | `queryTestDeployments-response.json` |
| 25 | `PROMO - Profile - CancelTestDeploymentRequest` | `cancelTestDeployment-request.json` |
| 26 | `PROMO - Profile - CancelTestDeploymentResponse` | `cancelTestDeployment-response.json` |
| 27 | `PROMO - Profile - WithdrawPromotionRequest` | `withdrawPromotion-request.json` |
| 28 | `PROMO - Profile - WithdrawPromotionResponse` | `withdrawPromotion-response.json` |
| 29 | `PROMO - Profile - ListClientAccountsRequest` | `listClientAccounts-request.json` |
| 30 | `PROMO - Profile - ListClientAccountsResponse` | `listClientAccounts-response.json` |
| 31 | `PROMO - Profile - GetExtensionsRequest` | `getExtensions-request.json` |
| 32 | `PROMO - Profile - GetExtensionsResponse` | `getExtensions-response.json` |
| 33 | `PROMO - Profile - UpdateExtensionsRequest` | `updateExtensions-request.json` |
| 34 | `PROMO - Profile - UpdateExtensionsResponse` | `updateExtensions-response.json` |
| 35 | `PROMO - Profile - CopyExtensionsTestToProdRequest` | `copyExtensionsTestToProd-request.json` |
| 36 | `PROMO - Profile - CopyExtensionsTestToProdResponse` | `copyExtensionsTestToProd-response.json` |
| 37 | `PROMO - Profile - UpdateMapExtensionRequest` | `updateMapExtension-request.json` |
| 38 | `PROMO - Profile - UpdateMapExtensionResponse` | `updateMapExtension-response.json` |
| 39 | `PROMO - Profile - CheckReleaseStatusRequest` | `checkReleaseStatus-request.json` |
| 40 | `PROMO - Profile - CheckReleaseStatusResponse` | `checkReleaseStatus-response.json` |
| 41 | `PROMO - Profile - ValidateScriptRequest` | `validateScript-request.json` |
| 42 | `PROMO - Profile - ValidateScriptResponse` | `validateScript-response.json` |

> **Recommended workflow:** Create one profile manually in the UI by importing the JSON schema, then export it via `GET /Component/{id}` to capture the internal XML representation. Use that exported XML as a template for the remaining 41 profiles. See [API-First Discovery Workflow](#api-first-discovery-workflow) below.

---

#### Step 6 -- Create HTTP Client Connection

Reference: [Phase 2a: HTTP Client Setup](02-http-client-setup.md), Step 2.1

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component" \
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
$connXml = @"
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
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component" `
  -Method POST -Headers $BoomiHeadersXml -Body $connXml
```

> **Note:** The password is supplied in plaintext and encrypted on save by the platform. Connection testing has no API equivalent. To validate the connection works, make a direct curl call: `curl -s -u "$BOOMI_AUTH" "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/ComponentMetadata/{anyComponentId}"` -- a 200 response confirms the credentials are valid.

---

#### Step 7 -- Create 28 HTTP Client Operations (Batch)

Reference: [Phase 2a: HTTP Client Setup](02-http-client-setup.md), Step 2.2

Each operation is a `connector-action` type component with subType `http`. All 28 operations use the `PROMO - Partner API Connection` from Step 6.

**Template (single operation):**

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{operationName}" type="connector-action" subType="http" folderFullPath="/Promoted/Operations">
  <bns:object>
    <!-- Operation-specific configuration (method, URL, headers) -->
  </bns:object>
</bns:Component>'
```

```powershell
$opXml = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{operationName}" type="connector-action" subType="http" folderFullPath="/Promoted/Operations">
  <bns:object>
    <!-- Operation-specific configuration (method, URL, headers) -->
  </bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component" `
  -Method POST -Headers $BoomiHeadersXml -Body $opXml
```

**Complete HTTP Client Operation Inventory (28 operations):**

| # | Component Name | Method | Request URL | Content-Type |
|---|---------------|--------|-------------|-------------|
| 1 | `PROMO - HTTP Op - GET Component` | GET | `/partner/api/rest/v1/{1}/Component/{2}` | `application/xml` |
| 2 | `PROMO - HTTP Op - POST Component Create` | POST | `/partner/api/rest/v1/{1}/Component~{2}` | `application/xml` |
| 3 | `PROMO - HTTP Op - POST Component Update` | POST | `/partner/api/rest/v1/{1}/Component/{2}~{3}` | `application/xml` |
| 4 | `PROMO - HTTP Op - GET ComponentReference` | GET | `/partner/api/rest/v1/{1}/ComponentReference/{2}` | `application/xml` |
| 5 | `PROMO - HTTP Op - GET ComponentMetadata` | GET | `/partner/api/rest/v1/{1}/ComponentMetadata/{2}` | `application/xml` |
| 6 | `PROMO - HTTP Op - QUERY PackagedComponent` | POST | `/partner/api/rest/v1/{1}/PackagedComponent/query` | `application/xml` |
| 7 | `PROMO - HTTP Op - POST PackagedComponent` | POST | `/partner/api/rest/v1/{1}/PackagedComponent` | `application/json` |
| 8 | `PROMO - HTTP Op - GET ReleaseIntegrationPackStatus` | GET | `/partner/api/rest/v1/{1}/ReleaseIntegrationPackStatus/{2}` | `application/json` |
| 9 | `PROMO - HTTP Op - POST IntegrationPack` | POST | `/partner/api/rest/v1/{1}/IntegrationPack` | `application/json` |
| 10 | `PROMO - HTTP Op - POST Branch` | POST | `/partner/api/rest/v1/{1}/Branch` | `application/json` |
| 11 | `PROMO - HTTP Op - QUERY Branch` | POST | `/partner/api/rest/v1/{1}/Branch/query` | `application/json` |
| 12 | `PROMO - HTTP Op - POST MergeRequest` | POST | `/partner/api/rest/v1/{1}/MergeRequest` | `application/json` |
| 13 | `PROMO - HTTP Op - POST MergeRequest Execute` | POST | `/partner/api/rest/v1/{1}/MergeRequest/execute/{2}` | `application/json` |
| 14 | `PROMO - HTTP Op - GET Branch` | GET | `/partner/api/rest/v1/{1}/Branch/{2}` | `application/json` |
| 15 | `PROMO - HTTP Op - DELETE Branch` | DELETE | `/partner/api/rest/v1/{1}/Branch/{2}` | `application/json` |
| 16 | `PROMO - HTTP Op - QUERY IntegrationPack` | POST | `/partner/api/rest/v1/{1}/IntegrationPack/query` | `application/xml` |
| 17 | `PROMO - HTTP Op - POST Add To IntegrationPack` | POST | `/partner/api/rest/v1/{1}/IntegrationPack/{2}/PackagedComponent/{3}` | `application/json` |
| 18 | `PROMO - HTTP Op - POST ReleaseIntegrationPack` | POST | `/partner/api/rest/v1/{1}/ReleaseIntegrationPack` | `application/json` |
| 19 | `PROMO - HTTP Op - GET MergeRequest` | GET | `/partner/api/rest/v1/{1}/MergeRequest/{2}` | `application/json` |
| 20 | `PROMO - HTTP Op - GET IntegrationPack` | GET | `/partner/api/rest/v1/{1}/IntegrationPack/{2}` | `application/json` |
| 21 | `PROMO - HTTP Op - QUERY Account` | POST | `/partner/api/rest/v1/{1}/Account/query` | `application/json` |
| 22 | `PROMO - HTTP Op - QUERY Environment` | POST | `/partner/api/rest/v1/{1}/Environment/query` | `application/json` |
| 23 | `PROMO - HTTP Op - GET EnvironmentExtensions` | GET | `/partner/api/rest/v1/{1}/EnvironmentExtensions/{2}` | `application/json` |
| 24 | `PROMO - HTTP Op - UPDATE EnvironmentExtensions` | POST | `/partner/api/rest/v1/{1}/EnvironmentExtensions/{2}/update` | `application/json` |
| 25 | `PROMO - HTTP Op - QUERY EnvironmentMapExtensionsSummary` | POST | `/partner/api/rest/v1/{1}/EnvironmentMapExtensions/{2}/query` | `application/json` |
| 26 | `PROMO - HTTP Op - GET EnvironmentMapExtension` | GET | `/partner/api/rest/v1/{1}/EnvironmentMapExtension/{2}` | `application/json` |
| 27 | `PROMO - HTTP Op - UPDATE EnvironmentMapExtension` | POST | `/partner/api/rest/v1/{1}/EnvironmentMapExtension/{2}/update` | `application/json` |
| 28 | `PROMO - HTTP Op - QUERY ComponentReference` | POST | `/partner/api/rest/v1/{1}/ComponentReference/query` | `application/json` |

> **Recommended workflow:** Create operation #1 (`GET Component`) manually in the UI, then export via `GET /Component/{id}` to capture the internal XML. Use that as a template, modifying the name, method, URL, and headers for each subsequent operation. The internal XML structure for connector-action components is not publicly documented, making the export-first approach essential.

---

#### Step 8 -- Create DataHub Connection

Reference: [Phase 2b: DataHub Connection Setup](03-datahub-connection-setup.md), Step 2.3

> **Manual step required:** The DataHub authentication token must be retrieved from the UI first: Services -> DataHub -> Repositories -> [your repo] -> Configure tab -> Authentication Token. This token cannot be generated via API.

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - DataHub Connection" type="connector-settings" subType="mdm" folderFullPath="/Promoted/Connections">
  <bns:object>
    <bns:hubToken>{datahub-auth-token}</bns:hubToken>
    <bns:repositoryId>{repositoryId}</bns:repositoryId>
  </bns:object>
</bns:Component>'
```

```powershell
$dhConnXml = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - DataHub Connection" type="connector-settings" subType="mdm" folderFullPath="/Promoted/Connections">
  <bns:object>
    <bns:hubToken>{datahub-auth-token}</bns:hubToken>
    <bns:repositoryId>{repositoryId}</bns:repositoryId>
  </bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component" `
  -Method POST -Headers $BoomiHeadersXml -Body $dhConnXml
```

> Replace `{datahub-auth-token}` with the token from the DataHub UI and `{repositoryId}` with your repository ID.

---

#### Step 9 -- Create 11 DataHub Operations (Batch)

Reference: [Phase 2b: DataHub Connection Setup](03-datahub-connection-setup.md), Step 2.4

Each DataHub operation is a `connector-action` component with subType `mdm`. All 11 use the `PROMO - DataHub Connection` from Step 8.

**Template (single operation):**

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{operationName}" type="connector-action" subType="mdm" folderFullPath="/Promoted/Operations">
  <bns:object>
    <!-- DataHub operation config (model, action type) -->
  </bns:object>
</bns:Component>'
```

```powershell
$dhOpXml = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{operationName}" type="connector-action" subType="mdm" folderFullPath="/Promoted/Operations">
  <bns:object>
    <!-- DataHub operation config (model, action type) -->
  </bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component" `
  -Method POST -Headers $BoomiHeadersXml -Body $dhOpXml
```

**Complete DataHub Operation Inventory (11 operations):**

| # | Component Name | Model | Action |
|---|---------------|-------|--------|
| 1 | `PROMO - DH Op - Query ComponentMapping` | ComponentMapping | QUERY |
| 2 | `PROMO - DH Op - Update ComponentMapping` | ComponentMapping | UPDATE |
| 3 | `PROMO - DH Op - Delete ComponentMapping` | ComponentMapping | DELETE |
| 4 | `PROMO - DH Op - Query DevAccountAccess` | DevAccountAccess | QUERY |
| 5 | `PROMO - DH Op - Query PromotionLog` | PromotionLog | QUERY |
| 6 | `PROMO - DH Op - Update PromotionLog` | PromotionLog | UPDATE |
| 7 | `PROMO - DH Op - Delete PromotionLog` | PromotionLog | DELETE |
| 8 | `PROMO - DH Op - Query ExtensionAccessMapping` | ExtensionAccessMapping | QUERY |
| 9 | `PROMO - DH Op - Update ExtensionAccessMapping` | ExtensionAccessMapping | UPDATE |
| 10 | `PROMO - DH Op - Query ClientAccountConfig` | ClientAccountConfig | QUERY |
| 11 | `PROMO - DH Op - Update ClientAccountConfig` | ClientAccountConfig | UPDATE |

> **Recommended workflow:** Create operation #1 manually (Build -> New Component -> Connector -> Operation -> Boomi DataHub), import the model profile, export via `GET /Component/{id}`, and use the exported XML as a template for the remaining 10.

---

#### Step 10 -- Create 21 FSS Operations (Batch)

Reference: [Phase 4: Flow Service Component](14-flow-service.md)

Each FSS Operation is a `connector-action` component with subType `flowservice`. These are the operations that the Flow Service links to message actions.

**Template (single FSS operation):**

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{fssOpName}" type="connector-action" subType="flowservice" folderFullPath="/Promoted/Operations">
  <bns:object>
    <!-- FSS operation config -->
  </bns:object>
</bns:Component>'
```

```powershell
$fssOpXml = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="{fssOpName}" type="connector-action" subType="flowservice" folderFullPath="/Promoted/Operations">
  <bns:object>
    <!-- FSS operation config -->
  </bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component" `
  -Method POST -Headers $BoomiHeadersXml -Body $fssOpXml
```

**Complete FSS Operation Inventory (21 operations):**

| # | Component Name | Linked Process | Action Name |
|---|---------------|---------------|-------------|
| 1 | `PROMO - FSS Op - GetDevAccounts` | Process A0 | `getDevAccounts` |
| 2 | `PROMO - FSS Op - ListDevPackages` | Process A | `listDevPackages` |
| 3 | `PROMO - FSS Op - ResolveDependencies` | Process B | `resolveDependencies` |
| 4 | `PROMO - FSS Op - ExecutePromotion` | Process C | `executePromotion` |
| 5 | `PROMO - FSS Op - PackageAndDeploy` | Process D | `packageAndDeploy` |
| 6 | `PROMO - FSS Op - QueryStatus` | Process E | `queryStatus` |
| 7 | `PROMO - FSS Op - ManageMappings` | Process F | `manageMappings` |
| 8 | `PROMO - FSS Op - QueryPeerReviewQueue` | Process E2 | `queryPeerReviewQueue` |
| 9 | `PROMO - FSS Op - SubmitPeerReview` | Process E3 | `submitPeerReview` |
| 10 | `PROMO - FSS Op - ListIntegrationPacks` | Process J | `listIntegrationPacks` |
| 11 | `PROMO - FSS Op - GenerateComponentDiff` | Process G | `generateComponentDiff` |
| 12 | `PROMO - FSS Op - QueryTestDeployments` | Process E4 | `queryTestDeployments` |
| 13 | `PROMO - FSS Op - CancelTestDeployment` | Process E4 | `cancelTestDeployment` |
| 14 | `PROMO - FSS Op - WithdrawPromotion` | Process E5 | `withdrawPromotion` |
| 15 | `PROMO - FSS Op - ListClientAccounts` | Process K | `listClientAccounts` |
| 16 | `PROMO - FSS Op - GetExtensions` | Process L | `getExtensions` |
| 17 | `PROMO - FSS Op - UpdateExtensions` | Process M | `updateExtensions` |
| 18 | `PROMO - FSS Op - CopyExtensionsTestToProd` | Process N | `copyExtensionsTestToProd` |
| 19 | `PROMO - FSS Op - UpdateMapExtension` | Process O | `updateMapExtension` |
| 20 | `PROMO - FSS Op - CheckReleaseStatus` | Process P | `checkReleaseStatus` |
| 21 | `PROMO - FSS Op - ValidateScript` | Process Q | `validateScript` |

---

#### Step 11 -- Create 20 Integration Processes

Reference: Build guide files [05](05-process-f-mapping-crud.md) through [13](13-process-g-component-diff.md)

> **Important:** Process canvas XML is an undocumented internal format and is extremely complex. Raw process XML templates are not provided because they would be unreliable without Boomi instance access for validation. The recommended workflow is:
>
> 1. Build each process manually following the Phase 3 build step files (05-13)
> 2. Export each completed process via `GET /Component/{processId}` to capture the internal XML
> 3. Store the exported XML as a template for automated recreation in other accounts
>
> See [API-First Discovery Workflow](#api-first-discovery-workflow) for the export pattern.

**Process Build Order (simplest to most complex):**

| # | Process | Letter Code | Build Guide |
|---|---------|------------|-------------|
| 1 | Mapping CRUD | F | [05-process-f-mapping-crud.md](05-process-f-mapping-crud.md) |
| 2 | Get Dev Accounts | A0 | [06-process-a0-get-dev-accounts.md](06-process-a0-get-dev-accounts.md) |
| 3 | Query Status | E | [07-process-e-status-and-review.md](07-process-e-status-and-review.md) |
| 4 | List Dev Packages | A | [08-process-a-list-dev-packages.md](08-process-a-list-dev-packages.md) |
| 5 | Resolve Dependencies | B | [09-process-b-resolve-dependencies.md](09-process-b-resolve-dependencies.md) |
| 6 | Execute Promotion | C | [10-process-c-execute-promotion.md](10-process-c-execute-promotion.md) |
| 7 | Package and Deploy | D | [11-process-d-package-and-deploy.md](11-process-d-package-and-deploy.md) |
| 8 | List Integration Packs | J | [12-process-j-list-integration-packs.md](12-process-j-list-integration-packs.md) |
| 9 | Component Diff | G | [13-process-g-component-diff.md](13-process-g-component-diff.md) |
| 10-12 | E2, E3, E4 | E2/E3/E4 | Extended from Process E; see [07](07-process-e-status-and-review.md) |
| 13 | Withdraw Promotion | E5 | Extended from Process E; see [07](07-process-e-status-and-review.md) |
| 14 | List Client Accounts | K | [20-extension-editor.md](20-extension-editor.md) |
| 15 | Get Extensions | L | [20-extension-editor.md](20-extension-editor.md) |
| 16 | Update Extensions | M | [20-extension-editor.md](20-extension-editor.md) |
| 17 | Copy Extensions Test to Prod | N | [20-extension-editor.md](20-extension-editor.md) |
| 18 | Update Map Extension | O | [20-extension-editor.md](20-extension-editor.md) |
| 19 | Check Release Status | P | [11-process-d-package-and-deploy.md](11-process-d-package-and-deploy.md) |
| 20 | Validate Script | Q | [24-extension-processes.md](24-extension-processes.md) |

**Export a completed process:**

```bash
curl -s -u "$BOOMI_AUTH" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component/{processComponentId}" \
  > process-template-{letterCode}.xml
```

```powershell
$result = Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component/{processComponentId}" `
  -Method GET -Headers @{ Authorization = "Basic $BoomiCred"; Accept = "application/xml" }
$result | Out-File "process-template-{letterCode}.xml" -Encoding UTF8
```

**Recreate a process from exported XML:**

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d @process-template-{letterCode}.xml
```

```powershell
$processXml = Get-Content -Raw "process-template-{letterCode}.xml"
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component" `
  -Method POST -Headers $BoomiHeadersXml -Body $processXml
```

> **Caveat:** Exported process XML contains embedded component IDs (connections, operations, profiles). When recreating in a different account, you must update all embedded IDs to match the new account's components. This is a manual find-and-replace step.

---

#### Step 12 -- Create Flow Service

Reference: [Phase 4: Flow Service Component](14-flow-service.md)

The Flow Service is a `flowservice` type component that links 21 message actions to their FSS Operations and profiles.

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component" \
  -H "Content-Type: application/xml" -H "Accept: application/xml" \
  -d '<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Flow Service" type="flowservice" folderFullPath="/Promoted">
  <bns:object>
    <bns:servicePath>/fs/PromotionService</bns:servicePath>
    <bns:externalName>PromotionService</bns:externalName>
    <!-- Message action definitions linking FSS operations to profiles -->
  </bns:object>
</bns:Component>'
```

```powershell
$fsXml = @"
<bns:Component xmlns:bns="http://api.platform.boomi.com/" name="PROMO - Flow Service" type="flowservice" folderFullPath="/Promoted">
  <bns:object>
    <bns:servicePath>/fs/PromotionService</bns:servicePath>
    <bns:externalName>PromotionService</bns:externalName>
    <!-- Message action definitions linking FSS operations to profiles -->
  </bns:object>
</bns:Component>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component" `
  -Method POST -Headers $BoomiHeadersXml -Body $fsXml
```

> **Recommended workflow:** Build the Flow Service in the UI following [Phase 4](14-flow-service.md) to link all 21 message actions correctly, then export with `GET /Component/{id}` to capture the complete XML for future automation.

---

#### Step 13 -- Package and Deploy Flow Service

After the Flow Service component is created and saved, package it and deploy to the public cloud atom.

**Create PackagedComponent:**

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/PackagedComponent" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{
  "componentId": "{flowServiceComponentId}",
  "packageVersion": "1.0.0",
  "notes": "Initial Flow Service deployment",
  "shareable": true
}'
```

```powershell
$packageBody = @"
{
  "componentId": "{flowServiceComponentId}",
  "packageVersion": "1.0.0",
  "notes": "Initial Flow Service deployment",
  "shareable": true
}
"@
$pkgResult = Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/PackagedComponent" `
  -Method POST -Headers $BoomiHeaders -Body $packageBody
$packageId = $pkgResult.packageId
```

**Deploy to environment:**

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/DeployedPackage" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{
  "packageId": "{packageId}",
  "environmentId": "{targetEnvironmentId}"
}'
```

```powershell
$deployBody = @"
{
  "packageId": "$packageId",
  "environmentId": "{targetEnvironmentId}"
}
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/DeployedPackage" `
  -Method POST -Headers $BoomiHeaders -Body $deployBody
```

**Post-deployment configuration:**

After deployment, set the `primaryAccountId` configuration value via the Boomi UI:

1. Navigate to Manage -> Atom Management -> select the public cloud atom.
2. Open Properties -> Configuration Values.
3. Set `primaryAccountId` to your primary Boomi account ID.
4. Save and verify all 21 listeners appear in Runtime Management -> Listeners.

> The `primaryAccountId` configuration value cannot be set via API -- it must be configured in the Atom Management UI after deployment.

---

### API-First Discovery Workflow

The Platform API's internal XML format for component configuration is undocumented. The recommended approach for programmatic component creation is the "GET first" pattern:

1. **Create a skeleton component in the UI** -- configure it manually with all required settings.
2. **Export via API** -- retrieve the full internal XML representation.
3. **Use as template** -- modify the exported XML (name, IDs, settings) for batch creation.
4. **Validate** -- verify each created component in the UI before relying on it.

This is the officially recommended approach per Boomi documentation. The internal XML format varies by component type and may change between platform releases.

**Export a component:**

```bash
curl -s -u "$BOOMI_AUTH" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component/{componentId}" \
  > component-template.xml
```

```powershell
$result = Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component/{componentId}" `
  -Method GET -Headers @{ Authorization = "Basic $BoomiCred"; Accept = "application/xml" }
$result | Out-File "component-template.xml" -Encoding UTF8
```

**Key fields to modify when reusing a template:**

| Field | What to Change |
|-------|---------------|
| `name` | New component name |
| `componentId` | Remove entirely (omit for create) or set to target ID (for update) |
| `version` | Remove or set to `0` for new components |
| `folderFullPath` | Update if targeting a different folder |
| Embedded component references | Replace with IDs from the target account |

---

### Profile XML Generation (Alternative to Export-First)

The setup tool includes a built-in JSON-to-XML profile generator that eliminates the need for the export-first workflow for JSON profiles. Instead of manually creating a template profile in the UI, the generator reads the JSON schema files directly and produces valid Boomi Component XML.

**How it works:**

1. Reads a JSON schema file from `integration/profiles/` (e.g., `executePromotion-request.json`)
2. Infers Boomi data types from example values (string→character, integer→number, boolean, datetime)
3. Generates a complete `<bns:Component type="profile.json">` XML with proper `<JSONProfile>` structure
4. Sequential key numbering, correct nesting for objects and arrays

**Usage via setup tool:**

```bash
# The setup tool's step 3.1 (CreateProfiles) uses the generator automatically
python -m setup setup
```

**Manual generation (Python):**

```python
from setup.generators.profile_xml import generate_profile_xml
import json

with open("integration/profiles/executePromotion-request.json") as f:
    schema = json.load(f)

xml = generate_profile_xml(schema, "PROMO - Profile - ExecutePromotionRequest", "PROMO/Profiles")
print(xml)
```

> **When to use export-first instead:** For non-JSON profile types (XML, Flat File, EDI, Database), the export-first approach is still required as the generator only supports JSON profiles.

---

### Script Creation (Automated)

The setup tool can automatically create all 11 Groovy process scripts from the source files in `integration/scripts/`. Each `.groovy` file is wrapped in the proper `<bns:Component type="script.processing">` XML envelope with CDATA content.

**Scripts created:**

| # | Component Name | Source File |
|---|---------------|-------------|
| 1 | `PROMO - Script - BuildVisitedSet` | `build-visited-set.groovy` |
| 2 | `PROMO - Script - SortByDependency` | `sort-by-dependency.groovy` |
| 3 | `PROMO - Script - StripEnvConfig` | `strip-env-config.groovy` |
| 4 | `PROMO - Script - ValidateConnectionMappings` | `validate-connection-mappings.groovy` |
| 5 | `PROMO - Script - RewriteReferences` | `rewrite-references.groovy` |
| 6 | `PROMO - Script - NormalizeXml` | `normalize-xml.groovy` |
| 7 | `PROMO - Script - FilterAlreadyPromoted` | `filter-already-promoted.groovy` |
| 8 | `PROMO - Script - BuildExtensionAccessCache` | `build-extension-access-cache.groovy` |
| 9 | `PROMO - Script - StripConnectionsForCopy` | `strip-connections-for-copy.groovy` |
| 10 | `PROMO - Script - MergeExtensionData` | `merge-extension-data.groovy` |
| 11 | `PROMO - Script - ValidateScript` | `validate-script.groovy` |

**Usage via setup tool:**

```bash
# Step 3.1b (CreateScripts) runs automatically during setup
python -m setup setup
```

> **Note:** Scripts are created as `processscript` type with `groovy2` language. The script content is preserved exactly as-is inside a CDATA block.

---

### Batch Creation Script Pattern

For steps that create many similar components (profiles, operations), use a loop with rate-limiting to stay within API limits.

**Bash batch loop:**

```bash
#!/bin/bash
# Batch create HTTP Client operations from a definition array.
# Each entry: "name|method|url|contentType"
# Requires: BOOMI_AUTH, BOOMI_ACCOUNT, and a valid operation XML template.

OPERATIONS=(
  "PROMO - HTTP Op - GET Component|GET|/partner/api/rest/v1/{1}/Component/{2}|application/xml"
  "PROMO - HTTP Op - POST Component Create|POST|/partner/api/rest/v1/{1}/Component~{2}|application/xml"
  "PROMO - HTTP Op - POST Component Update|POST|/partner/api/rest/v1/{1}/Component/{2}~{3}|application/xml"
  "PROMO - HTTP Op - GET ComponentReference|GET|/partner/api/rest/v1/{1}/ComponentReference/{2}|application/xml"
  "PROMO - HTTP Op - GET ComponentMetadata|GET|/partner/api/rest/v1/{1}/ComponentMetadata/{2}|application/xml"
  "PROMO - HTTP Op - QUERY PackagedComponent|POST|/partner/api/rest/v1/{1}/PackagedComponent/query|application/xml"
  "PROMO - HTTP Op - POST PackagedComponent|POST|/partner/api/rest/v1/{1}/PackagedComponent|application/json"
  "PROMO - HTTP Op - GET ReleaseIntegrationPackStatus|GET|/partner/api/rest/v1/{1}/ReleaseIntegrationPackStatus/{2}|application/json"
  "PROMO - HTTP Op - POST IntegrationPack|POST|/partner/api/rest/v1/{1}/IntegrationPack|application/json"
  "PROMO - HTTP Op - POST Branch|POST|/partner/api/rest/v1/{1}/Branch|application/json"
  "PROMO - HTTP Op - QUERY Branch|POST|/partner/api/rest/v1/{1}/Branch/query|application/json"
  "PROMO - HTTP Op - POST MergeRequest|POST|/partner/api/rest/v1/{1}/MergeRequest|application/json"
  "PROMO - HTTP Op - POST MergeRequest Execute|POST|/partner/api/rest/v1/{1}/MergeRequest/execute/{2}|application/json"
  "PROMO - HTTP Op - GET Branch|GET|/partner/api/rest/v1/{1}/Branch/{2}|application/json"
  "PROMO - HTTP Op - DELETE Branch|DELETE|/partner/api/rest/v1/{1}/Branch/{2}|application/json"
  "PROMO - HTTP Op - QUERY IntegrationPack|POST|/partner/api/rest/v1/{1}/IntegrationPack/query|application/xml"
  "PROMO - HTTP Op - POST Add To IntegrationPack|POST|/partner/api/rest/v1/{1}/IntegrationPack/{2}/PackagedComponent/{3}|application/json"
  "PROMO - HTTP Op - POST ReleaseIntegrationPack|POST|/partner/api/rest/v1/{1}/ReleaseIntegrationPack|application/json"
  "PROMO - HTTP Op - GET MergeRequest|GET|/partner/api/rest/v1/{1}/MergeRequest/{2}|application/json"
  "PROMO - HTTP Op - GET IntegrationPack|GET|/partner/api/rest/v1/{1}/IntegrationPack/{2}|application/json"
)

TEMPLATE_FILE="operation-template.xml"

for op in "${OPERATIONS[@]}"; do
  IFS='|' read -r name method url contentType <<< "$op"

  # Substitute placeholders in the template
  body=$(sed \
    -e "s|{OPERATION_NAME}|$name|g" \
    -e "s|{HTTP_METHOD}|$method|g" \
    -e "s|{REQUEST_URL}|$url|g" \
    -e "s|{CONTENT_TYPE}|$contentType|g" \
    "$TEMPLATE_FILE")

  # Create the component
  response=$(curl -s -u "$BOOMI_AUTH" \
    -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component" \
    -H "Content-Type: application/xml" -H "Accept: application/xml" \
    -d "$body")

  echo "Created: $name"

  # Rate limit: 120ms gap (~8 req/s with safety margin)
  sleep 0.12
done
```

**PowerShell batch loop:**

```powershell
# Batch create HTTP Client operations
# Requires: $BoomiCred, $env:BOOMI_ACCOUNT, and a valid operation XML template

$operations = @(
    @{ Name = "PROMO - HTTP Op - GET Component"; Method = "GET"; Url = "/partner/api/rest/v1/{1}/Component/{2}"; ContentType = "application/xml" }
    @{ Name = "PROMO - HTTP Op - POST Component Create"; Method = "POST"; Url = "/partner/api/rest/v1/{1}/Component~{2}"; ContentType = "application/xml" }
    @{ Name = "PROMO - HTTP Op - POST Component Update"; Method = "POST"; Url = "/partner/api/rest/v1/{1}/Component/{2}~{3}"; ContentType = "application/xml" }
    # ... (add all 28 operations)
)

$templateXml = Get-Content -Raw "operation-template.xml"

foreach ($op in $operations) {
    $body = $templateXml `
        -replace '\{OPERATION_NAME\}', $op.Name `
        -replace '\{HTTP_METHOD\}', $op.Method `
        -replace '\{REQUEST_URL\}', $op.Url `
        -replace '\{CONTENT_TYPE\}', $op.ContentType

    $result = Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component" `
        -Method POST `
        -Headers @{ Authorization = "Basic $BoomiCred"; "Content-Type" = "application/xml"; Accept = "application/xml" } `
        -Body $body

    Write-Host "Created: $($op.Name)"

    # Rate limit: 120ms gap
    Start-Sleep -Milliseconds 120
}
```

---

### Export/Import Pattern

To replicate the complete system from one Boomi account to another:

**1. Export all components from the source account:**

```bash
#!/bin/bash
# Export all PROMO components from the source account

COMPONENT_IDS=("id1" "id2" "id3")  # Populate with actual component IDs

mkdir -p exported-components

for id in "${COMPONENT_IDS[@]}"; do
  curl -s -u "$BOOMI_AUTH" \
    -H "Accept: application/xml" \
    "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component/$id" \
    > "exported-components/$id.xml"
  echo "Exported: $id"
  sleep 0.12
done
```

```powershell
# Export all PROMO components from the source account

$componentIds = @("id1", "id2", "id3")  # Populate with actual component IDs

New-Item -ItemType Directory -Force -Path "exported-components" | Out-Null

foreach ($id in $componentIds) {
    $result = Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component/$id" `
        -Method GET -Headers @{ Authorization = "Basic $BoomiCred"; Accept = "application/xml" }
    $result | Out-File "exported-components/$id.xml" -Encoding UTF8
    Write-Host "Exported: $id"
    Start-Sleep -Milliseconds 120
}
```

**2. Import into the target account:**

Before importing, you must:

1. **Remove `componentId` attributes** from each XML file (the target account assigns new IDs).
2. **Update embedded component references** -- connections, operations, and profiles referenced by ID within process XML must be mapped to the target account's component IDs.
3. **Update `folderFullPath`** if folder structure differs.

```bash
#!/bin/bash
# Import components into the target account

TARGET_ACCOUNT="target-account-id"
TARGET_AUTH="BOOMI_TOKEN.admin@company.com:target-api-token"

for xmlfile in exported-components/*.xml; do
  curl -s -u "$TARGET_AUTH" \
    -X POST "https://api.boomi.com/partner/api/rest/v1/$TARGET_ACCOUNT/Component" \
    -H "Content-Type: application/xml" -H "Accept: application/xml" \
    -d @"$xmlfile"
  echo "Imported: $xmlfile"
  sleep 0.12
done
```

```powershell
# Import components into the target account

$targetAccount = "target-account-id"
$targetCred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.admin@company.com:target-api-token"))

Get-ChildItem "exported-components/*.xml" | ForEach-Object {
    $body = Get-Content -Raw $_.FullName
    Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$targetAccount/Component" `
        -Method POST `
        -Headers @{ Authorization = "Basic $targetCred"; "Content-Type" = "application/xml"; Accept = "application/xml" } `
        -Body $body
    Write-Host "Imported: $($_.Name)"
    Start-Sleep -Milliseconds 120
}
```

> **ID Mapping:** Keep a spreadsheet or JSON file mapping source component IDs to target component IDs. You will need this mapping to update cross-references in process XML before importing.

---

### Verification Checklist

After completing all steps, run these verification commands to confirm every component category exists.

#### 1. Verify DataHub Models

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/mdm/api/v1/repositories/$BOOMI_REPO/models/ComponentMapping/records/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="1"><view><fieldId>devComponentId</fieldId></view></RecordQueryRequest>'
```

```powershell
$queryBody = '<RecordQueryRequest limit="1"><view><fieldId>devComponentId</fieldId></view></RecordQueryRequest>'
Invoke-RestMethod -Uri "https://api.boomi.com/mdm/api/v1/repositories/$env:BOOMI_REPO/models/ComponentMapping/records/query" `
  -Method POST -Headers $BoomiHeadersXml -Body $queryBody
```

Repeat for `DevAccountAccess` and `PromotionLog`. A 200 response (even with zero results) confirms the model is deployed and queryable.

#### 2. Verify Connections

```bash
# Verify HTTP Client connection
curl -s -u "$BOOMI_AUTH" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component/{httpConnectionId}"

# Verify DataHub connection
curl -s -u "$BOOMI_AUTH" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component/{dhConnectionId}"
```

```powershell
# Verify HTTP Client connection
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component/{httpConnectionId}" `
  -Method GET -Headers @{ Authorization = "Basic $BoomiCred"; Accept = "application/xml" }

# Verify DataHub connection
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component/{dhConnectionId}" `
  -Method GET -Headers @{ Authorization = "Basic $BoomiCred"; Accept = "application/xml" }
```

A 200 response with a `<bns:Component>` element confirms the connection exists.

#### 3. Verify Operations (Batch)

```bash
# Query all PROMO operations by name prefix
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component/query" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        { "operator": "STARTS_WITH", "property": "name", "argument": ["PROMO - "] },
        { "operator": "EQUALS", "property": "type", "argument": ["connector-action"] },
        { "operator": "EQUALS", "property": "deleted", "argument": ["false"] }
      ]
    }
  }
}'
```

```powershell
$queryBody = @"
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        { "operator": "STARTS_WITH", "property": "name", "argument": ["PROMO - "] },
        { "operator": "EQUALS", "property": "type", "argument": ["connector-action"] },
        { "operator": "EQUALS", "property": "deleted", "argument": ["false"] }
      ]
    }
  }
}
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component/query" `
  -Method POST -Headers $BoomiHeaders -Body $queryBody
```

Verify `numberOfResults` equals **60** (28 HTTP Client + 11 DataHub + 21 FSS operations).

#### 4. Verify Profiles

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component/query" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        { "operator": "STARTS_WITH", "property": "name", "argument": ["PROMO - Profile"] },
        { "operator": "EQUALS", "property": "type", "argument": ["profile.json"] },
        { "operator": "EQUALS", "property": "deleted", "argument": ["false"] }
      ]
    }
  }
}'
```

```powershell
$queryBody = @"
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        { "operator": "STARTS_WITH", "property": "name", "argument": ["PROMO - Profile"] },
        { "operator": "EQUALS", "property": "type", "argument": ["profile.json"] },
        { "operator": "EQUALS", "property": "deleted", "argument": ["false"] }
      ]
    }
  }
}
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component/query" `
  -Method POST -Headers $BoomiHeaders -Body $queryBody
```

Verify `numberOfResults` equals **42** (21 actions x 2 profiles each).

#### 5. Verify Processes

```bash
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component/query" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        { "operator": "STARTS_WITH", "property": "name", "argument": ["PROMO - "] },
        { "operator": "EQUALS", "property": "type", "argument": ["process"] },
        { "operator": "EQUALS", "property": "deleted", "argument": ["false"] }
      ]
    }
  }
}'
```

```powershell
$queryBody = @"
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        { "operator": "STARTS_WITH", "property": "name", "argument": ["PROMO - "] },
        { "operator": "EQUALS", "property": "type", "argument": ["process"] },
        { "operator": "EQUALS", "property": "deleted", "argument": ["false"] }
      ]
    }
  }
}
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component/query" `
  -Method POST -Headers $BoomiHeaders -Body $queryBody
```

Verify `numberOfResults` equals **20** processes.

#### 6. Verify Flow Service and Listeners

```bash
# Verify Flow Service component exists
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/$BOOMI_ACCOUNT/Component/query" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        { "operator": "EQUALS", "property": "name", "argument": ["PROMO - Flow Service"] },
        { "operator": "EQUALS", "property": "type", "argument": ["flowservice"] }
      ]
    }
  }
}'

# Verify the service is responding
curl -s -u "$BOOMI_AUTH" \
  -X POST "https://{cloud-base-url}/fs/PromotionService" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"action": "getDevAccounts", "request": {"userSsoGroups": ["YOUR_SSO_GROUP_ID"]}}'
```

```powershell
# Verify Flow Service component exists
$queryBody = @"
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        { "operator": "EQUALS", "property": "name", "argument": ["PROMO - Flow Service"] },
        { "operator": "EQUALS", "property": "type", "argument": ["flowservice"] }
      ]
    }
  }
}
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/$env:BOOMI_ACCOUNT/Component/query" `
  -Method POST -Headers $BoomiHeaders -Body $queryBody

# Verify the service is responding
$testBody = '{"action": "getDevAccounts", "request": {"userSsoGroups": ["YOUR_SSO_GROUP_ID"]}}'
Invoke-RestMethod -Uri "https://{cloud-base-url}/fs/PromotionService" `
  -Method POST -Headers $BoomiHeaders -Body $testBody
```

A successful `getDevAccounts` response with `"success": true` confirms the entire stack is operational.

#### Summary Checklist

| Category | Expected Count | Verification Query |
|----------|---------------|-------------------|
| DataHub Models | 5 | Query each model for 200 response |
| DataHub Sources | 3 | Check via DataHub UI |
| Connections | 2 | GET Component for each ID |
| HTTP Client Operations | 28 | STARTS_WITH "PROMO - HTTP Op" |
| DataHub Operations | 11 | STARTS_WITH "PROMO - DH Op" |
| FSS Operations | 21 | STARTS_WITH "PROMO - FSS Op" |
| JSON Profiles | 42 | STARTS_WITH "PROMO - Profile" |
| Integration Processes | 20 | type = "process", STARTS_WITH "PROMO - " |
| Flow Service | 1 | name = "PROMO - Flow Service" |
| **Total Components** | **134** | |

---

### Rate Limiting Reference

All batch operations must respect the Platform API rate limits:

| Parameter | Value |
|-----------|-------|
| Limit | ~10 requests/second |
| Recommended gap | 120ms between consecutive calls (~8 req/s with safety margin) |
| Retry on 429/503 | Up to 3 retries with exponential backoff |
| Backoff schedule | 1st: 1 second, 2nd: 2 seconds, 3rd: 4 seconds |

See [Appendix C: Platform API Reference](21-appendix-platform-api-reference.md) for complete rate limiting and error handling details.

---
Prev: [Appendix C: Platform API Reference](21-appendix-platform-api-reference.md) | Next: [Phase 7: Extension Editor Overview](23-phase7-extension-editor-overview.md) | [Back to Index](index.md)

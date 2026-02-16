# Boomi Component Promotion System - Build Guide

This guide walks through building every component of the Promotion System. Follow the phases in order — each phase builds on the previous.

## Prerequisites

- Primary Boomi account with Partner API enabled
- One or more dev sub-accounts
- Azure AD/Entra SSO configured in Boomi Flow
- Access to DataHub in your Boomi account
- A public Boomi cloud atom (or ability to provision one)

## Repository File Reference

All configuration files, profiles, scripts, and templates are in this repository:

| Directory | Contents |
|-----------|----------|
| `/datahub/models/` | DataHub model specifications (field definitions, match rules) |
| `/datahub/api-requests/` | Test XML for DataHub CRUD validation |
| `/integration/profiles/` | JSON request/response profiles for all 7 processes |
| `/integration/scripts/` | Groovy scripts for XML manipulation |
| `/integration/api-requests/` | API request templates for Platform API calls |
| `/integration/flow-service/` | Flow Service component specification |
| `/flow/` | Flow application structure and page layouts |
| `/docs/` | This guide and architecture reference |

---

## Phase 1: DataHub Foundation

### Step 1.1 — Create ComponentMapping Model

1. Navigate to **DataHub → Models → New Model**
2. Name: `ComponentMapping`, Root Element: `ComponentMapping`
3. Add fields per `/datahub/models/ComponentMapping-model-spec.json`:
   - `devComponentId` (String, match field)
   - `devAccountId` (String, match field)
   - `prodComponentId` (String)
   - `componentName` (String)
   - `componentType` (String)
   - `prodAccountId` (String)
   - `prodLatestVersion` (Number)
   - `lastPromotedAt` (Date, format: `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'`)
   - `lastPromotedBy` (String)
4. Add **match rule**: Exact match on `devComponentId` AND `devAccountId` (compound)
5. Add **source**: `PROMOTION_ENGINE` (contribute-only)
6. Skip data quality steps (we control data quality in Integration)
7. **Save → Publish → Deploy** to repository

### Step 1.2 — Create DevAccountAccess Model

1. Same process as above
2. Name: `DevAccountAccess`, Root Element: `DevAccountAccess`
3. Add fields per `/datahub/models/DevAccountAccess-model-spec.json`:
   - `ssoGroupId` (String, match field)
   - `ssoGroupName` (String)
   - `devAccountId` (String, match field)
   - `devAccountName` (String)
   - `isActive` (String — "true"/"false")
4. Match rule: Exact on `ssoGroupId` + `devAccountId`
5. Source: `ADMIN_CONFIG` (contribute-only)
6. Publish → Deploy to same repository

### Step 1.3 — Create PromotionLog Model

1. Name: `PromotionLog`, Root Element: `PromotionLog`
2. Add fields per `/datahub/models/PromotionLog-model-spec.json`:
   - `promotionId` (String, match field)
   - `devAccountId` (String)
   - `prodAccountId` (String)
   - `devPackageId` (String)
   - `initiatedBy` (String)
   - `initiatedAt` (Date)
   - `status` (String)
   - `componentsTotal` (Number)
   - `componentsCreated` (Number)
   - `componentsUpdated` (Number)
   - `componentsFailed` (Number)
   - `errorMessage` (Long Text, up to 5000 chars)
   - `resultDetail` (Long Text, up to 5000 chars)
3. Match rule: Exact on `promotionId`
4. Source: `PROMOTION_ENGINE`
5. Publish → Deploy

### Step 1.4 — Seed DevAccountAccess Data

Manually create golden records for each SSO group → dev account mapping:

```xml
<batch src="ADMIN_CONFIG">
  <DevAccountAccess>
    <ssoGroupId>YOUR_AZURE_AD_GROUP_ID</ssoGroupId>
    <ssoGroupName>Boomi Dev - Team Alpha</ssoGroupName>
    <devAccountId>YOUR_DEV_ACCOUNT_ID</devAccountId>
    <devAccountName>DevTeamAlpha</devAccountName>
    <isActive>true</isActive>
  </DevAccountAccess>
</batch>
```

### Step 1.5 — Test DataHub CRUD

1. Use `/datahub/api-requests/create-golden-record-test.xml` to POST a test mapping via Repository API
2. Use `/datahub/api-requests/query-golden-record-test.xml` to query it back
3. POST the same record again — verify it **updates** (not duplicates) due to match rule
4. Confirm the repository URL and Hub Auth Token work
5. **Delete the test record** after verification

---

## Phase 2: Integration Connections & Operations

### Step 2.1 — Create HTTP Client Connection (Partner API)

1. **Build → New Component → Connection → HTTP Client**
2. URL: `https://api.boomi.com`
3. Authentication: Basic
4. Username: `BOOMI_TOKEN.{your_email}`
5. Password: your API token (generate in **Settings → Account Information → Platform API Tokens**)
6. **Test connection** — should return 200

### Step 2.2 — Create HTTP Client Operations

Create operations for each API call. Reference templates in `/integration/api-requests/`:

| Operation Name | HTTP Method | Request URL Template | Template File |
|---------------|-------------|---------------------|---------------|
| GET Component | GET | `/partner/api/rest/v1/{1}/Component/{2}` | `get-component.xml` |
| POST Component (Create) | POST | `/partner/api/rest/v1/{1}/Component` | `create-component.xml` |
| POST Component (Update) | POST | `/partner/api/rest/v1/{1}/Component/{2}` | `update-component.xml` |
| GET ComponentReference | GET | `/partner/api/rest/v1/{1}/ComponentReference/{2}` | `query-component-reference.xml` |
| GET ComponentMetadata | GET | `/partner/api/rest/v1/{1}/ComponentMetadata/{2}` | `query-component-metadata.xml` |
| QUERY PackagedComponent | POST | `/partner/api/rest/v1/{1}/PackagedComponent/query` | `query-packaged-components.xml` |
| POST PackagedComponent | POST | `/partner/api/rest/v1/{1}/PackagedComponent` | `create-packaged-component.json` |
| POST DeployedPackage | POST | `/partner/api/rest/v1/{1}/DeployedPackage` | `create-deployed-package.json` |

For each:
1. Build → New Component → Operation → HTTP Client
2. Action: Send
3. Set HTTP Method and Request URL per table
4. Parameters tab: `{1}` = DPP `primaryAccountId`, `{2}` = DPP for specific ID
5. Add `overrideAccount` query parameter where needed
6. Content-Type: `application/xml` (or `application/json` for JSON endpoints)

### Step 2.3 — Create DataHub Connection

1. Build → New Component → Connection → Boomi DataHub
2. Hub Cloud Name: select your cloud region
3. Hub Authentication Token: from DataHub → repository → Configure tab
4. Repository: auto-detected after token entry
5. Test connection

### Step 2.4 — Create DataHub Operations

For each model (ComponentMapping, DevAccountAccess, PromotionLog):
1. **Query Golden Records** operation: import from model
2. **Update Golden Records** operation: import from model
3. Each creates XML request/response profiles automatically

---

## Phase 3: Integration Processes

### General Pattern for All Processes

Each process follows this pattern:
1. **Start shape**: Connector = Boomi Flow Services Server, Action = Listen
2. **Flow Service Operation**: Service Type = Message Action, import JSON request/response profiles
3. Process logic (varies per process)
4. **Return Documents** step: sends response JSON back to Flow

### Step 3.0 — Process A0: Get Dev Accounts

1. Create process: `PROMO - Get Dev Accounts`
2. Import profiles: `/integration/profiles/getDevAccounts-request.json` and `-response.json`
3. Canvas:
   - Start (FSS Listen)
   - → Set Properties (read `userSsoGroups` array from request)
   - → For each SSO group: DataHub Query → DevAccountAccess where `ssoGroupId = group AND isActive = "true"`
   - → Groovy: Deduplicate accounts (a user in multiple groups might access the same account)
   - → Map (build response JSON)
   - → Return Documents

### Step 3.1 — Process A: List Dev Packages

1. Create process: `PROMO - List Dev Packages`
2. Import profiles: `/integration/profiles/listDevPackages-request.json` and `-response.json`
3. Canvas:
   - Start (FSS Listen)
   - → Set Properties (read `devAccountId`)
   - → HTTP Client Send (POST PackagedComponent/query with overrideAccount)
   - → Handle pagination (queryMore token, 120ms gap between pages)
   - → For each package: HTTP Client (GET ComponentMetadata for name)
   - → Map (XML → JSON response)
   - → Return Documents

### Step 3.2 — Process B: Resolve Dependencies

1. Create process: `PROMO - Resolve Dependencies`
2. Import profiles: `/integration/profiles/resolveDependencies-request.json` and `-response.json`
3. Canvas:
   - Start (FSS Listen)
   - → Set Properties (componentId, devAccountId)
   - → Initialize visited set and queue (DPPs)
   - → Loop:
     - HTTP Client GET (ComponentReference with overrideAccount)
     - Groovy: `scripts/build-visited-set.groovy` (manage visited set, queue children)
     - Decision: alreadyVisited? → skip / continue
     - HTTP Client GET (ComponentMetadata)
     - DataHub Query (ComponentMapping — check for existing prod mapping)
     - Mark as NEW or UPDATE
   - → Map (build response JSON with full tree)
   - → Return Documents

### Step 3.3 — Process C: Execute Promotion (Core Engine)

1. Create process: `PROMO - Execute Promotion`
2. Import profiles: `/integration/profiles/executePromotion-request.json` and `-response.json`
3. Canvas (most complex — see `/docs/architecture.md` for full detail):
   - Start → Set Properties
   - → DataHub Update (PromotionLog IN_PROGRESS)
   - → Groovy: `scripts/sort-by-dependency.groovy`
   - → Initialize componentMappingCache DPP (empty JSON object)
   - → For each component (loop):
     - **Try/Catch**:
       - HTTP Client GET (component XML from dev)
       - Groovy: `scripts/strip-env-config.groovy`
       - Check in-memory cache first, then DataHub Query (mapping exists?)
       - Decision: mapping exists?
         - NO → Groovy: `scripts/rewrite-references.groovy` → HTTP Client POST (create)
         - YES → Groovy: `scripts/rewrite-references.groovy` → HTTP Client POST (update)
       - Update in-memory cache with new/updated mapping
     - **Catch**: Log error, mark dependents as SKIPPED
   - → Batch write all mappings to DataHub (single Update Golden Records call)
   - → DataHub Update (PromotionLog COMPLETED/FAILED)
   - → Map (build response JSON)
   - → Return Documents

### Step 3.4 — Process D: Package & Deploy

1. Create process: `PROMO - Package and Deploy`
2. Import profiles: `/integration/profiles/packageAndDeploy-request.json` and `-response.json`
3. Canvas:
   - Start → HTTP Client POST (PackagedComponent with shareable=true)
   - → Decision: createNewPack?
     - YES → HTTP Client POST (IntegrationPack) → add component
     - NO → Add component to existing pack
   - → HTTP Client POST (ReleaseIntegrationPack)
   - → For each target: HTTP Client POST (DeployedPackage)
   - → Return Documents

### Step 3.5 — Process E: Query Status

1. Create process: `PROMO - Query Status`
2. Import profiles: `/integration/profiles/queryStatus-request.json` and `-response.json`
3. Canvas:
   - Start → DataHub Query (PromotionLog, with optional filters)
   - → Map (build response JSON)
   - → Return Documents

### Step 3.6 — Process F: Mapping CRUD

1. Create process: `PROMO - Mapping CRUD`
2. Import profiles: `/integration/profiles/manageMappings-request.json` and `-response.json`
3. Canvas:
   - Start → Decision (operation: list/create/update)
   - List: DataHub Query → Map → Return Documents
   - Create/Update: DataHub Update → Return Documents

---

## Phase 4: Flow Service Component

### Step 4.1 — Create Flow Service

Reference: `/integration/flow-service/flow-service-spec.md`

1. **Build → New Component → Flow Service** → `PROMO - Flow Service`
2. General tab:
   - Path to Service: `/fs/PromotionService`
   - External Name: `PromotionService`
3. Message Actions tab — add 7 actions:
   - `getDevAccounts` → linked to Process A0 FSS Operation
   - `listDevPackages` → linked to Process A FSS Operation
   - `resolveDependencies` → linked to Process B FSS Operation
   - `executePromotion` → linked to Process C FSS Operation
   - `packageAndDeploy` → linked to Process D FSS Operation
   - `queryStatus` → linked to Process E FSS Operation
   - `manageMappings` → linked to Process F FSS Operation
4. Configuration Values: add `primaryAccountId` (String, required)
5. Save

### Step 4.2 — Deploy

1. Create a Packaged Component for the Flow Service
2. Deploy to your **public Boomi cloud atom**
3. Verify in **Runtime Management → Listeners**: all 7 processes should appear
4. Note the full URL: `https://{your-cloud-base-url}/fs/PromotionService`

---

## Phase 5: Flow Dashboard

Reference: `/flow/flow-structure.md` and `/flow/page-layouts/`

### Step 5.1 — Install Connector

1. **Flow → Connectors → New Connector**
2. Type: **Boomi Integration Service**
3. Runtime Type: select your public cloud
4. Path to Service: `/fs/PromotionService`
5. Authentication: Basic (username/token from Shared Web Server User Management)
6. Click **"Retrieve Connector Configuration Data"** → auto-generates Flow Types
7. Set `primaryAccountId` configuration value
8. Install → Save

### Step 5.2 — Create Flow Application

1. **Flow → Build → New Flow** → `Promotion Dashboard`
2. Add **Developer Swimlane**: Authorization = SSO group "Boomi Developers"
3. Add **Admin Swimlane**: Authorization = SSO group "Boomi Admins"
4. Build each page per the layout files:
   - Page 1: Package Browser (`/flow/page-layouts/page1-package-browser.md`)
   - Page 2: Promotion Review (`/flow/page-layouts/page2-promotion-review.md`)
   - Page 3: Promotion Status (`/flow/page-layouts/page3-promotion-status.md`)
   - Page 4: Deployment Submission (`/flow/page-layouts/page4-deployment-submission.md`)
   - Page 5: Approval Queue (`/flow/page-layouts/page5-approval-queue.md`)
   - Page 6: Mapping Viewer (`/flow/page-layouts/page6-mapping-viewer.md`)
5. Wire Message steps to Message Actions (see flow-structure.md)
6. Add Decision steps after each Message step (check `success` field)
7. Add Email notification at swimlane transition (Page 4 → Page 5)

### Step 5.3 — Configure SSO

1. Ensure Azure AD/Entra groups exist:
   - "Boomi Developers" — all dev users
   - "Boomi Admins" — approval administrators
2. Map groups to Flow swimlanes via Identity connector

---

## Phase 6: Testing

### Test 1 — DataHub CRUD
POST test golden record → query → post same record → verify UPSERT (no duplicate)

### Test 2 — Single Component Promotion
Run Flow → select simple package (no dependencies) → promote → verify:
- New component appears in primary account under `/Promoted/{team}/{name}/`
- DataHub has new ComponentMapping golden record
- PromotionLog shows COMPLETED

### Test 3 — Re-Promote (Version Increment)
Promote the same package again → verify:
- Same component updated (not duplicated)
- Version incremented
- DataHub mapping updated with new version + timestamp

### Test 4 — Full Dependency Tree
Package with dependencies (process → connections → profiles) → verify:
- Bottom-up processing order
- All references rewritten correctly
- All components created/updated in primary account

### Test 5 — Approval Workflow
Submit for deployment → log in as admin → approve → verify:
- Integration Pack created/updated
- Components deployed to target environment

### Test 6 — Error Recovery
Promote with intentional failure → verify:
- Failed component logged
- Dependent components marked SKIPPED
- Re-run picks up (creates become updates for already-promoted components)

### Test 7 — Browser Resilience
Start promotion → close browser → reopen same URL → verify state restored

---

## Troubleshooting

### Common Issues

**"No listeners found" after deployment**
- Verify atom is running and has the Flow Service deployed
- Check Runtime Management → Listeners tab
- Ensure the atom is a PUBLIC cloud atom (not private)

**DataHub queries return empty**
- Verify model is published AND deployed to repository
- Check Hub Auth Token is correct
- Verify source name matches exactly

**"overrideAccount not authorized"**
- Verify Partner API is enabled on primary account
- Verify the API token user has Partner-level access
- Verify the dev account is a sub-account of the primary

**Flow "Retrieve Connector Configuration Data" fails**
- Verify the atom is running and Flow Service is deployed
- Check Path to Service matches exactly: `/fs/PromotionService`
- Verify Basic Auth credentials are correct

**Component references not rewritten**
- Check the in-memory mapping cache (componentMappingCache DPP)
- Verify bottom-up sort order is correct
- Check Groovy script logs for rewrite details

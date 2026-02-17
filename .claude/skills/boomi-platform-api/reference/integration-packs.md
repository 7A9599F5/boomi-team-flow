# IntegrationPack Operations

IntegrationPack create, release, deploy lifecycle and operations.

---

## Overview

**IntegrationPacks** bundle multiple PackagedComponents for streamlined deployment across environments and accounts.

**Key Concepts:**
- Group related components (processes, connections, maps, etc.)
- Single deployment unit for multi-component solutions
- Support multi-tenant distribution (`MULTI` installation type)
- Versioned releases with update capabilities

---

## CREATE IntegrationPack

Create a new Integration Pack.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/IntegrationPack
```

**Request Body:**
```json
{
  "name": "Order Processing Pack",
  "description": "Complete order processing solution",
  "installationType": "MULTI"
}
```

**Fields:**
- `name` (required): Pack name (must be unique)
- `description` (optional): Pack description
- `installationType` (required): `MULTI` or `SINGLE`

**Installation Types:**
- **MULTI**: Supports multiple installations (recommended for this project)
- **SINGLE**: Only one installation allowed

**Response:**
```json
{
  "@type": "IntegrationPack",
  "id": "pack-uuid-abc123",
  "name": "Order Processing Pack",
  "description": "Complete order processing solution",
  "installationType": "MULTI",
  "createdDate": "2024-11-20T10:00:00Z",
  "createdBy": "user@boomi.com"
}
```

**Use Case in Process D:**
Create Integration Pack for promoted components.

---

## Add PackagedComponents to Integration Pack

After creating the pack, add PackagedComponents to it.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/IntegrationPack/{packId}/addPackagedComponent
```

**Request Body:**
```json
{
  "packageId": "package-uuid-456"
}
```

**Requirements:**
- PackagedComponent must have `shareable: true`
- PackagedComponent must exist in the same account
- Can add multiple packages (repeat for each)

**Response:**
```json
{
  "@type": "IntegrationPack",
  "id": "pack-uuid-abc123",
  "packages": [
    {"packageId": "package-uuid-456", "packageVersion": "1.2"}
  ]
}
```

**Process D Pattern:**
```javascript
// After creating PackagedComponents
for (const pkg of packagedComponents) {
  await addPackagedComponentToIntegrationPack(packId, pkg.packageId);
}
```

---

## Release IntegrationPack

Release the Integration Pack to make it deployable.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/IntegrationPack/{packId}/release
```

**Request Body:** (empty or minimal)

**Response:**
```json
{
  "@type": "IntegrationPack",
  "id": "pack-uuid-abc123",
  "status": "RELEASED",
  "releaseDate": "2024-11-20T10:10:00Z"
}
```

**Release Lifecycle:**
```
DRAFT → RELEASED → DEPLOYED
```

**Important:**
- Must release before deploying
- Cannot modify pack contents after release
- To update, create new version

---

## Deploy IntegrationPack

Deploy the released pack to target environments.

**Method 1: Deploy via DeployedPackage** (Process D uses this)

```http
POST /partner/api/rest/v1/{accountId}/DeployedPackage
{
  "environmentId": "{envId}",
  "packageId": "{packageId}",
  "notes": "Deployed via Integration Pack"
}
```

**Method 2: Deploy entire pack** (alternative)

```http
POST /partner/api/rest/v1/{accountId}/IntegrationPack/{packId}/deploy
{
  "environmentId": "{envId}"
}
```

Deploys all PackagedComponents in the pack to the target environment.

---

## GET IntegrationPack

Retrieve a specific Integration Pack by ID.

**Endpoint:**
```http
GET /partner/api/rest/v1/{accountId}/IntegrationPack/{packId}
```

**Response:**
```json
{
  "@type": "IntegrationPack",
  "id": "pack-uuid-abc123",
  "name": "Order Processing Pack",
  "description": "...",
  "installationType": "MULTI",
  "status": "RELEASED",
  "packages": [
    {"packageId": "...", "componentId": "...", "packageVersion": "1.2"}
  ]
}
```

---

## QUERY IntegrationPacks

List Integration Packs available to an account.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/IntegrationPack/query
```

**Request Body:**
```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "name",
      "argument": ["Order Processing Pack"]
    }
  }
}
```

**Queryable Fields:**
- `name`, `description`, `installationType`
- `status` (`DRAFT`, `RELEASED`, `DEPLOYED`)
- `createdDate`, `createdBy`

**Important:**
This query returns Integration Packs **available to secondary accounts**, not the primary/publisher account's own packs.

**Use Case in Process J:**
List historical Integration Packs for smart pack suggestions.

---

## IntegrationPack Lifecycle (Process D)

### Step 1: Create or Reuse Integration Pack

**Option A: Create New Pack**
```json
POST /IntegrationPack
{
  "name": "Orders - {timestamp}",
  "description": "Promoted components from DevTeamA",
  "installationType": "MULTI"
}
```

**Option B: Reuse Existing Pack** (recommended)
```javascript
// Query historical packs from PromotionLog
const suggestedPack = await querySuggestedPack(componentFamily);

if (suggestedPack) {
  packId = suggestedPack.integrationPackId;
} else {
  packId = await createIntegrationPack({...});
}
```

### Step 2: Add PackagedComponents

```javascript
for (const component of promotedComponents) {
  // Create PackagedComponent
  const pkg = await createPackagedComponent({
    componentId: component.prodId,
    packageVersion: component.version,
    shareable: true
  });

  // Add to Integration Pack
  await addPackagedComponentToIntegrationPack(packId, pkg.packageId);
}
```

### Step 3: Release Integration Pack

```http
POST /IntegrationPack/{packId}/release
```

### Step 4: Deploy to Environments

```javascript
for (const envId of targetEnvironments) {
  await deployPackage({
    environmentId: envId,
    packageId: pkg.packageId,
    notes: `Deployed from Integration Pack ${packId}`
  });
}
```

---

## Smart Pack Suggestion (Process J)

**Goal:** Suggest Integration Packs based on historical usage.

**Algorithm:**
1. Query PromotionLog for previous promotions of the same component family
2. Extract `integrationPackId` from historical records
3. Query IntegrationPack details for suggested pack
4. Return pack name and ID for user selection

**Example Query (PromotionLog):**
```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "devComponentId", "argument": ["{componentId}"]},
        {"operator": "EQUALS", "property": "reviewStage", "argument": ["APPROVED"]}
      ]
    }
  }
}
```

**Extract Pack:**
```javascript
const historicalPromotions = await queryPromotionLog(filter);
const packIds = [...new Set(historicalPromotions.map(p => p.integrationPackId))];

// Return most recent pack
return packIds[0];
```

---

## Versioning Strategy

### Option 1: One Pack Per Promotion (Not Recommended)

Create a new Integration Pack for each promotion:
```
Order Processing Pack - 2024-11-20
Order Processing Pack - 2024-11-21
Order Processing Pack - 2024-11-22
```

**Drawbacks:**
- Proliferation of packs
- Harder to track lineage
- No clear "current version"

### Option 2: Reuse Pack, Increment Package Versions (Recommended)

Reuse the same Integration Pack, update PackagedComponent versions:
```
Order Processing Pack (pack stays same)
  - OrderProcessor v1.0 → v1.1 → v2.0
  - OrderValidator v1.0 → v1.1
```

**Benefits:**
- Single source of truth
- Clear version progression
- Easier to track updates

**For This Project:**
Use Option 2 — reuse packs, increment package versions.

---

## Error Handling

### 400 Bad Request (Duplicate Name)

```json
{
  "@type": "Error",
  "statusCode": 400,
  "errorMessage": "Integration Pack with this name already exists."
}
```

**Resolution:**
- Use unique pack name (append timestamp or version)
- Query existing packs before creating

---

### 400 Bad Request (Non-Shareable Package)

```json
{
  "@type": "Error",
  "statusCode": 400,
  "errorMessage": "Cannot add non-shareable package to Integration Pack."
}
```

**Causes:**
- PackagedComponent has `shareable: false`

**Resolution:**
- Ensure all PackagedComponents created with `shareable: true`

---

### 404 Not Found

```json
{
  "@type": "Error",
  "statusCode": 404,
  "errorMessage": "Integration Pack not found."
}
```

**Causes:**
- Invalid `packId`
- Pack was deleted
- Querying wrong account

**Resolution:**
- Verify `packId` from CREATE or QUERY response
- Check pack was not deleted

---

## Best Practices

**DO:**
- ✅ Use `MULTI` installation type for flexibility
- ✅ Reuse Integration Packs for component families
- ✅ Include descriptive `description` for context
- ✅ Query historical packs for smart suggestions (Process J)
- ✅ Release pack before deploying

**DON'T:**
- ❌ Create new packs for every promotion (causes proliferation)
- ❌ Use `SINGLE` installation type (limits flexibility)
- ❌ Add non-shareable packages
- ❌ Skip release step

---

## Pack Naming Conventions

**For Component Families:**
```
{ComponentFamily} Pack
```

Examples:
- `Order Processing Pack`
- `Inventory Management Pack`
- `Customer Sync Pack`

**For Dev Teams:**
```
{TeamName} - {ComponentType} Pack
```

Examples:
- `DevTeamA - Orders Pack`
- `DevTeamB - Customers Pack`

**Avoid:**
- Date-based names (`Orders Pack - 2024-11-20`) — creates proliferation
- Generic names (`My Pack`, `Test Pack`) — no context

---

## Related References

- **`packaged-components.md`** — Creating PackagedComponents with `shareable: true`
- **`deployed-packages.md`** — Deploying packages to environments
- **`query-patterns.md`** — Querying Integration Packs
- **`error-handling.md`** — Error handling patterns

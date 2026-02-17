# Integration Pack Lifecycle

## Overview

**PackagedComponent:** A snapshot of a Boomi process component at a specific version, ready for deployment.

**IntegrationPack:** A container for one or more PackagedComponents, released as a unit and deployed to target environments.

**Process D (packageAndDeploy) Flow:** Create PackagedComponent → Add to Integration Pack → Release Pack → Deploy to Environments

---

## Step 1: Create PackagedComponent

```http
POST /partner/api/rest/v1/{accountId}/PackagedComponent
Content-Type: application/json

{
  "componentId": "process-uuid",
  "packageVersion": "1.0.5",
  "notes": "Promoted from dev - bug fixes for order processing",
  "shareable": true
}
```

**Fields:**
- `componentId`: The root process component ID (from main branch after merge)
- `packageVersion`: User-specified version string (e.g., "1.0.5", "2024-02-16")
- `shareable`: **MUST be `true`** to include in Integration Packs
- `notes`: Deployment notes (human-readable description)

**Response:**
```json
{
  "@type": "PackagedComponent",
  "packageId": "pkg-uuid",
  "componentId": "process-uuid",
  "packageVersion": "1.0.5"
}
```

**Critical:** `shareable: true` is REQUIRED for Integration Pack inclusion.

---

## Step 2: Create Integration Pack (New Pack)

```http
POST /partner/api/rest/v1/{accountId}/IntegrationPack
Content-Type: application/json

{
  "name": "Order Processing Pack",
  "description": "Contains order processing and fulfillment processes",
  "installationType": "MULTI"
}
```

**Installation Types:**
- `MULTI`: Can be deployed multiple times to different environments (used in this project)
- `SINGLE`: Single deployment per account

**Response:**
```json
{
  "@type": "IntegrationPack",
  "integrationPackId": "pack-uuid",
  "name": "Order Processing Pack"
}
```

---

## Step 3: Add PackagedComponent to Integration Pack

```http
POST /partner/api/rest/v1/{accountId}/IntegrationPack/{packId}/PackagedComponent/{packageId}
```

**No request body required.** This links the PackagedComponent to the pack.

---

## Step 4: Release Integration Pack

```http
POST /partner/api/rest/v1/{accountId}/ReleaseIntegrationPack
Content-Type: application/json

{
  "integrationPackId": "pack-uuid",
  "version": "1.0.5",
  "notes": "February 2026 release - bug fixes"
}
```

**Releasing creates a snapshot** — changes to the pack after this point require a new release.

---

## Step 5: Deploy Integration Pack

```http
POST /partner/api/rest/v1/{accountId}/DeployedPackage
Content-Type: application/json

{
  "packageId": "pack-uuid",
  "environmentId": "env-uuid"
}
```

**Key Points:**
- One deployment request per target environment
- The `packageId` is the Integration Pack ID (not the PackagedComponent ID)
- Deployment is idempotent — deploying again updates existing deployment

---

## Pitfalls

### shareable: true is REQUIRED

```json
// BAD
{
  "componentId": "process-uuid",
  "shareable": false  // Cannot be added to Integration Packs
}
```

```json
// GOOD
{
  "componentId": "process-uuid",
  "shareable": true  // Can be added to Integration Packs
}
```

### Release Before Deploy

```javascript
// BAD
await createIntegrationPack(...);
await addPackagedComponent(...);
await deployIntegrationPack(...);  // FAILS — pack not released
```

```javascript
// GOOD
await createIntegrationPack(...);
await addPackagedComponent(...);
await releaseIntegrationPack(...);  // Release first
await deployIntegrationPack(...);  // Now works
```

### PackagedComponent packageId vs Integration Pack integrationPackId

```json
// PackagedComponent response
{
  "packageId": "pkg-abc-123"  // This is the PackagedComponent ID
}

// IntegrationPack response
{
  "integrationPackId": "pack-def-456"  // This is the Integration Pack ID
}

// When deploying, use the Integration Pack ID
{
  "packageId": "pack-def-456",  // Use Integration Pack ID here!
  "environmentId": "env-uuid"
}
```

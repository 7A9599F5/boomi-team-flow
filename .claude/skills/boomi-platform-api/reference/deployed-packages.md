# DeployedPackage Operations

DeployedPackage create, query, delete operations for environment deployment.

---

## CREATE DeployedPackage

Deploy a packaged component to an environment.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/DeployedPackage
```

### Mode 1: Deploy Existing PackagedComponent (Recommended)

**Request Body:**
```json
{
  "environmentId": "e7fc610a-c1ef-4b66-8bb5-a01a1f8970e2",
  "packageId": "e5f2896e-5988-4d98-920e-4fb9750b469d",
  "notes": "Deployment notes",
  "listenerStatus": "RUNNING"
}
```

**Fields:**
- `environmentId` (required): Target environment ID
- `packageId` (required): Existing PackagedComponent ID
- `notes` (optional): Deployment notes
- `listenerStatus` (optional): `RUNNING` or `PAUSED` (default: `RUNNING` for listeners)

**Use Case in Process D:**
Deploy PackagedComponents from Integration Pack to target environments.

### Mode 2: Package and Deploy in One Operation

**Request Body:**
```json
{
  "environmentId": "983870bd-3e41-4fcc-a622-c3cb6042d9c2",
  "componentId": "1fa6c6c7-4847-4c57-8db2-587ea53afe33",
  "notes": "Package and deploy notes"
}
```

**Fields:**
- `environmentId` (required): Target environment ID
- `componentId` (required): Component to package and deploy
- `notes` (optional): Deployment notes

**Use Case:**
Quick deployment without pre-creating PackagedComponent.

**Response:**
```json
{
  "@type": "DeployedPackage",
  "deploymentId": "75bdf0f7-e9d5-46f7-b90f-37e77df03c0a",
  "version": 3,
  "packageId": "7f436a84-f9dd-4417-ac3e-ee01a1343a3b",
  "packageVersion": "3.0",
  "environmentId": "e7fc610a-c1ef-4b66-8bb5-a01a1f8970e2",
  "componentId": "5b4746bc-6a3e-4b18-838c-57887dae41e3",
  "componentVersion": "2.0",
  "componentType": "process",
  "deployedDate": "2017-04-04T15:15:36Z",
  "deployedBy": "admin@boomi.com",
  "listenerStatus": "RUNNING"
}
```

---

## GET DeployedPackage

Retrieve a specific deployment by ID.

**Endpoint:**
```http
GET /partner/api/rest/v1/{accountId}/DeployedPackage/{deploymentId}
```

---

## QUERY DeployedPackages

List deployed packages in an environment.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/DeployedPackage/query
```

**Request Body (all deployments in environment):**
```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "environmentId",
      "argument": ["{envId}"]
    }
  }
}
```

**Queryable Fields:**
- `deploymentId`, `packageId`, `componentId`, `environmentId`
- `componentType`, `deployedDate`, `deployedBy`
- `active` (boolean), `listenerStatus` (`RUNNING`, `PAUSED`)

**Use Case:**
Check current deployments before deploying new version.

---

## DELETE DeployedPackage

Undeploy a packaged component from an environment.

**Endpoint:**
```http
DELETE /partner/api/rest/v1/{accountId}/DeployedPackage/{deploymentId}
```

**Response:**
```http
HTTP/1.1 204 No Content
```

**Constraints:**
- Cannot delete if package is currently in use (active listeners)
- Must pause listener first, then delete

**Pattern:**
```javascript
// 1. Update deployment to pause listener
await updateDeployment(deploymentId, {listenerStatus: "PAUSED"});

// 2. Delete deployment
await deleteDeployment(deploymentId);
```

---

## Listener Status

For components with listeners (e.g., HTTP listeners, JMS listeners):

**Status Values:**
- **RUNNING**: Listener is active and processing messages
- **PAUSED**: Listener is stopped, no messages processed

**Setting Status:**

**On Deployment:**
```json
{
  "environmentId": "{envId}",
  "packageId": "{packageId}",
  "listenerStatus": "RUNNING"
}
```

**Update Existing Deployment:**
```http
POST /DeployedPackage/{deploymentId}
{
  "listenerStatus": "PAUSED"
}
```

---

## Deployment Versioning

### How Versioning Works

Each deployment has a `version` field that increments with each deployment to the same environment.

**Example Sequence:**
```
Component X deployed to Env A
  → deploymentId: abc-1, version: 1

Component X (updated) deployed to Env A
  → deploymentId: abc-2, version: 2

Component X (updated again) deployed to Env A
  → deploymentId: abc-3, version: 3
```

**Key Points:**
- `version` is per-environment deployment, not component version
- Each deployment creates a new `deploymentId`
- Previous deployment becomes inactive (`active: false`)

---

## Query Patterns

### Find Active Deployment for Component

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "componentId", "argument": ["{componentId}"]},
        {"operator": "EQUALS", "property": "environmentId", "argument": ["{envId}"]},
        {"operator": "EQUALS", "property": "active", "argument": ["true"]}
      ]
    }
  }
}
```

### Find All Deployments in Environment

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "environmentId",
      "argument": ["{envId}"]
    }
  }
}
```

### Find Running Listeners

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "listenerStatus",
      "argument": ["RUNNING"]
    }
  }
}
```

---

## Error Handling

### 404 Not Found (Environment)

```json
{
  "@type": "Error",
  "statusCode": 404,
  "errorMessage": "Environment not found."
}
```

**Causes:**
- Invalid `environmentId`

**Resolution:**
- Query environments via `/Environment/query`
- Verify environment ID

---

### 404 Not Found (Package)

```json
{
  "@type": "Error",
  "statusCode": 404,
  "errorMessage": "PackagedComponent not found."
}
```

**Causes:**
- Invalid `packageId`
- Package was deleted

**Resolution:**
- Verify `packageId` from PackagedComponent query
- Ensure package exists and is not deleted

---

### 409 Conflict (Active Listener)

```json
{
  "@type": "Error",
  "statusCode": 409,
  "errorMessage": "Cannot delete deployment with active listener."
}
```

**Causes:**
- Attempting to delete deployment with `listenerStatus: RUNNING`

**Resolution:**
- Update deployment to set `listenerStatus: PAUSED`
- Then delete deployment

---

## Best Practices

**DO:**
- ✅ Use Mode 1 (deploy existing package) for Integration Pack deployments
- ✅ Include descriptive `notes` for audit trail
- ✅ Set `listenerStatus: RUNNING` for listeners
- ✅ Query active deployments before deploying new version
- ✅ Pause listeners before undeploying

**DON'T:**
- ❌ Deploy without checking existing deployments (may create conflicts)
- ❌ Delete active listener deployments (will fail)
- ❌ Skip `notes` field (loses context)

---

## Deployment Workflow (Process D)

```javascript
// 1. Create PackagedComponent
const pkg = await createPackagedComponent({
  componentId: prodComponentId,
  packageVersion: version,
  shareable: true,
  notes: "Promoted from dev account"
});

// 2. Add to Integration Pack
await addPackagedComponentToIntegrationPack(packId, pkg.packageId);

// 3. Release Integration Pack
await releaseIntegrationPack(packId);

// 4. Deploy to each target environment
for (const envId of targetEnvironments) {
  await createDeployedPackage({
    environmentId: envId,
    packageId: pkg.packageId,
    notes: `Deployed from Integration Pack ${packId}`,
    listenerStatus: "RUNNING"
  });
}
```

---

## Related References

- **`packaged-components.md`** — Creating PackagedComponents for deployment
- **`integration-packs.md`** — Bundling packages for deployment
- **`query-patterns.md`** — Query filters and pagination
- **`error-handling.md`** — Error handling patterns

# PackagedComponent Operations

PackagedComponent lifecycle, versioning, and operations.

---

## CREATE PackagedComponent

Create a new packaged component from a component ID.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/PackagedComponent
```

**Request Body:**
```json
{
  "componentId": "66d665d1-3ec7-479c-9e24-8df3fa728cf8",
  "packageVersion": "1.2",
  "notes": "Package for deployment",
  "shareable": true
}
```

**Fields:**
- `componentId` (required): The component to package
- `packageVersion` (optional): User-defined version string (auto-incremented if omitted)
- `notes` (optional): Description of the package
- `shareable` (required for Integration Packs): **Must be `true`** to include in Integration Packs
- `branchName` (optional): Create package on a specific branch

**Response:**
```json
{
  "@type": "PackagedComponent",
  "packageId": "357f7a90-7708-45f9-9f28-a83bc74d49a6",
  "packageVersion": "1.3",
  "componentId": "66d665d1-3ec7-479c-9e24-8df3fa728cf8",
  "componentVersion": "2.0",
  "componentType": "process",
  "createdDate": "2017-11-01T18:40:55Z",
  "createdBy": "user@boomi.com",
  "shareable": true
}
```

**Use Case in Process D:**
Package the merged main component after promotion.

---

## GET PackagedComponent

Retrieve a specific packaged component by ID.

**Endpoint:**
```http
GET /partner/api/rest/v1/{accountId}/PackagedComponent/{packageId}
```

**Response:**
Same structure as CREATE response.

---

## QUERY PackagedComponents

List packaged components (from dev accounts for Process A).

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/PackagedComponent/query
```

**With `overrideAccount` (read from dev account):**
```http
POST /partner/api/rest/v1/{primaryAccountId}/PackagedComponent/query?overrideAccount={devAccountId}
```

**Request Body:**
```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "componentType", "argument": ["process"]},
        {"operator": "EQUALS", "property": "deleted", "argument": ["false"]}
      ]
    }
  }
}
```

**Queryable Fields:**
- `packageId`, `componentId`, `componentType`, `packageVersion`
- `deleted`, `shareable`, `createdDate`, `createdBy`

**Use Case in Process A:**
List packaged processes from dev accounts for promotion selection.

---

## DELETE PackagedComponent

Soft-delete a packaged component version.

**Endpoint:**
```http
DELETE /partner/api/rest/v1/{accountId}/PackagedComponent/{packageId}
```

**Constraints:**
- Cannot delete if currently deployed
- Can restore deleted packages via CREATE with the deleted `packageId`

---

## Versioning Mechanics

### Auto-Increment Behavior

**When `packageVersion` is omitted:**
- Boomi auto-increments based on previous packages of the same component
- Format: `{major}.{minor}` (e.g., `1.0`, `1.1`, `2.0`)

**Example Sequence:**
1. First package: `packageVersion: "1.0"` (auto-assigned)
2. Second package: `packageVersion: "1.1"` (auto-incremented)
3. Third package: `packageVersion: "2.0"` (auto-incremented)

### Manual Versioning

**When `packageVersion` is provided:**
- Use user-specified version string
- Must be unique for the component
- Can use custom formats (e.g., `"v2.5.3-beta"`)

**Best Practice:**
Use semantic versioning for clarity:
```
{major}.{minor}.{patch}
```
- `major`: Breaking changes
- `minor`: New features (backward compatible)
- `patch`: Bug fixes

### Version Constraints

**Rules:**
- `packageVersion` must be unique per component
- Cannot reuse a deleted package's version (unless restoring)
- No strict format enforcement (can use any string)

---

## `shareable` Field (Integration Pack Requirement)

### Purpose

The `shareable` field controls whether a PackagedComponent can be included in Integration Packs.

**Values:**
- `true`: Can be added to Integration Packs
- `false`: Cannot be added to Integration Packs (deployment-only)

### Requirement for This Project

**All promoted components MUST set `shareable: true`:**
```json
{
  "componentId": "...",
  "shareable": true
}
```

**Why:**
- Process D creates Integration Packs for cross-environment deployment
- Integration Packs can only contain `shareable: true` packages
- Without this, Process D will fail when adding to Integration Pack

### Error if Missing

```json
{
  "@type": "Error",
  "statusCode": 400,
  "errorMessage": "Cannot add non-shareable package to Integration Pack."
}
```

---

## Package Lifecycle

```
1. Create PackagedComponent
   ↓
2. Add to Integration Pack (optional)
   ↓
3. Release Integration Pack (optional)
   ↓
4. Deploy to Environment
   ↓
5. (Optional) Delete PackagedComponent after undeployment
```

### Step 1: Create PackagedComponent (Process D)

```json
POST /PackagedComponent
{
  "componentId": "{prodComponentId}",
  "packageVersion": "{version}",
  "shareable": true,
  "notes": "Promoted from dev account {devAccountId}"
}
```

### Step 2: Add to Integration Pack (Process D)

```http
POST /IntegrationPack/{packId}/addPackagedComponent
{
  "packageId": "{packageId}"
}
```

### Step 3: Release Integration Pack (Process D)

```http
POST /IntegrationPack/{packId}/release
```

### Step 4: Deploy to Environment (Process D)

```json
POST /DeployedPackage
{
  "environmentId": "{envId}",
  "packageId": "{packageId}",
  "listenerStatus": "RUNNING"
}
```

---

## Query Patterns

### Find All Packages for a Component

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "componentId", "argument": ["{componentId}"]},
        {"operator": "EQUALS", "property": "deleted", "argument": ["false"]}
      ]
    }
  }
}
```

### Find Packages by Version

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "packageVersion",
      "argument": ["1.5"]
    }
  }
}
```

### Find Shareable Packages

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "shareable",
      "argument": ["true"]
    }
  }
}
```

---

## Error Handling

### 404 Not Found

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
- Querying wrong account

**Resolution:**
- Verify `packageId` from query
- Check `deleted` status
- Use correct account ID

---

### 400 Bad Request (Version Conflict)

```json
{
  "@type": "Error",
  "statusCode": 400,
  "errorMessage": "Package version already exists for this component."
}
```

**Causes:**
- Attempting to create package with duplicate `packageVersion`

**Resolution:**
- Omit `packageVersion` for auto-increment
- Use unique version string

---

### 409 Conflict (Cannot Delete)

```json
{
  "@type": "Error",
  "statusCode": 409,
  "errorMessage": "Cannot delete package that is currently deployed."
}
```

**Causes:**
- Attempting to delete a package with active deployments

**Resolution:**
- Undeploy from all environments first
- Then delete package

---

## Best Practices

**DO:**
- ✅ Always set `shareable: true` for Integration Pack inclusion
- ✅ Use semantic versioning (`major.minor.patch`)
- ✅ Include descriptive `notes` for audit trail
- ✅ Query packages before creating to avoid duplicates
- ✅ Soft-delete unused packages (keep audit trail)

**DON'T:**
- ❌ Create packages with `shareable: false` for this project
- ❌ Reuse version numbers
- ❌ Delete packages with active deployments
- ❌ Skip `notes` field (loses context)

---

## Related References

- **`integration-packs.md`** — Adding packages to Integration Packs
- **`deployed-packages.md`** — Deploying packages to environments
- **`query-patterns.md`** — Advanced query filters and pagination
- **`error-handling.md`** — Retry patterns and error codes

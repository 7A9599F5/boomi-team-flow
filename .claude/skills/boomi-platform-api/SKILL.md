---
name: boomi-platform-api
description: |
  Boomi Platform API (AtomSphere/Partner API) reference. Use when working with
  API calls to api.boomi.com, component CRUD, branch operations, tilde syntax,
  PackagedComponent/IntegrationPack operations, or debugging API errors.
globs:
  - "integration/api-requests/**"
  - "integration/flow-service/**"
  - "**/*api*.md"
---

# Boomi Platform API Reference

The Boomi Platform API (also called AtomSphere API or Partner API) provides programmatic access to all Boomi Enterprise Platform functionality. This skill provides quick reference for the API patterns used in the promotion engine.

---

## Base URLs

| API Type | REST Base URL |
|----------|---------------|
| **Platform API** | `https://api.boomi.com/api/rest/v1/{accountId}` |
| **Partner API** | `https://api.boomi.com/partner/api/rest/v1/{accountId}` |

**Key Difference:**
- **Platform API**: Operates on the authenticated account only
- **Partner API**: Supports `overrideAccount` parameter to operate on sub-accounts

---

## Authentication Quick Reference

**HTTP Basic Authentication:**
```
Authorization: Basic base64(username:password)
```

**Credentials:**
- **Username**: Boomi account email
- **Password**: Account password OR API token

**API Token Format:**
```
BOOMI_TOKEN.{email}:{token-string}
```

**When API Tokens Required:**
- SSO users without Administrator privileges (MUST use tokens)
- Users with Two-Factor Authentication enabled (should use tokens)
- Best practice: Always use tokens for programmatic access

**See:** `reference/authentication.md` for HMAC details and `overrideAccount` header usage.

---

## Partner API `overrideAccount` Header

The Partner API's most powerful feature for multi-account operations:

**REST Usage:**
```
GET https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{id}?overrideAccount={devAccountId}
```

**How It Works:**
1. Authenticate as **primary account** (using primary credentials)
2. Add `overrideAccount={devAccountId}` query parameter
3. API executes request **as if** authenticated as dev account
4. Primary account must have management rights over sub-account

**Use Cases in This Project:**
- Reading components from dev sub-accounts (Process A, B, C)
- Querying PackagedComponents in dev accounts (Process A)
- Retrieving component metadata from dev accounts

**See:** `reference/authentication.md` for full details.

---

## Tilde Syntax for Branch Operations

**Format:**
```
{componentId}~{branchId}
```

**Usage:**
```http
POST /partner/api/rest/v1/{accountId}/Component/{componentId}~{branchId}
```

Creates or updates a component **on the specified branch** (isolated from main until merged).

**Use Case in Process C:** Promote components to promotion branch before merging.

**See:** `reference/branch-operations.md` for complete branch lifecycle.

---

## Key Endpoints Summary

| Object | Operation | URL Pattern |
|--------|-----------|-------------|
| **Component** | GET | `/Component/{id}` |
| | CREATE (branch) | `/Component/{id}~{branchId}` |
| | UPDATE | `/Component/{id}` (POST) |
| | DELETE | `/Component/{id}` (DELETE) |
| **ComponentMetadata** | QUERY | `/ComponentMetadata/query` (POST) |
| **ComponentReference** | QUERY | `/ComponentReference/query` (POST) |
| **PackagedComponent** | CREATE | `/PackagedComponent` (POST) |
| | GET | `/PackagedComponent/{packageId}` |
| | QUERY | `/PackagedComponent/query` (POST) |
| | DELETE | `/PackagedComponent/{packageId}` (DELETE) |
| **DeployedPackage** | CREATE | `/DeployedPackage` (POST) |
| | QUERY | `/DeployedPackage/query` (POST) |
| | DELETE | `/DeployedPackage/{deploymentId}` (DELETE) |
| **IntegrationPack** | CREATE | `/IntegrationPack` (POST) |
| | GET | `/IntegrationPack/{packId}` |
| | QUERY | `/IntegrationPack/query` (POST) |
| **Branch** | CREATE | `/Branch` (POST) |
| | GET | `/Branch/{branchId}` |
| | QUERY | `/Branch/query` (POST) |
| | DELETE | `/Branch/{branchId}` (DELETE) |
| **MergeRequest** | CREATE | `/MergeRequest` (POST) |
| | EXECUTE | `/MergeRequest/execute/{id}` (POST) |
| | GET | `/MergeRequest/{id}` |
| | DELETE | `/MergeRequest/{id}` (DELETE) |

**See:**
- `reference/component-crud.md` for Component operations
- `reference/branch-operations.md` for Branch and MergeRequest
- `reference/packaged-components.md` for PackagedComponent lifecycle
- `reference/integration-packs.md` for IntegrationPack operations
- `reference/deployed-packages.md` for DeployedPackage operations

---

## Common Request Headers

```http
Accept: application/json
Content-Type: application/json
Authorization: Basic {base64-encoded-credentials}
```

For XML operations (Component GET/POST):
```http
Accept: application/xml
Content-Type: application/xml
```

---

## Query Patterns Cheat Sheet

### Basic Query Filter
```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "name",
      "argument": ["ComponentName"]
    }
  }
}
```

### AND Query
```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "currentVersion", "argument": ["true"]},
        {"operator": "EQUALS", "property": "deleted", "argument": ["false"]},
        {"operator": "EQUALS", "property": "componentType", "argument": ["process"]}
      ]
    }
  }
}
```

### Query Operators
- `EQUALS`, `NOT_EQUALS`, `LIKE`, `STARTS_WITH`
- `IS_NULL`, `IS_NOT_NULL`
- `BETWEEN`, `GREATER_THAN`, `LESS_THAN`

**Best Practices:**
- Always filter `currentVersion = true` (avoid previous versions)
- Always filter `deleted = false` (avoid soft-deleted components)
- Use `LIKE` for name searches (supports wildcards: `%pattern%`)

**See:** `reference/query-patterns.md` for pagination and advanced filters.

---

## Pagination (Query Paging)

All QUERY operations return **maximum 100 results** per response.

**Check for More Results:**
```json
{
  "@type": "QueryResult",
  "numberOfResults": 100,
  "queryToken": "EXAMPLE_QUERY_TOKEN",
  "result": [...]
}
```

**Fetch Next Page:**
```http
POST /{ObjectType}/queryMore
Body: {"queryToken": "EXAMPLE_QUERY_TOKEN"}
```

**No `queryToken` in response = last page reached.**

**Platform API Connector Behavior:**
- Automatically handles pagination (no manual `queryMore` needed)

**Manual HTTP Client:**
- Must implement `queryMore` loop

**See:** `reference/query-patterns.md` for implementation patterns.

---

## Rate Limits and Throttling

**Limit:** **10 requests per second** per account

**On Exceeding Limit:**
```json
{
  "statusCode": 503,
  "errorMessage": "The Boomi server is currently unavailable or your account's rate limits have been exceeded. Retry later."
}
```

**Retry Strategy:**
- Implement exponential backoff
- Platform API connectors automatically retry up to 5 times

**See:** `reference/error-handling.md` for retry patterns.

---

## Branch Operations Cheat Sheet

### 1. Pre-Check Branch Count
```http
POST /Branch/query
Body: <QueryFilter xmlns='http://api.platform.boomi.com/'/>
```
**Soft Limit:** If count >= 15, abort with `BRANCH_LIMIT_REACHED` error.

### 2. Create Branch
```http
POST /Branch
Body: {"name": "promo-{promotionId}"}
```
**Response:** `branchId` with `ready: false`

### 3. Poll for Ready State
```http
GET /Branch/{branchId}
```
Poll every 2-5 seconds until `ready: true` (typically 5-30s).

### 4. Promote Components to Branch
```http
POST /Component/{componentId}~{branchId}
Body: <Component XML>
```
Use tilde syntax to target branch.

### 5. Create Merge Request
```http
POST /MergeRequest
Body: {
  "sourceBranchId": "{branchId}",
  "destinationBranchId": "main",
  "strategy": "OVERRIDE",
  "priorityBranch": "{branchId}"
}
```

### 6. Execute Merge
```http
POST /MergeRequest/execute/{mergeRequestId}
```

### 7. Delete Branch (CRITICAL)
```http
DELETE /Branch/{branchId}
```
**ALWAYS** delete branch to free up slots (20-branch limit).

**Merge Strategies:**
- **OVERRIDE**: Priority branch wins all conflicts (use this)
- **CONFLICT_RESOLVE**: Manual resolution required

**See:** `reference/branch-operations.md` for complete lifecycle.

---

## PackagedComponent Operations

### Create PackagedComponent
```json
{
  "componentId": "component-uuid",
  "packageVersion": "1.2",
  "notes": "Package notes",
  "shareable": true
}
```

**Fields:**
- `componentId` (required): Component to package
- `packageVersion` (optional): User-defined version (auto-incremented if omitted)
- `shareable` (required for Integration Packs): **Must be `true`**
- `notes` (optional): Description

**Use Case in Process D:** Package merged main component after promotion.

**See:** `reference/packaged-components.md` for versioning and lifecycle.

---

## IntegrationPack Operations

### Create IntegrationPack
```json
{
  "name": "Order Processing Pack",
  "description": "Complete order processing solution",
  "installationType": "MULTI"
}
```

**Installation Types:**
- `MULTI`: Supports multiple installations
- `SINGLE`: Single installation only

**Next Steps After Creation:**
1. Add PackagedComponents (via `AddToIntegrationPack` operation)
2. Release the pack (via `ReleaseIntegrationPack` operation)
3. Deploy to target accounts/environments

**See:** `reference/integration-packs.md` for complete lifecycle.

---

## Error Response Format

**JSON Format:**
```json
{
  "@type": "Error",
  "statusCode": 403,
  "errorMessage": "Access denied due to insufficient permissions."
}
```

**Common Status Codes:**

| Code | Meaning | Action |
|------|---------|--------|
| **200** | Success | Continue |
| **400** | Bad Request | Fix malformed JSON/XML |
| **401** | Unauthorized | Check credentials/token |
| **403** | Forbidden | Check permissions |
| **404** | Not Found | Verify resource ID |
| **503** | Service Unavailable | Retry with backoff |

**See:** `reference/error-handling.md` for detailed error handling patterns.

---

## Component XML Structure

**Basic Structure:**
```xml
<bns:Component
  xmlns:bns="http://api.platform.boomi.com/"
  componentId="{componentId}"
  version="{version}"
  name="{componentName}"
  type="{componentType}"
  folderFullPath="{folderPath}">
  <bns:object>
    <!-- Component-specific configuration XML -->
  </bns:object>
</bns:Component>
```

**Component Types:**
- `process`, `connection`, `connector`, `operation`, `map`, `profile`, `xslt`, `flowservice`

**See:** `reference/component-crud.md` for reference rewriting patterns.

---

## Project-Specific API Patterns

### Process A: listDevPackages
Query dev account's PackagedComponents using `overrideAccount`:
```http
POST /partner/api/rest/v1/{primaryAccountId}/PackagedComponent/query?overrideAccount={devAccountId}
```

### Process B: resolveDependencies
Recursively traverse dependencies using ComponentReference:
```http
POST /partner/api/rest/v1/{primaryAccountId}/ComponentReference/query?overrideAccount={devAccountId}
```

### Process C: executePromotion
Branch-scoped component creation using tilde syntax:
```http
POST /partner/api/rest/v1/{primaryAccountId}/Component/{prodComponentId}~{branchId}
```

### Process D: packageAndDeploy
Complete workflow: merge → package → Integration Pack → deploy → cleanup.

### Process G: generateComponentDiff
Fetch branch and main versions for XML diff:
- **Branch Version:** `GET /Component/{componentId}~{branchId}`
- **Main Version:** `GET /Component/{componentId}`

### Process J: listIntegrationPacks
Query Integration Packs for smart suggestions:
```http
POST /IntegrationPack/query
```

**See:** `examples/api-request-templates.md` for complete request/response examples.

---

## Quick Decision Matrix

| Task | Endpoint | Method |
|------|----------|--------|
| Read dev component | `/Component/{id}?overrideAccount={devId}` | GET |
| Promote to branch | `/Component/{id}~{branchId}` | POST |
| List dev packages | `/PackagedComponent/query?overrideAccount={devId}` | POST |
| Find dependencies | `/ComponentReference/query` | POST |
| Create branch | `/Branch` | POST |
| Merge branch | `/MergeRequest` (POST) → `/MergeRequest/execute/{id}` (POST) | POST |
| Package component | `/PackagedComponent` | POST |
| Create Integration Pack | `/IntegrationPack` | POST |
| Deploy package | `/DeployedPackage` | POST |

---

## Reference Files (Deep Dive)

- **`reference/authentication.md`** — HMAC auth, API tokens, `overrideAccount` header
- **`reference/component-crud.md`** — Component GET/CREATE/UPDATE/DELETE, reference rewriting
- **`reference/branch-operations.md`** — Branch lifecycle, tilde syntax, merge strategies, 20-branch limit
- **`reference/packaged-components.md`** — PackagedComponent lifecycle, versioning mechanics
- **`reference/integration-packs.md`** — IntegrationPack create/deploy lifecycle
- **`reference/deployed-packages.md`** — DeployedPackage operations
- **`reference/query-patterns.md`** — Pagination, QueryToken, filters, operators
- **`reference/error-handling.md`** — Error codes, rate limits, retry patterns, security

---

## Examples

- **`examples/api-request-templates.md`** — Common curl/request patterns for all 11 processes

---

## Official Documentation Links

- [Platform API Reference](https://developer.boomi.com/docs/api/platformapi/)
- [Partner API Overview](https://developer.boomi.com/docs/APIs/PlatformAPI/Introduction/Partner_API)
- [Authentication Guide](https://developer.boomi.com/docs/APIs/PlatformAPI/Introduction/Platform_API_and_Partner_API_authentication)
- [Query Paging](https://developer.boomi.com/docs/APIs/PlatformAPI/Introduction/Query_paging)
- [Branch & Merge Automation](https://developer.boomi.com/blog/Branchandmerge)

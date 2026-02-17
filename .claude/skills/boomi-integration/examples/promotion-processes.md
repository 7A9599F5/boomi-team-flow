# Promotion Processes Implementation Patterns

Project-specific implementation patterns for the 11 Integration processes (A0, A–G, E2, E3, J) in the Boomi dev-to-prod promotion system.

---

## Overview

**11 Integration Processes** act as backend APIs for the Flow dashboard via Flow Service Server.

**Architecture**:
```
Flow Dashboard (UI)
  ↓ Message Actions
Flow Service (Path: /fs/PromotionService)
  ↓ 11 Listener Processes
Integration Engine (Platform API, DataHub)
```

---

## Process A0 — Get Dev Accounts

### Purpose

Query `DevAccountAccess` DataHub model to get dev accounts accessible by current user's SSO group.

### Flow

```
Start (Flow Service Server, Listen, getDevAccounts)
  ↓
Set Properties (extract $User.ssoGroupId from request context)
  ↓
DataHub Connector (Query DevAccountAccess)
  Filter: ssoGroupId eq '{ssoGroupId}'
  ↓
Decision (query succeeded?)
  ├─→ True:
  │     Map (transform to response profile)
  │     End (return success response)
  │
  └─→ False:
        Set Properties (errorCode = DATAHUB_ERROR)
        Map (build error response)
        End
```

### Request/Response

**Request** (empty):
```json
{}
```

**Response**:
```json
{
  "success": true,
  "devAccounts": [
    {
      "accountId": "sub-account-123",
      "accountName": "Dev Team A"
    },
    {
      "accountId": "sub-account-456",
      "accountName": "Dev Team B"
    }
  ],
  "errorCode": "",
  "errorMessage": ""
}
```

### Key Techniques

- **SSO Group Extraction**: Read from Flow request context (`$User` object)
- **DataHub Query**: OData filter on `ssoGroupId`
- **Error Handling**: Return `DATAHUB_ERROR` if query fails

---

## Process A — List Dev Packages

### Purpose

Query Platform API for PackagedComponents in dev account.

### Flow

```
Start (Flow Service Server, Listen, listDevPackages)
  ↓
Set Properties (devAccountId from request)
  ↓
Set Properties (http.header.X-Boomi-OverrideAccount = {devAccountId})
  ↓
HTTP Client (POST /PackagedComponent/query)
  Request: QueryFilter (all PackagedComponents)
  ↓
Decision (HTTP status = 200?)
  ├─→ True:
  │     Map (transform to response profile)
  │     End (return packages list)
  │
  └─→ False:
        Set Properties (errorCode = AUTH_FAILED or COMPONENT_NOT_FOUND)
        End (return error)
```

### Request/Response

**Request**:
```json
{
  "devAccountId": "sub-account-123"
}
```

**Response**:
```json
{
  "success": true,
  "packages": [
    {
      "packageId": "pkg-123",
      "componentId": "comp-456",
      "componentName": "Process - Order Fulfillment",
      "version": "1.2.3",
      "packagedDate": "2026-02-16T10:30:00Z"
    }
  ],
  "errorCode": "",
  "errorMessage": ""
}
```

### Key Techniques

- **overrideAccount Header**: Access sub-account components from primary account
- **Platform API Query**: POST to `/PackagedComponent/query`
- **Error Handling**: Check HTTP status code (401 = auth failed, 404 = account not found)

---

## Process B — Resolve Dependencies

### Purpose

Recursive dependency traversal starting from root component.

### Flow

```
Start (Flow Service Server, Listen, resolveDependencies)
  ↓
Initialize DPPs (visitedComponentIds = [], componentQueue = [rootComponentId])
  ↓
Decision (queue not empty?)
  ├─→ True:
  │     Data Process (dequeue next component)
  │     ↓
  │     Decision (already visited?)
  │       ├─→ True: Skip (route back to Decision)
  │       └─→ False:
  │             Mark as visited
  │             HTTP Client (GET /Component/{id}/ComponentReference)
  │             Data Process (extract child component IDs, enqueue)
  │             Route (call self - recursive loop)
  │
  └─→ False:
        Data Process (sort-by-dependency.groovy)
        Map (build response)
        End
```

### Algorithm

**1. Initialize**:
```groovy
def visitedSet = []
def queue = [rootComponentId]
```

**2. Loop while queue not empty**:
```groovy
while (!queue.isEmpty()) {
    def currentId = queue.remove(0) // Dequeue

    if (visitedSet.contains(currentId)) {
        continue // Skip if already visited
    }

    visitedSet << currentId // Mark as visited

    // Query ComponentReference API
    def children = queryComponentReferences(currentId)

    // Enqueue children
    children.each { childId ->
        if (!visitedSet.contains(childId)) {
            queue << childId
        }
    }
}
```

**3. Sort by dependency**:
```groovy
// Type hierarchy: profile → connection → operation → map → process
def sortedComponents = visitedSet.sort { a, b ->
    def typeOrder = [profile: 1, connection: 2, operation: 3, map: 4, process: 5]
    typeOrder[a.type] <=> typeOrder[b.type]
}
```

### Key Techniques

- **DPP State Management**: `visitedComponentIds` (JSON array), `componentQueue` (JSON array)
- **Decision + Route Loop**: Recursive traversal pattern
- **Groovy Script**: `build-visited-set.groovy`, `sort-by-dependency.groovy`
- **Type Ordering**: Profile → Connection → Operation → Map → Process

### Scripts

**build-visited-set.groovy**:
```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

def logger = ExecutionUtil.getBaseLogger()

// Load current visited set from DPP
String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
def visitedSet = visitedJson ? new JsonSlurper().parseText(visitedJson) : []

// Get current component ID
String currentId = ExecutionUtil.getDynamicProcessProperty("currentComponentId")

// Check if already visited
if (visitedSet.contains(currentId)) {
    ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "true", false)
} else {
    visitedSet << currentId
    ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "false", false)

    // Parse ComponentReference XML to extract child IDs
    // ... (XmlSlurper logic to extract componentId nodes)
}

// Update visited set DPP
ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
```

---

## Process C — Execute Promotion

### Purpose

Batch promote components from dev account to prod account via branch.

### Flow

```
Start (Flow Service Server, Listen, executePromotion)
  ↓
Create Branch (POST /Branch)
  ↓
Batch Query Mappings (DataHub Query ComponentMapping)
  → Pre-load mapping cache in DPP
  ↓
Data Process (sort-by-dependency.groovy)
  ↓
Data Process (validate-connection-mappings.groovy)
  → Fail fast if missing connection mappings
  ↓
Decision (validation failed?)
  ├─→ True: Return error (MISSING_CONNECTION_MAPPINGS)
  └─→ False: Continue
  ↓
Loop through components (non-connections only):
  ├─→ Query mapping (check if exists)
  ├─→ GET Component XML (from dev account)
  ├─→ Data Process (strip-env-config.groovy)
  ├─→ Data Process (rewrite-references.groovy)
  ├─→ POST Component/{id}~{branchId} (promote to branch)
  ├─→ DataHub Upsert (store mapping)
  └─→ Continue to next component
  ↓
Upsert PromotionLog (DataHub)
  ↓
Return response (branchId, results, error summary)
  ↓
End
```

### Key Steps

**1. Create Branch**:
```
POST /Branch
{
  "name": "promo-dev-teamA-20260216-103045",
  "componentIds": []
}

Response: { "branchId": "branch-abc-123" }
```

**2. Pre-load Mapping Cache**:
```groovy
// Query all mappings for dev account
DataHub Query ComponentMapping
  Filter: devAccountId eq '{devAccountId}'
  Max Results: 1000

// Store in DPP as JSON
def cache = [:]
results.each { mapping ->
    cache[mapping.devComponentId] = mapping.prodComponentId
}
ExecutionUtil.setDynamicProcessProperty("componentMappingCache", JsonOutput.toJson(cache), false)
```

**3. Validate Connection Mappings**:
```groovy
// validate-connection-mappings.groovy
def missingMappings = []
components.findAll { it.type == 'connection' }.each { conn ->
    if (!cache.containsKey(conn.devComponentId)) {
        missingMappings << conn.name
    }
}

if (!missingMappings.isEmpty()) {
    ExecutionUtil.setDynamicProcessProperty("validationFailed", "true", false)
    ExecutionUtil.setDynamicProcessProperty("missingConnectionMappings", JsonOutput.toJson(missingMappings), false)
}
```

**4. Strip Environment Config**:
```groovy
// strip-env-config.groovy
def xml = new XmlSlurper(false, false).parseText(componentXml)

// Remove password fields
xml.depthFirst().findAll { it.name() == 'password' }.each { it.replaceBody('') }

// Remove host fields
xml.depthFirst().findAll { it.name() == 'host' }.each { it.replaceBody('') }

// Remove URL fields
xml.depthFirst().findAll { it.name() == 'url' }.each { it.replaceBody('') }

// Serialize back to XML
String strippedXml = XmlUtil.serialize(xml)
```

**5. Rewrite References**:
```groovy
// rewrite-references.groovy
def xml = new XmlSlurper(false, false).parseText(componentXml)

// Replace all componentId references with prod IDs
xml.depthFirst().findAll {
    it.name() == 'componentId' || it.name() == 'referenceComponentId'
}.each { ref ->
    String devId = ref.text()
    String prodId = cache[devId]
    if (prodId) {
        ref.replaceBody(prodId)
    }
}

String rewrittenXml = XmlUtil.serialize(xml)
```

**6. Promote to Branch**:
```
POST /Component/{prodComponentId}~{branchId}
  (tilde syntax promotes to branch, not main)

Response: { "componentId": "prod-comp-xyz", "version": 42 }
```

### Key Techniques

- **Tilde Syntax**: `{componentId}~{branchId}` promotes to branch
- **Mapping Cache**: Pre-load all mappings (avoid N+1 queries)
- **Batch Validation**: Validate ALL connections upfront (fail fast)
- **Groovy Scripts**: `strip-env-config.groovy`, `rewrite-references.groovy`
- **Error Rollback**: On failure, delete branch (cleanup)

---

## Process D — Package and Deploy

### Purpose

Merge branch to main, create PackagedComponents, create Integration Pack, deploy.

### Flow

```
Start (Flow Service Server, Listen, packageAndDeploy)
  ↓
POST /Branch/{branchId}/merge
  (Merge branch to main)
  ↓
Loop through components:
  ├─→ POST /PackagedComponent
  │     (Create packaged component for each promoted component)
  └─→ Continue
  ↓
POST /IntegrationPack
  (Create Integration Pack with all packaged components)
  ↓
POST /DeployedPackage
  (Deploy Integration Pack to target environment)
  ↓
DELETE /Branch/{branchId}
  (Cleanup: delete branch)
  ↓
Update PromotionLog (DataHub)
  Set adminReviewStatus = COMPLETED
  ↓
Return response (integrationPackId)
  ↓
End
```

### Key Steps

**1. Merge Branch**:
```
POST /Branch/{branchId}/merge
{
  "targetBranch": "main"
}

Response: { "success": true }
```

**2. Create Packaged Components**:
```
POST /PackagedComponent
{
  "componentId": "prod-comp-xyz",
  "version": "1.0.0",
  "notes": "Promoted from dev account",
  "packageType": "SINGLE"
}

Response: { "packagedComponentId": "pkg-123" }
```

**3. Create Integration Pack**:
```
POST /IntegrationPack
{
  "name": "Promoted from DevTeamA - 2026-02-16",
  "version": "1.0.0",
  "packagedComponentIds": ["pkg-123", "pkg-456", ...]
}

Response: { "integrationPackId": "ipack-789" }
```

**4. Deploy Integration Pack**:
```
POST /DeployedPackage
{
  "integrationPackId": "ipack-789",
  "environmentId": "env-prod",
  "runtimeId": "cloud-us-east"
}

Response: { "deployedPackageId": "deploy-abc" }
```

### Key Techniques

- **Branch Merge**: POST to `/Branch/{branchId}/merge`
- **Batch Packaging**: Create packaged components for all promoted components
- **Integration Pack**: Group all packages into single deployable unit
- **Cleanup**: Delete branch after successful merge

---

## Process E — Query Status

### Purpose

Query `PromotionLog` DataHub model with optional filters (review stage, date range).

### Flow

```
Start (Flow Service Server, Listen, queryStatus)
  ↓
Decision (reviewStage parameter)
  ├─→ ALL: No filter
  ├─→ PENDING_PEER_REVIEW: Filter by peerReviewStatus eq 'PENDING_PEER_REVIEW'
  ├─→ PENDING_ADMIN_REVIEW: Filter by adminReviewStatus eq 'PENDING_ADMIN_REVIEW'
  └─→ Default: No filter
  ↓
DataHub Query (PromotionLog with filter)
  ↓
Map (transform to response profile)
  ↓
End (return promotions list)
```

### OData Filters

**All promotions**:
```
(no filter)
```

**Pending peer review**:
```
peerReviewStatus eq 'PENDING_PEER_REVIEW'
```

**Pending admin review**:
```
adminReviewStatus eq 'PENDING_ADMIN_REVIEW' and peerReviewStatus eq 'APPROVED'
```

**Date range**:
```
promotionDate ge '2026-01-01T00:00:00Z' and promotionDate le '2026-01-31T23:59:59Z'
```

---

## Process E2 — Query Peer Review Queue

### Purpose

Query `PromotionLog` for promotions pending peer review, excluding own promotions.

### Flow

```
Start (Flow Service Server, Listen, queryPeerReviewQueue)
  ↓
Set Properties (currentUser from request context)
  ↓
DataHub Query (PromotionLog)
  Filter: peerReviewStatus eq 'PENDING_PEER_REVIEW' and initiatedBy ne '{currentUser}'
  ↓
Map (transform to response profile)
  ↓
End
```

### Key Techniques

- **Self-Review Prevention**: Filter `initiatedBy ne '{currentUser}'`
- **OData Filter**: Combine `peerReviewStatus` and `initiatedBy` with `and`

---

## Process E3 — Submit Peer Review

### Purpose

Record peer review decision (approve/reject) with self-review prevention.

### Flow

```
Start (Flow Service Server, Listen, submitPeerReview)
  ↓
Set Properties (currentUser from request context)
  ↓
DataHub Query (PromotionLog)
  Filter: promotionId eq '{promotionId}'
  ↓
Decision (initiatedBy = currentUser?)
  ├─→ True: Return error (SELF_REVIEW_NOT_ALLOWED)
  └─→ False: Continue
  ↓
DataHub Upsert (PromotionLog)
  Update: peerReviewStatus = {action}, peerReviewedBy = {currentUser}, peerReviewComments = {comments}
  ↓
Return success response
  ↓
End
```

### Key Techniques

- **Self-Review Prevention**: Check `initiatedBy` vs `currentUser`
- **DataHub Upsert**: Update existing PromotionLog record

---

## Process F — Manage Mappings

### Purpose

CRUD operations on `ComponentMapping` DataHub model.

### Flow

```
Start (Flow Service Server, Listen, manageMappings)
  ↓
Decision (action parameter)
  ├─→ CREATE/UPDATE:
  │     DataHub Upsert (ComponentMapping)
  │     Return success
  │
  ├─→ DELETE:
  │     DataHub Delete (ComponentMapping)
  │     Return success
  │
  └─→ QUERY:
        DataHub Query (ComponentMapping)
        Return mappings list
```

### Actions

**CREATE/UPDATE** (upsert):
```json
{
  "action": "UPSERT",
  "mapping": {
    "devComponentId": "abc-123",
    "prodComponentId": "xyz-789",
    "devAccountId": "sub-account-456",
    "componentName": "Connection - Salesforce",
    "componentType": "connection",
    "source": "ADMIN_SEEDING"
  }
}
```

**DELETE**:
```json
{
  "action": "DELETE",
  "mapping": {
    "devComponentId": "abc-123",
    "devAccountId": "sub-account-456"
  }
}
```

**QUERY**:
```json
{
  "action": "QUERY",
  "filter": {
    "devAccountId": "sub-account-456",
    "componentType": "connection"
  }
}
```

---

## Process G — Generate Component Diff

### Purpose

Fetch component XML from branch and main, normalize both, return for UI diff rendering.

### Flow

```
Start (Flow Service Server, Listen, generateComponentDiff)
  ↓
Decision (componentAction)
  ├─→ CREATE:
  │     GET Component/{prodComponentId}~{branchId} (branch version)
  │     Return branchXml, mainXml = ""
  │
  └─→ UPDATE:
        GET Component/{prodComponentId}~{branchId} (branch version)
        GET Component/{prodComponentId} (main version)
        ↓
        Data Process (normalize-xml.groovy on branch XML)
        Data Process (normalize-xml.groovy on main XML)
        ↓
        Return branchXml, mainXml
```

### XML Normalization

**normalize-xml.groovy**:
```groovy
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil

def xml = new XmlSlurper(false, false).parseText(componentXml)

// Serialize with canonical formatting
String normalized = XmlUtil.serialize(xml)

// Remove XML declaration
normalized = normalized.replaceFirst(/<\?xml[^>]+\?>/, '')

// Trim trailing whitespace from each line
normalized = normalized.split('\n').collect { it.trim() }.join('\n')

// Return normalized XML
normalized
```

### Why Normalize?

- Boomi API returns XML with inconsistent whitespace
- Attribute ordering can vary
- Without normalization, diff shows false positives on formatting

---

## Process J — List Integration Packs

### Purpose

Query Platform API for Integration Packs with smart suggestion from promotion history.

### Flow

```
Start (Flow Service Server, Listen, listIntegrationPacks)
  ↓
Set Properties (http.header.X-Boomi-OverrideAccount = {devAccountId})
  ↓
HTTP Client (POST /IntegrationPack/query)
  ↓
DataHub Query (PromotionLog)
  Filter: devAccountId eq '{devAccountId}'
  Sort: promotionDate desc
  Limit: 1
  → Get most recent promotion
  ↓
Map (build response: all packs + suggest most recent)
  ↓
End
```

### Smart Suggestion

**Logic**: Suggest the Integration Pack used in the most recent successful promotion.

**Response**:
```json
{
  "success": true,
  "packs": [
    {
      "packId": "ipack-123",
      "name": "Order Management v2",
      "version": "2.0.0",
      "suggested": true
    },
    {
      "packId": "ipack-456",
      "name": "Customer Sync v1",
      "version": "1.5.0",
      "suggested": false
    }
  ]
}
```

---

## Common Patterns

### Flow Service Listener

**All 11 processes follow this pattern**:
```
Start (Flow Service Server, Listen, {operation})
  ↓
Try/Catch
  ├─→ Try Path:
  │     [Processing Logic]
  │     Decision (success?)
  │       ├─→ True: Return success response
  │       └─→ False: Return error response
  │
  └─→ Catch Path:
        Set Properties (errorCode = PROCESS_FAILED, errorMessage = {trycatchmessage})
        Return error response
  ↓
End
```

### Standard Response Structure

```json
{
  "success": true | false,
  "errorCode": "ERROR_CODE_ENUM",
  "errorMessage": "Human-readable description",
  ... [operation-specific data]
}
```

### Dynamic Process Properties (DPPs)

**Common DPPs across processes**:
- `visitedComponentIds` (Process B): JSON array of visited component IDs
- `componentMappingCache` (Process C): JSON object of dev→prod mappings
- `validationFailed` (Process C): Boolean flag for validation errors
- `loopCount` (Process B): Loop counter for traversal

### Groovy Scripts

**6 Groovy scripts used across processes**:
1. `build-visited-set.groovy` (Process B): Dependency traversal state management
2. `sort-by-dependency.groovy` (Process B, C): Type-hierarchy ordering
3. `strip-env-config.groovy` (Process C): Remove passwords, hosts, URLs
4. `validate-connection-mappings.groovy` (Process C): Pre-promotion validation
5. `rewrite-references.groovy` (Process C): Component ID replacement
6. `normalize-xml.groovy` (Process G): XML formatting for diff comparison

---

## Related References

- `flow-service-server.md` — Flow Service Server patterns
- `http-client.md` — Platform API HTTP requests
- `datahub-connector.md` — DataHub queries and upserts
- `process-properties.md` — DPP patterns for state management
- `error-handling.md` — Try/Catch and error response patterns

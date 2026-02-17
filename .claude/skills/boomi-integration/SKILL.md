---
name: boomi-integration
description: |
  Boomi Integration (iPaaS) reference. Use when building integration processes,
  configuring connectors (HTTP Client, DataHub), creating JSON profiles, setting
  up Flow Service Server, handling errors with Try/Catch, or working with
  process properties and deployment.
globs:
  - "integration/**"
  - "**/*.groovy"
---

# Boomi Integration Reference

## Overview

**Boomi Integration** (AtomSphere iPaaS) is a cloud-native integration platform that connects applications, data, and systems using visual, low-code processes. This skill provides guidance for building integration processes, configuring connectors, and deploying solutions.

**Key Capabilities**:
- Visual process builder with drag-and-drop shapes
- 200+ pre-built connectors (HTTP, DataHub, databases, SaaS apps)
- Custom scripting with Groovy for transformations
- Flow Service Server for backend API integration with Boomi Flow
- Hybrid deployment (Cloud, on-premise Atoms/Molecules)

---

## Process Building Quick Reference

### What is a Process?

A **process** is the central component — a visual flow of data from source to destination with transformations, routing, and error handling.

**Execution Model**:
1. **Start Shape** → Defines trigger (listener, scheduled, no data)
2. **Connector Shapes** → Retrieve/send data (HTTP, DataHub, database)
3. **Logic Shapes** → Branch, Decision, Route, Try/Catch
4. **Transform Shapes** → Data Process, Map, Set Properties
5. **End Shape** → Terminates execution

**Process Canvas**: Visual workspace where shapes are connected via arrows.

### Document Flow Concepts

- **Documents**: Units of data flowing through the process (XML, JSON, CSV, binary)
- **Document Batching**: Multiple documents can flow together as a batch
- **Properties**: Metadata attached to documents (connector, dynamic, process)
- **Execution ID**: Unique identifier for each process run

---

## Process Shapes Summary

| Shape | Purpose | Key Use Cases |
|-------|---------|---------------|
| **Start** | Defines how process begins | Listener (HTTP, Flow Service), Scheduled, No Data |
| **End** | Terminates execution | Final step in any path |
| **Connector** | Interacts with external systems | Database, HTTP Client, DataHub, Salesforce |
| **Data Process** | Custom transformations/logic | Groovy scripts, split/combine documents, encode/decode |
| **Map** | Transforms data between profiles | Field mapping, functions, custom scripts |
| **Branch** | Parallel execution (all paths) | Multi-destination sends, parallel processing |
| **Decision** | Conditional routing | If-then-else logic, filtering |
| **Route** | Calls subprocess | Modular design, reusable logic |
| **Try/Catch** | Captures errors | Prevent failure, log errors, send notifications |
| **Set Properties** | Sets property values | Pass metadata between steps |
| **Message** | Sends email notifications | Error alerts, completion notifications |
| **Stop** | Immediately halts execution | Emergency shutdown (rare) |

**See**: `reference/process-shapes.md` for detailed shape configurations and behavior.

---

## HTTP Client Connector Setup

### Connection Configuration Checklist

```yaml
Connection Settings:
  - Base URL: https://api.example.com
  - Authentication Type: [None | Basic | OAuth 2.0 | AWS Signature | Client Certificate]
  - Username/Password: (for Basic auth)
  - OAuth 2.0 Grant: [Authorization Code | Resource Owner | Client Credentials]

Operation Settings:
  - Type: [GET | POST | QUERY]
  - Request Profile: JSON/XML structure for request body
  - Response Profile: JSON/XML structure for response body
  - Dynamic URL: Use {1}, {2}, {3} for document properties
```

### Dynamic URL Pattern

**Variables**:
- `{1}`, `{2}`, `{3}` → Document property values (in order)
- `{process.property.name}` → Process property values

**Example**: `https://api.boomi.com/api/rest/v1/{1}/Component/{2}`
- `{1}` = account ID (from document property)
- `{2}` = component ID (from document property)

### Custom Headers

Set headers via **Set Properties** step before HTTP connector:

```
Property Name: document.dynamic.userdefined.http.header.Authorization
Property Value: Bearer abc123

Property Name: document.dynamic.userdefined.http.header.Content-Type
Property Value: application/json
```

**See**: `reference/http-client.md` for authentication patterns and advanced configuration.

---

## JSON Profile Structure

**Profiles** define data structure for Flow Services, HTTP requests/responses, and DataHub operations.

### Profile Element Types

| Type | Description | Example |
|------|-------------|---------|
| **Character** | String/text field | `"name": "John Doe"` |
| **Number** | Numeric field | `"age": 30` |
| **Boolean** | True/false | `"isActive": true` |
| **Object** | Nested object | `"address": { "city": "NYC" }` |
| **Array** | List of items | `"tags": ["urgent", "finance"]` |
| **DateTime** | ISO 8601 timestamp | `"createdAt": "2026-02-16T10:30:00Z"` |

### Creating Profiles

**From JSON Sample** (recommended):
1. Navigate to **Build** → **Create New** → **Profile**
2. Select **JSON**
3. Paste sample JSON
4. Boomi auto-generates profile elements

**Manual Creation**:
1. Define root Object
2. Add child elements with types
3. Configure properties (required, min/max occurrences)

**See**: `reference/json-profiles.md` for profile best practices and Flow Service integration.

---

## Flow Service Server Binding

**Flow Service** enables Integration processes to act as backend APIs for Boomi Flow applications.

### Setup Pattern

**1. Create Flow Service Component**:
```yaml
Component Type: Boomi Flow Services
Path to Service: /fs/PromotionService
Operations:
  - Message Action: getDevAccounts
    Request Profile: GetDevAccountsRequest
    Response Profile: GetDevAccountsResponse
```

**2. Create Listener Process**:
```
Start (Flow Service Server, Listen, getDevAccounts)
  ↓
[Processing Logic: DataHub/HTTP/Map/Decision]
  ↓
End (Return response)
```

**3. Response Structure** (standard pattern):
```json
{
  "success": true | false,
  "errorCode": "ERROR_CODE_ENUM",
  "errorMessage": "Human-readable description",
  ... [operation-specific data]
}
```

### Async Behavior

- **Long-running operations** (>30s): Flow Service auto-returns wait response
- **Flow UI**: Displays spinner/progress indicator
- **Callback**: Flow Service sends final response when complete
- **State persistence**: IndexedDB caching allows tab closing

**See**: `reference/flow-service-server.md` for message action binding, timeout handling, and Flow integration.

---

## Data Process & Groovy Scripting

### Key Objects in Groovy Scripts

```groovy
// dataContext — access document data and properties
int docCount = dataContext.getDataCount()
InputStream is = dataContext.getStream(i)
Properties props = dataContext.getProperties(i)
String content = is.getText("UTF-8")
dataContext.storeStream(modifiedStream, props)

// ExecutionUtil — process properties, execution info, logging
def logger = ExecutionUtil.getBaseLogger()
logger.info("Processing...")
String value = ExecutionUtil.getDynamicProcessProperty("propertyName")
ExecutionUtil.setDynamicProcessProperty("propertyName", "value", false)
String accountId = ExecutionUtil.getRuntimeExecutionProperty("accountId")

// Document Properties
String fileName = props.getProperty("document.dynamic.userdefined.fileName")
props.setProperty("document.dynamic.userdefined.customProp", "value")
```

### Common Script Pattern

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String content = is.getText("UTF-8")

    // Process content (parse JSON, transform, etc.)
    def json = new JsonSlurper().parseText(content)
    // ... transformations ...
    String output = JsonOutput.toJson(json)

    // Store modified document
    dataContext.storeStream(
        new ByteArrayInputStream(output.getBytes("UTF-8")),
        props
    )
}
```

**See**: `reference/process-properties.md` for Dynamic Process Properties (DPP) and `reference/error-handling.md` for Try/Catch patterns.

---

## DataHub Connector

**DataHub** is Boomi's cloud-based master data management (MDM) and operational data store.

### Operations Summary

| Operation | Purpose | Configuration |
|-----------|---------|---------------|
| **Query Golden Records** | Retrieve records from universe | Filter, sort, max results |
| **Update Golden Records** | Upsert records (create/update) | Match keys, upsert mode |
| **Delete Golden Records** | Delete records by ID | Golden record ID |

### Query Example

**Configuration**:
- Universe Name: `ComponentMapping`
- Query Filter: `devComponentId eq 'abc123'`
- Max Results: `1`

**Response**: Auto-generated profile from model schema (includes IDs, fields, metadata)

### Update/Upsert Example

**Configuration**:
- Universe Name: `ComponentMapping`
- Upsert Mode: Create/update based on match keys
- Match Keys: `devComponentId` + `devAccountId`

**Request**:
```xml
<GoldenRecord>
  <devComponentId>abc-123</devComponentId>
  <prodComponentId>xyz-789</prodComponentId>
  <devAccountId>sub-account-123</devAccountId>
  <componentName>Process - Order Fulfillment</componentName>
  <componentType>process</componentType>
  <source>PROMOTION_ENGINE</source>
</GoldenRecord>
```

**See**: `reference/datahub-connector.md` for Hub Auth Token setup and batch operations.

---

## Process Properties Reference

### Property Types

| Type | Scope | Persistence | Access Method |
|------|-------|-------------|---------------|
| **Process Property Component** | Process-wide | Static (design time) | `ExecutionUtil.getProcessProperty(componentId, key)` |
| **Dynamic Process Property (DPP)** | Process-wide | Runtime | `ExecutionUtil.getDynamicProcessProperty(name)` |
| **Dynamic Document Property (DDP)** | Per-document | Per-document | `props.getProperty("document.dynamic.userdefined.key")` |
| **Execution Property** | Process-wide | Read-only | `ExecutionUtil.getRuntimeExecutionProperty(name)` |

### DPP Persistence Flag

```groovy
// Non-persisted (default) — cleared after execution
ExecutionUtil.setDynamicProcessProperty("tempCounter", "42", false)

// Persisted — survives across executions
ExecutionUtil.setDynamicProcessProperty("lastRunTimestamp", "2026-02-16T10:30:00Z", true)
```

**Warning**: Persisted DPPs consume storage. Use sparingly for true cross-execution state.

### Common DDP Naming Patterns

```
document.dynamic.userdefined.fileName
document.dynamic.userdefined.sourceRecordId
document.dynamic.userdefined.customMetadata
document.dynamic.connector.httpStatusCode
document.property.metadata.base.trycatchmessage
```

**See**: `reference/process-properties.md` for cross-process property passing and Route shape patterns.

---

## Error Handling Patterns

### Try/Catch Shape

**Behavior**:
1. Documents enter **Try** path
2. Failed documents → **Catch** path (with error message)
3. Successful documents continue on Try path

**Error Message Property**: `document.property.metadata.base.trycatchmessage`

**Example**:
```
Try Path:
  → HTTP Client (call API)
  → Map (transform)
  → Database (insert)

Catch Path:
  → Set Properties (capture error)
  → Notify (email alert)
  → Database (log error)
```

### Flow Service Error Response Pattern

**Standard Structure**:
```json
{
  "success": false,
  "errorCode": "COMPONENT_NOT_FOUND",
  "errorMessage": "Component ID abc-123 does not exist in account"
}
```

**Common Error Codes**:
- `AUTH_FAILED` — API authentication failed
- `COMPONENT_NOT_FOUND` — Invalid component ID
- `DATAHUB_ERROR` — DataHub operation failed
- `MISSING_CONNECTION_MAPPINGS` — Connection mappings not seeded
- `BRANCH_LIMIT_REACHED` — Too many active branches

**See**: `reference/error-handling.md` for nested Try/Catch and Stop shape usage.

---

## Deployment Quick Reference

### Runtime Types

| Runtime | Hosting | Use Cases |
|---------|---------|-----------|
| **Atom** | On-premise/cloud VM | Dev/test, low-volume integrations |
| **Molecule** | Clustered VMs (2+ nodes) | High availability, load balancing |
| **Cloud** | Boomi-managed multi-tenant | Flow Service, HTTP listeners (no firewall) |

### Packaged Component Workflow

1. **Create Packaged Component**:
   - Navigate to component → **Create Packaged Component**
   - Version: `1.0.0` (semantic versioning)
   - Mark as **shareable** (for Integration Packs)

2. **Deploy**:
   - Navigate to **Deploy** → **Deployments**
   - Select packaged component
   - Choose environment + runtime
   - **Deploy**

3. **Integration Pack** (optional):
   - Group multiple packaged components
   - Types: **SINGLE** (one root) or **MULTI** (multiple roots)
   - Deploy as unit to environment

**See**: `reference/deployment.md` for Integration Pack creation and Cloud runtime configuration.

---

## Project-Specific Patterns

### This Project's Integration Processes

**11 Integration Processes** (A0, A–G, E2, E3, J):

| Process | Purpose | Key Shapes |
|---------|---------|------------|
| **A0** | Get dev accounts (SSO → DataHub) | Flow Service listener, DataHub Query |
| **A** | List dev packages | HTTP Client (Platform API) |
| **B** | Resolve dependencies (recursive) | Decision loop, Route (self-call), Data Process |
| **C** | Execute promotion (batch) | HTTP Client, Data Process (strip/rewrite), DataHub Upsert |
| **D** | Package and deploy | HTTP Client (Branch merge, Integration Pack), Decision |
| **E** | Query status (with filters) | DataHub Query, Map |
| **E2** | Query peer review queue | DataHub Query (exclude self) |
| **E3** | Submit peer review | DataHub Upsert (prevent self-review) |
| **F** | Manage mappings (CRUD) | DataHub Query/Upsert/Delete |
| **G** | Generate component diff | HTTP Client, Data Process (normalize XML) |
| **J** | List integration packs | HTTP Client (Platform API), Map |

**See**: `examples/promotion-processes.md` for detailed implementation patterns.

---

## Supporting Reference Files

### Deep Dive Topics

- **`reference/process-shapes.md`** — All shapes with configuration details, behavior, and use cases
- **`reference/http-client.md`** — Authentication patterns, dynamic URLs, header configuration
- **`reference/datahub-connector.md`** — Hub Auth Token, batch operations, query filters
- **`reference/json-profiles.md`** — Profile best practices, Flow Type generation, request/response mapping
- **`reference/flow-service-server.md`** — Message action binding, async behavior, Flow integration
- **`reference/process-properties.md`** — DPP/DDP patterns, cross-process passing, Route shape
- **`reference/error-handling.md`** — Try/Catch, nested error handling, Stop shape
- **`reference/deployment.md`** — Atoms/Molecules/Clouds, packaged components, Integration Packs

### Project Examples

- **`examples/promotion-processes.md`** — Process A0-J implementation patterns for this project

---

## Best Practices

### Groovy Scripting

- **Always** call `dataContext.storeStream()` for each document (never skip output)
- Use `logger` for debugging (not `println` — output lost in cloud runtimes)
- Wrap in try/catch with `logger.severe()` for error logging
- Set DPP persistence flag to `false` by default (avoid storage bloat)

### HTTP Client

- Set custom headers via **Set Properties** before connector
- Use dynamic URL variables for parameterized endpoints
- Assign request/response profiles for structured data

### DataHub

- Pre-load mapping cache with batch query (avoid N+1 problem)
- Use match keys for upsert (auto-create or update)
- Limit query results (default: 100, adjust as needed)

### Flow Service

- Follow standard error response pattern (`success`, `errorCode`, `errorMessage`)
- Design for async (>30s) — return meaningful status
- Use uppercase snake_case for error codes

### Process Design

- Use **Branch** for parallel execution (all paths run)
- Use **Decision** for conditional routing (if-then-else)
- Use **Route** for modular subprocesses
- Use **Try/Catch** to prevent failures (not Stop shape)

---

**Total Lines**: ~448 (within 500-line limit)

**Navigation**: Start here for quick reference → dive into `reference/` files for deep detail → see `examples/` for project-specific patterns.

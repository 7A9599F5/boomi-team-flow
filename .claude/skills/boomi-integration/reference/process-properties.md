# Process Properties Reference

Complete guide to process properties, dynamic process properties (DPPs), dynamic document properties (DDPs), and cross-process property passing.

---

## Overview

**Process Properties** are name/value pairs used to store data that persists across process steps and (optionally) across executions.

**Property Types**:

| Type | Scope | Persistence | Use Cases |
|------|-------|-------------|-----------|
| **Process Property Component** | Process-wide | Static (design time) | Configuration values, environment settings |
| **Dynamic Process Property (DPP)** | Process-wide | Runtime (execution) | Counters, loop state, cross-step data |
| **Dynamic Document Property (DDP)** | Per-document | Per-document | Source IDs, file names, custom metadata |
| **Execution Property** | Process-wide | Read-only | Account ID, execution ID, process name |

---

## Process Property Components

### Definition

**Type**: Reusable component containing key/value pairs.

**Configuration**:
```yaml
Component Name: PROMO - Config
Component Type: Process Properties
Keys:
  - primaryAccountId: account-12345
  - maxRetries: 3
  - apiBaseUrl: https://api.boomi.com/api/rest/v1
  - branchPrefix: promo-
```

**Use Cases**:
- Environment-specific configuration (dev vs prod)
- Shared constants across processes
- Connection strings, API URLs, timeouts

---

### Access in Groovy Scripts

**Read Property**:
```groovy
import com.boomi.execution.ExecutionUtil

String accountId = ExecutionUtil.getProcessProperty("PROMO - Config", "primaryAccountId")
String apiUrl = ExecutionUtil.getProcessProperty("PROMO - Config", "apiBaseUrl")
```

**Write Property** (runtime update):
```groovy
ExecutionUtil.setProcessProperty("PROMO - Config", "retryCount", "1")
```

**Note**: Write updates are **runtime only** (not persisted to component definition).

---

### Access in Set Properties Shape

**Configuration**:
```yaml
Set Properties Shape:
  Properties:
    - Name: document.dynamic.userdefined.accountId
      Value: {process.property.PROMO - Config.primaryAccountId}
      Type: Process Property
```

**Dynamic URL Example** (HTTP Client):
```
Resource Path: {process.property.PROMO - Config.apiBaseUrl}/{1}/Component/{2}
  → https://api.boomi.com/api/rest/v1/account-123/Component/comp-456
```

---

## Dynamic Process Properties (DPPs)

### Characteristics

- **Created on-the-fly** (not pre-defined)
- **Shared across all documents** in the batch
- **Runtime scope** (cleared after execution by default)
- **Can be persisted** across executions (optional)

---

### Access in Groovy Scripts

**Read DPP**:
```groovy
String value = ExecutionUtil.getDynamicProcessProperty("counterValue")

// Handle null (property not set)
String value = ExecutionUtil.getDynamicProcessProperty("counterValue")
if (value == null) {
    value = "0"
}
```

**Write DPP (Non-Persisted)**:
```groovy
ExecutionUtil.setDynamicProcessProperty("counterValue", "42", false)
```

**Write DPP (Persisted)**:
```groovy
ExecutionUtil.setDynamicProcessProperty("lastRunTimestamp", "2026-02-16T10:30:00Z", true)
```

**Persistence Flag** (3rd parameter):
- **`false`** (default): Cleared after execution (recommended)
- **`true`**: Persisted across executions (use sparingly)

---

### Persistence Flag Guidance

**Non-Persisted (`false`) — Default**:
- **Use Case**: In-execution state (loop counters, caching, intermediate results)
- **Behavior**: Cleared after execution completes
- **Performance**: Fast (in-memory only)
- **Storage**: No storage cost

**Persisted (`true`) — Use Sparingly**:
- **Use Case**: Cross-execution state (last run timestamp, sequence counters)
- **Behavior**: Survives across executions
- **Performance**: Slower (database write)
- **Storage**: Consumes account storage quota

**Warning**: Over-using persisted DPPs can lead to:
- Storage quota exceeded
- Performance degradation
- Stale data (hard to debug)

**Best Practice**: Default to `false` (non-persisted) unless you have a specific need for cross-execution state.

---

### Use Cases (Project-Specific)

**1. Visited Set (Dependency Traversal)**:
```groovy
// Process B - build-visited-set.groovy
String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
def visitedSet = visitedJson ? new JsonSlurper().parseText(visitedJson) : []

// Add current component
visitedSet << currentId

// Update DPP (non-persisted)
ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
```

**2. Component Mapping Cache**:
```groovy
// Process C - Pre-load all mappings to avoid N+1 queries
String cacheJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
def cache = cacheJson ? new JsonSlurper().parseText(cacheJson) : [:]

// Store mapping
cache[devId] = prodId

// Update DPP (non-persisted)
ExecutionUtil.setDynamicProcessProperty("componentMappingCache", JsonOutput.toJson(cache), false)
```

**3. Loop Control**:
```groovy
// Increment counter
String countStr = ExecutionUtil.getDynamicProcessProperty("loopCount") ?: "0"
int count = Integer.parseInt(countStr)
count++
ExecutionUtil.setDynamicProcessProperty("loopCount", count.toString(), false)

// Check limit
if (count > 100) {
    logger.severe("Loop limit exceeded (100 iterations)")
    ExecutionUtil.setDynamicProcessProperty("loopExceeded", "true", false)
}
```

---

## Dynamic Document Properties (DDPs)

### Characteristics

- **Attached to individual documents**
- **Each document has its own property set**
- **Follows document through transformations**
- **Not shared across documents**

---

### Access in Groovy Scripts

**Read DDP**:
```groovy
Properties props = dataContext.getProperties(i)

String fileName = props.getProperty("document.dynamic.userdefined.fileName")
String sourceId = props.getProperty("document.dynamic.userdefined.sourceRecordId")
```

**Write DDP**:
```groovy
props.setProperty("document.dynamic.userdefined.fileName", "output.json")
props.setProperty("document.dynamic.userdefined.sourceRecordId", "12345")
```

**Property Naming Convention**:
```
document.dynamic.userdefined.{propertyName}
  → User-defined properties (custom)

document.dynamic.connector.{connectorProperty}
  → Connector-tracked properties (e.g., httpStatusCode, fileName)

document.property.metadata.{metadataProperty}
  → Metadata properties (e.g., trycatchmessage)
```

---

### Access in Set Properties Shape

**Configuration**:
```yaml
Set Properties Shape:
  Properties:
    - Name: document.dynamic.userdefined.fileName
      Value: output.json
      Type: Static
    - Name: document.dynamic.userdefined.timestamp
      Value: {function:CurrentDate}
      Type: Function
```

---

### Connector Properties (Read-Only)

**HTTP Client**:
```
document.dynamic.connector.httpStatusCode → HTTP status code (200, 404, etc.)
document.dynamic.connector.responseHeaders → HTTP response headers
```

**File Connector**:
```
document.dynamic.connector.fileName → File name
document.dynamic.connector.filePath → Full file path
document.dynamic.connector.fileSize → File size (bytes)
```

**Database Connector**:
```
document.dynamic.connector.rowCount → Number of rows retrieved
```

---

### HTTP Header Properties

**Pattern**: `document.dynamic.userdefined.http.header.{HeaderName}`

**Example**:
```
Set Properties Step:
  - document.dynamic.userdefined.http.header.Authorization = Bearer abc123
  - document.dynamic.userdefined.http.header.Content-Type = application/json

↓

HTTP Client Connector (headers auto-applied)
```

**See**: `http-client.md` for HTTP header configuration.

---

## Execution Properties (Read-Only)

### Available Properties

| Property | Description | Example |
|----------|-------------|---------|
| `accountId` | Boomi account ID | `yourcompany-ABC123` |
| `executionId` | Unique execution ID | `exec-abc-123-xyz` |
| `processName` | Process name | `PROMO - Process C - Execute Promotion` |
| `processId` | Process component ID | `proc-456-def-789` |
| `userName` | User who initiated execution | `user@example.com` |
| `runtimeId` | Atom/Molecule/Cloud ID | `cloud-us-east-1` |

---

### Access in Groovy Scripts

**Read Execution Property**:
```groovy
String executionId = ExecutionUtil.getRuntimeExecutionProperty("executionId")
String accountId = ExecutionUtil.getRuntimeExecutionProperty("accountId")
String processName = ExecutionUtil.getRuntimeExecutionProperty("processName")

logger.info("Execution ID: ${executionId}")
logger.info("Account ID: ${accountId}")
logger.info("Process: ${processName}")
```

**Use Cases**:
- Logging (include execution ID for troubleshooting)
- Audit trails (track which process executed which operation)
- Dynamic logic (execute different code based on account ID)

---

## Cross-Process Property Passing

### Route Shape Property Mapping

**Scenario**: Calling process has DPP `devAccountId`, subprocess needs it as DPP `targetAccountId`.

**Configuration**:
```yaml
Route Shape:
  Process Route Component: PROMO - Route - ProcessComponent
  Passthrough: true
  Process Properties:
    - Source: devAccountId (DPP from calling process)
      Target: targetAccountId (DPP in subprocess)
```

**Behavior**:
1. Route shape reads `devAccountId` DPP from calling process
2. Sets `targetAccountId` DPP in subprocess
3. Subprocess executes with `targetAccountId` available

---

### Static Property Passing

**Scenario**: Calling process wants to pass static values to subprocess.

**Configuration**:
```yaml
Route Shape:
  Process Route Component: PROMO - Route - Validation
  Process Properties:
    - Source: [Static Value: "PRODUCTION"]
      Target: environment (subprocess DPP)
```

---

### Process Property Component Passing

**Scenario**: Calling process wants subprocess to use different Process Property component.

**Configuration**:
```yaml
Route Shape:
  Process Route Component: PROMO - Route - Transform
  Process Properties:
    - Source: [Process Property: PROMO - Config.apiBaseUrl]
      Target: apiUrl (subprocess DPP)
```

---

## Best Practices

### DPPs (Dynamic Process Properties)

**Default to Non-Persisted**:
```groovy
// Good (non-persisted)
ExecutionUtil.setDynamicProcessProperty("loopCount", "42", false)

// Bad (persisted unnecessarily)
ExecutionUtil.setDynamicProcessProperty("loopCount", "42", true)
```

**Use JSON for Complex Data**:
```groovy
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

// Store complex data (arrays, maps)
def visitedSet = ["comp-123", "comp-456", "comp-789"]
ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)

// Retrieve complex data
String json = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
def visitedSet = new JsonSlurper().parseText(json)
```

**Initialize DPPs Before Use**:
```groovy
// Good (handle null)
String countStr = ExecutionUtil.getDynamicProcessProperty("loopCount")
int count = countStr ? Integer.parseInt(countStr) : 0

// Bad (NullPointerException if DPP not set)
int count = Integer.parseInt(ExecutionUtil.getDynamicProcessProperty("loopCount"))
```

---

### DDPs (Dynamic Document Properties)

**Use for Per-Document Metadata**:
```groovy
// Good (per-document metadata)
props.setProperty("document.dynamic.userdefined.sourceRecordId", "12345")
props.setProperty("document.dynamic.userdefined.fileName", "order_12345.json")

// Bad (should use DPP instead)
props.setProperty("document.dynamic.userdefined.accountId", "account-123")
```

**Naming Convention**:
- Use **camelCase**: `fileName`, `sourceRecordId`, `customerId`
- Avoid underscores: `file_name`, `source_record_id`

---

### Process Property Components

**Environment-Specific Configuration**:
```yaml
Component: PROMO - Config - DEV
Keys:
  - apiBaseUrl: https://api-dev.boomi.com
  - maxRetries: 5 (more retries in dev)

Component: PROMO - Config - PROD
Keys:
  - apiBaseUrl: https://api.boomi.com
  - maxRetries: 3
```

**Use in Process**: Reference appropriate component based on environment.

---

### Execution Properties

**Logging Pattern**:
```groovy
String executionId = ExecutionUtil.getRuntimeExecutionProperty("executionId")
logger.info("[${executionId}] Processing component: ${componentId}")
```

**Benefits**:
- Easier log filtering (search by execution ID)
- Easier troubleshooting (correlate logs across steps)

---

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **NullPointerException** | DPP not initialized | Check for null before use |
| **Property not found** | DPP/DDP typo or not set | Verify property name, initialize before use |
| **Persisted DPP quota exceeded** | Too many persisted DPPs | Switch to non-persisted (`false`) |
| **Route property not passed** | Route shape mapping missing | Configure property mapping in Route shape |

---

### Debugging DPPs

**Log DPP Values**:
```groovy
String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
logger.info("Visited component IDs: ${visitedJson}")

String cacheJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
logger.info("Mapping cache: ${cacheJson}")
```

**Check Execution Logs**:
- Navigate to **Process Reporting** → **Execution Logs**
- Search for execution ID
- Review log messages for DPP values

---

## Project-Specific Examples

### Process B — Dependency Traversal State

**DPPs Used**:
```groovy
// Visited set (JSON array)
visitedComponentIds: ["comp-123", "comp-456", "comp-789"]

// Component queue (JSON array)
componentQueue: ["comp-abc", "comp-def"]

// Current component being processed
currentComponentId: "comp-123"

// Already visited flag (boolean as string)
alreadyVisited: "false"
```

**Pattern**: Decision + Route loop with DPPs for state management.

---

### Process C — Mapping Cache

**DPP Used**:
```groovy
// Component mapping cache (JSON object)
componentMappingCache: {
  "dev-comp-123": "prod-comp-xyz",
  "dev-comp-456": "prod-comp-abc",
  ...
}
```

**Pattern**: Pre-load all mappings in one DataHub query, cache in DPP, use for reference rewriting.

---

## Related References

- `flow-service-server.md` — Flow Service request/response properties
- `http-client.md` — HTTP header properties
- `error-handling.md` — Error message properties (trycatchmessage)

# Flow Services — Message Actions and Integration Binding

## Overview

**Flow Service** is a component in Boomi Integration that exposes Integration processes as APIs that Flow applications can call. It acts as the bridge between Flow (frontend) and Integration (backend logic).

---

## Flow Service Component (in Integration)

### Location

**Boomi Integration** > **Components** > **Flow Service**

### Purpose

1. Define **Path to Service**: URI path for the connector
2. Map **Flow Service Operations** to Integration processes
3. Manage **callback logic** for async operations
4. Handle **timeouts** with wait responses

### Key Properties

| Property | Description | Example |
|----------|-------------|---------|
| **Path to Service** | URI path for the connector (must be unique) | `/promotion-service` |
| **Operations** | Message Actions and Data Actions defined within the service | `executePromotion`, `queryStatus`, etc. |

**Connector URI pattern:**

```
https://{atom-host}/ws/rest/{Path-to-Service}
```

**Example:**

```
https://c01-usa-east.integrate.boomi.com/ws/rest/promotion-service
```

**Note:** Public Cloud Atoms use standard Boomi infrastructure URLs, avoiding firewall issues.

---

## Flow Service in Flow

### Location

**Flow** > **Services** > **Add Service** > **Boomi Integration Service**

### Configuration

| Field | Description | Example |
|-------|-------------|---------|
| **Connector Type** | Boomi Integration Service | (dropdown selection) |
| **Path to Service** | Matches the Flow Service's Path to Service in Integration | `/promotion-service` |
| **Authentication** | Boomi account credentials or token-based auth | Account: `my-account`, Username: `api-user`, Password: `{token}` |
| **Message Actions** | Available operations exposed by the Flow Service | `executePromotion`, `resolveDependencies`, `queryStatus`, etc. |

### Authentication Options

**Option 1: Account credentials**
- Account name
- Username
- Password (or API token)

**Option 2: Token-based auth**
- API token generated in Boomi AtomSphere
- Passed as HTTP Authorization header

---

## Flow Services Server Component

### What is the Flow Services Server?

The **Flow Services Server** is a **connector** in Boomi Integration that acts as a **listener** for incoming requests from Flow applications. It is the **Start shape** for all Integration processes that serve Flow.

**Connector name:** `Boomi Flow Services Server`

### How It Works

```
Flow Application
  ↓ (HTTP Request)
Flow Services Server Connector (Listen mode)
  ↓
Integration Process (Start shape)
  ↓
Business Logic (Maps, Decisions, API Calls, etc.)
  ↓
Return Response (JSON)
  ↓ (HTTP Response)
Flow Application (Receives response)
```

### Configuration

**Start Shape Setup:**

| Field | Value | Description |
|-------|-------|-------------|
| **Connector** | Boomi Flow Services Server | (dropdown selection) |
| **Operation** | Listen | Only supported action |
| **Service Type** | Message Action OR Data Action | Type of operation |
| **Message Action/Data Action** | Select from Flow Service component | Specific operation to handle |
| **Response Profile** | JSON profile | Defines response structure |

### Operation Limitations

**Not supported:**
- Arrays (Absolute)
- Lists containing simple elements or lists of lists (must contain objects)

**DateTime format required:**
```
yyyy-MM-dd'T'HH:mm:ss.SSS'Z'
```

**Example:** `2026-02-16T14:30:00.000Z`

**Low Latency mode:**
- Flow Services Server can only be used in Start step in **Low Latency mode**
- Ensure process is configured for Low Latency execution

**Source:** [Flow Services Server operation - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Integration/Connectors/r-atm-Flow_Services_Server_operation_39812d14-99b6-436a-8761-e5172ac6f0f1)

---

## Message Actions

### Purpose

Execute complex business logic and return custom responses.

### How They Work

1. **Flow** calls Message Action via **Message Step**
2. **Integration** process receives request, executes logic (API calls, data transformations, etc.)
3. **Process** returns custom response (JSON structure defined by developer)
4. **Flow** receives response and stores it in Flow Values

### Integration Setup

**Flow Service Component:**

```
Component: Flow Service
Path to Service: /promotion-service

Operations:
  Message Action: executePromotion
    - Request Profile: ExecutePromotionRequest (JSON)
    - Response Profile: ExecutePromotionResponse (JSON)

  Message Action: resolveDependencies
    - Request Profile: ResolveDependenciesRequest (JSON)
    - Response Profile: ResolveDependenciesResponse (JSON)

  ... (additional message actions)
```

**Integration Process:**

```
Start (Flow Services Server - Listen - Message Action: executePromotion)
  ↓
Data Process (Groovy: build-visited-set.groovy)
  ↓
Decision (if > 20 components)
  ↓ YES
Return Wait Response (Flow shows spinner)
  ↓
For-each loop (promote each component via Platform API)
  ↓
Map (build promotion results JSON)
  ↓
Return Response (Flow receives results, hides spinner)
```

**JSON Profiles:**

**Request Profile: ExecutePromotionRequest**

```json
{
  "componentId": "string",
  "devAccountId": "string",
  "dependencyTree": [
    {
      "componentId": "string",
      "componentName": "string",
      "componentType": "string",
      "action": "CREATE"
    }
  ]
}
```

**Response Profile: ExecutePromotionResponse**

```json
{
  "success": true,
  "promotionId": "uuid",
  "branchId": "uuid",
  "results": [
    {
      "componentId": "string",
      "componentName": "string",
      "action": "CREATE",
      "status": "SUCCESS",
      "errorMessage": null
    }
  ],
  "componentsPassed": 50,
  "componentsFailed": 0
}
```

### Flow Setup

**Message Step Configuration:**

```
Step Type: Message
Message Action: executePromotion
Service: Boomi Integration Service (/promotion-service)

Input Mapping:
  componentId ← selectedPackage.componentId
  devAccountId ← selectedDevAccountId
  dependencyTree ← dependencyTree

Output Mapping:
  promotionId ← response.promotionId
  branchId ← response.branchId
  promotionResults ← response
```

**Request/Response Types:**

Flow **automatically generates** Request and Response types based on the JSON profiles:

- **Type**: `ExecutePromotionRequest`
  - Properties: `componentId`, `devAccountId`, `dependencyTree`
- **Type**: `ExecutePromotionResponse`
  - Properties: `success`, `promotionId`, `branchId`, `results`, `componentsPassed`, `componentsFailed`

**Benefits:**
- Type safety in Flow canvas
- Automatic property binding in message steps
- Consistent type definitions between Integration and Flow

---

## Wait Responses and Async Operations

### The Problem

Long-running Integration processes (e.g., promoting 50 components) can take minutes to complete. Flow needs to:
1. Not timeout the HTTP request
2. Provide user feedback (loading state)
3. Allow user to close browser and resume later
4. Display results when operation completes

### The Solution: Wait Responses

**How it works:**

1. **User triggers operation**: Clicks "Promote" button
2. **Message Step calls Integration**: Flow sends request to Flow Service
3. **Process starts execution**: Integration process begins long-running operation
4. **Wait response sent**: If operation will take > 30 seconds, process returns **wait response** to Flow
5. **Flow shows wait state**: Spinner/loading UI displayed to user
   - Message: "Promoting components to primary account..."
   - Optional: Progress indicator (if API provides updates)
   - Subtext: "This may take several minutes. You can safely close this window."
6. **State cached to IndexedDB**: Flow runtime caches state every 30 seconds
   - Includes: promotionId, request parameters, user context, Flow Values
7. **User can close browser**: State persisted in IndexedDB survives browser close/refresh
8. **Process completes**: Integration process finishes execution
9. **Callback to Flow**: Flow Service sends callback with final response
10. **Flow resumes**: If user still on page, Flow hides spinner and shows results
    - If user closed browser, Flow automatically resumes when user returns to URL

### Implementation

**Integration Process:**

```
Start (Flow Services Server - Listen)
  ↓
Decision: Will this take > 30 seconds?
  ↓ YES
Return Wait Response
  {
    "status": "WAIT",
    "message": "Promoting components to primary account...",
    "progress": 0
  }
  ↓
Continue processing in background
  ↓
For-each loop (promote each component)
  ↓ (Optional: Update progress)
Send Progress Update to Flow
  {
    "status": "WAIT",
    "message": "Processing component 5 of 50...",
    "progress": 10
  }
  ↓
Process completes
  ↓
Return Final Response
  {
    "status": "SUCCESS",
    "success": true,
    "promotionId": "uuid",
    "results": [...]
  }
```

**Flow:**

```
Message Step: executePromotion
  ↓
Flow receives wait response
  ↓
Show wait state overlay:
  - Spinner animation
  - "Promoting components to primary account..."
  - "Processing component 5 of 50..." (if progress available)
  - Progress bar (if progress available)
  - "This may take several minutes. You can safely close this window."
  ↓
Flow caches state to IndexedDB (every 30 seconds)
  ↓
User closes browser (optional)
  ↓
Process continues running
  ↓
Process completes, sends final response
  ↓
User returns to browser (if closed), navigates to flow URL
  ↓
Flow resumes from IndexedDB cache
  ↓
Flow receives final response, hides wait state
  ↓
Page 3: Promotion Status (results displayed)
```

### State Persistence

**Storage:** Browser IndexedDB (client-side)
**Frequency:** Every 30 seconds (automatic)
**Scope:** Per flow instance (unique URL with state ID)
**Survival:** Browser restart, tab close, network interruption
**Security:** No sensitive data stored (only Flow Values marked for persistence)

### Timeout Management

- Flow Service manages timeouts automatically
- No manual timeout configuration needed in most cases
- Process can run for minutes without Flow timing out
- Flow Service tracks execution status and resumes flow when complete

**Sources:**
- [Flow Service Timeouts - Boomi Community](https://community.boomi.com/s/article/Flow-Service-Timeouts)
- [Flow and Integration: Sync or Async?](https://community.boomi.com/s/article/Flow-and-Integration-Sync-or-Async)

---

## Data Actions

### Purpose

Perform standard CRUD operations (Create, Read, Update, Delete) on a specific data type.

### How They Work

1. **Flow** uses **Database Step** (Database Load, Database Save, Database Delete)
2. **Flow Service** Data Action maps to Integration process
3. **Process** performs CRUD operation and returns standardized response
4. **Flow** automatically handles the data according to step type

### Integration Setup

**Flow Service Component:**

```
Component: Flow Service
Path to Service: /customer-service

Operations:
  Data Action: Customer
    - Type: Customer
    - JSON Profile: CustomerProfile (JSON)
```

**Integration Process:**

```
Start (Flow Services Server - Listen - Data Action: Customer)
  ↓
Decision (Check operation type: GET, CREATE, UPDATE, DELETE)
  ↓ GET
Query DataHub or Database
  ↓
Map response to Customer JSON Profile
  ↓
Return Response
```

**JSON Profile: CustomerProfile**

```json
{
  "customerId": "string",
  "firstName": "string",
  "lastName": "string",
  "email": "string",
  "createdDate": "2026-02-16T14:30:00.000Z",
  "isActive": true
}
```

### Flow Setup

**Database Step Configuration:**

```
Step Type: Database Load
Service: Boomi Integration Service (/customer-service)
Type: Customer

Filters:
  customerId == selectedCustomerId

Output Mapping:
  customer ← response
```

### When to Use Data Actions

**Use Data Actions when:**
- Operations are standard CRUD
- You want to reuse the same Type across multiple flows
- You want Flow's built-in database step UX
- Consistency and simplicity are priorities

**Do NOT use Data Actions when:**
- Operations are complex (multi-step, custom logic)
- You need full control over request/response structure
- Operations don't fit CRUD patterns

**Project decision:** Promotion Dashboard uses **Message Actions exclusively** because operations are complex and don't fit CRUD patterns.

**Sources:**
- [Using Flow Service component Data Actions with Flow](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Getting_Started/Boomi_Flow_and_Boomi_Integration/Using_the_Flow_Service_component_with_Boomi_Flow/c-flo-FSS_Data_Actions_76d3fc99-d10d-46a1-b1b9-d19571bec6b6)
- [A worked example of using Integration Data Actions with Flow](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Getting_Started/Boomi_Flow_and_Boomi_Integration/A_worked_example_of_using_Boomi_Integration_Data_Actions_with_Boomi_Flow/c-flo-AS_Integration_Flow_Tutorial_Sim_f8255f8b-0e12-4a79-bf6d-307c56639e1d)

---

## Message Actions vs Data Actions: Decision Matrix

| Criteria | Message Actions | Data Actions |
|----------|----------------|--------------|
| **Operation type** | Complex, custom logic | Standard CRUD |
| **Response structure** | Custom JSON | Standardized by Type |
| **Request/Response types** | Unique per action | Shared across operations |
| **Flow step type** | Message Step | Database Step |
| **Reusability** | Per-action basis | Type-based (high reuse) |
| **Control level** | Full control | Framework-constrained |
| **Integration complexity** | Can be very complex | Usually simpler |
| **Use case** | Promotion execution, approval workflows, dependency resolution | Customer records, order management, simple data retrieval |

### When to Use Message Actions

- Complex multi-step operations (promotion, dependency resolution, diff generation)
- Custom calculations or aggregations
- External API calls (Platform API, third-party services)
- Operations that don't fit CRUD patterns
- Full control over request/response structure needed
- Each operation has unique requirements

### When to Use Data Actions

- Standard CRUD operations on a single record type
- Consistent data access patterns across multiple flows
- Simple read/write operations
- You want Flow's built-in database step UX
- Consistency and simplicity are priorities

---

## Error Handling

### Integration Process Error Handling

**Pattern:** Use Try/Catch to handle errors gracefully.

```
Start (Flow Services Server - Listen - Message Action: executePromotion)
  ↓
Try Block:
  ↓
  Business logic (API calls, data transformations, etc.)
  ↓
  Build success response
  ↓
  Return Response
Catch Block:
  ↓
  Log error
  ↓
  Build error response
    {
      "success": false,
      "errorCode": "COMPONENT_NOT_FOUND",
      "errorMessage": "Component not found in dev account."
    }
  ↓
  Return Response
```

### Flow Error Handling

**Pattern:** Use Decision step after Message step to check for errors.

```
Message Step: executePromotion
  ↓
Decision Step: Check Success
  ↓                    ↓
Outcome A            Outcome B
(success == true)    (success == false)
  ↓                    ↓
Page 3: Results      Error Page
```

**Decision Step Business Rules:**

- **Outcome A**: `promotionResults.success == $True`
- **Outcome B**: `promotionResults.success == $False`

**Error Page:**

```
Presentation: Error Message
  - Display: promotionResults.errorMessage

Button: "Retry"
  - Outcome: Return to Page 2 (allow user to retry)

Button: "Home"
  - Outcome: Return to Page 1
```

---

## Best Practices

### 1. Message Action Design

- **Clear naming**: Use camelCase, descriptive names (`executePromotion`, not `promote`)
- **Consistent structure**: All responses have `success` boolean and `errorCode`/`errorMessage` for failures
- **Type safety**: Define JSON profiles carefully, ensure properties match expected types
- **Error handling**: Always wrap business logic in Try/Catch blocks

### 2. Response Structure

**Standard response pattern:**

```json
{
  "success": true,
  "data": { /* operation-specific data */ },
  "errorCode": null,
  "errorMessage": null
}
```

**Error response pattern:**

```json
{
  "success": false,
  "data": null,
  "errorCode": "COMPONENT_NOT_FOUND",
  "errorMessage": "Component abc-123 not found in dev account xyz-456."
}
```

### 3. Async Operations

- **Return wait response** for operations expected to take > 30 seconds
- **Provide progress updates** if possible (e.g., "Processing component 5 of 50...")
- **Clear user messaging**: Tell users they can close browser and resume later
- **Test async resume**: Verify Flow correctly resumes from IndexedDB cache

### 4. Flow Service Configuration

- **Unique Path to Service**: Avoid conflicts with other Flow Services
- **Descriptive operation names**: Clear, self-documenting names
- **Version profiles carefully**: Changing JSON profiles breaks existing flows
- **Test in sandbox first**: Validate changes in non-production environment

### 5. Security

- **Never expose sensitive data**: Flow Service responses visible in browser dev tools
- **Use API tokens**: Avoid hardcoding passwords in Flow configuration
- **Validate inputs**: Always validate request data in Integration process
- **Audit trails**: Log all operations for compliance and debugging

---

## Troubleshooting

### Issue: Message step timeout

**Possible causes:**
1. Process taking too long without returning wait response
2. Flow Service Server not responding
3. Network connectivity issues

**Resolution:**
1. Add wait response logic for long-running operations
2. Check Flow Service Server process deployment (deployed to correct Atom/Cloud)
3. Verify network connectivity between Flow and Integration

### Issue: Response not matching JSON profile

**Possible causes:**
1. Integration process returning different structure than expected
2. JSON profile updated in Integration but not refreshed in Flow
3. Data type mismatch (string vs. number, etc.)

**Resolution:**
1. Validate Integration process response matches JSON profile exactly
2. Re-sync Flow Service in Flow (Services > Refresh)
3. Ensure data types match (use `.toString()` or `.toInteger()` in Groovy if needed)

### Issue: Flow not resuming after browser close

**Possible causes:**
1. IndexedDB disabled in browser
2. State ID not preserved in URL
3. Flow instance expired (> 24 hours old)

**Resolution:**
1. Enable IndexedDB in browser settings
2. Ensure user returns to same URL (with state ID query parameter)
3. For long-running flows, consider extending state expiration in Flow settings

---

## Sources

- [Using the Flow Service component with Flow](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Getting_Started/Boomi_Flow_and_Boomi_Integration/Using_the_Flow_Service_component_with_Boomi_Flow/c-flo-AS_Flow_Services_Component_f757eeb1-028b-4fac-b866-1f518817a8a9)
- [Message Actions with the Flow Services Server Component](https://community.boomi.com/s/article/Message-Actions-with-the-Flow-Services-Server-Component)
- [Flow Services Server operation - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Integration/Connectors/r-atm-Flow_Services_Server_operation_39812d14-99b6-436a-8761-e5172ac6f0f1)
- [Flow Service Timeouts - Boomi Community](https://community.boomi.com/s/article/Flow-Service-Timeouts)
- [Flow and Integration: Sync or Async?](https://community.boomi.com/s/article/Flow-and-Integration-Sync-or-Async)
- [Using Flow Service component Data Actions with Flow](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Getting_Started/Boomi_Flow_and_Boomi_Integration/Using_the_Flow_Service_component_with_Boomi_Flow/c-flo-FSS_Data_Actions_76d3fc99-d10d-46a1-b1b9-d19571bec6b6)

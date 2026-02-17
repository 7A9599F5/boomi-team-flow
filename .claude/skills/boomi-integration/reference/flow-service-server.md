# Flow Service Server Reference

Complete guide to using Flow Service Server to integrate Boomi Integration processes with Boomi Flow applications.

---

## Overview

**Flow Service** is a connector that enables Boomi Integration processes to act as backend APIs for Boomi Flow applications.

**Use Cases**:
- Flow dashboard needs to execute complex logic (multi-step integration)
- Flow needs to access external systems (Platform API, DataHub, databases)
- Flow needs to perform calculations or transformations beyond Flow capabilities

**Architecture**:
```
Flow Application (UI)
  ↓ Message Action
Flow Service Connector
  ↓ HTTPS
Integration Process (Listener)
  ↓ Processing Logic
Platform API / DataHub / Other Systems
```

---

## Flow Service Component

### Component Definition

**Type**: Boomi Flow Services

**Configuration**:
```yaml
Flow Service Component:
  Name: PROMO - Flow Service
  Path to Service: /fs/PromotionService
  Operations:
    - Message Action: getDevAccounts
      Request Profile: GetDevAccountsRequest
      Response Profile: GetDevAccountsResponse
    - Message Action: executePromotion
      Request Profile: ExecutePromotionRequest
      Response Profile: ExecutePromotionResponse
    ... (11 total operations)
```

**Path to Service**:
- URL path for the service (e.g., `/fs/PromotionService`)
- Exposed as: `https://{runtime-base-url}/fs/PromotionService`
- Must be unique per account

---

## Message Actions vs Data Actions

### Message Actions (Request/Response)

**Behavior**: Synchronous request/response (like REST API endpoints).

**Use Cases**:
- Complex logic requiring full process control
- Multi-step operations (query → transform → update)
- Error handling and validation
- **Recommended for this project**

**Configuration**:
```yaml
Message Action:
  Name: executePromotion
  Request Profile: ExecutePromotionRequest (JSON)
  Response Profile: ExecutePromotionResponse (JSON)
```

**Flow Integration**:
- Flow sends request → Integration process receives → processes → returns response
- Flow waits for response (or handles async wait)

---

### Data Actions (Simple CRUD)

**Behavior**: Direct database/API operations without custom logic.

**Use Cases**:
- Simple CRUD on DataHub universes
- Simple database queries
- **Not used in this project** (logic too complex for Data Actions)

**Limitations**:
- No custom logic (no Groovy scripts, no branching)
- No multi-step operations
- No error handling beyond HTTP status codes

**Why we use Message Actions**:
- This project requires complex logic (dependency traversal, credential stripping, reference rewriting)
- Message Actions provide full process control

---

## Listener Process

### Start Shape Configuration

**Connector**: Boomi Flow Services Server

**Action**: Listen

**Operation**: Select message action from Flow Service component

**Example**:
```yaml
Start Shape:
  Connector: Boomi Flow Services Server
  Connection: [Auto-configured, no manual setup]
  Action: Listen
  Operation: executePromotion
  Response Profile: ExecutePromotionRequest
```

**Response Profile**: Defines the structure of incoming request from Flow.

---

### Process Structure

**Standard Pattern**:
```
Start (Flow Service Server, Listen, {operation})
  ↓
[Processing Logic]
  ├─→ DataHub Connector (query/upsert)
  ├─→ HTTP Client (Platform API calls)
  ├─→ Map (transform data)
  ├─→ Decision (conditional logic)
  ├─→ Data Process (Groovy scripts)
  └─→ Try/Catch (error handling)
  ↓
Decision (check success)
  ├─→ True Path: Return success response
  └─→ False Path: Return error response
  ↓
End
```

**Key Points**:
- **Always return a response** (success or error)
- Follow standard error response pattern
- Use Try/Catch to prevent failures

---

### Response Construction

**Standard Response Structure** (from project):
```json
{
  "success": true | false,
  "errorCode": "ERROR_CODE_ENUM",
  "errorMessage": "Human-readable description",
  ... [operation-specific data]
}
```

**Success Response Example**:
```json
{
  "success": true,
  "errorCode": "",
  "errorMessage": "",
  "promotionId": "promo-123",
  "branchId": "branch-abc",
  "componentsCreated": 5,
  "componentsUpdated": 10,
  "results": [...]
}
```

**Error Response Example**:
```json
{
  "success": false,
  "errorCode": "MISSING_CONNECTION_MAPPINGS",
  "errorMessage": "Connection mappings not seeded for: HTTP-Salesforce, HTTP-NetSuite",
  "missingConnectionMappings": ["HTTP-Salesforce", "HTTP-NetSuite"]
}
```

**Map Shape** (construct response):
```
Data Process (build JSON)
  ↓
Map (to response profile)
  ↓
End (return response)
```

---

## Async Behavior

### Long-Running Operations

**Threshold**: Typically 30 seconds (configurable by Boomi).

**Behavior**:
1. Flow sends request → Integration process starts
2. After 30 seconds, if process still running → Flow Service returns **wait response**
3. Flow UI displays spinner/progress indicator
4. When process completes → Flow Service callbacks to Flow with final response
5. Flow UI updates with final response

**User Experience**:
- User sees spinner for long-running operations
- User can close browser tab (state persisted via IndexedDB)
- User can navigate away and return (Flow restores state)

**Project Examples**:
- `executePromotion`: 30-120 seconds (depends on component count)
- `packageAndDeploy`: 20-60 seconds (depends on target environment count)

**No Special Configuration**: Async behavior is automatic (handled by Flow Service).

---

### State Persistence (IndexedDB)

**Behavior**:
- Flow caches execution state in browser's IndexedDB
- User can close tab during long operation
- When user returns to Flow, state is restored
- User sees final response when operation completes

**Example**:
1. User clicks "Promote" → Flow sends `executePromotion` request
2. Integration process starts (takes 90 seconds)
3. After 30 seconds, Flow UI shows spinner
4. User closes browser tab
5. Process completes after 90 seconds
6. User reopens Flow → sees success message

---

## Flow Integration

### Connector Setup in Flow

**Steps**:
1. In Flow, navigate to **Integrations** → **Create Connector**
2. Select **Boomi Integration Service**
3. Configure connector:
   ```yaml
   Connector Name: Promotion Service
   Path to Service: /fs/PromotionService
   Environment: [Select runtime environment]
   ```
4. **Retrieve Connector Configuration Data**: Flow auto-discovers message actions

**Auto-Discovery**:
- Flow queries Flow Service for available operations
- Creates Flow Types from request/response profiles
- Creates message action bindings

---

### Flow Types (Auto-Generated)

**Naming Convention**:
- Request Type: `{ActionName} REQUEST - {ProfileEntryName}`
- Response Type: `{ActionName} RESPONSE - {ProfileEntryName}`

**Example**:
```
Message Action: executePromotion
Request Profile: ExecutePromotionRequest
Response Profile: ExecutePromotionResponse

Flow Types:
  - executePromotion REQUEST - ExecutePromotionRequest
  - executePromotion RESPONSE - ExecutePromotionResponse
```

**Usage**:
- **Message Step** in Flow references these types
- Map Flow values → request type fields
- Map response type fields → Flow values

---

### Message Step in Flow

**Configuration**:
```yaml
Message Step:
  Connector: Promotion Service
  Message Action: executePromotion
  Input Mapping:
    - Flow Value: devAccountId → Request Field: devAccountId
    - Flow Value: selectedComponents → Request Field: components
    - Flow Value: currentUser → Request Field: initiatedBy
  Output Mapping:
    - Response Field: success → Flow Value: operationSuccess
    - Response Field: promotionId → Flow Value: currentPromotionId
    - Response Field: errorMessage → Flow Value: errorMessage
```

**Conditional Logic** (based on response):
```
Message Step (executePromotion)
  ↓
Decision (operationSuccess = true?)
  ├─→ True: Navigate to Success Page
  └─→ False: Display Error Message
```

---

## Timeout Handling

### Default Timeout

**Listener Timeout**: 300 seconds (5 minutes) — configurable in runtime settings.

**Behavior**:
- If process exceeds timeout → Flow Service returns timeout error
- Process continues running (not killed)
- Response is lost (Flow does not receive it)

**Best Practice**: Design processes to complete within timeout or use async pattern.

---

### Process-Level Timeout

**Pattern**: Set timeout in process properties or operation config.

**Example**:
```yaml
HTTP Client Operation:
  Timeout: 60 seconds (per API call)
```

**Cumulative Timeout**:
- If process makes 5 API calls × 60 seconds each → 300 seconds total
- Exceeds listener timeout (300 seconds)
- **Solution**: Reduce individual timeouts or batch API calls

---

## Error Codes (Project-Specific)

### Standard Error Codes

| Code | Meaning | User Action |
|------|---------|-------------|
| `AUTH_FAILED` | API authentication failed | Check API token |
| `COMPONENT_NOT_FOUND` | Component ID invalid | Verify component exists |
| `DATAHUB_ERROR` | DataHub query/update failed | Contact admin |
| `MISSING_CONNECTION_MAPPINGS` | Connection mappings not seeded | Admin must seed mappings |
| `BRANCH_LIMIT_REACHED` | Too many active branches (20 max) | Wait for pending reviews to complete |
| `INVALID_REQUEST` | Request payload invalid | Check required fields |
| `PROCESS_FAILED` | Unexpected process error | Check logs, contact support |

### Error Handling in Processes

**Pattern**:
```
Try/Catch
  ├─→ Try Path:
  │     [Processing Logic]
  │     Decision (operation success?)
  │       ├─→ True: Set success response
  │       └─→ False: Set error response (errorCode, errorMessage)
  │
  └─→ Catch Path:
        Set Properties (capture trycatchmessage)
        Set error response (errorCode = PROCESS_FAILED, errorMessage = {trycatchmessage})
  ↓
End (return response)
```

**Benefits**:
- Flow always receives a valid response (never fails)
- User sees meaningful error message
- Logs capture error details for troubleshooting

---

## Deployment

### Runtime Selection

**Public Boomi Cloud** (recommended for Flow Service):
- No firewall configuration required
- Flow can access Flow Service over HTTPS
- Multi-tenant, auto-scaling
- **Used in this project**

**On-Premise Atom/Molecule**:
- Requires firewall rules (inbound HTTPS)
- Requires public IP or VPN
- More complex setup

**Configuration**:
```yaml
Deployment:
  Packaged Component: PROMO - Flow Service
  Environment: Production
  Runtime: Public Boomi Cloud
```

---

### Verify Deployment

**Steps**:
1. Navigate to **Runtime Management** → **Listeners**
2. Verify Flow Service operations are **Running**
3. Note Service URL: `https://{cloud-base-url}/fs/PromotionService`

**Test**:
```bash
curl -X POST https://{cloud-base-url}/fs/PromotionService/executePromotion \
  -H "Content-Type: application/json" \
  -d '{
    "devAccountId": "test",
    "prodAccountId": "test",
    "components": [],
    "initiatedBy": "test@example.com"
  }'
```

**Expected Response**: JSON with `success`, `errorCode`, `errorMessage` fields.

---

## Project-Specific Implementation

### 11 Integration Processes (Listener Processes)

| Process | Message Action | Request Fields | Response Fields | Est. Duration |
|---------|----------------|----------------|-----------------|---------------|
| **A0** | `getDevAccounts` | (empty) | `devAccounts[]` | <1s |
| **A** | `listDevPackages` | `devAccountId` | `packages[]` | 1-5s |
| **B** | `resolveDependencies` | `devAccountId`, `componentId` | `dependencies[]` | 5-30s |
| **C** | `executePromotion` | `devAccountId`, `components[]` | `promotionId`, `results[]` | 30-120s |
| **D** | `packageAndDeploy` | `branchId`, `promotionId` | `integrationPackId` | 20-60s |
| **E** | `queryStatus` | `reviewStage` | `promotions[]` | 1-5s |
| **E2** | `queryPeerReviewQueue` | (empty) | `promotions[]` | 1-5s |
| **E3** | `submitPeerReview` | `promotionId`, `action`, `comments` | `success` | 1-3s |
| **F** | `manageMappings` | `action`, `mapping` | `success` | 1-3s |
| **G** | `generateComponentDiff` | `promotionId`, `componentId` | `branchXml`, `mainXml` | 2-10s |
| **J** | `listIntegrationPacks` | `devAccountId` | `packs[]` | 1-5s |

**Async Operations** (>30s):
- `executePromotion` (Process C)
- `packageAndDeploy` (Process D)
- `resolveDependencies` (Process B) — if large dependency tree

---

## Best Practices

### Response Design
- **Always return a response** (success or error)
- Follow standard error response pattern
- Include operation-specific data in success responses
- Use `errorCode` enum for programmatic error handling

### Error Handling
- Use **Try/Catch** to prevent failures
- Capture `trycatchmessage` property for error details
- Return `errorCode` + `errorMessage` to Flow
- Log errors for troubleshooting

### Performance
- Design for <30s execution (avoid async wait)
- Batch API calls when possible
- Cache lookups (DPPs) to reduce round trips
- Monitor execution logs for slow operations

### Testing
- Test each message action in isolation (use Test mode)
- Test error scenarios (missing data, invalid input, API failures)
- Test long-running operations (verify async behavior)
- Test timeout scenarios (verify graceful handling)

### Deployment
- Deploy to **Public Boomi Cloud** (simplest for Flow integration)
- Verify all listener operations are **Running** after deployment
- Test from Flow after deployment (end-to-end integration test)

---

## Related References

- `json-profiles.md` — Request/response profile configuration
- `process-properties.md` — Dynamic Process Properties for state management
- `error-handling.md` — Try/Catch patterns for Flow Service processes
- `deployment.md` — Flow Service deployment to Cloud runtime

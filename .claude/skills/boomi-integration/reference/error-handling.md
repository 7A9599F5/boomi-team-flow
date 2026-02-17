# Error Handling Reference

Complete guide to error handling patterns in Boomi Integration processes using Try/Catch, Stop shape, and error properties.

---

## Overview

**Error Handling** in Boomi enables processes to:
- Capture failures without terminating execution
- Log errors for troubleshooting
- Send notifications (email, Slack, etc.)
- Return meaningful error responses to Flow
- Implement retry logic

**Primary Mechanism**: **Try/Catch shape** (recommended)

**Deprecated Mechanism**: **Stop shape** (use sparingly)

---

## Try/Catch Shape

### Basic Behavior

**Flow**:
1. Documents enter **Try** path
2. Processing steps execute normally
3. **If a document fails** → sent to **Catch** path
4. **If a document succeeds** → continues on Try path
5. Other documents (that didn't fail) continue on Try path

**Key Points**:
- **Per-document error handling** (not all-or-nothing)
- Original document and properties **preserved** in Catch path
- Try path continues for successful documents

---

### Configuration

**No Configuration Required**: Behavior is automatic.

**Example**:
```
Try/Catch
  ├─→ Try Path:
  │     → HTTP Client (call API)
  │     → Map (transform response)
  │     → Database (insert record)
  │     → End
  │
  └─→ Catch Path:
        → Set Properties (capture error message)
        → Notify (send email alert)
        → Database (log error)
        → End
```

---

### Error Message Property

**Property**: `document.property.metadata.base.trycatchmessage`

**Content**: Exception message from the failed step.

**Example Messages**:
```
HTTP Client failure:
  "HTTP request failed with status 404: Not Found"

Map failure:
  "Required field 'customerId' not found in source profile"

Database failure:
  "Connection timeout after 30 seconds"

Data Process failure:
  "NullPointerException at line 42 in script build-visited-set.groovy"
```

---

### Capturing Error Message

**Set Properties Shape**:
```yaml
Set Properties Shape:
  Properties:
    - Name: document.dynamic.userdefined.errorMessage
      Value: {property:document.property.metadata.base.trycatchmessage}
      Type: Property
```

**Groovy Script**:
```groovy
Properties props = dataContext.getProperties(i)
String errorMsg = props.getProperty("document.property.metadata.base.trycatchmessage")

logger.severe("Error occurred: ${errorMsg}")
props.setProperty("document.dynamic.userdefined.errorMessage", errorMsg)
```

---

### Use Cases

**1. API Failure Recovery**:
```
Try/Catch
  ├─→ Try Path:
  │     → HTTP Client (call external API)
  │     → Map (process response)
  │     → End
  │
  └─→ Catch Path:
        → Set Properties (capture error)
        → HTTP Client (fallback API)
        → End
```

**2. Error Logging**:
```
Try/Catch
  ├─→ Try Path:
  │     → Database (insert record)
  │     → End
  │
  └─→ Catch Path:
        → Set Properties (capture error)
        → Database (insert error log)
        → End
```

**3. Error Notification**:
```
Try/Catch
  ├─→ Try Path:
  │     → [Processing Logic]
  │     → End
  │
  └─→ Catch Path:
        → Set Properties (capture error)
        → Message (send email to admin)
        → End
```

**4. Flow Service Error Response**:
```
Try/Catch
  ├─→ Try Path:
  │     → [Processing Logic]
  │     → Decision (check success)
  │       ├─→ True: Return success response
  │       └─→ False: Return error response
  │
  └─→ Catch Path:
        → Set Properties (errorCode = PROCESS_FAILED, errorMessage = {trycatchmessage})
        → Return error response
        → End
```

---

## Nested Try/Catch

### Behavior

- **Inner Try/Catch** captures errors from nested steps
- **Outer Try/Catch** captures errors from inner Try/Catch and other steps

**Example**:
```
Outer Try/Catch
  ├─→ Outer Try Path:
  │     → Inner Try/Catch
  │       ├─→ Inner Try Path:
  │       │     → HTTP Client (call API)
  │       │     → End
  │       │
  │       └─→ Inner Catch Path:
  │             → Set Properties (retry flag = true)
  │             → Route (retry API call)
  │             → End
  │     → Decision (retry succeeded?)
  │       ├─→ True: Continue processing
  │       └─→ False: Throw error (caught by outer)
  │
  └─→ Outer Catch Path:
        → Set Properties (capture error)
        → Message (send alert)
        → End
```

**Use Cases**:
- Multi-level error handling (retry → escalate)
- Granular error recovery (different logic per step)

---

## Stop Shape

### Behavior

**Purpose**: Immediately halts process execution.

**Impact**:
- Terminates execution for **ALL documents** in the batch
- No downstream steps are executed
- Process execution is marked as **failed**

**Use Cases** (rare):
- Critical validation failure (e.g., missing required configuration)
- Emergency shutdown logic
- Testing/debugging

**Warning**: Stop is aggressive — prefer **Decision** shape with branching for conditional logic.

---

### Configuration

**No Configuration Required**: Stops execution immediately.

**Example**:
```
Decision (config missing?)
  ├─→ True: Stop (halt execution)
  └─→ False: Continue processing
```

---

### When to Use

**Use Stop Shape**:
- Pre-flight validation fails (e.g., required connection not configured)
- Critical security check fails (e.g., unauthorized access attempt)
- Testing/debugging (force process to halt at specific point)

**Do NOT Use Stop Shape**:
- Normal error handling (use **Try/Catch** instead)
- Conditional routing (use **Decision** shape instead)
- Flow control (use **Decision** + **Branch** instead)

---

## Error Response Patterns

### Flow Service Error Response (Project Standard)

**Structure**:
```json
{
  "success": false,
  "errorCode": "ERROR_CODE_ENUM",
  "errorMessage": "Human-readable description"
}
```

**Error Codes** (from project):

| Code | Meaning | Recovery Action |
|------|---------|-----------------|
| `AUTH_FAILED` | API authentication failed | Check API token, regenerate if expired |
| `COMPONENT_NOT_FOUND` | Component ID invalid | Verify component exists in account |
| `DATAHUB_ERROR` | DataHub query/update failed | Check DataHub connectivity, retry |
| `MISSING_CONNECTION_MAPPINGS` | Connection mappings not seeded | Admin must seed connection mappings |
| `BRANCH_LIMIT_REACHED` | Too many active branches (20 max) | Wait for pending reviews to complete, delete stale branches |
| `INVALID_REQUEST` | Request payload invalid | Check required fields, validate format |
| `PROCESS_FAILED` | Unexpected process error | Check logs, contact support |

---

### Process Pattern (Flow Service Listener)

```
Try/Catch
  ├─→ Try Path:
  │     → [Processing Logic: DataHub, HTTP Client, Map, etc.]
  │     → Decision (operation success?)
  │       ├─→ True Path:
  │       │     → Data Process (build success response JSON)
  │       │     → Map (to response profile)
  │       │     → End
  │       │
  │       └─→ False Path:
  │             → Data Process (build error response JSON)
  │             → Map (to response profile)
  │             → End
  │
  └─→ Catch Path:
        → Set Properties (capture trycatchmessage)
        → Data Process (build error response: errorCode = PROCESS_FAILED)
        → Map (to response profile)
        → End
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
  "componentsUpdated": 10
}
```

**Error Response Example** (business logic error):
```json
{
  "success": false,
  "errorCode": "MISSING_CONNECTION_MAPPINGS",
  "errorMessage": "Connection mappings not seeded for: HTTP-Salesforce, HTTP-NetSuite",
  "missingConnectionMappings": ["HTTP-Salesforce", "HTTP-NetSuite"]
}
```

**Error Response Example** (process failure):
```json
{
  "success": false,
  "errorCode": "PROCESS_FAILED",
  "errorMessage": "HTTP request failed with status 500: Internal Server Error"
}
```

---

## Retry Logic Patterns

### Simple Retry (Fixed Delay)

**Pattern**: Decision + Route loop with retry counter.

```
Set Properties (retryCount = 0)
  ↓
Try/Catch
  ├─→ Try Path:
  │     → HTTP Client (call API)
  │     → Decision (status = 200?)
  │       ├─→ True: Success path
  │       └─→ False: Continue to Catch
  │
  └─→ Catch Path:
        → Set Properties (capture error)
        → Decision (retryCount < 3?)
          ├─→ True:
          │     → Set Properties (retryCount++)
          │     → Wait (5 seconds)
          │     → Route (call self - retry)
          └─→ False:
                → Permanent failure (return error)
```

**DPP-Based Retry**:
```groovy
// Increment retry counter
String countStr = ExecutionUtil.getDynamicProcessProperty("retryCount") ?: "0"
int count = Integer.parseInt(countStr)
count++
ExecutionUtil.setDynamicProcessProperty("retryCount", count.toString(), false)

logger.info("Retry attempt ${count}")
```

---

### Exponential Backoff

**Pattern**: Increase wait time between retries.

```
Retry Attempt 1: Wait 2 seconds
Retry Attempt 2: Wait 4 seconds
Retry Attempt 3: Wait 8 seconds
Retry Attempt 4: Wait 16 seconds
```

**Implementation**:
```groovy
String countStr = ExecutionUtil.getDynamicProcessProperty("retryCount") ?: "0"
int count = Integer.parseInt(countStr)
int waitSeconds = Math.pow(2, count) as int

logger.info("Waiting ${waitSeconds} seconds before retry ${count + 1}")
ExecutionUtil.setDynamicProcessProperty("waitSeconds", waitSeconds.toString(), false)
```

**Wait Shape**: Use `{process.property.waitSeconds}` for dynamic delay.

---

### Retry Only Transient Errors

**Pattern**: Retry only if error is transient (500, 503, 429), not permanent (400, 404).

```
Try/Catch
  ├─→ Try Path:
  │     → HTTP Client (call API)
  │     → End
  │
  └─→ Catch Path:
        → Set Properties (capture httpStatusCode)
        → Decision (status in [500, 503, 429]?)
          ├─→ True: Retry logic
          └─→ False: Permanent failure (return error)
```

---

## Error Logging Patterns

### Log to Database

**Pattern**: Insert error record to database for audit trail.

```
Try/Catch
  └─→ Catch Path:
        → Set Properties (capture error details)
        → Data Process (build error log JSON)
        → Database (insert error log)
        → End
```

**Error Log Schema**:
```sql
CREATE TABLE error_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    execution_id VARCHAR(255),
    process_name VARCHAR(255),
    error_message TEXT,
    error_timestamp DATETIME,
    document_data TEXT
);
```

---

### Log to DataHub

**Pattern**: Upsert error record to DataHub universe.

```
Try/Catch
  └─→ Catch Path:
        → Set Properties (capture error details)
        → Data Process (build error log JSON)
        → DataHub Connector (upsert error log)
        → End
```

---

### Log to External Service (Slack, Email, etc.)

**Pattern**: Send error notification to external service.

```
Try/Catch
  └─→ Catch Path:
        → Set Properties (capture error details)
        → Data Process (build notification JSON)
        → HTTP Client (POST to Slack webhook)
        → End
```

**Slack Webhook Example**:
```json
{
  "text": "Process PROMO - Execute Promotion failed",
  "attachments": [
    {
      "color": "danger",
      "fields": [
        { "title": "Execution ID", "value": "exec-abc-123" },
        { "title": "Error Message", "value": "HTTP request failed with status 500" },
        { "title": "Timestamp", "value": "2026-02-16T10:30:00Z" }
      ]
    }
  ]
}
```

---

## Best Practices

### Try/Catch Usage

**Always Use Try/Catch**:
- Flow Service listener processes (return error response, not fail)
- External API calls (network failures, timeouts)
- Database operations (connection issues, constraint violations)

**Don't Overuse Try/Catch**:
- Simple validation logic (use Decision shape instead)
- Every single step (too granular, harder to maintain)

---

### Error Messages

**Be Specific**:
```groovy
// Good
logger.severe("Component ${componentId} not found in account ${accountId}")

// Bad
logger.severe("Error occurred")
```

**Include Context**:
```groovy
// Good
logger.severe("[${executionId}] Failed to promote component ${componentId}: ${errorMsg}")

// Bad
logger.severe("Failed")
```

---

### Error Response Construction

**Always Return Valid JSON** (Flow Service):
```json
{
  "success": false,
  "errorCode": "PROCESS_FAILED",
  "errorMessage": "Detailed error message here"
}
```

**Never Return**:
- Empty response (Flow will timeout)
- Malformed JSON (Flow will fail to parse)
- Generic "Error" message (not helpful for troubleshooting)

---

### Retry Logic

**Limit Retries**: 3-5 attempts max (avoid infinite loops).

**Use Exponential Backoff**: Reduce load on failing systems.

**Retry Only Transient Errors**:
- **Retry**: 500, 503, 429 (server errors, rate limits)
- **Don't Retry**: 400, 401, 404 (client errors, permanent failures)

---

### Error Logging

**Log Execution ID**: Enables log correlation.

**Log Component/Process Name**: Helps identify source of error.

**Log Error Message**: Full exception message from Try/Catch.

**Log Input Data** (optional): Helps reproduce error.

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Try/Catch not triggering** | Error not thrown (returned error code instead) | Check for Decision logic before Try/Catch |
| **Empty trycatchmessage** | Error occurred before document entered Try path | Move Try/Catch earlier in process |
| **Infinite retry loop** | Retry counter not incremented | Verify DPP increment logic |
| **Flow Service timeout** | No response returned from Catch path | Always return response (success or error) |

---

### Debugging

**Check Execution Logs**:
1. Navigate to **Process Reporting** → **Execution Logs**
2. Search for execution ID
3. Review log messages (look for `logger.severe()` output)
4. Check for Try/Catch messages

**Test Error Scenarios**:
- Force API failure (invalid auth, bad URL)
- Force database failure (connection timeout)
- Force validation failure (missing required field)

**Verify Error Response**:
- Test Flow Service operation with invalid input
- Verify error response structure (success = false, errorCode, errorMessage)

---

## Project-Specific Examples

### Process C — Execute Promotion Error Handling

**Scenario**: Validate all connection mappings exist before promotion.

**Pattern**:
```
Data Process (validate-connection-mappings.groovy)
  → If missing mappings → Set DPP validationFailed = true
  ↓
Decision (validationFailed = true?)
  ├─→ True:
  │     → Data Process (build error response: errorCode = MISSING_CONNECTION_MAPPINGS)
  │     → End
  │
  └─→ False:
        → Continue with promotion
```

**Error Response**:
```json
{
  "success": false,
  "errorCode": "MISSING_CONNECTION_MAPPINGS",
  "errorMessage": "Connection mappings not seeded for: HTTP-Salesforce, HTTP-NetSuite",
  "missingConnectionMappings": ["HTTP-Salesforce", "HTTP-NetSuite"]
}
```

---

### Process B — Dependency Traversal Loop Limit

**Scenario**: Prevent infinite loop in dependency traversal.

**Pattern**:
```groovy
// Increment loop counter
String countStr = ExecutionUtil.getDynamicProcessProperty("loopCount") ?: "0"
int count = Integer.parseInt(countStr)
count++
ExecutionUtil.setDynamicProcessProperty("loopCount", count.toString(), false)

// Check limit
if (count > 1000) {
    logger.severe("Dependency traversal exceeded 1000 iterations - potential circular reference")
    ExecutionUtil.setDynamicProcessProperty("loopLimitExceeded", "true", false)
}
```

**Decision**:
```
Decision (loopLimitExceeded = true?)
  ├─→ True: Return error (circular dependency detected)
  └─→ False: Continue traversal
```

---

## Related References

- `flow-service-server.md` — Flow Service error response patterns
- `process-properties.md` — Error message properties (trycatchmessage)
- `http-client.md` — HTTP error codes and retry patterns

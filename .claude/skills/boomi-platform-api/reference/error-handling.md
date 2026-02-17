# Error Handling Reference

Error codes, rate limits, retry patterns, and security best practices.

---

## HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| **200** | Success | Continue |
| **202** | Accepted | Asynchronous request accepted, check status later |
| **204** | No Content | Success, no data returned |
| **400** | Bad Request | Fix malformed request |
| **401** | Unauthorized | Check credentials/token |
| **403** | Forbidden | Check permissions |
| **404** | Not Found | Verify resource ID |
| **410** | Gone | Endpoint invalid or deprecated |
| **503** | Service Unavailable | Retry with backoff |

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

**XML Format:**
```xml
<Error>
  <statusCode>403</statusCode>
  <errorMessage>Access denied due to insufficient permissions.</errorMessage>
</Error>
```

---

## Common Error Scenarios

### 401 Unauthorized

**Response:**
```json
{
  "@type": "Error",
  "statusCode": 401,
  "errorMessage": "Authentication failed. Invalid credentials."
}
```

**Causes:**
- Invalid username/password
- Invalid or expired API token
- Token format incorrect (missing `BOOMI_TOKEN.` prefix)

**Resolution:**
1. Verify credentials are correct
2. Generate new API token if expired
3. Check token format: `BOOMI_TOKEN.{email}:{token-string}`
4. Ensure credentials are base64-encoded for Basic Auth

---

### 403 Forbidden

**Response:**
```json
{
  "@type": "Error",
  "statusCode": 403,
  "errorMessage": "Access denied due to insufficient permissions."
}
```

**Causes:**
- Missing required privileges (`API`, `DEPLOY`, `PACKAGE_MANAGEMENT`)
- SSO user without API token
- `overrideAccount` used without management rights
- Attempting to modify read-only resources

**Resolution:**
1. Request required privileges from account administrator
2. Generate API token for SSO users
3. Verify account hierarchy for `overrideAccount` operations
4. Check resource permissions

---

### 404 Not Found

**Response:**
```json
{
  "@type": "Error",
  "statusCode": 404,
  "errorMessage": "Component not found."
}
```

**Causes:**
- Invalid resource ID (componentId, packageId, branchId, etc.)
- Resource was deleted
- Typo in endpoint URL
- Using wrong account (without `overrideAccount`)

**Resolution:**
1. Verify resource ID from query response
2. Check `deleted` status
3. Validate endpoint URL
4. Use `overrideAccount` for sub-account resources

---

### 503 Service Unavailable

**Response:**
```json
{
  "@type": "Error",
  "statusCode": 503,
  "errorMessage": "The Boomi server is currently unavailable or your account's rate limits have been exceeded. Retry later."
}
```

**Causes:**
- Rate limit exceeded (10 req/sec)
- Boomi server maintenance or outage
- Network connectivity issues

**Resolution:**
1. Implement exponential backoff retry
2. Wait before retrying (start with 2 seconds, double each retry)
3. Check Boomi status page for maintenance
4. Reduce request frequency

---

## Rate Limits

### Global Limit

**10 requests per second** per account

### Enforcement

When limit is exceeded, API returns **HTTP 503**:
```json
{
  "statusCode": 503,
  "errorMessage": "Rate limit exceeded. Retry later."
}
```

### Rate Limit Context

**Per-Account Limits:**
- Rate limits are **per account**
- Using `overrideAccount` with Partner API:
  - If `overrideAccountRateLimit` feature enabled: limits apply to **override account**
  - If disabled: limits apply to **authenticating (primary) account**

**Built-in UI Operations:**
- None of the built-in Boomi UI operations use the API
- Using AtomSphere UI does **not** consume API rate limits
- Only programmatic API calls count against limit

---

## Retry Strategy

### Exponential Backoff Pattern

**JavaScript Example:**
```javascript
async function apiCallWithRetry(apiCall, maxRetries = 5) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      if (error.status === 503 && attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000; // 2s, 4s, 8s, 16s, 32s
        console.log(`Rate limit hit. Retrying in ${delay}ms (attempt ${attempt}/${maxRetries})`);
        await sleep(delay);
      } else {
        throw error;
      }
    }
  }
}
```

**Groovy Example (Boomi Data Process):**
```groovy
def maxRetries = 5
def attempt = 1

while (attempt <= maxRetries) {
    try {
        def response = makeApiCall()
        return response // Success
    } catch (Exception e) {
        if (e.message.contains("503") && attempt < maxRetries) {
            def delay = Math.pow(2, attempt) * 1000
            logger.info("Rate limit hit. Retrying in ${delay}ms (attempt ${attempt}/${maxRetries})")
            Thread.sleep(delay as long)
            attempt++
        } else {
            throw e // Non-retryable or max retries reached
        }
    }
}
```

### When to Retry

**Retryable Errors (Transient):**
- ✅ **503 Service Unavailable** — Rate limit or server issue
- ✅ **202 Accepted** — Async operation in progress, poll for completion
- ✅ Network timeouts (connection issues)

**Non-Retryable Errors (Permanent):**
- ❌ **400 Bad Request** — Malformed request
- ❌ **401 Unauthorized** — Invalid credentials
- ❌ **403 Forbidden** — Insufficient permissions
- ❌ **404 Not Found** — Resource does not exist

**Retry Logic:**
```javascript
function isRetryable(statusCode) {
  return statusCode === 503; // Only retry 503
}

if (isRetryable(error.status)) {
  // Retry with exponential backoff
} else {
  // Fail immediately, surface error to user
}
```

---

## Platform API Connector Retry Behavior

**Built-in Retry Logic:**
- The Boomi-provided **Platform API Connector** and **Partner API Connector** automatically retry on HTTP 503
- Retries up to **5 times** with exponential backoff
- Transparent to the process

**When to Implement Manual Retry:**
- Using HTTP Client connector (manual API calls)
- Custom integrations outside Boomi
- Need custom retry logic (different backoff, more retries)

**For This Project:**
- Use Platform API Connector for automatic retries
- Implement manual retry only for custom HTTP Client calls

---

## Error Logging Best Practices

### What to Log

**DO Log:**
- ✅ Timestamp of error
- ✅ Operation attempted (endpoint, HTTP method)
- ✅ Status code and error message
- ✅ Request parameters (componentId, packageId, etc.)
- ✅ Retry attempt number
- ✅ User/account context

**Example Log Entry:**
```json
{
  "timestamp": "2024-11-20T10:05:32Z",
  "operation": "GET /Component/{componentId}",
  "statusCode": 404,
  "errorMessage": "Component not found",
  "parameters": {
    "componentId": "abc-123",
    "overrideAccount": "dev-xyz"
  },
  "retry": 0,
  "userId": "user@boomi.com"
}
```

**DON'T Log:**
- ❌ API tokens or passwords (plain text)
- ❌ Full Authorization headers
- ❌ Base64-encoded credentials
- ❌ Sensitive component configuration (encrypted values)

### Groovy Logging

```groovy
import java.util.logging.Logger

Logger logger = Logger.getLogger("PromotionEngine")

try {
    def response = makeApiCall()
} catch (Exception e) {
    logger.severe("API call failed: ${e.message}, componentId=${componentId}, attempt=${attempt}")
    throw e
}
```

---

## Security Best Practices

### API Token Management

**DO:**
- ✅ Store tokens in environment variables or secret managers
- ✅ Rotate tokens every **90 days**
- ✅ Revoke tokens immediately if compromised
- ✅ Use separate tokens for different integrations
- ✅ Mark token fields as **password type** in Dynamic Process Properties

**DON'T:**
- ❌ Hardcode tokens in code
- ❌ Commit tokens to version control
- ❌ Share tokens across multiple users
- ❌ Log tokens in plain text

### Credential Storage (Boomi)

**Dynamic Process Properties (DPP):**
```
Property Name: BOOMI_API_TOKEN
Property Type: Password
Property Value: BOOMI_TOKEN.user@boomi.com:abc123...
```

**Reference in HTTP Client:**
```
Authorization: Basic base64(${property.BOOMI_USERNAME}:${property.BOOMI_API_TOKEN})
```

**Why Password Type:**
- Encrypted at rest
- Masked in UI
- Not visible in logs

---

## Error Handling Patterns for This Project

### Process C: executePromotion

```javascript
try {
  // Pre-check branch count
  const branchCount = await queryBranches();
  if (branchCount >= 15) {
    return {
      errorCode: "BRANCH_LIMIT_REACHED",
      errorMessage: "Too many active promotions. Please wait for pending reviews to complete."
    };
  }

  // Create branch
  const branch = await createBranch({name: `promo-${promotionId}`});

  try {
    // Wait for ready
    await waitForBranchReady(branch.branchId);

    // Promote components
    for (const component of components) {
      await createComponentOnBranch(component.prodId, branch.branchId, component.xml);
    }

    return {status: "SUCCESS", branchId: branch.branchId};

  } catch (promotionError) {
    // Cleanup branch on failure
    await deleteBranch(branch.branchId);
    throw promotionError;
  }

} catch (error) {
  // Log error
  logger.error(`Promotion failed: ${error.message}`, {promotionId, error});

  // Return user-friendly error
  return {
    errorCode: error.code || "UNKNOWN_ERROR",
    errorMessage: error.message || "An unexpected error occurred"
  };
}
```

### Process D: packageAndDeploy

```javascript
const branchId = input.branchId;

try {
  // Merge branch to main
  const mergeRequest = await createMergeRequest({sourceBranchId: branchId, ...});
  await executeMergeRequest(mergeRequest.id);

  // Package component
  const pkg = await createPackagedComponent({componentId, packageVersion, shareable: true});

  // Deploy to environments
  for (const envId of targetEnvironments) {
    await deployPackage({environmentId: envId, packageId: pkg.packageId});
  }

  return {status: "SUCCESS", packageId: pkg.packageId};

} catch (error) {
  logger.error(`Deployment failed: ${error.message}`, {branchId, error});

  return {
    errorCode: error.code || "DEPLOYMENT_FAILED",
    errorMessage: error.message
  };

} finally {
  // ALWAYS delete branch (success or failure)
  try {
    await deleteBranch(branchId);
  } catch (deleteError) {
    logger.warn(`Failed to delete branch: ${deleteError.message}`, {branchId});
  }
}
```

---

## Project-Specific Error Codes

| Error Code | Meaning | User Action |
|------------|---------|-------------|
| **BRANCH_LIMIT_REACHED** | Too many active promotions (>= 15 branches) | Wait for pending reviews to complete |
| **MISSING_CONNECTION_MAPPINGS** | One or more connection mappings not found | Contact admin to seed connection mappings |
| **COMPONENT_NOT_FOUND** | Component does not exist in dev account | Verify component ID |
| **PROMOTION_FAILED** | Generic promotion failure | Check logs for details |
| **DEPLOYMENT_FAILED** | Deployment to environment failed | Check environment status, permissions |
| **MERGE_FAILED** | Branch merge failed | Check for conflicts (should not happen with OVERRIDE) |

---

## Error Response to User (Flow UI)

**Success:**
```json
{
  "status": "SUCCESS",
  "message": "Components promoted successfully",
  "branchId": "branch-uuid"
}
```

**Error:**
```json
{
  "status": "ERROR",
  "errorCode": "BRANCH_LIMIT_REACHED",
  "errorMessage": "Too many active promotions. Please wait for pending reviews to complete.",
  "userAction": "Wait for peer/admin reviews to complete, or contact admin to clean up stale branches."
}
```

**Flow Display:**
- Show `errorMessage` in notification/alert
- Show `userAction` as guidance
- Log `errorCode` for support/debugging

---

## Related References

- **`authentication.md`** — 401/403 errors, API token management
- **`branch-operations.md`** — Branch limit errors, cleanup patterns
- **`query-patterns.md`** — Query filter errors, pagination errors
- **`component-crud.md`** — Component operation errors

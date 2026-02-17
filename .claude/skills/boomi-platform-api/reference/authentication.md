# Authentication Reference

Authentication patterns for Boomi Platform API and Partner API.

---

## HTTP Basic Authentication

All API calls use **HTTP Basic Authentication**.

**Format:**
```
Authorization: Basic base64(username:password)
```

**Credentials:**
- **Username**: Boomi account email address
- **Password**: Either the account password OR an API token

**Example Header:**
```http
Authorization: Basic dXNlckBib29taS5jb206Qk9PTUlfVE9LRU4udXNlckBib29taS5jb206YWJjMTIzZGVmNDU2
```

---

## API Tokens

### When Required

**MUST use API tokens:**
- SSO users without Administrator privileges
- Users with Two-Factor Authentication (2FA) enabled

**MAY use password OR token:**
- Regular (non-SSO) users
- SSO users with Administrator privileges

**Best Practice:** Always use API tokens for programmatic access.

### Token Format

```
BOOMI_TOKEN.{email}:{token-string}
```

**Example:**
```
BOOMI_TOKEN.user@boomi.com:a1b2c3d4e5f6g7h8i9j0
```

### How to Generate

1. Log in to Boomi AtomSphere UI
2. Navigate to **Account Settings** → **API Tokens**
3. Click **Generate Token**
4. Copy and securely store the token (cannot retrieve later)

### Token Security

**DO:**
- ✅ Store tokens in environment variables or secret managers
- ✅ Rotate tokens periodically
- ✅ Use separate tokens for different integrations
- ✅ Revoke tokens immediately if compromised

**DON'T:**
- ❌ Hardcode tokens in code
- ❌ Commit tokens to version control
- ❌ Share tokens across multiple users
- ❌ Log tokens in plain text

---

## The `overrideAccount` Parameter (Partner API)

The Partner API's most powerful feature for multi-account operations.

### How It Works

1. **Authenticate as primary account** using primary account credentials
2. **Add `overrideAccount` parameter** to the request
3. **API executes as if authenticated as the sub-account**
4. **Primary account must have management rights** over the sub-account

### REST Implementation

**Query Parameter:**
```http
GET https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}
```

**Example:**
```http
GET https://api.boomi.com/partner/api/rest/v1/primary-abc123/Component/comp-uuid-456?overrideAccount=dev-xyz789

Authorization: Basic {primary-account-credentials}
```

### SOAP Implementation

**Request Body:**
```xml
<api:operation>
  <api:accountId>{devAccountId}</api:accountId>
  <!-- operation parameters -->
</api:operation>
```

### Authorization Model

**Requirements:**
- Primary account must be in the **parent hierarchy** of the dev account
- Primary account must have **management rights** over the sub-account
- Both accounts must be active and accessible

**Permissions:**
- All operations execute with the **permissions of the override account**
- Primary account privileges do not carry over
- If override account lacks a permission, the operation fails

### Rate Limit Behavior

**With `overrideAccountRateLimit` feature enabled:**
- Rate limits apply to the **override account**
- Each sub-account has independent 10 req/sec limit

**Without `overrideAccountRateLimit` feature:**
- Rate limits apply to the **authenticating (primary) account**
- All sub-account operations count against primary account's limit

### Use Cases in This Project

**Process A: listDevPackages**
```http
POST /partner/api/rest/v1/{primaryAccountId}/PackagedComponent/query?overrideAccount={devAccountId}
```
Query dev account's PackagedComponents.

**Process B: resolveDependencies**
```http
GET /partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}
```
Read component XML from dev account.

**Process C: executePromotion**
```http
GET /partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}
```
Fetch dev component before promoting to prod branch.

### Error Scenarios

**401 Unauthorized:**
- Primary account credentials are invalid

**403 Forbidden:**
- Primary account does not have management rights over sub-account
- Account hierarchy relationship does not exist

**404 Not Found:**
- `overrideAccount` ID is invalid or does not exist

---

## Authentication Error Handling

### Common Errors

**401 Unauthorized:**
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
- Verify credentials
- Generate new API token
- Check token format

---

**403 Forbidden:**
```json
{
  "@type": "Error",
  "statusCode": 403,
  "errorMessage": "Access denied due to insufficient permissions."
}
```

**Causes:**
- SSO user without API token
- Missing required API privileges (`API`, `DEPLOY`, `PACKAGE_MANAGEMENT`)
- `overrideAccount` parameter used without management rights

**Resolution:**
- Generate and use API token for SSO users
- Request required privileges from account administrator
- Verify account hierarchy for `overrideAccount` operations

---

## Security Best Practices

### Token Storage

**Environment Variables:**
```bash
export BOOMI_USERNAME="user@boomi.com"
export BOOMI_API_TOKEN="BOOMI_TOKEN.user@boomi.com:a1b2c3d4e5f6"
```

**Boomi Process Properties:**
- Store tokens in **Dynamic Process Properties (DPP)**
- Mark as **password** type for encryption at rest
- Reference via `${property.name}` in HTTP Client connector

**Secret Managers:**
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

### Token Rotation

**Recommended Schedule:**
- Rotate tokens every **90 days**
- Rotate immediately if token is compromised
- Rotate when team members leave

**Rotation Process:**
1. Generate new token in AtomSphere UI
2. Update environment variables/DPP/secret manager
3. Test API calls with new token
4. Revoke old token after successful validation

### Audit Logging

**Log Authentication Events:**
- Successful API calls (timestamp, user, operation)
- Failed authentication attempts (timestamp, user, error)
- Token generation/revocation events

**DO NOT LOG:**
- ❌ API tokens or passwords in plain text
- ❌ Full Authorization headers
- ❌ Base64-encoded credentials

---

## Platform API vs Partner API Decision Matrix

| Use Case | API Type | Why |
|----------|----------|-----|
| Operate on own account | Platform API | Simpler, no `overrideAccount` needed |
| Read from sub-accounts | Partner API | Requires `overrideAccount` |
| Manage sub-account resources | Partner API | Requires `overrideAccount` |
| Deploy to own environments | Platform API | Standard deployment |
| Cross-account provisioning | Partner API | Account hierarchy operations |

**For This Project:**
- Use **Partner API** for all operations (unified interface)
- Use `overrideAccount` for dev account reads (Process A, B, C)
- Authenticate as **primary account** for all operations

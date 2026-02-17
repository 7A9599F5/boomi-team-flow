# HTTP Client Connector Reference

Complete guide to configuring and using the Boomi HTTP Client connector for REST/SOAP API integration.

---

## Connection Configuration

### Basic Settings

```yaml
HTTP Client Connection:
  Name: Platform API Connection
  URL: https://api.boomi.com/api/rest/v1
  Authentication Type: [None | Basic | Password Digest | OAuth 2.0 | AWS Signature | Client Certificate]
```

**URL Field**:
- Base URL of the server
- Can be overridden in operation
- Example: `https://api.example.com` or `https://api.boomi.com/api/rest/v1`

---

## Authentication Types

### None

**Use Case**: Public APIs with no authentication required.

**Configuration**: No additional fields.

**Example**:
```yaml
Authentication Type: None
URL: https://api.publicapis.org/entries
```

---

### Basic Authentication

**Use Case**: Username/password authentication (most common for Boomi Platform API).

**Configuration**:
```yaml
Authentication Type: Basic
User Name: your-username
Password: your-password-or-api-token
```

**How It Works**:
- Credentials are Base64-encoded as `username:password`
- Sent as `Authorization: Basic {base64Encoded}` header
- **Not secure over HTTP** (always use HTTPS)

**Example** (Boomi Platform API):
```yaml
User Name: yourcompany.prodaccount-ABCD
Password: your-api-token-12345abcde
```

**Authorization Header** (auto-generated):
```
Authorization: Basic eW91cmNvbXBhbnkucHJvZGFjY291bnQtQUJDRDp5b3VyLWFwaS10b2tlbi0xMjM0NWFiY2Rl
```

---

### OAuth 2.0

**Use Case**: Industry-standard token-based authentication for SaaS APIs.

**Grant Types**:

#### Authorization Code (3-Legged OAuth)

**Use Case**: User-delegated access (user logs in, grants permission).

**Configuration**:
```yaml
Authentication Type: OAuth 2.0
Grant Type: Authorization Code
Authorization URL: https://accounts.example.com/oauth/authorize
Token URL: https://accounts.example.com/oauth/token
Client ID: your-client-id
Client Secret: your-client-secret
Scope: read write
```

**Flow**:
1. User redirected to Authorization URL
2. User logs in and grants permission
3. Authorization server returns authorization code
4. Boomi exchanges code for access token via Token URL
5. Access token used for API requests

#### Resource Owner Password Credentials (2-Legged OAuth)

**Use Case**: Direct username/password exchange (less secure, avoid if possible).

**Configuration**:
```yaml
Grant Type: Resource Owner Password Credentials
Token URL: https://api.example.com/oauth/token
Client ID: your-client-id
Client Secret: your-client-secret
Username: user@example.com
Password: userpassword
Scope: api
```

#### Client Credentials (App-to-App)

**Use Case**: Machine-to-machine authentication (no user involved).

**Configuration**:
```yaml
Grant Type: Client Credentials
Token URL: https://api.example.com/oauth/token
Client ID: your-app-client-id
Client Secret: your-app-secret
Scope: api.read api.write
```

**Flow**:
1. Boomi sends client ID + secret to Token URL
2. Authorization server returns access token
3. Access token used for API requests

**Token Refresh**: Boomi automatically refreshes tokens using refresh token (if provided).

---

### AWS Signature (AWS Signature Version 4)

**Use Case**: AWS services (S3, Lambda, API Gateway, etc.).

**Configuration**:
```yaml
Authentication Type: AWS Signature
Access Key ID: AKIAIOSFODNN7EXAMPLE
Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Region: us-east-1
Service: execute-api
```

**How It Works**:
- Boomi calculates signature based on request details (method, URL, headers, body)
- Signature sent as `Authorization: AWS4-HMAC-SHA256 ...` header

---

### Client Certificate (Mutual TLS)

**Use Case**: Certificate-based authentication (highly secure).

**Configuration**:
```yaml
Authentication Type: Client Certificate
Certificate: [Upload .p12 or .pfx file]
Certificate Password: [password for certificate file]
```

**How It Works**:
- Boomi presents client certificate during TLS handshake
- Server validates certificate against trusted CA
- Connection established if certificate is valid

---

## Operation Configuration

### Operation Types

| Type | HTTP Method | Use Case |
|------|-------------|----------|
| **GET** | GET | Retrieve data from server |
| **POST** | POST | Send data to server (create/update) |
| **QUERY** | POST | Query-based retrieval (structured query) |

**Custom HTTP Methods**: Use **POST** operation with custom `X-HTTP-Method-Override` header for PUT, PATCH, DELETE.

---

### GET Operation

**Configuration**:
```yaml
Operation Name: Get Component
Operation Type: GET
Resource Path: /{1}/Component/{2}
Request Profile: [None - GET typically has no body]
Response Profile: ComponentXML
```

**Dynamic URL Example**:
```
Base URL: https://api.boomi.com/api/rest/v1
Resource Path: /{1}/Component/{2}

Full URL: https://api.boomi.com/api/rest/v1/account-123/Component/comp-456
  {1} = account-123 (from document property #1)
  {2} = comp-456 (from document property #2)
```

---

### POST Operation

**Configuration**:
```yaml
Operation Name: Create Component
Operation Type: POST
Resource Path: /{1}/Component
Request Profile: ComponentCreateXML
Response Profile: ComponentResponseXML
```

**Request Body**: Defined by Request Profile (JSON, XML, Flat File, etc.).

**Example**:
```
POST https://api.boomi.com/api/rest/v1/account-123/Component
Content-Type: application/xml

<Component>
  <name>Process - Order Fulfillment</name>
  <type>process</type>
  ...
</Component>
```

---

### QUERY Operation

**Configuration**:
```yaml
Operation Name: Query Components
Operation Type: QUERY
Resource Path: /{1}/Component/query
Request Profile: QueryFilter
Response Profile: QueryResult
```

**Use Case**: Structured queries with pagination, filters, sorting.

**Example** (Platform API QueryFilter):
```xml
<QueryFilter>
  <expression operator="and">
    <simpleExpression property="name" operator="CONTAINS" value="Order"/>
    <simpleExpression property="type" operator="EQUALS" value="process"/>
  </expression>
</QueryFilter>
```

---

## Dynamic URL Configuration

### URL Variable Syntax

**Document Properties**:
- `{1}`, `{2}`, `{3}`, ... — Replaced with document property values in order
- Property Names: `document.dynamic.userdefined.param1`, `document.dynamic.userdefined.param2`, etc.

**Process Properties**:
- `{process.property.name}` — Replaced with process property value

**Example**:
```
Resource Path: /{1}/Component/{2}/ComponentReference
Document Properties:
  - document.dynamic.userdefined.param1 = account-123
  - document.dynamic.userdefined.param2 = comp-456

Final URL: https://api.boomi.com/api/rest/v1/account-123/Component/comp-456/ComponentReference
```

---

## Custom Headers

### Setting Headers via Set Properties

**Pattern**: `document.dynamic.userdefined.http.header.{HeaderName}`

**Example**:
```
Set Properties Step:
  - Name: document.dynamic.userdefined.http.header.Authorization
    Value: Bearer abc123
  - Name: document.dynamic.userdefined.http.header.Content-Type
    Value: application/json
  - Name: document.dynamic.userdefined.http.header.X-Custom-Header
    Value: custom-value

↓

HTTP Client Connector (headers auto-applied)
```

**Common Headers**:
- `Authorization`: Authentication token
- `Content-Type`: Request body MIME type
- `Accept`: Response body MIME type
- `X-Boomi-OverrideAccount`: Boomi Platform API sub-account access
- `X-HTTP-Method-Override`: Override HTTP method (e.g., `PUT`, `PATCH`, `DELETE`)

---

## Request/Response Profiles

### Profile Assignment

**Request Profile**: Defines structure of outgoing request body (JSON, XML, Flat File).

**Response Profile**: Defines expected structure of incoming response body.

**Example**:
```yaml
POST Operation:
  Request Profile: CreateOrderRequest (JSON)
  Response Profile: CreateOrderResponse (JSON)
```

**Profile Types**:
- **JSON**: REST APIs (most common)
- **XML**: SOAP APIs, Boomi Platform API
- **Flat File**: CSV, TSV, fixed-width
- **Database**: Database query results
- **Custom**: Binary, EDI, etc.

---

### JSON Profile Example

**Request Profile** (`CreateOrderRequest`):
```json
{
  "customerId": "string",
  "orderDate": "2026-02-16T10:30:00Z",
  "items": [
    {
      "productId": "string",
      "quantity": 0,
      "price": 0.0
    }
  ]
}
```

**Response Profile** (`CreateOrderResponse`):
```json
{
  "orderId": "string",
  "status": "string",
  "total": 0.0
}
```

**Auto-Generation**: Paste sample JSON → Boomi generates profile elements.

**See**: `json-profiles.md` for detailed profile configuration.

---

## Project-Specific Patterns

### Boomi Platform API Integration

**Connection**:
```yaml
URL: https://api.boomi.com/api/rest/v1
Authentication: Basic
User Name: yourcompany.prodaccount-ABCD
Password: your-api-token
```

**Common Operations**:

| Operation | Method | Resource Path | Use Case |
|-----------|--------|---------------|----------|
| **Get Component** | GET | `/{1}/Component/{2}` | Fetch component XML |
| **Create Component** | POST | `/{1}/Component` | Create new component |
| **Update Component** | POST | `/{1}/Component/{2}` | Update existing component |
| **Delete Component** | DELETE | `/{1}/Component/{2}` | Delete component |
| **Get Component References** | GET | `/{1}/Component/{2}/ComponentReference` | Get dependencies |
| **Query Packaged Components** | POST | `/{1}/PackagedComponent/query` | List packages |
| **Create Integration Pack** | POST | `/{1}/IntegrationPack` | Create pack |

**Tilde Syntax** (branch operations):
```
Resource Path: /{1}/Component/{2}~{3}
  {1} = account ID
  {2} = component ID
  {3} = branch ID

Example: /account-123/Component/comp-456~branch-789
```

**Override Account Header** (sub-account access):
```
Set Properties:
  - document.dynamic.userdefined.http.header.X-Boomi-OverrideAccount = sub-account-123

↓

HTTP Client GET /{1}/Component/{2}
  (accesses sub-account's components instead of primary account)
```

---

## Error Handling

### HTTP Status Codes

**Success**:
- `200 OK` — Request succeeded (GET, POST, PUT, PATCH)
- `201 Created` — Resource created (POST)
- `204 No Content` — Request succeeded, no response body (DELETE)

**Client Errors**:
- `400 Bad Request` — Invalid request payload
- `401 Unauthorized` — Authentication failed
- `403 Forbidden` — Insufficient permissions
- `404 Not Found` — Resource not found
- `429 Too Many Requests` — Rate limit exceeded

**Server Errors**:
- `500 Internal Server Error` — Server error
- `503 Service Unavailable` — Server overloaded or down

### Reading HTTP Status Code

**Property**: `document.dynamic.connector.httpStatusCode`

**Example**:
```
HTTP Client (call API)
  ↓
Decision (check status code)
  ├─→ True (status = 200): Continue
  └─→ False (status != 200): Error handling
```

### Retry Logic

**Pattern**: Use Decision + Route loop for retries.

```
Set Properties (retryCount = 0)
  ↓
HTTP Client (call API)
  ↓
Decision (status = 200?)
  ├─→ True: Success path
  └─→ False:
        Decision (retryCount < 3?)
          ├─→ True:
          │     Set Properties (retryCount++)
          │     Wait (5 seconds)
          │     Route (call self - retry)
          └─→ False: Permanent failure
```

---

## Best Practices

### Authentication
- Use **OAuth 2.0** for SaaS APIs (most secure)
- Use **Basic** for username/password APIs (Boomi Platform API)
- Use **Client Certificate** for highest security (banking, healthcare)
- Never hardcode credentials — use connection components

### Dynamic URLs
- Use `{1}`, `{2}`, `{3}` for document properties (runtime values)
- Use `{process.property.name}` for static configuration values
- Always validate property values before HTTP call (avoid 400 errors)

### Headers
- Set `Content-Type` explicitly (don't rely on auto-detection)
- Set `Accept` to specify desired response format
- Use `X-HTTP-Method-Override` for PUT/PATCH/DELETE on restricted networks

### Profiles
- Always assign request/response profiles for structured data
- Use **JSON** for REST APIs (most common)
- Use **XML** for SOAP APIs and Boomi Platform API
- Auto-generate profiles from sample data (faster, more accurate)

### Error Handling
- Use **Try/Catch** to capture HTTP errors
- Read `httpStatusCode` property to determine error type
- Implement retry logic for transient errors (500, 503, 429)
- Log errors with `trycatchmessage` property

### Performance
- Batch requests when possible (reduce round trips)
- Use connection pooling (automatic in Boomi)
- Set timeouts appropriately (default: 60 seconds)
- Monitor rate limits (429 status code)

---

## Related References

- `json-profiles.md` — JSON profile configuration and best practices
- `flow-service-server.md` — Flow Service integration patterns
- `error-handling.md` — Try/Catch and error patterns
- `process-properties.md` — Dynamic property patterns for headers and URLs

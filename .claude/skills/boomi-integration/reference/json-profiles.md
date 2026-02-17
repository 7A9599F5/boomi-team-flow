# JSON Profiles Reference

Complete guide to creating and using JSON profiles for Flow Services, HTTP APIs, and DataHub operations.

---

## Overview

**Profiles** define the structure of data flowing through processes. JSON profiles are used for:
- **Flow Service** message actions (request/response)
- **HTTP Client** requests/responses (REST APIs)
- **DataHub** queries (when using JSON mode)
- **Map** transformations

---

## Profile Structure

### Root Entry

**Requirement**: Must be an **Object** (not an array or primitive).

**Why**: Boomi profiles require a root container element.

**Example**:
```json
{
  "field1": "value",
  "field2": 123,
  "nestedObject": {
    "field3": "value"
  }
}
```

**Invalid** (root is array):
```json
[
  { "field1": "value" },
  { "field1": "value" }
]
```

**Workaround**: Wrap array in object:
```json
{
  "items": [
    { "field1": "value" },
    { "field1": "value" }
  ]
}
```

---

## Element Types

### Character (String)

**Use Case**: Text fields, IDs, names, descriptions.

**JSON Example**:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "description": "A sample record"
}
```

**Profile Configuration**:
```yaml
Element:
  Name: name
  Type: Character
  Max Length: 255
  Required: true
```

---

### Number

**Use Case**: Numeric fields (integers, decimals).

**JSON Example**:
```json
{
  "age": 30,
  "price": 99.99,
  "quantity": 5
}
```

**Profile Configuration**:
```yaml
Element:
  Name: price
  Type: Number
  Decimals: 2
  Required: true
```

**Note**: Boomi Number type supports both integers and decimals.

---

### Boolean

**Use Case**: True/false flags.

**JSON Example**:
```json
{
  "isActive": true,
  "isPremium": false
}
```

**Profile Configuration**:
```yaml
Element:
  Name: isActive
  Type: Boolean
  Required: true
```

**Values**: `true`, `false` (case-sensitive).

---

### DateTime

**Use Case**: Timestamps, dates.

**JSON Example**:
```json
{
  "createdAt": "2026-02-16T10:30:00Z",
  "lastModified": "2026-02-16T15:45:30.123Z"
}
```

**Profile Configuration**:
```yaml
Element:
  Name: createdAt
  Type: DateTime
  Format: ISO 8601
  Required: true
```

**Supported Formats**:
- **ISO 8601**: `2026-02-16T10:30:00Z` (recommended)
- **RFC 3339**: `2026-02-16T10:30:00-05:00` (with timezone)
- **Unix Timestamp**: `1708084200000` (milliseconds since epoch)

**Note**: Always use ISO 8601 for cross-system compatibility.

---

### Object (Nested Object)

**Use Case**: Nested structures, hierarchical data.

**JSON Example**:
```json
{
  "user": {
    "firstName": "John",
    "lastName": "Doe",
    "address": {
      "street": "123 Main St",
      "city": "NYC",
      "zipCode": "10001"
    }
  }
}
```

**Profile Configuration**:
```yaml
Element:
  Name: user
  Type: Object
  Children:
    - firstName (Character)
    - lastName (Character)
    - address (Object)
      Children:
        - street (Character)
        - city (Character)
        - zipCode (Character)
```

---

### Array

**Use Case**: Lists of items (orders, tags, attachments).

**JSON Example**:
```json
{
  "tags": ["urgent", "finance", "approved"],
  "items": [
    { "productId": "P123", "quantity": 2 },
    { "productId": "P456", "quantity": 1 }
  ]
}
```

**Profile Configuration**:
```yaml
Element:
  Name: items
  Type: Array
  Min Occurrences: 0
  Max Occurrences: -1 (unlimited)
  Child Element:
    Type: Object
    Children:
      - productId (Character)
      - quantity (Number)
```

**Array of Primitives**:
```yaml
Element:
  Name: tags
  Type: Array
  Child Element:
    Type: Character
```

---

## Creating Profiles

### Method 1: From JSON Sample (Recommended)

**Steps**:
1. Navigate to **Build** → **Create New** → **Profile**
2. Select **JSON**
3. Paste sample JSON into text area
4. Click **Import**
5. Boomi auto-generates profile elements

**Example**:
```json
{
  "orderId": "ORD-12345",
  "customerId": "CUST-789",
  "orderDate": "2026-02-16T10:30:00Z",
  "total": 199.99,
  "items": [
    {
      "productId": "P123",
      "quantity": 2,
      "price": 49.99
    }
  ]
}
```

**Generated Profile**:
- Root: `Order` (Object)
  - `orderId` (Character)
  - `customerId` (Character)
  - `orderDate` (DateTime)
  - `total` (Number)
  - `items` (Array of Object)
    - `productId` (Character)
    - `quantity` (Number)
    - `price` (Number)

**Advantages**:
- Fast (seconds vs minutes)
- Accurate (auto-detects types)
- Less error-prone

---

### Method 2: Manual Creation

**Steps**:
1. Navigate to **Build** → **Create New** → **Profile**
2. Select **JSON**
3. Add root Object element
4. Add child elements manually
5. Configure types, required flags, occurrences

**Use Case**: When you need fine-grained control (custom validation, nested arrays, etc.).

---

## Element Properties

### Required Flag

**Behavior**:
- **Required = true**: Field must be present in JSON (validation error if missing)
- **Required = false**: Field is optional (null or absent is OK)

**Example**:
```yaml
Element:
  Name: email
  Required: true
  → JSON must include "email": "value"

Element:
  Name: phoneNumber
  Required: false
  → JSON can omit "phoneNumber" or set to null
```

---

### Min/Max Occurrences

**Use Case**: Control array sizes.

**Configuration**:
```yaml
Element:
  Name: items
  Type: Array
  Min Occurrences: 1 (at least 1 item required)
  Max Occurrences: 100 (no more than 100 items)
```

**Special Values**:
- **Min Occurrences = 0**: Array can be empty or absent
- **Max Occurrences = -1**: Unlimited (no maximum)

---

### Max Length (Character fields)

**Use Case**: Limit string length.

**Configuration**:
```yaml
Element:
  Name: description
  Type: Character
  Max Length: 500
  → Validation error if string > 500 characters
```

---

## Flow Service Integration

### Request/Response Profiles

**Pattern**: Create paired profiles for message actions.

**Example** (executePromotion):

**Request Profile** (`ExecutePromotionRequest`):
```json
{
  "devAccountId": "string",
  "prodAccountId": "string",
  "components": [
    {
      "devComponentId": "string",
      "name": "string",
      "type": "string",
      "folderFullPath": "string"
    }
  ],
  "initiatedBy": "string"
}
```

**Response Profile** (`ExecutePromotionResponse`):
```json
{
  "success": true,
  "errorCode": "",
  "errorMessage": "",
  "promotionId": "string",
  "branchId": "string",
  "branchName": "string",
  "componentsCreated": 0,
  "componentsUpdated": 0,
  "results": [
    {
      "devComponentId": "string",
      "name": "string",
      "action": "string",
      "prodComponentId": "string",
      "status": "string"
    }
  ]
}
```

**Flow Service Operation**:
```yaml
Message Action:
  Name: executePromotion
  Request Profile: ExecutePromotionRequest
  Response Profile: ExecutePromotionResponse
```

---

### Flow Type Auto-Generation

**Behavior**:
- Flow automatically generates **Flow Types** from profiles
- Type name: `{ActionName} REQUEST - {ProfileEntryName}` or `{ActionName} RESPONSE - {ProfileEntryName}`

**Example**:
```
Profile: ExecutePromotionRequest
Flow Type: executePromotion REQUEST - ExecutePromotionRequest

Profile: ExecutePromotionResponse
Flow Type: executePromotion RESPONSE - ExecutePromotionResponse
```

**Usage in Flow**:
- Message step references these auto-generated types
- Map Flow values to request type fields
- Map response type fields to Flow values

**See**: `flow-service-server.md` for Flow integration patterns.

---

## HTTP Client Integration

### Request Profile

**Use Case**: Define structure of HTTP request body (POST, PUT, PATCH).

**Example** (create order):
```json
{
  "customerId": "CUST-789",
  "orderDate": "2026-02-16T10:30:00Z",
  "items": [
    {
      "productId": "P123",
      "quantity": 2,
      "price": 49.99
    }
  ]
}
```

**HTTP Client Operation**:
```yaml
Operation:
  Type: POST
  Resource Path: /orders
  Request Profile: CreateOrderRequest
  Response Profile: CreateOrderResponse
```

---

### Response Profile

**Use Case**: Define expected structure of HTTP response body.

**Example** (create order response):
```json
{
  "orderId": "ORD-12345",
  "status": "CREATED",
  "total": 199.99
}
```

**Mapping**: Use Map shape to transform response to downstream format.

---

## DataHub Integration

### Query Response Profile

**Behavior**: Auto-generated from DataHub model schema.

**Example** (ComponentMapping query response):
```xml
<GoldenRecords>
  <GoldenRecord>
    <id>gr-12345</id>
    <devComponentId>abc-123</devComponentId>
    <prodComponentId>xyz-789</prodComponentId>
    <componentName>Process - Order Fulfillment</componentName>
    <createdDate>2026-01-15T08:00:00Z</createdDate>
  </GoldenRecord>
</GoldenRecords>
```

**Note**: DataHub uses XML profiles (not JSON) for golden records.

---

## Best Practices

### Profile Design

**Use descriptive names**:
- Good: `CreateOrderRequest`, `CustomerSearchResponse`
- Bad: `Request1`, `Output`

**Follow consistent naming**:
- Request profiles: `{Action}Request`
- Response profiles: `{Action}Response`

**Use camelCase for fields**:
- Good: `firstName`, `orderDate`, `totalAmount`
- Bad: `first_name`, `OrderDate`, `total-amount`

---

### Required Fields

**Rule**: Mark fields as required only if they are truly mandatory.

**Example**:
```yaml
Required:
  - orderId (always present)
  - customerId (always present)

Optional:
  - notes (may be absent)
  - shippingAddress (may be null)
```

**Warning**: Over-requiring fields causes validation errors (process failures).

---

### Arrays

**Use unbounded arrays** (`Max Occurrences = -1`) unless you have a hard limit.

**Example**:
```yaml
Element:
  Name: items
  Max Occurrences: -1 (unlimited)
  → Supports 0, 1, 10, 1000 items
```

**Bounded arrays** (use sparingly):
```yaml
Element:
  Name: phoneNumbers
  Max Occurrences: 3 (at most 3 phone numbers)
```

---

### Nested Objects

**Limit nesting depth**: Keep to 2-3 levels (readability, performance).

**Good**:
```json
{
  "order": {
    "customer": {
      "name": "John"
    }
  }
}
```

**Avoid** (too deep):
```json
{
  "level1": {
    "level2": {
      "level3": {
        "level4": {
          "level5": "value"
        }
      }
    }
  }
}
```

---

### DateTime Fields

**Always use ISO 8601**: `2026-02-16T10:30:00Z`

**Avoid**:
- Unix timestamps: `1708084200000` (ambiguous — seconds or milliseconds?)
- Custom formats: `02/16/2026 10:30:00` (locale-dependent)

---

### Error Response Pattern

**Standard structure** (from project):
```json
{
  "success": true | false,
  "errorCode": "ERROR_CODE_ENUM",
  "errorMessage": "Human-readable description"
}
```

**Benefits**:
- Consistent error handling across all message actions
- Flow can check `success` field to determine next steps
- `errorCode` enables programmatic error handling

---

## Project-Specific Examples

### Flow Service Request/Response Pairs

**All 11 message actions follow this pattern**:

| Action | Request Fields | Response Fields |
|--------|----------------|-----------------|
| **getDevAccounts** | (empty) | `success`, `devAccounts[]`, `errorCode`, `errorMessage` |
| **listDevPackages** | `devAccountId` | `success`, `packages[]`, `errorCode`, `errorMessage` |
| **resolveDependencies** | `devAccountId`, `componentId` | `success`, `dependencies[]`, `errorCode`, `errorMessage` |
| **executePromotion** | `devAccountId`, `components[]`, `initiatedBy` | `success`, `promotionId`, `results[]`, `errorCode`, `errorMessage` |
| **packageAndDeploy** | `branchId`, `promotionId`, `components[]` | `success`, `integrationPackId`, `errorCode`, `errorMessage` |
| **queryStatus** | `reviewStage`, `dateRange` | `success`, `promotions[]`, `errorCode`, `errorMessage` |
| **manageMappings** | `action`, `mapping` | `success`, `errorCode`, `errorMessage` |

**Naming Convention**:
- Profile: `PROMO - Profile - {ActionName}Request` / `{ActionName}Response`
- File: `integration/profiles/{actionName}-request.json` / `{actionName}-response.json`

---

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **Required field missing** | JSON missing required field | Add field or mark as optional |
| **Type mismatch** | Field type doesn't match profile | Check JSON value type (string, number, etc.) |
| **Invalid array** | Array structure incorrect | Ensure array element matches profile |
| **Root element error** | Root is not an object | Wrap array/primitive in object |

### Validation Testing

**Pattern**: Use **Test** button in profile editor.

**Steps**:
1. Open profile
2. Click **Test**
3. Paste sample JSON
4. Click **Validate**
5. Review validation errors/warnings

**Use Case**: Verify profile matches expected JSON structure before deployment.

---

## Related References

- `flow-service-server.md` — Flow Service integration and message actions
- `http-client.md` — HTTP Client request/response configuration
- `datahub-connector.md` — DataHub query/upsert patterns

# DataHub Models and Fields

## Model Overview

**Models** define the structure, validation rules, and matching logic for master data domains in DataHub.

**Model = Schema Definition → Deployed = Universe (Domain)**

### Model Components

| Component | Required | Purpose |
|-----------|----------|---------|
| **Name & Root Element** | Yes | Model name becomes domain name when deployed |
| **Fields** | Yes | Data categories describing golden record contents |
| **Match Rules** | Yes | Define uniqueness and UPSERT logic |
| **Sources** | Recommended | Contributor/acceptor settings embedded in model |
| **Data Quality Steps** | Recommended | Business rules, validation, enrichment |
| **Record Title Format** | Optional | Customize golden record display (e.g., "LastName, FirstName") |
| **Tags** | Optional | Classify golden records for governance |

### Model Lifecycle

```
1. Draft → Edit fields, match rules, sources
   ↓
2. Published → Versioned snapshot, eligible for deployment
   ↓
3. Deployed → Creates universe in repository
```

**Important**: Once deployed, model changes require new version and redeployment.

## Field Types

| Field Type | Description | Use Cases | Notes |
|------------|-------------|-----------|-------|
| **String** | Text values | Names, IDs, emails, descriptions | Default max length: 255 chars |
| **Number** | Numeric values | Versions, counts, integers | Stored as integer |
| **Date** | ISO 8601 timestamps | Created dates, modified dates | Format: `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'` |
| **Boolean** | True/false | Flags, status indicators | Stored as boolean |
| **Long Text** | Extended text | JSON payloads, detailed descriptions | Max 5,000 characters |
| **Collection** | Repeating groups | Phone numbers, addresses | Contains child elements |
| **Reference** | Intra-domain reference | Link to other golden records | Within same domain only |

## Field Properties

### Core Properties

```json
{
  "name": "fieldName",
  "type": "String",
  "description": "Human-readable documentation",
  "required": true,
  "matchField": true
}
```

| Property | Type | Description |
|----------|------|-------------|
| **name** | String | Field identifier (used in XML/API), camelCase recommended |
| **type** | Enum | Data type (String, Number, Date, Boolean, Long Text) |
| **description** | String | Human-readable documentation |
| **required** | Boolean | `true` = mandatory for golden record creation |
| **matchField** | Boolean | `true` = used in match rule compound keys |
| **masking** | Object | Configure to hide sensitive data based on user roles |

### Match Fields

Fields marked with `matchField: true` are used in match rules to identify unique records or detect duplicates.

**Example (Compound Match Key)**:
```json
{
  "fields": [
    {
      "name": "devComponentId",
      "type": "String",
      "required": true,
      "matchField": true
    },
    {
      "name": "devAccountId",
      "type": "String",
      "required": true,
      "matchField": true
    }
  ]
}
```

**Match Rule Using These Fields**:
```json
{
  "type": "EXACT",
  "description": "Compound match on dev component ID and dev account ID",
  "fields": ["devComponentId", "devAccountId"]
}
```

**Behavior**: Incoming record must match BOTH `devComponentId` AND `devAccountId` to match existing golden record.

### Field Constraints

**Required Fields**:
- Must be present in incoming entity for successful golden record creation
- If missing, entity quarantined with validation error

**Field Masking**:
- Hides sensitive data (SSN, credit cards) based on user roles
- Only applies with JWT authentication (not Basic Auth)
- Requires `MDM - Reveal Masked Data` privilege to unmask

**Example (Masked Field)**:
```json
{
  "name": "socialSecurityNumber",
  "type": "String",
  "masking": {
    "maskType": "PARTIAL",
    "visibleChars": 4,
    "maskChar": "*"
  }
}
```

**Masked Response**:
```xml
<socialSecurityNumber>***-**-1234</socialSecurityNumber>
```

## Model Creation Options

### 1. Import from Source

Import field definitions from existing systems:
- Salesforce objects
- CSV files
- Database tables
- REST API schemas

**Benefit**: Automatically generates field structure from source system.

### 2. Boomi Suggest (AI-Powered)

AI suggests fields based on Boomi Community patterns for common domains:
- Account
- Customer
- Employee
- Location
- Product
- Vendor

**Benefit**: Leverage best practices from community implementations.

### 3. Copy Existing Model

Duplicate an existing model and modify:
- Faster than starting from scratch
- Maintains consistent patterns across models

### 4. Manual Creation

Add fields one-by-one in UI.

## Layout Types

Models support different layout patterns for field organization.

### Simple Layout

Flat field structure, all fields at root level.

**Example**:
```xml
<ComponentMapping>
  <devComponentId>comp-123</devComponentId>
  <prodComponentId>comp-789</prodComponentId>
  <componentName>Order Process</componentName>
</ComponentMapping>
```

**Use Case**: Most common, suitable for 90% of models.

### Collection Layout

Repeating groups for multi-valued attributes.

**Example**:
```xml
<Contact>
  <name>John Doe</name>
  <phoneNumbers>
    <phoneNumber type="mobile">555-1234</phoneNumber>
    <phoneNumber type="work">555-5678</phoneNumber>
  </phoneNumbers>
</Contact>
```

**Use Case**: Multiple phone numbers, addresses, or other repeating data.

### Reference Layout

Link to other golden records within same domain.

**Example**:
```xml
<Employee>
  <name>Alice Smith</name>
  <managerId>GR-MANAGER-123</managerId>
</Employee>
```

**Use Case**: Hierarchical relationships (employee → manager, product → category).

**Limitation**: References only work within same domain (cannot reference golden record in different model).

## Model Versioning

### Version Lifecycle

```
Draft v1 → Publish v1 → Deploy v1 to Dev Repository
   ↓
Edit Draft → Publish v2 → Deploy v2 to Test Repository
   ↓
Deploy v2 to Prod Repository (replaces v1)
```

**Key Points**:
- Each publish creates immutable version
- Multiple versions can exist simultaneously
- Only one version deployed per repository at a time
- New deployment replaces previous version in that repository

### Backward Compatibility

**Field Addition**: Safe (existing data unaffected)

**Field Removal**: Risky (data loss if golden records have values)

**Field Rename**: Treated as remove + add (data loss)

**Match Rule Changes**: Can cause duplicate golden records if keys change

**Best Practice**: Test new model versions in dev/test before production deployment.

## Model Examples from This Project

### ComponentMapping Model

**Root Element**: `ComponentMapping`

**Purpose**: Map dev component IDs to production component IDs.

**Key Fields**:
```json
{
  "fields": [
    {"name": "id", "type": "String", "required": false, "matchField": false},
    {"name": "devComponentId", "type": "String", "required": true, "matchField": true},
    {"name": "devAccountId", "type": "String", "required": true, "matchField": true},
    {"name": "prodComponentId", "type": "String", "required": true},
    {"name": "componentName", "type": "String", "required": true},
    {"name": "componentType", "type": "String", "required": true},
    {"name": "prodLatestVersion", "type": "Number", "required": true},
    {"name": "lastPromotedAt", "type": "Date", "required": true},
    {"name": "mappingSource", "type": "String", "required": false}
  ]
}
```

**Match Rule**: Compound key on `(devComponentId, devAccountId)`

### DevAccountAccess Model

**Root Element**: `DevAccountAccess`

**Purpose**: Control SSO group access to dev accounts.

**Key Fields**:
```json
{
  "fields": [
    {"name": "ssoGroupId", "type": "String", "required": true, "matchField": true},
    {"name": "ssoGroupName", "type": "String", "required": true},
    {"name": "devAccountId", "type": "String", "required": true, "matchField": true},
    {"name": "devAccountName", "type": "String", "required": true},
    {"name": "isActive", "type": "String", "required": true}
  ]
}
```

**Match Rule**: Compound key on `(ssoGroupId, devAccountId)`

**Note**: `isActive` is String type ("true"/"false") for flexibility.

### PromotionLog Model

**Root Element**: `PromotionLog`

**Purpose**: Audit trail with 2-layer approval workflow.

**Key Fields**:
```json
{
  "fields": [
    {"name": "promotionId", "type": "String", "required": true, "matchField": true},
    {"name": "devAccountId", "type": "String", "required": true},
    {"name": "status", "type": "String", "required": true},
    {"name": "componentsTotal", "type": "Number", "required": true},
    {"name": "initiatedBy", "type": "String", "required": true},
    {"name": "initiatedAt", "type": "Date", "required": true},
    {"name": "resultDetail", "type": "String", "required": false},
    {"name": "peerReviewStatus", "type": "String", "required": false},
    {"name": "adminReviewStatus", "type": "String", "required": false},
    {"name": "integrationPackId", "type": "String", "required": false}
  ]
}
```

**Match Rule**: Single key on `promotionId`

**Note**: `resultDetail` field stores JSON (max 5,000 chars).

## Best Practices

### Field Naming

- **Use camelCase**: `firstName`, `emailAddress`, `prodComponentId`
- **Avoid underscores**: Use camelCase instead of snake_case
- **Avoid special characters**: Stick to alphanumeric + camelCase
- **Descriptive names**: `devAccountId` not `daid`

### Required Fields

- **Only mark truly mandatory**: Don't overuse required
- **Use data quality rules**: For conditional requirements
- **Consider defaults**: Provide default values where applicable

### Match Fields

- **Compound keys prevent collisions**: `(devComponentId, devAccountId)` ensures uniqueness across dev accounts
- **Choose stable identifiers**: Don't use volatile fields (names, emails change)
- **Test match rules**: Use Match Entities operation before deployment

### Field Types

- **Long Text for JSON**: Store JSON payloads as strings (max 5,000 chars)
- **String for booleans**: More flexible for API compatibility ("true"/"false")
- **Date for timestamps**: Always use ISO 8601 format

### Performance

- **Index match fields**: Automatically indexed for fast lookups
- **Limit field count**: 50-100 fields per model (avoid 200+)
- **Use References sparingly**: Can impact query performance

# DataHub Connector Reference

Complete guide to using the Boomi DataHub Connector for master data management and operational data storage.

---

## Overview

**Boomi DataHub** is a cloud-based master data management (MDM) and operational data store that enables:
- **Golden Record Management**: Store canonical master data across systems
- **Data Quality**: Validation, deduplication, enrichment
- **Multi-Source Consolidation**: Merge data from multiple contributing sources
- **API Access**: REST APIs + Boomi DataHub Connector

**Key Concepts**:
- **Repository**: A DataHub instance (one per account)
- **Model/Universe**: A deployed data model (schema) in the repository
- **Golden Records**: Master records in the DataHub
- **Contributing Sources**: Systems that contribute data to golden records

---

## Connection Configuration

### Basic Settings

```yaml
DataHub Connection:
  Name: DataHub Production
  Repository: [Select from deployed repositories]
  Authentication: Hub Auth Token
  Base URL: [Auto-populated, e.g., https://mdm-us.boomi.com]
```

**Repository Selection**:
- Dropdown shows all DataHub repositories in the account
- Each repository can have multiple deployed models/universes

**Base URL**:
- Auto-populated based on repository location
- US: `https://mdm-us.boomi.com`
- EU: `https://mdm-eu.boomi.com`
- APAC: `https://mdm-apac.boomi.com`

---

## Hub Auth Token

**What is it?**
- Automatically generated token for same-account DataHub access
- No manual configuration required
- Boomi connector handles token lifecycle (generation, refresh, expiration)

**How it works**:
1. Connector requests token from DataHub
2. DataHub validates account credentials
3. Token issued and cached by connector
4. Token automatically refreshed when expired

**Security**:
- Tokens are scoped to repository and account
- Cannot access other accounts' DataHub repositories
- Token expiration enforced (typically 1 hour)

**Cross-Account Access**:
- Not supported via Hub Auth Token
- Use DataHub REST API with Platform API credentials instead

---

## Operations

### Query Golden Records

**Purpose**: Retrieve golden records from a universe (model).

**Configuration**:
```yaml
Operation Name: Query ComponentMapping
Operation Type: Query Golden Records
Universe Name: ComponentMapping
Query Filter: devComponentId eq 'abc-123'
Sort Order: lastPromoted desc
Max Results: 100
```

**Query Filter Syntax** (OData-style):

| Operator | Syntax | Example |
|----------|--------|---------|
| **Equals** | `field eq 'value'` | `devComponentId eq 'abc-123'` |
| **Not Equals** | `field ne 'value'` | `status ne 'DELETED'` |
| **Greater Than** | `field gt value` | `age gt 18` |
| **Less Than** | `field lt value` | `price lt 100.00` |
| **Greater Than or Equal** | `field ge value` | `createdDate ge '2026-01-01'` |
| **Less Than or Equal** | `field le value` | `quantity le 50` |
| **Contains** | `field contains 'substring'` | `name contains 'Order'` |
| **Starts With** | `field startswith 'prefix'` | `sku startswith 'PROD-'` |
| **Ends With** | `field endswith 'suffix'` | `email endswith '@example.com'` |
| **AND** | `expr1 and expr2` | `status eq 'ACTIVE' and age gt 18` |
| **OR** | `expr1 or expr2` | `type eq 'A' or type eq 'B'` |

**Example Queries**:

```odata
// Single field match
devComponentId eq 'abc-123'

// Multiple conditions (AND)
devComponentId eq 'abc-123' and devAccountId eq 'sub-account-456'

// Date range
promotionDate ge '2026-01-01T00:00:00Z' and promotionDate le '2026-01-31T23:59:59Z'

// String contains
componentName contains 'Order' and componentType eq 'process'

// OR condition
reviewStatus eq 'PENDING_PEER_REVIEW' or reviewStatus eq 'PENDING_ADMIN_REVIEW'
```

**Response Profile**:
- Auto-generated from model schema
- Includes golden record IDs, field values, and metadata
- Standard fields: `id` (golden record ID), `createdDate`, `modifiedDate`, `source`

**Response Example**:
```xml
<GoldenRecords>
  <GoldenRecord>
    <id>gr-12345</id>
    <devComponentId>abc-123</devComponentId>
    <prodComponentId>xyz-789</prodComponentId>
    <devAccountId>sub-account-456</devAccountId>
    <componentName>Process - Order Fulfillment</componentName>
    <componentType>process</componentType>
    <source>PROMOTION_ENGINE</source>
    <lastPromoted>2026-02-16T10:30:00Z</lastPromoted>
    <createdDate>2026-01-15T08:00:00Z</createdDate>
    <modifiedDate>2026-02-16T10:30:00Z</modifiedDate>
  </GoldenRecord>
</GoldenRecords>
```

---

### Update Golden Records

**Purpose**: Upsert golden records (create new or update existing).

**Configuration**:
```yaml
Operation Name: Upsert ComponentMapping
Operation Type: Update Golden Records
Universe Name: ComponentMapping
Upsert Mode: true
Match Keys: devComponentId, devAccountId
```

**Upsert Behavior**:
1. DataHub checks if record exists based on **match keys**
2. If match found → **Update** existing golden record
3. If no match → **Create** new golden record

**Match Keys** (defined in model):
- Fields used to identify existing records
- Can be single field or compound key (multiple fields)
- Example: `devComponentId` + `devAccountId` (composite key)

**Request Profile**:
- Auto-generated from model schema
- XML format with field values

**Request Example**:
```xml
<GoldenRecord>
  <devComponentId>abc-123</devComponentId>
  <prodComponentId>xyz-789</prodComponentId>
  <devAccountId>sub-account-456</devAccountId>
  <componentName>Process - Order Fulfillment</componentName>
  <componentType>process</componentType>
  <source>PROMOTION_ENGINE</source>
  <lastPromoted>2026-02-16T10:30:00Z</lastPromoted>
</GoldenRecord>
```

**Response**:
- Returns golden record ID (new or updated)
- Includes success/failure status

---

### Delete Golden Records

**Purpose**: Delete golden records by ID.

**Configuration**:
```yaml
Operation Name: Delete ComponentMapping
Operation Type: Delete Golden Records
Universe Name: ComponentMapping
```

**Request**:
- Golden record ID (from Query response)
- Example: `<id>gr-12345</id>`

**Response**:
- Success/failure status

**Warning**: Deletion is permanent and cannot be undone.

---

## Batch Operations

### Batch Size Recommendations

| Operation | Recommended Batch Size | Max Batch Size |
|-----------|------------------------|----------------|
| **Query** | 100-500 records | 1000 records |
| **Update/Upsert** | 100-500 records | 1000 records |
| **Delete** | 100-500 records | 1000 records |

**Performance**:
- Larger batches reduce round trips (faster overall)
- Too large batches may cause timeouts (>10 seconds)
- Optimal: 200-300 records per batch

### Pagination

**Pattern**: Use `offset` and `limit` for large result sets.

```
Query 1: offset=0, limit=100 → returns records 1-100
Query 2: offset=100, limit=100 → returns records 101-200
Query 3: offset=200, limit=100 → returns records 201-300
```

**Configuration**:
```yaml
Query Filter: status eq 'ACTIVE'
Sort Order: createdDate asc
Max Results: 100
Offset: 0
```

**Loop Pattern**:
```
Set Properties (offset = 0, hasMore = true)
  ↓
Decision (hasMore = true?)
  ↓ True
Query DataHub (offset = {offset}, limit = 100)
  ↓
Data Process (check if resultCount < 100 → hasMore = false)
  ↓
Set Properties (offset += 100)
  ↓
Route (loop back to Decision)
```

---

## Accelerated Query

**What is it?**
- Automatic performance optimization for large universes (100,000+ records)
- Enabled by DataHub when universe size threshold reached
- No configuration required

**How it works**:
- DataHub uses indexed queries instead of full table scans
- Response time: <1 second (vs 5-30 seconds for non-accelerated)

**Requirements**:
- Universe must have 100,000+ records
- Query filter must use indexed fields
- Sort order must use indexed fields

**See**: DataHub model configuration for index definitions.

---

## Project-Specific Patterns

### ComponentMapping Model

**Purpose**: Store dev→prod component ID mappings.

**Match Keys**: `devComponentId` + `devAccountId` (compound key)

**Fields**:
```yaml
Fields:
  - devComponentId: string (match key)
  - prodComponentId: string
  - devAccountId: string (match key)
  - componentName: string
  - componentType: string (profile, connection, operation, map, process)
  - source: string (PROMOTION_ENGINE, ADMIN_SEEDING)
  - lastPromoted: datetime
```

**Usage**:

**Query** (lookup mapping):
```
Query Filter: devComponentId eq '{1}' and devAccountId eq '{2}'
Max Results: 1
```

**Upsert** (store mapping):
```xml
<GoldenRecord>
  <devComponentId>abc-123</devComponentId>
  <prodComponentId>xyz-789</prodComponentId>
  <devAccountId>sub-account-456</devAccountId>
  <componentName>Process - Order Fulfillment</componentName>
  <componentType>process</componentType>
  <source>PROMOTION_ENGINE</source>
  <lastPromoted>2026-02-16T10:30:00Z</lastPromoted>
</GoldenRecord>
```

---

### DevAccountAccess Model

**Purpose**: Store SSO group → dev account access control.

**Match Keys**: `ssoGroupId` + `devAccountId` (compound key)

**Fields**:
```yaml
Fields:
  - ssoGroupId: string (match key)
  - devAccountId: string (match key)
  - devAccountName: string
  - source: string (ADMIN_CONFIG)
```

**Usage**:

**Query** (get accessible accounts for SSO group):
```
Query Filter: ssoGroupId eq '{1}'
Max Results: 100
```

---

### PromotionLog Model

**Purpose**: Audit trail for promotion runs.

**Match Keys**: `promotionId` (single key)

**Fields**:
```yaml
Fields:
  - promotionId: string (match key)
  - devAccountId: string
  - prodAccountId: string
  - branchId: string
  - branchName: string
  - processName: string
  - initiatedBy: string
  - promotionDate: datetime
  - peerReviewStatus: string (PENDING_PEER_REVIEW, APPROVED, REJECTED)
  - adminReviewStatus: string (PENDING_ADMIN_REVIEW, APPROVED, REJECTED, N/A)
  - componentsPromoted: number
  - source: string (PROMOTION_ENGINE)
```

**Usage**:

**Query** (filter by review stage):
```
// Peer review queue
Query Filter: peerReviewStatus eq 'PENDING_PEER_REVIEW' and initiatedBy ne '{currentUser}'

// Admin approval queue
Query Filter: adminReviewStatus eq 'PENDING_ADMIN_REVIEW' and peerReviewStatus eq 'APPROVED'
```

**Upsert** (log promotion):
```xml
<GoldenRecord>
  <promotionId>promo-123</promotionId>
  <devAccountId>sub-account-456</devAccountId>
  <prodAccountId>primary-account-789</prodAccountId>
  <branchId>branch-abc</branchId>
  <branchName>promo-dev-teamA-20260216</branchName>
  <processName>Order Fulfillment</processName>
  <initiatedBy>user@example.com</initiatedBy>
  <promotionDate>2026-02-16T10:30:00Z</promotionDate>
  <peerReviewStatus>PENDING_PEER_REVIEW</peerReviewStatus>
  <adminReviewStatus>N/A</adminReviewStatus>
  <componentsPromoted>15</componentsPromoted>
  <source>PROMOTION_ENGINE</source>
</GoldenRecord>
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **Universe not found** | Typo in universe name or model not deployed | Verify universe name matches deployed model |
| **Invalid query filter** | Syntax error in OData filter | Check filter syntax (eq, and, or, etc.) |
| **Match key violation** | Missing required match key field | Include all match key fields in upsert request |
| **Record not found** | Query returned no results | Check filter values, verify data exists |
| **Timeout** | Query/update too large or slow | Reduce batch size, add indexes to model |

### Error Property

**Property**: `document.dynamic.connector.errorMessage`

**Example**:
```
DataHub Connector (query)
  ↓
Decision (errorMessage is empty?)
  ├─→ True: Success
  └─→ False: Error handling
```

---

## Best Practices

### Queries
- **Pre-load mapping cache**: Query all mappings once, cache in DPP (avoid N+1 queries)
- **Use indexed fields**: Filter and sort on indexed fields for accelerated queries
- **Limit results**: Set `Max Results` appropriately (don't return 10,000 records if you need 10)
- **Compound keys**: Use compound match keys for unique lookups (e.g., `devComponentId` + `devAccountId`)

### Upserts
- **Match keys required**: Always include all match key fields in upsert request
- **Batch upserts**: Batch 100-300 records per request (faster than individual upserts)
- **Source tracking**: Always set `source` field to identify data origin

### Performance
- **Cache lookups**: Use Dynamic Process Properties (DPPs) to cache frequently accessed data
- **Batch operations**: Use batch queries/upserts instead of loops (reduce round trips)
- **Pagination**: Use offset/limit for large result sets (avoid timeouts)

### Error Handling
- **Try/Catch**: Wrap DataHub operations in Try/Catch to prevent failures
- **Read error message**: Check `errorMessage` property for troubleshooting
- **Retry transient errors**: Implement retry logic for timeouts and network errors

---

## Related References

- `json-profiles.md` — Profile configuration for DataHub requests/responses
- `process-properties.md` — Dynamic Process Properties for caching
- `error-handling.md` — Try/Catch patterns for DataHub errors

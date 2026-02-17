# DataHub Connector Operations

## Overview

The **Boomi DataHub Connector** provides a low-code interface for integrating with DataHub repositories from Integration processes.

**Key Features**:
- **HTTPS Connection**: Web service calls via XML request/response
- **Simplified Configuration**: No manual header setup or complex error handling
- **Hub Auth Token**: Basic authentication using repository credentials
- **Unlimited Deployment**: Does not count against license limits
- **Read-Only and Write Operations**: Query golden records or update/upsert batches

## Connector vs. HTTP Client

| Aspect | DataHub Connector | HTTP Client Connector |
|--------|-------------------|----------------------|
| **Configuration** | Simple, guided UI | Manual endpoint/header setup |
| **Authentication** | Built-in Hub Auth Token | Manual Basic Auth header |
| **Operations** | Predefined actions (Query, Update/Upsert, Match) | Full REST API access |
| **Error Handling** | Automatic fault parsing | Manual error response parsing |
| **Use Case** | Common DataHub operations | Advanced/custom API calls |
| **Learning Curve** | Low | Medium |

**Recommendation**: Use DataHub Connector for standard operations. Use HTTP Client for advanced scenarios (Platform API, custom endpoints).

## DataHub Connector Operations

### 1. Update/Upsert Golden Records

**Operation Type**: Outbound (send data TO DataHub)

**Purpose**: Send batch of source entities to create/update golden records.

**Process Flow**:
```
Integration Process
    ↓ (batch of entities)
DataHub Connector
    ↓ (POST /mdm/universes/{universeID}/records)
DataHub Repository
    ↓ (apply match rules)
Golden Records Created/Updated
    ↓ (response)
Integration Process (handle success/failure)
```

**Request Format**:
```xml
<batch src="SOURCE_ID">
  <ModelRootElement>
    <id>source-entity-id-1</id>
    <field1>value1</field1>
    <field2>value2</field2>
  </ModelRootElement>
  <ModelRootElement>
    <id>source-entity-id-2</id>
    <field1>valueA</field1>
    <field2>valueB</field2>
  </ModelRootElement>
</batch>
```

**Key Attributes**:
- `src`: Source ID (identifies contributing source system)
- `<id>`: Source entity identifier (required for linking)

**Connector Configuration**:
1. Action: **Update/Upsert Golden Records**
2. Model: Select deployed model (universe) from repository
3. Source: Choose source ID (or configure in connection)

**Endpoints**:
- **Update Mode**: `POST /mdm/universes/{universeID}/records`
- **Staging Mode**: `POST /mdm/universes/{universeID}/staging/{stagingAreaID}`

**Response**:
- Success: HTTP 200, confirmation XML
- Failure: HTTP 4xx/5xx, error details

**Privilege Required**: `MDM - Batch Management`

**Example Use Cases**:
- Process C: Update ComponentMapping after successful promotion
- Process D: Create PromotionLog record after deployment
- Incremental sync from source systems to DataHub

### 2. Query Golden Records

**Operation Type**: Inbound (retrieve data FROM DataHub)

**Purpose**: Retrieve active golden records with optional filtering and sorting.

**Process Flow**:
```
Integration Process
    ↓ (query request XML)
DataHub Connector
    ↓ (POST /mdm/universes/{universeID}/records/query)
DataHub Repository
    ↓ (filter, sort, paginate)
Golden Records Returned
    ↓ (response XML)
Integration Process (process results)
```

**Request Format**:
```xml
<RecordQueryRequest limit="200">
  <view>
    <fieldId>field1</fieldId>
    <fieldId>field2</fieldId>
  </view>
  <filter op="AND">
    <fieldValue>
      <fieldId>field1</fieldId>
      <operator>EQUALS</operator>
      <value>search-value</value>
    </fieldValue>
  </filter>
  <sort>
    <fieldId>field1</fieldId>
    <order>ASC</order>
  </sort>
</RecordQueryRequest>
```

**Query Features**:

| Feature | Description |
|---------|-------------|
| **Field Selection** | `<view>` — Choose which fields to return |
| **Filtering** | `<filter>` — Filter by field values, dates, source links |
| **Sorting** | `<sort>` — Order results by field values |
| **Pagination** | `limit` + `offset` — Handle large result sets |
| **Accelerated Query** | Optimized performance for 100,000+ records |

**Filter Operators**:

| Operator | Description | Example |
|----------|-------------|---------|
| `EQUALS` | Exact match | `<operator>EQUALS</operator><value>comp-123</value>` |
| `NOT_EQUALS` | Not equal | `<operator>NOT_EQUALS</operator><value>inactive</value>` |
| `CONTAINS` | Substring match | `<operator>CONTAINS</operator><value>Order</value>` |
| `NOT_CONTAINS` | Does not contain | `<operator>NOT_CONTAINS</operator><value>Test</value>` |
| `GREATER_THAN` | Numeric/date comparison | `<operator>GREATER_THAN</operator><value>100</value>` |
| `LESS_THAN` | Numeric/date comparison | `<operator>LESS_THAN</operator><value>2024-01-01T00:00:00Z</value>` |
| `BETWEEN` | Range (dates) | `<operator>BETWEEN</operator><value>2024-01-01...2024-12-31</value>` |
| `Linked` | Has source link | `<sourceLink><operator>Linked</operator><source>SOURCE_ID</source></sourceLink>` |
| `Not Linked` | No source link | `<sourceLink><operator>Not Linked</operator><source>SOURCE_ID</source></sourceLink>` |

**Compound Filters**:
```xml
<filter op="AND">
  <fieldValue>
    <fieldId>devComponentId</fieldId>
    <operator>EQUALS</operator>
    <value>comp-123</value>
  </fieldValue>
  <fieldValue>
    <fieldId>devAccountId</fieldId>
    <operator>EQUALS</operator>
    <value>DEV_A</value>
  </fieldValue>
</filter>
```

**Response Format**:
```xml
<Record recordId="c863..." createdDate="2024-04-26T19:48:20Z" updatedDate="2024-05-10T20:26:26Z">
  <Fields>
    <ComponentMapping>
      <devComponentId>comp-123</devComponentId>
      <prodComponentId>comp-789</prodComponentId>
      <componentName>Order Process</componentName>
    </ComponentMapping>
  </Fields>
  <links>
    <link source="PROMOTION_ENGINE" entityId="entity-001" establishedDate="2024-04-11T14:45:33Z"/>
  </links>
</Record>
```

**Connector Configuration**:
1. Action: **Query Golden Records**
2. Model: Select deployed model (universe) from repository
3. Query Options: Configure filters, fields, sorting in operation settings

**Privilege Required**: `MDM - Stewardship` or `MDM - View Data`

**Example Use Cases**:
- Process B: Query ComponentMapping for existing mappings
- Process E: Query PromotionLog for status retrieval
- Process E2: Query PENDING_PEER_REVIEW promotions

### 3. Match Entities

**Operation Type**: Outbound (test data WITHOUT committing)

**Purpose**: Test match rules without staging or committing data to golden records.

**Process Flow**:
```
Integration Process
    ↓ (test entity batch)
DataHub Connector
    ↓ (POST /mdm/universes/{universeID}/match)
DataHub Repository
    ↓ (apply match rules, NO commit)
Match Results Returned
    ↓ (matching golden records + scores)
Integration Process (review results)
```

**Request Format**:
```xml
<batch src="SOURCE_ID">
  <contact>
    <id>test-001</id>
    <name>bobby</name>
    <city>berwyn</city>
  </contact>
</batch>
```

**Response Format**:
```xml
<MatchEntitiesResponse>
  <MatchResult matchRule="Incoming name is similar to (Jaro-Winkler) Existing name" status="SUCCESS">
    <entity>
      <contact>
        <id>test-001</id>
        <name>bobby</name>
      </contact>
    </entity>
    <match>
      <contact recordId="GR-123">
        <name>bob</name>
      </contact>
      <fuzzyMatchDetails>
        <field>name</field>
        <first>BOBBY</first>
        <second>BOB</second>
        <method>jarowinkler</method>
        <score>0.92</score>
      </fuzzyMatchDetails>
    </match>
    <duplicate>
      <!-- Golden records already linked to source -->
    </duplicate>
  </MatchResult>
</MatchEntitiesResponse>
```

**Response Sections**:
- `<match>`: Matching golden records NOT yet linked to source
- `<duplicate>`: Matching golden records already linked to source
- `<fuzzyMatchDetails>`: Similarity scores for fuzzy matches

**Use Cases**:
- Validate match rule configuration before production
- Preview duplicate detection for incoming batch
- Troubleshoot quarantine issues
- Test fuzzy matching thresholds

### 4. Query Quarantine Entries

**Operation Type**: Inbound (retrieve quarantined entities)

**Purpose**: Retrieve entities that failed validation or match rules.

**Endpoint**: `POST /mdm/universes/{universeID}/quarantine/query`

**Request Format**:
```xml
<QuarantineQueryRequest limit="100">
  <view>
    <fieldId>name</fieldId>
    <fieldId>email</fieldId>
  </view>
  <filter op="AND">
    <cause>MATCH_FAILURE</cause>
    <resolution>UNRESOLVED</resolution>
  </filter>
</QuarantineQueryRequest>
```

**Supported Filters**:
- **Created Date**: Filter by quarantine timestamp
- **Cause**: MATCH_FAILURE, DATA_QUALITY_FAILURE, VALIDATION_FAILURE
- **Resolution**: UNRESOLVED, RESOLVED, IGNORED

**Response Includes**:
- Quarantined source entity data
- Reason for quarantine
- Matching golden records (if match failure)
- Resolution status

**Use Case**: Data steward workflows for reviewing and resolving quarantine entries.

### 5. Load/Update Quarantined Records

**Operation Type**: Both (manage quarantine resolution)

**Purpose**: Programmatically resolve quarantine entries (link to golden record, create new, etc.).

**Use Case**: Automated or semi-automated quarantine resolution workflows.

## Connector Configuration

### Step 1: Create Connection Component

**Connection Settings**:

| Field | Value | Notes |
|-------|-------|-------|
| **Boomi Hub Cloud Name** | `c01-usa-east.hub.boomi.com` | Select from dropdown |
| **Custom Cloud URL** | `https://<cloud-host>/mdm` | Alternative to dropdown |
| **Username** | Repository username | From Repository → Configure tab |
| **Authentication Token** | Hub Auth Token | From Repository → Configure tab |

**Find Hub Cloud Host**:
1. Integration → Manage → Runtime Management
2. Find repository name in runtime cloud list
3. Copy hostname (e.g., `c01-usa-east.hub.boomi.com`)

**Authentication**:
- Connector uses Basic Auth only (no JWT support)
- Credentials = `username:hubAuthToken`
- Provides administrator-level privileges

### Step 2: Create Operation Component

**Operation Settings**:

1. Click **Import Operation**
2. Select online **Basic Runtime** (must be deployed)
3. Choose **Deployed Model** (universe) from repository
4. Configure action-specific settings:
   - **Update/Upsert**: Select source ID
   - **Query**: Configure filters, fields, sorting
   - **Match**: Test settings

**Import Notes**:
- Operation imports model schema automatically
- Creates request/response profiles
- Universe must be deployed before import

### Step 3: Configure Request/Response Profiles

**Profile Types**:
- **Request Profile**: Defines outgoing XML structure (batch, query)
- **Response Profile**: Defines incoming XML structure (records, errors)

**Auto-Generated**:
- Connector auto-generates profiles based on model schema
- Profiles match model field names exactly

**Custom Profiles**:
- Use custom profiles for advanced filtering/field selection
- Build XML manually for complex queries

## Hub Authentication Token

### Token Generation

**Initial Token**:
- Auto-generated when repository created
- Found in Repository → Configure tab

**Regenerate Token**:
1. Navigate to Repositories page → Select repository
2. Click Configure tab
3. Click **Generate New** button
4. **WARNING**: Old token immediately invalidated

**Impact of Regeneration**:
- All integrations using old token fail immediately
- Update all DataHub connections with new token
- Coordinate with integration team before rotation

### Authorization Header (Manual HTTP Client)

If using HTTP Client connector instead of DataHub connector:

**Header Format**:
```
Authorization: Basic <Base64(accountID:hubAuthToken)>
```

**Example**:
```bash
# Encode credentials
echo -n "my-account-id:abc123token" | base64
# Output: bXktYWNjb3VudC1pZDphYmMxMjN0b2tlbg==

# Use in request
curl -X POST https://c01-usa-east.hub.boomi.com/mdm/universes/universe-123/records \
  -H "Authorization: Basic bXktYWNjb3VudC1pZDphYmMxMjN0b2tlbg==" \
  -H "Content-Type: application/xml" \
  -d @batch.xml
```

### Privileges with Hub Auth Token

Basic Auth (Hub Auth Token) provides **full administrator access**:

| Capability | Allowed |
|------------|---------|
| **Update/Upsert Golden Records** | ✅ Yes |
| **Query Golden Records** | ✅ Yes |
| **Match Entities** | ✅ Yes |
| **Query Quarantine** | ✅ Yes |
| **Resolve Quarantine** | ✅ Yes |
| **Reveal Masked Fields** | ✅ Yes (all masked data unmasked) |

**Security Note**: For role-based permissions, use JWT authentication (Platform API only).

## Error Handling

### Common Errors

**403 Forbidden** — Invalid credentials:
```xml
<UserMessage id="error.user.login" type="error">
  <Data>Incorrect user name and password combination.</Data>
</UserMessage>
```

**Fix**: Verify account ID and Hub Auth Token are correct.

**400 Bad Request** — Insufficient privileges:
```xml
<error>
  <message>The authenticated user does not have access rights to this functionality</message>
</error>
```

**Fix**: Ensure user has required MDM privilege (Batch Management, Stewardship, etc.).

**404 Not Found** — Universe/source not found:
```xml
<error>
  <message>A universe with id 'ac11cc59-c77a-4afe-8c92-ed86a7daabec' does not exist.</message>
</error>
```

**Fix**: Verify universe ID is correct and model is deployed.

**TOO_MANY_MATCHES** — Quarantine due to ambiguous match:
```xml
<MatchResult status="TOO_MANY_MATCHES">
  <entity>...</entity>
</MatchResult>
```

**Fix**: Refine match rules to reduce ambiguity, or handle quarantine workflow.

### Error Handling in Processes

**Try/Catch Pattern**:
```
[Start]
  ↓
[Try]
  ↓
[DataHub Connector] (Update/Upsert)
  ↓
[Branch on Success/Failure]
  ↙         ↘
[Success]  [Catch]
  ↓          ↓
[Log OK]  [Log Error]
           ↓
        [Alert Steward]
```

**Branch Shape**:
- Check HTTP response code (200 = success, 4xx/5xx = failure)
- Parse response XML for error details
- Route to appropriate error handling logic

## Best Practices

### Batch Size Optimization

| Batch Size | Use Case | Performance |
|------------|----------|-------------|
| 50-200 | Real-time sync | Fast response, low latency |
| 200-500 | Incremental sync | Balanced throughput |
| 500-1,000 | Bulk loads | High throughput, longer processing |

**Error Isolation**: Smaller batches = easier troubleshooting (failed entity identification).

### Idempotency

**Ensure batch submissions are idempotent**:
- Use consistent source entity IDs
- UPSERT behavior prevents duplicates (match rules + source links)
- Safe to retry on transient failures

**Example**:
```xml
<batch src="PROMOTION_ENGINE">
  <ComponentMapping>
    <id>comp-123-DEV_A</id> <!-- Consistent ID for retries -->
    <devComponentId>comp-123</devComponentId>
    <devAccountId>DEV_A</devAccountId>
  </ComponentMapping>
</batch>
```

If retry occurs, match rule detects existing link → Update (not duplicate creation).

### Monitoring

**Track Key Metrics**:
- Batch success/failure rates
- Quarantine entry volume (alert on spikes)
- Query response times
- Connector error counts

**Alerting**:
- Critical: Connector authentication failures
- High: Sudden increase in quarantine entries
- Medium: Slow query performance (100,000+ records without accelerated query)

### Pagination for Large Queries

**Problem**: Querying 10,000+ golden records in single request = timeout/memory issues.

**Solution**: Use limit + offset for pagination.

**Example**:
```xml
<!-- Page 1 -->
<RecordQueryRequest limit="500" offset="0">
  <!-- filters -->
</RecordQueryRequest>

<!-- Page 2 -->
<RecordQueryRequest limit="500" offset="500">
  <!-- filters -->
</RecordQueryRequest>
```

**Accelerated Query**: Enable for models with 100,000+ records for significant performance improvement.

## Project-Specific Connector Usage

### Process B: Query ComponentMapping

**Operation**: Query Golden Records

**Purpose**: Retrieve existing dev→prod mappings for reference rewriting.

**Request**:
```xml
<RecordQueryRequest limit="1000">
  <view>
    <fieldId>devComponentId</fieldId>
    <fieldId>prodComponentId</fieldId>
  </view>
  <filter op="AND">
    <fieldValue>
      <fieldId>devAccountId</fieldId>
      <operator>EQUALS</operator>
      <value>${devAccountId}</value>
    </fieldValue>
  </filter>
</RecordQueryRequest>
```

**Output**: Cache of dev→prod mappings loaded into DPP for Groovy script access.

### Process C: Validate Connection Mappings

**Operation**: Query Golden Records

**Purpose**: Validate all required connection mappings exist before promotion.

**Groovy Script**: `validate-connection-mappings.groovy` calls DataHub connector to check mapping existence.

**Failure**: If mapping missing → Fail promotion with error code `MISSING_CONNECTION_MAPPINGS`.

### Process D: Update ComponentMapping

**Operation**: Update/Upsert Golden Records

**Purpose**: Update ComponentMapping records after successful promotion.

**Request**:
```xml
<batch src="PROMOTION_ENGINE">
  <ComponentMapping>
    <id>${devComponentId}-${devAccountId}</id>
    <devComponentId>${devComponentId}</devComponentId>
    <devAccountId>${devAccountId}</devAccountId>
    <prodComponentId>${prodComponentId}</prodComponentId>
    <prodLatestVersion>${newVersion}</prodLatestVersion>
    <lastPromotedAt>${timestamp}</lastPromotedAt>
    <lastPromotedBy>${userEmail}</lastPromotedBy>
  </ComponentMapping>
</batch>
```

**Match Rule**: EXACT on `(devComponentId, devAccountId)` → UPSERT behavior.

### Process E: Query PromotionLog

**Operation**: Query Golden Records

**Purpose**: Retrieve promotion status for Flow dashboard display.

**Request**:
```xml
<RecordQueryRequest limit="200">
  <view>
    <fieldId>promotionId</fieldId>
    <fieldId>status</fieldId>
    <fieldId>componentsTotal</fieldId>
    <fieldId>initiatedBy</fieldId>
  </view>
  <filter op="AND">
    <fieldValue>
      <fieldId>initiatedBy</fieldId>
      <operator>EQUALS</operator>
      <value>${userEmail}</value>
    </fieldValue>
  </filter>
  <sort>
    <fieldId>initiatedAt</fieldId>
    <order>DESC</order>
  </sort>
</RecordQueryRequest>
```

**Output**: List of promotions initiated by current user, sorted by most recent.

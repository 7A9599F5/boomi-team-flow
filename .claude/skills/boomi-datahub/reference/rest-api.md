# DataHub REST APIs

## Overview

DataHub exposes two distinct REST API types for different use cases.

| API Type | Purpose | Base URL | Auth Methods |
|----------|---------|----------|--------------|
| **Repository API** | Golden record operations | `https://<hub-cloud-host>/mdm` | Basic Auth, JWT |
| **Platform API** | Admin operations (models, repos) | `https://api.boomi.com/mdm/api/rest/v1` | Basic Auth, API Token |

## Repository API

**Purpose**: Programmatic access to golden records, quarantine, and staging within a repository.

### Base URL

```
https://<hub-cloud-host>/mdm
```

**Find Hub Cloud Host**:
1. Integration → Manage → Runtime Management
2. Find repository name in runtime cloud list
3. Copy hostname (e.g., `c01-usa-east.hub.boomi.com`)

**Examples**:
- `https://c01-usa-east.hub.boomi.com/mdm`
- `https://c01-europe-west.hub.boomi.com/mdm`
- `https://c01-asia-pacific.hub.boomi.com/mdm`

### Authentication

#### 1. Basic Authentication

**Credentials**:
- **Username**: Boomi Account ID (from Repository → Configure tab)
- **Password**: Hub Auth Token (from Repository → Configure tab)

**Header Format**:
```
Authorization: Basic <Base64(accountID:hubAuthToken)>
```

**Example**:
```bash
echo -n "my-account-id:abc123token" | base64
# Output: bXktYWNjb3VudC1pZDphYmMxMjN0b2tlbg==

curl -X POST https://c01-usa-east.hub.boomi.com/mdm/universes/universe-123/records \
  -H "Authorization: Basic bXktYWNjb3VudC1pZDphYmMxMjN0b2tlbg==" \
  -H "Content-Type: application/xml" \
  -d @batch.xml
```

**Privileges**: Full administrator access to repository.

#### 2. JWT Authentication

**Credentials**:
- **Token**: JSON Web Token from Boomi Enterprise Platform authentication

**Header Format**:
```
Authorization: Bearer <jwt-token>
```

**Query Parameter Required**:
```
?repositoryId=<repository-id>
```

**Example**:
```bash
curl -X POST "https://c01-usa-east.hub.boomi.com/mdm/universes/universe-123/records?repositoryId=repo-456" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/xml" \
  -d @batch.xml
```

**Privileges**: Role-based access based on user's MDM privileges.

### Endpoints

#### Update/Upsert Golden Records

**Endpoint**:
```
POST /mdm/universes/{universeID}/records
```

**Purpose**: Submit batch of source entities to create/update golden records.

**Request**:
```xml
<batch src="SOURCE_ID">
  <ModelRootElement>
    <id>entity-1</id>
    <field1>value1</field1>
  </ModelRootElement>
</batch>
```

**Response** (Success):
```xml
<success>true</success>
```

**Response** (Failure):
```xml
<error>
  <message>Validation error details</message>
</error>
```

**Privilege Required**: `MDM - Batch Management`

#### Query Golden Records

**Endpoint**:
```
POST /mdm/universes/{universeID}/records/query
```

**Purpose**: Retrieve golden records with filtering, sorting, pagination.

**Request**:
```xml
<RecordQueryRequest limit="200" offset="0">
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

**Response**:
```xml
<Record recordId="gr-123" createdDate="2024-01-15T10:00:00Z" updatedDate="2024-02-20T14:30:00Z">
  <Fields>
    <ModelRootElement>
      <field1>value1</field1>
      <field2>value2</field2>
    </ModelRootElement>
  </Fields>
  <links>
    <link source="SOURCE_ID" entityId="entity-1" establishedDate="2024-01-15T10:00:00Z"/>
  </links>
</Record>
```

**Privilege Required**: `MDM - Stewardship` or `MDM - View Data`

#### Match Entities

**Endpoint**:
```
POST /mdm/universes/{universeID}/match
```

**Purpose**: Test match rules without committing data.

**Request**:
```xml
<batch src="TEST_SOURCE">
  <contact>
    <id>test-001</id>
    <name>bobby</name>
  </contact>
</batch>
```

**Response**:
```xml
<MatchEntitiesResponse>
  <MatchResult matchRule="Rule description" status="SUCCESS">
    <entity><!-- Incoming entity --></entity>
    <match><!-- Matching golden records not linked --></match>
    <duplicate><!-- Golden records already linked --></duplicate>
  </MatchResult>
</MatchEntitiesResponse>
```

#### Query Quarantine Entries

**Endpoint**:
```
POST /mdm/universes/{universeID}/quarantine/query
```

**Purpose**: Retrieve quarantined entities.

**Request**:
```xml
<QuarantineQueryRequest limit="100">
  <filter op="AND">
    <cause>MATCH_FAILURE</cause>
    <resolution>UNRESOLVED</resolution>
  </filter>
</QuarantineQueryRequest>
```

**Supported Filters**:
- **cause**: MATCH_FAILURE, DATA_QUALITY_FAILURE, VALIDATION_FAILURE
- **resolution**: UNRESOLVED, RESOLVED, IGNORED
- **createdDate**: Date range

**Response**:
```xml
<QuarantineEntry>
  <entity><!-- Quarantined source entity --></entity>
  <cause>TOO_MANY_MATCHES</cause>
  <matchingRecords><!-- Golden records that matched --></matchingRecords>
</QuarantineEntry>
```

#### Query Staging Area

**Endpoint**:
```
POST /mdm/universes/{universeID}/staging
```

**Purpose**: Query staged entities (test batches not yet committed).

**Request**:
```xml
<StagingQueryRequest limit="100">
  <stagingAreaID>staging-area-001</stagingAreaID>
</StagingQueryRequest>
```

**Response**: List of staged entities with match results.

#### Stage Batch

**Endpoint**:
```
POST /mdm/universes/{universeID}/staging/{stagingAreaID}
```

**Purpose**: Submit batch to staging area (test without committing).

**Request**:
```xml
<batch src="SOURCE_ID">
  <ModelRootElement>
    <id>entity-1</id>
    <field1>value1</field1>
  </ModelRootElement>
</batch>
```

**Response**: Match results and validation outcomes (no golden record changes).

#### Get Golden Record for Source Entity

**Endpoint**:
```
GET /mdm/universes/{universeID}/records/sources/{sourceID}/entities/{entityID}
```

**Purpose**: Retrieve golden record linked to specific source entity.

**Example**:
```bash
curl -X GET "https://c01-usa-east.hub.boomi.com/mdm/universes/universe-123/records/sources/PROMOTION_ENGINE/entities/entity-001" \
  -H "Authorization: Basic bXktYWNjb3VudC1pZDphYmMxMjN0b2tlbg=="
```

**Response**: Golden record XML with all fields and source links.

### Query Syntax

#### Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `EQUALS` | Exact match | `<operator>EQUALS</operator><value>comp-123</value>` |
| `NOT_EQUALS` | Not equal | `<operator>NOT_EQUALS</operator><value>inactive</value>` |
| `CONTAINS` | Substring match | `<operator>CONTAINS</operator><value>Order</value>` |
| `NOT_CONTAINS` | Does not contain | `<operator>NOT_CONTAINS</operator><value>Test</value>` |
| `GREATER_THAN` | Numeric/date > | `<operator>GREATER_THAN</operator><value>100</value>` |
| `LESS_THAN` | Numeric/date < | `<operator>LESS_THAN</operator><value>2024-01-01T00:00:00Z</value>` |
| `BETWEEN` | Date range | `<operator>BETWEEN</operator><value>2024-01-01...2024-12-31</value>` |

#### Compound Filters

**AND Logic** (all conditions must match):
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

**OR Logic** (any condition matches):
```xml
<filter op="OR">
  <fieldValue>
    <fieldId>status</fieldId>
    <operator>EQUALS</operator>
    <value>PENDING_PEER_REVIEW</value>
  </fieldValue>
  <fieldValue>
    <fieldId>status</fieldId>
    <operator>EQUALS</operator>
    <value>PENDING_ADMIN_REVIEW</value>
  </fieldValue>
</filter>
```

#### Source Link Filters

**Has Source Link**:
```xml
<filter op="AND">
  <sourceLink>
    <operator>Linked</operator>
    <source>PROMOTION_ENGINE</source>
  </sourceLink>
</filter>
```

**No Source Link**:
```xml
<filter op="AND">
  <sourceLink>
    <operator>Not Linked</operator>
    <source>PROMOTION_ENGINE</source>
  </sourceLink>
</filter>
```

#### Pagination

**Page 1** (first 500 records):
```xml
<RecordQueryRequest limit="500" offset="0">
  <!-- filters -->
</RecordQueryRequest>
```

**Page 2** (next 500 records):
```xml
<RecordQueryRequest limit="500" offset="500">
  <!-- filters -->
</RecordQueryRequest>
```

**Best Practice**: Use limit 200-1000 per page for optimal performance.

### Error Responses

**403 Forbidden** — Invalid credentials:
```xml
<UserMessage id="error.user.login" type="error">
  <Data>Incorrect user name and password combination.</Data>
</UserMessage>
```

**400 Bad Request** — Insufficient privileges:
```xml
<error>
  <message>The authenticated user does not have access rights to this functionality</message>
</error>
```

**404 Not Found** — Universe/source/entity not found:
```xml
<error>
  <message>A universe with id 'ac11cc59-c77a-4afe-8c92-ed86a7daabec' does not exist.</message>
</error>
```

**500 Internal Server Error** — DataHub processing error:
```xml
<error>
  <message>An unexpected error occurred. Please contact support.</message>
</error>
```

## Platform API

**Purpose**: Platform-level administrative operations on models, repositories, and universes.

### Base URL

```
https://api.boomi.com/mdm/api/rest/v1
```

**Note**: Platform API uses standard Boomi API endpoint (not Hub Cloud-specific).

### Authentication

#### 1. Basic Authentication

**Credentials**:
- **Username**: Boomi user email
- **Password**: User password

**Header Format**:
```
Authorization: Basic <Base64(email:password)>
```

**2FA Support**:
If user has 2FA enabled, include header:
```
X-Boomi-OTP: <authentication-code>
```

#### 2. API Token

**Credentials**:
- **Username**: API token ID
- **Password**: API token value

**Header Format**:
```
Authorization: Basic <Base64(tokenID:tokenValue)>
```

**Required Privilege**: `API Access` for all Platform API requests.

### Endpoints

#### List Models

**Endpoint**:
```
GET /mdm/api/rest/v1/{accountID}/models
```

**Purpose**: Retrieve all DataHub models in account.

**Example**:
```bash
curl -X GET "https://api.boomi.com/mdm/api/rest/v1/my-account-id/models" \
  -H "Authorization: Basic <base64-credentials>"
```

**Response**:
```json
[
  {
    "id": "model-123",
    "name": "ComponentMapping",
    "status": "PUBLISHED",
    "version": 2
  }
]
```

#### Get Model Details

**Endpoint**:
```
GET /mdm/api/rest/v1/{accountID}/models/{modelID}
```

**Purpose**: Retrieve detailed model definition (fields, match rules, sources).

**Response**: JSON model specification (same structure as model creation).

#### List Repositories

**Endpoint**:
```
GET /mdm/api/rest/v1/{accountID}/repositories
```

**Purpose**: Retrieve all DataHub repositories in account.

**Response**:
```json
[
  {
    "id": "repo-123",
    "name": "Production Repository",
    "cloudHost": "c01-usa-east.hub.boomi.com"
  }
]
```

#### Deploy Model to Repository

**Endpoint**:
```
POST /mdm/api/rest/v1/{accountID}/repositories/{repoID}/universes/{universeID}/deploy
```

**Purpose**: Deploy published model version to repository (creates or updates universe).

**Request**:
```json
{
  "modelID": "model-123",
  "modelVersion": 2
}
```

**Response**: Deployment status and universe ID.

#### Query Staged Entities (Platform API Variant)

**Endpoint**:
```
POST /mdm/api/rest/v1/{accountID}/repositories/{repoID}/universes/{universeID}/staging
```

**Purpose**: Query staged entities via Platform API (alternative to Repository API).

**Note**: Repository API variant is more commonly used for staging queries.

### Response Formats

**Repository API**: XML only

**Platform API**: XML or JSON (depending on endpoint, most support JSON)

## API Comparison

| Aspect | Repository API | Platform API |
|--------|---------------|--------------|
| **Base URL** | `https://<hub-cloud-host>/mdm` | `https://api.boomi.com/mdm/api/rest/v1` |
| **Auth** | Basic (Hub Auth Token) or JWT | Basic (user credentials) or API Token |
| **Purpose** | Golden record operations | Admin operations (models, repos) |
| **Response Format** | XML | XML or JSON |
| **Use Cases** | Data sync, query, UPSERT | Model deployment, repository management |
| **Privileges** | MDM privileges (Batch, Stewardship, etc.) | API Access + operation-specific privileges |

## Best Practices

### Repository API

**1. Use Hub Auth Token for Integration**:
- Simple authentication (no user passwords)
- Full admin privileges (suitable for system-to-system integration)
- Rotate tokens periodically for security

**2. Use JWT for User-Level Access**:
- Enforce role-based permissions
- Mask sensitive fields based on user roles
- Audit trail per user

**3. Pagination for Large Queries**:
- Use `limit` + `offset` for queries returning 1,000+ records
- Avoid querying all records in single request (timeout risk)

**4. Error Handling**:
- Parse error responses for actionable details
- Retry on transient failures (5xx errors)
- Alert on authentication failures (403)

### Platform API

**1. Use API Tokens for Automation**:
- Avoid hardcoding user passwords
- Rotate tokens regularly
- Scope tokens to minimum required privileges

**2. Model Versioning**:
- Always publish models before deployment
- Test new versions in dev repository before production
- Maintain version history for rollback capability

**3. Deployment Coordination**:
- Coordinate model deployments with integration team (connector operations depend on deployed schema)
- Avoid deploying breaking changes without integration updates

## Project-Specific API Usage

### Process B: Query ComponentMapping

**API**: Repository API

**Endpoint**: `POST /mdm/universes/{componentMappingUniverseID}/records/query`

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

**Purpose**: Load mapping cache for Groovy reference rewriting script.

### Process E2: Query Peer Review Queue

**API**: Repository API

**Endpoint**: `POST /mdm/universes/{promotionLogUniverseID}/records/query`

**Request**:
```xml
<RecordQueryRequest limit="200">
  <view>
    <fieldId>promotionId</fieldId>
    <fieldId>status</fieldId>
    <fieldId>initiatedBy</fieldId>
    <fieldId>componentsTotal</fieldId>
  </view>
  <filter op="AND">
    <fieldValue>
      <fieldId>peerReviewStatus</fieldId>
      <operator>EQUALS</operator>
      <value>PENDING_PEER_REVIEW</value>
    </fieldValue>
    <fieldValue>
      <fieldId>initiatedBy</fieldId>
      <operator>NOT_EQUALS</operator>
      <value>${currentUserEmail}</value>
    </fieldValue>
  </filter>
  <sort>
    <fieldId>initiatedAt</fieldId>
    <order>DESC</order>
  </sort>
</RecordQueryRequest>
```

**Purpose**: Retrieve promotions awaiting peer review (exclude own promotions for self-review prevention).

### Admin: Seed Connection Mappings

**API**: Repository API

**Endpoint**: `POST /mdm/universes/{componentMappingUniverseID}/records`

**Request**:
```xml
<batch src="ADMIN_SEEDING">
  <ComponentMapping>
    <id>conn-shared-salesforce-DEV_A</id>
    <devComponentId>conn-dev-salesforce-123</devComponentId>
    <devAccountId>DEV_A</devAccountId>
    <prodComponentId>conn-shared-salesforce</prodComponentId>
    <componentName>Salesforce Production</componentName>
    <componentType>connection</componentType>
    <prodAccountId>PRIMARY_ACCT</prodAccountId>
    <prodLatestVersion>1</prodLatestVersion>
    <lastPromotedAt>2024-01-01T00:00:00.000Z</lastPromotedAt>
    <lastPromotedBy>admin@company.com</lastPromotedBy>
    <mappingSource>ADMIN_SEEDING</mappingSource>
  </ComponentMapping>
</batch>
```

**Purpose**: Pre-configure connection mappings linking dev connection IDs to parent account shared connections (in `#Connections` folder).

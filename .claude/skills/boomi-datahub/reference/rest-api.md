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

**Purpose**: Platform-level administrative operations on models, repositories, sources, and universes.

All operations are **account-scoped** (not repository-scoped). Models and sources are account-level resources that get deployed/attached to repositories via universe operations.

### Base URL

```
https://api.boomi.com/mdm/api/rest/v1/{accountID}
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
- **Username**: `BOOMI_TOKEN.{user}`
- **Password**: API token value

**Header Format**:
```
Authorization: Basic <Base64(BOOMI_TOKEN.user:tokenValue)>
```

**Required Privilege**: `API Access` for all Platform API requests. Individual operations require additional MDM privileges listed below.

### Response Format

**All Platform API responses are XML** (namespace `http://mdm.api.platform.boomi.com/`). Unlike the AtomSphere API, the DataHub Platform API does not support JSON request/response bodies.

### Hub Cloud Endpoints

#### Get Hub Clouds

```
GET /{accountID}/clouds
```

List available Hub Clouds for the account. Required before creating a repository.

**Privilege**: `MDM - Repository Management`

**Response**:
```xml
<mdm:Clouds xmlns:mdm="http://mdm.api.platform.boomi.com/">
    <mdm:Cloud cloudId="01234567-89ab-cdef-0123-456789abcdef"
               containerId="fedcba98-7654-3210-fedc-ba9876543210"
               name="USA East Hub Cloud"/>
</mdm:Clouds>
```

### Repository Endpoints

#### Create Repository

```
POST /{accountID}/clouds/{cloudID}/repositories/{repositoryName}/create
```

Request async creation of a repository on a specified Hub Cloud. Poll status with Get Repository Creation Status.

**Request Body**: Empty

**Privilege**: `MDM - Repository Management`

**Response** (200): Plain text repository ID string:
```
23456789-abcd-ef01-2345-6789abcdef01
```

**Errors**: 400 if privileges missing or cloud repo limit exceeded.

#### Get Repository Creation Status

```
GET /{accountID}/repositories/{repositoryID}/status
```

Poll async repository creation progress.

**Response**:
```xml
<mdm:RepositoryStatus xmlns:mdm="http://mdm.api.platform.boomi.com/" status="SUCCESS"/>
```

**Status values**: `SUCCESS`, `PENDING`, `DELETED`

#### Delete Repository

```
DELETE /{accountID}/repositories/{repositoryID}
```

Delete a repository. **Cannot delete if it contains a deployed model** — undeploy first.

**Privilege**: `MDM - Repository Management`

**Response** (200): `true`

#### Get Repositories Summary

```
GET /{accountID}/repositories
```

List all repositories with record counts per universe.

**Privilege**: `MDM - View Repositories`

**Response**:
```xml
<mdm:Repositories xmlns:mdm="http://mdm.api.platform.boomi.com/">
    <mdm:Repository id="repo-123" name="PromotionHub"
                    atomName="PromotionHub" repositoryBaseUrl="c01-usa-east.hub.boomi.com">
        <mdm:Universe name="ComponentMapping" id="univ-456">
            <mdm:goldenRecords>150</mdm:goldenRecords>
            <mdm:quarantinedRecords>3</mdm:quarantinedRecords>
        </mdm:Universe>
    </mdm:Repository>
</mdm:Repositories>
```

#### Get Repository Summary

```
GET /{accountID}/repositories/{repositoryID}
```

Get a single repository with aggregate counts and per-universe breakdown.

**Privilege**: `MDM - View Repositories`

**Response**: Same structure as single `<mdm:Repository>` element above.

### Model Endpoints

Models are **account-level** resources. They are deployed to repositories via Universe operations.

#### Get Models (List)

```
GET /{accountID}/models
```

**Optional Query Parameters**:
- `name` — filter by model name
- `publicationStatus` — `all`, `draft`, or `publish`

**Privilege**: `MDM - View Models`

**Response**:
```xml
<mdm:Models xmlns:mdm="http://mdm.api.platform.boomi.com/">
    <mdm:Model>
        <mdm:name>ComponentMapping</mdm:name>
        <mdm:id>model-123</mdm:id>
        <mdm:publicationStatus>true</mdm:publicationStatus>
        <mdm:latestVersion>2</mdm:latestVersion>
    </mdm:Model>
</mdm:Models>
```

#### Get Model (Detail)

```
GET /{accountID}/models/{modelID}
GET /{accountID}/models/{modelID}?version={version}
GET /{accountID}/models/{modelID}?draft=true
```

Retrieve full model definition (fields, match rules, sources, tags).

**Privilege**: `MDM - View Models`

**Response**: `<mdm:GetModelResponse>` with full model specification.

#### Create Model

```
POST /{accountID}/models
```

**Request Body** (XML):
```xml
<mdm:CreateModelRequest xmlns:mdm="http://mdm.api.platform.boomi.com/"
                        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <mdm:name>ComponentMapping</mdm:name>
    <mdm:fields>
        <mdm:field name="devComponentId" type="STRING" required="true"/>
        <!-- ... -->
    </mdm:fields>
    <mdm:matchRules><!-- ... --></mdm:matchRules>
</mdm:CreateModelRequest>
```

**Privilege**: `MDM - Edit Models`

**Response**:
```xml
<mdm:CreateModelResponse xmlns:mdm="http://mdm.api.platform.boomi.com/">
    <mdm:id>model-123</mdm:id>
</mdm:CreateModelResponse>
```

**Model name**: 2-40 characters.

#### Update Model

```
PUT /{accountID}/models/{modelID}
```

Copy `<mdm:GetModelResponse>` content into `<mdm:UpdateModelRequest>` and modify.

**Privilege**: `MDM - Edit Models`

**Response**:
```xml
<mdm:UpdateModelResponse xmlns:mdm="http://mdm.api.platform.boomi.com/">
    <mdm:id>model-123</mdm:id>
</mdm:UpdateModelResponse>
```

#### Publish Model

```
POST /{accountID}/models/{modelID}/publish
```

**Request Body** (XML):
```xml
<mdm:PublishModelRequest xmlns:mdm="http://mdm.api.platform.boomi.com/"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <mdm:notes>Initial publish</mdm:notes>
</mdm:PublishModelRequest>
```

**Privilege**: `MDM - Edit Models`

**Response**:
```xml
<mdm:PublishModelResponse xmlns:mdm="http://mdm.api.platform.boomi.com/">
    <mdm:version>1</mdm:version>
    <mdm:lastModifiedDate>2024-01-15T10:00:00Z</mdm:lastModifiedDate>
    <mdm:user>admin@company.com</mdm:user>
</mdm:PublishModelResponse>
```

#### Delete Model

```
DELETE /{accountID}/models/{modelID}
```

**Cannot delete while deployed** — undeploy first.

**Privilege**: `MDM - Edit Models`

**Response** (200): `true`

### Source Endpoints

Sources are **account-level** resources attached to models, not repositories.

#### Get Sources

```
GET /{accountID}/sources
```

**Privilege**: `MDM - Source Management`

**Response**:
```xml
<mdm:AccountSources xmlns:mdm="http://mdm.api.platform.boomi.com/">
    <mdm:AccountSource>
        <mdm:name>PROMOTION_ENGINE</mdm:name>
        <mdm:sourceId>PROMOTION_ENGINE</mdm:sourceId>
    </mdm:AccountSource>
    <mdm:AccountSource>
        <mdm:name>ADMIN_SEEDING</mdm:name>
        <mdm:sourceId>ADMIN_SEEDING</mdm:sourceId>
    </mdm:AccountSource>
</mdm:AccountSources>
```

#### Create Source

```
POST /{accountID}/sources/create
```

**Request Body** (XML):
```xml
<mdm:CreateSourceRequest xmlns:mdm="http://mdm.api.platform.boomi.com/"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <mdm:name>PROMOTION_ENGINE</mdm:name>
    <mdm:sourceId>PROMOTION_ENGINE</mdm:sourceId>
</mdm:CreateSourceRequest>
```

- `name`: max 255 characters
- `sourceId`: max 50 characters, alphanumeric + underscore + hyphen only
- `entityIdUrl` (optional): URL template with `{id}` placeholder

**Privilege**: `MDM - Source Management`

**Response** (200): `<true/>`

#### Delete Source

```
DELETE /{accountID}/sources/{sourceID}
```

**Cannot delete** if embedded in a model or attached to a universe.

**Privilege**: `MDM - Source Management`

**Response** (200): `true`

### Universe (Deployment) Endpoints

Universes connect models to repositories. "Universe" = a deployed model instance within a repository.

#### Deploy Universe

```
POST /{accountID}/universe/{universeID}/deploy?repositoryId={repositoryID}
POST /{accountID}/universe/{universeID}/deploy?version={versionID}&repositoryId={repositoryID}
```

Deploy a published model version to a repository. `version` defaults to latest if omitted.

**Request Body**: Empty

**Privilege**: `MDM - Model Deployment`

**Response**:
```xml
<mdm:UniverseDeployment xmlns:mdm="http://mdm.api.platform.boomi.com/">
    <mdm:id>deploy-789</mdm:id>
    <mdm:universeId>model-123</mdm:universeId>
    <mdm:universeVersion>1</mdm:universeVersion>
    <mdm:status>PENDING</mdm:status>
    <mdm:deployDate>2024-01-15T10:00:00Z</mdm:deployDate>
</mdm:UniverseDeployment>
```

**Note**: `universeID` = `modelID`. The path uses singular `/universe/` not `/universes/`.

#### Get Universe Deployment Status

```
GET /{accountID}/universe/{universeID}/deployments/{deploymentID}
```

Poll async deployment progress. `deploymentID` from Deploy Universe response.

**Status values**: `SUCCESS`, `PENDING`, `CANCELED`

**Response**: Same `<mdm:UniverseDeployment>` structure with updated status and `completionDate`.

#### Get Universe Summary

```
GET /{accountID}/repositories/{repositoryID}/universes/{universeID}
```

Get record counts for a deployed universe within a repository.

**Privilege**: `MDM - View Repositories`

**Response**:
```xml
<mdm:Universe name="ComponentMapping" id="model-123">
    <mdm:goldenRecords>150</mdm:goldenRecords>
    <mdm:quarantinedRecords>3</mdm:quarantinedRecords>
    <mdm:pendingBatches>0</mdm:pendingBatches>
</mdm:Universe>
```

#### Undeploy Universe

```
DELETE /{accountID}/repositories/{repositoryID}/universe/{universeID}
```

Remove model deployment from repository. **Destroys associated data and source connections.**

**Privilege**: `MDM - Model Removal`

**Response** (200): `<true/>`

### Other Platform API Operations

These operations are available but not used by the promotion system:

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Get Source | GET | `/{accountID}/sources/{sourceID}` |
| Update Source | PUT | `/{accountID}/sources/{sourceID}` |
| Get Source Status | GET | `/{accountID}/sources/{sourceID}/status` |
| Import Domain Source Config | POST | `/{accountID}/models/{modelID}/sources/import` |
| Enable Initial Load Mode | POST | `/{accountID}/repositories/{repoID}/universes/{univID}/initialLoad/enable` |
| Finish Initial Load | POST | `/{accountID}/repositories/{repoID}/universes/{univID}/initialLoad/finish` |
| Query Transactions | POST | `/{accountID}/repositories/{repoID}/universes/{univID}/transactions/query` |
| Add Staging Area | POST | `/{accountID}/repositories/{repoID}/universes/{univID}/staging` |
| Get Staging Area Status | GET | `/{accountID}/repositories/{repoID}/universes/{univID}/staging/{stagingID}` |
| Quarantine operations | various | `/{accountID}/repositories/{repoID}/universes/{univID}/quarantine/...` |

### Common Error Responses

**400 Bad Request** — Missing privileges or invalid parameters:
```xml
<error>
    <message>The authenticated user does not have access rights to this functionality</message>
</error>
```

**403 Forbidden** — Authentication failure:
```xml
<UserMessage id="error.user.login" type="error">
    <Data>Incorrect user name and password combination.</Data>
</UserMessage>
```

## API Comparison

| Aspect | Repository API | Platform API |
|--------|---------------|--------------|
| **Base URL** | `https://<hub-cloud-host>/mdm` | `https://api.boomi.com/mdm/api/rest/v1/{accountID}` |
| **Auth** | Basic (Hub Auth Token) or JWT | Basic (user credentials) or `BOOMI_TOKEN` API Token |
| **Purpose** | Golden record CRUD | Admin operations (models, repos, sources, deployments) |
| **Response Format** | XML | XML |
| **Resource Scope** | Repository-scoped (universes) | Account-scoped (models, sources, repos, clouds) |
| **Use Cases** | Data sync, query, UPSERT, quarantine | Model lifecycle, repository management, deployments |
| **Privileges** | MDM privileges (Batch, Stewardship, etc.) | API Access + operation-specific MDM privileges |

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

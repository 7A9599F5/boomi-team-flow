---
name: boomi-datahub
description: |
  Boomi DataHub (MDM) reference. Use when working with DataHub models, match
  rules, golden records, DataHub connector operations (Query, Update/Upsert),
  Hub authentication, or the DataHub REST API.
globs:
  - "datahub/**"
  - "**/*datahub*"
  - "**/*DataHub*"
---

# Boomi DataHub Skill

**Purpose**: Master Data Management (MDM) reference for working with Boomi DataHub repositories, models, golden records, match rules, and connector operations.

## When to Use This Skill

Use this skill when:
- Working with DataHub model definitions, field types, or constraints
- Configuring match rules for UPSERT behavior
- Building Integration processes with DataHub connector
- Querying or updating golden records via API
- Setting up Hub authentication
- Troubleshooting quarantine entries or duplicate detection

## Architecture Overview

```
Boomi DataHub
    ├── Repositories (Virtual runtimes in Hub Cloud)
    │   └── Universes (Deployed domains from models)
    │       ├── Golden Records (Authoritative master data)
    │       ├── Source Links (Lineage to source entities)
    │       ├── Match Rules (UPSERT logic)
    │       └── Quarantine (Failed validations)
    │
    ├── Models (Data schemas)
    │   ├── Fields (String, Number, Date, Boolean, Long Text)
    │   ├── Match Rules (EXACT, Fuzzy)
    │   ├── Sources (Contributor/acceptor settings)
    │   └── Data Quality Steps (Validation, enrichment)
    │
    └── APIs
        ├── Repository API (Golden record operations)
        └── Platform API (Admin operations)
```

**Key Concept**: DataHub merges data from multiple source systems into single "golden records" using configurable match rules, providing a unified source of truth.

## Match Rule Quick Reference

Match rules determine when to **CREATE** new golden records vs. **UPDATE** existing ones (UPSERT behavior).

### Match Rule Types

| Type | Description | Use Case |
|------|-------------|----------|
| **EXACT** | All fields must exactly match | Unique IDs, compound keys |
| **Fuzzy** | Similarity algorithms (Jaro-Winkler, Levenshtein, Soundex) | Name matching with typos |

### Match Rule Behavior

```
Incoming Entity
    ↓
Check for existing source link
    ↓ (if no link)
Apply match rules in order
    ↓
┌─────────────────────────────────────┐
│ No match → CREATE golden record    │
│ Match found → UPDATE golden record  │
│ Multiple matches → QUARANTINE       │
│ Already linked → Skip               │
└─────────────────────────────────────┘
```

### EXACT Match Examples

**Single Field:**
```json
{
  "type": "EXACT",
  "description": "Match on promotion ID",
  "fields": ["promotionId"]
}
```

**Compound Key (Multi-Field):**
```json
{
  "type": "EXACT",
  "description": "Compound match on component ID and account ID",
  "fields": ["devComponentId", "devAccountId"]
}
```

**CRITICAL**: Incoming record must match ALL specified fields to be considered a match.

### Match Rule Ordering

**ALWAYS order from most restrictive to least restrictive:**

1. **Strictest**: `EXACT on lastName + firstName + dateOfBirth`
2. **Medium**: `EXACT on email`
3. **Least Strict**: `FUZZY on lastName`

If reversed, the least strict rule would match first and prevent stricter rules from evaluating.

### Match Result Statuses

| Status | Meaning |
|--------|---------|
| **SUCCESS** | Request processed successfully |
| **TOO_MANY_MATCHES** | 10+ EXACT matches (1,000+ fuzzy) → quarantined |
| **ALREADY_LINKED** | Entity already linked to golden record |
| **MATCH_REFERENCE_FAILURE** | Reference field value doesn't resolve |
| **FAILED_TO_RUN** | Internal error occurred |

## DataHub Connector Operations

The Boomi DataHub Connector provides low-code integration with DataHub repositories.

### Update/Upsert Golden Records

**Purpose**: Send batch of source entities to create/update golden records.

**Operation Type**: Outbound

**Request Format**:
```xml
<batch src="SOURCE_ID">
  <ModelRootElement>
    <id>source-entity-id</id>
    <field1>value1</field1>
    <field2>value2</field2>
  </ModelRootElement>
  <ModelRootElement>
    <!-- Additional entities -->
  </ModelRootElement>
</batch>
```

**Process Flow**:
1. Connector receives batch from Integration process
2. For each entity:
   - Check existing link → Update if linked
   - If not linked → Apply match rules
   - Match found → Update + link
   - No match → Create new golden record
   - Error → Quarantine
3. Return success/failure status

**Endpoint**: `POST /mdm/universes/{universeID}/records`

**Privilege Required**: `MDM - Batch Management`

### Query Golden Records

**Purpose**: Retrieve active golden records with optional filtering.

**Operation Type**: Inbound

**Features**:
- Field selection (choose which fields to return)
- Filtering (EQUALS, CONTAINS, BETWEEN, etc.)
- Sorting (order by field values)
- Pagination (limit/offset)
- Accelerated Query (for 100,000+ records)

**Request Example**:
```xml
<RecordQueryRequest limit="200">
  <view>
    <fieldId>devComponentId</fieldId>
    <fieldId>prodComponentId</fieldId>
  </view>
  <filter op="AND">
    <fieldValue>
      <fieldId>devComponentId</fieldId>
      <operator>EQUALS</operator>
      <value>comp-123</value>
    </fieldValue>
  </filter>
</RecordQueryRequest>
```

**Response Example**:
```xml
<Record recordId="c863..." createdDate="2024-04-26T19:48:20Z">
  <Fields>
    <ComponentMapping>
      <devComponentId>comp-123</devComponentId>
      <prodComponentId>comp-789</prodComponentId>
    </ComponentMapping>
  </Fields>
  <links>
    <link source="PROMOTION_ENGINE" entityId="entity-001"/>
  </links>
</Record>
```

**Endpoint**: `POST /mdm/universes/{universeID}/records/query`

**Privilege Required**: `MDM - Stewardship` or `MDM - View Data`

### Match Entities (Test Rules)

**Purpose**: Test match rules without committing data to golden records.

**Operation Type**: Outbound

**Use Cases**:
- Validate match rule configuration before deployment
- Preview duplicate detection for incoming batch
- Troubleshoot quarantine issues

**Response Includes**:
- **match**: Matching golden records not yet linked
- **duplicate**: Matching golden records already linked
- **fuzzyMatchDetails**: Similarity scores (if fuzzy rules)

**Endpoint**: `POST /mdm/universes/{universeID}/match`

### Other Operations

| Operation | Purpose |
|-----------|---------|
| **Query Quarantine Entries** | Retrieve quarantined records |
| **Load/Update Quarantined Records** | Manage quarantine resolution |

## Hub Auth Token Setup Checklist

DataHub uses **Basic Authentication** with repository-specific credentials.

**Required Credentials**:
1. **Username**: Boomi Account ID (found in Repository → Configure tab)
2. **Password**: Hub Authentication Token (from Repository → Configure tab)

**Authorization Header Format**:
```
Authorization: Basic <Base64(accountID:hubAuthToken)>
```

**Example**:
```bash
# Encode credentials
echo -n "my-account-id:abc123token" | base64

# Use in request
curl -X POST https://c01-usa-east.hub.boomi.com/mdm/universes/universe-123/records \
  -H "Authorization: Basic bXktYWNjb3VudC1pZDphYmMxMjN0b2tlbg==" \
  -H "Content-Type: application/xml" \
  -d @batch.xml
```

**DataHub Connector Configuration**:
1. Select **Boomi Hub Cloud Name** from dropdown (e.g., `c01-usa-east.hub.boomi.com`)
   - OR enter **Custom Cloud URL**: `https://<cloud-host>/mdm`
2. Enter **Username**: Repository username
3. Enter **Authentication Token**: Hub Auth Token

**Find Hub Cloud Host**:
1. Integration → Manage → Runtime Management
2. Find repository name in runtime cloud list
3. Copy hostname (e.g., `c01-usa-east.hub.boomi.com`)

**Token Regeneration** (CRITICAL):
- Regenerating token immediately invalidates old token
- Breaks existing integrations using old token
- Coordinate with integration team before rotation

**Privileges**:
- Basic Auth = Full administrator access (all operations permitted)
- JWT Auth = Role-based permissions (use for user-level access)

**Connector Authentication**:
- DataHub Connector uses Basic Auth only (no JWT support)
- Provides administrator-level privileges
- Masked field values are unmasked in connector responses

## Common Patterns

### UPSERT Pattern

```
1st Submission (devComponentId=comp-123, devAccountId=DEV_A):
   No match → CREATE golden record GR-001
   Link source entity to GR-001

2nd Submission (same keys, updated fields):
   Existing link found → UPDATE GR-001 directly
   Skip match rules

3rd Submission (same keys from different source):
   No link for this source → Apply match rules
   Match on compound key → UPDATE GR-001
   Link new source entity to GR-001
   Merge field values based on source ranking
```

### Batch Processing

**Best Practices**:
- **Small batches**: 50-200 entities for real-time sync
- **Large batches**: Up to 1,000 entities for bulk loads
- **Error isolation**: Individual entity failures don't fail entire batch
- **Staging**: Test batches in staging area before production

**Batch XML Structure**:
```xml
<batch src="SOURCE_ID">
  <RootElement>
    <id>entity-1</id>
    <field1>value1</field1>
  </RootElement>
  <RootElement>
    <id>entity-2</id>
    <field1>value1</field1>
  </RootElement>
</batch>
```

**Reserved Source ID**: `*MDM*` (used for manual data steward submissions, do NOT use in API requests)

### Quarantine Handling

**Quarantine Causes**:
- **TOO_MANY_MATCHES**: 10+ EXACT matches or 1,000+ fuzzy matches
- **ALREADY_LINKED**: Duplicate source entity for same source
- **MATCH_REFERENCE_FAILURE**: Reference field doesn't resolve
- **Data Quality Failure**: Failed business rule or validation

**Resolution Options**:
1. Link to existing golden record
2. Create new golden record
3. Fix data and resubmit
4. Mark as duplicate/ignore

**Query Quarantine**:
```
POST /mdm/universes/{universeID}/quarantine/query
```

## Reference Files

For detailed information on specific topics, see:

- **`reference/models-fields.md`**: Model definitions, field types, constraints, layout types
- **`reference/match-rules.md`**: Match rule configuration, UPSERT behavior, compound keys
- **`reference/connector-operations.md`**: Query, Update/Upsert, connector config, Hub Auth Token
- **`reference/rest-api.md`**: Repository API, Platform API endpoints, query syntax
- **`reference/golden-records.md`**: Source records, merging logic, quarantine, source ranking

## Example Files

Project-specific DataHub patterns:

- **`examples/promotion-models.md`**: ComponentMapping, DevAccountAccess, PromotionLog model patterns for this project

## Key Takeaways

1. **Match Rules Are UPSERT Logic**: They determine create vs. update behavior
2. **Compound Keys Prevent Collisions**: Use multi-field EXACT matches for uniqueness (e.g., `devComponentId + devAccountId`)
3. **Order Matters**: Match rules execute sequentially, first match wins
4. **Source Links Track Lineage**: Every golden record knows which sources contributed
5. **Connector vs. HTTP Client**: Connector simplifies common operations, HTTP Client provides full API control
6. **Hub Auth Token = Admin Access**: Use JWT for role-based permissions
7. **Quarantine = Manual Review**: Too many matches or validation failures require data steward intervention
8. **Staging = Safe Testing**: Preview batch processing without committing to production

## Why DataHub for This Project

From `/home/glitch/code/boomi_team_flow/docs/architecture.md`:

**DataHub vs. External Database**:
- **Sub-second latency**: DataHub accessible without firewall issues from Public Boomi Cloud Atom
- **Built-in UPSERT**: Match rules eliminate custom merge logic
- **No 30s+ latency**: External DBs suffer from firewall/domain limitations
- **Simplified architecture**: No external DB infrastructure to manage

**Project-Specific Models**:
1. **ComponentMapping**: Maps dev component IDs → prod component IDs (compound key on `devComponentId + devAccountId`)
2. **DevAccountAccess**: Controls SSO group access to dev accounts (compound key on `ssoGroupId + devAccountId`)
3. **PromotionLog**: Audit trail with 2-layer approval workflow (single key on `promotionId`)

**Key Design Decision**:
> Match rules provide built-in UPSERT behavior — no custom Groovy scripting needed for merge logic.

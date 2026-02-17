# Golden Records

## Overview

**Golden Records** are single, authoritative master records created by merging and enriching data from multiple source systems.

**Key Concept**: Instead of each system maintaining its own version of "Customer #123", DataHub creates one golden record that represents the true, unified view of that customer.

## Source Records vs. Golden Records

### Source Records

**Definition**: Individual entity records stored in contributing source systems (Salesforce, MySQL, SAP, etc.).

**Characteristics**:
- **Source-Specific**: Each source maintains its own copy
- **Potentially Inconsistent**: Same entity may have different field values across sources
- **Linked to Golden Record**: Via source entity ID
- **Audit Trail**: Track which source contributed each field value

**Example**:
```
Salesforce Contact (Source Record):
  - Source Entity ID: SF-12345
  - Name: "Robert Smith"
  - Email: "bob@company.com"
  - Phone: "555-1234"
  - Source: SALESFORCE

MySQL Customer (Source Record):
  - Source Entity ID: MYSQL-67890
  - Name: "Bob Smith"
  - Email: "robert.smith@company.com"
  - Phone: "555-1234"
  - Source: MYSQL
```

**Problem**: Both represent the same person but with slight differences (name variation, email variation).

### Golden Records

**Definition**: Single, authoritative master record created by merging source records.

**Characteristics**:
- **Single Source of Truth**: One record per unique entity
- **Merged Data**: Field values combined from multiple sources
- **Data Quality Applied**: Validated, cleansed, enriched
- **Source Links**: Tracks which sources contributed
- **Conflict Resolution**: Source ranking determines priority

**Example**:
```
Golden Record (Merged):
  - Golden Record ID: GR-ABC123
  - Name: "Robert Smith" (from Salesforce, ranked higher)
  - Email: "robert.smith@company.com" (from MySQL, more complete)
  - Phone: "555-1234" (consensus from both)
  - Linked Sources:
    - Salesforce: SF-12345 (established 2024-01-15)
    - MySQL: MYSQL-67890 (established 2024-02-20)
```

**Benefit**: Downstream systems query DataHub for golden record → receive consistent, authoritative data.

## Golden Record Lifecycle

### 1. First Source Entity Arrives

```
Source Entity 1 (Salesforce: SF-12345)
    ↓
No existing link to golden record
    ↓
Apply match rules
    ↓
No match found (no existing golden records)
    ↓
CREATE new golden record GR-ABC123
    ↓
Link SF-12345 to GR-ABC123
```

**Result**: Golden record GR-ABC123 created with data from Salesforce.

### 2. Second Source Entity Arrives (Same Person)

```
Source Entity 2 (MySQL: MYSQL-67890)
    ↓
No existing link to golden record
    ↓
Apply match rules (EXACT on email)
    ↓
Match found: GR-ABC123 (same email "robert.smith@company.com")
    ↓
UPDATE golden record GR-ABC123
    ↓
Merge field values (source ranking)
    ↓
Link MYSQL-67890 to GR-ABC123
```

**Result**: Golden record GR-ABC123 now has 2 source links, merged field values.

### 3. Source Entity Updates

```
Source Entity 1 (Salesforce: SF-12345) — Phone updated to "555-9999"
    ↓
Existing link found to GR-ABC123
    ↓
Skip match rules (link provides direct path)
    ↓
UPDATE golden record GR-ABC123
    ↓
Merge updated field values (source ranking)
```

**Result**: Golden record phone number updated to "555-9999" (if Salesforce has higher priority than MySQL).

### 4. End-Dating Golden Record

```
Source Entity 1 (Salesforce: SF-12345) — Customer closed account
    ↓
Submit entity with end-date flag
    ↓
Golden record GR-ABC123 end-dated
    ↓
Excluded from active queries
    ↓
Historical data retained
```

**Result**: Golden record marked as inactive, preserved for audit/compliance.

## Merging Logic

### Source Ranking

**Purpose**: Determine which source "wins" when field values conflict.

**Configuration**:
- **Source Ranking**: Priority order (1 = highest priority)
- **Default Source**: Used when no ranking specified

**Example Ranking**:
```
1. ERP System (most authoritative for financial data)
2. CRM System (authoritative for customer contact info)
3. Marketing Automation (least authoritative)
```

**Conflict Resolution**:

Incoming data:
- Salesforce (rank 2): `creditLimit: 10000`
- ERP (rank 1): `creditLimit: 15000`

**Result**: Golden record `creditLimit: 15000` (ERP ranked higher).

### Field-Level Source Priority

Some models configure source priority per field (not globally):

**Example**:
- **Name** field → Use CRM value (CRM more accurate for names)
- **Credit Limit** field → Use ERP value (ERP authoritative for financials)
- **Email** field → Use most recent update (timestamp-based)

**Configuration**: Set in model data quality steps or source settings.

### Data Enrichment

**Purpose**: Enhance golden records with computed or third-party data.

**Data Quality Steps**:
- **Address Standardization**: Loqate API validates and formats addresses
- **Phone Formatting**: Convert to E.164 format (+1-555-1234)
- **Geocoding**: Add latitude/longitude from address
- **Email Validation**: Verify email deliverability

**Example**:
```
Source Entity (Salesforce):
  - Address: "123 main st berwyn pa"

After Address Standardization:
  - Address Line 1: "123 Main Street"
  - City: "Berwyn"
  - State: "PA"
  - Postal Code: "19312"
  - Country: "USA"
  - Latitude: 40.0451
  - Longitude: -75.4432
```

### Data Quality Rules

**Purpose**: Enforce data standards and validation.

**Business Rules**:
- **Required Fields**: Must be present from at least one source
- **Format Validation**: Email regex, phone patterns, date formats
- **Range Checks**: Numeric values within bounds (e.g., age 0-120)
- **Reference Integrity**: Foreign keys resolve to valid records
- **Custom Logic**: Groovy scripts for complex validation

**Example Rule**:
```
IF creditLimit > 100000 THEN creditCheckRequired = true
```

**Failure Handling**: Entity quarantined if validation fails.

## Source Links

**Purpose**: Track lineage between golden records and source entities.

**Link Attributes**:
- **source**: Source ID (e.g., "PROMOTION_ENGINE", "SALESFORCE")
- **entityId**: Source-specific entity identifier
- **establishedDate**: When link was created

**Query Response Example**:
```xml
<Record recordId="GR-ABC123" createdDate="2024-01-15T10:00:00Z" updatedDate="2024-02-20T14:30:00Z">
  <Fields>
    <contact>
      <name>Robert Smith</name>
      <email>robert.smith@company.com</email>
      <phone>555-1234</phone>
    </contact>
  </Fields>
  <links>
    <link source="SALESFORCE" entityId="SF-12345" establishedDate="2024-01-15T10:00:00Z"/>
    <link source="MYSQL" entityId="MYSQL-67890" establishedDate="2024-02-20T14:30:00Z"/>
  </links>
</Record>
```

**Use Cases**:
- **Lineage Tracking**: Identify which sources contributed to golden record
- **Source-Specific Queries**: Filter golden records by source link (e.g., "all customers from Salesforce")
- **Data Quality Investigation**: Trace incorrect field value back to source
- **Bi-Directional Sync**: Update source system when golden record changes (using source link to identify entity)

### Linking Behavior

**Automatic Linking**:
- First submission: No link → Apply match rules → Create golden record → Link source entity
- Subsequent submissions (same source entity ID): Existing link → Skip match rules → Update golden record

**Manual Linking**:
- Data steward resolves quarantine → Manually links quarantined entity to golden record

**Unlinking**:
- Not supported via API (requires manual intervention in UI)
- Use case: Incorrect match, need to separate entities

## Updating Golden Records

### When Source Entity Changes

**Process**:
1. Source system updates its record (e.g., Salesforce contact phone changed)
2. Inbound sync process queries changed records (filter by `LastModifiedDate`)
3. Submit batch to DataHub with source entity ID
4. DataHub finds existing link → Updates golden record
5. Field values re-merged based on source ranking
6. Other sources not affected (their links remain)

**Example**:
```xml
<!-- Salesforce entity SF-12345 phone updated -->
<batch src="SALESFORCE">
  <contact>
    <id>SF-12345</id>
    <name>Robert Smith</name>
    <phone>555-9999</phone> <!-- Changed -->
  </contact>
</batch>
```

**Result**: Golden record phone updated to "555-9999" (if Salesforce has priority over MySQL).

### When Golden Record Changes

**Process**:
1. Data steward edits golden record (or business rule updates it)
2. Outbound sync process queries changed golden records (filter by `updatedDate`)
3. For each linked source with **open channel**:
   - Transform golden record to source format
   - Update source system record via source connector
4. Source systems synchronized with golden record changes

**Channel Control**:
- **Open Channel**: Golden record changes flow to source (bi-directional sync)
- **Closed Channel**: No outbound sync to source (uni-directional sync)

**Example**:
```
Golden Record GR-ABC123 email updated to "robert.smith@newcompany.com"
    ↓
Outbound Sync Process
    ↓
Salesforce: Update SF-12345 email (channel open)
    ↓
MySQL: Update MYSQL-67890 email (channel open)
```

**Result**: Both source systems receive updated email from golden record.

## End-Dating Golden Records

**Purpose**: Mark golden record as inactive/deleted without removing data.

**Use Cases**:
- Customer account closure
- Employee termination
- Product discontinuation
- Maintain historical data while excluding from active queries

**End-Date Attributes**:
- **enddate**: Timestamp when record was end-dated (ISO 8601 format)
- **enddatesource**: Source that requested end-dating (or `*MDM*` for manual)

**End-Dated Record Example**:
```xml
<contact enddate="2019-09-24T15:34:07.000-0400"
         grid="GR-8219b49a"
         source="*MDM*">
  <id>GR-8219b49a</id>
  <name>pete</name>
  <email>pete@oldcompany.com</email>
</contact>
```

**Query Behavior**:
- **Default Queries**: Exclude end-dated records (only active golden records returned)
- **Include End-Dated**: Add filter to include end-dated records in results

**Reversing End-Date**:
- Submit update with `enddate` removed or set to null
- Golden record becomes active again

## Quarantine Handling

**Quarantine** is a holding area for entities that cannot be automatically processed.

### Quarantine Causes

| Cause | Description | Resolution |
|-------|-------------|------------|
| **TOO_MANY_MATCHES** | 10+ EXACT matches or 1,000+ fuzzy matches | Data steward selects correct golden record or creates new |
| **ALREADY_LINKED** | Duplicate source entity for same source | Verify duplicate submission, ignore or investigate source data |
| **MATCH_REFERENCE_FAILURE** | Reference field doesn't resolve to golden record | Fix reference or create missing referenced record |
| **Data Quality Failure** | Failed business rule or validation | Fix source data, adjust validation rules |
| **Validation Failure** | Missing required fields, type mismatch | Fix source data format |

### Quarantine Workflow

```
Source Entity Submitted
    ↓
Match Rules Applied
    ↓
Multiple Matches Found (TOO_MANY_MATCHES)
    ↓
Entity Quarantined
    ↓
Data Steward Notified (alert/queue)
    ↓
Data Steward Reviews:
  - View quarantined entity
  - View matching golden records
  - Review field values
    ↓
Resolution Options:
  1. Link to Existing Golden Record (manual match)
  2. Create New Golden Record (no match)
  3. Fix Data and Resubmit (source data issue)
  4. Mark as Duplicate/Ignore (invalid submission)
```

### Querying Quarantine

**API Endpoint**:
```
POST /mdm/universes/{universeID}/quarantine/query
```

**Request**:
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

**Response**:
```xml
<QuarantineEntry>
  <entity>
    <contact>
      <id>quarantine-001</id>
      <name>John Smith</name>
    </contact>
  </entity>
  <cause>TOO_MANY_MATCHES</cause>
  <matchingRecords>
    <contact recordId="GR-1">...</contact>
    <contact recordId="GR-2">...</contact>
    <!-- ... 15 total matches -->
  </matchingRecords>
  <resolution>UNRESOLVED</resolution>
</QuarantineEntry>
```

### Resolving Quarantine

**Manual Resolution (UI)**:
1. Navigate to Stewardship → Quarantine
2. Select repository/domain
3. Click quarantined entity
4. Review matching golden records
5. Choose resolution:
   - Link to existing golden record
   - Create new golden record
   - Edit data and resubmit
   - Ignore (mark as duplicate)

**Programmatic Resolution**:
- Use Repository API to update quarantine status
- Link entity to golden record via API
- Requires `MDM - Stewardship` privilege with `Match Quarantine` entitlement

## Project-Specific Golden Record Patterns

### ComponentMapping Golden Records

**Purpose**: One golden record per unique `(devComponentId, devAccountId)` pair.

**Source Links**:
- **PROMOTION_ENGINE**: Updated after each successful promotion
- **ADMIN_SEEDING**: Manually seeded for pre-configured connections

**Merging Logic**:
- No conflict resolution needed (single contributing source per golden record)
- PROMOTION_ENGINE updates version, timestamp after promotion
- ADMIN_SEEDING mappings never updated (static shared connection mappings)

**Example**:
```xml
<Record recordId="GR-COMP-123">
  <Fields>
    <ComponentMapping>
      <devComponentId>comp-123</devComponentId>
      <devAccountId>DEV_A</devAccountId>
      <prodComponentId>comp-prod-789</prodComponentId>
      <componentName>Order Processing Map</componentName>
      <prodLatestVersion>5</prodLatestVersion>
      <lastPromotedAt>2026-02-16T14:30:00.000Z</lastPromotedAt>
      <lastPromotedBy>alice@company.com</lastPromotedBy>
      <mappingSource>PROMOTION_ENGINE</mappingSource>
    </ComponentMapping>
  </Fields>
  <links>
    <link source="PROMOTION_ENGINE" entityId="comp-123-DEV_A" establishedDate="2024-01-15T10:00:00Z"/>
  </links>
</Record>
```

### DevAccountAccess Golden Records

**Purpose**: One golden record per unique `(ssoGroupId, devAccountId)` pair.

**Source Links**:
- **ADMIN_CONFIG**: Manually configured by admins

**Merging Logic**:
- Single source (no merging needed)
- ADMIN_CONFIG updates `isActive` to enable/disable access

**Example**:
```xml
<Record recordId="GR-ACCESS-123">
  <Fields>
    <DevAccountAccess>
      <ssoGroupId>aad-group-dev-team-a</ssoGroupId>
      <ssoGroupName>Dev Team A</ssoGroupName>
      <devAccountId>DEV_ACCT_TEAM_A</devAccountId>
      <devAccountName>Team A Development</devAccountName>
      <isActive>true</isActive>
    </DevAccountAccess>
  </Fields>
  <links>
    <link source="ADMIN_CONFIG" entityId="aad-group-dev-team-a-DEV_ACCT_TEAM_A" establishedDate="2024-01-01T00:00:00Z"/>
  </links>
</Record>
```

### PromotionLog Golden Records

**Purpose**: One golden record per unique `promotionId`.

**Source Links**:
- **PROMOTION_ENGINE**: Created by Process C, updated by Processes D, E3, admin review

**Merging Logic**:
- Single source (no merging needed)
- Multiple updates to same golden record as promotion progresses through lifecycle

**Lifecycle Updates**:
```
1. Process C Start:
   CREATE golden record (status=IN_PROGRESS)

2. Process C Complete:
   UPDATE golden record (status=COMPLETED, component counts)

3. Process E3 (Peer Review):
   UPDATE golden record (peerReviewStatus=PEER_APPROVED, reviewer, timestamp)

4. Admin Review:
   UPDATE golden record (adminReviewStatus=ADMIN_APPROVED)

5. Process D (Deploy):
   UPDATE golden record (integrationPackId, status=DEPLOYED)
```

**Example**:
```xml
<Record recordId="GR-PROMO-123" createdDate="2026-02-16T10:00:00Z" updatedDate="2026-02-16T14:00:00Z">
  <Fields>
    <PromotionLog>
      <promotionId>promo-uuid-12345</promotionId>
      <status>DEPLOYED</status>
      <componentsTotal>15</componentsTotal>
      <peerReviewStatus>PEER_APPROVED</peerReviewStatus>
      <peerReviewedBy>bob@company.com</peerReviewedBy>
      <adminReviewStatus>ADMIN_APPROVED</adminReviewStatus>
      <adminApprovedBy>admin@company.com</adminApprovedBy>
      <integrationPackId>ipack-789</integrationPackId>
    </PromotionLog>
  </Fields>
  <links>
    <link source="PROMOTION_ENGINE" entityId="promo-uuid-12345" establishedDate="2026-02-16T10:00:00Z"/>
  </links>
</Record>
```

## Best Practices

### Source Management

**1. Contribute-Only Sources**:
- Use for one-way data flow (e.g., promotion engine writes, never reads back)
- Prevents unintended outbound sync from golden records to Integration processes

**2. Source Ranking**:
- Rank by data authority (ERP > CRM > Marketing)
- Document ranking rationale
- Review ranking when adding new sources

**3. Source Entity IDs**:
- Use stable, unique identifiers (UUIDs, primary keys)
- Avoid volatile identifiers (row numbers, timestamps)

### Golden Record Quality

**1. Match Rule Design**:
- Order from most restrictive to least restrictive
- Test with production-like data before deployment
- Monitor quarantine volume, adjust rules as needed

**2. Data Quality Steps**:
- Implement validation at source boundaries
- Use third-party enrichment (Loqate, geocoding)
- Standardize formats (phone, address, email)

**3. Quarantine Management**:
- Assign data stewards to review quarantine daily
- Set up alerts for quarantine threshold breaches
- Tune match rules to reduce false positives

### Performance

**1. Indexing**:
- Match fields automatically indexed (fast lookups)
- Query frequently filtered fields benefit from indexes

**2. Pagination**:
- Use limit/offset for large query results (1,000+ records)
- Avoid retrieving all golden records in single request

**3. Accelerated Query**:
- Enable for models with 100,000+ golden records
- Significant performance improvement for large datasets

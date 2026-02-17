# Match Rules

## Overview

**Match Rules** are the core logic that determines when to **CREATE** a new golden record vs. **UPDATE** an existing one. They implement UPSERT behavior in DataHub.

**Key Concept**: Match rules only apply when incoming source entity has NO existing link to a golden record.

## Match Rule Execution Flow

```
Incoming Source Entity
    ↓
Check for existing link to golden record
    ↓
┌──────────────────────────────────────────┐
│ Link exists?                             │
│   YES → UPDATE linked golden record      │
│   NO  → Apply match rules                │
└──────────────────────────────────────────┘
    ↓ (if no link)
Apply match rules sequentially
    ↓
┌──────────────────────────────────────────┐
│ No match → CREATE new golden record      │
│ 1 match → UPDATE + link to golden record │
│ 10+ matches → QUARANTINE (TOO_MANY)      │
│ Already linked → Skip (ALREADY_LINKED)   │
└──────────────────────────────────────────┘
```

**Important**: Once a source entity is linked to a golden record, match rules are bypassed on subsequent updates. The link provides direct update path.

## Match Rule Types

### 1. EXACT Match

**Definition**: All specified fields must exactly match between incoming entity and golden record.

**Match Logic**: Case-sensitive, character-for-character comparison.

**Single Field Example**:
```json
{
  "type": "EXACT",
  "description": "Match on promotion ID (each promotion run is unique)",
  "fields": ["promotionId"]
}
```

**Behavior**:
- Incoming `promotionId: "promo-123"` matches existing golden record with `promotionId: "promo-123"`
- No match if values differ (even whitespace differences)

**Compound Key (Multi-Field) Example**:
```json
{
  "type": "EXACT",
  "description": "Compound match on dev component ID and dev account ID",
  "fields": ["devComponentId", "devAccountId"]
}
```

**Behavior**:
- Incoming entity must match ALL specified fields to be considered a match
- `devComponentId: "comp-123"` + `devAccountId: "DEV_A"` only matches golden record with both values
- Prevents collisions when two dev accounts use same component ID

**Use Cases**:
- Unique identifiers (UUIDs, account numbers, promotion IDs)
- Compound keys (multi-field uniqueness)
- High-confidence matching (no ambiguity)

### 2. Fuzzy Match

**Definition**: Uses similarity algorithms to match on approximate field values.

**Supported Algorithms**:

| Algorithm | Description | Best For |
|-----------|-------------|----------|
| **Jaro-Winkler** | String similarity with prefix bonus | Names with typos (Robert vs. Bob) |
| **Levenshtein** | Edit distance (insertions/deletions) | Misspellings |
| **Bigram/Trigram** | N-gram similarity | Partial matches |
| **Soundex** | Phonetic matching | Similar-sounding names (Smith vs. Smyth) |

**Example Configuration**:
```
"Incoming name is similar to (Jaro-Winkler) Existing name"
```

**Similarity Threshold**:
- Configurable threshold (e.g., 80% similarity required)
- Lower threshold = more matches (more false positives)
- Higher threshold = fewer matches (more false negatives)

**Response Includes Scores**:
```xml
<fuzzyMatchDetails>
  <field>name</field>
  <first>BOBBY</first>
  <second>BOB</second>
  <method>jarowinkler</method>
  <score>0.92</score>
</fuzzyMatchDetails>
```

**Use Cases**:
- Customer name deduplication
- Product name matching
- Address standardization
- Data with known quality issues (typos, abbreviations)

**Performance Note**: Fuzzy matching is computationally expensive. Use EXACT rules first when possible.

## Match Rule Ordering

**CRITICAL**: Match rules are applied sequentially. First match wins.

**Correct Ordering (Most Restrictive → Least Restrictive)**:

```json
{
  "matchRules": [
    {
      "type": "EXACT",
      "description": "Strictest: exact match on lastName + firstName + DOB",
      "fields": ["lastName", "firstName", "dateOfBirth"]
    },
    {
      "type": "EXACT",
      "description": "Medium: exact match on email",
      "fields": ["email"]
    },
    {
      "type": "FUZZY",
      "description": "Least strict: fuzzy match on lastName",
      "algorithm": "Jaro-Winkler",
      "threshold": 0.85,
      "fields": ["lastName"]
    }
  ]
}
```

**Why This Ordering Matters**:

Incoming entity: `lastName: Smith, firstName: John, dateOfBirth: 1990-01-01, email: john.smith@email.com`

Existing golden records:
- GR-1: `Smith, John, 1990-01-01, john.smith@email.com` (exact match on all fields)
- GR-2: `Smith, John, 1985-05-15, john.smyth@email.com` (matches on name only)
- GR-3: `Smyth, Jane, 1992-03-20, jane@email.com` (fuzzy match on last name)

**Execution**:
1. Rule 1 (EXACT on lastName + firstName + DOB): Matches GR-1 → **STOP, use GR-1**
2. Rule 2 and 3 never evaluated

**Incorrect Ordering (Least Restrictive First)**:

```json
{
  "matchRules": [
    {
      "type": "FUZZY",
      "description": "Fuzzy match on lastName",
      "fields": ["lastName"]
    },
    {
      "type": "EXACT",
      "description": "Exact match on email",
      "fields": ["email"]
    }
  ]
}
```

**Problem**:
1. Rule 1 (FUZZY on lastName): Matches GR-1, GR-2, GR-3 → Multiple matches → **QUARANTINE**
2. Rule 2 (EXACT on email) never evaluated, even though it would uniquely identify GR-1

**Best Practice**: Always order from most specific to least specific.

## UPSERT Behavior

Match rules enable UPSERT (Update or Insert) logic.

### Scenario 1: No Match Found

**Incoming Entity**:
```xml
<ComponentMapping>
  <id>src-entity-001</id>
  <devComponentId>comp-999</devComponentId>
  <devAccountId>DEV_NEW</devAccountId>
  <prodComponentId>comp-prod-999</prodComponentId>
</ComponentMapping>
```

**Existing Golden Records**: None matching `(comp-999, DEV_NEW)`

**Match Rule Applied**: EXACT on `devComponentId + devAccountId`

**Result**:
- **CREATE** new golden record GR-NEW
- Link source entity `src-entity-001` to GR-NEW
- Source link: `<link source="PROMOTION_ENGINE" entityId="src-entity-001"/>`

### Scenario 2: Exact Match Found (Not Yet Linked)

**Incoming Entity**:
```xml
<ComponentMapping>
  <id>src-entity-002</id>
  <devComponentId>comp-123</devComponentId>
  <devAccountId>DEV_A</devAccountId>
  <prodComponentId>comp-prod-789</prodComponentId>
  <prodLatestVersion>5</prodLatestVersion>
</ComponentMapping>
```

**Existing Golden Record** GR-123:
```xml
<ComponentMapping recordId="GR-123">
  <devComponentId>comp-123</devComponentId>
  <devAccountId>DEV_A</devAccountId>
  <prodComponentId>comp-prod-456</prodComponentId>
  <prodLatestVersion>3</prodLatestVersion>
</ComponentMapping>
```

**Match Rule Applied**: EXACT on `devComponentId + devAccountId`

**Result**:
- **UPDATE** GR-123 with new field values (version 5, new prod ID)
- Link source entity `src-entity-002` to GR-123
- Field merging based on source ranking

### Scenario 3: Exact Match Found (Already Linked)

**Incoming Entity**: Same as scenario 2, but source entity `src-entity-002` already linked to GR-123

**Result**:
- **Match Status**: `ALREADY_LINKED`
- No action taken (prevents duplicate links)
- Typically indicates duplicate data submission

### Scenario 4: Multiple Matches Found

**Incoming Entity**:
```xml
<Contact>
  <id>src-entity-003</id>
  <lastName>Smith</lastName>
</Contact>
```

**Existing Golden Records**:
- GR-1: `Smith, John, john@email.com`
- GR-2: `Smith, Jane, jane@email.com`
- GR-3: `Smith, Bob, bob@email.com`
- ... (15 total Smiths)

**Match Rule Applied**: EXACT on `lastName`

**Result**:
- **Match Status**: `TOO_MANY_MATCHES`
- Entity quarantined for manual stewardship
- Data steward reviews and selects correct golden record or creates new one

**Threshold**: 10+ matches for EXACT rules, 1,000+ for fuzzy rules

## Match Result Statuses

| Status | Meaning | Action Taken |
|--------|---------|--------------|
| **SUCCESS** | Request processed successfully | Golden record created or updated |
| **FAILED_TO_RUN** | Internal error occurred | Entity rejected, check logs |
| **TOO_MANY_MATCHES** | 10+ matching golden records (1,000+ for fuzzy) | Entity quarantined |
| **ALREADY_LINKED** | Entity already linked to golden record | No action (duplicate submission) |
| **MATCH_REFERENCE_FAILURE** | Reference field value doesn't resolve | Entity quarantined |

## Compound Match Keys

**Purpose**: Prevent collisions when single field is not unique across contexts.

**Example Problem**:

Two dev accounts use same component ID:
- Dev Team A: `devComponentId: "comp-123"` (Order Processing Map)
- Dev Team B: `devComponentId: "comp-123"` (Inventory Map)

**Single Key Match Rule** (WRONG):
```json
{
  "type": "EXACT",
  "fields": ["devComponentId"]
}
```

**Problem**: Both dev accounts match same golden record → Incorrect mapping

**Compound Key Match Rule** (CORRECT):
```json
{
  "type": "EXACT",
  "fields": ["devComponentId", "devAccountId"]
}
```

**Result**: Each `(devComponentId, devAccountId)` pair is unique → Separate golden records per dev account

**Best Practice**: Use compound keys when single field is not globally unique.

## Testing Match Rules

### Match Entities Operation

**Purpose**: Test match rules without committing data to golden records.

**API Endpoint**:
```
POST https://<hub-cloud-host>/mdm/universes/{universeID}/match
```

**Request Example**:
```xml
<batch src="TEST_SOURCE">
  <ComponentMapping>
    <id>test-001</id>
    <devComponentId>comp-123</devComponentId>
    <devAccountId>DEV_A</devAccountId>
  </ComponentMapping>
</batch>
```

**Response Example**:
```xml
<MatchEntitiesResponse>
  <MatchResult matchRule="Compound match on dev component ID and dev account ID" status="SUCCESS">
    <entity>
      <ComponentMapping>
        <id>test-001</id>
        <devComponentId>comp-123</devComponentId>
        <devAccountId>DEV_A</devAccountId>
      </ComponentMapping>
    </entity>
    <match>
      <ComponentMapping recordId="GR-123">
        <devComponentId>comp-123</devComponentId>
        <devAccountId>DEV_A</devAccountId>
        <prodComponentId>comp-prod-789</prodComponentId>
      </ComponentMapping>
    </match>
    <duplicate>
      <!-- Golden records already linked to this source -->
    </duplicate>
  </MatchResult>
</MatchEntitiesResponse>
```

**Use Cases**:
- Validate match rule configuration before production
- Identify potential duplicates in incoming batch
- Troubleshoot quarantine issues
- Test fuzzy matching thresholds

### Staging Areas

**Purpose**: Preview batch processing without committing to golden records.

**Create Staging Area**:
1. Repository → Domain → Sources tab
2. Select source gear icon → Add a Staging Area
3. Provide name and ID

**Stage Batch**:
```
POST /mdm/universes/{universeID}/staging/{stagingAreaID}
```

**Staging Process**:
- Applies match rules
- Applies data quality steps
- Does NOT create/update golden records
- Does NOT quarantine entities
- Returns match results and validation outcomes

**Review Staged Entities**:
1. Navigate to Stewardship → Staged Entities
2. Select staging area
3. Review entities, match results, potential duplicates
4. Commit (incorporate into domain) or Delete (discard)

## Best Practices

### Match Rule Design

**1. Start with Most Restrictive Rules**:
- Order: Strictest → Medium → Least Strict
- First match wins, so prioritize high-confidence matches

**2. Use Compound Keys for Context**:
- Single field often insufficient (e.g., `componentId` not unique across accounts)
- Compound keys prevent collisions: `(devComponentId, devAccountId)`

**3. Avoid Overly Strict Rules**:
- Too many match rules = Too many quarantine entries
- Balance precision vs. stewardship burden

**4. Test Before Deployment**:
- Use Match Entities operation
- Stage batches to preview behavior
- Validate with production-like data

**5. Document Match Logic**:
- Use descriptive `description` field
- Explain why each rule exists
- Include examples in documentation

### Quarantine Reduction

**Problem**: High quarantine volume overwhelms data stewards.

**Solutions**:
1. **Adjust thresholds**: Lower fuzzy match threshold (more lenient)
2. **Reorder rules**: Ensure strictest rules evaluated first
3. **Add intermediate rules**: Fill gap between strict and lenient rules
4. **Improve source data quality**: Clean data before submission
5. **Use staging**: Test rules before production

### Performance Optimization

**1. EXACT Rules First**:
- EXACT matching is fast (indexed lookups)
- Fuzzy matching is slow (algorithm computation)

**2. Limit Fuzzy Rules**:
- Use fuzzy only when necessary
- Consider pre-processing data (standardize names, addresses)

**3. Index Match Fields**:
- Match fields automatically indexed
- Queries on match fields are optimized

## Project-Specific Match Rules

### ComponentMapping

**Match Rule**: Compound EXACT on `(devComponentId, devAccountId)`

**Rationale**: Dev component IDs are not globally unique. Same ID can exist in multiple dev accounts for different components. Compound key ensures accurate mapping.

**Example**:
```json
{
  "type": "EXACT",
  "description": "Compound match on dev component ID and dev account ID",
  "fields": ["devComponentId", "devAccountId"]
}
```

### DevAccountAccess

**Match Rule**: Compound EXACT on `(ssoGroupId, devAccountId)`

**Rationale**: One SSO group can access multiple dev accounts. One dev account can be accessed by multiple SSO groups. Compound key represents unique access grant.

**Example**:
```json
{
  "type": "EXACT",
  "description": "Compound match on SSO group ID and dev account ID",
  "fields": ["ssoGroupId", "devAccountId"]
}
```

### PromotionLog

**Match Rule**: Single EXACT on `promotionId`

**Rationale**: Each promotion run has globally unique UUID. Single key sufficient.

**Example**:
```json
{
  "type": "EXACT",
  "description": "Match on promotion ID (each promotion run is unique)",
  "fields": ["promotionId"]
}
```

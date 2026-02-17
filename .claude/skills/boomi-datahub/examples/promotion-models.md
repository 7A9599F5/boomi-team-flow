# Promotion System DataHub Models

This file documents the three DataHub models used in the Boomi Dev-to-Prod Component Promotion System, with practical examples and usage patterns.

## Overview

| Model | Root Element | Purpose | Match Key |
|-------|--------------|---------|-----------|
| **ComponentMapping** | `ComponentMapping` | Map dev component IDs → prod component IDs | `(devComponentId, devAccountId)` |
| **DevAccountAccess** | `DevAccountAccess` | Control SSO group access to dev accounts | `(ssoGroupId, devAccountId)` |
| **PromotionLog** | `PromotionLog` | Audit trail with 2-layer approval workflow | `promotionId` |

## 1. ComponentMapping Model

### Model Specification

**File**: `/home/glitch/code/boomi_team_flow/datahub/models/ComponentMapping-model-spec.json`

**Fields**:

| Field | Type | Required | Match Field | Description |
|-------|------|----------|-------------|-------------|
| `id` | String | No | No | Auto-generated DataHub record ID |
| `devComponentId` | String | Yes | **Yes** | Component ID in dev sub-account (Boomi UUID) |
| `devAccountId` | String | Yes | **Yes** | Dev sub-account ID |
| `prodComponentId` | String | Yes | No | Component ID in production account |
| `componentName` | String | Yes | No | Human-readable component name |
| `componentType` | String | Yes | No | Boomi type: process, connection, map, profile.xml, etc. |
| `prodAccountId` | String | Yes | No | Primary production account ID |
| `prodLatestVersion` | Number | Yes | No | Latest version number in production |
| `lastPromotedAt` | Date | Yes | No | Timestamp of last promotion (ISO 8601) |
| `lastPromotedBy` | String | Yes | No | SSO user email who triggered promotion |
| `mappingSource` | String | No | No | PROMOTION_ENGINE or ADMIN_SEEDING |

**Match Rule**:
```json
{
  "type": "EXACT",
  "description": "Compound match on dev component ID and dev account ID",
  "fields": ["devComponentId", "devAccountId"]
}
```

**Rationale**: Dev component IDs are not globally unique. Same ID can exist in multiple dev accounts for different components. Compound key ensures accurate mapping per dev account.

### Sources

**1. PROMOTION_ENGINE** (contribute-only):
- Written by Process C/D after successful promotion
- Updates mapping with new version, timestamp, user
- UPSERT behavior: First promotion creates mapping, subsequent promotions update it

**2. ADMIN_SEEDING** (contribute-only):
- Manually seeded by admins for pre-configured connection mappings
- Links dev connection IDs to parent account shared connections (in `#Connections` folder)
- Static mappings, never updated by promotion engine

### Example Records

#### Promoted Component Mapping

```xml
<batch src="PROMOTION_ENGINE">
  <ComponentMapping>
    <id>comp-123-DEV_A</id>
    <devComponentId>dev-comp-abc123</devComponentId>
    <devAccountId>DEV_TEAM_A</devAccountId>
    <prodComponentId>prod-comp-xyz789</prodComponentId>
    <componentName>Order Processing Map</componentName>
    <componentType>map</componentType>
    <prodAccountId>PRIMARY_ACCT</prodAccountId>
    <prodLatestVersion>3</prodLatestVersion>
    <lastPromotedAt>2026-02-16T14:30:00.000Z</lastPromotedAt>
    <lastPromotedBy>alice@company.com</lastPromotedBy>
    <mappingSource>PROMOTION_ENGINE</mappingSource>
  </ComponentMapping>
</batch>
```

**UPSERT Behavior**:
- **1st Promotion**: No match on `(dev-comp-abc123, DEV_TEAM_A)` → CREATE golden record
- **2nd Promotion**: Match found → UPDATE with version 4, new timestamp

#### Admin-Seeded Connection Mapping

```xml
<batch src="ADMIN_SEEDING">
  <ComponentMapping>
    <id>conn-shared-salesforce-DEV_A</id>
    <devComponentId>conn-dev-salesforce-123</devComponentId>
    <devAccountId>DEV_TEAM_A</devAccountId>
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

**Purpose**: Pre-configure mapping so Process C can rewrite connection references to shared parent account connection.

### Process Integration

#### Process B: Query for Reference Rewriting

**Operation**: Query Golden Records

**Request**:
```xml
<RecordQueryRequest limit="1000">
  <view>
    <fieldId>devComponentId</fieldId>
    <fieldId>prodComponentId</fieldId>
    <fieldId>componentType</fieldId>
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

**Output**: Mapping cache loaded into DPP for Groovy script `rewrite-references.groovy`.

**Cache Structure** (JSON):
```json
{
  "dev-comp-abc123": "prod-comp-xyz789",
  "dev-proc-456": "prod-proc-012",
  "conn-dev-salesforce-123": "conn-shared-salesforce"
}
```

#### Process C: Validate Connection Mappings

**Groovy Script**: `validate-connection-mappings.groovy`

**Logic**:
1. Extract all connection IDs from dependency tree
2. Query ComponentMapping for each connection ID
3. If ANY mapping missing → Fail with `MISSING_CONNECTION_MAPPINGS` error

**Query Example** (per connection):
```xml
<RecordQueryRequest limit="1">
  <view>
    <fieldId>prodComponentId</fieldId>
  </view>
  <filter op="AND">
    <fieldValue>
      <fieldId>devComponentId</fieldId>
      <operator>EQUALS</operator>
      <value>${connectionId}</value>
    </fieldValue>
    <fieldValue>
      <fieldId>devAccountId</fieldId>
      <operator>EQUALS</operator>
      <value>${devAccountId}</value>
    </fieldValue>
  </filter>
</RecordQueryRequest>
```

**Validation Failure Response**:
```json
{
  "success": false,
  "errorCode": "MISSING_CONNECTION_MAPPINGS",
  "errorMessage": "Connection mappings missing for: conn-dev-mysql-789, conn-dev-http-012",
  "missingConnections": ["conn-dev-mysql-789", "conn-dev-http-012"]
}
```

#### Process D: Update Mapping After Deployment

**Operation**: Update/Upsert Golden Records

**Request** (after successful merge to main):
```xml
<batch src="PROMOTION_ENGINE">
  <ComponentMapping>
    <id>comp-123-DEV_A</id>
    <devComponentId>dev-comp-abc123</devComponentId>
    <devAccountId>DEV_TEAM_A</devAccountId>
    <prodComponentId>prod-comp-xyz789</prodComponentId>
    <componentName>Order Processing Map</componentName>
    <componentType>map</componentType>
    <prodAccountId>PRIMARY_ACCT</prodAccountId>
    <prodLatestVersion>4</prodLatestVersion> <!-- Incremented -->
    <lastPromotedAt>2026-02-16T15:00:00.000Z</lastPromotedAt> <!-- Updated -->
    <lastPromotedBy>alice@company.com</lastPromotedBy>
    <mappingSource>PROMOTION_ENGINE</mappingSource>
  </ComponentMapping>
</batch>
```

**UPSERT Behavior**: Match on `(dev-comp-abc123, DEV_TEAM_A)` → UPDATE existing golden record with new version.

---

## 2. DevAccountAccess Model

### Model Specification

**File**: `/home/glitch/code/boomi_team_flow/datahub/models/DevAccountAccess-model-spec.json`

**Fields**:

| Field | Type | Required | Match Field | Description |
|-------|------|----------|-------------|-------------|
| `ssoGroupId` | String | Yes | **Yes** | Azure AD group object ID |
| `ssoGroupName` | String | Yes | No | Human-readable group display name |
| `devAccountId` | String | Yes | **Yes** | Boomi dev sub-account ID |
| `devAccountName` | String | Yes | No | Human-readable dev account name |
| `isActive` | String | Yes | No | "true" or "false" (enable/disable access) |

**Match Rule**:
```json
{
  "type": "EXACT",
  "description": "Compound match on SSO group ID and dev account ID",
  "fields": ["ssoGroupId", "devAccountId"]
}
```

**Rationale**: One SSO group can access multiple dev accounts. One dev account can be accessed by multiple SSO groups. Compound key represents unique access grant.

### Sources

**ADMIN_CONFIG** (contribute-only):
- Manually seeded by admins via DataHub API or UI
- Updated to enable/disable access (`isActive` toggling)

### Example Records

#### Grant Access to Single Dev Account

```xml
<batch src="ADMIN_CONFIG">
  <DevAccountAccess>
    <ssoGroupId>aad-group-dev-team-a</ssoGroupId>
    <ssoGroupName>Dev Team A</ssoGroupName>
    <devAccountId>DEV_ACCT_TEAM_A</devAccountId>
    <devAccountName>Team A Development</devAccountName>
    <isActive>true</isActive>
  </DevAccountAccess>
</batch>
```

#### Grant Admin Access to Multiple Dev Accounts

```xml
<batch src="ADMIN_CONFIG">
  <DevAccountAccess>
    <ssoGroupId>aad-group-admins</ssoGroupId>
    <ssoGroupName>Platform Admins</ssoGroupName>
    <devAccountId>DEV_ACCT_TEAM_A</devAccountId>
    <devAccountName>Team A Development</devAccountName>
    <isActive>true</isActive>
  </DevAccountAccess>
  <DevAccountAccess>
    <ssoGroupId>aad-group-admins</ssoGroupId>
    <ssoGroupName>Platform Admins</ssoGroupName>
    <devAccountId>DEV_ACCT_TEAM_B</devAccountId>
    <devAccountName>Team B Development</devAccountName>
    <isActive>true</isActive>
  </DevAccountAccess>
</batch>
```

**Result**: Platform Admins group can access both Team A and Team B dev accounts.

#### Revoke Access

```xml
<batch src="ADMIN_CONFIG">
  <DevAccountAccess>
    <ssoGroupId>aad-group-dev-team-a</ssoGroupId>
    <ssoGroupName>Dev Team A</ssoGroupName>
    <devAccountId>DEV_ACCT_TEAM_A</devAccountId>
    <devAccountName>Team A Development</devAccountName>
    <isActive>false</isActive> <!-- Revoked -->
  </DevAccountAccess>
</batch>
```

**UPSERT Behavior**: Match on `(aad-group-dev-team-a, DEV_ACCT_TEAM_A)` → UPDATE `isActive` to "false".

### Process Integration

#### Process A0: Authorize User

**Operation**: Query Golden Records

**Purpose**: Determine which dev accounts user can access based on SSO group membership.

**Request**:
```xml
<RecordQueryRequest limit="100">
  <view>
    <fieldId>devAccountId</fieldId>
    <fieldId>devAccountName</fieldId>
  </view>
  <filter op="AND">
    <filter op="OR">
      <fieldValue>
        <fieldId>ssoGroupId</fieldId>
        <operator>EQUALS</operator>
        <value>${userGroup1}</value>
      </fieldValue>
      <fieldValue>
        <fieldId>ssoGroupId</fieldId>
        <operator>EQUALS</operator>
        <value>${userGroup2}</value>
      </fieldValue>
      <!-- ... for each user SSO group -->
    </filter>
    <fieldValue>
      <fieldId>isActive</fieldId>
      <operator>EQUALS</operator>
      <value>true</value>
    </fieldValue>
  </filter>
</RecordQueryRequest>
```

**Output** (JSON array):
```json
[
  {"devAccountId": "DEV_ACCT_TEAM_A", "devAccountName": "Team A Development"},
  {"devAccountId": "DEV_ACCT_TEAM_B", "devAccountName": "Team B Development"}
]
```

**Authorization Logic**:
- User in `aad-group-dev-team-a` → Can access `DEV_ACCT_TEAM_A`
- User in `aad-group-admins` → Can access ALL dev accounts with active mappings
- User not in any mapped group → Access denied, return empty list

---

## 3. PromotionLog Model

### Model Specification

**File**: `/home/glitch/code/boomi_team_flow/datahub/models/PromotionLog-model-spec.json`

**Fields**:

| Field | Type | Required | Match Field | Description |
|-------|------|----------|-------------|-------------|
| `promotionId` | String | Yes | **Yes** | UUID uniquely identifying this promotion |
| `devAccountId` | String | Yes | No | Source dev sub-account ID |
| `prodAccountId` | String | Yes | No | Target production account ID |
| `devPackageId` | String | Yes | No | PackagedComponent ID from dev account |
| `prodPackageId` | String | No | No | PackagedComponent ID created in production |
| `initiatedBy` | String | Yes | No | SSO user email who started promotion |
| `initiatedAt` | Date | Yes | No | Timestamp when promotion started |
| `status` | String | Yes | No | Lifecycle status |
| `componentsTotal` | Number | Yes | No | Total components in dependency tree |
| `componentsCreated` | Number | Yes | No | New components created in production |
| `componentsUpdated` | Number | Yes | No | Existing components updated |
| `componentsFailed` | Number | Yes | No | Components that failed to promote |
| `errorMessage` | String | No | No | Error details if failed (max 5000 chars) |
| `resultDetail` | String | No | No | JSON with per-component results (max 5000 chars) |
| `peerReviewStatus` | String | No | No | PENDING_PEER_REVIEW, PEER_APPROVED, PEER_REJECTED |
| `peerReviewedBy` | String | No | No | Email of peer reviewer |
| `peerReviewedAt` | Date | No | No | Timestamp of peer review action |
| `peerReviewComments` | String | No | No | Peer reviewer comments (max 500 chars) |
| `adminReviewStatus` | String | No | No | PENDING_ADMIN_REVIEW, ADMIN_APPROVED, ADMIN_REJECTED |
| `adminApprovedBy` | String | No | No | Email of admin approver |
| `adminApprovedAt` | Date | No | No | Timestamp of admin review action |
| `adminComments` | String | No | No | Admin comments (max 500 chars) |
| `branchId` | String | No | No | Promotion branch ID (set on creation, cleared after cleanup) |
| `branchName` | String | No | No | Promotion branch name (e.g., `promo-{promotionId}`) |
| `integrationPackId` | String | No | No | Integration Pack ID (populated after deploy) |
| `integrationPackName` | String | No | No | Integration Pack name |
| `processName` | String | No | No | Root process name (for Integration Pack suggestions) |

**Status Lifecycle**:
```
IN_PROGRESS → COMPLETED → PENDING_PEER_REVIEW
                            ↓
                      PEER_APPROVED → PENDING_ADMIN_REVIEW
                            ↓                  ↓
                      PEER_REJECTED    ADMIN_APPROVED → DEPLOYED
                                               ↓
                                       ADMIN_REJECTED
```

**Match Rule**:
```json
{
  "type": "EXACT",
  "description": "Match on promotion ID (each promotion run is unique)",
  "fields": ["promotionId"]
}
```

**Rationale**: Each promotion run has globally unique UUID. Single key sufficient.

### Sources

**PROMOTION_ENGINE** (contribute-only):
- Written by Processes C, D, E3, and admin review workflow
- Multiple updates to same golden record as promotion progresses

### Example Records

#### Process C Start (IN_PROGRESS)

```xml
<batch src="PROMOTION_ENGINE">
  <PromotionLog>
    <promotionId>promo-uuid-12345</promotionId>
    <devAccountId>DEV_TEAM_A</devAccountId>
    <prodAccountId>PRIMARY_ACCT</prodAccountId>
    <devPackageId>dev-pkg-abc</devPackageId>
    <initiatedBy>alice@company.com</initiatedBy>
    <initiatedAt>2026-02-16T10:00:00.000Z</initiatedAt>
    <status>IN_PROGRESS</status>
    <componentsTotal>0</componentsTotal>
    <componentsCreated>0</componentsCreated>
    <componentsUpdated>0</componentsUpdated>
    <componentsFailed>0</componentsFailed>
    <branchId>branch-promo-12345</branchId>
    <branchName>promo-promo-uuid-12345</branchName>
  </PromotionLog>
</batch>
```

**UPSERT**: No match on `promo-uuid-12345` → CREATE golden record.

#### Process C Complete (COMPLETED)

```xml
<batch src="PROMOTION_ENGINE">
  <PromotionLog>
    <promotionId>promo-uuid-12345</promotionId>
    <devAccountId>DEV_TEAM_A</devAccountId>
    <prodAccountId>PRIMARY_ACCT</prodAccountId>
    <devPackageId>dev-pkg-abc</devPackageId>
    <prodPackageId>prod-pkg-xyz</prodPackageId>
    <initiatedBy>alice@company.com</initiatedBy>
    <initiatedAt>2026-02-16T10:00:00.000Z</initiatedAt>
    <status>COMPLETED</status>
    <componentsTotal>15</componentsTotal>
    <componentsCreated>3</componentsCreated>
    <componentsUpdated>12</componentsUpdated>
    <componentsFailed>0</componentsFailed>
    <resultDetail>{"components":[...]}</resultDetail>
    <branchId>branch-promo-12345</branchId>
    <branchName>promo-promo-uuid-12345</branchName>
    <processName>Order Processing Workflow</processName>
  </PromotionLog>
</batch>
```

**UPSERT**: Match on `promo-uuid-12345` → UPDATE with component counts, result detail.

#### Process E3: Peer Review Approval

```xml
<batch src="PROMOTION_ENGINE">
  <PromotionLog>
    <promotionId>promo-uuid-12345</promotionId>
    <status>PEER_APPROVED</status>
    <peerReviewStatus>PEER_APPROVED</peerReviewStatus>
    <peerReviewedBy>bob@company.com</peerReviewedBy>
    <peerReviewedAt>2026-02-16T11:30:00.000Z</peerReviewedAt>
    <peerReviewComments>Looks good, process logic verified</peerReviewComments>
  </PromotionLog>
</batch>
```

**UPSERT**: Match on `promo-uuid-12345` → UPDATE with peer review details.

**Self-Review Prevention**:
- Backend validation: Reject if `peerReviewedBy == initiatedBy`
- UI filter: Exclude own promotions from peer review queue

#### Admin Approval

```xml
<batch src="PROMOTION_ENGINE">
  <PromotionLog>
    <promotionId>promo-uuid-12345</promotionId>
    <status>ADMIN_APPROVED</status>
    <adminReviewStatus>ADMIN_APPROVED</adminReviewStatus>
    <adminApprovedBy>admin@company.com</adminApprovedBy>
    <adminApprovedAt>2026-02-16T13:00:00.000Z</adminApprovedAt>
    <adminComments>Approved for deployment</adminComments>
  </PromotionLog>
</batch>
```

#### Process D: Deployment Complete

```xml
<batch src="PROMOTION_ENGINE">
  <PromotionLog>
    <promotionId>promo-uuid-12345</promotionId>
    <status>DEPLOYED</status>
    <integrationPackId>ipack-789</integrationPackId>
    <integrationPackName>Order Processing Workflow v5</integrationPackName>
    <branchId></branchId> <!-- Cleared after merge/delete -->
  </PromotionLog>
</batch>
```

**UPSERT**: Match on `promo-uuid-12345` → UPDATE with Integration Pack details, clear branch ID.

### Process Integration

#### Process E: Query Status

**Operation**: Query Golden Records

**Request** (user's own promotions):
```xml
<RecordQueryRequest limit="200">
  <view>
    <fieldId>promotionId</fieldId>
    <fieldId>status</fieldId>
    <fieldId>componentsTotal</fieldId>
    <fieldId>initiatedAt</fieldId>
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

#### Process E2: Query Peer Review Queue

**Operation**: Query Golden Records

**Request** (exclude own promotions):
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
    <order>ASC</order>
  </sort>
</RecordQueryRequest>
```

**Self-Review Prevention**: `initiatedBy NOT_EQUALS currentUserEmail` ensures user cannot peer-review own promotions.

#### Process J: Smart Integration Pack Suggestions

**Operation**: Query Golden Records

**Request** (promotions with same process name):
```xml
<RecordQueryRequest limit="10">
  <view>
    <fieldId>integrationPackName</fieldId>
    <fieldId>integrationPackId</fieldId>
  </view>
  <filter op="AND">
    <fieldValue>
      <fieldId>processName</fieldId>
      <operator>EQUALS</operator>
      <value>${rootProcessName}</value>
    </fieldValue>
    <fieldValue>
      <fieldId>status</fieldId>
      <operator>EQUALS</operator>
      <value>DEPLOYED</value>
    </fieldValue>
  </filter>
  <sort>
    <fieldId>initiatedAt</fieldId>
    <order>DESC</order>
  </sort>
</RecordQueryRequest>
```

**Purpose**: Suggest Integration Pack name/ID based on previous promotions of same process.

---

## Best Practices

### Compound Match Keys

**Always use compound keys when single field is not globally unique**:
- ComponentMapping: `(devComponentId, devAccountId)` prevents collision across dev accounts
- DevAccountAccess: `(ssoGroupId, devAccountId)` represents unique access grant

### String Type for Booleans

**Use "true"/"false" strings instead of Boolean type**:
- More flexible for API compatibility
- Consistent with Flow Service JSON handling
- Example: `isActive` field in DevAccountAccess

### Long Text for JSON

**Use Long Text (max 5,000 chars) for JSON payloads**:
- `resultDetail` field stores per-component promotion results as JSON string
- Truncate if exceeds 5,000 chars (rare, but handle gracefully)

### Source Naming Conventions

**Use descriptive, uppercase source IDs**:
- `PROMOTION_ENGINE`: Identifies automated promotion system
- `ADMIN_SEEDING`: Identifies manual admin configuration
- `ADMIN_CONFIG`: Identifies admin access control configuration

### Field Naming Consistency

**Use camelCase for all field names**:
- `devComponentId`, `prodAccountId`, `lastPromotedAt`
- Consistent with Boomi API conventions
- Easier for JavaScript/JSON processing in Flow

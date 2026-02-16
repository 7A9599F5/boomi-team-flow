# Flow Service Component Specification

## Component Overview

**Component Name**: `PROMO - Flow Service`
**Component Type**: Flow Service
**Path to Service**: `/fs/PromotionService`
**External Name**: `PromotionService`
**Deployment Target**: Public Boomi Cloud Atom
**Purpose**: Backend API for Boomi Team Promotion Flow application

---

## Message Actions

The Flow Service exposes 9 message actions, each linked to a corresponding Integration process.

### 1. getDevAccounts

**Action Name**: `getDevAccounts`
**Linked Process**: Process A0 - Get Dev Accounts
**Flow Service Operation**: `PROMO - FSS Op - GetDevAccounts`
**Request Profile**: `PROMO - Profile - GetDevAccountsRequest`
**Response Profile**: `PROMO - Profile - GetDevAccountsResponse`
**Service Type**: Message Action

**Description**: Retrieves the list of development sub-accounts available for package selection. Called when the Flow application first loads to populate the dev account dropdown.

**Request Fields**:
- None (empty request)

**Response Fields**:
- `success` (boolean)
- `devAccounts` (array)
  - `accountId` (string)
  - `accountName` (string)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 2. listDevPackages

**Action Name**: `listDevPackages`
**Linked Process**: Process A - List Dev Packages
**Flow Service Operation**: `PROMO - FSS Op - ListDevPackages`
**Request Profile**: `PROMO - Profile - ListDevPackagesRequest`
**Response Profile**: `PROMO - Profile - ListDevPackagesResponse`
**Service Type**: Message Action

**Description**: Queries PackagedComponents from the specified dev account and returns a filtered/sorted list for the UI selection grid.

**Request Fields**:
- `devAccountId` (string, required)

**Response Fields**:
- `success` (boolean)
- `packages` (array)
  - `packageId` (string)
  - `packageVersion` (string)
  - `componentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `createdDate` (datetime)
  - `createdBy` (string) — Boomi user who created the package
  - `notes` (string)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 3. resolveDependencies

**Action Name**: `resolveDependencies`
**Linked Process**: Process B - Resolve Dependencies
**Flow Service Operation**: `PROMO - FSS Op - ResolveDependencies`
**Request Profile**: `PROMO - Profile - ResolveDependenciesRequest`
**Response Profile**: `PROMO - Profile - ResolveDependenciesResponse`
**Service Type**: Message Action

**Description**: Recursively traverses component references starting from the selected process, builds a visited set, and returns the full dependency tree for review.

**Request Fields**:
- `devAccountId` (string, required)
- `rootComponentId` (string, required)

**Response Fields**:
- `success` (boolean)
- `dependencies` (array)
  - `componentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `dependencyType` (string: "DEPENDENT" | "INDEPENDENT")
  - `depth` (integer)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 4. executePromotion

**Action Name**: `executePromotion`
**Linked Process**: Process C - Execute Promotion
**Flow Service Operation**: `PROMO - FSS Op - ExecutePromotion`
**Request Profile**: `PROMO - Profile - ExecutePromotionRequest`
**Response Profile**: `PROMO - Profile - ExecutePromotionResponse`
**Service Type**: Message Action

**Description**: Promotes all components from dev to primary account. For each component: checks DataHub for existing prod mapping, strips credentials, rewrites references, creates/updates component, and stores mapping.

**Request Fields**:
- `devAccountId` (string, required)
- `components` (array)
  - `componentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `folderFullPath` (string)
- `promotionMetadata` (object)
  - `processName` (string)
  - `requestedBy` (string)
  - `requestDate` (datetime)

**Response Fields**:
- `success` (boolean)
- `promotionResults` (array)
  - `devComponentId` (string)
  - `prodComponentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `action` (string: "created" | "updated")
  - `version` (integer)
- `connectionsSkipped` (integer) — count of shared connections not promoted
- `missingConnectionMappings` (array, conditional) — present when errorCode=MISSING_CONNECTION_MAPPINGS
  - `devComponentId` (string)
  - `name` (string)
  - `type` (string)
  - `devAccountId` (string)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 5. packageAndDeploy

**Action Name**: `packageAndDeploy`
**Linked Process**: Process D - Package and Deploy
**Flow Service Operation**: `PROMO - FSS Op - PackageAndDeploy`
**Request Profile**: `PROMO - Profile - PackageAndDeployRequest`
**Response Profile**: `PROMO - Profile - PackageAndDeployResponse`
**Service Type**: Message Action

**Description**: Creates a shareable PackagedComponent, optionally creates/updates an Integration Pack, releases it, and deploys to specified target environments.

**Request Fields**:
- `prodComponentId` (string, required - root process component)
- `packageVersion` (string, required)
- `deploymentNotes` (string)
- `createNewPack` (boolean)
- `newPackName` (string, conditional - required if createNewPack=true)
- `newPackDescription` (string, conditional)
- `existingPackId` (string, conditional - required if createNewPack=false)
- `targetEnvironments` (array)
  - `environmentId` (string)
  - `environmentName` (string)
- `devAccountId` (string, required) — Source dev account ID
- `devPackageId` (string, required) — Source dev package ID
- `devPackageCreator` (string) — Boomi user who created the dev package
- `devPackageVersion` (string) — Version of the dev package

**Response Fields**:
- `success` (boolean)
- `packageId` (string)
- `prodPackageId` (string) — Package ID of the created prod PackagedComponent
- `integrationPackId` (string)
- `deploymentResults` (array)
  - `environmentId` (string)
  - `environmentName` (string)
  - `deployed` (boolean)
  - `errorMessage` (string, optional)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 6. queryStatus

**Action Name**: `queryStatus`
**Linked Process**: Process E - Query Status
**Flow Service Operation**: `PROMO - FSS Op - QueryStatus`
**Request Profile**: `PROMO - Profile - QueryStatusRequest`
**Response Profile**: `PROMO - Profile - QueryStatusResponse`
**Service Type**: Message Action

**Description**: Queries the promotion history DataHub for a specific process or component to retrieve past promotion records. Supports filtering by review stage for the 2-layer approval workflow.

**Request Fields**:
- `queryType` (string: "byProcess" | "byComponent")
- `processName` (string, conditional)
- `componentId` (string, conditional)
- `startDate` (datetime, optional)
- `endDate` (datetime, optional)
- `reviewStage` (string, optional: "PENDING_PEER_REVIEW" | "PENDING_ADMIN_REVIEW" | "ALL") — filters by approval workflow stage. When set, Process E filters DataHub queries by `peerReviewStatus` and/or `adminReviewStatus` fields. Default: "ALL" (no filtering)

**Response Fields**:
- `success` (boolean)
- `promotions` (array)
  - `promotionId` (string)
  - `processName` (string)
  - `devAccountId` (string)
  - `promotionDate` (datetime)
  - `requestedBy` (string)
  - `componentCount` (integer)
  - `packageVersion` (string, optional)
  - `integrationPackId` (string, optional)
  - `prodPackageId` (string, optional) — Package ID of the prod PackagedComponent (populated after packageAndDeploy)
  - `peerReviewStatus` (string, optional) — PENDING_PEER_REVIEW, PEER_APPROVED, PEER_REJECTED
  - `peerReviewedBy` (string, optional) — email of peer reviewer
  - `peerReviewedAt` (datetime, optional) — timestamp of peer review
  - `peerReviewComments` (string, optional) — peer reviewer comments
  - `adminReviewStatus` (string, optional) — PENDING_ADMIN_REVIEW, ADMIN_APPROVED, ADMIN_REJECTED
  - `adminApprovedBy` (string, optional) — email of admin reviewer
  - `adminApprovedAt` (datetime, optional) — timestamp of admin review
  - `adminComments` (string, optional) — admin reviewer comments
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 7. manageMappings

**Action Name**: `manageMappings`
**Linked Process**: Process F - Manage Mappings
**Flow Service Operation**: `PROMO - FSS Op - ManageMappings`
**Request Profile**: `PROMO - Profile - ManageMappingsRequest`
**Response Profile**: `PROMO - Profile - ManageMappingsResponse`
**Service Type**: Message Action

**Description**: Allows querying and manual editing of dev-to-prod component ID mappings stored in the DataHub (admin/troubleshooting feature).

**Connection Seeding Workflow:**
Connections are shared resources pre-configured in the parent account's `#Connections` folder. Admins use the `manageMappings` action with `operation = "create"` to seed ComponentMapping records that link each dev account's connection IDs to the parent's canonical connection IDs. The same parent connection can be mapped from multiple dev accounts (each dev account has its own connection component IDs, but they all map to the same parent `#Connections` component).

**Request Fields**:
- `action` (string: "query" | "update" | "delete")
- `devComponentId` (string, conditional)
- `prodComponentId` (string, conditional)
- `componentName` (string, conditional)

**Response Fields**:
- `success` (boolean)
- `mappings` (array)
  - `devComponentId` (string)
  - `prodComponentId` (string)
  - `componentName` (string)
  - `componentType` (string)
  - `lastPromoted` (datetime)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 8. queryPeerReviewQueue

**Action Name**: `queryPeerReviewQueue`
**Linked Process**: Process E2 - Query Peer Review Queue
**Flow Service Operation**: `PROMO - FSS Op - QueryPeerReviewQueue`
**Request Profile**: `PROMO - Profile - QueryPeerReviewQueueRequest`
**Response Profile**: `PROMO - Profile - QueryPeerReviewQueueResponse`
**Service Type**: Message Action

**Description**: Queries PromotionLog records that are in PENDING_PEER_REVIEW status, excluding promotions initiated by the requesting user (self-review prevention). Returns promotions ready for peer review along with deployment metadata.

**Request Fields**:
- `requesterEmail` (string, required) — the authenticated user's email; used to exclude their own submissions from the results

**Response Fields**:
- `success` (boolean)
- `pendingReviews` (array)
  - `promotionId` (string)
  - `processName` (string)
  - `devAccountId` (string)
  - `initiatedBy` (string) — submitter email
  - `initiatedAt` (datetime) — submission timestamp
  - `componentsTotal` (integer)
  - `componentsCreated` (integer)
  - `componentsUpdated` (integer)
  - `notes` (string) — deployment notes from submitter
  - `packageVersion` (string)
  - `devPackageId` (string)
  - `resultDetail` (string) — JSON per-component results for review
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

---

### 9. submitPeerReview

**Action Name**: `submitPeerReview`
**Linked Process**: Process E3 - Submit Peer Review
**Flow Service Operation**: `PROMO - FSS Op - SubmitPeerReview`
**Request Profile**: `PROMO - Profile - SubmitPeerReviewRequest`
**Response Profile**: `PROMO - Profile - SubmitPeerReviewResponse`
**Service Type**: Message Action

**Description**: Records a peer review decision (approve or reject) against a PromotionLog record. Validates that the reviewer is not the submitter (self-review prevention), that the promotion is in the correct state, and that it hasn't already been reviewed. On approval, updates peerReviewStatus to PEER_APPROVED and adminReviewStatus to PENDING_ADMIN_REVIEW. On rejection, updates peerReviewStatus to PEER_REJECTED.

**Request Fields**:
- `promotionId` (string, required) — the promotion to review
- `decision` (string, required: "APPROVED" | "REJECTED") — the peer review decision
- `reviewerEmail` (string, required) — email of the peer reviewer
- `reviewerName` (string, required) — display name of the peer reviewer
- `comments` (string, optional) — reviewer comments (up to 500 characters)

**Response Fields**:
- `success` (boolean)
- `promotionId` (string) — echoed back for confirmation
- `newStatus` (string) — the resulting peerReviewStatus (PEER_APPROVED or PEER_REJECTED)
- `errorCode` (string, optional)
- `errorMessage` (string, optional)

**Error Codes (specific to this action)**:
- `SELF_REVIEW_NOT_ALLOWED` — reviewerEmail matches the promotion's initiatedBy field
- `ALREADY_REVIEWED` — promotion has already been peer-reviewed (peerReviewStatus is not PENDING_PEER_REVIEW)
- `INVALID_REVIEW_STATE` — promotion is not in PENDING_PEER_REVIEW state (may be IN_PROGRESS, FAILED, etc.)

---

## Configuration Values

The Flow Service requires one configuration value to be set at deployment:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `primaryAccountId` | String | Yes | The primary Boomi account ID used in all Partner API calls. This ID is passed to every integration process via Dynamic Process Properties. |

**Setting Configuration Values**:
1. In AtomSphere, navigate to the deployed Flow Service component
2. Click "Configuration Values"
3. Add `primaryAccountId` with your primary account ID
4. Save and restart the listener if needed

---

## Deployment Steps

### Step 1: Create Packaged Component

1. In AtomSphere, navigate to the `PROMO - Flow Service` component
2. Select "Create Packaged Component"
3. Enter version (e.g., "1.0.0")
4. Add deployment notes
5. Mark as "shareable" if integrating into a pack

### Step 2: Deploy to Public Cloud Atom

1. Navigate to "Deploy" → "Deployments"
2. Select the packaged Flow Service component
3. Choose deployment target: **Public Boomi Cloud Atom**
4. Select environment (e.g., "Production")
5. Deploy

### Step 3: Verify Deployment

1. Navigate to "Runtime Management" → "Listeners"
2. Verify all 9 processes are visible and running:
   - `PROMO - FSS Op - GetDevAccounts`
   - `PROMO - FSS Op - ListDevPackages`
   - `PROMO - FSS Op - ResolveDependencies`
   - `PROMO - FSS Op - ExecutePromotion`
   - `PROMO - FSS Op - PackageAndDeploy`
   - `PROMO - FSS Op - QueryStatus`
   - `PROMO - FSS Op - ManageMappings`
   - `PROMO - FSS Op - QueryPeerReviewQueue`
   - `PROMO - FSS Op - SubmitPeerReview`
3. Note the full service URL: `https://{cloud-base-url}/fs/PromotionService`

---

## Flow Connector Setup

After deploying the Flow Service, configure the Flow application to connect to it.

### Step 1: Create Boomi Integration Service Connector

1. In Flow, navigate to "Connectors"
2. Create new connector: **Boomi Integration Service**
3. Configure:
   - **Runtime Type**: Public Cloud
   - **Path to Service**: `/fs/PromotionService`
   - **Authentication**: Basic Auth
     - Username: (from Shared Web Server User Management)
     - API Token: (from API Token Management)

### Step 2: Retrieve Connector Configuration

1. Click "Retrieve Connector Configuration Data"
2. Flow will automatically discover all 7 message actions
3. Auto-generated Flow Types will be created (see below)

### Step 3: Set Configuration Value

1. In the connector configuration, locate "Configuration Values"
2. Set `primaryAccountId` to your primary Boomi account ID
3. Save connector

---

## Auto-Generated Flow Types

When you retrieve the connector configuration, Flow automatically generates request and response types for each message action.

**Naming Convention**: `{ActionName} {REQUEST|RESPONSE} - {ProfileEntryName}`

**Generated Types**:

1. `getDevAccounts REQUEST - getDevAccountsRequest`
2. `getDevAccounts RESPONSE - getDevAccountsResponse`
3. `listDevPackages REQUEST - listDevPackagesRequest`
4. `listDevPackages RESPONSE - listDevPackagesResponse`
5. `resolveDependencies REQUEST - resolveDependenciesRequest`
6. `resolveDependencies RESPONSE - resolveDependenciesResponse`
7. `executePromotion REQUEST - executePromotionRequest`
8. `executePromotion RESPONSE - executePromotionResponse`
9. `packageAndDeploy REQUEST - packageAndDeployRequest`
10. `packageAndDeploy RESPONSE - packageAndDeployResponse`
11. `queryStatus REQUEST - queryStatusRequest`
12. `queryStatus RESPONSE - queryStatusResponse`
13. `manageMappings REQUEST - manageMappingsRequest`
14. `manageMappings RESPONSE - manageMappingsResponse`
15. `queryPeerReviewQueue REQUEST - queryPeerReviewQueueRequest`
16. `queryPeerReviewQueue RESPONSE - queryPeerReviewQueueResponse`
17. `submitPeerReview REQUEST - submitPeerReviewRequest`
18. `submitPeerReview RESPONSE - submitPeerReviewResponse`

These types are used throughout the Flow application to ensure type safety when calling the Flow Service operations.

---

## Timeout and Async Behavior

The Flow Service leverages Boomi's built-in async processing for long-running operations:

1. **Initial Request**: Flow sends request to Flow Service operation
2. **Flow Service Processing**: Integration process begins execution
3. **Automatic Wait Response**: If processing exceeds threshold (typically 30s), Flow Service automatically returns a wait response
4. **Flow UI Spinner**: Flow displays spinner/progress indicator to user
5. **Callback on Completion**: When Integration process completes, Flow Service callbacks to Flow
6. **Result Display**: Flow receives final response and updates UI

**User Experience**:
- User can close the browser tab during long operations
- State is persisted via IndexedDB
- User can return later to check status
- No manual polling required

**Typical Operation Durations**:
- `getDevAccounts`: < 5 seconds
- `listDevPackages`: 10-30 seconds (depends on package count)
- `resolveDependencies`: 5-15 seconds (depends on dependency depth)
- `executePromotion`: 30-120 seconds (depends on component count)
- `packageAndDeploy`: 20-60 seconds (depends on target environment count)
- `queryStatus`: < 5 seconds
- `manageMappings`: < 5 seconds

---

## Error Handling Contract

All Flow Service responses follow a consistent error handling pattern.

**Standard Response Fields**:

| Field | Type | Always Present | Description |
|-------|------|----------------|-------------|
| `success` | boolean | Yes | `true` if operation succeeded, `false` if error occurred |
| `errorCode` | string | Conditional | Error code for programmatic handling (present when success=false) |
| `errorMessage` | string | Conditional | Human-readable error description (present when success=false) |

**Flow Decision Logic**:

In Flow, every operation response should be followed by a Decision step:

```
Decision: Check Success
  - If success = true → Continue to next step
  - If success = false → Branch to error handling path
```

**Common Error Codes**:

| Error Code | Description | User Action |
|------------|-------------|-------------|
| `AUTH_FAILED` | API authentication failed | Check API token configuration |
| `ACCOUNT_NOT_FOUND` | Dev account ID invalid | Verify account exists |
| `COMPONENT_NOT_FOUND` | Component ID not found | Check component exists in dev account |
| `DATAHUB_ERROR` | DataHub query/update failed | Contact administrator |
| `API_RATE_LIMIT` | Partner API rate limit exceeded | Retry after cooldown period |
| `DEPENDENCY_CYCLE` | Circular dependency detected | Review component references |
| `INVALID_REQUEST` | Request validation failed | Check required fields |
| `PROMOTION_FAILED` | Component promotion failed | Review error message for details |
| `DEPLOYMENT_FAILED` | Environment deployment failed | Check target environment status |
| `MISSING_CONNECTION_MAPPINGS` | One or more connection mappings not found in DataHub | Admin must seed missing mappings via Mapping Viewer |
| `SELF_REVIEW_NOT_ALLOWED` | Reviewer attempted to review their own promotion submission | A different team member must perform the peer review |
| `ALREADY_REVIEWED` | Promotion has already been peer-reviewed | No action needed; check current status |
| `INVALID_REVIEW_STATE` | Promotion is not in the expected state for this review action | Verify the promotion status before retrying |

**Error Handling Best Practices**:

1. Always check `success` field before processing response data
2. Log `errorCode` and `errorMessage` to Flow console for debugging
3. Display user-friendly error messages in the UI (translate errorCode to UI text)
4. Provide retry mechanism for transient errors (e.g., rate limits)
5. For critical errors, allow user to contact support with error details

---

## Security Considerations

### Authentication

- Flow Service uses Basic Auth with Shared Web Server User credentials
- API tokens should be stored securely in Flow connector configuration
- Rotate API tokens periodically (recommended: every 90 days)

### Authorization

- Partner API requires primary account privileges
- All sub-account access uses `overrideAccount` parameter
- Flow Service inherits permissions from API token owner

### Data Privacy

- Credential values are stripped during promotion (Process C)
- No sensitive data persisted in DataHub mapping tables
- All API communication over HTTPS

---

## Monitoring and Troubleshooting

### Process Logs

1. Navigate to "Process Reporting" in AtomSphere
2. Filter by process names: `PROMO - FSS Op - *`
3. Review execution logs for errors or performance issues

### Common Issues

**Issue**: Flow Service operation times out
**Cause**: Component count too high, API rate limiting
**Solution**: Increase timeout threshold, add pagination

**Issue**: Dependency resolution returns incomplete tree
**Cause**: Circular dependencies or broken references
**Solution**: Review component references in dev account, check for orphaned components

**Issue**: Promotion creates duplicates
**Cause**: DataHub mapping not found, componentId mismatch
**Solution**: Query mappings via `manageMappings` action, verify dev/prod ID pairs

**Issue**: Deployment fails to target environment
**Cause**: Environment ID invalid, insufficient permissions
**Solution**: Verify environment exists in account group, check API token permissions

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-16 | Initial Flow Service specification |

---

## Related Documentation

- Partner API Reference: https://help.boomi.com/docs/atomsphere/integration/api/r-atm-partner_api_5f0c0b46-e0b0-4a45-9437-4b8e66dd1c74/
- Flow Service Developer Guide: https://help.boomi.com/docs/flow/flow-configuration/t-flow-configure_flow_service_connector_77e89cc9-a02e-43fd-8c24-7b0c4b41a479/
- DataHub Usage: https://help.boomi.com/docs/atomsphere/integration/datahub/c-atm-datahub_overview_1b87a58b-5b9f-4b4e-9d0d-5d0e7b5e5e5e/

---

## Support

For issues or questions:
- Internal support: Contact Boomi platform team
- External support: Open ticket via Boomi Support Portal
- Community: Boomi Community Forums

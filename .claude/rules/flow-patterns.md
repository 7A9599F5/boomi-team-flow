---
globs:
  - "flow/**"
---

# Flow Patterns

## Page Naming Conventions

### Developer Swimlane Pages
- **Page 1**: Package Browser
- **Page 2**: Promotion Review
- **Page 3**: Promotion Status
- **Page 4**: Deployment Submission

### Peer Review Swimlane Pages
- **Page 5**: Peer Review Queue
- **Page 6**: Peer Review Detail

### Admin Swimlane Pages
- **Page 7**: Admin Approval Queue
- **Page 8**: Mapping Viewer

## Swimlane Structure

### Authorization Model
- **Developer Swimlane**: SSO group "Boomi Developers"
- **Peer Review Swimlane**: SSO groups "Boomi Developers" OR "Boomi Admins" (any listed group grants access)
- **Admin Swimlane**: SSO group "Boomi Admins"

### Self-Review Prevention
- Peer reviewers cannot review their own submissions
- Enforced at backend (Process E2 excludes own submissions) + UI level (Decision step blocks if `$User/Email` matches `initiatedBy`)

## Flow Value Naming

### Standard Naming Pattern
- Use camelCase for all Flow value names
- Prefix with context when needed: `selected{Entity}`, `pending{Action}`, `available{Resources}`
- Examples:
  - `selectedDevAccountId`
  - `pendingPeerReviews`
  - `availableIntegrationPacks`

### Key Flow Values
- **selectedPackage**: Selected package from browser (object with componentId, packageId, componentName, packageVersion, createdBy)
- **dependencyTree**: Resolved dependency tree from resolveDependencies
- **promotionId**: UUID of current promotion run
- **branchId**: Promotion branch ID for diff/merge operations
- **userSsoGroups**: User's Azure AD group memberships
- **accessibleAccounts**: Dev accounts user can access based on SSO groups

## Message Action Naming

### Pattern
- **Always use camelCase** for message action names
- Match the Integration process's purpose (not the process letter code)
- Examples:
  - `getDevAccounts` (Process A0)
  - `listDevPackages` (Process A)
  - `resolveDependencies` (Process B)
  - `executePromotion` (Process C)
  - `packageAndDeploy` (Process D)
  - `queryStatus` (Process E)
  - `queryPeerReviewQueue` (Process E2)
  - `submitPeerReview` (Process E3)
  - `manageMappings` (Process F)
  - `generateComponentDiff` (Process G)
  - `listIntegrationPacks` (Process J)

### Auto-Generated Flow Types
When using Boomi Integration Service connector, Flow auto-generates request/response types:
- **Pattern**: `{actionName} REQUEST - {profileEntryName}`
- **Example**: `executePromotion REQUEST - executePromotionRequest`

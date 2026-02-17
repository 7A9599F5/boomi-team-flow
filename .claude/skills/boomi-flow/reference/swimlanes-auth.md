# Swimlanes and Authorization

## Purpose

**Swimlanes** are authorization containers that restrict access to specific parts of a flow based on user identity and group membership. They enable multi-stage approval workflows where different roles have different permissions.

---

## How Swimlanes Work

### Container Model

1. **Swimlane step acts as a container** on the flow canvas
2. **Authentication challenge**: When a user enters a swimlane, they are challenged for authentication if not already authenticated for that swimlane
3. **Group/user restrictions**: Swimlanes are configured with specific SSO groups or individual users who can access them
4. **Flow pause at boundaries**: Flow execution pauses at swimlane boundaries until a user with appropriate authorization continues it

### Execution Flow

```
User in Swimlane A
  ↓
Completes action (e.g., "Submit for Review" button)
  ↓
Outcome triggers transition to Swimlane B
  ↓
Flow pauses (waiting for user in Swimlane B to authenticate)
  ↓ (Email notification sent to Swimlane B users)
User in Swimlane B authenticates
  ↓
Flow resumes in Swimlane B
```

---

## Configuration

### Authorization Options

**SSO Groups:**
- Azure AD / Microsoft Entra ID
- Okta
- Salesforce
- SAML 2.0-based authentication providers
- ADFS (Active Directory Federation Services)

**Individual Users:**
- Specific user accounts (by email or username)

**OR Logic for Groups:**
- Multiple groups can be specified
- Access granted if user belongs to ANY listed group
- Example: Swimlane authorized for "Boomi Developers" OR "Boomi Admins"
  - User in "Boomi Developers" → access granted
  - User in "Boomi Admins" → access granted
  - User in neither group → access denied

### Swimlane Settings

**Location:** Flow canvas > Add step > Swimlane

**Configuration fields:**
- **Name**: Display name for the swimlane
- **Authorization**:
  - **SSO Groups**: List of group names (case-sensitive, must match IdP group names)
  - **Individual Users**: List of user emails or usernames
- **Notification**: Email template for when flow pauses at swimlane boundary (optional)

---

## 2-Layer Approval Pattern

### Use Case: Developer → Peer Review → Admin Approval

**Scenario:** Component promotion requires peer review by another developer, then final admin approval before deployment.

**Swimlane structure:**

```
Swimlane 1: Developer (SSO group: "Boomi Developers")
├── Page 1: Package Browser (select package to promote)
├── Page 2: Promotion Review (review dependency tree, add notes)
└── Outcome: "Submit for Peer Review"
    ↓ (Email notification to all Boomi Developers)
Swimlane 2: Peer Review (SSO groups: "Boomi Developers" OR "Boomi Admins")
├── Page 5: Peer Review Queue (list of pending peer reviews, excluding own submissions)
├── Page 6: Peer Review Detail (view promotion details, diff, notes)
└── Outcome: "Approve" or "Reject"
    ↓ (Email notification to Boomi Admins)
Swimlane 3: Admin (SSO group: "Boomi Admins")
├── Page 7: Admin Approval Queue (list of peer-approved promotions)
└── Outcome: "Deploy" (final approval, triggers Integration Pack deployment)
```

**Authorization rules:**
- **Swimlane 1**: Only "Boomi Developers" can submit promotions
- **Swimlane 2**: "Boomi Developers" OR "Boomi Admins" can perform peer review
  - Backend logic prevents self-review (see Self-Review Prevention below)
- **Swimlane 3**: Only "Boomi Admins" can perform final approval and deployment

**Flow pauses:**
- **After Page 2**: Flow pauses until a peer reviewer (not the submitter) authenticates
- **After Page 6**: Flow pauses until an admin authenticates

---

## SSO and Identity Providers

### SAML 2.0 Implementation

**Flow role:** Service Provider (SP)
**IdP role:** Identity Provider
**Flow model:** Service Provider-initiated sign-in

**Authentication flow:**

1. User navigates to Flow application URL
2. Flow redirects to IdP login page
3. User authenticates with IdP (username/password, MFA, etc.)
4. IdP sends SAML assertion back to Flow
5. Flow validates assertion and creates session
6. User accesses flow with SSO identity

**Enhanced Token Security:**
- Encrypted one-time-use token provided to Flow runtime
- Token exchanged with Flow API to complete authentication
- Prevents token replay attacks

### SSO Configuration in Flow

**Location:** Flow > Settings > Identity Providers

**Setup steps:**

1. Add new Identity Provider
2. Configure provider details:
   - **Provider Type**: Azure AD, Okta, SAML, etc.
   - **Metadata URL**: IdP metadata endpoint (e.g., `https://login.microsoftonline.com/{tenant-id}/federationmetadata/2007-06/federationmetadata.xml`)
   - **Entity ID**: SP entity identifier (unique identifier for Flow tenant)
   - **SSO URL**: IdP SSO endpoint
   - **Certificate**: X.509 certificate for assertion validation
3. Enable SSO for tenant
4. Configure group mappings (optional, map IdP groups to Flow groups)

**Important:** Tenant must always have at least one admin user who is **NOT SSO-enabled** for tenant management.

### Azure AD Configuration

**Azure AD side:**

1. Register Flow as enterprise application in Azure AD
2. Configure SAML SSO:
   - **Identifier (Entity ID)**: Flow tenant entity ID
   - **Reply URL (Assertion Consumer Service URL)**: Flow callback URL
3. Add group claims to token:
   - **Groups claim**: Send groups as `groups` claim in token
   - **Group format**: Security groups, Object IDs or Display Names
4. Assign users and groups to application

**Flow side:**

1. Add Azure AD as Identity Provider
2. Copy SAML metadata URL from Azure AD app
3. Paste metadata URL into Flow IdP configuration
4. Save and test SSO

**Sources:**
- [Configure Boomi for Single sign-on with Microsoft Entra ID](https://learn.microsoft.com/en-us/entra/identity/saas-apps/boomi-tutorial)
- [Implementing Flow single sign-on with SAML](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Setting_up_and_managing_flows/Tenants/Flow_single_sign-on_with_SAML_authentication/flo-SAML_SSO_Implementing_b0f9d93f-ea74-4afe-8768-a914e7c7b7e8)

---

## $User Object

### Properties

Flow provides a `$User` object with authenticated user details:

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `$User/Email` | String | User email address | `alice@example.com` |
| `$User/First Name` | String | User first name | `Alice` |
| `$User/Last Name` | String | User last name | `Smith` |
| `$User/Groups` | List | SSO group memberships | `["Boomi Developers", "Boomi Admins"]` |
| `$User/Username` | String | Username (if different from email) | `alice.smith` |
| `$User/ID` | String | Unique user identifier | `user-uuid-1234` |

### Usage Patterns

#### 1. Binding to Flow Values (Audit Trails)

Store user identity for logging and audit trails:

```
Flow Value: peerReviewerEmail (String) = $User/Email
Flow Value: peerReviewerName (String) = $User/First Name + " " + $User/Last Name
Flow Value: reviewedAt (DateTime) = $Now (current timestamp)
```

**Use case:** When peer reviewer approves a promotion, store their identity in DataHub PromotionLog record:

```json
{
  "promotionId": "uuid",
  "reviewStage": "PEER_REVIEW",
  "reviewedBy": "alice@example.com",
  "reviewedByName": "Alice Smith",
  "reviewedAt": "2026-02-16T14:30:00.000Z",
  "reviewAction": "APPROVED"
}
```

#### 2. Business Rules (Conditional Visibility)

Control component or page visibility based on user identity:

**Show component only if user is admin:**

```
Business Rule: Show when
ALL (AND)
  $User/Groups contains "Boomi Admins"
```

**Show "Deploy" button only if user is admin:**

```
Button: Deploy
Visibility Rule:
ALL (AND)
  $User/Groups contains "Boomi Admins"
  reviewStage == "APPROVED_FOR_DEPLOYMENT"
```

#### 3. Self-Review Prevention

Compare current user with record owner to prevent self-review:

**Scenario:** Prevent developers from reviewing their own promotions.

**Implementation:**

**Page 5: Peer Review Queue (on page load)**

```
Message Step: queryPeerReviewQueue
Request:
{
  "reviewStage": "PENDING_PEER_REVIEW",
  "excludeSubmittedBy": $User/Email  // Backend filters out records where initiatedBy == current user
}

Response:
{
  "promotions": [
    {
      "promotionId": "uuid",
      "initiatedBy": "bob@example.com",  // Alice cannot review Bob's submission
      "componentName": "Orders Process",
      ...
    }
  ]
}
```

**Page 6: Peer Review Detail (on page load)**

```
Decision Step: Check Self-Review
Business Rule on Outcome "Allow Access":
ALL (AND)
  selectedPeerReview.initiatedBy != $User/Email

Business Rule on Outcome "Block Access":
ALL (AND)
  selectedPeerReview.initiatedBy == $User/Email

Outcome "Block Access" → Error Page
  Message: "You cannot review your own submission. Please ask another developer to perform peer review."
```

**Backend validation (Integration Process E3: submitPeerReview):**

```groovy
// Groovy script in Data Process shape
def initiatedBy = promotionLogRecord.initiatedBy
def peerReviewerEmail = requestData.peerReviewerEmail

if (initiatedBy == peerReviewerEmail) {
    // Reject with error
    responseData.success = false
    responseData.errorCode = "SELF_REVIEW_NOT_ALLOWED"
    responseData.errorMessage = "You cannot review your own submission."
    return
}

// Proceed with peer review update
// ...
```

---

## Access Control Best Practices

### 1. Always Have Non-SSO Admin

**Requirement:** Tenant must always have at least one admin user who is NOT SSO-enabled.

**Reason:** If SSO provider is down or misconfigured, non-SSO admin can still access tenant to fix issues.

**How to configure:**
- Create admin user with email/password authentication
- Assign admin role
- Do NOT enable SSO for this user

### 2. Use Swimlanes for Approval Gates

**Pattern:** Multi-stage approval workflows with swimlane boundaries acting as gates.

**Example:**
- Developer submits request (Swimlane 1)
- Peer reviews and approves (Swimlane 2)
- Admin performs final approval and deployment (Swimlane 3)

**Benefit:** Flow pauses at each stage until authorized user continues, ensuring proper approval sequence.

### 3. Combine with Business Rules for Fine-Grained Control

**Pattern:** Use swimlanes for coarse-grained authorization (role-based), business rules for fine-grained access (data-based).

**Example:**
- Swimlane: "Boomi Developers" can access peer review section
- Business Rule: Hide "Approve" button if `selectedPeerReview.initiatedBy == $User/Email` (self-review prevention)

### 4. Store User Identity for Audit Trails

**Pattern:** Bind `$User/Email`, `$User/First Name`, `$User/Last Name` to Flow Values, then pass to Integration processes for logging.

**Example:**

```
Flow Value: peerReviewerEmail = $User/Email
Flow Value: peerReviewerName = $User/First Name + " " + $User/Last Name

Message Step: submitPeerReview
Request:
{
  "promotionId": "uuid",
  "reviewAction": "APPROVED",
  "reviewedBy": peerReviewerEmail,
  "reviewedByName": peerReviewerName,
  "reviewNotes": reviewNotes
}

Integration Process E3:
- Update PromotionLog record in DataHub with peer review details
- Create audit log entry
```

### 5. Test with Multiple Roles

**Pattern:** Validate authorization logic with different SSO groups.

**Test cases:**
- User in "Boomi Developers" only → can submit promotions, perform peer review (not on own submissions)
- User in "Boomi Admins" only → can perform peer review, final admin approval
- User in both groups → can access all swimlanes
- User in neither group → cannot access flow (redirected to "Access Denied" page)

---

## Email Notifications at Swimlane Transitions

### Purpose

Send email notifications to users in the next swimlane when flow pauses at a boundary.

### Configuration

**Location:** Swimlane step > Notification settings

**Email template:**

```
Subject: New Peer Review Request: {componentName}

Body:
A new promotion has been submitted for peer review.

Component: {componentName}
Submitted By: {initiatedByName} ({initiatedBy})
Submitted At: {initiatedAt}

To review and approve/reject this promotion, please visit:
{flowUrl}

Thank you!
```

**Substitution tokens:**
- `{componentName}`: Flow Value `selectedPackage.componentName`
- `{initiatedByName}`: Flow Value `initiatedByName`
- `{initiatedBy}`: Flow Value `initiatedBy`
- `{initiatedAt}`: Flow Value `initiatedAt`
- `{flowUrl}`: Flow URL with state ID (auto-generated)

**Recipient groups:**
- Send to all users in "Boomi Developers" group (for peer review notifications)
- Send to all users in "Boomi Admins" group (for admin approval notifications)

---

## Troubleshooting

### Issue: User cannot access swimlane despite being in SSO group

**Possible causes:**
1. SSO group name in Flow doesn't match IdP group name (case-sensitive)
2. IdP not sending group claims in SAML assertion
3. User not yet assigned to SSO group in IdP
4. Flow session cached with old group memberships (user needs to re-authenticate)

**Resolution:**
1. Verify SSO group name matches exactly (case-sensitive)
2. Check IdP configuration (ensure group claims enabled and sent in token)
3. Verify user is assigned to group in IdP
4. Have user log out of Flow and re-authenticate to refresh session

### Issue: Flow pauses at swimlane boundary but no email notification sent

**Possible causes:**
1. Email notification not configured on swimlane step
2. Email template missing substitution tokens
3. Recipient group has no members
4. SMTP configuration issue in Flow tenant settings

**Resolution:**
1. Check swimlane step notification settings
2. Verify email template has valid substitution tokens
3. Check recipient group has active users
4. Verify SMTP configuration in Flow > Settings > Email

### Issue: Self-review prevention not working

**Possible causes:**
1. Business rule comparing wrong Flow Values
2. Backend validation missing or bypassed
3. `$User/Email` not bound to request data
4. Email comparison case-sensitive mismatch

**Resolution:**
1. Verify business rule compares `selectedPeerReview.initiatedBy` with `$User/Email`
2. Add backend validation in Integration process to double-check
3. Bind `$User/Email` to Flow Value, then pass to message step request
4. Normalize emails to lowercase for comparison: `LOWER($User/Email) == LOWER(selectedPeerReview.initiatedBy)`

---

## Sources

- [Swimlane steps - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Building_and_publishing_flows/Steps/c-flo-ME_Swimlane_872bacc3-8123-4bfa-9b87-8bc3ee9d8beb)
- [Overview - Identity Providers](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Setting_up_and_managing_flows/Identity_providers/flo-IDP_cc718062-51e1-4c35-b9e7-3e971ac28249)
- [Implementing Flow single sign-on with SAML](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Setting_up_and_managing_flows/Tenants/Flow_single_sign-on_with_SAML_authentication/flo-SAML_SSO_Implementing_b0f9d93f-ea74-4afe-8768-a914e7c7b7e8)
- [Configure Boomi for Single sign-on with Microsoft Entra ID](https://learn.microsoft.com/en-us/entra/identity/saas-apps/boomi-tutorial)
- [Authenticating Boomi Flow with SAML service using ADFS Identity Provider](https://www.linkedin.com/pulse/authenticating-boomi-flow-saml-service-using-adfs-identity-padala)

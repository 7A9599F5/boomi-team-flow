# Page 7: Admin Approval Queue (Admin Swimlane)

## Overview

The Admin Approval Queue is the final approval gate in the 2-layer approval workflow. Only promotions that have passed peer review (peerReviewStatus = PEER_APPROVED) appear here. Admins authenticate via SSO, review promotion details including peer review information, and execute deployment to the target account group.

## Page Load Behavior

1. **Admin authentication:**
   - User must authenticate via SSO with `ABC_BOOMI_FLOW_ADMIN` group membership
   - If not authorized: Show error "Access denied. This page requires admin privileges."
   - Store admin user context: `adminUserName`, `adminUserEmail`

2. **Message step execution:** `queryStatus`
   - Input:
     - `status` = "COMPLETED"
     - `deployed` = false
     - `reviewStage` = "PENDING_ADMIN_REVIEW"
   - Output: `pendingApprovals` array (promotions that have passed peer review and are awaiting admin approval)

3. **Populate approval queue:**
   - Display pending approval requests in Data Grid
   - Sort by `initiatedAt` descending (newest first)

4. **Error handling:**
   - If `queryStatus` fails → Navigate to Error Page

## Components

### Approval Queue Data Grid

**Component Type:** Data Grid / Table

**Data Source:**
- API: `queryStatus` response → `promotions` array (filtered for pending approval)
- Flow value: `pendingApprovals`

**Columns:**

| Column | Field | Width | Sortable | Formatting |
|--------|-------|-------|----------|------------|
| Submitter | `initiatedBy` | 12% | Yes | Email or name |
| Process Name | `processName` | 17% | Yes | Bold text |
| Components | `componentsTotal` | 7% | Yes | Numeric |
| Created/Updated | `componentsCreated` / `componentsUpdated` | 10% | Yes | "X new, Y updated" |
| Peer Reviewed By | `peerReviewedBy` | 12% | Yes | Email or name |
| Submitted | `initiatedAt` | 12% | Yes | Date/time format |
| Status | `status` | 8% | Yes | Badge |
| Environment | `targetEnvironment` | 8% | Yes | Badge: "PRODUCTION" blue |
| Hotfix | `isHotfix` | 7% | Yes | Badge: "EMERGENCY HOTFIX" red if true; hidden if false |
| Notes | `notes` | 12% | No | Truncated, tooltip |

**Column Details:**

1. **Submitter**
   - Display: Submitter email or full name (e.g., "john.doe@company.com" or "John Doe")
   - Format: Plain text, left-aligned
   - Sortable: Alphabetical

2. **Process Name**
   - Display: Root process name (e.g., "Order Processing Main")
   - Format: Bold text for emphasis
   - Sortable: Alphabetical
   - Derived from: `promotionResults` or `deploymentRequest.processName`

3. **Components**
   - Display: Total component count (e.g., "12")
   - Format: Numeric text, centered
   - Sortable: Numeric order

4. **Created/Updated**
   - Display: "X new, Y updated" (e.g., "2 new, 10 updated")
   - Format: Plain text or badge (e.g., blue "2 new" / green "10 updated")
   - Sortable: By total components (created + updated)
   - Derived from: `componentsCreated`, `componentsUpdated`

5. **Submitted**
   - Display: Submission timestamp
   - Format: "YYYY-MM-DD HH:mm" or relative time ("2 hours ago", "Yesterday")
   - Sortable: Chronological (default descending = newest first)
   - Field: `initiatedAt`

6. **Status**
   - Display: Promotion status (e.g., "COMPLETED", "PENDING_APPROVAL")
   - Format: Badge with color:
     - **COMPLETED:** Green badge
     - **PENDING_APPROVAL:** Yellow/orange badge
   - Sortable: Alphabetical

7. **Notes**
   - Display: Deployment notes from submitter
   - Format: Truncated to 50 chars with ellipsis
   - Tooltip: Show full text on hover
   - Empty: "No notes provided" (gray text)
   - Not sortable

**Row Selection:**
- **Mode:** Single-row selection
- **Visual:** Highlight selected row with accent color
- **On select event:**
  1. Store selected promotion → `selectedPromotion` Flow value
  2. Expand Promotion Detail Panel (below grid or side panel)
  3. Enable Approve/Deny buttons

**Default Sort:**
- `initiatedAt` descending (newest submissions at top)

**Empty State:**
- Message: "No pending approvals"
- Submessage: "All deployment requests have been processed."
- Icon: Checkmark or empty inbox icon

**Pagination:**
- If > 25 requests: Enable pagination (25 rows per page)

---

### Admin Self-Approval Prevention

**Implementation:** Decision step after row selection (mirrors peer review self-review prevention)

1. **Decision step:** After a row is selected and before approval actions are enabled
   - Condition: `LOWERCASE($User/Email)` != `LOWERCASE(selectedPromotion.initiatedBy)`
   - **True path (different person):** Proceed — expand Promotion Detail Panel, enable Approve/Deny buttons
   - **False path (same person):** Show inline error banner: "You cannot approve your own promotion. Please ask another admin to review." Disable Approve and Deny buttons. The detail panel may still be shown (read-only) but no approval actions are available.

2. **Purpose:** Prevents an admin who submitted a promotion from also serving as the final approver, enforcing independence in the 2-layer approval workflow. Even though peer review was performed by a different person, the admin approval gate must also be independent from the original submitter.

---

### Promotion Detail Panel

**Component Type:** Expandable panel or side panel

**Trigger:** When a row is selected in Approval Queue Data Grid

**Location:** Below the grid (collapsible) or as a side panel (desktop)

**Content:**

#### Section 1: Submission Details

**Submitter Information:**
- **Submitted by:** `{initiatedBy}` (email and name)
- **Submitted at:** `{initiatedAt}` (full timestamp)
- **Promotion ID:** `{promotionId}` (with copy button)

**Deployment Information:**
- **Package Version:** `{deploymentRequest.packageVersion}`
- **Integration Pack:** `{deploymentRequest.integrationPackName}` or "New: {newPackName}"
- **Target Account Group:** `{deploymentRequest.targetAccountGroupName}`

**Deployment Notes:**
- Display: `{deploymentRequest.notes}`
- Format: Plain text or markdown rendering
- Empty: "No notes provided"

---

#### Section 2: Peer Review Information

**Peer Review Status:**
- **Reviewed by:** `{peerReviewedBy}` (email and name)
- **Reviewed at:** `{peerReviewedAt}` (full timestamp)
- **Decision:** `{peerReviewStatus}` (PEER_APPROVED badge — green)
- **Comments:** `{peerReviewComments}` or "No comments provided"

---

#### Section 2b: Environment & Hotfix Information

**Hotfix Alert (conditional — shown when `isHotfix = "true"`):**
- **Large Banner:** Red background with warning icon
- **Title:** "⚠ EMERGENCY HOTFIX"
- **Justification:** `{selectedPromotion.hotfixJustification}` — displayed prominently
- **Warning text:** "This deployment bypassed the test environment. Please review carefully."

**Test Deployment History (conditional — shown when `testPromotionId` is populated):**
- **Header:** "Test Environment Validation"
- **Test Promotion ID:** `{selectedPromotion.testPromotionId}`
- **Test Deployed Date:** `{selectedPromotion.testDeployedAt}`
- **Test Integration Pack:** `{selectedPromotion.testIntegrationPackName}`
- **Styling:** Light green info panel

---

#### Section 3: Promotion Results

**Component Results Table:**
- Smaller data grid showing individual component results
- Columns:
  - Component Name
  - Action (CREATE/UPDATE)
  - Status (SUCCESS/FAILED)
  - Config Stripped (Yes/No)
  - Changes ("View Diff" link for UPDATE; "View New" for CREATE)
- Rows: All components from `promotionResults` array

**Summary:**
- **Total Components:** `{componentsTotal}`
- **Created:** `{componentsCreated}` (blue badge)
- **Updated:** `{componentsUpdated}` (green badge)
- **Failed:** `{componentsFailed}` (red badge, if > 0)

---

#### Section 4: Credential Warning (Conditional)

**Visibility:** Shown if any component has `configStripped = true`

**Content:**
- Warning icon and title: "Credential Reconfiguration Required"
- List of components needing credential reconfiguration
- Extracted from `promotionResults` where `configStripped = true`

**Example:**
```
⚠️ The following components need credential reconfiguration:
• DB Connection - MySQL Prod
• API Profile - Salesforce
```

---

#### Component Diff Panel

**Component Type:** Expandable panel (XmlDiffViewer custom component)

**Trigger:** When admin clicks "View Diff" or "View New" link in the component results table

**Location:** Expands inline below Section 3 table

**Behavior:**
1. On click: Show loading spinner
2. Call `generateComponentDiff` message step with `branchId` from promotion data
3. On response: Render `XmlDiffViewer` with branch vs main XML
4. Max-height: 500px, scrollable
5. Close button (X) in top-right
6. Only one panel open at a time

**Purpose:** Enables admins to review the actual XML-level changes before merging to main and deploying. This is the final safety gate.

---

#### Section 5: Source Account

**Dev Account Information:**
- **Source Account:** `{devAccountName}`
- **Account ID:** `{devAccountId}`

---

### Admin Comments Textarea

**Component Type:** Textarea

**Configuration:**
- **Label:** "Admin Comments"
- **Placeholder:** "Add any notes about this approval or denial..."
- **Required:** No (optional)
- **Max length:** 500 characters
- **Rows:** 3

**Behavior:**
- **On change:** Store value in `adminComments` Flow value
- **Character counter:** Show "X / 500 characters" below textarea

**Styling:**
- Full width or max 600px
- Located below Promotion Detail Panel

---

### Approve Button

**Component Type:** Button (Primary, Success)

**Configuration:**
- **Label:** "Approve and Deploy"
- **Style:** Large primary button
- **Color:** Green/success color
- **Icon (optional):** Checkmark icon
- **Size:** Large

**Enabled Condition:**
- **Enabled when:** A request is selected (`selectedPromotion` not null)
- **Disabled when:** No request selected

**Confirmation Modal:**
- **Trigger:** On button click
- **Modal title:** "Confirm Approval"
- **Modal content:**
  ```
  Are you sure you want to approve and deploy this promotion?

  Process: {processName}
  Package Version: {packageVersion}
  Target Account Group: {targetAccountGroupName}
  Total Components: {componentsTotal}

  This will create/update an Integration Pack and deploy it to the target account group.
  ```
- **Buttons:**
  - "Cancel" (secondary, left)
  - "Confirm Approval" (primary green, right)

**Hotfix Confirmation (conditional — shown when `isHotfix = "true"`):**
- Additional warning text in modal: "⚠ This is an emergency hotfix that bypassed the test environment."
- Extra checkbox (required): "I acknowledge this is an emergency hotfix that bypassed testing"
- Checkbox must be checked before "Confirm Approval" button is enabled

**Behavior on Confirm:**

1. **Close modal**

2. **Create merge request:**
   - `POST /MergeRequest` with body:
     - `source`: `{selectedPromotion.branchId}`
     - `strategy`: "OVERRIDE"
     - `priorityBranch`: `{selectedPromotion.branchId}`
   - Store `mergeRequestId` from response

3. **Execute merge:**
   - `POST /MergeRequest/execute/{mergeRequestId}` with action: "MERGE"
   - Poll `GET /MergeRequest/{mergeRequestId}` until `stage` = "MERGED"
   - Show "Merging branch to main..." spinner

4. **Trigger Message step:** `packageAndDeploy`
   - Input includes `branchId` for post-deploy cleanup
   - Packages from **main** (components now merged to main)
   - Standard packageAndDeploy flow (create PackagedComponent, Integration Pack, deploy)

5. **Delete promotion branch:**
   - `DELETE /Branch/{branchId}`
   - Update PromotionLog: set `branchId` = null

6. **Show deployment results:**
   - If success:
     - Show success message: "Branch merged, packaged, and deployed successfully!"
     - Display deployment ID and prod package ID
   - If failure:
     - Show error message with details
     - Branch may still exist (admin can retry)

7. **Send email notification to submitter + peer reviewer:**
   - Same email as before but add: "Branch merged to main before packaging."

8. **Refresh approval queue:**
   - Re-run `queryStatus` to update pending approvals list
   - Clear selected promotion
   - Collapse detail panel

---

### Deny Button

**Component Type:** Button (Danger, Secondary)

**Configuration:**
- **Label:** "Deny"
- **Style:** Medium button
- **Color:** Red/danger color
- **Icon (optional):** X icon
- **Size:** Medium

**Enabled Condition:**
- **Enabled when:** A request is selected (`selectedPromotion` not null)
- **Disabled when:** No request selected

**Behavior on Click:**

1. **Show denial reason prompt:**
   - Modal or inline form
   - **Title:** "Deny Deployment Request"
   - **Field:** Textarea for denial reason
     - Label: "Reason for Denial"
     - Placeholder: "Explain why this deployment is being denied..."
     - Required: Yes
     - Max length: 500 characters
   - **Buttons:**
     - "Cancel" (secondary, left)
     - "Confirm Denial" (danger red, right)

2. **On confirm denial:**
   - Update promotion status to "DENIED"
   - Store denial reason and admin info

3. **Send email notification to submitter + peer reviewer:**
   - **To:** `{initiatedBy}` (submitter email), `{peerReviewedBy}` (peer reviewer email)
   - **Subject:** `"Admin Denied: {processName} v{packageVersion}"`
   - **Body:**
     ```
     The promotion request has been denied by admin review.

     PROMOTION DETAILS:
     Promotion ID: {promotionId}
     Process: {processName}
     Package Version: {packageVersion}

     PEER REVIEW:
     Reviewed by: {peerReviewerName} ({peerReviewedBy})

     ADMIN DENIAL:
     Denied by: {adminUserName} ({adminUserEmail})
     Date: {deniedAt}

     REASON FOR DENIAL:
     {denialReason}

     ADMIN COMMENTS:
     {adminComments or "No additional comments."}

     Please address the issues mentioned and resubmit if needed.
     ```

4. **Refresh approval queue:**
   - Re-run `queryStatus` to update pending approvals list
   - Remove denied request from queue
   - Clear selected promotion
   - Collapse Promotion Detail Panel

4b. **Delete promotion branch:**
   - Call `DELETE /Branch/{branchId}` to clean up
   - `branchId` from `selectedPromotion.branchId`
   - Main branch remains untouched
   - Update PromotionLog: set `branchId` = null

5. **Show confirmation:**
   - "Deployment request denied. Submitter has been notified."

---

### Mapping Viewer Link

**Component Type:** Navigation link or button

**Configuration:**
- **Label:** "View Component Mappings"
- **Style:** Text link or secondary button
- **Icon (optional):** External link or grid icon
- **Location:** Top right of page or in navigation menu

**Behavior:**
- **On click:** Navigate to Page 8 (Mapping Viewer)
- Opens in same Flow application (not new tab)

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| "Deployment Approval Queue"        [View Component Maps] |
| Admin: {adminUserName} ({adminUserEmail})               |
+----------------------------------------------------------+
| MAIN AREA - TOP HALF                                     |
|                                                          |
|  Approval Queue Data Grid                                |
|  +----------------------------------------------------+  |
|  | Submitter | Process | Comps | Created | Submitted |  |
|  |--------------------------------------------------------|  |
|  | john@co   | Order P | 12    | 2/10    | 2h ago    |  |
|  | jane@co   | API Syn | 5     | 0/5     | 1d ago    |  |
|  | ...       | ...     | ...   | ...     | ...       |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
| MAIN AREA - BOTTOM HALF (expandable)                     |
|                                                          |
|  Promotion Detail Panel                                  |
|  +----------------------------------------------------+  |
|  | Submission Details                                  |  |
|  | Submitted by: john@company.com                      |  |
|  | Promotion ID: abc123-def456                         |  |
|  | Package Version: 1.2.3                              |  |
|  | Integration Pack: Order Management v3               |  |
|  | Target: Production                                  |  |
|  |                                                     |  |
|  | Promotion Results                                   |  |
|  | [Component results table]                           |  |
|  | Total: 12 | Created: 2 | Updated: 10               |  |
|  |                                                     |  |
|  | ⚠️ Credential Warning                              |  |
|  | • DB Connection needs reconfiguration              |  |
|  +----------------------------------------------------+  |
|                                                          |
|  Admin Comments                                          |
|  [_____________________________]                         |
|  [_____________________________]                         |
|                                                          |
+----------------------------------------------------------+
| FOOTER / ACTION BAR                                      |
| [Deny]                                  [Approve & Deploy]|
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- Page title: "Deployment Approval Queue"
- Admin user context: Display name and email
- "View Component Mappings" link in top right

**Main Area - Top Half:**
- Approval Queue Data Grid
- Full width
- Min height: 250px

**Main Area - Bottom Half:**
- Promotion Detail Panel (collapsible or side panel)
- Expandable: Opens when row selected, closes when deselected
- Full width (or 60% if side panel on desktop)
- Admin Comments textarea below detail panel

**Footer / Action Bar:**
- Fixed at bottom or below detail panel
- Deny button left-aligned (red)
- Approve button right-aligned (green)
- Only enabled when a request is selected

### Responsive Behavior

**Desktop (> 1024px):**
- Full table with all columns visible
- Detail panel below grid (or side panel on right)
- Buttons in footer bar

**Tablet (768px - 1024px):**
- Scroll table horizontally if needed
- Detail panel below grid
- Buttons full-width or centered

**Mobile (< 768px):**
- Card-based layout for approval queue
- Detail panel full-screen overlay
- Buttons stacked, full-width

## Accessibility

- **Keyboard navigation:** Tab through grid rows → detail panel → textarea → buttons
- **Screen reader:** Announce selected request, detail content, button states
- **Focus indicators:** Clear visual focus on selected row and focused buttons
- **ARIA labels:** Proper labels for grid, panel, textarea, buttons
- **Modal accessibility:** Focus trap in confirmation modals

## User Flow Example (Approval)

1. **Admin receives email notification**
   - Subject: "Promotion Approval Needed: Order Processing Main v1.2.3"
   - Clicks link in email

2. **Admin authenticates via SSO**
   - `ABC_BOOMI_FLOW_ADMIN` group membership validated
   - Redirected to Page 7

3. **Admin sees approval queue**
   - Grid shows 3 pending approval requests
   - Newest at top: "Order Processing Main" from john@company.com

4. **Admin selects first request**
   - Row highlights
   - Detail panel expands below grid
   - Shows: 12 components, 2 created, 10 updated, 3 need credentials

5. **Admin reviews details**
   - Reads deployment notes: "Deploy during maintenance window"
   - Reviews component list
   - Notes credential warning for DB Connection

6. **Admin adds comments**
   - Types: "Approved for Sunday 2am deployment. Please reconfigure DB connection credentials."

7. **Admin clicks "Approve and Deploy"**
   - Confirmation modal appears
   - Admin reviews summary: 12 components, Production target
   - Admin clicks "Confirm Approval"

8. **Deployment executes**
   - Modal closes
   - Page shows "Deploying..." spinner
   - `packageAndDeploy` Message step runs

9. **Deployment succeeds**
   - Success message: "Deployment approved and completed successfully!"
   - Deployment ID: xyz789-uvw012
   - Email sent to submitter

10. **Queue refreshes**
    - Request removed from pending list
    - Detail panel clears
    - Admin sees 2 remaining requests

## User Flow Example (Denial)

4. **Admin selects request**
   - Row highlights
   - Detail panel expands

5. **Admin reviews details**
   - Sees 5 components, all updates
   - Notes: "Emergency hotfix for API timeout"

6. **Admin clicks "Deny"**
   - Denial reason prompt appears
   - Admin types: "This should be deployed to UAT first for testing, not directly to Production."

7. **Admin confirms denial**
   - Clicks "Confirm Denial"
   - Email sent to submitter with denial reason

8. **Queue refreshes**
   - Request removed from pending list
   - Confirmation message: "Deployment request denied. Submitter has been notified."

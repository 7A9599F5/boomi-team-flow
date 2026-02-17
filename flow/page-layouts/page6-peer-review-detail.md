# Page 6: Peer Review Detail (Peer Review Swimlane)

## Overview

The Peer Review Detail page shows the full details of a promotion submission and allows the peer reviewer to approve or reject it. On approval, the promotion advances to the Admin Approval Queue (Page 7). On rejection, the submitter is notified and the flow ends.

## Page Load Behavior

1. **Pre-condition:** `selectedPeerReview` Flow value is populated (from Page 5 row selection)

2. **Display promotion details:**
   - Populate all sections from `selectedPeerReview` object
   - No additional message step needed (data already loaded from queryPeerReviewQueue response)

3. **Self-review guard (fallback):**
   - Decision step: `LOWERCASE($User/Email)` != `LOWERCASE(selectedPeerReview.initiatedBy)`
   - If equal: Navigate to Error Page with message "You cannot review your own submission"

## Components

### Promotion Detail Panel

**Component Type:** Full-page detail view

#### Section 1: Submission Details

**Submitter Information:**
- **Submitted by:** `{selectedPeerReview.initiatedBy}` (email and name)
- **Submitted at:** `{selectedPeerReview.initiatedAt}` (full timestamp)
- **Promotion ID:** `{selectedPeerReview.promotionId}` (with copy button)

**Package Information:**
- **Process Name:** `{selectedPeerReview.processName}`
- **Package Version:** `{selectedPeerReview.packageVersion}`
- **Dev Package ID:** `{selectedPeerReview.devPackageId}`

**Deployment Information:**
- **Integration Pack:** `{deploymentRequest.integrationPackName}` or "New: {newPackName}"
- **Target Account Group:** `{deploymentRequest.targetAccountGroupName}`

**Deployment Notes:**
- Display: `{deploymentRequest.notes}`
- Format: Plain text or markdown rendering
- Empty: "No notes provided"

---

#### Section 1b: Environment & Hotfix Information

**Deployment Target:**
- **Target Environment:** `{selectedPeerReview.targetEnvironment}` — Badge: "PRODUCTION" (blue)
- Note: Only production deployments reach peer review. Test deployments skip this step.

**Hotfix Information (conditional — shown when `isHotfix = "true"`):**
- **Badge:** "⚠ EMERGENCY HOTFIX" — large red badge
- **Justification:** `{selectedPeerReview.hotfixJustification}` (read-only, prominent display)
- **Warning text:** "This deployment bypasses the test environment. Please review carefully."
- **Styling:** Red background panel (#ffebee), red left border, warning icon

**Test Deployment History (conditional — shown when `testPromotionId` is populated):**
- **Header:** "Previously Tested"
- **Test Promotion ID:** `{selectedPeerReview.testPromotionId}` (with copy button)
- **Test Deployed Date:** `{selectedPeerReview.testDeployedAt}` (formatted)
- **Test Integration Pack:** `{selectedPeerReview.testIntegrationPackName}`
- **Styling:** Light green background (#e8f5e9), green left border, checkmark icon

---

#### Section 2: Promotion Results

**Summary:**
- **Total Components:** `{selectedPeerReview.componentsTotal}`
- **Created:** `{selectedPeerReview.componentsCreated}` (blue badge)
- **Updated:** `{selectedPeerReview.componentsUpdated}` (green badge)
- **Failed:** `{selectedPeerReview.componentsFailed}` (red badge, if > 0)

**Component Results Table:**
- Smaller data grid showing individual component results
- Columns:
  - Component Name
  - Type (badge)
  - Action (CREATE/UPDATE)
  - Status (SUCCESS/FAILED)
  - Config Stripped (Yes/No — warning icon)
  - Changes ("View Diff" link for UPDATE; "View New" for CREATE)
- Rows: All components from `selectedPeerReview.resultDetail` (parsed JSON)

---

#### Component Diff Panel

**Component Type:** Expandable panel (XmlDiffViewer custom component)

**Trigger:** When reviewer clicks "View Diff" or "View New" link in the component results table

**Location:** Expands inline below Section 2 table (between Section 2 and Section 3)

**Behavior:**
1. On click: Show loading spinner
2. Call `generateComponentDiff` message step with `branchId` from promotion data
3. On response: Render `XmlDiffViewer` with branch vs main XML
4. Max-height: 500px, scrollable
5. Close button (X) in top-right
6. Only one panel open at a time

**Purpose:** Enables peer reviewers to see the actual XML changes for each promoted component, not just metadata. This is the core review mechanism for the diff-based approval workflow.

---

#### Section 3: Credential Warning (Conditional)

**Visibility:** Shown if any component has `configStripped = true`

**Content:**
- Warning icon and title: "Credential Reconfiguration Required"
- List of components needing credential reconfiguration after deployment

---

#### Section 4: Source Account

**Dev Account Information:**
- **Source Account:** `{selectedPeerReview.devAccountName}` or `{selectedPeerReview.devAccountId}`
- **Account ID:** `{selectedPeerReview.devAccountId}`

---

### Peer Review Comments Textarea

**Component Type:** Textarea

**Configuration:**
- **Label:** "Peer Review Comments"
- **Placeholder:** "Add your review comments here..."
- **Required:** No for approval, Yes for rejection (see Reject button behavior)
- **Max length:** 500 characters
- **Rows:** 4

**Behavior:**
- **On change:** Store value in `peerReviewComments` Flow value
- **Character counter:** Show "X / 500 characters" below textarea

**Styling:**
- Full width or max 600px
- Located below Promotion Detail Panel

---

### Approve Button

**Component Type:** Button (Primary, Success)

**Configuration:**
- **Label:** "Approve — Send to Admin Review"
- **Style:** Large primary button
- **Color:** Green/success color
- **Icon (optional):** Checkmark icon
- **Size:** Large

**Confirmation Modal:**
- **Trigger:** On button click
- **Modal title:** "Confirm Peer Approval"
- **Modal content:**
  ```
  Are you sure you want to approve this promotion for admin review?

  Process: {processName}
  Package Version: {packageVersion}
  Total Components: {componentsTotal}
  Submitted by: {initiatedBy}

  After approval, this promotion will advance to the Admin Approval Queue
  for final review and deployment.
  ```
- **Buttons:**
  - "Cancel" (secondary, left)
  - "Confirm Approval" (primary green, right)

**Behavior on Confirm:**

1. **Close modal**

2. **Trigger Message step:** `submitPeerReview`
   - Input:
     - `promotionId`: `{selectedPeerReview.promotionId}`
     - `decision`: "APPROVED"
     - `reviewerEmail`: `{peerReviewerEmail}` (from `$User/Email`)
     - `reviewerName`: `{peerReviewerName}`
     - `comments`: `{peerReviewComments}` (optional)
   - Output:
     - `success`: boolean
     - `promotionId`: string
     - `newStatus`: "PEER_APPROVED"

3. **Decision step:** Check `{submitPeerReviewResponse.success} == true`
   - **True path:** Continue
   - **False path:** Show error (handle `SELF_REVIEW_NOT_ALLOWED`, `ALREADY_REVIEWED`, `INVALID_REVIEW_STATE`)

4. **Send email notifications:**
   - **To admins:** Subject: `"Peer Approved — Admin Review Needed: {processName} v{packageVersion}"`
   - **To submitter:** Subject: `"Peer Approved — Admin Review Needed: {processName} v{packageVersion}"`
   - Body includes peer reviewer info, promotion details, and link to admin approval queue

5. **Show success message:**
   ```
   Peer review approved!

   This promotion has been forwarded to the Admin Approval Queue.
   The submitter and admin team have been notified.

   Promotion ID: {promotionId}
   ```

6. **Transition to Admin Swimlane:**
   - Flow state transitions to Admin swimlane
   - Admin must authenticate with SSO (`ABC_BOOMI_FLOW_ADMIN` group) to continue to Page 7

---

### Reject Button

**Component Type:** Button (Danger, Secondary)

**Configuration:**
- **Label:** "Reject"
- **Style:** Medium button
- **Color:** Red/danger color
- **Icon (optional):** X icon
- **Size:** Medium

**Behavior on Click:**

1. **Show rejection reason modal:**
   - **Title:** "Reject Promotion"
   - **Field:** Textarea for rejection reason
     - Label: "Reason for Rejection"
     - Placeholder: "Explain why this promotion should not proceed..."
     - Required: Yes
     - Max length: 500 characters
   - **Buttons:**
     - "Cancel" (secondary, left)
     - "Confirm Rejection" (danger red, right)

2. **On confirm rejection:**

3. **Trigger Message step:** `submitPeerReview`
   - Input:
     - `promotionId`: `{selectedPeerReview.promotionId}`
     - `decision`: "REJECTED"
     - `reviewerEmail`: `{peerReviewerEmail}`
     - `reviewerName`: `{peerReviewerName}`
     - `comments`: `{rejectionReason}` (from modal textarea)
   - Output:
     - `success`: boolean
     - `promotionId`: string
     - `newStatus`: "PEER_REJECTED"

4. **Decision step:** Check success

5. **Send email notification to submitter:**
   - **To:** `{selectedPeerReview.initiatedBy}`
   - **Subject:** `"Peer Review Rejected: {processName} v{packageVersion}"`
   - **Body:** Includes rejection reason, reviewer info, and instructions to address feedback

6. **Show confirmation:**
   - "Promotion rejected. The submitter has been notified with your feedback."

6b. **Delete promotion branch:**
   - Call `DELETE /Branch/{branchId}` to clean up the promotion branch
   - `branchId` from `selectedPeerReview.branchId`
   - Main branch remains untouched
   - Update PromotionLog: set `branchId` = null

7. **End flow.**

---

### Back to Queue Button

**Component Type:** Navigation link or button

**Configuration:**
- **Label:** "Back to Peer Review Queue"
- **Icon (optional):** Left arrow icon
- **Location:** Top left of page

**Behavior:**
- **On click:** Navigate back to Page 5 (Peer Review Queue)

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| [← Back to Peer Review Queue]                            |
| "Peer Review Detail"                                     |
| Reviewer: {peerReviewerName} ({peerReviewerEmail})       |
+----------------------------------------------------------+
| MAIN AREA                                                |
|                                                          |
|  Submission Details                                      |
|  +----------------------------------------------------+  |
|  | Submitted by: john@company.com                      |  |
|  | Promotion ID: abc123-def456 [Copy]                  |  |
|  | Process: Order Processing Main                      |  |
|  | Package Version: 1.2.3                              |  |
|  | Integration Pack: Order Management v3               |  |
|  | Target: Production                                  |  |
|  | Notes: Deploy during maintenance window             |  |
|  +----------------------------------------------------+  |
|                                                          |
|  Promotion Results                                       |
|  +----------------------------------------------------+  |
|  | [Component results table]                           |  |
|  | Total: 12 | Created: 2 | Updated: 10               |  |
|  +----------------------------------------------------+  |
|                                                          |
|  Component Diff Panel (on "View Diff" click)             |
|  +----------------------------------------------------+  |
|  | XmlDiffViewer: branch vs main comparison            |  |
|  +----------------------------------------------------+  |
|                                                          |
|  Credential Warning (conditional)                        |
|  +----------------------------------------------------+  |
|  | Components needing reconfiguration                  |  |
|  +----------------------------------------------------+  |
|                                                          |
|  Source Account                                          |
|  +----------------------------------------------------+  |
|  | Dev Account: DevTeamAlpha (a1b2c3d4...)             |  |
|  +----------------------------------------------------+  |
|                                                          |
|  Peer Review Comments                                    |
|  [_____________________________]                         |
|  [_____________________________]                         |
|  [_____________________________]                         |
|  0 / 500 characters                                      |
|                                                          |
+----------------------------------------------------------+
| FOOTER / ACTION BAR                                      |
| [Reject]                     [Approve — Send to Admin]   |
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- "Back to Peer Review Queue" link in top left
- Page title: "Peer Review Detail"
- Reviewer context: Display name and email
- Subtitle: "2-Layer Approval — Step 1 of 2"

**Main Area:**
- Stacked detail sections (submission details, results, warnings, source account)
- Comments textarea below all detail sections
- Full width, max 900px centered

**Footer / Action Bar:**
- Fixed at bottom or below content
- Reject button left-aligned (red)
- Approve button right-aligned (green)

### Responsive Behavior

**Desktop (> 1024px):**
- Detail sections side-by-side where possible
- Centered content with max width
- Buttons in footer bar

**Tablet (768px - 1024px):**
- Detail sections stacked
- Buttons full-width or centered

**Mobile (< 768px):**
- All sections stacked, full-width
- Buttons stacked, full-width
- Reduce font sizes for compact display

## Accessibility

- **Keyboard navigation:** Tab through sections → textarea → buttons
- **Screen reader:** Announce section headings, content, button states
- **Focus indicators:** Clear visual focus on focused elements
- **ARIA labels:** Proper labels for all interactive elements
- **Modal accessibility:** Focus trap in confirmation/rejection modals

## User Flow Example (Approval)

1. **Reviewer arrives from Page 5**
   - Selected "Order Processing Main" from john@company.com
   - Detail page loads with full promotion information

2. **Reviewer examines details**
   - Reviews 12 components: 2 new, 10 updated
   - Notes credential warning for DB Connection
   - Reads deployment notes

3. **Reviewer adds comments**
   - Types: "Looks good. Verified dependency order is correct."

4. **Reviewer clicks "Approve — Send to Admin Review"**
   - Confirmation modal appears
   - Reviewer clicks "Confirm Approval"

5. **Approval succeeds**
   - Success message displayed
   - Email sent to admin group and submitter
   - Flow transitions to Admin swimlane

## User Flow Example (Rejection)

1. **Reviewer arrives from Page 5**
   - Selected "API Sync Process" from jane@company.com

2. **Reviewer identifies issue**
   - Notices missing error handling in one of the promoted components
   - Component results show all SUCCESS but reviewer knows there's a logic issue

3. **Reviewer clicks "Reject"**
   - Rejection reason modal appears
   - Types: "Missing retry logic on the API timeout handler. Please add exponential backoff before resubmitting."
   - Clicks "Confirm Rejection"

4. **Rejection succeeds**
   - Confirmation message displayed
   - Email sent to submitter with rejection reason
   - Flow ends

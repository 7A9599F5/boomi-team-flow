# Page 7: Admin Approval Queue (Admin Swimlane)

## Overview

The Admin Approval Queue is the final approval gate in the 2-layer approval workflow. Only promotions that have passed peer review (peerReviewStatus = PEER_APPROVED) appear in the Approval Queue tab. A second tab — Pack Assignment — shows PENDING_PACK_ASSIGNMENT promotions awaiting Integration Pack selection from an admin. Admins authenticate via SSO, review promotion details, select an Integration Pack, and execute deployment.

## Page Load Behavior

1. **Admin authentication:**
   - User must authenticate via SSO with `ABC_BOOMI_FLOW_ADMIN` group membership
   - If not authorized: Show error "Access denied. This page requires admin privileges."
   - Store admin user context: `adminUserName`, `adminUserEmail`

2. **Message step execution — Approval Queue:** `queryStatus`
   - Input:
     - `status` = "COMPLETED"
     - `deployed` = false
     - `reviewStage` = "PENDING_ADMIN_REVIEW"
   - Output: `pendingApprovals` array (promotions that have passed peer review and are awaiting admin approval)

3. **Message step execution — Integration Packs:** `listIntegrationPacks`
   - Called on page load with `packPurpose` = "MULTI" (standard deployment packs)
   - Output: `availableIntegrationPacks` array (for use in the IP selector on both tabs)

4. **Populate approval queue:**
   - Display pending approval requests in Data Grid under the "Approval Queue" tab
   - Sort by `initiatedAt` descending (newest first)

5. **Pack Assignment tab (lazy-loaded):**
   - On first switch to Pack Assignment tab: call `queryStatus` with `reviewStage = "PENDING_PACK_ASSIGNMENT"`
   - Output: `pendingPackAssignments` array
   - Update tab count badge with result count

6. **Error handling:**
   - If `queryStatus` or `listIntegrationPacks` fails → Navigate to Error Page

---

## Tab Navigation

**Component Type:** Tab bar / Tab group

**Location:** Below page header, above the main data grid

**Tabs:**

| Tab | Label | Default | Data Source |
|-----|-------|---------|-------------|
| 1 | Approval Queue | Yes (active on load) | `pendingApprovals` |
| 2 | Pack Assignment `(N)` | No | `pendingPackAssignments` (lazy) |

**Count Badge:**
- The "Pack Assignment" tab label includes a count badge: e.g., "Pack Assignment (3)"
- Badge updates after each successful pack assignment or queue refresh
- Badge shows 0 when pack assignment queue is empty

**Tab Switch Behavior:**
- Switching to "Pack Assignment": if not yet loaded, call `queryStatus` with `reviewStage = "PENDING_PACK_ASSIGNMENT"` and populate `pendingPackAssignments`
- Switching back to "Approval Queue": no reload unless stale (use cached `pendingApprovals`)
- Tab switch clears `selectedPromotion` and collapses detail panel

---

## Components

### Approval Queue Data Grid

**Component Type:** Data Grid / Table

**Visible When:** "Approval Queue" tab is active

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
  4. Reset IP Selector to default state (clear previously selected IP)
  5. Auto-populate IP suggestion if `listIntegrationPacks` returned a match for this `processName` + `targetEnvironment`

**Default Sort:**
- `initiatedAt` descending (newest submissions at top)

**Empty State:**
- Message: "No pending approvals"
- Submessage: "All deployment requests have been processed."
- Icon: Checkmark or empty inbox icon

**Pagination:**
- If > 25 requests: Enable pagination (25 rows per page)

---

### Pack Assignment Queue Data Grid

**Component Type:** Data Grid / Table

**Visible When:** "Pack Assignment" tab is active

**Data Source:**
- API: `queryStatus` with `reviewStage = "PENDING_PACK_ASSIGNMENT"` → `promotions` array
- Flow value: `pendingPackAssignments`

**Columns:**

| Column | Field | Width | Sortable | Formatting |
|--------|-------|-------|----------|------------|
| Process Name | `processName` | 20% | Yes | Bold text |
| Package Version | `packageVersion` | 12% | Yes | Monospace |
| Submitted By | `initiatedBy` | 15% | Yes | Email or name |
| Submitted At | `initiatedAt` | 15% | Yes | Date/time format |
| Target Environment | `targetEnvironment` | 15% | Yes | Badge: "PRODUCTION" blue |
| Components | `componentsTotal` | 8% | Yes | Numeric |
| Notes | `notes` | 15% | No | Truncated, tooltip |

**Row Selection:**
- **Mode:** Single-row selection
- **On select event:**
  1. Store selected record → `selectedPromotion` Flow value
  2. Expand Promotion Detail Panel below grid
  3. Reset IP Selector; auto-suggest if PromotionLog history match found
  4. Enable "Assign and Release" button

**Empty State:**
- Message: "No promotions awaiting pack assignment"
- Submessage: "All released promotions have been assigned to an Integration Pack."
- Icon: Package or checkmark icon

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

3. **Pack Assignment tab:** Self-approval prevention does NOT apply to pack assignment — the admin is assigning a pack to a previously approved promotion, not re-approving their own work.

---

### Promotion Detail Panel

**Component Type:** Expandable panel or side panel

**Trigger:** When a row is selected in either data grid

**Location:** Below the active grid (collapsible) or as a side panel (desktop)

**Content:**

#### Section 1: Submission Details

**Submitter Information:**
- **Submitted by:** `{initiatedBy}` (email and name)
- **Submitted at:** `{initiatedAt}` (full timestamp)
- **Promotion ID:** `{promotionId}` (with copy button)

**Deployment Information:**
- **Package Version:** `{deploymentRequest.packageVersion}`
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
- **Title:** "EMERGENCY HOTFIX"
- **Justification:** `{selectedPromotion.hotfixJustification}` — displayed prominently
- **Warning text:** "This is an emergency hotfix. Please review carefully."

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
The following components need credential reconfiguration:
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

#### Section 6: Integration Pack Selector

**Location:** Below Section 5 (Source Account), within the Promotion Detail Panel

**Visibility:** Always shown when a row is selected in either tab

See [Integration Pack Selector](#integration-pack-selector) below for full component specification.

---

### Integration Pack Selector

**Component Type:** Form group (Combobox + conditional fields + expandable panel)

**Usage:** Shown in the Promotion Detail Panel for both Approval Queue and Pack Assignment tabs. Required before the primary action button is enabled.

**Call on Display:** `listIntegrationPacks`
- Input: `packPurpose` = "MULTI" (or "HOTFIX" for the test IP selector on hotfix promotions)
- Output: `availableIntegrationPacks` array
- If already called on page load, use cached result; no duplicate call needed

#### IP Combobox

**Label:** "Integration Pack"

**Placeholder:** "Select or create an Integration Pack..."

**Options:**
1. **"+ Create New Integration Pack"** — special option, always shown at the top of the dropdown
2. Existing MULTI-type Integration Packs from `availableIntegrationPacks`

**Auto-Suggestion:**
- When a row is selected: query `availableIntegrationPacks` for a pack whose history matches `selectedPromotion.processName` + `selectedPromotion.targetEnvironment`
- If a match is found, pre-select it in the combobox
- Show "(suggested)" label next to the auto-selected pack name
- Admin can override by selecting a different option

**Behavior on Selection:**
- If "Create New Integration Pack" selected:
  - Show New Pack Name field and Description field
  - Set `createNewPack` = true
  - Hide current-packages panel
- If existing pack selected:
  - Set `selectedIntegrationPackId` = chosen pack ID
  - Set `createNewPack` = false
  - Show Current Packages expandable panel

#### Conditional: New Pack Fields (shown when "Create New" is selected)

**New Pack Name:**
- **Type:** Text input
- **Label:** "New Integration Pack Name"
- **Placeholder:** "e.g., Order Management Production"
- **Required:** Yes (when createNewPack = true)
- **Max length:** 100 characters
- **Stored in:** `newPackName` Flow value

**Description:**
- **Type:** Textarea
- **Label:** "Description"
- **Placeholder:** "Optional description for the new Integration Pack..."
- **Required:** No
- **Max length:** 250 characters
- **Rows:** 2
- **Stored in:** `newPackDescription` Flow value

#### Conditional: Current Packages Panel (shown when existing pack is selected)

**Component Type:** Expandable / collapsible panel

**Label:** "Current packages in this Integration Pack:"

**Default State:** Collapsed (show expand link)

**Expand Trigger:** Click on label or chevron icon

**Content:**
- Simple list of packages currently attached to the selected Integration Pack
- Data sourced from `selectedIntegrationPack.packages` (included in `listIntegrationPacks` response)
- Each list item shows: package name + version (e.g., "Order Processing Main v1.2.3")
- Empty state: "No packages currently in this Integration Pack."

**Example:**
```
Current packages in this Integration Pack:
  • Order Processing Main v1.2.3
  • Order Validation Process v0.9.1
  • Inventory Sync v2.0.0
```

#### Conditional: Test IP Selector (shown for hotfix promotions only)

**Visibility:** Only shown when `selectedPromotion.isHotfix = "true"`

**Label:** "Test Integration Pack (for sync)"

**Behavior:** Same as main IP selector — combobox with MULTI packs (using `packPurpose = "HOTFIX"` for the separate `listIntegrationPacks` call), "Create New" option, auto-suggestion, and current packages panel.

**Purpose:** Hotfix dual-release deploys to prod first, then syncs to test. The test IP selector provides the target for the test environment sync step.

**Fields stored:**
- `selectedTestIntegrationPackId`
- `createNewTestPack`
- `newTestPackName`
- `newTestPackDescription`

#### Enable Condition for Action Buttons

- **Approval Queue — "Approve and Deploy":**
  - `selectedPromotion` is not null
  - AND (`selectedIntegrationPackId` is set) OR (`createNewPack = true` AND `newPackName` is not empty)
  - AND (if hotfix): test IP also selected or createNewTestPack with name provided
  - AND self-approval check passes

- **Pack Assignment — "Assign and Release":**
  - `selectedPromotion` is not null
  - AND (`selectedIntegrationPackId` is set) OR (`createNewPack = true` AND `newPackName` is not empty)

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
- Located below Integration Pack Selector, within the detail panel area

---

### Approve Button (Approval Queue Tab)

**Component Type:** Button (Primary, Success)

**Configuration:**
- **Label:** "Approve and Deploy"
- **Style:** Large primary button
- **Color:** Green/success color
- **Icon (optional):** Checkmark icon
- **Size:** Large

**Enabled Condition:**
- IP selector is satisfied (see Enable Condition above)
- Self-approval check passes

**Confirmation Modal:**
- **Trigger:** On button click
- **Modal title:** "Confirm Approval"
- **Modal content:**
  ```
  Are you sure you want to approve and deploy this promotion?

  Process: {processName}
  Package Version: {packageVersion}
  Target Account Group: {targetAccountGroupName}
  Integration Pack: {selectedPackName} (or "New: {newPackName}")
  Total Components: {componentsTotal}

  This will package and deploy the promoted components to the target account group.
  ```
- **Buttons:**
  - "Cancel" (secondary, left)
  - "Confirm Approval" (primary green, right)

**Hotfix Confirmation (conditional — shown when `isHotfix = "true"`):**
- Additional warning text in modal: "This is an emergency hotfix."
- Extra checkbox (required): "I acknowledge this is an emergency hotfix"
- Checkbox must be checked before "Confirm Approval" button is enabled

**Behavior on Confirm:**

1. **Close modal**

2. **Trigger Message step:** `packageAndDeploy`
   - Input:
     - `promotionId` from `selectedPromotion.promotionId`
     - `integrationPackId` = `selectedIntegrationPackId` (if existing pack selected)
     - `createNewPack` = true/false
     - `newPackName` = `newPackName` (if createNewPack)
     - `newPackDescription` = `newPackDescription` (if createNewPack)
     - For hotfix: `testIntegrationPackId`, `createNewTestPack`, `newTestPackName`, `newTestPackDescription`
   - Process D handles: merging branch to main, creating PackagedComponent, assigning/creating Integration Pack, deploying to production

3. **Show deployment results inline:**
   - If success:
     - Show success message: "Packaged and deployed successfully to {targetAccountGroupName}!"
     - Display deployment ID and prod package ID
     - Display assigned Integration Pack name
   - If failure:
     - Show error message with details
     - Admin can retry

4. **Send email notification to submitter + peer reviewer** (handled by Process D)

5. **Refresh approval queue:**
   - Re-run `queryStatus` to update `pendingApprovals`
   - Clear `selectedPromotion`
   - Collapse detail panel
   - Clear IP selector state

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
- **Enabled when:** A request is selected (`selectedPromotion` not null) AND self-approval check passes
- **Disabled when:** No request selected or admin is the submitter

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

### Assign and Release Button (Pack Assignment Tab)

**Component Type:** Button (Primary, Success)

**Configuration:**
- **Label:** "Assign and Release"
- **Style:** Large primary button
- **Color:** Green/success color
- **Icon (optional):** Package icon
- **Size:** Large

**Enabled Condition:**
- IP selector is satisfied (existing pack selected OR createNewPack with name provided)

**Confirmation Modal:**
- **Trigger:** On button click
- **Modal title:** "Assign Integration Pack and Release?"
- **Modal content:**
  ```
  Assign Integration Pack and release this promotion?

  Process: {processName}
  Package Version: {packageVersion}
  Integration Pack: {selectedPackName} (or "New: {newPackName}")
  Target Environment: {targetEnvironment}
  ```
- **Buttons:**
  - "Cancel" (secondary, left)
  - "Assign and Release" (primary green, right)

**Behavior on Confirm:**

1. **Close modal**

2. **Trigger Message step:** `packageAndDeploy`
   - Input:
     - `promotionId` from `selectedPromotion.promotionId`
     - `integrationPackId` = `selectedIntegrationPackId` (if existing pack selected)
     - `createNewPack` = true/false
     - `newPackName` = `newPackName` (if createNewPack)
     - `newPackDescription` = `newPackDescription` (if createNewPack)
   - Process D detects PENDING_PACK_ASSIGNMENT status → executes Mode 4 (assign IP and release without re-merging)

3. **Show results inline:**
   - If success:
     - Show success message: "Assigned to {selectedPackName} and released successfully!"
     - Display release ID
   - If failure:
     - Show error message with details
     - Admin can retry

4. **Refresh pack assignment queue:**
   - Re-run `queryStatus` with `reviewStage = "PENDING_PACK_ASSIGNMENT"` to update `pendingPackAssignments`
   - Update tab count badge
   - Clear `selectedPromotion`
   - Collapse detail panel
   - Clear IP selector state

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
+------------------------------------------------------------------+
| HEADER                                                            |
| "Deployment Approval Queue"               [View Component Maps]  |
| Admin: {adminUserName} ({adminUserEmail})                        |
+------------------------------------------------------------------+
| TAB BAR                                                           |
| [Approval Queue]  [Pack Assignment (3)]                          |
+------------------------------------------------------------------+
| MAIN AREA - TOP HALF (active tab content)                        |
|                                                                  |
|  [Approval Queue Tab]                                            |
|  Approval Queue Data Grid                                        |
|  +--------------------------------------------------------------+|
|  | Submitter | Process | Comps | Created | Peer Reviewed | ...  ||
|  |--------------------------------------------------------------|
|  | john@co   | Order P | 12    | 2/10    | jane@co       | ...  ||
|  | jane@co   | API Syn | 5     | 0/5     | bob@co        | ...  ||
|  +--------------------------------------------------------------+|
|                                                                  |
|  [Pack Assignment Tab]                                           |
|  Pack Assignment Data Grid                                       |
|  +--------------------------------------------------------------+|
|  | Process Name | Package | Submitted By | Submitted At | ...   ||
|  |--------------------------------------------------------------|
|  | Inv Sync     | v1.0.0  | alice@co     | 2h ago       | ...   ||
|  +--------------------------------------------------------------+|
|                                                                  |
+------------------------------------------------------------------+
| MAIN AREA - BOTTOM HALF (expandable on row select)               |
|                                                                  |
|  Promotion Detail Panel                                          |
|  +--------------------------------------------------------------+|
|  | Section 1: Submission Details                                ||
|  | Submitted by: john@company.com | Promotion ID: abc123       ||
|  | Package Version: 1.2.3 | Target: Production                 ||
|  |                                                              ||
|  | Section 2: Peer Review Info                                  ||
|  | Reviewed by: jane@company.com | PEER_APPROVED               ||
|  |                                                              ||
|  | Section 3: Promotion Results                                 ||
|  | [Component results table]                                    ||
|  | Total: 12 | Created: 2 | Updated: 10                        ||
|  |                                                              ||
|  | Section 4: Credential Warning (conditional)                  ||
|  | Components needing reconfiguration                           ||
|  |                                                              ||
|  | Section 5: Source Account                                    ||
|  |                                                              ||
|  | Section 6: Integration Pack Selector                        ||
|  | [Select or create an Integration Pack...  v]                ||
|  | [> Current packages in this Integration Pack: (collapsed)]  ||
|  | (New pack fields shown if Create New selected)               ||
|  | (Test IP selector shown for hotfix promotions)               ||
|  +--------------------------------------------------------------+|
|                                                                  |
|  Admin Comments [__________________________________]             |
|                                                                  |
+------------------------------------------------------------------+
| FOOTER / ACTION BAR                                              |
| [Deny]                              [Approve & Deploy]           |
|                          -- OR (Pack Assignment tab) --          |
|                                    [Assign and Release]          |
+------------------------------------------------------------------+
```

### Layout Details

**Header:**
- Page title: "Deployment Approval Queue"
- Admin user context: Display name and email
- "View Component Mappings" link in top right

**Tab Bar:**
- Directly below header
- Two tabs: "Approval Queue" (default) and "Pack Assignment (N)"
- Active tab underlined or highlighted

**Main Area - Top Half:**
- Active tab's Data Grid
- Full width
- Min height: 250px

**Main Area - Bottom Half:**
- Promotion Detail Panel (collapsible or side panel)
- Expandable: Opens when row selected, closes when deselected
- Full width (or 60% if side panel on desktop)
- Integration Pack Selector embedded within detail panel (Section 6)
- Admin Comments textarea below detail panel

**Footer / Action Bar:**
- Fixed at bottom or below detail panel
- Approval Queue tab: Deny button left-aligned (red), Approve and Deploy button right-aligned (green)
- Pack Assignment tab: Assign and Release button right-aligned (green); no Deny button
- Only enabled when a request is selected and IP selector is satisfied

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

- **Keyboard navigation:** Tab through tab bar → grid rows → detail panel → IP selector → textarea → buttons
- **Screen reader:** Announce selected request, detail content, IP selector state, button states
- **Focus indicators:** Clear visual focus on selected row and focused buttons
- **ARIA labels:** Proper labels for tab bar, grids, panel, IP selector, textarea, buttons
- **Modal accessibility:** Focus trap in confirmation modals
- **Tab announcements:** Screen readers announce tab count badge changes when pack assignment queue updates

## User Flow Example (Approval)

1. **Admin receives email notification**
   - Subject: "Promotion Approval Needed: Order Processing Main v1.2.3"
   - Clicks link in email

2. **Admin authenticates via SSO**
   - `ABC_BOOMI_FLOW_ADMIN` group membership validated
   - Redirected to Page 7

3. **Admin sees Approval Queue tab (default)**
   - Grid shows 3 pending approval requests
   - Tab bar shows "Pack Assignment (2)" badge
   - Newest at top: "Order Processing Main" from john@company.com

4. **Admin selects first request**
   - Row highlights
   - Detail panel expands below grid
   - Shows: 12 components, 2 created, 10 updated, 3 need credentials
   - IP Selector pre-populated with suggested "Order Management v3" (from history)

5. **Admin reviews details**
   - Reads deployment notes: "Deploy during maintenance window"
   - Reviews component list
   - Notes credential warning for DB Connection
   - Expands "Current packages in this Integration Pack" — sees 2 existing packages

6. **Admin confirms IP selection and adds comments**
   - Accepts suggested Integration Pack or selects a different one
   - Types comment: "Approved for Sunday 2am deployment. Please reconfigure DB connection credentials."

7. **Admin clicks "Approve and Deploy"**
   - Confirmation modal appears
   - Admin reviews summary: 12 components, Production target, Integration Pack name
   - Admin clicks "Confirm Approval"

8. **Deployment executes**
   - Modal closes
   - Page shows "Deploying..." spinner
   - `packageAndDeploy` Message step runs (Process D handles merge, package, IP assignment, deploy)

9. **Deployment succeeds**
   - Success message: "Packaged and deployed successfully to Production!"
   - Deployment ID: xyz789-uvw012, Integration Pack: Order Management v3

10. **Queue refreshes**
    - Request removed from pending list
    - Detail panel clears
    - Admin sees 2 remaining requests

## User Flow Example (Pack Assignment)

1. **Admin switches to "Pack Assignment" tab**
   - Tab loads `queryStatus` with `reviewStage = "PENDING_PACK_ASSIGNMENT"`
   - Grid shows 2 promotions waiting for pack assignment

2. **Admin selects a record**
   - Row highlights
   - Detail panel expands: shows promotion details, promotion results
   - IP Selector shown in Section 6 with auto-suggestion

3. **Admin selects Integration Pack**
   - Chooses "Inventory Management v2" from dropdown
   - Expands current packages panel — sees 1 existing package

4. **Admin clicks "Assign and Release"**
   - Confirmation modal: "Assign Integration Pack and release?"
   - Admin confirms

5. **Release executes**
   - `packageAndDeploy` called with `promotionId` + `integrationPackId`
   - Process D detects PENDING_PACK_ASSIGNMENT → Mode 4

6. **Success**
   - Message: "Assigned to Inventory Management v2 and released successfully!"
   - Queue refreshes, tab badge count decrements to "(1)"

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

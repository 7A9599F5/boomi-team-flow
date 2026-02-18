# Page 3: Promotion Status (Developer Swimlane)

## Overview

The Promotion Status page displays the results of the promotion execution. It shows which components were successfully created/updated, which failed, and which need credential reconfiguration. Users can submit the promotion for deployment or end the flow.

## Direct Navigation Guard

Before any page content loads, a Decision step validates required Flow values:

- **Check:** `promotionId` is not null/empty
- **If missing:** Redirect to Page 1 (Package Browser) with toast message: "No active promotion"
- **If present:** Continue to page load behavior below

This prevents users from bookmarking or manually navigating to this page without an active promotion context.

## Page Load Behavior

1. **Arrival condition:** User navigates here after `executePromotion` Message step completes

2. **Flow Service async handling:**
   - Flow Service automatically sends wait responses during long-running promotion
   - User sees spinner/progress indicator during execution
   - State persisted via IndexedDB (cached every 30 seconds)
   - User CAN close browser and return later
   - On completion: Flow Service callback resumes the flow
   - If user returns to URL: Sees completed results

3. **Populate results:**
   - `promotionResults` Flow value contains array of component results
   - `promotionId` Flow value for audit reference
   - `componentsCreated`, `componentsUpdated`, `componentsFailed` counts

4. **Calculate summary counts:**
   - Total components = `promotionResults.length`
   - Created count = components where `action = "CREATE"`
   - Updated count = components where `action = "UPDATE"`
   - Failed count = components where `status = "FAILED"`
   - Config stripped count = components where `configStripped = true`

## Wait State (During Execution)

**Visual Display:**
- Page-level overlay or loading screen
- Large spinner/loading animation
- Progress message: "Promoting components to primary account..."
- Optional progress indicator:
  - "Processing component 5 of 12..."
  - Progress bar showing percentage (if API provides progress updates)
- Subtext: "This may take several minutes. You can safely close this window."

**State Persistence:**
- Flow Service caches state to IndexedDB every 30 seconds
- Includes: promotionId, request parameters, user context
- User can close browser window
- User can return to same URL later
- On return: Flow Service checks execution status and resumes

**User Experience:**
- User does NOT need to stay on page
- No "keep this window open" warnings needed
- Modern async experience

## Promotion Failed Banner

**Component Type:** Alert / Error panel

**Visibility:** Shown when `componentsFailed > 0` (i.e., the promotion has any failed components)

**Location:** Above the Results Data Grid, below the Summary Section

**Content:**

| Element | Details |
|---------|---------|
| **Icon** | Error/warning icon (red circle with X) |
| **Heading** | "Promotion Failed" |
| **Failure Count** | "{componentsFailed} of {totalComponents} component(s) failed" |
| **Explanation** | "The promotion branch has been deleted. No changes were applied to the production environment. Review the failure details below, resolve the underlying issues, and re-run the promotion from the Package Browser." |
| **Action Button** | "Return to Package Browser" → navigates to Page 1 |
| **Collapsible Section** | "Common Failure Causes" — expandable guide listing: API timeout (retry — transient network issue), component locked by another user (wait and retry), insufficient permissions (verify API credentials), component deleted since package creation (re-package from current components) |

**Styling:**
- Background: Light red (#ffebee)
- Border: Red left border (4px)
- Padding: 16px
- Action button: Secondary style, positioned at bottom of panel
- Collapsible section: Collapsed by default, toggle with chevron icon

---

## Components (After Completion)

### Results Data Grid

**Component Type:** Data Grid / Table

**Data Source:**
- API: `executePromotion` response → `results` array
- Flow value: `promotionResults`

**Columns:**

| Column | Field | Width | Sortable | Formatting |
|--------|-------|-------|----------|------------|
| Component | `name` | 25% | Yes | Plain text |
| Action | `action` | 10% | Yes | Badge: CREATE/UPDATE/SKIPPED |
| Status | `status` | 10% | Yes | Badge: SUCCESS/FAILED/SKIPPED |
| Prod Component ID | `prodComponentId` | 20% | No | Clickable link (optional) |
| Prod Version | `prodVersion` | 8% | Yes | Numeric |
| Config Stripped | `configStripped` | 10% | Yes | Checkmark/X icon |
| Error | `errorMessage` | 17% | No | Truncated, tooltip |
| Changes | — | 10% | No | "View Diff" link (UPDATE rows); "View New" (CREATE rows); hidden for SKIPPED/FAILED |

**Column Details:**

1. **Component**
   - Display: Component name (e.g., "Order Processing Main")
   - Format: Plain text, left-aligned
   - Sortable: Alphabetical

2. **Action**
   - Display: "CREATE", "UPDATE", or "SKIPPED"
   - Format: Badge/pill:
     - **CREATE:** Blue badge
     - **UPDATE:** Green badge
     - **SKIPPED:** Gray badge
     - **SKIPPED_CONNECTION:** Gray badge with "(shared)" text
     - **PRE_MAPPED:** Cyan badge — connection was pre-mapped and not promoted
   - Sortable: Alphabetical

3. **Status**
   - Display: "SUCCESS", "FAILED", or "SKIPPED"
   - Format: Badge/pill with color:
     - **SUCCESS:** Green badge with checkmark icon
     - **FAILED:** Red badge with X icon
     - **SKIPPED:** Gray badge
   - Sortable: By status (SUCCESS → SKIPPED → FAILED)

4. **Prod Component ID**
   - Display: Production component ID (GUID)
   - Format: Truncated to first 12 chars (e.g., "a1b2c3d4e5f6...")
   - Tooltip: Show full GUID on hover
   - Optional: Clickable link → opens component in Boomi UI (new tab)
   - Empty: "-" if action was SKIPPED or FAILED
   - Not sortable

5. **Prod Version**
   - Display: New version number in prod account
   - Format: Numeric text, centered
   - Empty: "-" if SKIPPED or FAILED
   - Sortable: Numeric order

6. **Config Stripped**
   - Display: Boolean indicating if credentials were removed
   - Format:
     - **True:** Warning icon (⚠️) with orange color, text "Yes"
     - **False:** Checkmark icon (✓) with green color, text "No"
   - Tooltip: "Credential configuration was removed for security"
   - Sortable: Boolean (Yes → No)

7. **Error**
   - Display: Error message if status = FAILED
   - Format: Red text, truncated to 50 chars
   - Tooltip: Show full error message on hover
   - Empty: "-" if SUCCESS or SKIPPED
   - Not sortable

8. **Changes**
   - Display: Clickable link to view component diff
   - Format:
     - **UPDATE rows:** "View Diff" link (blue text, underline)
     - **CREATE rows:** "View New" link (blue text, underline)
     - **SKIPPED/FAILED rows:** Hidden (no link)
   - **On click:** Calls `generateComponentDiff` message step with:
     - `branchId`: from `{branchId}` Flow value (returned by executePromotion)
     - `prodComponentId`: `{row.prodComponentId}`
     - `componentName`: `{row.name}`
     - `componentAction`: `{row.action}`
   - Shows XmlDiffViewer panel below the grid row (expandable, max-height 500px, scrollable)
   - Only one diff panel open at a time (clicking another row closes the previous)

**Row Styling:**
- **FAILED rows:** Red background color (light red, e.g., #ffebee)
- **SKIPPED rows:** Gray background color (light gray, e.g., #f5f5f5)
- **SUCCESS rows:** White/default background
- **Config stripped rows:** Small warning icon in row (in addition to column)

**Sorting:**
- Default sort: By dependency order (same as Page 2)
- User can sort by: Component name, Action, Status, Prod Version, Config Stripped

**Filters (Optional):**
- Quick filters above grid:
  - "Show All" (default)
  - "Show Failed Only"
  - "Show Config Stripped Only"

---

### Summary Section

**Component Type:** Info panel / Label group

**Location:** Above the Results Data Grid

**Content:**

1. **Promotion ID**
   - Text: `"Promotion ID: {promotionId}"`
   - Format: Monospace font, small text
   - Purpose: Audit trail reference
   - Copyable: Click to copy icon next to ID

2. **Created Count**
   - Text: `"Created: {componentsCreated}"`
   - Format: Badge/pill with blue background
   - Icon: Plus icon (+)
   - Only shown if > 0

3. **Updated Count**
   - Text: `"Updated: {componentsUpdated}"`
   - Format: Badge/pill with green background
   - Icon: Refresh icon
   - Only shown if > 0

4. **Failed Count**
   - Text: `"Failed: {componentsFailed}"`
   - Format: Badge/pill with red background
   - Icon: X icon
   - Only shown if > 0
   - Prominent warning styling

4b. **Branch Info**
   - Text: `"Branch: {branchName}"`
   - Format: Monospace font, small text
   - Purpose: Shows which branch components were promoted to
   - Only shown after successful promotion (when branchId is present)

5. **Connections Skipped Count**
   - Text: `"Connections (Shared): {connectionsSkipped}"`
   - Format: Badge/pill with cyan background
   - Icon: Link/chain icon
   - Always shown when `connectionsSkipped > 0`

**Layout:**
- Horizontal arrangement on desktop
- Wrap or stack on mobile
- Clear visual separation from grid (border or background)

---

### Credential Warning Box

**Component Type:** Alert / Warning panel

**Visibility:** Shown when any component has `configStripped = true`

**Content:**

**Header:**
- Icon: Warning icon (⚠️)
- Title: "Credential Reconfiguration Required"
- Color: Light yellow/amber background (less prominent — connections are now shared and pre-configured, reducing credential concerns)

**Body:**
```
The following components need credential reconfiguration in the primary account:

• DB Connection - MySQL Prod
• API Profile - Salesforce
• SFTP Connection - Legacy FTP

These components had their credentials removed for security reasons during promotion.
```

**List:**
- Bullet list of component names where `configStripped = true`
- Extracted from `promotionResults` where `configStripped = true`

**Instructions:**
```
To reconfigure:
1. Navigate to the Build tab in the primary Boomi account
2. Open each listed component
3. Enter the appropriate connection credentials
4. Test the connection and save
```

**Note:** Connection credentials are no longer affected by promotion. Connections are pre-configured as shared resources in the parent account's `#Connections` folder. Only non-connection components (e.g., custom properties, external endpoints) may need reconfiguration.

**Styling:**
- Border: Orange/yellow
- Background: Light orange/yellow (#fff4e5)
- Icon: Warning triangle
- Padding: 16px

---

### Component Diff Panel

**Component Type:** Expandable panel (XmlDiffViewer custom component)

**Trigger:** When user clicks "View Diff" or "View New" link in the Changes column

**Location:** Below the Results Data Grid (or inline below the clicked row)

**Behavior:**
1. On click: Show loading spinner in panel area
2. Call `generateComponentDiff` message step
3. On response: Render `XmlDiffViewer` custom component with response data
4. Panel is scrollable (max-height: 500px)
5. "Close" button (X) in top-right corner of panel
6. Only one panel open at a time

**Data Binding:**
- `branchXml`: from `generateComponentDiff` response
- `mainXml`: from `generateComponentDiff` response
- `componentName`: from response
- `componentAction`: from response
- `branchVersion`: from response
- `mainVersion`: from response

**Purpose:** Allows the developer to preview exactly what changed in each component before submitting for peer review. This helps catch issues early — before the peer reviewer even sees the promotion.

**Note:** Diff links are unavailable when `branchId` is absent (FAILED promotions delete the branch). Rows with FAILED or SKIPPED status already hide diff links per the per-component status rules in the Changes column.

---

### Deployment Target Selection

**Visibility:** Hidden when `componentsFailed > 0` — failed promotions cannot proceed to deployment. The entire Deployment Target section and Submit button are replaced by the Promotion Failed Banner above.

**Component Type:** Radio Button Group with conditional content

**Location:** Between the Component Diff Panel and the Submit button — this is the key decision point.

**Configuration:**

**Section Header:** "Deployment Target"

**Option 1 (Default):**
- **Radio label:** "Deploy to Test"
- **Badge:** "(Recommended)" green badge
- **Description text:** "Components will be deployed to your Test Integration Pack. No peer or admin review required. You can promote to production after validating in test."
- **On select:** Set `targetEnvironment = "TEST"`, `isHotfix = "false"`

**Option 2:**
- **Radio label:** "Deploy to Production (Emergency Hotfix)"
- **Badge:** "⚠ Emergency" red badge
- **Description text:** "WARNING: This will skip the test environment. Both peer review and admin review are still required. This exception will be logged for leadership review."
- **On select:** Set `targetEnvironment = "PRODUCTION"`, `isHotfix = "true"`
- **Conditional content (shown when selected):**
  - **Warning Banner:**
    - Background: Red/amber (#fff3e0 or #ffebee)
    - Icon: Warning triangle
    - Text: "Emergency hotfixes bypass the test environment. This action will be logged and flagged for leadership review. Both peer review and admin review are still required before deployment."
  - **Hotfix Justification Textarea:**
    - Label: "Hotfix Justification (Required)"
    - Placeholder: "Explain why this deployment must bypass the test environment..."
    - Required: Yes (when Emergency Hotfix is selected)
    - Max length: 1000 characters
    - Character counter: "X / 1000 characters"
    - On change: Store in `hotfixJustification` Flow value

**Default Selection:** "Deploy to Test" is pre-selected on page load.

**Styling:**
- Radio group with card-style options (each option in a bordered card)
- Default option has subtle green left border
- Emergency option has subtle red left border
- Conditional warning + textarea slides open with animation when emergency option selected

**Validation:**
- If "Emergency Hotfix" selected and `hotfixJustification` is empty → block submission with error "Hotfix justification is required"

---

### Submit for Deployment Button

**Component Type:** Button (Primary)

**Configuration:**
- **Label:** "Continue to Deployment"
- **Style:** Primary button (prominent)
- **Color:** Accent/success color
- **Icon (optional):** Right arrow or package icon
- **Size:** Large

**Note:** Button label is the same regardless of target environment selection. The deployment path diverges on Page 4.

**Enabled Condition:**
- **Enabled when:** `componentsFailed == 0` (all components succeeded)
- **Disabled when:** `componentsFailed > 0` (any component failed)

**Disabled State:**
- Grayed out, not clickable
- Tooltip: "Some components failed. Fix issues and re-run promotion before submitting for deployment."
- Alternative: Show warning message below button instead of tooltip

**Behavior:**
- **On click:**
  1. Navigate to Page 4 (Deployment Submission)
  2. Carry forward `promotionId` and `promotionResults` Flow values
  3. Pre-populate deployment form with promotion data

---

### Done Button

**Component Type:** Button (Secondary)

**Configuration:**
- **Label:** "Done"
- **Style:** Secondary button (less prominent)
- **Color:** Gray or default
- **Size:** Medium

**Behavior:**
- **On click:**
  1. End flow (return to start or exit)
  2. Show completion message (optional): "Promotion complete. You can close this window."
  3. Clear Flow values (optional, for cleanup)

**Always Available:**
- Not conditionally disabled
- User can exit at any time

---

### Release Propagation Status

**Visibility:** Only shown when the promotion has a `releaseId` in state (i.e., after a successful deployment).

**Component Type:** Status Card

**Configuration:**
- **Header:** "Release Propagation"
- **Auto-check:** On page load, if `releaseId` exists in state, automatically call `checkReleaseStatus` with `promotionId` and `releaseType = "ALL"`
- **Refresh button:** Manual "Check Status" button to re-poll

**Status Display:**

| Release Type | Status | Icon | Color |
|---|---|---|---|
| Production | PENDING | Clock | Gray |
| Production | IN_PROGRESS | Spinner | Blue |
| Production | COMPLETE | Checkmark | Green |
| Production | FAILED | X-circle | Red |
| Test | PENDING | Clock | Gray |
| Test | IN_PROGRESS | Spinner | Blue |
| Test | COMPLETE | Checkmark | Green |
| Test | FAILED | X-circle | Red |

**Fields shown per release:**
- Integration Pack Name
- Release Type (Production / Test)
- Status (with icon)
- Start Time
- Completion Time (or "Propagating..." if not complete)

**Behavior:**
- If status is PENDING or IN_PROGRESS, show info banner: "Releases can take up to 1 hour to propagate to all environments."
- If status is FAILED, show error banner: "Release propagation failed. Contact your Boomi administrator."
- If no releases found (non-deployed promotion), this section is hidden

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| "Promotion Results"                                      |
+----------------------------------------------------------+
| SUMMARY SECTION                                          |
| Promotion ID: abc123-def456-ghi789  [Copy]              |
| [Created: 2] [Updated: 10] [Failed: 0]                  |
| [Connections (Shared): 4]                                |
+----------------------------------------------------------+
| CREDENTIAL WARNING BOX (conditional)                     |
| ⚠️ Credential Reconfiguration Required                  |
| • DB Connection - MySQL Prod                             |
| • API Profile - Salesforce                               |
| Instructions: Navigate to Build tab...                   |
+----------------------------------------------------------+
| MAIN AREA                                                |
|                                                          |
|  Results Data Grid                                       |
|  +----------------------------------------------------+  |
|  | Component | Action | Status | Prod ID | Ver | Chg | ...|  |
|  |--------------------------------------------------------|  |
|  | Order Proc| UPDATE | ✓ SUC  | a1b2... | 6  | Diff| ...|  |
|  | DB Conn   | UPDATE | ✓ SUC  | c3d4... | 4  | Diff| ⚠️ |  |
|  | API Prof  | CREATE | ✓ SUC  | e5f6... | 1  | New | ...|  |
|  | ...       | ...    | ...    | ...     | ... | ... | ...|  |
|  +----------------------------------------------------+  |
|                                                          |
|  COMPONENT DIFF PANEL (expandable, on "View Diff" click)  |
|  +----------------------------------------------------+  |
|  | XmlDiffViewer: side-by-side XML comparison          |  |
|  | [Split | Unified] [Expand All] [Copy]               |  |
|  | LEFT (main) | RIGHT (branch)                        |  |
|  | max-height: 500px, scrollable                       |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
| FOOTER / ACTION BAR                                      |
| [Done]                [Submit for Integration Pack Deploy]|
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- Page title: "Promotion Results"
- Subheader (optional): "Process: {processName} v{packageVersion}"

**Summary Section:**
- Positioned above grid
- Horizontal badges on desktop, wrap on mobile
- Promotion ID at top left or above badges

**Credential Warning Box:**
- Positioned between summary and grid
- Full width
- Conditionally visible (only if any component has `configStripped = true`)

**Main Area:**
- Results Data Grid takes full width
- Responsive table with horizontal scroll on small screens
- Min height: 300px

**Footer / Action Bar:**
- Fixed at bottom or below grid
- Done button left-aligned
- Submit button right-aligned (only enabled if no failures)
- Clear visual separation from grid

### Responsive Behavior

**Desktop (> 1024px):**
- Full table with all columns visible
- Summary badges horizontal
- Buttons in footer bar

**Tablet (768px - 1024px):**
- Scroll table horizontally if needed
- Summary badges may wrap
- Buttons full-width or centered

**Mobile (< 768px):**
- Card-based layout for results
- Summary stacked vertically
- Buttons stacked, full-width
- Credential warning collapsible

## Error Handling

**If any components failed:**
- Failed count badge prominently displayed in red
- Failed rows highlighted in red in grid
- Error messages visible in Error column
- Submit for Deployment button disabled
- Show guidance message: "Fix the following issues and re-run promotion:"
  - List failed component names and error messages
  - Suggest: "Return to Package Browser to retry after fixing issues"

**Common failure scenarios:**
- API timeout (suggest retry)
- Missing dependencies (suggest reviewing dependency tree)
- Permission errors (suggest admin escalation)

## Accessibility

- **Keyboard navigation:** Tab through grid → buttons
- **Screen reader:** Announce summary counts, failed components, button states
- **Focus indicators:** Clear visual focus on buttons
- **ARIA labels:** Proper labels for grid, alerts, buttons
- **Color contrast:** Ensure red/green status colors have sufficient contrast

## User Flow Example

1. **User arrives at Page 3 after promotion execution**
   - Sees "Promoting components..." spinner
   - Wait state persisted, can close browser

2. **User returns 5 minutes later**
   - Page resumes automatically
   - Shows completed results

3. **Promotion completed successfully**
   - Grid shows 12 components: 2 created, 10 updated, 0 failed
   - Warning box shows 3 components need credential reconfiguration
   - Submit for Deployment button enabled

4. **User reviews results**
   - Sees DB Connection has config stripped warning
   - Notes error column is empty (no failures)
   - Copies Promotion ID for reference

5. **User clicks "Submit for Integration Pack Deployment"**
   - Navigation to Page 4
   - Deployment form pre-populated with promotion data

**Alternate flow (with failures):**

3. **Promotion completed with 1 failure**
   - Grid shows 11 success, 1 failed
   - Failed row highlighted in red
   - Error message: "API timeout: Connection to external service failed"
   - Submit for Deployment button disabled

4. **User reviews failure**
   - Sees which component failed
   - Reads error message
   - Decides to fix issue and re-run

5. **User clicks "Done"**
   - Returns to Package Browser (Page 1) to retry

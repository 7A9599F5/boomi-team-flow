# Page 9: Production Readiness Queue (Developer Swimlane)

## Overview

The Production Readiness Queue shows test deployments that are ready to be promoted to production. This page is the bridge between the test deployment phase and the production review workflow. Developers return here after validating components in the test environment, select a test deployment, and initiate the production promotion — which then follows the standard peer review → admin approval path.

## Navigation Entry Points

This page can be reached from:
- **Page 4 (Deployment Submission):** After a successful test deployment, via the "View in Production Readiness" button
- **Direct navigation:** From the dashboard sidebar/menu (always accessible to Developer swimlane users)
- **Page 1 (Package Browser):** Via a "Tested Deployments" link in the navigation header (if implemented)

No navigation guard is required for this page because it does not depend on prior page state. The page loads its own data independently via the `queryTestDeployments` message step.

## Page Load Behavior

1. **Authorization:** Same as Developer swimlane — SSO group "ABC_BOOMI_FLOW_CONTRIBUTOR" OR "ABC_BOOMI_FLOW_ADMIN"

2. **Message step execution:** `queryTestDeployments` (Process E4)
   - Input:
     - `devAccountId` = (optional, for filtering)
     - `initiatedBy` = (optional, for filtering)
   - Output: `testDeployments` array (TEST_DEPLOYED promotions not yet promoted to production)

3. **Populate queue:**
   - Display test deployments in Data Grid
   - Sort by `testDeployedAt` descending (most recently tested first)

4. **Error handling:**
   - If `queryTestDeployments` fails → Navigate to Error Page

## Components

### Production Readiness Data Grid

**Component Type:** Data Grid / Table

**Data Source:**
- API: `queryTestDeployments` response → `testDeployments` array
- Flow value: `testDeployments`

**Columns:**

| Column | Field | Width | Sortable | Formatting |
|--------|-------|-------|----------|------------|
| Process Name | `processName` | 18% | Yes | Bold text |
| Package Version | `packageVersion` | 10% | Yes | Plain text |
| Test Deployed | `testDeployedAt` | 14% | Yes | Date/time + relative age |
| Deployment Age | (calculated) | 10% | Yes | Days since `testDeployedAt` — amber if > 14 days, red if > 30 days |
| Components | `componentsTotal` | 8% | Yes | Numeric |
| Created/Updated | `componentsCreated` / `componentsUpdated` | 12% | Yes | "X new, Y updated" |
| Test Pack | `testIntegrationPackName` | 15% | No | Plain text |
| Submitted By | `initiatedBy` | 13% | Yes | Email or name |
| Release Status | (fetched via `checkReleaseStatus`) | 10% | No | Badge with icon — see detail below |

**Column Details:**

1. **Process Name**
   - Display: Root process name (e.g., "Order Processing Main")
   - Format: Bold text for emphasis
   - Sortable: Alphabetical

2. **Package Version**
   - Display: Package version string
   - Format: Plain text
   - Sortable: Alphabetical

3. **Test Deployed**
   - Display: Test deployment timestamp
   - Format: "YYYY-MM-DD HH:mm" with relative time in parentheses ("2 days ago")
   - Sortable: Chronological (default descending)

4. **Deployment Age**
   - Display: Number of days since test deployment
   - Format: Numeric with color coding:
     - **Green (0-14 days):** Normal — fresh test deployment
     - **Amber (15-30 days):** Warning — encourage timely production promotion
     - **Red (> 30 days):** Critical — test deployment approaching stale state
   - Tooltip: "Test deployments should be promoted to production in a timely manner"
   - Sortable: Numeric

5. **Components**
   - Display: Total component count
   - Format: Numeric text, centered
   - Sortable: Numeric

6. **Created/Updated**
   - Display: "X new, Y updated"
   - Format: Plain text or badges
   - Sortable: By total

7. **Test Pack**
   - Display: Test Integration Pack name
   - Format: Plain text
   - Not sortable

8. **Submitted By**
   - Display: Submitter email or name
   - Format: Plain text
   - Sortable: Alphabetical

#### Release Status Column (New)

**Column Header:** "Release Status"
**Position:** After the last existing column
**Data Source:** For each row, if `releaseId` exists, call `checkReleaseStatus` with `releaseType = "TEST"` (since this page shows test deployments ready for production)

**Display:**
- **No release:** Empty / dash
- **PENDING:** "Pending" (gray badge)
- **IN_PROGRESS:** "Propagating..." (blue badge with spinner)
- **COMPLETE:** "Complete" (green badge with checkmark)
- **FAILED:** "Failed" (red badge)

**Note:** Status is fetched on page load for all visible rows. A "Refresh All" button in the grid header re-checks all statuses.

**Row Selection:**
- **Mode:** Single-row selection
- **Visual:** Highlight selected row with accent color
- **On select event:**
  1. Store selected deployment → `selectedTestDeployment` Flow value
  2. Expand detail panel below grid

**Default Sort:**
- `testDeployedAt` descending (most recently tested first)

**Empty State:**
- Message: "No test deployments ready for production"
- Submessage: "Deploy components to a test environment first, then return here to promote to production."
- Icon: Rocket or test flask icon

**Pagination:**
- If > 25 records: Enable pagination (25 rows per page)

---

### Test Deployment Detail Panel

**Component Type:** Expandable panel below grid

**Trigger:** When a row is selected in the Production Readiness Data Grid

**Content:**

#### Promotion Details
- **Promotion ID:** `{selectedTestDeployment.promotionId}` (with copy button)
- **Process Name:** `{selectedTestDeployment.processName}`
- **Package Version:** `{selectedTestDeployment.packageVersion}`
- **Submitted by:** `{selectedTestDeployment.initiatedBy}`
- **Submitted at:** `{selectedTestDeployment.initiatedAt}` (formatted)

#### Test Deployment Info
- **Test Deployed:** `{selectedTestDeployment.testDeployedAt}` (formatted)
- **Test Integration Pack:** `{selectedTestDeployment.testIntegrationPackName}`
- **Branch:** Deleted after test packaging
- **Branch Status:** "Deleted — will be recreated from package for production merge"

#### Component Summary
- **Total:** `{selectedTestDeployment.componentsTotal}`
- **Created:** `{selectedTestDeployment.componentsCreated}` (blue badge)
- **Updated:** `{selectedTestDeployment.componentsUpdated}` (green badge)

---

### Promote to Production Button

**Component Type:** Button (Primary, Success)

**Configuration:**
- **Label:** "Promote to Production"
- **Style:** Large primary button
- **Color:** Green/success
- **Icon (optional):** Right arrow or rocket icon
- **Size:** Large

**Enabled Condition:**
- **Enabled when:** A test deployment is selected (`selectedTestDeployment` not null)
- **Disabled when:** No selection

**Behavior on Click:**
1. Set Flow values:
   - `testPromotionId` = `{selectedTestDeployment.promotionId}`
   - `targetEnvironment` = "PRODUCTION"
   - `isHotfix` = "false"
   - Carry forward: `promotionId`, `processName`, `packageVersion`, `componentsTotal`, `componentsCreated`, `componentsUpdated`
2. Navigate to Page 4 (Deployment Submission) — pre-filled for production mode

---

### Refresh Button

**Component Type:** Button (Secondary)

**Configuration:**
- **Label:** "Refresh"
- **Icon:** Refresh icon
- **Size:** Medium

**Behavior:**
- Re-execute `queryTestDeployments` message step
- Update grid with fresh data

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| "Production Readiness — Tested Deployments"              |
| [Refresh]                                                |
+----------------------------------------------------------+
| INFO BANNER                                               |
| "These deployments have been validated in test and are   |
|  ready for production. Select one to begin the peer      |
|  review and admin approval process."                     |
+----------------------------------------------------------+
| STALE DEPLOYMENT WARNING (conditional)                    |
| ⚠ "X deployments have been in test for over 30 days.    |
|  Consider promoting to production to keep queue current." |
+----------------------------------------------------------+
| MAIN AREA                                                |
|                                                          |
|  Production Readiness Data Grid                          |
|  +----------------------------------------------------+  |
|  | Process | Version | Tested | Age | Comps | Pack    |  |
|  |--------------------------------------------------------|
|  | Order P | 1.2.3   | Feb 14 | 2d  | 12    | Orders  |  |
|  | API Syn | 2.0.0   | Feb 10 | 6d  | 5     | API     |  |
|  | Legacy  | 1.0.1   | Jan 12 | 35d | 3     | Legacy  |  |
|  +----------------------------------------------------+  |
|                                                          |
|  Test Deployment Detail Panel (expandable)                |
|  +----------------------------------------------------+  |
|  | Promotion Details, Test Info, Component Summary     |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
| FOOTER / ACTION BAR                                      |
|                                [Promote to Production]    |
+----------------------------------------------------------+
```

### Stale Deployment Warning

**Note:** Test branches are automatically deleted after packaging. The stale deployment age indicator helps identify test deployments that have not been promoted to production. The age color coding in the grid (green/amber/red) still applies to the deployment age and should be used to encourage timely production promotion.

**Visibility:** Shown when any test deployment has `Deployment Age > 30 days`

**Content:**
- Warning icon and amber background
- Text: "{count} deployment(s) have been in test for over 30 days. Consider promoting to production to keep the queue current."
- "30-day threshold" is advisory, not enforced

### Layout Details

**Header:**
- Page title: "Production Readiness — Tested Deployments"
- Refresh button in top right

**Info Banner:**
- Light blue or info-colored background
- Brief instructions
- Dismissible (optional)

**Main Area:**
- Data Grid takes full width
- Detail panel expands below selected row
- Min height: 300px

**Footer / Action Bar:**
- "Promote to Production" button right-aligned
- Only enabled when selection is made

### Responsive Behavior

**Desktop (> 1024px):**
- Full table with all columns visible
- Detail panel below grid

**Tablet (768px - 1024px):**
- Horizontal scroll on table
- Detail panel below grid

**Mobile (< 768px):**
- Card-based layout
- Detail panel full-width
- Button full-width

## Accessibility

- **Keyboard navigation:** Tab through grid rows → detail panel → button
- **Screen reader:** Announce row details, branch age warnings, button state
- **Focus indicators:** Clear visual focus
- **ARIA labels:** Proper labels for grid, panel, buttons
- **Color contrast:** Ensure amber/red age indicators meet WCAG requirements

## User Flow Example

1. **Developer returns to dashboard after testing**
   - Navigates to "Tested Packages" / Production Readiness page

2. **Developer sees test deployments**
   - Grid shows 3 deployments: Order Processing (2 days), API Sync (6 days), Legacy (35 days - red)
   - Stale branch warning shows for Legacy deployment

3. **Developer selects Order Processing**
   - Detail panel expands showing test deployment info
   - "Promote to Production" button enabled

4. **Developer clicks "Promote to Production"**
   - Flow values set with test deployment info
   - Navigates to Page 4 (Deployment Submission)
   - Page 4 shows "Submit for Production Deployment" header
   - Test deployment summary panel visible

5. **Standard review flow continues**
   - Page 4 → Submit for Peer Review → Pages 5-6 → Page 7 → Deploy to Production

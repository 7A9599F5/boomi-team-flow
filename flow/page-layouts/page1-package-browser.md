# Page 1: Package Browser (Developer Swimlane)

## Overview

The Package Browser is the entry point for the developer flow. Users select a development account (if they have access to multiple) and browse available packages to promote.

## Page Load Behavior

1. **Message step execution:** `getDevAccounts`
   - Input: `userSsoGroups` from SSO authorization context
   - Output: `accessibleAccounts` list

2. **Store result:** `accessibleAccounts` Flow value

3. **Auto-selection logic:**
   - **If `accessibleAccounts.length == 1`:**
     - Automatically select the account
     - Set `selectedDevAccountId` and `selectedDevAccountName`
     - Hide Account Selector Combobox
     - Trigger Message step → `listDevPackages` immediately
   - **If `accessibleAccounts.length > 1`:**
     - Show Account Selector Combobox
     - Wait for user selection
     - Package grid shows empty state

3b. **Active promotions query:** 2 parallel `queryStatus` calls:
   - Call 1: `reviewStage = "PENDING_PEER_REVIEW"`
   - Call 2: `reviewStage = "PENDING_ADMIN_REVIEW"`
   - Filter results in Flow: keep only records where `initiatedBy.toLowerCase() == $User/Email.toLowerCase()`
   - Store filtered results → `activePromotions` Flow value

4. **Error handling:**
   - If `getDevAccounts` fails → Navigate to Error Page

## Components

### Your Active Promotions (Collapsible Panel)

**Component Type:** Collapsible panel / Accordion

**Visibility:**
- **Shown when:** `activePromotions` list is non-empty (at least one pending promotion by this user)
- **Hidden when:** `activePromotions` is empty (no pending promotions)

**Data Source:**
- Flow value: `activePromotions` (combined PENDING_PEER_REVIEW + PENDING_ADMIN_REVIEW records where `initiatedBy` matches current user)

**Default State:** Expanded (user sees their active promotions immediately)

**Grid Columns:**

| Column | Field | Width | Description |
|--------|-------|-------|-------------|
| Package Name | `processName` | 25% | Root process name from the promotion |
| Dev Account | `devAccountId` | 15% | Source dev account |
| Status | `peerReviewStatus` or `adminReviewStatus` | 15% | Badge: amber for PENDING_PEER_REVIEW, blue for PENDING_ADMIN_REVIEW |
| Submitted | `initiatedAt` | 15% | Relative date ("2 hours ago", "3 days ago") |
| Components | `componentsTotal` | 10% | Total component count |
| | | 20% | Withdraw button |

**Status Badges:**
- `PENDING_PEER_REVIEW` → Amber badge: "Awaiting Peer Review"
- `PENDING_ADMIN_REVIEW` → Blue badge: "Awaiting Admin Review"

**Withdraw Button:**
- **Label:** "Withdraw"
- **Style:** Destructive/danger (red outline or red text)
- **On click:**
  1. Show confirmation dialog:
     - Title: "Withdraw Promotion?"
     - Message: "This will cancel the promotion for **{processName}** and delete the promotion branch. This action cannot be undone."
     - Optional textarea: "Reason for withdrawal (optional)" — max 500 characters
     - Buttons: "Cancel" (secondary) | "Withdraw" (destructive/red)
  2. On confirm: Message step → `withdrawPromotion` with:
     - `promotionId` from the selected row
     - `initiatorEmail` from `$User/Email`
     - `reason` from the textarea (or empty string)
  3. On success:
     - Remove the row from `activePromotions` list
     - Show success toast: "Promotion withdrawn successfully"
     - Refresh the panel (re-query if needed)
  4. On failure:
     - Show error toast with `errorMessage`
     - Keep the row in place (do not remove)

**Empty State:**
- Panel is hidden entirely when no active promotions exist

---

### Account Selector (Combobox)

**Component Type:** Combobox (dropdown selector)

**Configuration:**
- **Label:** "Select Dev Account"
- **Data source:** `accessibleAccounts` list (from Flow value)
- **Display field:** `devAccountName`
- **Value field:** `devAccountId`
- **Placeholder:** "Choose a development account..."
- **Required:** Yes (when visible)

**Visibility:**
- **Hidden when:** `accessibleAccounts.length == 1`
- **Shown when:** `accessibleAccounts.length > 1`

**Behavior:**
- **On change event:**
  1. Store selected `devAccountId` → `selectedDevAccountId` Flow value
  2. Store selected `devAccountName` → `selectedDevAccountName` Flow value
  3. Trigger Message step → `listDevPackages` with `selectedDevAccountId`
  4. Show loading spinner on Packages Data Grid
  5. On response: populate grid with `packages` array

**Styling:**
- Full width or responsive (max 400px)
- Prominent placement at top of page

---

### Packages Data Grid

**Component Type:** Data Grid / Table

**Data Source:**
- API: `listDevPackages` response → `packages` array
- Flow value: Could be stored as `packagesList` for persistence

**Columns:**

| Column | Field | Width | Sortable | Default Sort |
|--------|-------|-------|----------|--------------|
| Package Name | `componentName` | 30% | Yes | No |
| Version | `packageVersion` | 15% | Yes | No |
| Type | `componentType` | 15% | Yes | No |
| Created | `createdDate` | 20% | Yes | Yes (descending) |
| Notes | `notes` | 20% | No | - |

**Column Details:**

1. **Package Name**
   - Display: Component name (e.g., "Order Processing Main")
   - Format: Plain text, left-aligned
   - Sortable: Alphabetical (A-Z, Z-A)

2. **Version**
   - Display: Package version (e.g., "1.2.3")
   - Format: Numeric text, centered
   - Sortable: Numeric order

3. **Type**
   - Display: Component type (e.g., "process", "connection")
   - Format: Badge/pill style with color coding
     - `process` → Blue
     - `connection` → Green
     - `map` → Purple
     - Other → Gray
   - Sortable: Alphabetical

4. **Created**
   - Display: Creation date/time
   - Format: "YYYY-MM-DD HH:mm" or relative time ("2 days ago")
   - Sortable: Chronological (newest first by default)
   - Default sort: Descending (most recent at top)

5. **Notes**
   - Display: Package notes/description
   - Format: Truncated text with ellipsis if > 100 chars
   - Tooltip: Show full text on hover
   - Not sortable

**Selection:**
- **Mode:** Single-row selection
- **Visual:** Highlight selected row with accent color
- **On select event:**
  1. Store entire selected row object → `selectedPackage` Flow value
  2. Store `selectedPackage.componentId` for next steps
  3. Store `selectedPackage.packageId` for next steps
  4. Enable "Review for Promotion" button

**Empty States:**

1. **No account selected:**
   - Message: "Select a dev account to view packages"
   - Icon: Folder icon
   - No data grid shown (or empty grid)

2. **No packages found:**
   - Message: "No packages found in this account"
   - Submessage: "Packages are created when you version components in the Build tab"
   - Icon: Empty box icon

3. **Loading:**
   - Show spinner/skeleton rows while `listDevPackages` executes
   - Message: "Loading packages..."

**Pagination:**
- If > 50 packages: Enable pagination (50 rows per page)
- Show row count: "Showing 1-50 of 234 packages"

**Search/Filter (Optional Enhancement):**
- Text search box above grid: "Search packages..."
- Filters: Package name, type
- Client-side filtering for responsiveness

---

### Review Button

**Component Type:** Button (Primary/Call-to-action)

**Configuration:**
- **Label:** "Review for Promotion"
- **Style:** Primary button (prominent, accent color)
- **Icon (optional):** Right arrow icon
- **Size:** Medium or large

**Enabled State:**
- **Enabled when:** `selectedPackage` is not null (a package row is selected)
- **Disabled when:** No package selected
- **Disabled style:** Grayed out, cursor not-allowed

**Behavior:**
- **On click event:**
  1. Validate `selectedPackage` exists (should always be true if button enabled)
  2. Store `selectedPackage.componentId` → Flow value (if not already stored)
  3. Store `selectedPackage.packageId` → Flow value (if not already stored)
  4. Navigate to Page 2 (Promotion Review)
  5. Page 2 will trigger `resolveDependencies` on load

**Validation:**
- Show tooltip on hover when disabled: "Select a package to review"

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| "Component Promotion Dashboard"                          |
| User: {userName} ({userEmail})                           |
+----------------------------------------------------------+
| YOUR ACTIVE PROMOTIONS (collapsible, hidden if empty)    |
| +------------------------------------------------------+ |
| | Package Name | Account | Status | Submitted | Action | |
| | Order Proc   | DevA    | Peer   | 2h ago    | [Withdraw]| |
| +------------------------------------------------------+ |
+----------------------------------------------------------+
| ACCOUNT SELECTOR ROW                                     |
| [Combobox: Select Dev Account ▼]   (conditional)        |
+----------------------------------------------------------+
| MAIN AREA                                                |
|                                                          |
|  Packages Data Grid                                      |
|  +----------------------------------------------------+  |
|  | Package Name | Version | Type | Created | Notes    |  |
|  |------------------------------------------------------|  |
|  | Order Proc   | 1.2.3   | Proc | 2026... | Main     |  |
|  | API Conn     | 2.0.0   | Conn | 2026... | Auth     |  |
|  | ...          | ...     | ...  | ...     | ...      |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
| FOOTER / ACTION BAR                                      |
|                                    [Review for Promotion]|
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- Fixed or sticky at top
- Application title: "Component Promotion Dashboard"
- User context: Display name and email from SSO
- Logout link (optional)

**Account Selector Row:**
- Conditionally visible (hidden when only 1 account)
- Full-width or centered (max 600px)
- Padding: 16px vertical

**Main Area:**
- Packages Data Grid takes full width
- Responsive: Adjust column widths on smaller screens
- Min height: 400px (to prevent layout jump on load)

**Footer / Action Bar:**
- Fixed at bottom or below grid
- Right-aligned button placement
- Padding: 16px
- Clear visual separation from grid (border or shadow)

### Responsive Behavior

**Desktop (> 1024px):**
- Full table with all columns visible
- Button in bottom-right corner

**Tablet (768px - 1024px):**
- Hide "Notes" column or make collapsible
- Button below grid, centered or right-aligned

**Mobile (< 768px):**
- Card-based layout instead of table
- Each package as a card with key info
- Tap card to select
- Button fixed at bottom of screen

## Error Handling

All pages in the Flow dashboard follow these error handling patterns:

- **Transient errors** (network timeout, HTTP 429 rate limit, 5xx server errors): Display an inline error banner with a "Retry" button that re-executes the failed Message step. Include the error code when available.
- **Permanent errors** (e.g., `COMPONENT_NOT_FOUND`, `MISSING_CONNECTION_MAPPINGS`, `BRANCH_LIMIT_REACHED`): Display the error details with a "Contact Admin" action and contextual recovery links — for example, a link back to the Package Browser for re-selection or the Status page for checking promotion progress.
- **Contextual recovery:** Every error state should offer at least one navigation path (e.g., "Return to Package Browser", "View Promotion Status") so users are never stranded on a dead-end error screen.

## Accessibility

- **Keyboard navigation:** Tab through combobox → grid rows → button
- **Screen reader:** Announce selected account, selected package, button state
- **Focus indicators:** Clear visual focus on selected row and focused button
- **ARIA labels:** Proper labels for combobox, grid, button

## User Flow Example

1. **User arrives at Page 1**
   - Sees "Loading..." while `getDevAccounts` executes
   - If 1 account: Auto-selected, packages load immediately
   - If multiple: Sees account dropdown

1b. **User sees active promotions panel** (if any)
   - Panel shows 1 promotion: "Order Processing v1.1.0" — Awaiting Peer Review (submitted 3 hours ago)
   - User can click "Withdraw" to cancel it, or ignore and continue browsing

2. **User selects account "Dev Team A"**
   - Dropdown value updates
   - Packages grid shows loading spinner
   - Grid populates with 15 packages

3. **User sorts by "Created" (newest first)**
   - Clicks "Created" column header
   - Grid reorders

4. **User selects package "Order Processing Main v1.2.3"**
   - Row highlights
   - "Review for Promotion" button enables
   - User sees button is now clickable

5. **User clicks "Review for Promotion"**
   - Navigation to Page 2
   - Page 2 begins loading dependency tree

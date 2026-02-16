# Page 2: Promotion Review (Developer Swimlane)

## Overview

The Promotion Review page displays a resolved dependency tree for the selected package, showing all components that will be created or updated in the primary account. Users review the impact and execute the promotion.

## Page Load Behavior

1. **Automatic Message step execution:** `resolveDependencies`
   - Input:
     - `selectedPackage.componentId`
     - `selectedDevAccountId`
   - Output:
     - `dependencyTree` (array of component objects)
     - `totalComponents` (integer)
     - `newCount` (integer)
     - `updateCount` (integer)
     - `envConfigCount` (integer)
     - `rootProcessName` (string)

2. **Store result:** `dependencyTree` Flow value

3. **Calculate summary counts:**
   - Components to create: `newCount`
   - Components to update: `updateCount`
   - Components with credentials: `envConfigCount`

4. **Display dependency tree:** Populate Data Grid with components

5. **Error handling:**
   - If `resolveDependencies` fails → Navigate to Error Page with message

## Components

### Dependency Tree Data Grid

**Component Type:** Data Grid / Table

**Data Source:**
- API: `resolveDependencies` response → `components` array
- Flow value: `dependencyTree`

**Columns:**

| Column | Field | Width | Sortable | Formatting |
|--------|-------|-------|----------|------------|
| Component Name | `name` | 25% | No | Bold for root process |
| Type | `type` | 12% | No | Badge/pill style |
| Dev Version | `devVersion` | 8% | No | Numeric |
| Prod Status | `prodStatus` | 12% | No | Color: Green=UPDATE, Blue=NEW |
| Prod Component | `prodComponentId` | 15% | No | Truncated GUID, tooltip for full |
| Prod Version | `prodCurrentVersion` | 8% | No | Numeric, "-" if NEW |
| Env Config | `hasEnvConfig` | 10% | No | Warning icon if true |

**Column Details:**

1. **Component Name**
   - Display: Component name (e.g., "Order Processing Main")
   - Format: Plain text, left-aligned
   - Special formatting: **Bold** for the root process (first row)
   - Not sortable (maintains dependency order)

2. **Type**
   - Display: Component type (e.g., "process", "connection", "map")
   - Format: Badge/pill with color coding:
     - `process` → Blue badge
     - `connection` → Green badge with "(shared)" suffix text (e.g., "connection (shared)")
     - `map` → Purple badge
     - `profile` → Orange badge
     - `operation` → Teal badge
   - Not sortable

3. **Dev Version**
   - Display: Version in dev account (e.g., "5")
   - Format: Numeric text, centered
   - Not sortable

4. **Prod Status**
   - Display: "NEW" or "UPDATE"
   - Format: Badge with color:
     - **NEW:** Blue badge (component doesn't exist in prod)
     - **UPDATE:** Green badge (component exists, will be updated)
     - **MAPPED:** Cyan badge (shared connection — mapping exists in DataHub, will not be promoted)
     - **UNMAPPED:** Red badge (shared connection — mapping missing, promotion will fail)
   - Not sortable

5. **Prod Component**
   - Display: Production component ID (GUID)
   - Format: Truncated to first 8 chars (e.g., "a1b2c3d4...")
   - Tooltip: Show full GUID on hover
   - Empty: "-" if status is NEW (no prod component yet)
   - Optional: Clickable link to open component in Boomi UI (new tab)
   - Not sortable

6. **Prod Version**
   - Display: Current version in prod account
   - Format: Numeric text, centered
   - Empty: "-" if status is NEW
   - Not sortable

7. **Env Config**
   - Display: `hasEnvConfig` boolean
   - Format:
     - **True:** Warning icon (⚠️) with orange color
     - **False:** Checkmark icon (✓) with gray/green color
   - Tooltip: "This component has environment-specific configuration that will need reconfiguration"
   - Not sortable

**Row Styling:**
- **Highlight rows with `hasEnvConfig=true`:** Yellow/orange background color
- **Root process (first row):** Slightly bolder or different background
- **Connection rows (shared):** Lighter background (e.g., #f0f7ff), italic text — visually distinct to indicate these components will NOT be promoted
- **Unmapped connection rows:** Light red background (e.g., #fff0f0), italic text — highlights missing mappings
- **Alternating row colors:** Light gray/white for readability

**Sorting:**
- **Pre-sorted by dependency order:**
  - Profiles first
  - Connections second
  - Operations third
  - Maps fourth
  - Processes last
- **Not user-sortable:** Maintains proper deployment order

**Empty State:**
- Should not occur (user selected a package on Page 1)
- If occurs: "No dependencies found. Please return to Package Browser."

---

### Summary Labels

**Component Type:** Text display / Info panel

**Location:** Above or below the Dependency Tree Data Grid

**Content:**

1. **Root Process Label**
   - Text: `"Root Process: {rootProcessName}"`
   - Format: Bold, large font (18-20px)
   - Color: Primary/accent color

2. **Total Components**
   - Text: `"Total Components: {totalComponents}"`
   - Format: Medium font (16px)
   - Color: Default text

3. **New Components Badge**
   - Text: `"{newCount} components to create"`
   - Format: Badge/pill with blue background
   - Icon: Plus icon (+)

4. **Update Components Badge**
   - Text: `"{updateCount} components to update"`
   - Format: Badge/pill with green background
   - Icon: Refresh/update icon

5. **Env Config Warning Badge**
   - Text: `"{envConfigCount} components with credentials to reconfigure"`
   - Format: Badge/pill with orange/warning background
   - Icon: Warning icon (⚠️)
   - Visibility: Only shown if `envConfigCount > 0`

6. **Shared Connections Badge**
   - Text: `"{sharedConnectionCount} shared connections (pre-mapped)"`
   - Format: Badge/pill with cyan background
   - Icon: Link/chain icon
   - Visibility: Always shown (even if 0, to clarify connections are handled separately)

7. **Unmapped Connections Warning Badge**
   - Text: `"{unmappedConnectionCount} connections missing mappings — promotion will fail"`
   - Format: Badge/pill with red/danger background
   - Icon: Error/X icon
   - Visibility: Only shown if `unmappedConnectionCount > 0`
   - Behavior: Draws immediate attention to blocking issue

**Layout:**
- Horizontal arrangement of badges/labels
- Wrap on smaller screens
- Clear visual hierarchy (root process most prominent)

---

### Promote Button

**Component Type:** Button (Primary/Prominent)

**Configuration:**
- **Label:** "Promote to Primary Account"
- **Style:** Large, prominent primary button
- **Color:** Success/accent color (green or blue)
- **Icon (optional):** Upload/arrow-up icon
- **Size:** Large

**Confirmation Modal:**
- **Trigger:** On button click
- **Modal title:** "Confirm Promotion"
- **Modal content:**
  ```
  Are you sure you want to promote this package?

  This will create/update {totalComponents} components in the primary account.

  Root Process: {rootProcessName}
  - {newCount} components to create
  - {updateCount} components to update
  - {envConfigCount} components will need credential reconfiguration
  Shared Connections: {sharedConnectionCount} (pre-mapped, will not be promoted)
  ```
- **Buttons:**
  - "Cancel" (secondary, left)
  - "Confirm Promotion" (primary, right)

**Behavior:**
- **On confirm:**
  1. Close modal
  2. Disable Promote button (show spinner inside button)
  3. Trigger Message step → `executePromotion` with:
     - `selectedPackage.componentId`
     - `selectedDevAccountId`
     - `dependencyTree`
  4. Show page-level loading state: "Promoting components... This may take several minutes."
  5. Flow Service handles async execution (automatic wait responses)
  6. On completion: Navigate to Page 3 (Promotion Status)

**Disabled State (During Execution):**
- Button shows spinner
- Label changes to "Promoting..."
- Button disabled (not clickable)
- User can close browser (state persisted, can return later)

**Disabled State (Unmapped Connections):**
- Button disabled (not clickable)
- Label remains "Promote to Primary Account"
- Tooltip: "Cannot promote — {unmappedConnectionCount} connection(s) missing mappings. Ask an admin to seed the missing mappings in the Mapping Viewer."
- Visual: Grayed out, same as during execution but without spinner

---

### Cancel Button

**Component Type:** Button (Secondary)

**Configuration:**
- **Label:** "Cancel"
- **Style:** Secondary button (less prominent)
- **Color:** Gray or default
- **Size:** Medium

**Behavior:**
- **On click:**
  1. Navigate back to Page 1 (Package Browser)
  2. Clear `selectedPackage` Flow value (optional)
  3. No confirmation required (no data loss)

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| "Review: Order Processing Main (v1.2.3)"                |
| "From: Dev Team A"                                       |
+----------------------------------------------------------+
| SUMMARY SECTION                                          |
| Root Process: Order Processing Main                     |
| Total Components: 12                                     |
| [2 to create] [10 to update] [3 with credentials]      |
| [4 shared connections (pre-mapped)]                      |
+----------------------------------------------------------+
| MAIN AREA                                                |
|                                                          |
|  Dependency Tree Data Grid                               |
|  +----------------------------------------------------+  |
|  | Component | Type | Dev V | Status | Prod ID | ... |  |
|  |--------------------------------------------------------|  |
|  | Order Proc| Proc | 5     | UPDATE | a1b2... | ... |  |
|  | DB Conn   |Conn(shared)| 3  | MAPPED | c3d4... |     |  |
|  | API Prof  | Prof | 2     | NEW    | -       | ... |  |
|  | ...       | ...  | ...   | ...    | ...     | ... |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
| FOOTER / ACTION BAR                                      |
| [Cancel]                      [Promote to Primary Acct] |
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- Page title: `"Review: {selectedPackage.componentName} (v{selectedPackage.packageVersion})"`
- Subheader: `"From: {selectedDevAccountName}"`
- Breadcrumb (optional): "Package Browser > Promotion Review"

**Summary Section:**
- Positioned above the grid
- Horizontal layout on desktop, stacked on mobile
- Clear visual separation (border or background color)

**Main Area:**
- Dependency Tree Data Grid takes full width
- Responsive table with horizontal scroll on small screens
- Min height: 300px

**Footer / Action Bar:**
- Fixed at bottom or below grid
- Cancel button left-aligned
- Promote button right-aligned
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
- Card-based layout for dependency tree
- Summary stacked vertically
- Buttons stacked, full-width

## Loading State

**During `resolveDependencies` execution:**
- Show page-level spinner or skeleton grid
- Message: "Analyzing dependencies..."
- Disable navigation (or show "Loading..." on buttons)

**During `executePromotion` execution:**
- Show page-level overlay with spinner
- Message: "Promoting components to primary account... This may take several minutes."
- Progress indicator (if available from API):
  - "Promoting component 5 of 12..."
  - Progress bar showing percentage complete
- User can close browser and return later (state persisted)

## Accessibility

- **Keyboard navigation:** Tab through grid → buttons
- **Screen reader:** Announce summary counts, grid contents, button states
- **Focus indicators:** Clear visual focus on buttons
- **ARIA labels:** Proper labels for grid, buttons, badges

## User Flow Example

1. **User arrives at Page 2 from Page 1**
   - Sees "Analyzing dependencies..." spinner
   - `resolveDependencies` executes

2. **Dependency tree loads**
   - Grid populates with 12 components
   - Summary shows: 2 new, 10 updates, 3 with credentials
   - Yellow highlight on 3 rows with credentials warning

3. **User reviews grid**
   - Sees root process "Order Processing Main" at top
   - Notes connection "DB Conn" has warning icon
   - Hovers over prod component ID to see full GUID

4. **User clicks "Promote to Primary Account"**
   - Confirmation modal appears
   - User reviews counts: 12 components total
   - User clicks "Confirm Promotion"

5. **Promotion executes**
   - Modal closes
   - Page shows overlay: "Promoting components..."
   - Progress: "Promoting component 3 of 12..."
   - User waits (or closes browser)

6. **Promotion completes**
   - Navigation to Page 3 (Promotion Status)
   - Results grid shows success/failure for each component

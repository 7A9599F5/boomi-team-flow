# Page 6: Mapping Viewer (Admin Swimlane)

## Overview

The Mapping Viewer page allows admins to view, search, filter, and manually manage ComponentMapping golden records. This page provides visibility into the mapping between developer account components and production account components, which is essential for tracking promotion history and troubleshooting issues.

## Page Load Behavior

1. **Admin authentication:**
   - User must be authenticated via SSO with "Boomi Admins" group membership
   - If not authorized: Show error "Access denied. This page requires admin privileges."

2. **Message step execution:** `manageMappings`
   - Input:
     - `operation` = "list"
     - Optional filters (if implemented): account, component type
   - Output: `mappings` array (all ComponentMapping records)

3. **Populate Mapping Data Grid:**
   - Display all mappings in Data Grid
   - Default sort: `lastPromotedAt` descending (most recently promoted first)

4. **Error handling:**
   - If `manageMappings` fails → Navigate to Error Page

## Components

### Mapping Data Grid

**Component Type:** Data Grid / Table

**Data Source:**
- API: `manageMappings` response → `mappings` array
- Flow value: `componentMappings`

**Columns:**

| Column | Field | Width | Sortable | Filterable | Formatting |
|--------|-------|-------|----------|------------|------------|
| Component Name | `componentName` | 20% | Yes | Yes (text) | Plain text |
| Type | `componentType` | 10% | Yes | Yes (dropdown) | Badge |
| Dev Account | `devAccountId` | 12% | Yes | Yes (dropdown) | Truncated, tooltip |
| Dev Component ID | `devComponentId` | 15% | No | No | Truncated, tooltip |
| Prod Component ID | `prodComponentId` | 15% | No | No | Truncated, tooltip |
| Prod Version | `prodLatestVersion` | 8% | Yes | No | Numeric |
| Last Promoted | `lastPromotedAt` | 12% | Yes | No | Date/time |
| Promoted By | `lastPromotedBy` | 8% | Yes | No | Email/name |

**Column Details:**

1. **Component Name**
   - Display: Component name (e.g., "Order Processing Main")
   - Format: Plain text, left-aligned
   - Sortable: Alphabetical (A-Z, Z-A)
   - Filterable: Text search (partial match, case-insensitive)

2. **Type**
   - Display: Component type (e.g., "process", "connection", "map")
   - Format: Badge/pill with color coding:
     - `process` → Blue
     - `connection` → Green
     - `map` → Purple
     - `profile` → Orange
     - `operation` → Teal
   - Sortable: Alphabetical
   - Filterable: Dropdown with options: All, process, connection, map, profile, operation

3. **Dev Account**
   - Display: Dev account ID (GUID)
   - Format: Truncated to first 8 chars (e.g., "a1b2c3d4...")
   - Tooltip: Show full GUID and account name on hover
   - Sortable: Alphabetical
   - Filterable: Dropdown populated with accessible dev accounts

4. **Dev Component ID**
   - Display: Dev component ID (GUID)
   - Format: Truncated to first 12 chars (e.g., "a1b2c3d4e5f6...")
   - Tooltip: Show full GUID on hover
   - Optional: Clickable link → opens component in Boomi UI (new tab)
   - Not sortable
   - Not filterable

5. **Prod Component ID**
   - Display: Prod component ID (GUID)
   - Format: Truncated to first 12 chars (e.g., "x7y8z9a0b1c2...")
   - Tooltip: Show full GUID on hover
   - Optional: Clickable link → opens component in Boomi UI (new tab)
   - Not sortable
   - Not filterable

6. **Prod Version**
   - Display: Latest version number in prod account (e.g., "5")
   - Format: Numeric text, centered
   - Sortable: Numeric order (descending by default = highest version first)
   - Not filterable

7. **Last Promoted**
   - Display: Timestamp of last promotion
   - Format: "YYYY-MM-DD HH:mm" or relative time ("2 days ago")
   - Sortable: Chronological (default descending = most recent first)
   - Not filterable (could add date range filter in future)

8. **Promoted By**
   - Display: Email or name of user who last promoted
   - Format: Truncated to 15 chars with ellipsis if needed
   - Tooltip: Show full email on hover
   - Sortable: Alphabetical
   - Not filterable

**Row Selection:**
- **Mode:** Single-row selection (optional, for edit functionality)
- **Visual:** Highlight selected row with accent color

**Default Sort:**
- `lastPromotedAt` descending (most recently promoted at top)

**Pagination:**
- **Page size:** 50 rows per page
- **Controls:** Previous/Next buttons, page number selector
- **Row count display:** "Showing 1-50 of 234 mappings"

**Empty State:**
- Message: "No component mappings found"
- Submessage: "Mappings are created automatically during component promotions."
- Icon: Empty database icon

---

### Filter Bar

**Component Type:** Filter controls above Data Grid

**Purpose:** Allow admins to quickly filter large mapping lists

**Components:**

1. **Component Type Filter**
   - Type: Dropdown
   - Label: "Type"
   - Options:
     - "All" (default)
     - "process"
     - "connection"
     - "map"
     - "profile"
     - "operation"
   - Behavior: On change, filter grid rows by `componentType`

2. **Dev Account Filter**
   - Type: Dropdown
   - Label: "Dev Account"
   - Options:
     - "All" (default)
     - List of accessible dev accounts (populated from API or cached list)
     - Display: Account name (if available) or truncated ID
   - Behavior: On change, filter grid rows by `devAccountId`

3. **Text Search**
   - Type: Text input
   - Label: "Search"
   - Placeholder: "Search by component name..."
   - Behavior: On input, filter grid rows by `componentName` (partial match, case-insensitive)
   - Debounce: 300ms delay after typing stops

4. **Apply Button**
   - Type: Button (primary, small)
   - Label: "Apply Filters"
   - Behavior: Apply all selected filters to grid
   - Optional: Auto-apply on change instead of button

5. **Clear Button**
   - Type: Button (secondary, small)
   - Label: "Clear"
   - Behavior: Reset all filters to defaults ("All", empty search)

**Layout:**
- Horizontal arrangement on desktop
- Wrap or stack on mobile
- Clear visual separation from grid (border or background)

---

### CSV Export Button

**Component Type:** Button (Secondary)

**Configuration:**
- **Label:** "Export to CSV"
- **Icon:** Download icon
- **Location:** Top right of Mapping Data Grid (above or to the right)

**Behavior:**
- **On click:**
  1. Export current filtered/sorted view of mappings to CSV file
  2. CSV includes all columns from grid
  3. Filename: `component-mappings-{date}.csv` (e.g., `component-mappings-2026-02-16.csv`)
  4. Download file to user's browser

**CSV Format:**
```csv
Component Name,Type,Dev Account,Dev Component ID,Prod Component ID,Prod Version,Last Promoted,Promoted By
Order Processing Main,process,a1b2c3d4-...,dev123-...,prod456-...,5,2026-02-15 14:30,john@company.com
API Connection,connection,a1b2c3d4-...,dev789-...,prod012-...,3,2026-02-14 09:15,jane@company.com
...
```

---

### Manual Mapping Form

**Component Type:** Collapsible form section

**Purpose:** Allow admins to manually create or edit mappings for edge cases (e.g., fixing incorrect mappings, creating mappings for components promoted outside the Flow)

**Visibility:** Collapsed by default, expandable via "Add/Edit Mapping" button or link

**Fields:**

1. **Dev Component ID**
   - Type: Text Input
   - Label: "Dev Component ID"
   - Placeholder: "Enter dev component GUID..."
   - Required: Yes
   - Max length: 40 characters (GUID length)
   - Validation: Valid GUID format

2. **Dev Account ID**
   - Type: Text Input or Dropdown
   - Label: "Dev Account ID"
   - Placeholder: "Enter dev account GUID..."
   - Required: Yes
   - Max length: 40 characters (GUID length)
   - Validation: Valid GUID format
   - Alternative: Dropdown of accessible dev accounts

3. **Prod Component ID**
   - Type: Text Input
   - Label: "Prod Component ID"
   - Placeholder: "Enter prod component GUID..."
   - Required: Yes
   - Max length: 40 characters (GUID length)
   - Validation: Valid GUID format

4. **Component Name**
   - Type: Text Input
   - Label: "Component Name"
   - Placeholder: "e.g., Order Processing Main"
   - Required: Yes
   - Max length: 200 characters

5. **Component Type**
   - Type: Dropdown
   - Label: "Component Type"
   - Options: process, connection, map, profile, operation
   - Required: Yes

6. **Prod Account ID** (pre-populated)
   - Type: Text Input (read-only or hidden)
   - Label: "Prod Account ID"
   - Value: Primary account ID (pre-populated from config)
   - Required: Yes
   - Disabled: Not editable (always primary account)

**Buttons:**

1. **Save Button**
   - Type: Button (primary)
   - Label: "Save Mapping"
   - Validation: Check all required fields filled and valid
   - Behavior:
     - Trigger Message step → `manageMappings` with:
       - `operation` = "create" (if new) or "update" (if editing)
       - `mapping` object with form values
     - On success:
       - Refresh Mapping Data Grid
       - Collapse form
       - Show success message: "Mapping saved successfully"
     - On error:
       - Show error message: `{errorMessage}`
       - Keep form open for correction

2. **Cancel Button**
   - Type: Button (secondary)
   - Label: "Cancel"
   - Behavior: Collapse form, clear fields

**Validation:**
- **Uniqueness:** Dev Component ID + Dev Account ID must be unique (no duplicate mappings)
- **GUID format:** Dev/Prod Component IDs must be valid GUIDs
- **Required fields:** All fields except Prod Account ID (pre-populated)

**Use Cases:**
- Admin needs to manually map a component promoted outside Flow
- Admin needs to fix an incorrect mapping (wrong prod component ID)
- Admin needs to create mapping for retroactive component promotion tracking

---

### Back to Approvals Link

**Component Type:** Navigation link or button

**Configuration:**
- **Label:** "Back to Approval Queue"
- **Icon (optional):** Left arrow icon
- **Location:** Top left or bottom left of page

**Behavior:**
- **On click:** Navigate back to Page 5 (Approval Queue)
- Opens in same Flow application (not new tab)

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| [← Back to Approval Queue]                               |
| "Component Mapping Viewer"                               |
| Admin: {adminUserName}                                   |
+----------------------------------------------------------+
| FILTER BAR                                               |
| Type: [All ▼]  Dev Acct: [All ▼]  Search: [______]      |
| [Apply] [Clear]                              [Export CSV]|
+----------------------------------------------------------+
| MAIN AREA                                                |
|                                                          |
|  Mapping Data Grid                                       |
|  +----------------------------------------------------+  |
|  | Comp Name | Type | Dev Acct | Dev ID | Prod ID | ...|  |
|  |--------------------------------------------------------|  |
|  | Order Proc| Proc | a1b2...  | dev... | prod... | ...|  |
|  | API Conn  | Conn | a1b2...  | dev... | prod... | ...|  |
|  | ...       | ...  | ...      | ...    | ...     | ...|  |
|  +----------------------------------------------------+  |
|  Showing 1-50 of 234 mappings        [Prev] [1] [2] [Next]|
|                                                          |
+----------------------------------------------------------+
| MANUAL MAPPING FORM (collapsible)                        |
| [+ Add/Edit Mapping] (collapsed)                         |
|                                                          |
| (When expanded:)                                         |
| +----------------------------------------------------+   |
| | Dev Component ID: [__________________]             |   |
| | Dev Account ID:   [__________________]             |   |
| | Prod Component ID:[__________________]             |   |
| | Component Name:   [__________________]             |   |
| | Component Type:   [process ▼]                      |   |
| | [Cancel] [Save Mapping]                            |   |
| +----------------------------------------------------+   |
|                                                          |
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- "Back to Approval Queue" link in top left
- Page title: "Component Mapping Viewer"
- Admin user context: Display name
- Breadcrumb (optional): "Approval Queue > Mapping Viewer"

**Filter Bar:**
- Horizontal arrangement on desktop
- Filters left-aligned, Export CSV button right-aligned
- Wrap or stack filters on mobile
- Clear visual separation from grid (border or background)

**Main Area:**
- Mapping Data Grid takes full width
- Responsive table with horizontal scroll on small screens
- Pagination controls below grid

**Manual Mapping Form:**
- Collapsed by default
- Expandable via toggle button/link
- Full width when expanded
- Clear visual separation (border, background color)
- Located below grid

### Responsive Behavior

**Desktop (> 1024px):**
- Full table with all columns visible
- Filter bar horizontal
- Export CSV button right-aligned

**Tablet (768px - 1024px):**
- Scroll table horizontally if needed
- Filter bar may wrap
- Export button below filters or right-aligned

**Mobile (< 768px):**
- Card-based layout for mappings (alternative to table)
- Filter bar stacked vertically
- Export button full-width
- Manual form full-screen overlay

## Data Operations

### List Mappings (Default)

**Operation:** `manageMappings` with `operation = "list"`

**Request:**
```json
{
  "operation": "list",
  "filters": {
    "componentType": "process",
    "devAccountId": "a1b2c3d4-..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "mappings": [
    {
      "componentName": "Order Processing Main",
      "componentType": "process",
      "devAccountId": "a1b2c3d4-...",
      "devComponentId": "dev123-...",
      "prodAccountId": "prod-primary-...",
      "prodComponentId": "prod456-...",
      "prodLatestVersion": 5,
      "lastPromotedAt": "2026-02-15T14:30:00Z",
      "lastPromotedBy": "john@company.com"
    },
    ...
  ]
}
```

---

### Create Mapping (Manual)

**Operation:** `manageMappings` with `operation = "create"`

**Request:**
```json
{
  "operation": "create",
  "mapping": {
    "componentName": "New API Connection",
    "componentType": "connection",
    "devAccountId": "a1b2c3d4-...",
    "devComponentId": "dev999-...",
    "prodAccountId": "prod-primary-...",
    "prodComponentId": "prod888-...",
    "lastPromotedBy": "admin@company.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Mapping created successfully",
  "mappingId": "mapping123-..."
}
```

---

### Update Mapping (Manual)

**Operation:** `manageMappings` with `operation = "update"`

**Request:**
```json
{
  "operation": "update",
  "mappingId": "mapping123-...",
  "mapping": {
    "prodComponentId": "prod777-...",
    "prodLatestVersion": 6
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Mapping updated successfully"
}
```

---

### Delete Mapping (Manual)

**Operation:** `manageMappings` with `operation = "delete"`

**Request:**
```json
{
  "operation": "delete",
  "mappingId": "mapping123-..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Mapping deleted successfully"
}
```

## Accessibility

- **Keyboard navigation:** Tab through filters → grid rows → form fields → buttons
- **Screen reader:** Announce filter changes, grid contents, form field labels, button states
- **Focus indicators:** Clear visual focus on focused elements
- **ARIA labels:** Proper labels for filters, grid, form, buttons
- **Modal accessibility:** Focus trap in expanded manual form (if modal)

## User Flow Example

1. **Admin navigates to Page 6 from Page 5**
   - Clicks "View Component Mappings" link
   - Page loads with "Loading mappings..." spinner

2. **Mappings load**
   - Grid populates with 234 component mappings
   - Default sort: Most recently promoted first
   - Pagination: Showing 1-50 of 234

3. **Admin applies filters**
   - Type: "connection"
   - Dev Account: "Dev Team A"
   - Search: "API"
   - Clicks "Apply"

4. **Grid updates**
   - Shows 8 matching mappings
   - All connections from Dev Team A with "API" in name

5. **Admin exports to CSV**
   - Clicks "Export to CSV"
   - File downloads: `component-mappings-2026-02-16.csv`
   - Contains 8 filtered rows

6. **Admin manually creates mapping**
   - Clicks "Add/Edit Mapping"
   - Form expands
   - Fills in fields:
     - Dev Component ID: `dev-abc123-...`
     - Dev Account ID: `a1b2c3d4-...`
     - Prod Component ID: `prod-xyz789-...`
     - Component Name: "Legacy SFTP Connection"
     - Component Type: "connection"
   - Clicks "Save Mapping"

7. **Mapping saves**
   - Success message: "Mapping saved successfully"
   - Form collapses
   - Grid refreshes, new mapping appears at top

8. **Admin returns to approvals**
   - Clicks "Back to Approval Queue"
   - Navigates to Page 5

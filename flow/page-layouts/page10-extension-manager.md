# Page 10: Extension Manager (Developer + Admin Swimlane)

## Overview

The Extension Manager provides a general-purpose interface for viewing and editing Boomi Environment Extensions across client accounts and environments. It is accessible from all swimlanes (Developer and Admin) and is always reachable from the dashboard sidebar regardless of prior navigation state. The page loads available client accounts on entry, prompts the user to select an account and environment, then delegates all editing interaction to the `ExtensionEditor` custom React component. Developers can edit process properties, operation settings, and cross-reference overrides in the test environment; administrators additionally have access to connection extensions and a cache rebuild utility.

## Navigation Entry Points

This page can be reached from:
- **Dashboard sidebar/menu:** Direct navigation link always visible to authorized users, from any page in any swimlane
- **Any page with an "Extension Manager" link:** Other pages may surface a shortcut link to this page

No navigation guard is required because the page loads its own data independently via the `listClientAccounts` message step. It does not depend on prior page state.

## Page Load Behavior

1. **Authorization:** SSO group "ABC_BOOMI_FLOW_CONTRIBUTOR" OR "ABC_BOOMI_FLOW_ADMIN"

2. **Message step execution:** `listClientAccounts` (Process K)
   - Input:
     - `userSsoGroups` (from user context)
   - Output: `clientAccounts` array, each entry containing:
     - `clientAccountId`
     - `clientAccountName`
     - `testEnvironmentId`
     - `prodEnvironmentId`

3. **Populate account selector:**
   - Populate Account Selector dropdown with `clientAccounts` data
   - Sort accounts alphabetically by `clientAccountName`

4. **Auto-select single account:**
   - If `clientAccounts` contains exactly one entry, auto-select it and immediately populate the Environment Selector
   - If multiple accounts exist, leave Account Selector blank until user selects

5. **Error handling:**
   - If `listClientAccounts` fails → Show error banner with "Failed to load client accounts. Please try again." and a Retry button that re-executes the message step

### After Account + Environment Selection

Once both Account Selector and Environment Selector have values:

1. **Message step execution:** `getExtensions` (Process L)
   - Input:
     - `clientAccountId` (from Account Selector)
     - `environmentId` (from Environment Selector)
     - `userSsoGroups` (from user context)
     - `userEmail` (from user context)
   - Output:
     - `extensionData` (JSON string — full extension tree for selected environment)
     - `accessMappings` (JSON string — per-extension edit permission map)
     - `extensionCounts` (object with counts by category)

2. **Pass data to ExtensionEditor component:**
   - Bind `extensionData` and `accessMappings` to the ExtensionEditor custom component inputs
   - ExtensionEditor renders tree navigation, property table, search, and undo/redo internally

3. **Error handling:**
   - If `getExtensions` fails → Display error message inside the ExtensionEditor component area: "Failed to load extensions. {errorCode}: {errorMessage}"
   - Show Retry button that re-executes `getExtensions` with the current account and environment selection

## Components

### Account Selector

**Component Type:** Dropdown (single-select)

**Data Source:**
- API: `listClientAccounts` response → `clientAccounts` array
- Flow value: `clientAccounts`

**Configuration:**
- Display field: `clientAccountName`
- Value field: `clientAccountId`
- Placeholder: "Select a client account..."
- Disabled until `listClientAccounts` response is received

**Behavior on Change:**
- Store selected account ID → `selectedClientAccountId` Flow value
- Store selected account name → `selectedClientAccountName` Flow value
- Populate Environment Selector with test and production environments for the selected account
- Clear any previously loaded extension data and reset ExtensionEditor

---

### Environment Selector

**Component Type:** Dropdown (single-select)

**Data Source:**
- Derived from selected client account record: `testEnvironmentId`, `prodEnvironmentId`
- Static display labels: "Test Environment" / "Production Environment"

**Configuration:**
- Options:
  - `{ label: "Test Environment", value: testEnvironmentId }`
  - `{ label: "Production Environment", value: prodEnvironmentId }`
- Placeholder: "Select an environment..."
- Disabled until an account is selected

**Behavior on Change:**
- Store selected environment ID → `selectedEnvironmentId` Flow value
- Store environment label → `selectedEnvironmentName` Flow value
- Trigger `getExtensions` message step with current account and new environment selection
- Clear any previously loaded extension data and reset ExtensionEditor

---

### ExtensionEditor

**Component Type:** Custom Component

**Component Name:** `ExtensionEditor`

**Data Bindings (inputs):**
- `extensionData` — JSON string of the full extension tree for the selected environment
- `accessMappings` — JSON string mapping extension IDs to edit permission flags

**Outcomes:**
- **"Save"** outcome → triggers `updateExtensions` message step (Process M)
  - Input: `clientAccountId`, `environmentId`, `extensionData` (modified), `userSsoGroups`, `userEmail`
  - On success: show Save Success Toast; refresh `extensionData` Flow value with returned data
  - On failure: show Save Error Banner
- **"CopyTestToProd"** outcome → set `testEnvironmentId`, `testEnvironmentName`, `prodEnvironmentId`, `prodEnvironmentName`, and `extensionData` Flow values, then navigate to Page 11 (Extension Copy Confirmation)

**Internal Behavior (managed by the component):**
- Tree navigation panel: browse extensions by category (Process Properties, Operations, Connections, Cross References, PGP Certificates)
- Property table: display and edit individual extension field values
- Search: filter extensions by name or value across all categories
- Undo/redo: track local edit history before saving
- Diff indicators: highlight fields changed from saved state

**Admin-Specific Behavior:**
- Admin users (SSO group "ABC_BOOMI_FLOW_ADMIN") see Connection extensions as editable
- Admin users see a "Rebuild Cache" button in the component toolbar
  - Clicking "Rebuild Cache" triggers a `rebuildExtensionCache` operation (Process L with cache-rebuild flag)
  - Shows loading indicator during rebuild; shows success/failure toast on completion

---

### Save Success Toast

**Component Type:** Toast notification (conditional)

**Visibility Condition:** Shown after a successful `updateExtensions` response

**Configuration:**
- Style: Success (green)
- Message: "Extensions saved successfully. {updatedFieldCount} fields updated."
- Auto-dismiss after 5 seconds
- Can also be manually dismissed

---

### Save Error Banner

**Component Type:** Inline error banner (conditional)

**Visibility Condition:** Shown if `updateExtensions` fails

**Configuration:**
- Style: Error (red)
- Displays error code and message text
- Not auto-dismissed; user must close manually

**Special Error Code Handling:**

| Error Code | Display Message |
|------------|-----------------|
| `CONNECTION_EDIT_ADMIN_ONLY` | "Connection extensions can only be edited by administrators." |
| `UNAUTHORIZED_EXTENSION_EDIT` | "You do not have access to edit this extension. Contact your administrator." |
| `EXTENSION_NOT_FOUND` | "Extension access mapping not found. The extension access cache may need to be rebuilt." |

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| "Extension Manager"                                       |
+----------------------------------------------------------+
| SELECTOR BAR                                              |
|  Account: [Select a client account...    ▼]               |
|  Environment: [Select an environment...  ▼]               |
+----------------------------------------------------------+
| SAVE ERROR BANNER (conditional)                           |
| ✕  CONNECTION_EDIT_ADMIN_ONLY: Connection extensions...  |
+----------------------------------------------------------+
| MAIN AREA                                                |
|                                                          |
|  ExtensionEditor Custom Component                         |
|  +----------------------------------------------------+  |
|  |  [Tree Nav Panel]  | [Property Table]              |  |
|  |  Process Props     | Field Name    | Value         |  |
|  |  > Operations      | db.host       | prod-db.co... |  |
|  |  Connections       | api.timeout   | 30000         |  |
|  |  Cross Refs        | max.retries   | 3             |  |
|  |  PGP Certs         |               |               |  |
|  |                    |  [Search...]  [Undo] [Redo]   |  |
|  +----------------------------------------------------+  |
|  (Admin only: [Rebuild Cache])                            |
|                                                          |
+----------------------------------------------------------+
| FOOTER / ACTION BAR                                      |
| [Copy Test → Prod]                 [Save Extensions]     |
+----------------------------------------------------------+
| SAVE SUCCESS TOAST (conditional, bottom right)           |
| ✓ Extensions saved. 4 fields updated.        [✕]        |
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- Page title: "Extension Manager"
- No per-page refresh button needed (selectors serve as reload triggers)

**Selector Bar:**
- Account Selector and Environment Selector displayed inline (horizontal on desktop, stacked on mobile)
- Loading spinner replaces selector content while `listClientAccounts` is in progress

**Main Area:**
- ExtensionEditor takes full remaining page height
- Min height: 400px
- Scrolls internally within the component

**Footer / Action Bar:**
- "Copy Test → Prod" button left-aligned; only visible when Test Environment is selected
- "Save Extensions" button right-aligned; enabled only when ExtensionEditor has unsaved changes

### Responsive Behavior

**Desktop (> 1024px):**
- ExtensionEditor renders in two-panel mode: tree navigation on the left (~30% width), property table on the right (~70% width)
- Selector bar displays Account and Environment dropdowns side by side

**Tablet (768px - 1024px):**
- ExtensionEditor renders in stacked mode: tree navigation panel above, property table below
- Selector bar stacks dropdowns vertically

**Mobile (< 768px):**
- ExtensionEditor renders in single-panel mode with a navigation drawer for the tree (accessible via hamburger icon)
- Selector bar stacks dropdowns vertically, full width
- Footer action buttons stack vertically, full width

## Accessibility

- **Keyboard navigation:** Tab through Account Selector → Environment Selector → ExtensionEditor tree → property fields → Save button
- **Screen reader:** Announce loading states for `listClientAccounts` and `getExtensions`; announce save success/failure; announce error banner content
- **Focus indicators:** Clear visual focus rings on all interactive elements
- **ARIA labels:** Proper labels for selectors, ExtensionEditor region, save button, toast, and error banner
- **Color contrast:** Error banner and success toast must meet WCAG AA contrast requirements

## User Flow Example

1. **Developer navigates to Extension Manager**
   - Clicks "Extension Manager" in the dashboard sidebar from any page
   - Page loads; `listClientAccounts` executes; Account Selector populates with two accounts: "Acme Corp (DEV)" and "Acme Corp (STAGING)"

2. **Developer selects an account**
   - Selects "Acme Corp (DEV)" from the Account Selector
   - Environment Selector populates with "Test Environment" and "Production Environment"

3. **Developer selects Test Environment**
   - Selects "Test Environment"
   - `getExtensions` executes; loading indicator shown inside ExtensionEditor area
   - ExtensionEditor renders with the full extension tree for the test environment

4. **Developer edits a process property**
   - Expands "Process Properties" in the tree panel
   - Locates "api.endpoint.url" in the property table
   - Changes value from "https://api-test.acme.com" to "https://api-dev.acme.com"
   - Field is highlighted to indicate an unsaved change; "Save Extensions" button becomes active

5. **Developer saves changes**
   - Clicks "Save Extensions"
   - `updateExtensions` executes
   - Save Success Toast appears: "Extensions saved successfully. 1 field updated."
   - Toast auto-dismisses after 5 seconds

6. **Developer initiates Copy Test → Prod**
   - Clicks "Copy Test → Prod" in the footer
   - Flow values set: `testEnvironmentId`, `testEnvironmentName`, `prodEnvironmentId`, `prodEnvironmentName`, `extensionData`
   - Navigates to Page 11 (Extension Copy Confirmation)

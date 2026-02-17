# Page 11: Extension Copy Confirmation (Developer + Admin Swimlane)

## Overview

The Extension Copy Confirmation page is the review and commit step for copying environment extensions from a test environment to a production environment within the same client account. Users arrive here exclusively from Page 10 (Extension Manager) via the "Copy Test → Prod" action. The page presents a summary of what will be copied, clearly distinguishes what will be excluded (connections, PGP certificates), and warns about encrypted field values that require manual follow-up in production. After review, the user confirms the copy or cancels back to the Extension Manager.

## Navigation Entry Points

This page can **only** be reached from:
- **Page 10 (Extension Manager):** Via the "Copy Test → Prod" action in the footer

**Navigation Guard:**
- Required Flow values must all be set before this page renders:
  - `selectedClientAccountId`
  - `selectedClientAccountName`
  - `testEnvironmentId`
  - `testEnvironmentName`
  - `prodEnvironmentId`
  - `prodEnvironmentName`
  - `extensionData`
- If any of these values are absent (e.g., user navigates directly via URL), redirect to Page 10 (Extension Manager) with a warning banner: "Please select an account and environment before copying extensions."

## Page Load Behavior

1. **Authorization:** SSO group "ABC_BOOMI_FLOW_CONTRIBUTOR" OR "ABC_BOOMI_FLOW_ADMIN"

2. **Read Flow values set by Page 10:**
   - `selectedClientAccountId`
   - `selectedClientAccountName`
   - `testEnvironmentId`
   - `testEnvironmentName`
   - `prodEnvironmentId`
   - `prodEnvironmentName`
   - `extensionData` (test environment extensions — used to compute copy preview counts)

3. **Parse extensionData for preview:**
   - Compute per-category counts (Process Properties, Operations, Cross-Reference Overrides, Connections, PGP Certificates)
   - Identify encrypted field count across all non-excluded categories
   - No additional message step is required on load; all data is available from Page 10

4. **Error handling:**
   - If `extensionData` cannot be parsed → Show error banner: "Extension data could not be read. Return to the Extension Manager and reload your extensions before retrying the copy."
   - Show "Return to Extension Manager" button; do not allow copy to proceed

## Components

### Copy Summary Header

**Component Type:** Static header panel

**Configuration:**
- Displays the source, destination, and client account for the copy operation
- Layout: Three labeled fields with an arrow indicating direction

**Content:**
- **Source:** "Test Environment: {testEnvironmentName}"
- **Destination:** "Production Environment: {prodEnvironmentName}"
- **Client Account:** "{selectedClientAccountName}"
- **Direction indicator:** Arrow or flow graphic pointing Test → Prod

---

### Sections Included Panel

**Component Type:** Info panel (green/success styling)

**Visibility Condition:** Always shown

**Content:**
- Heading: "What will be copied"
- List of categories that will be included in the copy, each with a count and green check icon:
  - "Process Properties ({count})"
  - "Operation Settings ({count})"
  - "Cross-Reference Overrides ({count})"

**Counts:**
- Derived from parsing `extensionData` at page load
- Show "0" for any category with no entries; do not hide empty categories

---

### Sections Excluded Panel

**Component Type:** Warning panel (amber/warning styling)

**Visibility Condition:** Always shown

**Content:**
- Heading: "What will NOT be copied"
- List of excluded categories, each with an amber warning icon and an explanatory note:
  - "Connections ({count}) — Connection settings contain environment-specific URLs, credentials, and certificates that must be configured separately in production."
  - "PGP Certificates — Certificate data is environment-specific and cannot be transferred."

**Counts:**
- Derived from parsing `extensionData` at page load
- If connection count is 0, still show the Connections row to confirm awareness of the exclusion rule

---

### Encrypted Fields Warning

**Component Type:** Caution banner (red/caution styling)

**Visibility Condition:** Shown only if encrypted field count > 0

**Content:**
- "{encryptedFieldCount} encrypted field(s) were detected."
- "Encrypted values (passwords, API keys) will be copied as-is. If an encrypted value is environment-specific, you must update it manually in production after the copy."
- Icon: Lock or warning icon

**Encrypted Field Count:**
- Derived from parsing `extensionData` — count fields where value is masked or flagged as encrypted by the API
- If count is 0, this panel is hidden entirely

---

### Extension Preview Table

**Component Type:** Collapsible table panel

**Configuration:**
- Collapsed by default; user can expand to review detail
- Toggle label when collapsed: "Show Extension Details ({totalExtensionCount} extensions)"
- Toggle label when expanded: "Hide Extension Details"

**Columns:**

| Column | Field | Width | Formatting |
|--------|-------|-------|------------|
| Extension Name | `extensionName` | 35% | Plain text |
| Category | `category` | 25% | Plain text (e.g., "Process Property", "Operation", "Connection") |
| Property Count | `propertyCount` | 15% | Numeric |
| Action | (derived) | 25% | Badge: "Will Copy" (green) or "Excluded" (amber) |

**Action Badge Logic:**
- Connections → "Excluded" (amber badge)
- PGP Certificates → "Excluded" (amber badge)
- All other categories → "Will Copy" (green badge)

**Empty State:**
- Message: "No extensions found in test environment."

**Pagination:**
- If > 25 rows: Enable pagination (25 rows per page)

---

### Action Buttons

**Component Type:** Button group

**Buttons:**

1. **Confirm Copy** (Primary, green)
   - Label: "Confirm Copy"
   - Style: Large primary button
   - Color: Green/success
   - Enabled condition: `extensionData` parsed successfully and no blocking errors
   - Behavior on click:
     1. Show loading spinner on button; disable both action buttons
     2. Execute `copyExtensionsTestToProd` message step (Process N)
        - Input: `clientAccountId`, `testEnvironmentId`, `prodEnvironmentId`, `userSsoGroups`, `userEmail`
     3. On success → hide action buttons; show Copy Result Panel (success state)
     4. On failure → re-enable action buttons; show Copy Result Panel (failure state)

2. **Cancel** (Secondary)
   - Label: "Cancel"
   - Style: Medium secondary button
   - Behavior on click: Navigate back to Page 10 (Extension Manager)

---

### Copy Result Panel

**Component Type:** Result panel (conditional)

**Visibility Condition:** Shown after `copyExtensionsTestToProd` completes (success or failure)

**Success State:**
- Style: Success (green)
- Message: "Extensions copied successfully. {fieldsCopied} fields copied, {sectionsExcluded} sections excluded, {encryptedFieldsSkipped} encrypted fields preserved."
- Button: "Return to Extension Manager" (primary) → navigates to Page 10

**Failure State:**
- Style: Error (red)
- Message: "Extension copy failed. {errorCode}: {errorMessage}"
- Button: "Return to Extension Manager" (secondary) → navigates to Page 10
- Note: A failed copy does not modify the production environment; it is safe to retry after investigating the error

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| "Copy Extensions: Test → Production"                     |
| Client Account: Acme Corp (DEV)                          |
+----------------------------------------------------------+
| COPY SUMMARY HEADER                                       |
|   Source: Test Environment: test-env-name                |
|       →                                                  |
|   Destination: Production Environment: prod-env-name     |
+----------------------------------------------------------+
| TWO-COLUMN PANELS                                        |
|  +------------------------+ +-------------------------+  |
|  | SECTIONS INCLUDED      | | SECTIONS EXCLUDED       |  |
|  | ✓ Process Props  (12)  | | ⚠ Connections    (3)   |  |
|  | ✓ Operations     (7)   | |   (env-specific URLs)  |  |
|  | ✓ Cross-Refs     (4)   | | ⚠ PGP Certs     (—)   |  |
|  |                        | |   (cert data env-spec) |  |
|  +------------------------+ +-------------------------+  |
+----------------------------------------------------------+
| ENCRYPTED FIELDS WARNING (conditional)                    |
| 🔒 2 encrypted field(s) detected. Values will be        |
|    copied as-is. Update env-specific secrets manually.   |
+----------------------------------------------------------+
| EXTENSION PREVIEW TABLE (collapsible)                     |
| ▶ Show Extension Details (23 extensions)                 |
|   +--------------------------------------------------+   |
|   | Extension Name | Category | Props | Action       |   |
|   |--------------------------------------------------|   |
|   | Order Proc...  | Process  | 4     | Will Copy    |   |
|   | API Connector  | Connect. | 2     | Excluded     |   |
|   | XREF Table 1   | Cross-R  | 6     | Will Copy    |   |
|   +--------------------------------------------------+   |
+----------------------------------------------------------+
| ACTION BUTTONS                                           |
| [Cancel]                          [Confirm Copy]         |
+----------------------------------------------------------+
| COPY RESULT PANEL (conditional, shown after copy)        |
| ✓ Extensions copied. 23 fields, 2 excluded, 0 skipped.  |
|                          [Return to Extension Manager]   |
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- Page title: "Copy Extensions: Test → Production"
- Client account name displayed beneath title as subtitle

**Copy Summary Header:**
- Centered directional layout with Test on the left, arrow in the middle, Production on the right
- Environment names pulled from Flow values set on Page 10

**Two-Column Panels:**
- Sections Included (left) and Sections Excluded (right) displayed side by side on desktop
- Each panel is fixed height; non-scrolling

**Encrypted Fields Warning:**
- Full-width banner between the two-column panels and the preview table
- Hidden when encrypted field count is 0

**Extension Preview Table:**
- Full-width collapsible section
- Collapsed by default to keep the page concise

**Action Buttons:**
- "Cancel" left-aligned, "Confirm Copy" right-aligned
- Both buttons hidden and replaced by Copy Result Panel after the copy operation completes

### Responsive Behavior

**Desktop (> 1024px):**
- Sections Included and Sections Excluded panels displayed side by side (50%/50%)
- Copy Summary Header displays Test, arrow, and Production in a single horizontal row

**Tablet (768px - 1024px):**
- Two-column panels remain side by side with reduced padding
- Copy Summary Header stacks vertically (Test above, arrow, Production below)

**Mobile (< 768px):**
- Sections Included and Sections Excluded panels stack vertically (Included first, Excluded below)
- Copy Summary Header stacks vertically
- Action buttons stack vertically, full width; "Confirm Copy" on top, "Cancel" below

## Accessibility

- **Keyboard navigation:** Tab through Copy Summary → Sections Included → Sections Excluded → Encrypted Fields Warning → Preview Table toggle → Cancel button → Confirm Copy button
- **Screen reader:** Announce copy summary (source, destination, account); announce category counts in both panels; announce encrypted field warning if present; announce result panel content after copy completes
- **Focus indicators:** Clear visual focus rings on table toggle, Cancel button, and Confirm Copy button
- **ARIA labels:** Proper labels for the included panel, excluded panel, encrypted warning, preview table, action buttons, and result panel; use `aria-live` region for the Copy Result Panel to announce outcome without requiring focus
- **Color contrast:** Green (included) and amber (excluded) panel styling must meet WCAG AA contrast requirements; red encrypted warning must also meet AA requirements

## User Flow Example

1. **Developer arrives from Page 10**
   - Had selected "Acme Corp (DEV)" account and "Test Environment" on Page 10
   - Clicked "Copy Test → Prod" in the Page 10 footer
   - Flow values `testEnvironmentId`, `testEnvironmentName`, `prodEnvironmentId`, `prodEnvironmentName`, and `extensionData` are set

2. **Developer reviews the copy summary**
   - Copy Summary Header shows: "Test Environment: acme-test → Production Environment: acme-prod"
   - Client Account: "Acme Corp (DEV)"

3. **Developer reviews included and excluded sections**
   - Sections Included: Process Properties (12), Operations (7), Cross-Reference Overrides (4)
   - Sections Excluded: Connections (3) with explanation, PGP Certificates with explanation
   - Developer acknowledges that the 3 connection settings in production must remain as they are

4. **Developer notes the encrypted fields warning**
   - Banner reads: "2 encrypted field(s) detected. Encrypted values will be copied as-is..."
   - Developer makes a note to verify those 2 fields manually in production after the copy

5. **Developer expands the preview table (optional)**
   - Clicks "Show Extension Details (23 extensions)"
   - Reviews the list; confirms the "Excluded" badge on the API Connector connection row
   - Collapses the table

6. **Developer confirms the copy**
   - Clicks "Confirm Copy"
   - Button shows loading spinner; both buttons disabled
   - `copyExtensionsTestToProd` executes

7. **Copy completes successfully**
   - Action buttons disappear; Copy Result Panel shows in success state:
     "Extensions copied successfully. 23 fields copied, 2 sections excluded, 2 encrypted fields preserved."
   - Developer clicks "Return to Extension Manager" and is navigated back to Page 10

# Pages and Navigation

## Page Types

Flow pages serve as UI screens and logic containers. Every user-facing screen in a Flow application is a page.

---

## Components of a Page

### 1. Containers
Layout elements that structure content:
- **Row**: Horizontal layout
- **Column**: Vertical layout
- **Grid**: Multi-column grid with responsive breakpoints
- **Panel**: Collapsible sections
- **Tabs**: Tabbed content areas

### 2. Components
UI elements that display data or collect input:

#### Input Components
- Text Input, Text Area, Number Input
- Date Picker, DateTime Picker
- Toggle, Checkbox, Radio Buttons
- Combobox/Dropdown, Multi-select
- File Upload

#### Display Components
- Presentation (static text, HTML, Markdown)
- Image, Rich Text
- Chart (if available)

#### Data Components
- Data Grid/Table (tabular data with sorting, filtering, pagination)
- List, Tag List

#### Action Components
- Button (primary, secondary, link styles)
- Outcome (navigation triggers)

### 3. Outcomes
Navigation paths to other steps (pages, decisions, messages, swimlanes).

**Triggers:**
- User action (button click, form submission)
- Business rule evaluation (conditional routing)
- Automatic progression (after message step completes)

### 4. Page Conditions
Business rules that control page visibility or behavior.

**Example:** Only show page if user is admin and promotion status is pending.

```
Page Condition:
ALL (AND)
  $User/Groups contains "Boomi Admins"
  promotionStatus == "PENDING_ADMIN_APPROVAL"
```

---

## Page Builder

The **Page Builder** is a drag-and-drop interface for creating pages.

### Interface Layout

1. **Components panel (left)**: Library of standard and custom components
2. **Page canvas (center)**: Visual editor for arranging containers and components
3. **Configuration panel (right)**: Settings for selected container/component
4. **Page header**: Page settings, metadata editor, preview, save

### Page Settings

- **Page name**: Display title (shown in navigation, breadcrumbs)
- **Page conditions**: Business rules that control when page is accessible
- **Metadata**: Custom properties and tags
- **Mobile/desktop preview**: Live preview modes

### Page Persistence

**Important:** Pages are **not auto-saved**. Developers must manually save and commit changes using the **Save** button.

**Source:** [Overview - Page Builder](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Setting_up_and_managing_flows/Pages/Creating_a_Page/Using_the_page_builder/flo-pages-builder_eafc591c-11b8-4924-835f-beff9aecd8c5)

---

## Navigation Patterns

### 1. Outcome-Based Navigation

**How it works:**
- Pages connect to other steps via **outcomes**
- Outcome triggered by user action (button click, form submission)
- Outcome can have business rules (conditional routing)
- Flow follows outcome to next step

**Example:**

```
Page 1: Package Browser
  ↓
User selects package from data grid
  ↓
Button: "Review and Promote"
  ↓
Outcome: "Review" → Page 2: Promotion Review
```

**Outcome configuration:**
- **From**: Page 1
- **To**: Page 2
- **Triggered by**: Button click
- **Business rule**: None (always follow)

### 2. Conditional Routing with Outcomes

**Use case:** Route to different pages based on user selections.

**Example:**

```
Page 2: Promotion Review
  ↓
Button: "Promote"
  ↓
Outcome A: "Submit for Peer Review" (if requiresPeerReview == true) → Peer Review Swimlane
Outcome B: "Submit Directly" (if requiresPeerReview == false) → Admin Swimlane
```

**Outcome A configuration:**
- **Business Rule**: `ALL (AND) requiresPeerReview == $True`
- **Order**: 0 (highest priority)

**Outcome B configuration:**
- **Business Rule**: `ALL (AND) requiresPeerReview == $False`
- **Order**: 1 (fallback)

**Flow logic:**
- If `requiresPeerReview == true`, follow Outcome A (order 0)
- If `requiresPeerReview == false`, follow Outcome B (order 1)

### 3. Historical Navigation (Breadcrumbs)

Flow supports **breadcrumb-style navigation** that allows users to navigate back to previously visited pages.

**How it works:**
- Flow automatically adds breadcrumb links as user progresses
- Breadcrumbs show page names in order visited
- User can click breadcrumb to return to previous page
- Collapses after 5 steps with ellipsis (`Page 1 > ... > Page 4 > Page 5`)

**Configuration:**
- **Location**: Flow > Settings > Navigation
- **Enable/Disable**: Enabled by default
- **Collapse threshold**: 5 pages (configurable)

**Best practice:** Enable historical navigation for complex flows with many pages. Disable for linear workflows where users should not go back (e.g., onboarding wizards).

**Source:** [Historical navigation - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Building_and_publishing_flows/Navigation/c-flo-Nav_Historical_d63d245e-098d-4bd4-aa7e-fd3d937a33ba)

### 4. Swimlane Transitions

Crossing a swimlane boundary pauses flow execution until a user with appropriate authorization continues.

**Example:**

```
Developer Swimlane
  ↓
  Page 2: Promotion Review
  ↓
  Outcome: "Submit for Peer Review"
  ↓
Peer Review Swimlane (Flow pauses here)
  ↓ (Email notification sent to peer reviewers)
User in Peer Review Swimlane authenticates
  ↓
  Page 5: Peer Review Queue
```

**User experience:**
- Developer clicks "Submit for Peer Review" → Flow pauses
- Email notification sent to all users in "Boomi Developers" group
- Peer reviewer clicks link in email → Flow resumes in Peer Review Swimlane
- Peer reviewer sees Page 5: Peer Review Queue

---

## Common Page Patterns

### Pattern 1: List/Browser Page

**Purpose:** Display data grid with filtering and selection.

**Components:**
- **Data Grid**: List of items (e.g., packages, promotions)
  - Columns: Display properties (name, version, type, date)
  - Selection: Single or multiple row selection
  - Sorting: Client-side or server-side
  - Pagination: 50 rows per page if > 50 total
- **Filter controls**: Text input, dropdown, date range
- **Action button**: "Review and Promote", "View Details"

**Flow logic:**
1. **On page load**: Message step calls API to fetch list (e.g., `listDevPackages`)
2. **Response stored in Flow Value**: `packagesList` (List type)
3. **Data grid bound to Flow Value**: `packagesList`
4. **User selects row**: Selection stored in Flow Value `selectedPackage` (Object type)
5. **User clicks button**: Outcome → next page (detail/form)

**Example: Page 1 - Package Browser**

```
On Page Load:
  Message Step: listDevPackages
  Request: { "devAccountId": selectedDevAccountId }
  Response: { "packages": [...] }
  Store response.packages in Flow Value: packagesList

Page Layout:
  Combobox: "Developer Account" (bound to selectedDevAccountId)
  Data Grid: "Packages"
    - Data Source: packagesList
    - Columns: Package Name, Version, Type, Created, Notes
    - Selection: Single row → stores to selectedPackage
  Button: "Review and Promote"
    - Outcome: "Review" → Page 2

Outcome:
  From: Page 1
  To: Page 2
  Triggered by: Button "Review and Promote"
  Business Rule: selectedPackage is not empty
```

### Pattern 2: Detail/Form Page

**Purpose:** Collect user input, display detailed data.

**Components:**
- **Presentation**: Display selected item details (read-only)
- **Form inputs**: Text input, text area, toggle, date picker
- **Action buttons**: "Submit", "Cancel"

**Flow logic:**
1. **On page load**: Display details from Flow Value (e.g., `selectedPackage`)
2. **User enters data**: Form inputs update Flow Values
3. **User clicks button**: Outcome → next page (review/submit) or previous page (cancel)

**Example: Page 2 - Promotion Review**

```
On Page Load:
  Message Step: resolveDependencies
  Request: { "componentId": selectedPackage.componentId, "devAccountId": selectedDevAccountId }
  Response: { "dependencyTree": [...] }
  Store response.dependencyTree in Flow Value: dependencyTree

Page Layout:
  Presentation: "Selected Package"
    - Component Name: selectedPackage.componentName
    - Version: selectedPackage.packageVersion
    - Type: selectedPackage.componentType

  Data Grid: "Dependencies"
    - Data Source: dependencyTree
    - Columns: Component Name, Type, Action (CREATE/UPDATE)

  Text Area: "Deployment Notes"
    - Value binding: deploymentRequest.notes
    - Max length: 500

  Button: "Promote"
    - Outcome: "Promote" → Message Step: executePromotion → Page 3

  Button: "Cancel"
    - Outcome: "Cancel" → Page 1
```

### Pattern 3: Review/Approval Page

**Purpose:** Show summary data with approve/reject actions.

**Components:**
- **Presentation**: Display summary data (read-only)
- **Data grid**: List of items to review (if multiple)
- **Action buttons**: "Approve", "Reject"

**Flow logic:**
1. **On page load**: Message step fetches review queue (e.g., `queryPeerReviewQueue`)
2. **User selects item**: Selection stored in Flow Value `selectedPeerReview`
3. **User navigates to detail page**: Outcome → next page (detail)
4. **User approves/rejects**: Outcome → Message step (e.g., `submitPeerReview`) → next page (confirmation)

**Example: Page 5 - Peer Review Queue**

```
On Page Load:
  Message Step: queryPeerReviewQueue
  Request: { "reviewStage": "PENDING_PEER_REVIEW", "excludeSubmittedBy": $User/Email }
  Response: { "promotions": [...] }
  Store response.promotions in Flow Value: peerReviewQueue

Page Layout:
  Presentation: "Peer Review Queue"
    - Text: "Review promotions submitted by other developers."

  Data Grid: "Pending Peer Reviews"
    - Data Source: peerReviewQueue
    - Columns: Component Name, Submitted By, Submitted At, Notes
    - Selection: Single row → stores to selectedPeerReview
    - Empty state: "No pending peer reviews."

  Button: "Review"
    - Outcome: "Review" → Page 6
    - Enabled: selectedPeerReview is not empty
```

### Pattern 4: Status/Results Page

**Purpose:** Display operation results, wait states, success/error messages.

**Components:**
- **Presentation**: Display status message
- **Data grid**: List of results (if multiple items)
- **Progress indicator**: Spinner, progress bar (for async operations)
- **Action buttons**: "Done", "Retry", "Submit for Deployment"

**Flow logic:**
1. **On page load**: Display results from Flow Value (e.g., `promotionResults`)
2. **If async operation**: Show spinner/loading state while waiting for completion
   - Flow Service caches state to IndexedDB (every 30 seconds)
   - User can close browser and resume later
   - Flow automatically resumes when operation completes
3. **When operation completes**: Hide spinner, show results
4. **User clicks button**: Outcome → next page (submit for deployment, return home, etc.)

**Example: Page 3 - Promotion Status**

```
On Page Load:
  (No message step — results already in Flow Value: promotionResults from Page 2)

Page Layout:
  Presentation: "Promotion Results"
    - Text: "Promotion completed. Review results below."

  Data Grid: "Promoted Components"
    - Data Source: promotionResults.results
    - Columns: Component Name, Action (CREATE/UPDATE), Status (SUCCESS/FAILED), Error Message

  Presentation: "Summary"
    - Total: promotionResults.results.length
    - Succeeded: promotionResults.componentsPassed
    - Failed: promotionResults.componentsFailed

  Button: "Submit for Deployment"
    - Outcome: "Submit" → Message Step: packageAndDeploy → Page 4
    - Enabled: promotionResults.componentsFailed == 0

  Button: "Done"
    - Outcome: "Done" → Page 1
```

**Wait state variant (async operation):**

```
Page 2 → User clicks "Promote" button
  ↓
Message Step: executePromotion (long-running, 5+ minutes)
  ↓
Flow Service returns wait response
  ↓
Page 3 loads with wait state overlay:
  - Spinner animation
  - "Promoting components to primary account..."
  - "Processing component 5 of 50..." (if progress available)
  - Progress bar (if progress available)
  - "This may take several minutes. You can safely close this window."
  ↓
Flow caches state to IndexedDB (every 30 seconds)
  ↓
User closes browser (goes to lunch)
  ↓
Process completes (5 minutes later)
  ↓
User returns to browser, navigates to flow URL
  ↓
Flow resumes from IndexedDB cache
  ↓
Wait state overlay hides, results displayed
```

---

## Data Grid Configuration

### Key Properties

| Property | Description | Example |
|----------|-------------|---------|
| **Data Source** | Bind to Flow Value (list) | `packagesList` |
| **Columns** | Define column structure | Component Name, Version, Type |
| **Selection** | Single or multiple row selection | Single → stores to `selectedPackage` |
| **Pagination** | Rows per page, page controls | 50 rows per page if > 50 total |
| **Filtering** | Client-side or server-side filtering | Client-side for < 500 rows |
| **Sorting** | Enable sorting, default sort column | Default DESC by Created Date |
| **Empty state** | Message when no data | "No packages found in this account" |

### Column Configuration

**Column properties:**
- **Field**: Property name from data source (e.g., `componentName`)
- **Header**: Column display name (e.g., "Package Name")
- **Width**: Column width (%, px, auto)
- **Sortable**: Enable sorting (true/false)
- **Format**: Data formatting (date, number, currency)
- **Cell renderer**: Custom rendering (badge, link, button)

**Example: Packages data grid**

```
Column 1: Package Name
  - Field: componentName
  - Width: 30%
  - Sortable: true
  - Sort order: alphabetical

Column 2: Version
  - Field: packageVersion
  - Width: 15%
  - Sortable: true
  - Sort order: numeric

Column 3: Type
  - Field: componentType
  - Width: 15%
  - Sortable: true
  - Cell renderer: Badge (color-coded by type)

Column 4: Created
  - Field: createdDate
  - Width: 20%
  - Sortable: true
  - Sort order: default DESC (newest first)
  - Format: date (MM/DD/YYYY HH:mm)

Column 5: Notes
  - Field: notes
  - Width: 20%
  - Sortable: false
  - Cell renderer: Truncated text (show "..." if > 50 chars)
```

### Selection Handling

**Single row selection:**

```
Data Grid: Packages
  Selection mode: Single
  On selection changed:
    Store selected row to Flow Value: selectedPackage
```

**Multiple row selection:**

```
Data Grid: Promotions
  Selection mode: Multiple
  On selection changed:
    Store selected rows to Flow Value: selectedPromotions (List)
```

---

## Forms and Input Binding

### Input Binding Pattern

1. Component's **Value** property binds to Flow Value
2. User enters data
3. On change event, Flow Value updates automatically
4. On outcome (button click), Flow Values passed to next step

**Example:**

```
Text Input: "Deployment Notes"
  - Value binding: deploymentRequest.notes
  - Placeholder: "Enter deployment notes..."
  - Required: Yes
  - Max length: 500

Button: "Submit for Peer Review"
  - On click: Outcome → triggers message step with deploymentRequest
```

### Validation

**Client-side validation:**
- Required fields (marked with red asterisk)
- Field-level validation (email format, number range, max length)
- Form-level validation (all required fields filled)

**Business rule validation:**

```
Button: "Submit"
  Enabled when:
  ALL (AND)
    deploymentRequest.notes is not empty
    dependencyTree.length > 0
```

---

## Conditional Visibility

### Component Visibility

Components can have **visibility rules** based on Flow Values or `$User` properties.

**Example: Show admin-only button**

```
Button: "Delete Promotion"
Visibility Rule:
ALL (AND)
  $User/Groups contains "Boomi Admins"
```

**Example: Show error message only if failures exist**

```
Presentation: "Error: Some components failed to promote."
Visibility Rule:
ALL (AND)
  promotionResults.componentsFailed > 0
```

### Container Visibility

Containers can have visibility rules to show/hide entire sections.

**Example: Show "Submit for Deployment" section only if no failures**

```
Container: "Deployment Section"
Visibility Rule:
ALL (AND)
  promotionResults.componentsFailed == 0
```

---

## Responsive Design

Flow components support responsive layouts with breakpoints:

| Breakpoint | Width | Layout Adjustments |
|------------|-------|-------------------|
| **Desktop** | > 1024px | Full layouts with all columns |
| **Tablet** | 768px - 1024px | Adjusted column widths, some columns hidden |
| **Mobile** | < 768px | Card-based layouts, stacked components |

### Responsive Settings

**Container responsive settings:**
- **Hide on mobile**: Hide entire container on small screens
- **Reorder**: Change order of containers on mobile
- **Stack direction**: Horizontal on desktop, vertical on mobile

**Data grid responsive behavior:**
- **Desktop**: Show all columns in tabular format
- **Tablet**: Hide less important columns (e.g., Notes)
- **Mobile**: Convert to card-based layout (each row becomes a card)

---

## Best Practices

### 1. Page Design
- **Keep pages focused**: One task per page (select package, review promotion, approve)
- **Progressive disclosure**: Show only relevant information at each step
- **Clear navigation**: Use breadcrumbs for multi-page flows
- **Responsive layouts**: Test on mobile, tablet, desktop

### 2. Data Grids
- **Paginate large datasets**: Use pagination for > 50 rows
- **Client-side filtering**: For small datasets (< 500 rows), filter in browser for faster UX
- **Default sort**: Set sensible default sort (newest first for lists)
- **Empty states**: Provide helpful messages when no data ("No packages found in this account")

### 3. Forms and Input
- **Mark required fields**: Use red asterisk or "Required" label
- **Provide placeholders**: Help users understand expected input
- **Validate on submit**: Show validation errors when user clicks submit
- **Disable submit until valid**: Gray out button until all required fields filled

### 4. Outcomes and Navigation
- **Descriptive button labels**: "Submit for Peer Review" instead of "Submit"
- **Confirm destructive actions**: Show confirmation dialog before delete/reject
- **Provide cancel path**: Always offer "Cancel" or "Go Back" option
- **Use business rules**: Enable/disable buttons based on state

### 5. Conditional Visibility
- **Show errors contextually**: Only show error messages when relevant
- **Hide admin features**: Use `$User/Groups` to hide admin-only buttons
- **Progressive disclosure**: Show/hide sections based on user selections

---

## Sources

- [Overview - Page Builder](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Setting_up_and_managing_flows/Pages/Creating_a_Page/Using_the_page_builder/flo-pages-builder_eafc591c-11b8-4924-835f-beff9aecd8c5)
- [Historical navigation - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Building_and_publishing_flows/Navigation/c-flo-Nav_Historical_d63d245e-098d-4bd4-aa7e-fd3d937a33ba)
- [Business rules - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Building_and_publishing_flows/Steps/Outcomes/c-flo-Canvas_Business_Rules_e8860ab5-4260-449c-b72d-137d9902baec)

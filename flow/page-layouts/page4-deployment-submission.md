# Page 4: Deployment Submission (Developer Swimlane → Admin Swimlane Transition)

## Overview

The Deployment Submission page is where the developer fills out deployment details and submits the promotion for admin approval. This page represents the transition point between the Developer and Admin swimlanes. After submission, the flow pauses at the swimlane boundary until an admin authenticates and takes action.

## Page Load Behavior

1. **Arrival condition:** User navigates here from Page 3 (Promotion Status) via "Submit for Deployment" button

2. **Pre-populate form fields:**
   - `packageVersion`: From `selectedPackage.packageVersion` (if available)
   - `processName`: From `promotionResults` or `selectedPackage.componentName`
   - `componentsTotal`: From `totalComponents` Flow value
   - `promotionId`: From previous step

3. **Load integration pack options (optional):**
   - Message step → API to get list of existing Integration Packs (if available)
   - Populate Combobox with pack names
   - Store in `availableIntegrationPacks` Flow value

4. **Load account group options (optional):**
   - Message step → API to get list of account groups (if available)
   - Populate Combobox with group names
   - Store in `availableAccountGroups` Flow value

## Components

### Package Version Input

**Component Type:** Text Input

**Configuration:**
- **Label:** "Package Version"
- **Placeholder:** "e.g., 1.0.0"
- **Pre-populated value:** `selectedPackage.packageVersion` (if available)
- **Required:** Yes
- **Validation:** Non-empty string
- **Pattern (optional):** Semantic versioning regex (e.g., `^\d+\.\d+\.\d+$`)
- **Max length:** 20 characters

**Behavior:**
- **On change:** Store value in `deploymentRequest.packageVersion`
- **Validation message:** "Package version is required" (if empty on submit)

**Styling:**
- Full width or max 300px
- Standard text input with border

---

### Integration Pack Selector (Combobox)

**Component Type:** Combobox (Dropdown)

**Configuration:**
- **Label:** "Integration Pack"
- **Placeholder:** "Select an integration pack or create new..."
- **Required:** Yes

**Options:**
1. **Special option:** "Create New Integration Pack"
   - Value: `"__CREATE_NEW__"` (special identifier)
   - Icon: Plus icon (+)
   - Positioned at top of dropdown

2. **Existing packs:**
   - Populated from `availableIntegrationPacks` API response
   - Display field: `packName`
   - Value field: `packId`
   - Example: "Order Management v2", "Customer Sync v1"

**Behavior:**
- **On select "Create New Integration Pack":**
  1. Show New Pack Name and New Pack Description fields (below selector)
  2. Store `deploymentRequest.createNewPack = true`
  3. Clear `deploymentRequest.integrationPackId`

- **On select existing pack:**
  1. Hide New Pack Name and New Pack Description fields
  2. Store selected `packId` → `deploymentRequest.integrationPackId`
  3. Store selected `packName` → `deploymentRequest.integrationPackName`
  4. Set `deploymentRequest.createNewPack = false`

**Validation:**
- "Integration Pack selection is required" (if empty on submit)

---

### New Pack Name Input (Conditional)

**Component Type:** Text Input

**Configuration:**
- **Label:** "New Pack Name"
- **Placeholder:** "e.g., Order Management v3"
- **Visibility:** Only shown when "Create New Integration Pack" is selected
- **Required:** Yes (when visible)
- **Max length:** 100 characters

**Behavior:**
- **On change:** Store value in `deploymentRequest.newPackName`
- **Validation message:** "New pack name is required when creating a new pack" (if empty on submit)

**Styling:**
- Indented or visually nested under Integration Pack Selector
- Full width or max 500px

---

### New Pack Description Input (Conditional)

**Component Type:** Textarea

**Configuration:**
- **Label:** "New Pack Description"
- **Placeholder:** "Describe the purpose and contents of this integration pack..."
- **Visibility:** Only shown when "Create New Integration Pack" is selected
- **Required:** No (optional)
- **Max length:** 500 characters
- **Rows:** 3

**Behavior:**
- **On change:** Store value in `deploymentRequest.newPackDescription`
- **Character counter:** Show "X / 500 characters" below textarea

**Styling:**
- Indented or visually nested under New Pack Name
- Full width or max 600px

---

### Target Account Group Selector

**Component Type:** Combobox (Dropdown)

**Configuration:**
- **Label:** "Target Account Group"
- **Placeholder:** "Select the target account group..."
- **Required:** Yes
- **Data source:** `availableAccountGroups` API response (or static config)
- **Display field:** `groupName`
- **Value field:** `groupId`

**Options:**
- Example: "Production", "UAT", "QA", "Dev Sandbox"
- Populated from primary account configuration
- May include group descriptions in tooltip

**Behavior:**
- **On change:** Store selected `groupId` → `deploymentRequest.targetAccountGroupId`
- **Validation message:** "Target account group is required" (if empty on submit)

**Styling:**
- Full width or max 400px

---

### Deployment Notes Textarea

**Component Type:** Textarea

**Configuration:**
- **Label:** "Deployment Notes"
- **Placeholder:** "Describe what's being deployed and any relevant context..."
- **Required:** No (optional)
- **Max length:** 500 characters
- **Rows:** 4

**Behavior:**
- **On change:** Store value in `deploymentRequest.notes`
- **Character counter:** Show "X / 500 characters" below textarea

**Styling:**
- Full width or max 600px

---

### Submit Button

**Component Type:** Button (Primary)

**Configuration:**
- **Label:** "Submit for Approval"
- **Style:** Primary button (prominent, large)
- **Color:** Accent/success color
- **Icon (optional):** Send/paper plane icon
- **Size:** Large

**Validation:**
- Check all required fields filled:
  - `packageVersion` not empty
  - `integrationPackId` selected OR (`createNewPack=true` AND `newPackName` not empty)
  - `targetAccountGroupId` selected
- If validation fails: Show error message, highlight empty required fields

**Behavior on Click:**

1. **Validate form:**
   - If validation fails: Show error messages, stop execution
   - If validation passes: Continue

2. **Build `deploymentRequest` object:**
   ```json
   {
     "promotionId": "{promotionId}",
     "packageVersion": "{packageVersion}",
     "integrationPackId": "{integrationPackId}" or null,
     "createNewPack": true/false,
     "newPackName": "{newPackName}" or null,
     "newPackDescription": "{newPackDescription}" or null,
     "targetAccountGroupId": "{targetAccountGroupId}",
     "notes": "{notes}",
     "submittedBy": "{userEmail}",
     "submittedAt": "{timestamp}",
     "processName": "{processName}",
     "componentsTotal": {componentsTotal}
   }
   ```

3. **Send email notification to admin group:**
   - **To:** Admin SSO group email distribution list (e.g., `boomi-admins@company.com`)
   - **CC:** Submitter (for confirmation)
   - **Subject:** `"Promotion Approval Needed: {processName} v{packageVersion}"`
   - **Body:**
     ```
     A new promotion has been submitted for approval and deployment.

     PROMOTION DETAILS:
     Promotion ID: {promotionId}
     Process: {processName}
     Package Version: {packageVersion}
     Total Components: {componentsTotal}

     DEPLOYMENT DETAILS:
     Integration Pack: {integrationPackName or newPackName}
     Target Account Group: {targetAccountGroupName}

     SUBMITTED BY:
     Name: {submitterName}
     Email: {submitterEmail}
     Date: {submittedAt}

     NOTES:
     {deploymentRequest.notes or "No notes provided."}

     Please review and approve/deny this deployment in the Promotion Dashboard:
     [Link to Flow approval page]
     ```

4. **Transition to Admin Swimlane:**
   - Flow state PAUSES at swimlane boundary
   - Store `deploymentRequest` in Flow state
   - Show confirmation message to developer:
     ```
     Submitted for approval!

     Your deployment request has been sent to the admin team.
     You will receive an email notification when an admin approves or denies your request.

     Promotion ID: {promotionId}
     ```

5. **End developer flow:**
   - Show "Close" button to exit
   - Admin must authenticate with SSO to continue flow

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
  1. Navigate back to Page 3 (Promotion Status)
  2. Do not clear any Flow values (user may want to retry)
  3. No confirmation required (form data not critical)

---

## Layout

### Page Structure

```
+----------------------------------------------------------+
| HEADER                                                    |
| "Submit for Integration Pack Deployment"                |
+----------------------------------------------------------+
| SUBHEADER / CONTEXT BAR                                  |
| Process: Order Processing Main                           |
| Components: 12 | Promotion ID: abc123-def456             |
+----------------------------------------------------------+
| FORM AREA                                                |
|                                                          |
|  Package Version                                         |
|  [1.2.3_____________________]                            |
|                                                          |
|  Integration Pack                                        |
|  [Create New Integration Pack ▼]                         |
|                                                          |
|    New Pack Name (conditional)                           |
|    [Order Management v3_________]                        |
|                                                          |
|    New Pack Description (conditional)                    |
|    [_________________________]                           |
|    [_________________________]                           |
|                                                          |
|  Target Account Group                                    |
|  [Production ▼______________]                            |
|                                                          |
|  Deployment Notes                                        |
|  [_________________________]                             |
|  [_________________________]                             |
|  [_________________________]                             |
|  [_________________________]                             |
|  0 / 500 characters                                      |
|                                                          |
+----------------------------------------------------------+
| FOOTER / ACTION BAR                                      |
| [Cancel]                        [Submit for Approval]    |
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- Page title: "Submit for Integration Pack Deployment"
- Clear, prominent heading

**Subheader / Context Bar:**
- Display key context from previous steps:
  - Process name: `{processName}`
  - Components count: `{componentsTotal}`
  - Promotion ID: `{promotionId}` (truncated or full)
- Light background color to differentiate from form
- Padding: 12px

**Form Area:**
- Stacked vertically with clear spacing between fields
- Labels bold and above inputs
- Consistent input widths (max-width for readability)
- Indented conditional fields (New Pack Name/Description)

**Footer / Action Bar:**
- Fixed at bottom or below form
- Cancel button left-aligned
- Submit button right-aligned
- Clear visual separation from form

### Responsive Behavior

**Desktop (> 1024px):**
- Form centered with max width 700px
- Inputs full width within form container
- Buttons in footer bar

**Tablet (768px - 1024px):**
- Form full width with padding
- Buttons full width or centered

**Mobile (< 768px):**
- Form full width
- Inputs full width
- Buttons stacked, full width
- Reduce font sizes for compact display

## Validation

### Field-Level Validation

**Package Version:**
- Required: "Package version is required"
- Pattern (optional): "Invalid version format (use X.Y.Z)"

**Integration Pack:**
- Required: "Please select an integration pack or choose to create a new one"

**New Pack Name (when visible):**
- Required: "New pack name is required when creating a new pack"
- Max length: "Pack name cannot exceed 100 characters"

**Target Account Group:**
- Required: "Target account group is required"

**Deployment Notes:**
- Max length: "Notes cannot exceed 500 characters"

### Form-Level Validation

On "Submit for Approval" click:
1. Check all required fields filled
2. If any validation errors: Show error messages, highlight fields in red
3. Scroll to first error field
4. Do not proceed until all errors resolved

## After Submission

### Developer Experience

**Confirmation Message:**
- Display success message on same page or modal:
  ```
  ✓ Submitted for Approval

  Your deployment request has been sent to the admin team.

  Promotion ID: abc123-def456-ghi789
  Package Version: 1.2.3
  Target Account Group: Production

  You will receive an email notification when an admin approves or denies your request.
  ```

**Actions:**
- "View Promotion Status" button → Returns to Page 3 (read-only)
- "Close" button → Ends flow, user can close window

### Admin Notification

**Email sent to admin group:**
- Subject: "Promotion Approval Needed: Order Processing Main v1.2.3"
- Body includes all submission details
- Link to Flow application opens Page 5 (Approval Queue)

### Flow State

**Swimlane boundary pause:**
- Flow PAUSES at the transition from Developer to Admin swimlane
- Flow state stored with `deploymentRequest` data
- Admin must authenticate with SSO ("Boomi Admins" group) to access Page 5
- Fresh Flow session for admin (separate from developer session)

## Accessibility

- **Keyboard navigation:** Tab through form fields → buttons
- **Screen reader:** Announce field labels, required status, error messages
- **Focus indicators:** Clear visual focus on current field
- **ARIA labels:** Proper labels for all form inputs, error messages
- **Error announcements:** Announce validation errors to screen readers

## User Flow Example

1. **User arrives at Page 4 from Page 3**
   - Form loads with pre-populated package version: "1.2.3"
   - Integration pack dropdown shows options
   - Other fields empty

2. **User selects "Create New Integration Pack"**
   - New Pack Name field appears below dropdown
   - New Pack Description field appears below name

3. **User fills out form:**
   - New Pack Name: "Order Management v3"
   - New Pack Description: "Handles order processing from API to database"
   - Target Account Group: "Production"
   - Deployment Notes: "Deploy during maintenance window on Sunday 2am ET"

4. **User clicks "Submit for Approval"**
   - Form validates: All required fields filled
   - Email sends to admin group
   - Confirmation message displays
   - Flow pauses at swimlane boundary

5. **Admin receives email notification**
   - Subject: "Promotion Approval Needed: Order Processing Main v1.2.3"
   - Email includes all details and link to approval queue

6. **Admin clicks link in email**
   - Opens Flow application
   - Prompted to authenticate via SSO ("Boomi Admins" group)
   - After auth: Arrives at Page 5 (Approval Queue)
   - Sees pending approval request from developer

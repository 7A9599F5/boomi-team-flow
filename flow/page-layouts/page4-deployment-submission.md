# Page 4: Deployment Submission (Developer Swimlane → Peer Review Swimlane Transition)

## Overview

The Deployment Submission page handles three deployment modes based on the `targetEnvironment` and `isHotfix` Flow values set on Page 3 (or Page 9 for test→production promotions). The page adapts its header, form fields, submit button, and post-submission behavior based on the deployment mode.

## Deployment Modes

### Mode 1: Test Deployment (`targetEnvironment = "TEST"`)
- **Header:** "Deploy to Test Environment"
- **Info banner:** Blue/info — "Components will be packaged from your promotion branch and deployed to a test Integration Pack. If no pack exists for this process, an admin will assign one."
- **Submit button label:** "Deploy to Test"
- **On submit:** Directly call `packageAndDeploy` with `deploymentTarget="TEST"`
- **Post-submit:** Show deployment results inline (no swimlane transition):
  - Success with auto-detected IP: Green banner — "Released to Test Integration Pack: {testIntegrationPackName} v{releaseVersion}"
  - Pending pack assignment: Amber banner — "Package created. Pending Integration Pack assignment by admin."
  - "View in Production Readiness" button → Page 9
  - Failure: Red banner with error message, "Retry" button
- **Email:** Simplified "Deployed to Test" notification to submitter only
- **Navigation after:** "Return to Dashboard" button → Page 1

### Mode 2: Production from Test (`targetEnvironment = "PRODUCTION"`, `testPromotionId` populated)
- **Header:** "Submit for Production Deployment"
- **Info banner:** Green/success — "This deployment was previously validated in the test environment."
- **Test deployment summary:** Read-only panel showing test deployment date, test pack name, components
- **Admin assigns IP:** "Admin will select the production Integration Pack during approval."
- **Submit button label:** "Submit for Peer Review"
- **On submit:** Standard peer review workflow (same as current production flow)
- **Post-submit:** Swimlane transition → Peer Review → Admin Approval
- **Email:** "Peer Review Needed" notification (same as current, but includes test deployment reference)

### Mode 3: Emergency Hotfix (`targetEnvironment = "PRODUCTION"`, `isHotfix = "true"`)
- **Header:** "Submit Emergency Hotfix for Peer Review"
- **Warning banner:** Red — "⚠ EMERGENCY HOTFIX: This deployment releases to production first, then syncs to test. Both peer review and admin review are required."
- **Hotfix justification:** Read-only display of justification from Page 3
- **Admin assigns IPs:** "Admin will select Integration Packs during approval."
- **Submit button label:** "Submit Emergency Hotfix for Peer Review"
- **On submit:** Standard peer review workflow with hotfix flag
- **Post-submit:** Swimlane transition → Peer Review → Admin Approval
- **Email:** "EMERGENCY HOTFIX — Peer Review Needed" notification with justification included

## Direct Navigation Guard

Before any page content loads, a Decision step validates required Flow values:

- **Check:** `promotionId` is not null/empty
  - For Mode 1 (test deployment from Page 3): also check `branchId` is present (Process C created it)
  - For Mode 2 (production from test, arriving from Page 9): `branchId` may not be present (deleted after test packaging) — do not require it
- **If `promotionId` missing:** Redirect to Page 1 (Package Browser) with toast message: "No active promotion for deployment"
- **If present:** Continue to page load behavior below

This prevents users from bookmarking or manually navigating to this page without the required promotion context.

## Page Load Behavior

1. **Arrival condition:** User navigates here from Page 3 (Promotion Status) via "Submit for Deployment" button

2. **Pre-populate form fields:**
   - `packageVersion`: From `selectedPackage.packageVersion` (if available)
   - `processName`: From `promotionResults` or `selectedPackage.componentName`
   - `componentsTotal`: From `totalComponents` Flow value
   - `promotionId`: From previous step

3. **Determine deployment mode:**
   - Check `targetEnvironment` Flow value (set by Page 3 or Page 9)
   - Check `isHotfix` Flow value
   - Check `testPromotionId` Flow value (set by Page 9 for test→production)
   - Apply appropriate mode (see Deployment Modes above)

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

### Test Deployment Summary Panel (Mode 2: Production from Test)

**Component Type:** Read-only info panel

**Visibility:** Only shown when `testPromotionId` is populated (arriving from Page 9)

**Content:**
- **Header:** "Previously Tested Deployment"
- **Test Deployed Date:** `{testDeployedAt}` (formatted)
- **Test Integration Pack:** `{testIntegrationPackName}`
- **Promotion ID (Test):** `{testPromotionId}` (with copy button)
- **Components:** `{componentsTotal}` total — `{componentsCreated}` created, `{componentsUpdated}` updated

**Styling:**
- Light green background (#e8f5e9)
- Green left border
- Provides confidence that this deployment was validated

---

### Hotfix Justification Display (Mode 3: Emergency Hotfix)

**Component Type:** Read-only text display

**Visibility:** Only shown when `isHotfix = "true"`

**Content:**
- **Header:** "Emergency Hotfix Justification"
- **Warning icon** and red left border
- **Justification text:** `{hotfixJustification}` (read-only, from Page 3)
- **Submitted by:** `{userEmail}`

**Styling:**
- Light red background (#ffebee)
- Red left border
- Red warning icon

---

### Submit Button

**Component Type:** Button (Primary)

**Configuration:**
- **Label:** (varies by mode — see below)
- **Style:** Primary button (prominent, large)
- **Color:** Accent/success color
- **Icon (optional):** Send/paper plane icon
- **Size:** Large

**Conditional Button Behavior:**

| Mode | Label | Color | On Click |
|------|-------|-------|----------|
| Test | "Deploy to Test" | Blue/primary | Directly call `packageAndDeploy` with `deploymentTarget="TEST"` — no swimlane transition |
| Production from Test | "Submit for Peer Review" | Green/success | Transition to Peer Review swimlane (standard flow) |
| Emergency Hotfix | "Submit Emergency Hotfix for Peer Review" | Red/danger | Transition to Peer Review swimlane with hotfix flags |

**Test Deployment Post-Submit Results:**
When `targetEnvironment = "TEST"`, the `packageAndDeploy` response is displayed inline:
- Success with auto-detected IP: Green banner — "Released to Test Integration Pack: {testIntegrationPackName} v{releaseVersion}"
- Pending pack assignment: Amber banner — "Package created. Pending Integration Pack assignment by admin."
- "View in Production Readiness" button → Page 9
- Failure: Red banner with error message, "Retry" button

**Validation:**
- Check all required fields filled:
  - `packageVersion` not empty
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
     "notes": "{notes}",
     "submittedBy": "{userEmail}",
     "submittedAt": "{timestamp}",
     "processName": "{processName}",
     "componentsTotal": {componentsTotal},
     "devAccountId": "{selectedDevAccountId}",
     "devPackageId": "{selectedPackage.packageId}",
     "devPackageCreator": "{selectedPackage.createdBy}",
     "devPackageVersion": "{selectedPackage.packageVersion}"
   }
   ```

3. **Send email notification to dev + admin groups:**
   - **To:** Dev + Admin distribution lists (e.g., `boomi-developers@company.com`, `boomi-admins@company.com`)
   - **CC:** Submitter (for confirmation)
   - **Subject:** `"Peer Review Needed: {processName} v{packageVersion}"`
   - **Body:**
     ```
     A new promotion has been submitted for peer review.

     PROMOTION DETAILS:
     Promotion ID: {promotionId}
     Process: {processName}
     Package Version: {packageVersion}
     Total Components: {componentsTotal}

     SUBMITTED BY:
     Name: {submitterName}
     Email: {submitterEmail}
     Date: {submittedAt}

     NOTES:
     {deploymentRequest.notes or "No notes provided."}

     Please review in the Promotion Dashboard:
     [Link to Flow peer review page]
     ```

4. **Transition to Peer Review Swimlane:**
   - Flow state PAUSES at swimlane boundary
   - Store `deploymentRequest` in Flow state
   - Show confirmation message to developer:
     ```
     Submitted for peer review!

     Your deployment request has been sent for peer review.
     A team member will review your submission before it advances to admin approval.
     You will receive email notifications as the review progresses.

     Promotion ID: {promotionId}
     ```

5. **End developer flow:**
   - Show "Close" button to exit
   - Peer reviewer must authenticate with SSO (`ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN` group) to continue flow

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
| "Submit for Deployment"                                   |
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
|  Deployment Notes                                        |
|  [_________________________]                             |
|  [_________________________]                             |
|  [_________________________]                             |
|  [_________________________]                             |
|  0 / 500 characters                                      |
|                                                          |
+----------------------------------------------------------+
| FOOTER / ACTION BAR                                      |
| [Cancel]                      [Submit for Peer Review]   |
+----------------------------------------------------------+
```

### Layout Details

**Header:**
- Page title: "Submit for Deployment"
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

**Deployment Notes:**
- Max length: "Notes cannot exceed 500 characters"

### Form-Level Validation

On "Submit for Peer Review" click:
1. Check all required fields filled
2. If any validation errors: Show error messages, highlight fields in red
3. Scroll to first error field
4. Do not proceed until all errors resolved

## After Submission

### Developer Experience

**Confirmation Message:**
- Display success message on same page or modal:
  ```
  Submitted for Peer Review

  Your deployment request has been sent for peer review.
  A team member will review your submission before it advances to admin approval.

  Promotion ID: abc123-def456-ghi789
  Package Version: 1.2.3

  You will receive email notifications as the review progresses.
  ```

**Actions:**
- "View Promotion Status" button → Returns to Page 3 (read-only)
- "Close" button → Ends flow, user can close window

### Peer Review Notification

**Email sent to dev + admin groups:**
- Subject: "Peer Review Needed: Order Processing Main v1.2.3"
- Body includes all submission details
- Link to Flow application opens Page 5 (Peer Review Queue)

### Flow State

**Swimlane boundary pause:**
- Flow PAUSES at the transition from Developer to Peer Review swimlane
- Flow state stored with `deploymentRequest` data
- Peer reviewer must authenticate with SSO (`ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN` group) to access Page 5
- Fresh Flow session for reviewer (separate from developer session)

## Accessibility

- **Keyboard navigation:** Tab through form fields → buttons
- **Screen reader:** Announce field labels, required status, error messages
- **Focus indicators:** Clear visual focus on current field
- **ARIA labels:** Proper labels for all form inputs, error messages
- **Error announcements:** Announce validation errors to screen readers

## User Flow Example

1. **User arrives at Page 4 from Page 3**
   - Form loads with pre-populated package version: "1.2.3"
   - Deployment notes field empty

2. **User fills out form:**
   - Deployment Notes: "Deploy during maintenance window on Sunday 2am ET"

3. **User clicks "Submit for Peer Review"**
   - Form validates: Package version is filled
   - Email sends to dev + admin groups
   - Confirmation message displays
   - Flow pauses at swimlane boundary

4. **Team receives email notification**
   - Subject: "Peer Review Needed: Order Processing Main v1.2.3"
   - Email includes all details and link to peer review queue

5. **Peer reviewer clicks link in email**
   - Opens Flow application
   - Prompted to authenticate via SSO (`ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN` group)
   - After auth: Arrives at Page 5 (Peer Review Queue)
   - Sees pending review request (submitter's own submissions excluded)

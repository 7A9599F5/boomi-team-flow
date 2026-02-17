#### Page 5: Peer Review Queue (Peer Review Swimlane)

Reference: `/flow/page-layouts/page5-peer-review-queue.md` for full UI specification.

Peer reviewer authenticates via SSO ("Boomi Developers" or "Boomi Admins" group) and sees promotions submitted by other users. Own submissions are excluded by the backend.

**Page load:**

1. Message step: action = `queryPeerReviewQueue`, input = `requesterEmail` (from `$User/Email`), output = `pendingPeerReviews` array.
2. Decision step: check success.

**UI components:**

3. **Peer Review Queue Data Grid** bound to `pendingPeerReviews`. Columns: Submitter, Process Name, Components count, Created/Updated counts, **Target Environment** badge (`TEST`/`PRODUCTION`), **Hotfix** badge (red "EMERGENCY HOTFIX" when `isHotfix = "true"`, hidden otherwise), Submitted date (default sort descending), Status badge, Notes (truncated).
4. On row select: Store selected promotion in `selectedPeerReview` Flow value, then navigate to Page 6.
5. **Self-review guard (fallback):** Add a Decision step after row selection comparing `$User/Email` with `selectedPeerReview.initiatedBy`. If equal, show error banner: "You cannot review your own submission."

#### Page 6: Peer Review Detail (Peer Review Swimlane)

Reference: `/flow/page-layouts/page6-peer-review-detail.md` for full UI specification.

Displays full promotion details and allows the peer reviewer to approve or reject.

**UI components:**

1. **Promotion Detail Panel**: Submission details, promotion results table, credential warning (conditional), source account info.
   - **Test Deployment Info** (conditional, shown when `testPromotionId` is non-empty): Displays test deployment date (`testDeployedAt`), Test Integration Pack (`testIntegrationPackName`), branch name, and branch age since test deployment. Labeled "Previously Tested" with a green checkmark.
   - **Hotfix Justification** (conditional, shown when `isHotfix = "true"`): Prominent amber/warning panel displaying the `hotfixJustification` text with "EMERGENCY HOTFIX" header and warning icon.
2. **Peer Review Comments** textarea: Optional for approval, required for rejection. Max 500 characters.
3. **"Approve — Send to Admin Review"** button (green):
   - Confirmation modal summarizing the promotion
   - On confirm: Message step with action = `submitPeerReview`, inputs = `promotionId` + `decision=APPROVED` + `reviewerEmail` + `reviewerName` + `comments`
   - Decision step: check success; handle `SELF_REVIEW_NOT_ALLOWED`, `ALREADY_REVIEWED`, `INVALID_REVIEW_STATE` errors
   - On success: Send email to admins + submitter, transition to Admin swimlane (Page 7)
4. **"Reject"** button (red):
   - Rejection reason modal (required textarea)
   - On confirm: Message step with action = `submitPeerReview`, inputs = `promotionId` + `decision=REJECTED` + `reviewerEmail` + `reviewerName` + `comments`
   - On success: Send rejection email to submitter, end flow
5. **"Back to Peer Review Queue"** link: Navigate to Page 5.

#### Page 7: Admin Approval Queue (Admin Swimlane)

Reference: `/flow/page-layouts/page7-admin-approval-queue.md` for full UI specification.

Admin authenticates via SSO ("Boomi Admins" group) and reviews promotions that have passed peer review.

**Page load:**

1. Message step: action = `queryStatus`, inputs = `status` = "COMPLETED", `deployed` = false, `reviewStage` = "PENDING_ADMIN_REVIEW", output = `pendingApprovals` array (only promotions that passed peer review).
2. Decision step: check success.

**UI components:**

3. **Approval Queue Data Grid** bound to `pendingApprovals`. Columns: Submitter, Process Name, Components count, Created/Updated counts, **Target Environment** badge (`TEST`/`PRODUCTION`), **Hotfix** badge (red "EMERGENCY HOTFIX" when `isHotfix = "true"`, hidden otherwise), **Peer Reviewed By**, Submitted date (default sort descending), Status badge, Notes (truncated).
4. On row select: Expand **Promotion Detail Panel** below the grid. Panel sections: Submission Details (submitter, promotion ID, package version, integration pack, target account group, notes), **Peer Review Information** (reviewed by, reviewed at, decision, comments), Promotion Results (component results mini-table with summary badges), Credential Warning (conditional), Source Account info.
   - **Hotfix Justification** (conditional, shown when `isHotfix = "true"`): Prominent red/danger panel at top of detail section with "EMERGENCY HOTFIX" header, warning icon, and the full `hotfixJustification` text. Ensures admin sees the justification before making a decision.
   - **Test Deployment History** (conditional, shown when `testPromotionId` is non-empty): Panel showing the preceding test deployment details — test date, test Integration Pack, branch age, test deployment status. Labeled "Test Deployment Record" with link to the test PromotionLog entry.
5. **Admin Comments** textarea below the detail panel. Optional, max 500 characters.
5.5. **Hotfix Acknowledgment Checkbox** (conditional, shown when `isHotfix = "true"`): Required checkbox labeled "I acknowledge this is an emergency hotfix bypassing the test environment." Must be checked before the "Approve and Deploy" button is enabled. Positioned between the admin comments and the approve button.
6. **"Approve and Deploy"** button (green, enabled when a row is selected):
   - **Self-approval guard (UI-level):** Add a Decision step comparing `$User/Email` (lowercase) with `selectedPromotion.initiatedBy` (lowercase). If equal, show error banner: "You cannot approve your own promotion. A different admin must approve." The backend (Process D step 2.1) enforces this independently as defense-in-depth.
   - Confirmation modal summarizing process name, version, target, component count
   - On confirm: Message step with action = `packageAndDeploy`, inputs = `promotionId` + `deploymentRequest` + `adminComments` + `approvedBy`, outputs = `deploymentResults` + `deploymentId`
   - Decision step: check success; handle `SELF_APPROVAL_NOT_ALLOWED` error specifically with a user-friendly message; display other results or errors
   - On success: Send approval email to **submitter + peer reviewer** (subject: `"Approved & Deployed: {processName} v{packageVersion}"`), refresh the approval queue
7. **"Deny"** button (red, enabled when a row is selected):
   - Denial reason modal with required textarea
   - On confirm: Delete the promotion branch (`DELETE /Branch/{branchId}` — 200 = deleted, 404 = already deleted, both are success), update promotion status to `ADMIN_REJECTED` with `branchId = null`, send denial email to **submitter + peer reviewer** (subject: `"Admin Denied: {processName} v{packageVersion}"`, body includes denial reason and admin comments), refresh the queue
8. **"View Component Mappings"** link in the page header: Navigate to Page 8.
9. **"View Production Readiness"** link (optional): Navigate to Page 9 (Production Readiness Queue) to see test deployments ready for production promotion. This provides a direct entry point for admins to review test deployment status.

#### Page 8: Mapping Viewer (Admin Swimlane)

Reference: `/flow/page-layouts/page8-mapping-viewer.md` for full UI specification.

Admin views and manages dev-to-prod component ID mappings stored in the DataHub.

**Page load:**

1. Message step: action = `manageMappings`, input = `operation` = "list", output = `mappings` array.
2. Decision step: check success.

**UI components:**

3. **Filter bar** above the grid:
   - Component Type dropdown (All / process / connection / map / profile / operation)
   - Dev Account dropdown (All / list of accessible accounts)
   - Text search input (filters by component name, case-insensitive, 300ms debounce)
   - Apply and Clear buttons
4. **Mapping Data Grid** bound to `mappings`. 8 columns: Component Name, Type (badge), Dev Account (truncated GUID with tooltip), Dev Component ID (truncated GUID), Prod Component ID (truncated GUID), Prod Version, Last Promoted (default sort descending), Promoted By. Pagination at 50 rows per page.
5. **"Export to CSV"** button (top right): Exports the current filtered view to `component-mappings-{date}.csv`.
6. **Manual Mapping Form** (collapsible, collapsed by default): Expand via "Add/Edit Mapping" toggle. Fields: Dev Component ID, Dev Account ID, Prod Component ID, Component Name, Component Type dropdown. CRUD operations use the `manageMappings` action:
   - Create: `operation` = "create" with mapping object
   - Update: `operation` = "update" with mapping ID and changed fields
   - Delete: `operation` = "delete" with mapping ID
   - Each operation followed by a Decision step checking success. On success, refresh the grid and collapse the form. On failure, display the error and keep the form open.
7. **"Back to Admin Approval Queue"** link: Navigate to Page 7.

### Step 5.3 -- Configure SSO

1. In Azure AD (Entra), create or verify two security groups:
   - `Boomi Developers` -- contains all developer users who will browse packages and submit promotions
   - `Boomi Admins` -- contains administrators who approve or deny deployment requests
2. In Boomi Flow, open the Identity connector (Azure AD / Entra).
3. Map each group to the corresponding swimlane(s):
   - `Boomi Developers` -> Developer Swimlane, Peer Review Swimlane
   - `Boomi Admins` -> Peer Review Swimlane, Admin Swimlane
   - **Note**: The Peer Review Swimlane accepts both groups (OR logic). Any developer or admin can peer-review, but self-review is prevented at the backend level.
4. Save the Identity connector configuration.

**Note:** The complete navigation wiring for all 9 pages (Step 5.4) is in [Phase 5a: Flow Dashboard — Developer Swimlane](15-flow-dashboard-developer.md). Refer to that file for the full canvas wiring checklist including Page 9 (Production Readiness Queue) navigation.

**Verify:**

1. Open the published Flow application URL in a browser.
2. **Peer review flow**: Authenticate as a user in the `Boomi Developers` or `Boomi Admins` SSO group (different from the submitter). Verify the pending review appears in the Peer Review Queue (Page 5). Confirm the submitter's own submissions do NOT appear. Select the review, examine the detail page (Page 6), add comments, and click "Approve — Send to Admin Review". Confirm the success message and that both the admin group and submitter receive emails. Also test rejection: select a different review, reject with a reason, and verify the submitter receives the rejection email.
3. **Self-review prevention**: Authenticate as the **same user who submitted**. Verify their own promotion does NOT appear in the Peer Review Queue.
4. **Admin flow**: Authenticate as a user in the `Boomi Admins` SSO group (or follow the link from the peer approval email). Verify the peer-approved request appears in the Admin Approval Queue (Page 7) with the "Peer Reviewed By" column populated. Select it, review the detail panel including peer review information, add admin comments, and click "Approve and Deploy". Confirm the deployment succeeds and both the submitter and peer reviewer receive approval emails. Repeat with a denial to verify the denial flow and email.
5. **Self-approval prevention**: Authenticate as the **same admin who submitted the original promotion**. Click "Approve and Deploy" and verify the backend returns `SELF_APPROVAL_NOT_ALLOWED` error. A different admin must approve.
6. **Mapping Viewer**: From the Admin Approval Queue, click "View Component Mappings". Verify mappings load in the grid, filters work, CSV export downloads, and manual mapping create/update/delete operations succeed.
7. **Production Readiness**: From Page 7, click "View Production Readiness" to navigate to Page 9. Verify test deployments are listed and the "Promote to Production" button navigates to Page 4 in production-from-test mode.

---

### Step 5.5 -- Build and Deploy XmlDiffViewer Custom Component

**Purpose:** Build the React-based XML diff viewer and register it with the Flow custom player.

**Prerequisites:**
- Node.js 18+ and npm
- Flow custom player configured for the tenant

**Build Steps:**

1. **Create React project:**
   - Initialize with webpack or vite
   - Install dependencies: `diff`, `react-diff-view`, `prismjs`

2. **Implement XmlDiffViewer component:**
   - Reference: `flow/custom-components/xml-diff-viewer.md` for full spec
   - Register with `manywho.component.register('XmlDiffViewer', ...)`
   - Support: split/unified toggle, syntax highlighting, context collapse, copy buttons

3. **Build production bundle:**
   - Output: `xml-diff-viewer.js` (< 150KB gzipped) + `xml-diff-viewer.css` (< 10KB)

4. **Upload to Flow tenant:**
   - Navigate to Flow tenant asset management
   - Upload both JS and CSS files
   - Note the asset URLs

5. **Register in custom player:**
   ```javascript
   manywho.initialize({
     tenantId: '{tenant-id}',
     flowId: '{flow-id}',
     customResources: [
       'https://{asset-host}/xml-diff-viewer.js',
       'https://{asset-host}/xml-diff-viewer.css'
     ]
   });
   ```

6. **Add to Flow pages:**
   - On Pages 3, 6, and 7: Add Custom Component element
   - Set component name: `XmlDiffViewer`
   - Bind object data to `generateComponentDiff` response values

**Verify:**
- Load Page 3 after a promotion → click "View Diff" → see side-by-side XML comparison
- Verify syntax highlighting, line numbers, and context collapse work
- Test responsive behavior on tablet/mobile

---

---
Prev: [Phase 5a: Flow Dashboard — Developer Swimlane](15-flow-dashboard-developer.md) | Next: [Phase 6: Testing](17-testing.md) | [Back to Index](index.md)

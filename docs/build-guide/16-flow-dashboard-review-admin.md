#### Page 5: Peer Review Queue (Peer Review Swimlane)

Reference: `/flow/page-layouts/page5-peer-review-queue.md` for full UI specification.

Peer reviewer authenticates via SSO ("Boomi Developers" or "Boomi Admins" group) and sees promotions submitted by other users. Own submissions are excluded by the backend.

**Page load:**

1. Message step: action = `queryPeerReviewQueue`, input = `requesterEmail` (from `$User/Email`), output = `pendingPeerReviews` array.
2. Decision step: check success.

**UI components:**

3. **Peer Review Queue Data Grid** bound to `pendingPeerReviews`. Columns: Submitter, Process Name, Components count, Created/Updated counts, Submitted date (default sort descending), Status badge, Notes (truncated).
4. On row select: Store selected promotion in `selectedPeerReview` Flow value, then navigate to Page 6.
5. **Self-review guard (fallback):** Add a Decision step after row selection comparing `$User/Email` with `selectedPeerReview.initiatedBy`. If equal, show error banner: "You cannot review your own submission."

#### Page 6: Peer Review Detail (Peer Review Swimlane)

Reference: `/flow/page-layouts/page6-peer-review-detail.md` for full UI specification.

Displays full promotion details and allows the peer reviewer to approve or reject.

**UI components:**

1. **Promotion Detail Panel**: Submission details, promotion results table, credential warning (conditional), source account info.
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

3. **Approval Queue Data Grid** bound to `pendingApprovals`. Columns: Submitter, Process Name, Components count, Created/Updated counts, **Peer Reviewed By**, Submitted date (default sort descending), Status badge, Notes (truncated).
4. On row select: Expand **Promotion Detail Panel** below the grid. Panel sections: Submission Details (submitter, promotion ID, package version, integration pack, target account group, notes), **Peer Review Information** (reviewed by, reviewed at, decision, comments), Promotion Results (component results mini-table with summary badges), Credential Warning (conditional), Source Account info.
5. **Admin Comments** textarea below the detail panel. Optional, max 500 characters.
6. **"Approve and Deploy"** button (green, enabled when a row is selected):
   - Confirmation modal summarizing process name, version, target, component count
   - On confirm: Message step with action = `packageAndDeploy`, inputs = `promotionId` + `deploymentRequest` + `adminComments` + `approvedBy`, outputs = `deploymentResults` + `deploymentId`
   - Decision step: check success; display results or error
   - On success: Send approval email to **submitter + peer reviewer** (subject: `"Approved & Deployed: {processName} v{packageVersion}"`), refresh the approval queue
7. **"Deny"** button (red, enabled when a row is selected):
   - Denial reason modal with required textarea
   - On confirm: Update promotion status to ADMIN_REJECTED, send denial email to **submitter + peer reviewer** (subject: `"Admin Denied: {processName} v{packageVersion}"`, body includes denial reason and admin comments), refresh the queue
8. **"View Component Mappings"** link in the page header: Navigate to Page 8.

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

### Step 5.4 -- Wire Navigation

Connect all pages via Outcome elements on the Flow canvas.

1. **Flow start** -> Page 1 (Package Browser) in the Developer swimlane.
2. **Page 1** "Review for Promotion" button outcome -> Page 2 (Promotion Review).
3. **Page 2** "Promote" button (after `executePromotion` Message step + success Decision) -> Page 3 (Promotion Status).
4. **Page 2** "Cancel" button outcome -> Page 1.
5. **Page 3** "Submit for Integration Pack Deployment" button outcome -> Page 4 (Deployment Submission).
6. **Page 3** "Done" button outcome -> End flow.
7. **Page 4** "Submit for Peer Review" button outcome -> Swimlane transition (Developer -> Peer Review) -> Page 5 (Peer Review Queue).
8. **Page 4** "Cancel" button outcome -> Page 3.
9. **Page 5** Row select -> Decision (self-review check) -> Page 6 (Peer Review Detail).
10. **Page 6** "Approve" (after `submitPeerReview` success with decision=APPROVED) -> Swimlane transition (Peer Review -> Admin) -> Page 7 (Admin Approval Queue).
11. **Page 6** "Reject" (after `submitPeerReview` success with decision=REJECTED) -> Email to submitter -> End flow.
12. **Page 6** "Back to Peer Review Queue" link outcome -> Page 5.
13. **Page 7** "Approve and Deploy" (after `packageAndDeploy` success) -> Refresh queue / End flow.
14. **Page 7** "Deny" (after denial confirmation) -> Refresh queue / End flow.
15. **Page 7** "View Component Mappings" link outcome -> Page 8 (Mapping Viewer).
16. **Page 8** "Back to Admin Approval Queue" link outcome -> Page 7.

For every Decision step, wire the **failure outcome** to a shared Error Page that displays `{responseObject.errorMessage}` with Back, Retry, and Home buttons.

**Verify:**

1. Open the published Flow application URL in a browser.
2. **Developer flow**: Authenticate as a user in the `Boomi Developers` SSO group. Select a dev account, browse packages, select a package, click "Review for Promotion", review the dependency tree, click "Promote to Primary Account", confirm, wait for results on the status page, and click "Submit for Integration Pack Deployment". Fill out the deployment form and submit. Confirm you see the "Submitted for peer review!" message and receive a confirmation email.
3. **Peer review flow**: Authenticate as a **different** user in the `Boomi Developers` or `Boomi Admins` SSO group (or follow the link from the notification email). Verify the pending review appears in the Peer Review Queue (Page 5). Confirm the submitter's own submissions do NOT appear. Select the review, examine the detail page (Page 6), add comments, and click "Approve — Send to Admin Review". Confirm the success message and that both the admin group and submitter receive emails. Also test rejection: select a different review, reject with a reason, and verify the submitter receives the rejection email.
4. **Self-review prevention**: Authenticate as the **same user who submitted**. Verify their own promotion does NOT appear in the Peer Review Queue.
5. **Admin flow**: Authenticate as a user in the `Boomi Admins` SSO group (or follow the link from the peer approval email). Verify the peer-approved request appears in the Admin Approval Queue (Page 7) with the "Peer Reviewed By" column populated. Select it, review the detail panel including peer review information, add admin comments, and click "Approve and Deploy". Confirm the deployment succeeds and both the submitter and peer reviewer receive approval emails. Repeat with a denial to verify the denial flow and email.
6. **Mapping Viewer**: From the Admin Approval Queue, click "View Component Mappings". Verify mappings load in the grid, filters work, CSV export downloads, and manual mapping create/update/delete operations succeed.

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

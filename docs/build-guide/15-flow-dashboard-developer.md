## Phase 5: Flow Dashboard

### Step 5.1 -- Install Connector

1. In Boomi Flow, navigate to **Services -> Connectors -> New Connector**.
2. Select connector type: **Boomi Integration Service**.
3. Configure the connection:
   - **Runtime Type**: Public Cloud
   - **Path to Service**: `/fs/PromotionService`
   - **Authentication**: Basic
     - **Username**: the shared web server user (from **Shared Web Server User Management** in AtomSphere)
     - **Password**: the API token for that user
4. Click **"Retrieve Connector Configuration Data"**. Flow contacts the deployed Flow Service and auto-discovers all 12 message actions. Wait for the operation to complete.
5. Verify the auto-generated Flow Types. You should see exactly 24 types (one request and one response for each action):
   1. `getDevAccounts REQUEST - getDevAccountsRequest`
   2. `getDevAccounts RESPONSE - getDevAccountsResponse`
   3. `listDevPackages REQUEST - listDevPackagesRequest`
   4. `listDevPackages RESPONSE - listDevPackagesResponse`
   5. `resolveDependencies REQUEST - resolveDependenciesRequest`
   6. `resolveDependencies RESPONSE - resolveDependenciesResponse`
   7. `executePromotion REQUEST - executePromotionRequest`
   8. `executePromotion RESPONSE - executePromotionResponse`
   9. `packageAndDeploy REQUEST - packageAndDeployRequest`
   10. `packageAndDeploy RESPONSE - packageAndDeployResponse`
   11. `queryStatus REQUEST - queryStatusRequest`
   12. `queryStatus RESPONSE - queryStatusResponse`
   13. `manageMappings REQUEST - manageMappingsRequest`
   14. `manageMappings RESPONSE - manageMappingsResponse`
   15. `queryPeerReviewQueue REQUEST - queryPeerReviewQueueRequest`
   16. `queryPeerReviewQueue RESPONSE - queryPeerReviewQueueResponse`
   17. `submitPeerReview REQUEST - submitPeerReviewRequest`
   18. `submitPeerReview RESPONSE - submitPeerReviewResponse`
   19. `listIntegrationPacks REQUEST - listIntegrationPacksRequest`
   20. `listIntegrationPacks RESPONSE - listIntegrationPacksResponse`
   21. `generateComponentDiff REQUEST - generateComponentDiffRequest`
   22. `generateComponentDiff RESPONSE - generateComponentDiffResponse`
   23. `queryTestDeployments REQUEST - queryTestDeploymentsRequest`
   24. `queryTestDeployments RESPONSE - queryTestDeploymentsResponse`
6. Open the **Configuration Values** section of the connector. Set `primaryAccountId` to your primary Boomi account ID.
7. Click **Install**, then **Save**.

**Verify:** Open the connector and confirm all 24 types appear under **Types**. If any are missing, click "Retrieve Connector Configuration Data" again and check that the Flow Service is deployed and all 12 listeners are running.

### Step 5.2 -- Create Flow Application

1. Navigate to **Flow -> Build -> New Flow**.
2. Name: `Promotion Dashboard`.
3. Add **Developer Swimlane**:
   - Authorization: SSO group `Boomi Developers`
   - This swimlane is the entry point for the application
4. Add **Peer Review Swimlane**:
   - Authorization: SSO groups `Boomi Developers` OR `Boomi Admins` (any listed group grants access)
   - This swimlane receives control after the developer submits for peer review
   - Note: Boomi Flow supports multiple SSO groups per swimlane with OR logic
5. Add **Admin Swimlane**:
   - Authorization: SSO group `Boomi Admins`
   - This swimlane receives control after peer review passes

Build the 8 pages in order. Each page uses Message steps to call Flow Service actions and Decision steps to handle the `success` field in responses.

#### Page 1: Package Browser (Developer Swimlane)

Reference: `/flow/page-layouts/page1-package-browser.md` for full UI specification.

This is the developer entry point. Users select a dev account and browse available packages.

**Page load -- Message step configuration:**

1. Add a **Message** step on the page load event.
   - **Action**: `getDevAccounts`
   - **Connector**: `Promotion Service Connector`
   - **Input values**: Bind `userSsoGroups` from the SSO authorization context (the user's Azure AD group memberships)
   - **Output values**: Bind response to `accessibleAccounts` Flow value (list of dev accounts with `devAccountId` and `devAccountName` fields)
2. Add a **Decision** step immediately after the Message step.
   - **Condition**: `{getDevAccountsResponse.success} == true`
   - **True path**: Continue to render page UI
   - **False path**: Navigate to Error Page with `{getDevAccountsResponse.errorMessage}`

**UI components:**

3. Add an **Account Selector** combobox:
   - Data source: `accessibleAccounts`
   - Display field: `devAccountName`
   - Value field: `devAccountId`
   - On change: Store selected value in `selectedDevAccountId` and `selectedDevAccountName` Flow values, then trigger a second Message step
4. Add the on-change **Message** step for the combobox:
   - **Action**: `listDevPackages`
   - **Input values**: `selectedDevAccountId`
   - **Output values**: `packages` (array of package objects)
   - **Decision**: Check `{listDevPackagesResponse.success} == true`; on failure, show error
5. Add a **Packages Data Grid** bound to the `packages` output. Columns: Package Name, Version, Type, Created (default sort descending), Notes.
6. On row select: Store the entire row object in `selectedPackage` Flow value (contains `componentId`, `packageId`, `componentName`, `packageVersion`).
7. Add a **"Review for Promotion"** button:
   - Enabled when `selectedPackage` is not null
   - On click: Navigate to Page 2

**Flow values set on this page:** `selectedDevAccountId`, `selectedDevAccountName`, `selectedPackage`, `accessibleAccounts`.

#### Page 2: Promotion Review (Developer Swimlane)

Reference: `/flow/page-layouts/page2-promotion-review.md` for full UI specification.

Displays the resolved dependency tree and allows the developer to execute promotion.

**Page load:**

1. Message step: action = `resolveDependencies`, inputs = `selectedPackage.componentId` + `selectedDevAccountId`, outputs = `dependencyTree` (list), `totalComponents`, `newCount`, `updateCount`, `envConfigCount`.
2. Decision step: check `{resolveDependenciesResponse.success} == true`. Failure path goes to Error Page.

**UI components:**

3. **Summary labels**: Root Process name, Total Components count, badges for "X to create", "Y to update", "Z with credentials to reconfigure" (conditional on `envConfigCount > 0`).
4. **Dependency Tree Data Grid** bound to `dependencyTree`. Columns: Component Name (bold for root), Type (badge), Dev Version, Prod Status (NEW/UPDATE badge), Prod Component ID (truncated GUID), Prod Version, Env Config (warning icon). Grid is pre-sorted by dependency order (profiles first, root process last) and not user-sortable.
5. **"Promote to Primary Account"** button:
   - On click: Show confirmation modal summarizing counts
   - On confirm: Message step with action = `executePromotion`, inputs = `selectedPackage.componentId` + `selectedDevAccountId` + `dependencyTree`, outputs = `promotionId`, `promotionResults`, `componentsCreated`, `componentsUpdated`, `componentsFailed`
   - Decision step: check success. On true: navigate to Page 3. On false: navigate to Error Page
   - The Flow Service handles async wait responses automatically; the user sees a spinner during execution
6. **"Cancel"** button: Navigate back to Page 1.

#### Page 3: Promotion Status (Developer Swimlane)

Reference: `/flow/page-layouts/page3-promotion-status.md` for full UI specification.

Displays results after `executePromotion` completes. The Flow Service returns wait responses during long-running promotion; the user sees a spinner and can safely close the browser.

**UI components (after completion):**

1. **Summary section**: Promotion ID (copyable), badges for Created/Updated/Failed counts.
2. **Results Data Grid** bound to `promotionResults`. Columns: Component Name, Action (CREATE/UPDATE badge), Status (SUCCESS/FAILED badge), Prod Component ID, Prod Version, Config Stripped (warning icon if true), Error message (red text, truncated with tooltip).
3. **Credential Warning box** (conditional): Shown when any component has `configStripped = true`. Lists affected component names and instructions for reconfiguration in the primary account Build tab.
4. **"Submit for Integration Pack Deployment"** button:
   - Enabled only when `componentsFailed == 0`
   - On click: Navigate to Page 4
5. **"Done"** button: End flow.

#### Page 4: Deployment Submission (Developer to Peer Review Transition)

Reference: `/flow/page-layouts/page4-deployment-submission.md` for full UI specification.

The developer fills out deployment details and submits for peer review. This page marks the transition between the Developer and Peer Review swimlanes — the first step of the 2-layer approval workflow.

**Form components:**

1. **Package Version** text input: Pre-populated from `selectedPackage.packageVersion`. Required.
2. **Integration Pack Selector** combobox: Options include "Create New Integration Pack" (special value) and existing packs. On "Create New" selection, show conditional fields below.
3. **New Pack Name** text input (conditional): Shown when "Create New" is selected. Required when visible.
4. **New Pack Description** textarea (conditional): Shown when "Create New" is selected. Optional.
5. **Target Account Group** combobox: Populated from available account groups. Required.
6. **Deployment Notes** textarea: Optional, max 500 characters.

**Submit behavior:**

7. **"Submit for Peer Review"** button:
   - Validates all required fields
   - Builds the `deploymentRequest` object with `promotionId`, `packageVersion`, `integrationPackId` (or `createNewPack` + `newPackName`), `targetAccountGroupId`, `notes`, `submittedBy`, `processName`, `componentsTotal`
   - Sends email notification to dev + admin distribution lists:
     - **To**: dev group + admin group emails (e.g., `boomi-developers@company.com`, `boomi-admins@company.com`)
     - **Subject**: `"Peer Review Needed: {processName} v{packageVersion}"`
     - **Body**: Promotion ID, process name, package version, component counts, deployment details, submitter info, and a link to the peer review queue
   - Transitions to the **Peer Review swimlane** -- the flow pauses at the swimlane boundary
   - Developer sees a confirmation message ("Submitted for peer review!") with the Promotion ID, then the flow ends for them
8. **"Cancel"** button: Navigate back to Page 3.

---
Prev: [Phase 4: Flow Service Component](14-flow-service.md) | Next: [Phase 5b: Flow Dashboard — Review & Admin](16-flow-dashboard-review-admin.md) | [Back to Index](index.md)

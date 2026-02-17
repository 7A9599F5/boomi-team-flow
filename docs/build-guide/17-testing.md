## Phase 6: Testing

### Smoke Test Sequence (5-Minute Check)

Before running the full test suite, perform this quick end-to-end validation:

1. **DataHub** -- Query the ComponentMapping model for any existing records. Expect either an empty result set or known seed data. If the query fails, stop and resolve Phase 1 issues before proceeding.
2. **Flow Service** -- POST a `getDevAccounts` request to `https://{your-cloud-base-url}/fs/PromotionService`. Expect a JSON response with `success: true` and a list of accessible dev accounts (or an empty list if no DevAccountAccess records are seeded).
3. **Flow Dashboard** -- Open the Promotion Dashboard URL in a browser. Verify the page loads, the Package Browser (Page 1) renders, and the dev account dropdown populates.

If all three checks pass, proceed to the full test suite below.

---

### Test 1 -- DataHub CRUD

Validate that the DataHub models accept records, enforce match rules, and support upsert behavior.

#### 1a. Create a Test Record

POST a test ComponentMapping record using the template at `datahub/api-requests/create-golden-record-test.xml`:

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/create" \
  -H "Content-Type: application/xml" \
  -d @datahub/api-requests/create-golden-record-test.xml
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = Get-Content -Raw datahub/api-requests/create-golden-record-test.xml
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/create" `
  -Method POST -Headers $headers -Body $body
```

#### 1b. Query the Test Record

Query the record back using the template at `datahub/api-requests/query-golden-record-test.xml`:

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d @datahub/api-requests/query-golden-record-test.xml
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = Get-Content -Raw datahub/api-requests/query-golden-record-test.xml
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body $body
```

**Expected output** (truncated):

```xml
<RecordQueryResponse totalCount="1">
  <record>
    <field name="devComponentId">test-dev-comp-001</field>
    <field name="devAccountId">TEST_DEV_ACCT</field>
    <field name="prodComponentId">test-prod-comp-001</field>
    <field name="componentName">Test Connection</field>
    <field name="componentType">connection</field>
    <field name="prodLatestVersion">1</field>
    ...
  </record>
</RecordQueryResponse>
```

**Pass criteria:** `totalCount="1"`, `devComponentId` and `devAccountId` match the values from the create request.

#### 1c. Upsert Test (No Duplicate)

POST the same `create-golden-record-test.xml` a second time. Then query again using step 1b.

**Pass criteria:** `totalCount` is still `1`. The record ID is unchanged. The match rule on `devComponentId` + `devAccountId` prevented a duplicate.

#### 1d. Clean Up

Delete the test record via the DataHub UI or API to avoid polluting production data.

---

### Test 2 -- Single Component Promotion

Run the Flow Dashboard and promote a simple package with no dependencies (a single connection or profile).

1. Open the Promotion Dashboard.
2. Select a dev account from the dropdown (Page 1).
3. Select a package containing a single component (no child references).
4. Proceed to Promotion Review (Page 2) and click Promote.
5. Wait for the Promotion Status (Page 3) to show COMPLETED.

#### Verification: Component Exists in Primary Account

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{prodComponentId}"
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    Accept         = "application/xml"
}
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{prodComponentId}" `
  -Method GET -Headers $headers
```

**Expected output** (truncated):

```xml
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId="{prodComponentId}" version="1"
    name="{componentName}" type="{componentType}"
    folderFullPath="/Promoted{devFolderFullPath}">
  <bns:object>...</bns:object>
</bns:Component>
```

**Pass criteria:** Component exists, `version="1"`, `folderFullPath` starts with `/Promoted/`.

#### Verification: DataHub Mapping Created

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="10">
  <view><fieldId>devComponentId</fieldId><fieldId>prodComponentId</fieldId><fieldId>prodLatestVersion</fieldId></view>
  <filter op="AND">
    <fieldValue><fieldId>devComponentId</fieldId><operator>EQUALS</operator><value>{devComponentId}</value></fieldValue>
    <fieldValue><fieldId>devAccountId</fieldId><operator>EQUALS</operator><value>{devAccountId}</value></fieldValue>
  </filter>
</RecordQueryRequest>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = @"
<RecordQueryRequest limit="10">
  <view><fieldId>devComponentId</fieldId><fieldId>prodComponentId</fieldId><fieldId>prodLatestVersion</fieldId></view>
  <filter op="AND">
    <fieldValue><fieldId>devComponentId</fieldId><operator>EQUALS</operator><value>{devComponentId}</value></fieldValue>
    <fieldValue><fieldId>devAccountId</fieldId><operator>EQUALS</operator><value>{devAccountId}</value></fieldValue>
  </filter>
</RecordQueryRequest>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body $body
```

**Pass criteria:** `totalCount="1"`, `prodComponentId` is populated, `prodLatestVersion` is `1`.

**Verify:** PromotionLog shows `status=COMPLETED`, `componentsCreated=1`, `componentsFailed=0`.

---

### Test 3 -- Re-Promote (Version Increment)

Promote the same package from Test 2 a second time.

1. Repeat the flow steps from Test 2 with the same package.
2. On Page 2 (Promotion Review), the dependency tree should show the component as UPDATE (not NEW).

#### Verification: Version Incremented

Run the same GET Component command from Test 2.

**Pass criteria:** Same `componentId`, `version` is now greater than `1` (API auto-increments).

#### Verification: DataHub Mapping Updated

Run the same DataHub query from Test 2.

**Pass criteria:**
- Same record ID (no duplicate created)
- `prodLatestVersion` incremented (now `2` or higher)
- `lastPromotedAt` updated to a more recent timestamp than Test 2

---

### Test 4 -- Full Dependency Tree

Select a package containing a process with dependencies (process references connections, profiles, maps, and/or sub-processes).

1. Open the Promotion Dashboard and select the complex package.
2. On Page 2 (Promotion Review), verify the dependency tree shows all components with correct types.
3. Click Promote and wait for COMPLETED status.

#### Verification: All Components Promoted

Query ComponentMapping for all components in the tree:

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="200">
  <view>
    <fieldId>devComponentId</fieldId><fieldId>componentName</fieldId>
    <fieldId>componentType</fieldId><fieldId>prodComponentId</fieldId>
  </view>
  <filter op="AND">
    <fieldValue><fieldId>devAccountId</fieldId><operator>EQUALS</operator><value>{devAccountId}</value></fieldValue>
  </filter>
</RecordQueryRequest>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = @"
<RecordQueryRequest limit="200">
  <view>
    <fieldId>devComponentId</fieldId><fieldId>componentName</fieldId>
    <fieldId>componentType</fieldId><fieldId>prodComponentId</fieldId>
  </view>
  <filter op="AND">
    <fieldValue><fieldId>devAccountId</fieldId><operator>EQUALS</operator><value>{devAccountId}</value></fieldValue>
  </filter>
</RecordQueryRequest>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body $body
```

**Pass criteria:**
- `totalCount` matches the `totalComponents` value from the promotion response
- Every component in the tree has a `prodComponentId` populated
- Bottom-up processing order was respected: profiles (priority 1) created before connections (priority 2) before operations (priority 3) before maps (priority 4) before sub-processes (priority 5) before root process (priority 6). Confirm by checking `lastPromotedAt` timestamps or the PromotionLog `resultDetail` field.

---

### Test 5 -- Approval Workflow

After a successful promotion (Test 2 or Test 4), submit for deployment.

1. On Page 4 (Deployment Submission), fill in the package version and deployment notes.
2. Click Submit -- the flow transitions to the Peer Review swimlane and sends an email notification.
3. Log in as a different developer or admin (peer reviewer, member of "Boomi Developers" or "Boomi Admins" SSO group).
4. Open Page 5 (Peer Review Queue), locate the pending review, and click Approve on Page 6 (Peer Review Detail).
5. Log in as an admin user (member of "Boomi Admins" SSO group).
6. Open Page 7 (Admin Approval Queue), locate the peer-approved request, and click Approve.
7. Verify the deployment completes.

#### Verification: Integration Pack Exists

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/json" \
  "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/IntegrationPack/{integrationPackId}"
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization = "Basic $cred"
    Accept        = "application/json"
}
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/IntegrationPack/{integrationPackId}" `
  -Method GET -Headers $headers
```

**Pass criteria:** Integration Pack exists, contains the promoted component, deployment status shows success.

---

### Test 6 -- Error Recovery

Simulate a failure by promoting a component that will fail mid-tree (for example, temporarily revoke API access to a referenced component, or corrupt a component reference).

1. Trigger the promotion and wait for the FAILED/PARTIAL status on Page 3.

#### Verification: PromotionLog Shows Failure

Query the PromotionLog model:

```bash
# Linux/macOS
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="10">
  <view>
    <fieldId>promotionId</fieldId><fieldId>status</fieldId>
    <fieldId>componentsFailed</fieldId><fieldId>errorMessage</fieldId>
  </view>
  <filter op="AND">
    <fieldValue><fieldId>promotionId</fieldId><operator>EQUALS</operator><value>{promotionId}</value></fieldValue>
  </filter>
</RecordQueryRequest>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{
    Authorization  = "Basic $cred"
    "Content-Type" = "application/xml"
}
$body = @"
<RecordQueryRequest limit="10">
  <view>
    <fieldId>promotionId</fieldId><fieldId>status</fieldId>
    <fieldId>componentsFailed</fieldId><fieldId>errorMessage</fieldId>
  </view>
  <filter op="AND">
    <fieldValue><fieldId>promotionId</fieldId><operator>EQUALS</operator><value>{promotionId}</value></fieldValue>
  </filter>
</RecordQueryRequest>
"@
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body $body
```

**Pass criteria:**
- `status` is `FAILED`
- `componentsFailed` is `>= 1`
- `errorMessage` describes the failure
- The failed component's dependents are marked SKIPPED in the `resultDetail` field

2. Fix the underlying issue (restore API access, correct the reference).
3. Re-run the same promotion.

**Pass criteria for re-run:**
- Previously promoted components show as UPDATE (not duplicated)
- Previously SKIPPED components now succeed (become CREATE or UPDATE)
- PromotionLog for the new run shows `status=COMPLETED`

---

### Test 7 -- Browser Resilience

1. Start a promotion via the Flow Dashboard (click Promote on Page 2).
2. While the promotion is executing (before the status page loads), close the browser tab.
3. Reopen the same Flow Dashboard URL.

**Pass criteria:**
- The Flow state is restored from IndexedDB -- the user returns to Page 3 (Promotion Status) or the current step in the flow
- The promotion completed successfully in the background (the Integration process continues regardless of browser state)
- Verify the PromotionLog shows `status=COMPLETED` using the query from Test 6

---

### Test 8 -- Dev → Test → Production (Happy Path)

Run the full 3-tier deployment lifecycle.

1. Execute a promotion via Process C — creates branch, promotes components to branch.
2. On Page 3 (Promotion Status), select "Deploy to Test" (default).
3. On Page 4 (Deployment Submission), deploy to a Test Integration Pack.
4. Wait for test deployment to complete (inline results on Page 4).

#### Verification: Test Deployment

- PromotionLog shows `targetEnvironment = "TEST"`, `status = "TEST_DEPLOYED"`, `testDeployedAt` populated
- `testIntegrationPackId` and `testIntegrationPackName` populated
- Branch is preserved: `GET /Branch/{branchId}` returns `200` with `ready = true`
- `branchId` still set in PromotionLog (not null)

5. Navigate to Page 9 (Production Readiness Queue).
6. Verify the test deployment appears in the queue with correct branch age.
7. Select it and click "Promote to Production".
8. On Page 4, submit for peer review (production mode).
9. Complete peer review (Pages 5-6) — approve.
10. Complete admin review (Page 7) — approve and deploy to production.

#### Verification: Production Deployment

- PromotionLog for production record shows `targetEnvironment = "PRODUCTION"`, `status = "DEPLOYED"`
- `testPromotionId` links back to the test deployment's `promotionId`
- Branch is deleted: `GET /Branch/{branchId}` returns `404`
- `branchId` set to null in PromotionLog
- Integration Pack deployed to production environment(s)

**Pass criteria:** Full 3-tier flow completes. Both PromotionLog records correctly linked via `testPromotionId`. Branch created once, preserved through test, deleted after production deploy.

---

### Test 9 -- Emergency Hotfix (Dev → Production)

Test the emergency hotfix bypass path.

1. Execute a promotion via Process C — creates branch.
2. On Page 3 (Promotion Status), select "Deploy to Production (Emergency Hotfix)".
3. Enter hotfix justification (required field).
4. Click "Continue to Deployment".
5. On Page 4, submit for peer review with hotfix flag.

#### Verification: Peer Review Queue

- On Pages 5-6, verify the EMERGENCY HOTFIX badge is visible on the queue row.
- On Page 6 (detail), verify `hotfixJustification` is displayed prominently.
- Peer reviewer approves.

6. On Page 7 (Admin Approval Queue), verify:
   - Hotfix badge and warning displayed prominently.
   - `hotfixJustification` visible in the detail panel.
   - Extra acknowledgment checkbox present for hotfix approvals.
7. Admin checks the acknowledgment checkbox and approves.

#### Verification: Hotfix Deployment

- PromotionLog shows `targetEnvironment = "PRODUCTION"`, `isHotfix = "true"`, `hotfixJustification` populated
- `status = "DEPLOYED"`
- Branch is deleted
- No `testPromotionId` (bypassed test)

**Pass criteria:** Hotfix deploys directly to production. Hotfix justification visible at every review stage. Acknowledgment required from admin.

---

### Test 10 -- Multi-Environment Rejection Scenarios

Test rejection at each stage of the multi-environment workflow.

#### 10a. Peer Rejection of Hotfix

1. Submit a hotfix for peer review (follow Test 9 steps 1-5).
2. Peer reviewer rejects with reason.

**Pass criteria:**
- PromotionLog shows `peerReviewStatus = "PEER_REJECTED"`
- Branch is deleted (rejection triggers branch cleanup)
- Submitter receives rejection email with hotfix context

#### 10b. Admin Denial of Production from Test

1. Complete a test deployment (follow Test 8 steps 1-4).
2. Submit for production promotion (Test 8 steps 5-9).
3. Admin denies with reason.

**Pass criteria:**
- PromotionLog for production record shows `adminReviewStatus = "ADMIN_REJECTED"`
- Branch is deleted
- Submitter + peer reviewer receive denial emails
- Test deployment record remains unchanged (`status = "TEST_DEPLOYED"`)

#### 10c. Test Deployment Failure with Retry

1. Trigger a test deployment that will fail (e.g., invalid environment ID).
2. Verify Page 4 shows the deployment error inline.

**Pass criteria:**
- PromotionLog shows `status = "TEST_DEPLOY_FAILED"`
- Branch is preserved (not deleted on test failure — allows retry)
- Developer can retry the test deployment from Page 4

---

---

### Test 11 -- Component Diff Generation (Process G)

Validate that Process G fetches branch and main component XML and returns normalized output for diff rendering.

#### 11a. Diff for Updated Component

After a successful promotion (Test 2 or Test 4), generate a diff for a component that was updated (not created):

1. Call `generateComponentDiff` with:
   - `branchId`: the promotion branch ID from the executePromotion response
   - `prodComponentId`: a component that existed before promotion (action = "UPDATE")
   - `componentName`: the component's display name
   - `componentAction`: `"UPDATE"`

**Pass criteria:**
- `success` is `true`
- `branchXml` contains the normalized XML from the promotion branch (non-empty)
- `mainXml` contains the normalized XML from main branch (non-empty)
- `branchVersion` > `mainVersion`
- Both XML strings are well-formed and consistently formatted (indentation, attribute ordering)

#### 11b. Diff for New Component

Generate a diff for a component that was newly created during promotion:

1. Call `generateComponentDiff` with:
   - `branchId`: the promotion branch ID
   - `prodComponentId`: a component that was created during promotion (action = "CREATE")
   - `componentAction`: `"CREATE"`

**Pass criteria:**
- `success` is `true`
- `branchXml` contains the normalized component XML (non-empty)
- `mainXml` is an empty string (no prior version on main)
- `mainVersion` is `0`

#### 11c. Diff for Non-Existent Component

Call `generateComponentDiff` with an invalid `prodComponentId`:

**Pass criteria:**
- `success` is `false`
- `errorCode` is `COMPONENT_NOT_FOUND`
- `errorMessage` describes which component ID was not found

---

### Test 12 -- Integration Pack Listing (Process J)

Validate that Process J retrieves Integration Packs with filtering and smart suggestion.

#### 12a. List All Packs

Call `listIntegrationPacks` with no filters (or `packPurpose = "ALL"`):

**Pass criteria:**
- `success` is `true`
- `integrationPacks` array contains all MULTI-type Integration Packs in the primary account
- Each entry has `packId`, `packName`, `packDescription`, `installationType`

#### 12b. Filter by Purpose

Call `listIntegrationPacks` with `packPurpose = "TEST"`:

**Pass criteria:**
- `integrationPacks` array contains only packs with names ending in `"- TEST"`

Call again with `packPurpose = "PRODUCTION"`:

**Pass criteria:**
- `integrationPacks` array contains only packs without the `"- TEST"` suffix

#### 12c. Smart Suggestion

After completing at least one deployment (Test 8 or Test 9), call `listIntegrationPacks` with `suggestForProcess` set to the deployed process name:

**Pass criteria:**
- `suggestedPackId` is populated and matches the most recently used pack for that process
- `suggestedPackName` matches the pack name

#### 12d. No Packs Available

Call `listIntegrationPacks` against an account with no Integration Packs (or filter to a purpose with no matching packs):

**Pass criteria:**
- `success` is `true`
- `integrationPacks` is an empty array
- `suggestedPackId` is absent or null

---

### Test 13 -- Mapping Management (Process F)

Validate CRUD operations on ComponentMapping records via the `manageMappings` action.

#### 13a. Create Mapping

Call `manageMappings` with `action = "query"` and `devComponentId` set to a known unmapped component:

**Pass criteria:** `mappings` array is empty (no existing mapping).

Then seed a mapping by calling the DataHub API directly (admin seeding workflow) or by promoting the component. After seeding, call `manageMappings` with `action = "query"` and the same `devComponentId`:

**Pass criteria:**
- `mappings` array contains exactly 1 record
- `devComponentId` and `prodComponentId` are correctly populated
- `componentName` and `componentType` match the seeded values

#### 13b. Update Mapping

Call `manageMappings` with `action = "update"`, providing the `devComponentId` and a corrected `prodComponentId`:

**Pass criteria:**
- `success` is `true`
- Re-query shows the updated `prodComponentId`
- Record count remains 1 (no duplicate created)

#### 13c. Delete Mapping

Call `manageMappings` with `action = "delete"` and the `devComponentId`:

**Pass criteria:**
- `success` is `true`
- Re-query returns empty `mappings` array

#### 13d. Query Non-Existent Mapping

Call `manageMappings` with `action = "query"` and a `devComponentId` that has no mapping:

**Pass criteria:**
- `success` is `true`
- `mappings` array is empty (not an error)

---

### Test 14 -- Test Deployment Queue (Process E4)

Validate that Process E4 returns test-deployed promotions ready for production promotion.

#### 14a. Query After Test Deployment

After completing a test deployment (Test 8 steps 1-4), call `queryTestDeployments`:

**Pass criteria:**
- `success` is `true`
- `testDeployments` array contains the test-deployed promotion
- Entry includes: `promotionId`, `processName`, `devAccountId`, `initiatedBy`, `testDeployedAt`, `testIntegrationPackId`, `testIntegrationPackName`, `branchId`, `branchName`
- `branchId` is non-null (branch preserved from test phase)

#### 14b. Exclusion After Production Promotion

After promoting a test deployment to production (Test 8 steps 5-10), call `queryTestDeployments` again:

**Pass criteria:**
- The previously test-deployed promotion no longer appears in `testDeployments` (it has been promoted to production and should be excluded)

#### 14c. Filter by Dev Account

Call `queryTestDeployments` with `devAccountId` set to a specific dev account:

**Pass criteria:**
- `testDeployments` array contains only promotions from that dev account

#### 14d. No Test Deployments

Call `queryTestDeployments` when no promotions are in TEST_DEPLOYED status:

**Pass criteria:**
- `success` is `true`
- `testDeployments` is an empty array

---

### Test 15 -- Negative / Error Path Tests

Validate that the system returns correct error codes and messages for known failure scenarios.

#### 15a. MISSING_CONNECTION_MAPPINGS

**Setup:** Identify a process that references a connection with no ComponentMapping record in DataHub (no admin-seeded mapping exists for the connection's dev component ID).

**Trigger:** Call `executePromotion` with the process's dependency tree.

**Expected result:**
- `success` is `false`
- `errorCode` is `MISSING_CONNECTION_MAPPINGS`
- `errorMessage` describes which connection mappings are missing
- `missingConnectionMappings` array is populated with entries containing `devComponentId`, `name`, `type`, `devAccountId`
- No branch is created (pre-validation fails before branch creation)

#### 15b. SELF_REVIEW_NOT_ALLOWED

**Setup:** Complete a promotion and submit it for peer review. Note the `initiatedBy` email.

**Trigger:** Call `submitPeerReview` with `reviewerEmail` set to the same email as `initiatedBy` (test with matching case and different case to verify case-insensitive comparison).

**Expected result:**
- `success` is `false`
- `errorCode` is `SELF_REVIEW_NOT_ALLOWED`
- `errorMessage` indicates the reviewer cannot review their own submission
- PromotionLog `peerReviewStatus` remains `PENDING_PEER_REVIEW` (no state change)

#### 15c. BRANCH_LIMIT_REACHED

**Setup:** Create 15+ active promotion branches in the primary account (or mock the branch count query to return 15+).

**Trigger:** Call `executePromotion` with a new package.

**Expected result:**
- `success` is `false`
- `errorCode` is `BRANCH_LIMIT_REACHED`
- `errorMessage` indicates the branch limit has been reached and suggests waiting for pending reviews to complete
- No new branch is created

#### 15d. PROMOTION_IN_PROGRESS

**Setup:** Start a promotion for a dev account (leave it in IN_PROGRESS status).

**Trigger:** Call `executePromotion` again for the same dev account before the first promotion completes.

**Expected result:**
- `success` is `false`
- `errorCode` is `PROMOTION_IN_PROGRESS`
- `errorMessage` indicates a promotion is already in progress for this account
- No new branch is created (concurrency guard blocks the second promotion)

#### 15e. ALREADY_REVIEWED

**Setup:** Complete a promotion, submit for peer review, and have a peer reviewer approve it.

**Trigger:** Call `submitPeerReview` again for the same `promotionId` (from a different reviewer).

**Expected result:**
- `success` is `false`
- `errorCode` is `ALREADY_REVIEWED`
- `errorMessage` indicates the promotion has already been peer-reviewed
- PromotionLog `peerReviewStatus` remains `PEER_APPROVED` (no state change)

#### 15f. COMPONENT_NOT_FOUND

**Setup:** Construct a component list containing a non-existent component ID.

**Trigger:** Call `resolveDependencies` with `rootComponentId` set to the invalid ID.

**Expected result:**
- `success` is `false`
- `errorCode` is `COMPONENT_NOT_FOUND`
- `errorMessage` identifies the missing component ID

---

### Test 16 -- Multi-Environment Deployment Paths

Validate the 3 distinct deployment paths end-to-end.

#### 16a. Test Deployment Path

1. Execute a promotion via `executePromotion` — record `branchId` and `promotionId`.
2. Call `packageAndDeploy` with `deploymentTarget = "TEST"`.

**Pass criteria:**
- Response: `branchPreserved = true`, `deploymentTarget = "TEST"`
- PromotionLog: `status = "TEST_DEPLOYED"`, `targetEnvironment = "TEST"`, `testDeployedAt` populated
- PromotionLog: `testIntegrationPackId` and `testIntegrationPackName` populated
- Branch preserved: `GET /Branch/{branchId}` returns 200

#### 16b. Promote from Test to Production

After Test 16a completes:

1. Call `queryTestDeployments` — verify the test deployment appears.
2. Call `packageAndDeploy` with `deploymentTarget = "PRODUCTION"` and `testPromotionId` set to the test deployment's `promotionId`.

**Pass criteria:**
- Response: `branchPreserved = false`, `deploymentTarget = "PRODUCTION"`
- PromotionLog (production record): `status = "DEPLOYED"`, `targetEnvironment = "PRODUCTION"`, `testPromotionId` links back to test record
- Branch deleted: `GET /Branch/{branchId}` returns 404
- Test deployment excluded from `queryTestDeployments` results

#### 16c. Emergency Hotfix Path

1. Execute a promotion via `executePromotion`.
2. Call `packageAndDeploy` with `deploymentTarget = "PRODUCTION"`, `isHotfix = true`, `hotfixJustification = "Critical production bug fix"`.

**Pass criteria:**
- Response: `branchPreserved = false`, `isHotfix = true`
- PromotionLog: `status = "DEPLOYED"`, `targetEnvironment = "PRODUCTION"`, `isHotfix = "true"`, `hotfixJustification` populated
- Branch deleted
- No `testPromotionId` (test phase bypassed)

---

---
Prev: [Phase 5b: Flow Dashboard — Review & Admin](16-flow-dashboard-review-admin.md) | Next: [Troubleshooting](18-troubleshooting.md) | [Back to Index](index.md)

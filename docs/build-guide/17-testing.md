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

---
Prev: [Phase 5b: Flow Dashboard — Review & Admin](16-flow-dashboard-review-admin.md) | Next: [Troubleshooting](18-troubleshooting.md) | [Back to Index](index.md)

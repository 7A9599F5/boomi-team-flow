## Phase 7: Multi-Environment Deployment

This phase adds 3-tier deployment support (Dev → Test → Production) with emergency hotfix capability.

### Prerequisites
- Phases 1-6 completed and tested
- At least one test environment configured in the primary account
- Test and production Integration Packs created (or plan to create during first deployment)

---

### Step 7.1: Update PromotionLog Model

**Reference:** `datahub/models/PromotionLog-model-spec.json`

1. Navigate to DataHub → PromotionLog model
2. Add 8 new fields (after `processName`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `targetEnvironment` | String | Yes | "TEST" or "PRODUCTION" |
| `isHotfix` | String | No | "true" / "false" |
| `hotfixJustification` | String | No | Required when isHotfix="true" (up to 1000 chars) |
| `testPromotionId` | String | No | Links PRODUCTION record to its TEST predecessor |
| `testDeployedAt` | Date | No | When test deployment completed |
| `testIntegrationPackId` | String | No | Test Integration Pack ID |
| `testIntegrationPackName` | String | No | Test Integration Pack name |
| `promotedFromTestBy` | String | No | Who initiated test→production promotion |

3. **Verify:** Query PromotionLog model via API and confirm new fields are visible

```bash
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/model/PromotionLog" \
  | python3 -m json.tool | grep -E "targetEnvironment|isHotfix|testPromotionId"
```

---

### Step 7.2: Create Process E4 — Query Test Deployments

**Reference:** `integration/profiles/queryTestDeployments-request.json`, `queryTestDeployments-response.json`

1. Create JSON profiles:
   - `PROMO - Profile - QueryTestDeploymentsRequest`
   - `PROMO - Profile - QueryTestDeploymentsResponse`

2. Create Integration process: `PROMO - Query Test Deployments`
   - Start shape → DataHub Connector (Query PromotionLog)
   - Filter: `targetEnvironment = "TEST"` AND `status = "TEST_DEPLOYED"`
   - Exclude promotions that have a matching PRODUCTION record (where another PromotionLog record has `testPromotionId` = this `promotionId`)
   - Map to response profile → Return shape

3. Create FSS Operation: `PROMO - FSS Op - QueryTestDeployments`
   - Link to Process E4
   - Request profile: QueryTestDeploymentsRequest
   - Response profile: QueryTestDeploymentsResponse

4. Add operation to Flow Service: `PROMO - Flow Service`
   - Add `queryTestDeployments` message action

5. **Verify:** Test via Flow Service endpoint:

```bash
curl -s -u "user:token" \
  -H "Content-Type: application/json" \
  -X POST "https://{cloud-base-url}/fs/PromotionService/queryTestDeployments" \
  -d '{"devAccountId": "", "initiatedBy": ""}'
```

---

### Step 7.3: Refactor Process D — Package and Deploy (3 Modes)

**Reference:** `integration/profiles/packageAndDeploy-request.json`, `packageAndDeploy-response.json`

1. Update JSON profiles with new fields:
   - Request: `deploymentTarget`, `isHotfix`, `hotfixJustification`, `testPromotionId`, `testIntegrationPackId`, `testIntegrationPackName`
   - Response: `deploymentTarget`, `branchPreserved`, `isHotfix`

2. Refactor Process D logic with a Decision shape on `deploymentTarget`:

**Mode 1: TEST**
- Merge branch to main (MergeRequest OVERRIDE)
- Create PackagedComponent from main
- Create/use Test Integration Pack
- Release + Deploy to test environment(s)
- DO NOT delete branch
- Update PromotionLog: `status=TEST_DEPLOYED`, `testDeployedAt`, `testIntegrationPackId/Name`

**Mode 2: PRODUCTION from test** (testPromotionId populated)
- Skip merge (content already on main)
- Create PackagedComponent from main
- Create/use Production Integration Pack
- Release + Deploy to production
- Delete branch
- Update PromotionLog: `status=DEPLOYED`

**Mode 3: PRODUCTION hotfix** (isHotfix=true)
- Merge branch to main
- Create PackagedComponent
- Create/use Production Integration Pack
- Release + Deploy to production
- Delete branch
- Update PromotionLog: `status=DEPLOYED`, `isHotfix="true"`

3. **Verify each mode:**

```bash
# Test mode
curl -s -u "user:token" -X POST "https://{cloud-base-url}/fs/PromotionService/packageAndDeploy" \
  -H "Content-Type: application/json" \
  -d '{"deploymentTarget": "TEST", "prodComponentId": "...", "packageVersion": "1.0.0-test", ...}'

# Production from test
curl -s -u "user:token" -X POST "https://{cloud-base-url}/fs/PromotionService/packageAndDeploy" \
  -H "Content-Type: application/json" \
  -d '{"deploymentTarget": "PRODUCTION", "testPromotionId": "{testPromoId}", ...}'

# Hotfix
curl -s -u "user:token" -X POST "https://{cloud-base-url}/fs/PromotionService/packageAndDeploy" \
  -H "Content-Type: application/json" \
  -d '{"deploymentTarget": "PRODUCTION", "isHotfix": true, "hotfixJustification": "Critical API fix", ...}'
```

---

### Step 7.4: Update Process J — List Integration Packs

**Reference:** `integration/profiles/listIntegrationPacks-request.json`

1. Update request profile with `packPurpose` field
2. Add Decision shape on `packPurpose`:
   - "TEST": Filter packs with "- TEST" suffix
   - "PRODUCTION": Filter packs without "- TEST" suffix
   - "ALL" (default): Return all packs
3. Update suggestion logic to consider target environment

4. **Verify:**

```bash
curl -s -u "user:token" -X POST "https://{cloud-base-url}/fs/PromotionService/listIntegrationPacks" \
  -H "Content-Type: application/json" \
  -d '{"suggestForProcess": "Order Processing Main", "packPurpose": "TEST"}'
```

---

### Step 7.5: Update Process C — Branch Limit Threshold

1. Change the branch count threshold from 18 to 15
2. This provides earlier warning as branches now persist longer during the test→production lifecycle

3. **Verify:** Check that Process C fails with `BRANCH_LIMIT_REACHED` when branch count >= 15

---

### Step 7.6: Update Flow Dashboard

#### 7.6.1: Page 3 — Add Deployment Target Selection

**Reference:** `flow/page-layouts/page3-promotion-status.md`

1. Add radio button group between diff panel and submit button:
   - "Deploy to Test" (default, recommended)
   - "Deploy to Production (Emergency Hotfix)" — shows warning + justification textarea
2. Set Flow values: `targetEnvironment`, `isHotfix`, `hotfixJustification`
3. Update submit button label to "Continue to Deployment"

#### 7.6.2: Page 4 — Conditional Deployment Modes

**Reference:** `flow/page-layouts/page4-deployment-submission.md`

1. Add mode detection logic on page load (check `targetEnvironment`, `isHotfix`, `testPromotionId`)
2. Mode 1 (Test): Direct deploy, inline results, no swimlane transition
3. Mode 2 (Production from Test): Show test summary panel, submit for peer review
4. Mode 3 (Hotfix): Show justification, submit for peer review with hotfix flag
5. Update `listIntegrationPacks` call to include `packPurpose` filter

#### 7.6.3: Pages 5-6 — Peer Review Badges

**Reference:** `flow/page-layouts/page5-peer-review-queue.md`, `page6-peer-review-detail.md`

1. Add `targetEnvironment` and `isHotfix` badges to queue grid
2. Page 6 detail: Show test deployment info when `testPromotionId` exists
3. Page 6 detail: Show hotfix justification when `isHotfix = "true"`

#### 7.6.4: Page 7 — Admin Hotfix Acknowledgment

**Reference:** `flow/page-layouts/page7-admin-approval-queue.md`

1. Add environment and hotfix badges to queue grid
2. Show hotfix justification prominently in detail panel
3. Add extra acknowledgment checkbox for hotfix approvals
4. Show test deployment history when `testPromotionId` exists

#### 7.6.5: New Page 9 — Production Readiness Queue

**Reference:** `flow/page-layouts/page9-production-readiness.md`

1. Add to Developer swimlane navigation
2. Data grid with test deployments (from `queryTestDeployments`)
3. Branch age column with color coding (green/amber/red)
4. "Promote to Production" button → navigates to Page 4 with production context
5. Stale branch warning for deployments > 30 days old

#### 7.6.6: Flow Structure Updates

**Reference:** `flow/flow-structure.md`

1. Add Page 9 to Developer swimlane
2. Add new Flow values
3. Update navigation diagram with branching paths
4. Add `queryTestDeployments` message step
5. Add new email notifications (test deployment, emergency hotfix)

---

### Step 7.7: End-to-End Testing

Test all 3 deployment paths:

#### Test 1: Dev → Test → Production (Happy Path)

1. Execute promotion (Process C) — creates branch
2. Page 3: Select "Deploy to Test"
3. Page 4: Deploy to Test Integration Pack
4. Verify: PromotionLog shows `targetEnvironment=TEST`, `status=TEST_DEPLOYED`, branch preserved
5. Page 9: Select test deployment → "Promote to Production"
6. Page 4: Submit for Peer Review
7. Pages 5-6: Peer review approves
8. Page 7: Admin approves and deploys
9. Verify: PromotionLog shows `status=DEPLOYED`, `testPromotionId` links back, branch deleted

#### Test 2: Emergency Hotfix (Dev → Production)

1. Execute promotion (Process C)
2. Page 3: Select "Emergency Hotfix", enter justification
3. Page 4: Submit for Peer Review with hotfix flag
4. Pages 5-6: Verify EMERGENCY HOTFIX badge and justification visible, approve
5. Page 7: Verify hotfix warning, check acknowledgment checkbox, approve
6. Verify: PromotionLog shows `isHotfix=true`, `hotfixJustification` populated, branch deleted

#### Test 3: Rejection at Each Stage

1. Test peer rejection of hotfix — verify branch deleted
2. Test admin denial of production from test — verify branch deleted
3. Test deployment failure in test mode — verify branch preserved, retry possible

---

### Step 7.8: Update Bill of Materials

Update the Bill of Materials table in the Prerequisites section:

| Addition | Count | Components |
|----------|-------|------------|
| DataHub Model Update | 0 (modified) | PromotionLog +8 fields |
| JSON Profile | 2 (new) | QueryTestDeploymentsRequest, QueryTestDeploymentsResponse |
| JSON Profile | 3 (modified) | PackageAndDeployRequest, PackageAndDeployResponse, ListIntegrationPacksRequest |
| Integration Process | 1 (new) | Process E4 (Query Test Deployments) |
| FSS Operation | 1 (new) | PROMO - FSS Op - QueryTestDeployments |
| Flow Page | 1 (new) | Page 9 (Production Readiness) |
| Flow Pages | 5 (modified) | Pages 3, 4, 5, 6, 7 |

**New totals:** 12 integration processes, 24 JSON profiles, 12 FSS operations, 9 Flow pages, **~69 components total**

---

---
Prev: [Phase 6: Testing](17-testing.md) | Next: [Troubleshooting](18-troubleshooting.md) | [Back to Index](index.md)

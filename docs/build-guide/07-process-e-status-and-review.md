### Process E: Query Status (`PROMO - Query Status`)

> **API Alternative:** This process can be created programmatically via `POST /Component` with `type="process"`. Due to the complexity of process canvas XML (shapes, routing, DPP mappings, script references), the recommended workflow is: (1) build the process manually following the steps below, (2) use `GET /Component/{processId}` to export the XML, (3) store the XML as a template for automated recreation. See [Appendix D: API Automation Guide](22-api-automation-guide.md) for the full workflow.

This process queries the PromotionLog DataHub model for past promotion records, with optional filtering.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - QueryStatusRequest` | `/integration/profiles/queryStatus-request.json` |
| `PROMO - Profile - QueryStatusResponse` | `/integration/profiles/queryStatus-response.json` |

The request JSON contains:
- `promotionId` (string, optional): filter by specific promotion
- `devAccountId` (string, optional): filter by dev account
- `status` (string, optional): filter by status (e.g., `"COMPLETED"`, `"FAILED"`, `"IN_PROGRESS"`)
- `limit` (number): maximum records to return (default 50)

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `promotions` (array): each entry contains `promotionId`, `devAccountId`, `prodAccountId`, `devPackageId`, `initiatedBy`, `initiatedAt`, `status`, `componentsTotal`, `componentsCreated`, `componentsUpdated`, `componentsFailed`, `errorMessage`, `resultDetail`

#### FSS Operation

Create `PROMO - FSS Op - QueryStatus` per Section 3.B, using `PROMO - Profile - QueryStatusRequest` and `PROMO - Profile - QueryStatusResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - QueryStatus`

2. **Set Properties** (read request fields)
   - DPP `promotionId` = document path: `promotionId`
   - DPP `filterDevAccountId` = document path: `devAccountId`
   - DPP `filterStatus` = document path: `status`
   - DPP `queryLimit` = document path: `limit`

3. **DataHub Query**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query PromotionLog`
   - Build filters dynamically from DPPs: if `promotionId` is non-empty, add filter `promotionId EQUALS {value}`; if `filterDevAccountId` is non-empty, add filter `devAccountId EQUALS {value}`; if `filterStatus` is non-empty, add filter `status EQUALS {value}`
   - Set query limit from DPP `queryLimit` (default 50)
   - Combine multiple filters with `AND` operator

4. **Map — Build Response JSON**
   - Source: DataHub PromotionLog query response (XML)
   - Destination: `PROMO - Profile - QueryStatusResponse`
   - Map each PromotionLog record to a `promotions` array entry
   - Map all fields: `promotionId`, `devAccountId`, `prodAccountId`, `devPackageId`, `initiatedBy`, `initiatedAt`, `status`, `componentsTotal`, `componentsCreated`, `componentsUpdated`, `componentsFailed`, `errorMessage`, `resultDetail`
   - Set `success` = `true`

5. **Return Documents** — same as Process F

#### Error Handling

Wrap the DataHub Query in a **Try/Catch**. Catch block builds error response with `errorCode = "DATAHUB_ERROR"`.

**Verify:**

- First, run Process C (Execute Promotion) to create a PromotionLog record, or manually seed one via the DataHub API
- Send a Query Status request with the `promotionId` of that record
- **Expected**: response with `success = true` and the `promotions` array containing that single record
- Send a request with `status = "COMPLETED"` and no other filters
- **Expected**: all completed promotion records returned (up to the limit)
- Send a request with a non-existent `promotionId`
- **Expected**: `success = true`, `promotions = []`

---

### Process E2: Query Peer Review Queue (`PROMO - Query Peer Review Queue`)

This process queries the PromotionLog DataHub model for promotions awaiting peer review, excluding the requesting user's own submissions to enforce self-review prevention. It powers the Peer Review Queue page (Page 5) in the Flow dashboard.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - QueryPeerReviewQueueRequest` | `/integration/profiles/queryPeerReviewQueue-request.json` |
| `PROMO - Profile - QueryPeerReviewQueueResponse` | `/integration/profiles/queryPeerReviewQueue-response.json` |

The request JSON contains:
- `requesterEmail` (string, required): the authenticated user's email; used to exclude their own submissions from the results

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `pendingReviews` (array): each entry contains `promotionId`, `processName`, `devAccountId`, `initiatedBy`, `initiatedAt`, `componentsTotal`, `componentsCreated`, `componentsUpdated`, `notes`, `packageVersion`, `devPackageId`, `resultDetail`, `targetEnvironment`, `isHotfix`, `branchId`, `branchName`

#### FSS Operation

Create `PROMO - FSS Op - QueryPeerReviewQueue` following the pattern in [Step 14 (Flow Service Setup)](14-flow-service.md). Configure the operation with `PROMO - Profile - QueryPeerReviewQueueRequest` as the request profile and `PROMO - Profile - QueryPeerReviewQueueResponse` as the response profile. Link it to the `PROMO - Query Peer Review Queue` process.

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - QueryPeerReviewQueue`

2. **Set Properties** (read request fields)
   - DPP `requesterEmail` = document path: `requesterEmail`

3. **DataHub Query — Pending Peer Reviews**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query PromotionLog`
   - Filter: `peerReviewStatus EQUALS "PENDING_PEER_REVIEW"`
   - This returns all promotions awaiting peer review, including the requester's own submissions (filtered in the next step)

4. **Data Process — Exclude Own Submissions (Self-Review Prevention)**
   - Groovy script that filters out records where the requester is the submitter:
   ```groovy
   import java.util.logging.Logger
   import groovy.xml.XmlSlurper
   import groovy.xml.XmlUtil
   import com.boomi.execution.ExecutionUtil

   Logger logger = Logger.getLogger("PROMO.E2.ExcludeOwnSubmissions")

   try {
       String requesterEmail = ExecutionUtil.getDynamicProcessProperty("requesterEmail")

       for (int i = 0; i < dataContext.getDataCount(); i++) {
           InputStream is = dataContext.getStream(i)
           Properties props = dataContext.getProperties(i)

           String docText = is.text
           def xml = new XmlSlurper().parseText(docText)
           String initiatedBy = xml.initiatedBy?.text() ?: ""

           // Case-insensitive comparison — Azure AD may return varying capitalization
           if (initiatedBy.toLowerCase() != requesterEmail.toLowerCase()) {
               dataContext.storeStream(
                   new ByteArrayInputStream(docText.getBytes("UTF-8")), props)
           }
           // Records where initiatedBy matches requesterEmail are silently dropped
       }
   } catch (Exception e) {
       logger.severe("Failed to filter own submissions: " + e.getMessage())
       throw new Exception("Self-review exclusion filter failed: " + e.getMessage())
   }
   ```
   - **Key requirement**: The `toLowerCase()` comparison on both sides is mandatory. Azure AD may return email addresses with varying capitalization (e.g., `John.Doe@company.com` vs `john.doe@company.com`). Without case-insensitive comparison, a user could review their own promotion.

5. **Map — Build Response JSON**
   - Source: filtered DataHub PromotionLog query response (XML)
   - Destination: `PROMO - Profile - QueryPeerReviewQueueResponse`
   - Map each remaining record to a `pendingReviews` array entry
   - Map all fields: `promotionId`, `processName`, `devAccountId`, `initiatedBy`, `initiatedAt`, `componentsTotal`, `componentsCreated`, `componentsUpdated`, `notes`, `packageVersion`, `devPackageId`, `resultDetail`, `targetEnvironment`, `isHotfix`, `branchId`, `branchName`
   - Set `success` = `true`

6. **Return Documents** — same as Process F

#### Error Handling

Wrap the DataHub Query and Data Process shapes in a **Try/Catch**. Catch block builds error response with `errorCode = "DATAHUB_ERROR"`.

---

### Process E3: Submit Peer Review (`PROMO - Submit Peer Review`)

This process records a peer review decision (approve or reject) against a PromotionLog record. It enforces self-review prevention and idempotency (cannot review an already-reviewed promotion). On approval, the promotion advances to the admin approval stage.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - SubmitPeerReviewRequest` | `/integration/profiles/submitPeerReview-request.json` |
| `PROMO - Profile - SubmitPeerReviewResponse` | `/integration/profiles/submitPeerReview-response.json` |

The request JSON contains:
- `promotionId` (string, required): the promotion to review
- `decision` (string, required: `"APPROVED"` | `"REJECTED"`): the peer review decision
- `reviewerEmail` (string, required): email of the peer reviewer
- `reviewerName` (string, required): display name of the peer reviewer
- `comments` (string, optional): reviewer comments (up to 500 characters)

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `promotionId` (string): echoed back for confirmation
- `newStatus` (string): the resulting `peerReviewStatus` (`PEER_APPROVED` or `PEER_REJECTED`)

#### FSS Operation

Create `PROMO - FSS Op - SubmitPeerReview` following the pattern in [Step 14 (Flow Service Setup)](14-flow-service.md). Configure the operation with `PROMO - Profile - SubmitPeerReviewRequest` as the request profile and `PROMO - Profile - SubmitPeerReviewResponse` as the response profile. Link it to the `PROMO - Submit Peer Review` process.

#### DPP Initialization

| DPP Name | Initial Value | Purpose |
|----------|--------------|---------|
| `promotionId` | (from request) | Target promotion to review |
| `decision` | (from request) | `"APPROVED"` or `"REJECTED"` |
| `reviewerEmail` | (from request) | Reviewer's email for self-review check |
| `reviewerName` | (from request) | Reviewer's display name for audit trail |
| `comments` | (from request) | Reviewer comments |
| `initiatedBy` | (from DataHub query) | Original submitter email for self-review check |
| `currentPeerReviewStatus` | (from DataHub query) | Current review status for idempotency check |

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - SubmitPeerReview`

2. **Set Properties — Read Request**
   - DPP `promotionId` = document path: `promotionId`
   - DPP `decision` = document path: `decision`
   - DPP `reviewerEmail` = document path: `reviewerEmail`
   - DPP `reviewerName` = document path: `reviewerName`
   - DPP `comments` = document path: `comments`

3. **DataHub Query — Fetch Promotion Record**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query PromotionLog`
   - Filter: `promotionId EQUALS` DPP `promotionId`
   - If no record found: build error response with `success = false`, `errorCode = "COMPONENT_NOT_FOUND"`, `errorMessage = "Promotion not found: {promotionId}"` → **Return Documents** (exit)
   - Extract from the returned record:
     - DPP `initiatedBy` = `initiatedBy` field
     - DPP `currentPeerReviewStatus` = `peerReviewStatus` field

4. **Decision — Self-Review Validation**
   - Groovy script evaluation (Data Process shape):
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import java.util.logging.Logger

   Logger logger = Logger.getLogger("PROMO.E3.SelfReviewCheck")

   try {
       String reviewerEmail = ExecutionUtil.getDynamicProcessProperty("reviewerEmail")
       String initiatedBy = ExecutionUtil.getDynamicProcessProperty("initiatedBy")

       // Case-insensitive comparison — mandatory for Azure AD compatibility
       boolean isSelfReview = reviewerEmail.toLowerCase() == initiatedBy.toLowerCase()
       ExecutionUtil.setDynamicProcessProperty("isSelfReview",
           isSelfReview ? "true" : "false", false)

       if (isSelfReview) {
           logger.warning("Self-review attempt blocked: " + reviewerEmail +
               " attempted to review their own promotion " +
               ExecutionUtil.getDynamicProcessProperty("promotionId"))
       }
   } catch (Exception e) {
       logger.severe("Self-review validation failed: " + e.getMessage())
       throw new Exception("Self-review validation failed: " + e.getMessage())
   }
   ```
   - **Decision shape**: DPP `isSelfReview` **EQUALS** `"true"`
     - **YES (self-review detected)**: Build error response with `success = false`, `errorCode = "SELF_REVIEW_NOT_ALLOWED"`, `errorMessage = "You cannot review your own promotion submission"` → **Return Documents** (exit)
     - **NO**: Continue to step 5

5. **Decision — Already Reviewed Check**
   - **Decision shape**: DPP `currentPeerReviewStatus` **NOT EQUALS** `"PENDING_PEER_REVIEW"`
     - **YES (already reviewed)**: Build error response with `success = false`, `errorCode = "ALREADY_REVIEWED"`, `errorMessage = "This promotion has already been peer-reviewed (current status: {currentPeerReviewStatus})"` → **Return Documents** (exit)
     - **NO (still pending)**: Continue to step 6

6. **DataHub Update — Record Peer Review Decision**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Update PromotionLog`
   - Build the update XML:
     - `promotionId` = DPP `promotionId` (match field)
     - `peerReviewedBy` = DPP `reviewerEmail`
     - `peerReviewedAt` = current timestamp
     - `peerReviewComments` = DPP `comments`
   - **If decision = "APPROVED"**:
     - `peerReviewStatus` = `"PEER_APPROVED"`
     - `adminReviewStatus` = `"PENDING_ADMIN_REVIEW"` (advance to admin stage)
     - `status` = `"PENDING_ADMIN_APPROVAL"`
   - **If decision = "REJECTED"**:
     - `peerReviewStatus` = `"PEER_REJECTED"`
     - `status` = `"PEER_REJECTED"`
   - Use a **Map** shape before the DataHub connector to build the update XML from DPPs, with a Decision function to set field values based on the `decision` DPP

7. **Map — Build Response JSON**
   - Source: DPPs
   - Destination: `PROMO - Profile - SubmitPeerReviewResponse`
   - Map:
     - `success` = `true`
     - `promotionId` = DPP `promotionId`
     - `newStatus` = `"PEER_APPROVED"` if decision was `"APPROVED"`, `"PEER_REJECTED"` if `"REJECTED"`

8. **Return Documents** — same as Process F

#### Error Handling

Wrap steps 3 through 7 in a **Try/Catch**. Catch block builds error response with `errorCode = "DATAHUB_ERROR"`.

**Error Codes (specific to this process)**:
- `SELF_REVIEW_NOT_ALLOWED` — `reviewerEmail.toLowerCase()` matches `initiatedBy.toLowerCase()`
- `ALREADY_REVIEWED` — promotion has already been peer-reviewed (`peerReviewStatus` is not `PENDING_PEER_REVIEW`)
- `COMPONENT_NOT_FOUND` — `promotionId` references a non-existent PromotionLog record

---

### Process E4: Query Test Deployments (`PROMO - Query Test Deployments`)

This process queries the PromotionLog for test deployments that are ready to be promoted to production.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - QueryTestDeploymentsRequest` | `/integration/profiles/queryTestDeployments-request.json` |
| `PROMO - Profile - QueryTestDeploymentsResponse` | `/integration/profiles/queryTestDeployments-response.json` |

The request JSON contains:
- `devAccountId` (string, optional): filter by dev account
- `initiatedBy` (string, optional): filter by submitter

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `testDeployments` (array): each entry contains `promotionId`, `devAccountId`, `prodAccountId`, `processName`, `packageVersion`, `initiatedBy`, `initiatedAt`, `componentsTotal`, `componentsCreated`, `componentsUpdated`, `testDeployedAt`, `testIntegrationPackId`, `testIntegrationPackName`, `branchId`, `branchName`

#### FSS Operation

Create `PROMO - FSS Op - QueryTestDeployments` per Section 3.B, using `PROMO - Profile - QueryTestDeploymentsRequest` and `PROMO - Profile - QueryTestDeploymentsResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - QueryTestDeployments`

2. **Set Properties** (read request fields)
   - DPP `filterDevAccountId` = document path: `devAccountId`
   - DPP `filterInitiatedBy` = document path: `initiatedBy`

3. **DataHub Query — Test Deployments**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query PromotionLog`
   - Filter: `targetEnvironment EQUALS "TEST"` AND (`status EQUALS "TEST_DEPLOYED"` OR `status EQUALS "TEST_DEPLOYING"`)
   - If `filterDevAccountId` is non-empty, add filter `devAccountId EQUALS {value}`
   - If `filterInitiatedBy` is non-empty, add filter `initiatedBy EQUALS {value}`
   - Combine filters with `AND` operator

4. **Data Process — Exclude Already-Promoted Records**
   - Groovy script that filters out test deployments where a matching PRODUCTION record already exists. See `integration/scripts/filter-already-promoted.groovy` for the complete implementation.
   - **Pre-requisite**: Add a **second DataHub query** between steps 3 and 4 that queries `PromotionLog WHERE targetEnvironment = "PRODUCTION" AND testPromotionId IS NOT NULL AND status != "FAILED"`. Use a Data Process shape to extract the `testPromotionId` values and store them as a comma-separated string in DPP `productionPromotionIds`. This single batch query avoids per-record lookups.
   - The script reads DPP `productionPromotionIds`, builds a Set for O(1) lookups, then filters out any test deployment document whose `promotionId` appears in that Set. Documents that pass through represent test deployments not yet promoted to production.

5. **Map — Build Response JSON**
   - Source: filtered DataHub PromotionLog query response (XML)
   - Destination: `PROMO - Profile - QueryTestDeploymentsResponse`
   - Map each record to a `testDeployments` array entry
   - Set `success` = `true`

6. **Return Documents** — same as Process F

#### Error Handling

Wrap the DataHub Query in a **Try/Catch**. Catch block builds error response with `errorCode = "DATAHUB_ERROR"`.

**Verify:**

- Seed a PromotionLog record with `targetEnvironment = "TEST"`, `status = "TEST_DEPLOYED"`, and populated test deployment fields
- Send a Query Test Deployments request
- **Expected**: response with `success = true` and the `testDeployments` array containing that record
- Create a second PromotionLog record with `targetEnvironment = "PRODUCTION"` and `testPromotionId` pointing to the first record
- Re-send the query
- **Expected**: the first record no longer appears (it has been promoted to production)

---

### Process E5: Withdraw Promotion (`PROMO - Withdraw Promotion`)

This process allows the original initiator to withdraw their promotion while it is awaiting review. It validates ownership and status, deletes the promotion branch, and updates the PromotionLog to WITHDRAWN status.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - WithdrawPromotionRequest` | `/integration/profiles/withdrawPromotion-request.json` |
| `PROMO - Profile - WithdrawPromotionResponse` | `/integration/profiles/withdrawPromotion-response.json` |

The request JSON contains:
- `promotionId` (string, required): the promotion ID to withdraw
- `initiatorEmail` (string, required): email of the user requesting withdrawal; must match `initiatedBy`
- `reason` (string, optional): reason for withdrawal (up to 500 characters)

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `promotionId` (string): echoed back for confirmation
- `previousStatus` (string): the status before withdrawal
- `newStatus` (string): always `WITHDRAWN` on success
- `branchDeleted` (boolean): true if the branch was successfully deleted (or already absent)
- `message` (string): human-readable confirmation message

#### FSS Operation

Create `PROMO - FSS Op - WithdrawPromotion` following the pattern in [Step 14 (Flow Service Setup)](14-flow-service.md). Configure the operation with `PROMO - Profile - WithdrawPromotionRequest` as the request profile and `PROMO - Profile - WithdrawPromotionResponse` as the response profile. Link it to the `PROMO - Withdraw Promotion` process.

#### DPP Initialization

| DPP Name | Initial Value | Purpose |
|----------|--------------|---------|
| `promotionId` | (from request) | Target promotion to withdraw |
| `initiatorEmail` | (from request) | Requester's email for ownership check |
| `reason` | (from request) | Optional withdrawal reason |
| `initiatedBy` | (from DataHub query) | Original submitter email for ownership check |
| `currentStatus` | (from DataHub query) | Current promotion status for validation |
| `branchId` | (from DataHub query) | Branch ID for deletion |
| `previousStatus` | (from DPP) | Captured before status update |
| `branchDeleted` | `"false"` | Set to `"true"` after successful branch deletion |
| `responseMessage` | `""` | Human-readable confirmation message |

#### Canvas — Shape by Shape

1. **Start shape** — Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - WithdrawPromotion`

2. **Set Properties — Read Request**
   - DPP `promotionId` = document path: `promotionId`
   - DPP `initiatorEmail` = document path: `initiatorEmail`
   - DPP `reason` = document path: `reason`

3. **DataHub Query — Fetch Promotion Record**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query PromotionLog`
   - Filter: `promotionId EQUALS` DPP `promotionId`
   - If no record found: build error response with `success = false`, `errorCode = "PROMOTION_NOT_FOUND"`, `errorMessage = "Promotion not found: {promotionId}"` → **Return Documents** (exit)
   - Extract from the returned record:
     - DPP `initiatedBy` = `initiatedBy` field
     - DPP `currentStatus` = `status` field
     - DPP `branchId` = `branchId` field
   - DPP `previousStatus` = DPP `currentStatus` (capture before update)

4. **Decision — Status Validation**
   - **Decision shape**: Check if DPP `currentStatus` equals `"PENDING_PEER_REVIEW"` OR `"PENDING_ADMIN_REVIEW"`
   - Groovy script evaluation (Data Process shape):
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import java.util.logging.Logger

   Logger logger = Logger.getLogger("PROMO.E5.StatusValidation")

   try {
       String currentStatus = ExecutionUtil.getDynamicProcessProperty("currentStatus")
       boolean isWithdrawable = (currentStatus == "PENDING_PEER_REVIEW" || currentStatus == "PENDING_ADMIN_REVIEW")
       ExecutionUtil.setDynamicProcessProperty("isWithdrawable", isWithdrawable ? "true" : "false", false)

       if (!isWithdrawable) {
           logger.warning("Withdrawal rejected: promotion status is " + currentStatus +
               " (expected PENDING_PEER_REVIEW or PENDING_ADMIN_REVIEW)")
       }
   } catch (Exception e) {
       logger.severe("Status validation failed: " + e.getMessage())
       throw new Exception("Status validation failed: " + e.getMessage())
   }
   ```
   - **Decision shape**: DPP `isWithdrawable` **EQUALS** `"false"`
     - **YES (not withdrawable)**: Build error response with `success = false`, `errorCode = "INVALID_PROMOTION_STATUS"`, `errorMessage = "Cannot withdraw promotion with status {currentStatus}; expected PENDING_PEER_REVIEW or PENDING_ADMIN_REVIEW"` → **Return Documents** (exit)
     - **NO (withdrawable)**: Continue to step 5

5. **Decision — Ownership Validation**
   - Groovy script evaluation (Data Process shape):
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import java.util.logging.Logger

   Logger logger = Logger.getLogger("PROMO.E5.OwnershipValidation")

   try {
       String initiatorEmail = ExecutionUtil.getDynamicProcessProperty("initiatorEmail")
       String initiatedBy = ExecutionUtil.getDynamicProcessProperty("initiatedBy")

       // Case-insensitive comparison — mandatory for Azure AD compatibility
       boolean isOwner = initiatorEmail.toLowerCase() == initiatedBy.toLowerCase()
       ExecutionUtil.setDynamicProcessProperty("isOwner", isOwner ? "true" : "false", false)

       if (!isOwner) {
           logger.warning("Withdrawal rejected: " + initiatorEmail +
               " is not the initiator (" + initiatedBy + ") of promotion " +
               ExecutionUtil.getDynamicProcessProperty("promotionId"))
       }
   } catch (Exception e) {
       logger.severe("Ownership validation failed: " + e.getMessage())
       throw new Exception("Ownership validation failed: " + e.getMessage())
   }
   ```
   - **Decision shape**: DPP `isOwner` **EQUALS** `"false"`
     - **YES (not owner)**: Build error response with `success = false`, `errorCode = "NOT_PROMOTION_INITIATOR"`, `errorMessage = "Only the promotion initiator can withdraw this promotion"` → **Return Documents** (exit)
     - **NO (is owner)**: Continue to step 6

6. **HTTP Client Send — Delete Promotion Branch**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - DELETE Branch`
   - URL: `/Branch/{branchId}` (substitute DPP `branchId`)
   - **Idempotent handling**: HTTP 200 (deleted) and HTTP 404 (already absent) are both treated as success → set DPP `branchDeleted` = `"true"`
   - HTTP 4xx/5xx (except 404): set DPP `branchDeleted` = `"false"`, log warning but continue (branch cleanup is best-effort)

7. **DataHub Update — Record Withdrawal**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Update PromotionLog`
   - Build the update XML:
     - `promotionId` = DPP `promotionId` (match field)
     - `status` = `"WITHDRAWN"`
     - `branchId` = `""` (clear the branch reference)
     - `withdrawnAt` = current timestamp (format: `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'`)
     - `withdrawalReason` = DPP `reason`

8. **Map — Build Success Response JSON**
   - Source: DPPs
   - Destination: `PROMO - Profile - WithdrawPromotionResponse`
   - Map:
     - `success` = `true`
     - `promotionId` = DPP `promotionId`
     - `previousStatus` = DPP `previousStatus`
     - `newStatus` = `"WITHDRAWN"`
     - `branchDeleted` = DPP `branchDeleted`
     - `message` = `"Promotion {promotionId} withdrawn successfully. Branch deleted."`

9. **Return Documents** — same as Process F

#### Error Handling

Wrap steps 3 through 8 in a **Try/Catch**. Catch block builds error response with `errorCode = "DATAHUB_ERROR"`.

**Error Codes (specific to this process)**:
- `PROMOTION_NOT_FOUND` — `promotionId` references a non-existent PromotionLog record
- `INVALID_PROMOTION_STATUS` — promotion is not in `PENDING_PEER_REVIEW` or `PENDING_ADMIN_REVIEW` status
- `NOT_PROMOTION_INITIATOR` — `initiatorEmail` does not match the promotion's `initiatedBy` field

---

### Testing — Processes E2, E3, E4, E5

#### E2 — queryPeerReviewQueue

| # | Scenario | Setup | Expected Result |
|---|----------|-------|-----------------|
| 1 | No pending reviews | No PromotionLog records with `peerReviewStatus = "PENDING_PEER_REVIEW"` | `success = true`, `pendingReviews = []` |
| 2 | Exclude own submissions | Create 2 PromotionLog records with `peerReviewStatus = "PENDING_PEER_REVIEW"`: one with `initiatedBy = "alice@company.com"`, one with `initiatedBy = "bob@company.com"`. Query with `requesterEmail = "Alice@Company.com"` (note: different casing) | `success = true`, `pendingReviews` contains only Bob's record. Alice's record is excluded despite different casing (case-insensitive comparison) |
| 3 | Multiple pending reviews | Create 3 records with `peerReviewStatus = "PENDING_PEER_REVIEW"`, all from different users. Query with `requesterEmail = "reviewer@company.com"` (not matching any submitter) | `success = true`, `pendingReviews` contains all 3 records |

#### E3 — submitPeerReview

| # | Scenario | Setup | Expected Result |
|---|----------|-------|-----------------|
| 1 | Approve another user's promotion | PromotionLog record with `initiatedBy = "alice@company.com"`, `peerReviewStatus = "PENDING_PEER_REVIEW"`. Submit with `reviewerEmail = "bob@company.com"`, `decision = "APPROVED"` | `success = true`, `newStatus = "PEER_APPROVED"`. PromotionLog updated: `peerReviewStatus = "PEER_APPROVED"`, `adminReviewStatus = "PENDING_ADMIN_REVIEW"`, `peerReviewedBy = "bob@company.com"`, `peerReviewedAt` populated |
| 2 | Reject another user's promotion | Same setup as Test 1. Submit with `decision = "REJECTED"`, `comments = "Missing unit tests"` | `success = true`, `newStatus = "PEER_REJECTED"`. PromotionLog updated: `peerReviewStatus = "PEER_REJECTED"`, `peerReviewComments = "Missing unit tests"` |
| 3 | Self-review attempt | PromotionLog record with `initiatedBy = "alice@company.com"`. Submit with `reviewerEmail = "Alice@Company.com"` (different casing) | `success = false`, `errorCode = "SELF_REVIEW_NOT_ALLOWED"`. PromotionLog unchanged |
| 4 | Already-reviewed promotion | PromotionLog record with `peerReviewStatus = "PEER_APPROVED"`. Submit another review | `success = false`, `errorCode = "ALREADY_REVIEWED"`. PromotionLog unchanged |
| 5 | Non-existent promotion | Submit with `promotionId = "nonexistent-uuid"` | `success = false`, `errorCode = "COMPONENT_NOT_FOUND"` |

#### E4 — queryTestDeployments

| # | Scenario | Setup | Expected Result |
|---|----------|-------|-----------------|
| 1 | Test deployments ready for production | PromotionLog record with `targetEnvironment = "TEST"`, `status = "TEST_DEPLOYED"`, no matching PRODUCTION record | `success = true`, `testDeployments` contains the record |
| 2 | Test deployment already promoted | Same as Test 1, plus a second PromotionLog record with `targetEnvironment = "PRODUCTION"`, `testPromotionId` = first record's `promotionId`, `status != "FAILED"` | `success = true`, `testDeployments` does NOT contain the first record (filtered out) |
| 3 | No test deployments | No PromotionLog records with `targetEnvironment = "TEST"` | `success = true`, `testDeployments = []` |

#### E5 — withdrawPromotion

| # | Scenario | Setup | Expected Result |
|---|----------|-------|-----------------|
| 1 | Withdraw from PENDING_PEER_REVIEW | PromotionLog record with `status = "PENDING_PEER_REVIEW"`, `initiatedBy = "alice@company.com"`, `branchId` populated. Withdraw with `initiatorEmail = "alice@company.com"` | `success = true`, `previousStatus = "PENDING_PEER_REVIEW"`, `newStatus = "WITHDRAWN"`, `branchDeleted = true`. PromotionLog updated: `status = "WITHDRAWN"`, `branchId = ""`, `withdrawnAt` populated |
| 2 | Withdraw from PENDING_ADMIN_REVIEW | Same as Test 1 but `status = "PENDING_ADMIN_REVIEW"` | `success = true`, `previousStatus = "PENDING_ADMIN_REVIEW"`, `newStatus = "WITHDRAWN"`, `branchDeleted = true` |
| 3 | Non-initiator attempts withdrawal | PromotionLog with `initiatedBy = "alice@company.com"`. Withdraw with `initiatorEmail = "bob@company.com"` | `success = false`, `errorCode = "NOT_PROMOTION_INITIATOR"`. PromotionLog unchanged |
| 4 | Invalid status (COMPLETED) | PromotionLog with `status = "COMPLETED"`. Withdraw attempt | `success = false`, `errorCode = "INVALID_PROMOTION_STATUS"`. PromotionLog unchanged |
| 5 | Non-existent promotion | Withdraw with `promotionId = "nonexistent-uuid"` | `success = false`, `errorCode = "PROMOTION_NOT_FOUND"` |
| 6 | Withdraw with reason | Same as Test 1, add `reason = "Selected wrong package"` | `success = true`, `withdrawalReason = "Selected wrong package"` in PromotionLog |
| 7 | Case-insensitive email match | PromotionLog with `initiatedBy = "alice@company.com"`. Withdraw with `initiatorEmail = "Alice@Company.com"` | `success = true` — case-insensitive match succeeds |

---

---
Prev: [Process A0: Get Dev Accounts](06-process-a0-get-dev-accounts.md) | Next: [Process A: List Dev Packages](08-process-a-list-dev-packages.md) | [Back to Index](index.md)

### Process E: Query Status (`PROMO - Query Status`)

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
   - Groovy script that filters out test deployments where a matching PRODUCTION record already exists (another PromotionLog record has `testPromotionId` equal to this record's `promotionId` with `status` not `FAILED`)
   - This ensures only "ready for production" deployments appear in the queue

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

---
Prev: [Process A0: Get Dev Accounts](06-process-a0-get-dev-accounts.md) | Next: [Process A: List Dev Packages](08-process-a-list-dev-packages.md) | [Back to Index](index.md)

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

---
Prev: [Process A0: Get Dev Accounts](06-process-a0-get-dev-accounts.md) | Next: [Process A: List Dev Packages](08-process-a-list-dev-packages.md) | [Back to Index](index.md)

### 3.C — Individual Processes

Build in this order. Process F is fully detailed as the template; subsequent processes fully detail unique patterns but reference Process F for shared patterns (Start shape, Return Documents, profile import).

---

### Process F: Mapping CRUD (`PROMO - Mapping CRUD`)

> **API Alternative:** This process can be created programmatically via `POST /Component` with `type="process"`. Due to the complexity of process canvas XML (shapes, routing, DPP mappings, script references), the recommended workflow is: (1) build the process manually following the steps below, (2) use `GET /Component/{processId}` to export the XML, (3) store the XML as a template for automated recreation. See [Appendix D: API Automation Guide](22-api-automation-guide.md) for the full workflow.

This is the simplest process — a good "hello world" to validate the FSS-to-process pipeline before tackling complex logic.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - ManageMappingsRequest` | `/integration/profiles/manageMappings-request.json` |
| `PROMO - Profile - ManageMappingsResponse` | `/integration/profiles/manageMappings-response.json` |

The request JSON contains:
- `operation` (string): one of `"list"`, `"create"`, `"update"`
- `filters` (object): optional filter fields (`devAccountId`, `componentType`, `componentName`)
- `mapping` (object): the mapping record to create or update (used by create/update operations)

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `operation` (string): echoes the requested operation
- `mappings` (array): returned mapping records (for list operations)
- `totalCount` (number): count of returned records

#### FSS Operation

1. Create `PROMO - FSS Op - ManageMappings` per the pattern in Section 3.B
2. Service Type: Message Action
3. Request Profile: `PROMO - Profile - ManageMappingsRequest`
4. Response Profile: `PROMO - Profile - ManageMappingsResponse`

#### Canvas — Shape by Shape

1. **Start shape**
   - Double-click the Start shape on the new process canvas
   - Connector: **Boomi Flow Services Server**
   - Action: **Listen**
   - Operation: select `PROMO - FSS Op - ManageMappings`
   - This receives the request JSON from the Flow Service

2. **Set Properties** (read request fields into DPPs)
   - Drag a **Set Properties** shape onto the canvas; connect Start to it
   - Add property: DPP `operation` = read from document using JSON profile `PROMO - Profile - ManageMappingsRequest`, path: `operation`
   - Add property: DPP `filterDevAccountId` = read from document path: `filters/devAccountId`
   - Add property: DPP `filterComponentType` = read from document path: `filters/componentType`
   - Add property: DPP `filterComponentName` = read from document path: `filters/componentName`

3. **Decision** (branch on operation type)
   - Drag a **Decision** shape; connect Set Properties to it
   - First branch condition: DPP `operation` **EQUALS** `"list"`
   - Name this branch: `List`
   - Default (else) branch handles create and update operations

4. **List branch — DataHub Query**
   - From the Decision `List` branch, add a **Connector** shape (DataHub)
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query ComponentMapping`
   - The query applies filters from the DPPs set in step 2 (configure filter parameters in the operation to read from DPPs `filterDevAccountId`, `filterComponentType`, `filterComponentName`)
   - If all filters are empty, the query returns all records (up to the limit)

5. **List branch — Map to response**
   - Add a **Map** shape after the DataHub Query on the List branch
   - Source profile: DataHub ComponentMapping query response (XML)
   - Destination profile: `PROMO - Profile - ManageMappingsResponse` (JSON)
   - Map fields:
     - Each `ComponentMapping` record maps to an entry in the `mappings` array
     - Map `devComponentId`, `devAccountId`, `prodComponentId`, `componentName`, `componentType`, `prodAccountId`, `prodLatestVersion`, `lastPromotedAt`, `lastPromotedBy`
     - Set `success` = `true`
     - Set `operation` = DPP `operation`
     - Set `totalCount` = count of records returned

6. **List branch — Return Documents**
   - Add a **Return Documents** shape after the Map; connect to it
   - No configuration needed — this sends the mapped response JSON back to Flow

7. **Create/Update branch — DataHub Update**
   - From the Decision default branch, add a **Connector** shape (DataHub)
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Update ComponentMapping`
   - The incoming document must be transformed to the DataHub XML update format before this shape
   - Add a **Map** shape between the Decision and the DataHub Update connector:
     - Source: `PROMO - Profile - ManageMappingsRequest` (JSON) — specifically the `mapping` object
     - Destination: DataHub ComponentMapping update request (XML)
     - Map `mapping.devComponentId`, `mapping.devAccountId`, `mapping.prodComponentId`, `mapping.componentName`, `mapping.componentType`, `mapping.prodAccountId`, `mapping.prodLatestVersion`

8. **Create/Update branch — Map to response**
   - Add a **Map** shape after the DataHub Update connector
   - Source: DataHub update response (XML)
   - Destination: `PROMO - Profile - ManageMappingsResponse` (JSON)
   - Set `success` = `true`
   - Set `operation` = DPP `operation`
   - Set `totalCount` = `1`

9. **Create/Update branch — Return Documents**
   - Add a **Return Documents** shape; connect to it

#### Error Handling

Add a **Try/Catch** around the DataHub connector shapes (both branches). In the Catch block:
1. Add a **Map** shape that builds the error response JSON:
   - `success` = `false`
   - `errorCode` = `"DATAHUB_ERROR"`
   - `errorMessage` = the caught exception message
2. Connect to a **Return Documents** shape

**Verify:**

- Deploy the process to your public cloud atom
- Send a test request through the Flow Service with `operation = "list"` and empty filters
- **Expected**: response with `success = true`, `operation = "list"`, `mappings = []` (empty array, since no records exist yet), `totalCount = 0`
- Send a test request with `operation = "create"` and a populated `mapping` object
- **Expected**: response with `success = true`, `operation = "create"`, `totalCount = 1`
- Send another `operation = "list"` request
- **Expected**: the mapping you just created appears in the `mappings` array

---

---
Prev: [Phase 3: Process Canvas Fundamentals](04-process-canvas-fundamentals.md) | Next: [Process A0: Get Dev Accounts](06-process-a0-get-dev-accounts.md) | [Back to Index](index.md)

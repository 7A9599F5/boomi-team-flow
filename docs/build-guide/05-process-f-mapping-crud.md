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
- `action` (string): one of `"query"`, `"update"`, `"delete"`
- `devComponentId` (string, conditional): the dev component ID to query, update, or delete
- `prodComponentId` (string, conditional): the production component ID (used by update)
- `componentName` (string, conditional): human-readable name (used by update)

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `mappings` (array): returned mapping records (for query operations)

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
   - Add property: DPP `action` = read from document using JSON profile `PROMO - Profile - ManageMappingsRequest`, path: `action`

3. **Decision** (branch on action type)
   - Drag a **Decision** shape; connect Set Properties to it
   - First branch condition: DPP `action` **EQUALS** `"query"`
   - Name this branch: `Query`
   - Default (else) branch handles update and delete operations

4. **Query branch — DataHub Query**
   - From the Decision `Query` branch, add a **Connector** shape (DataHub)
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query ComponentMapping`
   - Configure the query to filter by `devComponentId` from the incoming request (if provided)
   - If `devComponentId` is empty, the query returns all records (up to the limit)

5. **Query branch — Map to response**
   - Add a **Map** shape after the DataHub Query on the Query branch
   - Source profile: DataHub ComponentMapping query response (XML)
   - Destination profile: `PROMO - Profile - ManageMappingsResponse` (JSON)
   - Map fields:
     - Each `ComponentMapping` record maps to an entry in the `mappings` array
     - Map `devComponentId`, `prodComponentId`, `componentName`, `componentType`, `lastPromoted`
     - Set `success` = `true`

6. **Query branch — Return Documents**
   - Add a **Return Documents** shape after the Map; connect to it
   - No configuration needed — this sends the mapped response JSON back to Flow

7. **Update/Delete branch — Map request to DataHub XML**
   - From the Decision default branch, add a **Map** shape
   - Source: `PROMO - Profile - ManageMappingsRequest` (JSON)
   - Destination: DataHub ComponentMapping update request (XML)
   - Map `devComponentId`, `prodComponentId`, `componentName` from the flat request fields

8. **Update/Delete branch — DataHub Update**
   - Add a **Connector** shape (DataHub) after the Map
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Update ComponentMapping`
   - For `"update"`: the DataHub upsert creates or updates the mapping record based on match rules (`devComponentId` + `devAccountId`)
   - For `"delete"`: send an update that marks the record for removal (or use the DataHub Repository API delete endpoint)

9. **Update/Delete branch — Map to response**
   - Add a **Map** shape after the DataHub Update connector
   - Source: DataHub update response (XML)
   - Destination: `PROMO - Profile - ManageMappingsResponse` (JSON)
   - Set `success` = `true`

10. **Update/Delete branch — Return Documents**
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
- Send a test request through the Flow Service with `action = "query"` and a `devComponentId` that has no mapping
- **Expected**: response with `success = true`, `mappings = []` (empty array, since no records exist yet)
- Send a test request with `action = "update"` and populated `devComponentId`, `prodComponentId`, `componentName`
- **Expected**: response with `success = true`
- Send another `action = "query"` request with the same `devComponentId`
- **Expected**: the mapping you just created appears in the `mappings` array

---

---
Prev: [Phase 3: Process Canvas Fundamentals](04-process-canvas-fundamentals.md) | Next: [Process A0: Get Dev Accounts](06-process-a0-get-dev-accounts.md) | [Back to Index](index.md)

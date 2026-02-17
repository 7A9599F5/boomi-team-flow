### Process B: Resolve Dependencies (`PROMO - Resolve Dependencies`)

> **API Alternative:** This process can be created programmatically via `POST /Component` with `type="process"`. Due to the complexity of process canvas XML (shapes, routing, DPP mappings, script references), the recommended workflow is: (1) build the process manually following the steps below, (2) use `GET /Component/{processId}` to export the XML, (3) store the XML as a template for automated recreation. See [Appendix D: API Automation Guide](22-api-automation-guide.md) for the full workflow.

This process performs a breadth-first traversal of component references starting from a root component. It builds a complete dependency tree and checks each component against the DataHub for existing prod mappings (marking components as NEW or UPDATE).

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - ResolveDependenciesRequest` | `/integration/profiles/resolveDependencies-request.json` |
| `PROMO - Profile - ResolveDependenciesResponse` | `/integration/profiles/resolveDependencies-response.json` |

The request JSON contains:
- `devAccountId` (string): the dev sub-account
- `componentId` (string): the root component ID to resolve from

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `rootProcessName` (string): name of the root component
- `totalComponents` (number): total count of resolved components
- `components` (array): each entry has `devComponentId`, `name`, `type`, `devVersion`, `prodStatus` (`"NEW"` or `"UPDATE"`), `prodComponentId`, `prodCurrentVersion`, `hasEnvConfig`, `folderFullPath` (string, the component's folder path in dev), `isSharedConnection` (boolean, `true` if type is `connection`)

#### FSS Operation

Create `PROMO - FSS Op - ResolveDependencies` per Section 3.B, using `PROMO - Profile - ResolveDependenciesRequest` and `PROMO - Profile - ResolveDependenciesResponse`.

#### DPP Initialization

This process uses the following DPPs. Initialize them in a Set Properties shape immediately after reading request fields:

| DPP Name | Initial Value | Purpose |
|----------|--------------|---------|
| `rootComponentId` | (from request `componentId`) | Root component being resolved |
| `devAccountId` | (from request `devAccountId`) | Dev sub-account for API calls |
| `visitedComponentIds` | `[]` | JSON array tracking visited IDs |
| `componentQueue` | `["{rootComponentId}"]` | BFS queue; seeded with root ID |
| `visitedCount` | `0` | Counter for visited components |
| `queueCount` | `1` | Counter for remaining queue items |
| `currentComponentId` | (empty) | Set during each loop iteration |
| `alreadyVisited` | `false` | Flag set by `build-visited-set.groovy` |

#### Canvas — Shape by Shape

1. **Start shape** — Operation = `PROMO - FSS Op - ResolveDependencies`

2. **Set Properties — Read Request**
   - DPP `devAccountId` = document path: `devAccountId`
   - DPP `rootComponentId` = document path: `componentId`

3. **Set Properties — Initialize BFS State**
   - DPP `visitedComponentIds` = `[]`
   - DPP `componentQueue` = construct JSON array containing `rootComponentId` (use a Groovy Data Process if needed to build `["<rootComponentId value>"]`)
   - DPP `visitedCount` = `0`
   - DPP `queueCount` = `1`
   - DPP `alreadyVisited` = `false`

4. **Decision — Loop Condition: Queue Not Empty?**
   - Condition: DPP `queueCount` **GREATER THAN** `0`
   - **YES** branch: enter loop body (step 5)
   - **NO** branch: exit loop, skip to step 11

5. **Data Process — Pop Next from Queue**
   - Groovy script that reads the `componentQueue` DPP, removes the first item, sets it as `currentComponentId`, and updates `componentQueue` and `queueCount`:
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import groovy.json.JsonSlurper
   import groovy.json.JsonOutput

   def queue = new JsonSlurper().parseText(
       ExecutionUtil.getDynamicProcessProperty("componentQueue"))
   String nextId = queue.remove(0)
   ExecutionUtil.setDynamicProcessProperty("currentComponentId", nextId, false)
   ExecutionUtil.setDynamicProcessProperty("componentQueue",
       JsonOutput.toJson(queue), false)
   ExecutionUtil.setDynamicProcessProperty("queueCount",
       queue.size().toString(), false)
   ```

6. **HTTP Client Send — GET ComponentReference**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - GET ComponentReference`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - URL parameter `{2}` = DPP `currentComponentId`
   - Query parameter: `overrideAccount` = DPP `devAccountId`
   - Returns XML listing all component IDs referenced by the current component

7. **Data Process — `build-visited-set.groovy`**
   - Paste contents of `/integration/scripts/build-visited-set.groovy`
   - This script:
     - Reads DPPs: `visitedComponentIds`, `componentQueue`, `currentComponentId`
     - Checks if `currentComponentId` is already in the visited set
     - If visited: sets DPP `alreadyVisited` = `"true"` and skips
     - If not visited: adds to visited set, parses the ComponentReference XML to extract child component IDs, adds unvisited children to the queue
     - Writes DPPs: `visitedComponentIds`, `componentQueue`, `alreadyVisited`, `visitedCount`, `queueCount`

8. **Decision — Already Visited?**
   - Condition: DPP `alreadyVisited` **EQUALS** `"true"`
   - **YES** branch: skip this component, loop back to step 4
   - **NO** branch: continue to step 9

9. **HTTP Client Send — GET ComponentMetadata**
   - Operation: `PROMO - HTTP Op - GET ComponentMetadata`
   - URL parameter `{2}` = DPP `currentComponentId`
   - Query parameter: `overrideAccount` = DPP `devAccountId`
   - Returns component `name`, `type`, `version`, and other metadata
   - Extract `folderFullPath` from the metadata response and include it in the accumulated results JSON for each component. This path is passed through to Process C to construct the mirrored promotion target folder.

10. **DataHub Query — Check Existing Mapping**
    - Connector: `PROMO - DataHub Connection`
    - Operation: `PROMO - DH Op - Query ComponentMapping`
    - Filter: `devComponentId EQUALS` DPP `currentComponentId` `AND devAccountId EQUALS` DPP `devAccountId`
    - If a record is returned: this component has been promoted before; mark `prodStatus = "UPDATE"` and extract `prodComponentId` and `prodCurrentVersion` from the mapping
    - If no record: mark `prodStatus = "NEW"`, `prodComponentId = ""`, `prodCurrentVersion = 0`
    - Store these values as DPPs or accumulate into a results JSON document
    - **Loop back** to step 4 (the Decision on queue count)

11. **Data Process — Sort Results**
    - After the loop exits (queue is empty), use the `sort-by-dependency.groovy` logic or simply pass the accumulated results. The sort here is optional (Process C does the actual sort before promotion), but sorting in the response helps the UI display dependencies in logical order.

12. **Map — Build Response JSON**
    - Source: accumulated component results
    - Destination: `PROMO - Profile - ResolveDependenciesResponse`
    - Map each component to a `components` array entry
    - Set `rootProcessName` from the root component's metadata (captured during the first iteration)
    - Set `totalComponents` = DPP `visitedCount`
    - Set `success` = `true`

13. **Return Documents** — same as Process F

#### Error Handling

Wrap the loop body (steps 5-10) in a **Try/Catch**. In the Catch block:
- Log the error with `currentComponentId` for diagnostics
- Mark the component as having `prodStatus = "ERROR"` in the results
- Continue the loop (do not abort the entire traversal for one failed component)

For fatal errors (e.g., authentication failure), catch at the outer process level and return the standard error response.

**Verify:**

- In a dev sub-account, create a simple process that references at least one connection and one profile
- Package that process
- Send a Resolve Dependencies request with the process's `componentId` and the `devAccountId`
- **Expected**: response with `success = true`, `totalComponents >= 3` (the process + at least 1 connection + at least 1 profile), each entry showing `prodStatus = "NEW"` (since nothing has been promoted yet)
- Verify no duplicates: each `devComponentId` appears exactly once in the `components` array
- Verify the root process appears in the results with its correct `name` and `type = "process"`

---

---
Prev: [Process A: List Dev Packages](08-process-a-list-dev-packages.md) | Next: [Process C: Execute Promotion](10-process-c-execute-promotion.md) | [Back to Index](index.md)

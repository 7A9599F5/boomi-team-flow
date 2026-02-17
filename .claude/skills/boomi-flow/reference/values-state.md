# Flow Values and State Management

## What are Flow Values?

**Flow Values** are state variables that persist across pages and steps within a Flow application. They store user input, API responses, and calculated data during flow execution.

---

## Types of Flow Values

| Type | Description | Example |
|------|-------------|---------|
| **String** | Text values | `"alice@example.com"`, `"Orders Process"` |
| **Number** | Numeric values | `42`, `3.14` |
| **Boolean** | True/false flags | `$True`, `$False` |
| **Date** | Date only (no time) | `2026-02-16` |
| **DateTime** | Date and time | `2026-02-16T14:30:00.000Z` |
| **Object** | Complex data structures (JSON-like) | `{ "componentId": "abc-123", "componentName": "Orders" }` |
| **List** | Arrays of values or objects | `[{ "name": "Alice" }, { "name": "Bob" }]` |

### DateTime Format

**Required format:** `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'`

**Example:** `2026-02-16T14:30:00.000Z`

**Compatibility:**
- ISO 8601 standard
- UTC timezone (Z suffix)
- Milliseconds included (`.SSS`)
- Compatible with JavaScript `Date`, Java `Instant`, etc.

**Source:** [Flow Services Server operation - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Integration/Connectors/r-atm-Flow_Services_Server_operation_39812d14-99b6-436a-8761-e5172ac6f0f1)

---

## Declaring Flow Values

Flow Values are declared at the **application level** and are available throughout the flow.

**Declaration location:** Flow > Values > Add Value

**Properties:**
- **Name**: Variable name (camelCase recommended)
- **Type**: String, Number, Boolean, Date, DateTime, Object, List
- **Default value**: Initial value (optional)
- **Description**: Documentation (optional)

**Example declarations:**

```
Flow Value: selectedDevAccountId
  - Type: String
  - Default: null
  - Description: Currently selected developer account ID

Flow Value: selectedPackage
  - Type: Object
  - Default: null
  - Description: Selected package from browser (includes componentId, packageId, componentName, etc.)

Flow Value: dependencyTree
  - Type: List
  - Default: []
  - Description: Resolved dependency tree from API call

Flow Value: promotionResults
  - Type: Object
  - Default: null
  - Description: Results from executePromotion API call

Flow Value: promotionId
  - Type: String
  - Default: null
  - Description: UUID of current promotion run
```

---

## Setting Flow Values

Flow Values can be set by:

1. **User input** (form fields, selections)
2. **Message step responses** (API call results)
3. **Business rules** (calculated values)
4. **Decision steps** (conditional assignments)
5. **Default values** (declared at application level)

### 1. User Input (Form Fields)

**Components bind to Flow Values via output binding:**

```
Text Input: "Deployment Notes"
  - Output binding: deploymentRequest.notes
  - User types: "Deploy to production after business hours"
  - Flow Value updated: deploymentRequest.notes = "Deploy to production after business hours"
```

**Data Grid selection:**

```
Data Grid: "Packages"
  - Data Source: packagesList
  - Selection: Single row
  - Output binding: selectedPackage
  - User selects row: Package "Orders Process"
  - Flow Value updated: selectedPackage = { componentId: "abc-123", componentName: "Orders Process", ... }
```

### 2. Message Step Responses

**Message step populates Flow Values from API responses:**

```
Message Step: listDevPackages
  - Request: { "devAccountId": selectedDevAccountId }
  - Response: { "packages": [...] }
  - Output mapping:
      packagesList ← response.packages
      packageCount ← response.packages.length
```

**Flow Values after message step completes:**

```
packagesList = [
  { componentId: "abc-123", componentName: "Orders Process", packageVersion: 10 },
  { componentId: "def-456", componentName: "Inventory Sync", packageVersion: 5 }
]

packageCount = 2
```

### 3. Business Rules (Calculated Values)

**Business rules can set Flow Values based on conditions:**

**Example: Set flag based on dependency count**

```
Business Rule: Set requiresPeerReview flag
Condition:
  IF dependencyTree.length > 20
  THEN set requiresPeerReview = $True
  ELSE set requiresPeerReview = $False
```

### 4. Decision Steps (Conditional Assignments)

**Decision steps can set Flow Values before routing:**

```
Decision Step: Set Review Stage
  ↓
Outcome A (if componentsFailed > 0):
  - Set reviewStage = "FAILED"
  - Route to Error Page

Outcome B (if componentsFailed == 0):
  - Set reviewStage = "PENDING_PEER_REVIEW"
  - Route to Peer Review Swimlane
```

---

## State Persistence Mechanisms

### 1. In-Memory State (Default)

Flow Values exist in memory during flow execution. State is maintained across page transitions within a session.

**Lifecycle:**
- User starts flow → Flow Values initialized
- User progresses through pages → Flow Values updated
- User completes flow → Flow Values cleared
- User closes browser (without async operation) → Flow Values lost

**Use case:** Short-lived flows (< 5 minutes), synchronous operations

### 2. IndexedDB Caching (Automatic)

Flow runtime automatically caches state to **IndexedDB** (browser-side storage) every **30 seconds**.

**Purpose:** Allow users to close browser and resume later (especially for long-running async operations)

**How it works:**

1. **User triggers async operation**: Clicks "Promote" button
2. **Flow shows wait state**: Spinner displayed
3. **Flow caches state to IndexedDB**: Every 30 seconds, state snapshot saved
   - Includes: All Flow Values, user context, current page, wait state
4. **User closes browser**: IndexedDB persists across browser restarts
5. **User returns to flow URL**: Flow loads state from IndexedDB cache
6. **Flow resumes**: User sees same page with same data, wait state continues
7. **Operation completes**: Flow receives callback, updates state, hides wait state

**State cached:**
- All Flow Values (primitives, objects, lists)
- User context (`$User` object)
- Current page and navigation history
- Wait state (if in async operation)

**State NOT cached:**
- Sensitive data (passwords, API tokens)
- Flow Values marked as "do not persist"
- Session-specific data (unless explicitly persisted)

**Survival:**
- Browser restart
- Tab close
- Network interruption
- Page refresh

**Expiration:**
- Default: 24 hours (configurable in Flow settings)
- After expiration, state cleared and flow resets

**Sources:**
- [Using IndexedDB - Web APIs](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Using_IndexedDB)
- [Best Practices for Persisting Application State with IndexedDB](https://web.dev/articles/indexeddb-best-practices-app-state)

### 3. No Long-Term Data Storage (By Design)

Flow does **NOT** provide long-term data storage. Business data must be stored in external systems:
- Boomi DataHub
- Customer databases
- Integrated third-party services (Salesforce, etc.)

**Flow's data handling is transient** — it processes data but does not retain it after flow completion.

**Implication:** If you need to audit or retrieve flow data later, store it in DataHub or external database via Integration process.

**Source:** [Data Handling - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Technical_overview/r-flo-Techref_Security_data_b0044f19-b7ff-4f8c-8632-18226017ec4a)

---

## Data Binding Patterns

### 1. Input Binding (Flow Value → Component)

Component **reads** value from Flow Value (display mode).

**Example: Display selected account name**

```
Presentation: "Selected Account"
  - Input binding: selectedDevAccountName
  - Displays: "DevTeamA"
```

### 2. Output Binding (Component → Flow Value)

Component **writes** user input to Flow Value (input mode).

**Example: Store form field value**

```
Text Input: "Deployment Notes"
  - Output binding: deploymentRequest.notes
  - User types: "Deploy after 6pm"
  - Flow Value updated: deploymentRequest.notes = "Deploy after 6pm"
```

### 3. Two-Way Binding (Component ↔ Flow Value)

Component both reads and writes Flow Value.

**Example: Toggle switch**

```
Toggle: "Require Peer Review"
  - Binding: requiresPeerReview
  - Initial state: $False (read from Flow Value)
  - User toggles on: requiresPeerReview = $True (writes to Flow Value)
  - Toggle reflects current state: ON (reads from Flow Value)
```

### 4. Object Data Binding (Complex Data → Custom Component)

Custom component receives complex object via `objectData` property.

**Example: XML diff viewer**

```
Custom Component: XmlDiffViewer
  - Object Data: diffData (from generateComponentDiff response)
  - Properties accessed:
      - diffData.branchXml
      - diffData.mainXml
      - diffData.componentName
      - diffData.componentAction
```

**How it works:**

1. **Message step populates Flow Value:**

```
Message Step: generateComponentDiff
  - Response: { "branchXml": "...", "mainXml": "...", "componentName": "Orders Process", ... }
  - Output mapping: diffData ← response
```

2. **Custom component receives objectData:**

```tsx
const XmlDiffViewer: React.FC<IComponentProps> = (props) => {
  const data = props.getObjectData<DiffData>();
  const branchXml = data[0]?.branchXml || '';
  const mainXml = data[0]?.mainXml || '';
  // ... render diff
};
```

### 5. List Binding (Array → Data Grid)

Data grid displays list of items.

**Example: Packages data grid**

```
Message Step: listDevPackages
  - Response: { "packages": [...] }
  - Output mapping: packagesList ← response.packages

Data Grid: "Packages"
  - Data Source: packagesList (List<Package>)
  - Columns: map to Package properties (componentName, packageVersion, componentType, etc.)
```

---

## Asynchronous Operations and Wait States

### Use Case: Long-Running Operations

**Scenario:** Promoting 50 components via Platform API takes 5+ minutes.

**Challenge:**
- HTTP request would timeout (default 30-60 seconds)
- User needs feedback (not just blank screen)
- User might close browser and come back later

**Solution:** Async operations with wait states and IndexedDB caching.

### How It Works

**Page 2 → Page 3 transition:**

```
Page 2: Promotion Review
  ↓
User clicks "Promote" button
  ↓
Outcome triggers Message Step: executePromotion
  ↓
Flow Service receives request
  ↓
Integration process starts (Process C: executePromotion)
  ↓
Process detects 50 components to promote (> 1 minute execution)
  ↓
Process returns wait response to Flow:
  {
    "status": "WAIT",
    "message": "Promoting components to primary account...",
    "progress": 0
  }
  ↓
Flow shows wait state overlay:
  - Spinner animation
  - "Promoting components to primary account..."
  - "Processing component 5 of 50..." (if progress available)
  - Progress bar (if progress available)
  - "This may take several minutes. You can safely close this window."
  ↓
Flow caches state to IndexedDB (every 30 seconds):
  - promotionId, selectedPackage, dependencyTree, branchId
  ↓
User closes browser (goes to lunch)
  ↓
Process continues running (for-each loop, 50 API calls)
  ↓
Process completes (5 minutes later)
  ↓
Flow Service sends callback with promotion results:
  {
    "status": "SUCCESS",
    "success": true,
    "promotionId": "uuid",
    "results": [...]
  }
  ↓
User returns to browser, navigates to flow URL
  ↓
Flow resumes from IndexedDB cache
  ↓
Flow receives completion callback, hides spinner
  ↓
Page 3: Promotion Status
  - Results grid populated
  - Summary counts displayed
  - "Submit for Deployment" button enabled
```

**No user intervention required** — Flow handles all state management automatically.

### Implementation

**Integration Process (Process C: executePromotion):**

```
Start (Flow Services Server - Listen)
  ↓
Data Process: Count components
  componentsToPromote = dependencyTree.length
  ↓
Decision: Will this take > 30 seconds?
  IF componentsToPromote > 20:
    Return Wait Response:
      {
        "status": "WAIT",
        "message": "Promoting components to primary account...",
        "progress": 0
      }
  ELSE:
    Proceed normally (synchronous)
  ↓
For-each loop: Promote each component
  ↓ (Optional: Update progress every 10 components)
Send Progress Update to Flow:
  {
    "status": "WAIT",
    "message": "Processing component 10 of 50...",
    "progress": 20
  }
  ↓
Process completes
  ↓
Return Final Response:
  {
    "status": "SUCCESS",
    "success": true,
    "promotionId": "uuid",
    "results": [...]
  }
```

**Flow (Page 3: Promotion Status):**

```
Wait State Overlay (conditional, shown when status == "WAIT"):
  - Spinner animation
  - Message: promotionResults.message
  - Progress: promotionResults.progress (if available)
  - Subtext: "This may take several minutes. You can safely close this window."

Results Section (conditional, shown when status == "SUCCESS"):
  - Data Grid: promotionResults.results
  - Summary: componentsPassed, componentsFailed
  - Button: "Submit for Deployment" (enabled if componentsFailed == 0)
```

---

## Example: Promotion Dashboard Flow Values

From the project's `flow-structure.md`:

| Variable Name | Type | Purpose |
|--------------|------|---------|
| `selectedDevAccountId` | String | Currently selected developer account ID |
| `selectedDevAccountName` | String | Developer account display name |
| `packagesList` | List | List of packages from listDevPackages response |
| `selectedPackage` | Object | Selected package from browser (includes componentId, packageId, componentName, etc.) |
| `dependencyTree` | List | Resolved dependency tree from resolveDependencies response |
| `promotionResults` | Object | Results from executePromotion API call |
| `promotionId` | String | UUID of current promotion run |
| `branchId` | String | Promotion branch ID for diff viewing |
| `deploymentRequest` | Object | Deployment notes and metadata |
| `userSsoGroups` | List | User's Azure AD group memberships (from `$User/Groups`) |
| `peerReviewerEmail` | String | Email of authenticated peer reviewer (from `$User/Email`) |
| `peerReviewQueue` | List | List of promotions pending peer review |
| `selectedPeerReview` | Object | Selected promotion from peer review queue |
| `adminApprovalQueue` | List | List of promotions pending admin approval |
| `selectedAdminApproval` | Object | Selected promotion from admin approval queue |
| `diffData` | Object | Component diff data from generateComponentDiff response |
| `integrationPacksList` | List | List of Integration Packs from listIntegrationPacks response |
| `selectedIntegrationPack` | Object | Selected Integration Pack for deployment |

---

## Best Practices

### 1. Minimize Flow Values

**Guideline:** Only store what's needed across pages.

**Bad practice:**

```
Flow Value: package1ComponentName
Flow Value: package1ComponentId
Flow Value: package1PackageVersion
Flow Value: package2ComponentName
Flow Value: package2ComponentId
Flow Value: package2PackageVersion
... (50+ Flow Values for 10 packages)
```

**Good practice:**

```
Flow Value: packagesList (List<Package>)
  - Stores all packages in a single list
  - Access via: packagesList[0].componentName, packagesList[1].packageVersion, etc.

Flow Value: selectedPackage (Object)
  - Stores currently selected package
  - Access via: selectedPackage.componentName, selectedPackage.packageVersion, etc.
```

### 2. Clear State on Flow End

**Guideline:** Avoid bloating browser storage.

**Implementation:**

```
Page 8: Deployment Complete
  ↓
Outcome: "Done"
  ↓
Decision Step: Clear State
  - Set all Flow Values to null or default values
  - Clear IndexedDB cache (automatic on flow completion)
  ↓
Return to Page 1 (flow resets)
```

### 3. Use Message Step Responses

**Guideline:** Store API responses in Flow Values for display.

**Pattern:**

```
Message Step: executePromotion
  - Response: { "success": true, "promotionId": "uuid", "results": [...] }
  - Output mapping:
      promotionId ← response.promotionId
      promotionResults ← response  (store entire response)

Page 3: Promotion Status
  - Data Grid: promotionResults.results
  - Summary: promotionResults.componentsPassed, promotionResults.componentsFailed
```

### 4. Leverage IndexedDB Caching

**Guideline:** Design for async operations, allow users to close browser.

**User messaging:**

```
Wait State Overlay:
  - "Promoting components to primary account..."
  - "This may take several minutes. You can safely close this window."
  - "Your progress will be saved. Return to this URL to check status."
```

**Technical implementation:**
- Flow automatically caches state every 30 seconds
- No manual configuration needed
- Flow resumes when user returns to URL (with state ID)

### 5. No Long-Term Storage

**Guideline:** Store business data in external systems (DataHub, databases).

**Pattern:**

```
Message Step: executePromotion
  - Integration process:
      1. Promote components via Platform API
      2. Store results in DataHub PromotionLog record
      3. Return results to Flow

Message Step: queryStatus
  - Integration process:
      1. Query DataHub PromotionLog records
      2. Return results to Flow
  - Flow displays results (read-only)
```

**Benefit:** Audit trail persists beyond flow execution, can be queried later.

---

## Troubleshooting

### Issue: Flow Value not updating

**Possible causes:**
1. Output binding not configured on component
2. Component not triggering change event
3. Business rule preventing update
4. Typo in Flow Value name (case-sensitive)

**Resolution:**
1. Verify component has output binding configured
2. Check component's change event trigger (e.g., on blur, on change)
3. Review business rules that might be blocking update
4. Double-check Flow Value name (exact match, case-sensitive)

### Issue: Flow state lost after browser close

**Possible causes:**
1. IndexedDB disabled in browser
2. State ID not preserved in URL
3. Flow instance expired (> 24 hours old)
4. User navigated to different URL (lost state ID)

**Resolution:**
1. Enable IndexedDB in browser settings
2. Ensure user returns to same URL (with state ID query parameter)
3. Extend state expiration in Flow settings if needed
4. Provide "bookmark this URL" guidance to users

### Issue: Custom component not receiving objectData

**Possible causes:**
1. Object Data binding not configured on component
2. Flow Value is null or undefined
3. Component not using HOC (`component` wrapper)
4. Property name mismatch (case-sensitive)

**Resolution:**
1. Verify component's Object Data property is bound to Flow Value
2. Check that Flow Value is populated (use debug mode to inspect)
3. Use HOC wrapper for simplified property access
4. Double-check property names match JSON profile (case-sensitive)

---

## Sources

- [Flow Services Server operation - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Integration/Connectors/r-atm-Flow_Services_Server_operation_39812d14-99b6-436a-8761-e5172ac6f0f1)
- [Data Handling - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Technical_overview/r-flo-Techref_Security_data_b0044f19-b7ff-4f8c-8632-18226017ec4a)
- [Using IndexedDB - Web APIs](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Using_IndexedDB)
- [Best Practices for Persisting Application State with IndexedDB](https://web.dev/articles/indexeddb-best-practices-app-state)

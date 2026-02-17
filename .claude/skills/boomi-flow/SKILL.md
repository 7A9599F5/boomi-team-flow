---
name: boomi-flow
description: |
  Boomi Flow low-code platform reference. Use when working with Flow dashboard
  pages, swimlane authorization, Flow Services, message actions, custom components,
  page layouts, business rules, or SSO/identity configuration.
globs:
  - "flow/**"
  - "**/flow-*.md"
---

# Boomi Flow — Low-Code Workflow Platform

## Overview

**Boomi Flow** is a cloud-native, low-code workflow automation platform that enables building applications and workflows visually using a drag-and-drop interface. It provides both UI design (pages) and workflow logic (flow canvas) in a unified environment.

**Key capabilities:**
- Visual page builder with standard and custom components
- Swimlane-based authorization (SSO groups, multi-stage approvals)
- Flow Services integration with Boomi Integration processes
- State management with browser-side persistence (IndexedDB)
- Custom React components for specialized UI elements
- Business rules for conditional logic and routing

---

## Architecture: Swimlanes → Pages → Outcomes → Services

### Application Structure

```
Flow Application
├── Swimlanes (0 or more) — Authorization containers
│   └── Pages — UI screens with components
│       └── Outcomes — Navigation paths (button clicks, routing)
│           └── Steps — Messages, Decisions, Swimlanes
│               └── Flow Services — Backend Integration processes
└── Flow Values — State variables (persist across pages)
```

### Execution Model

1. **User loads page** → Flow Values populated (from message steps or previous state)
2. **User interacts** → Components update Flow Values
3. **User triggers outcome** → Button click, form submit
4. **Flow evaluates business rules** → Determine which outcome path to follow
5. **Next step executes** → Message step (API call), Decision step (routing), or Page (display)
6. **State persists** → Flow Values cached to IndexedDB (every 30 seconds for async ops)

**Key principle:** Flow is stateful — user context, selections, and data persist across pages within a flow instance.

---

## Core Components

### 1. Pages
**Purpose:** UI screens and logic containers

**Components of a page:**
- **Containers**: Layout elements (rows, columns, grids)
- **Components**: UI elements (inputs, tables, buttons, presentations, data grids)
- **Outcomes**: Navigation paths to other steps (trigger message steps, decisions, page transitions)
- **Page conditions**: Business rules controlling page visibility or behavior

**Common page types:**
- **List/Browser pages**: Display data grids with filtering and selection
- **Detail/Form pages**: Collect user input, display detailed data
- **Review/Approval pages**: Show summary data with approve/reject actions
- **Status/Results pages**: Display operation results, wait states, success/error messages

**Sources:** Reference `reference/pages-navigation.md` for detailed page patterns.

### 2. Swimlanes
**Purpose:** Authorization containers that restrict access to flow sections

**How they work:**
- Act as containers on the flow canvas
- Challenge users for authentication when entering
- Support SSO groups (Azure AD, Okta, Salesforce) or individual users
- Flow execution pauses at swimlane boundaries until authorized user continues

**Common use case: Multi-stage approval workflows**

```
Developer Swimlane (SSO group: "Boomi Developers")
  ↓
  Page 1: Submit request
  ↓ (Email notification sent)
Peer Review Swimlane (SSO groups: "Boomi Developers" OR "Boomi Admins")
  ↓ (Flow pauses until peer reviewer authenticated)
  Page 5: Review and approve/reject
  ↓ (Email notification sent)
Admin Swimlane (SSO group: "Boomi Admins")
  ↓ (Flow pauses until admin authenticated)
  Page 7: Final approval and deployment
```

**Access control:**
- Per-swimlane authorization (different requirements per swimlane)
- OR logic for groups (user in ANY listed group can access)
- `$User` object provides identity context (`$User/Email`, `$User/Groups`, etc.)
- Backend logic can prevent self-review (compare `$User/Email` with record owner)

**Sources:** Reference `reference/swimlanes-auth.md` for SSO configuration and authorization patterns.

### 3. Flow Values
**Purpose:** State variables that persist across pages

**Types:**
- **String**: Text values
- **Number**: Numeric values
- **Boolean**: True/false flags
- **Date/DateTime**: Temporal values (format: `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'`)
- **Object**: Complex data structures (JSON-like)
- **List**: Arrays of values or objects

**Lifecycle:**
- Declared at application level
- Set by user input, message step responses, business rules, decision steps
- Persist in memory during flow execution
- Automatically cached to IndexedDB every 30 seconds (allows browser close/resume)
- No long-term storage — Flow is transient, business data stored externally

**Data binding patterns:**
- **Input binding**: Component reads value (e.g., display selected account name)
- **Output binding**: Component writes user input (e.g., store form field value)
- **Object data binding**: Custom components receive complex data via `objectData` property

**Sources:** Reference `reference/values-state.md` for state management patterns.

### 4. Outcomes
**Purpose:** Navigation paths triggered by user actions or business rules

**How they work:**
- Attached to pages, messages, decisions, swimlanes
- Triggered by user actions (button clicks, form submissions)
- Can have business rules (conditional routing)
- Priority-based (order numbers determine which outcome follows if multiple match)

**Outcome types:**
- **Page transitions**: Navigate to another page
- **Message step calls**: Invoke Integration process via Flow Service
- **Decision step routing**: Evaluate Flow Values and route accordingly
- **Swimlane transitions**: Cross authorization boundary

**Sources:** Reference `reference/pages-navigation.md` for outcome patterns and routing logic.

---

## Message Actions vs Data Actions

Flow Services support two operation types: **Message Actions** and **Data Actions**. Understanding when to use each is critical.

### Message Actions

**Purpose:** Execute complex business logic and return custom responses

**How they work:**
1. Flow calls Message Action via Message Step
2. Integration process receives request, executes logic (API calls, data transformations, etc.)
3. Process returns custom response (JSON structure defined by developer)
4. Flow receives response and stores it in Flow Values

**Use cases:**
- Complex multi-step operations (promotion execution, approval workflows)
- Custom calculations or aggregations
- External API calls (Platform API, third-party services)
- Operations that don't fit CRUD patterns
- Full control over request/response structure

**Integration setup:**
- Service Type: Message Action
- Request/Response Profiles: Custom JSON profiles (defined by developer)
- Start shape: Flow Services Server connector in Listen mode
- Process logic: Any Integration shapes (Map, Decision, Business Rules, API calls, etc.)

**Flow setup:**
- Step type: Message Step
- Input mapping: Map Flow Values to request properties
- Output mapping: Map response properties to Flow Values
- Request/Response Types: Auto-generated based on JSON profiles

**Example:**

```
Message Action: executePromotion

Request Profile (JSON):
{
  "componentId": "string",
  "devAccountId": "string",
  "dependencyTree": [...]
}

Response Profile (JSON):
{
  "success": true,
  "promotionId": "uuid",
  "branchId": "uuid",
  "results": [...]
}

Flow Message Step:
- Input: selectedPackage.componentId, selectedDevAccountId, dependencyTree
- Output: promotionId, branchId, promotionResults
```

### Data Actions

**Purpose:** Perform standard CRUD operations (Create, Read, Update, Delete) on a specific data type

**How they work:**
1. Flow uses Database Step (Database Load, Database Save, Database Delete)
2. Flow Service Data Action maps to Integration process
3. Process performs CRUD operation and returns standardized response
4. Flow automatically handles the data according to step type

**Use cases:**
- Standard CRUD operations on a single record type
- Consistent data access patterns across multiple flows
- Simple read/write operations
- When you want Flow's built-in database step UX

**Integration setup:**
- Service Type: Data Action
- Type: Defines the data structure (e.g., "Customer", "Order")
- JSON Profile: Defines the structure of the record type
- Start shape: Flow Services Server connector in Listen mode
- Process logic: Typically simpler than Message Actions (direct DB queries, etc.)

**Flow setup:**
- Step type: Database Load / Database Save / Database Delete
- Service: Boomi Integration Service connector
- Type: Select the data type (from Data Actions)
- Filters/Values: Flow automatically provides appropriate UI based on step type

### Decision Matrix: When to Use Each

| Criteria | Message Actions | Data Actions |
|----------|----------------|--------------|
| **Operation type** | Complex, custom logic | Standard CRUD |
| **Response structure** | Custom JSON | Standardized by Type |
| **Request/Response types** | Unique per action | Shared across operations |
| **Flow step type** | Message Step | Database Step |
| **Reusability** | Per-action basis | Type-based (high reuse) |
| **Control level** | Full control | Framework-constrained |
| **Use case** | Promotion execution, approval workflows | Customer records, order management |

**Rule of thumb:**
- **Use Message Actions when** you need full control or operations don't fit CRUD patterns
- **Use Data Actions when** operations are standard CRUD and you want consistency across flows

**Sources:** Reference `reference/flow-services.md` for detailed Flow Service configuration.

---

## Flow Service Configuration

### What is a Flow Service?

A **Flow Service** is a component in Boomi Integration that exposes Integration processes as APIs that Flow applications can call. It acts as the bridge between Flow (frontend) and Integration (backend logic).

### Flow Service Component (in Integration)

**Location:** Boomi Integration > Components > Flow Service

**Key properties:**
- **Path to Service**: URI path (e.g., `/promotion-service`)
  - Used by Flow's Boomi Integration Service connector
  - Must be unique within Integration account
- **Operations**: Message Actions and Data Actions defined within the service

### Flow Service in Flow

**Location:** Flow > Services > Boomi Integration Service connector

**Configuration:**
- **Connector Type**: Boomi Integration Service
- **Path to Service**: Matches the Flow Service's Path to Service in Integration
- **Authentication**: Boomi account credentials or token-based auth
- **Message Actions**: Available operations exposed by the Flow Service

### Flow Service Server Connector

**Purpose:** Listener for incoming requests from Flow applications (Start shape in Integration processes)

**Connector name:** `Boomi Flow Services Server`

**Start Shape Setup:**
- **Connector**: Boomi Flow Services Server
- **Operation**: Listen (only supported action)
- **Service Type**: Message Action OR Data Action
- **Response Profile**: JSON profile defining response structure

**Operation limitations:**
- Arrays (Absolute) NOT supported
- Lists must contain objects (not simple elements or lists of lists)
- DateTime format required: `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'`
- Low Latency mode required

### Async Operations and Wait Responses

**Problem:** Long-running processes (e.g., promoting 50 components) can take minutes. Flow needs to handle this without timeouts.

**Solution:** Flow Service supports **wait responses**:

1. Process starts execution
2. If operation will take > 30 seconds, process returns wait response to Flow
3. Flow displays spinner/loading state to user
4. Flow Service caches state to IndexedDB (every 30 seconds)
5. Process continues running in background
6. When process completes, Flow Service sends callback to Flow
7. Flow resumes and displays results

**User experience:**
- User sees "Promoting components..." with spinner
- User can close browser (state cached)
- User returns later → Flow automatically resumes and shows results
- Modern async UX without "keep this window open" warnings

**Sources:** Reference `reference/flow-services.md` for timeout management and async patterns.

---

## Swimlane Authorization

### Quick Reference

**Swimlane capabilities:**
- Restrict access to flow sections based on SSO groups or individual users
- Pause flow execution at boundaries until authorized user continues
- Support OR logic for groups (user in ANY listed group can access)
- Enable multi-stage approval workflows (Developer → Peer Review → Admin)

**SSO Groups:**
- Azure AD / Microsoft Entra ID
- Okta
- Salesforce
- SAML 2.0-based providers
- ADFS (Active Directory Federation Services)

**$User Object Properties:**
- `$User/Email`: User email address
- `$User/First Name`: User first name
- `$User/Last Name`: User last name
- `$User/Groups`: List of SSO group memberships
- `$User/Username`: Username (if different from email)
- `$User/ID`: Unique user identifier

**Usage patterns:**
- **Bind to Flow Values**: `peerReviewerEmail = $User/Email`
- **Business Rules**: `Show when: $User/Groups contains "Boomi Admins"`
- **Self-review prevention**: `IF $User/Email == selectedPeerReview.initiatedBy THEN block access`

**Sources:** Reference `reference/swimlanes-auth.md` for detailed SSO configuration and authorization patterns.

---

## Custom Components

### Overview

Flow supports **custom React components** that can be registered and used in the page builder alongside standard components.

**Use cases:**
- Custom visualizations (charts, graphs, diff viewers)
- Specialized input controls (date pickers, code editors, signature pads)
- Third-party widget integrations
- Domain-specific UI elements

### Component Development

**Component types:**
1. **Standard Custom Components**: General-purpose UI components
2. **Column Custom Components**: For use in tables/datagrids

**Development workflow:**
1. **Build React component** using TypeScript/JavaScript
   - Official boilerplate: `Boomi-PSO/ui-custom-component` (GitHub)
2. **Register with Flow runtime** using `manywho.component.register`
3. **Build and bundle** (`npm run build` → `dist/custom-component.js`, `dist/custom-component.css`)
4. **Upload to tenant** as assets (`npm run upload`)
5. **Register in Flow** (Components > New Component) or use Custom Player

### ObjectData Binding

**ObjectData** is Flow's mechanism for passing data to custom components.

**How it works:**
1. In Flow page builder, add custom component to page
2. Bind **Object Data** to a Flow Value (e.g., `diffData` from API response)
3. Component receives data via `props.objectData`

**With HOC (`component` wrapper):**

```javascript
const objectData = props.getObjectData();
const propertyValue = objectData[0].PropertyName; // Direct property access
objectData[0].PropertyName = 'New Value'; // Can also set values
```

**Type safety:**

```typescript
interface DiffData {
  branchXml: string;
  mainXml: string;
  componentName: string;
  componentAction: 'CREATE' | 'UPDATE';
}

const XmlDiffViewer: React.FC<IComponentProps> = (props) => {
  const data = props.getObjectData<DiffData>();
  const branchXml = data[0]?.branchXml || '';
  // ...
};
```

**Sources:** Reference `reference/custom-components.md` for detailed component development patterns.

---

## Business Rules and Conditional Logic

### Purpose

**Business Rules** define conditional logic that controls flow behavior, routing, and visibility.

**Use cases:**
- Route flow execution based on conditions (outcome selection)
- Control component/page visibility
- Validate data and flag errors
- Create complex decision trees

### Where Business Rules Are Used

1. **Outcomes**: Determine which outcome path to follow from a step
2. **Page Conditions**: Control when a page is accessible
3. **Component Visibility**: Show/hide components based on conditions

### Syntax

**Comparison Operators:**
- `ANY` = OR logic (at least one condition must be true)
- `ALL` = AND logic (all conditions must be true)

**Value Comparisons:**
- Equals (`==`), Not equals (`!=`)
- Greater than (`>`), Less than (`<`)
- Contains (string/list contains value)
- Is empty / Is not empty

**Example: Outcome Business Rule**

```
ALL (AND)
  requiresCreditCard == $True
```

**Example: Complex Nested Rule**

```
ALL (AND)
  - CompanyCar == $False
  - OfficeLocation == "Chesterbrook"
  - ANY (OR)
      - WorkPhone == "Apple"
      - WorkPhone == "Samsung"
```

### Outcome Priority

If multiple outcomes have business rules that match, Flow follows the outcome with the **highest priority (lowest order number)**.

**Order values:**
- Outcome with order `0` takes precedence over order `1`
- Outcome with order `1` takes precedence over order `2`

**Best practice:** Set business rules such that only one outcome matches at a time, or use order priority intentionally for fallback logic.

**Sources:** Reference `reference/business-rules.md` for detailed conditional logic patterns.

---

## Reference Files

| File | Topics |
|------|--------|
| `reference/swimlanes-auth.md` | Swimlane config, SSO groups, `$User` object, 2-layer approval |
| `reference/pages-navigation.md` | Page types, outcomes, navigation model |
| `reference/flow-services.md` | Message Action binding, Flow Service config, FSS interaction |
| `reference/values-state.md` | Flow values, types, state persistence, IndexedDB caching |
| `reference/custom-components.md` | React custom components, custom player, objectData binding |
| `reference/business-rules.md` | Conditional logic, validation, visibility rules |
| `examples/promotion-dashboard.md` | Project-specific: 8 pages, 3 swimlanes, Message Actions |

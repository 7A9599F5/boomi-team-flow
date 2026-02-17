# Process Shapes Reference

All process shapes in Boomi Integration with detailed configuration, behavior, and use cases.

---

## Core Shapes

### Start Shape

**Purpose**: Defines how the process begins execution.

**Connector Types**:

| Type | Description | Use Cases |
|------|-------------|-----------|
| **No Data** | Process starts with no incoming document | Scheduled processes, routes called by other processes |
| **Listener** | Waits for incoming requests | HTTP endpoints, Flow Service endpoints, database polling, file watcher |
| **Application Connector** | Initiates on external events | Salesforce outbound messages, webhook triggers |

**Operation Types**:
- **Listen**: Passive listening (HTTP, Flow Service)
- **GET**: Retrieve data from source (Database, File, HTTP GET)
- **QUERY**: Query-based retrieval (Database query, API query)

**Configuration**:
```yaml
Start Shape:
  Connector: [No Data | HTTP Server | Flow Service Server | Database | File | ...]
  Operation: [Listen | GET | QUERY]
  Profile: [Response profile for incoming data]
```

**Example** (Flow Service listener):
```
Start Shape:
  Connector: Boomi Flow Services Server
  Action: Listen
  Operation: executePromotion
  Response Profile: ExecutePromotionRequest
```

---

### End Shape

**Purpose**: Terminates the process execution.

**Behavior**:
- Marks the end of an execution path
- All paths must end with an End shape
- Does NOT return data (unless listener process with response profile)

**Configuration**: No configuration required.

**Example**:
```
[Processing Logic]
  ↓
End
```

---

### Branch Shape

**Purpose**: Splits execution into multiple parallel paths.

**Behavior**:
- **All branches execute** (not conditional)
- All branches receive the **same input documents**
- Property changes on one branch do **NOT** affect other branches
- Process properties (DPPs) are **shared** across branches

**Use Cases**:
- Send same data to multiple destinations
- Parallel processing paths
- Multi-channel notifications

**Example**:
```
Start
  ↓
Branch
  ├─→ HTTP Client (send to System A)
  ├─→ HTTP Client (send to System B)
  └─→ Database (log record)
```

**Warning**: Document property changes on one branch are isolated. Use process properties for cross-branch communication.

---

### Decision Shape

**Purpose**: Conditional routing based on property values (if-then-else).

**Conditions**:
- Based on document properties, process properties, or execution properties
- Operators: `=`, `!=`, `<`, `>`, `<=`, `>=`, `contains`, `starts with`, `ends with`, `matches regex`
- Multiple conditions: AND/OR logic

**Outputs**:
- **True Path**: Condition matches
- **False Path**: Condition does not match
- **No Data Path**: No documents match (optional)

**Configuration**:
```yaml
Decision Shape:
  Condition:
    Property: document.dynamic.userdefined.status
    Operator: =
    Value: SUCCESS
```

**Example**:
```
Decision (status = SUCCESS?)
  ├─→ True Path: Continue processing
  └─→ False Path: Error handling
```

**Advanced**: Multiple conditions with AND/OR:
```yaml
Condition 1: status = SUCCESS
AND
Condition 2: recordCount > 0
```

---

### Route Shape

**Purpose**: Calls a subprocess or Process Route component.

**Route Types**:

| Type | Behavior | Use Cases |
|------|----------|-----------|
| **Passthrough** | Documents flow through subprocess and return | Transformations, enrichment, validation |
| **Non-Passthrough** | Fire-and-forget (no return) | Async notifications, parallel processing, logging |

**Process Property Passing**:
- Can pass static or dynamic process properties to subprocess
- Map DPPs from calling process to subprocess DPPs

**Configuration**:
```yaml
Route Shape:
  Process Route Component: PROMO - Route - ProcessComponent
  Passthrough: true
  Process Properties:
    - Source: devAccountId (DPP)
      Target: targetAccountId (subprocess DPP)
```

**Example** (recursive loop):
```
Decision (queue not empty?)
  ↓ True
Route (call self)
  ↓
End
```

---

### Try/Catch Shape

**Purpose**: Captures process-level or document-level errors for custom error handling.

**Behavior**:
1. Documents enter **Try** path
2. If a document **fails** during processing → sent to **Catch** path
3. Original document and properties are **preserved** in Catch path
4. Other documents (that didn't fail) continue on Try path

**Error Message Property**: `document.property.metadata.base.trycatchmessage`

**Configuration**: No configuration required (behavior is automatic).

**Example**:
```
Try/Catch
  ├─→ Try Path:
  │     → HTTP Client (call API)
  │     → Map (transform)
  │     → Database (insert)
  │     → End
  │
  └─→ Catch Path:
        → Set Properties (capture error message)
        → Notify (email alert)
        → Database (log error)
        → End
```

**Nested Try/Catch**: Inner Try/Catch captures errors from nested steps; outer captures errors from inner Try/Catch.

**See**: `error-handling.md` for advanced patterns.

---

### Data Process Shape

**Purpose**: Performs custom transformations and logic using processing steps.

**Processing Step Types**:

| Type | Purpose |
|------|---------|
| **Custom Scripting** | Execute Groovy or JavaScript code |
| **Split Documents** | Split document into multiple (by line, profile element, etc.) |
| **Combine Documents** | Merge multiple documents into one |
| **Search/Replace** | Regex-based search and replace |
| **BASE64 Encode/Decode** | Encode/decode document data |
| **PGP Encrypt/Decrypt** | Encrypt/decrypt with PGP |
| **Zip/Unzip** | Compress/decompress documents |
| **XSLT Transformation** | Apply XSLT stylesheet to XML |

**Custom Scripting**: See SKILL.md and Groovy scripting patterns.

**Example** (Groovy script):
```groovy
import com.boomi.execution.ExecutionUtil

def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String content = is.getText("UTF-8")
    // ... process content ...

    dataContext.storeStream(
        new ByteArrayInputStream(modifiedContent.getBytes("UTF-8")),
        props
    )
}
```

---

### Map Shape

**Purpose**: Transforms data between profiles using field mappings.

**Configuration**:
```yaml
Map Shape:
  Source Profile: OrderRequest (JSON)
  Destination Profile: SalesforceOpportunity (JSON)
  Mappings:
    - Source: orderNumber → Target: OpportunityName
    - Source: orderTotal → Target: Amount
    - Function: Current Date → Target: CloseDate
```

**Mapping Functions**:
- String functions: substring, concat, uppercase, lowercase
- Date functions: current date, add days, format date
- Math functions: add, subtract, multiply, divide
- Conditional functions: if-then-else, lookup
- Custom Groovy scripts: inline Groovy for complex logic

**Example**:
```
HTTP Client (retrieve JSON)
  ↓
Map (transform JSON to Salesforce format)
  ↓
Salesforce Connector (create Opportunity)
```

---

### Set Properties Shape

**Purpose**: Sets document or process property values.

**Property Types**:
- **Dynamic Document Properties**: `document.dynamic.userdefined.{name}`
- **Dynamic Process Properties**: DPPs set via property component
- **HTTP Headers**: `document.dynamic.userdefined.http.header.{HeaderName}`

**Configuration**:
```yaml
Set Properties Shape:
  Properties:
    - Name: document.dynamic.userdefined.fileName
      Value: output.json
      Type: Static
    - Name: document.dynamic.userdefined.timestamp
      Value: {function:CurrentDate}
      Type: Function
```

**Example** (set HTTP header):
```
Set Properties
  - document.dynamic.userdefined.http.header.Authorization = Bearer abc123
  ↓
HTTP Client (call API with auth header)
```

---

### Message Shape

**Purpose**: Sends email notifications.

**Configuration**:
```yaml
Message Shape:
  Email Configuration:
    To: admin@example.com
    From: noreply@boomi.com
    Subject: Process Error Alert
    Body: [Plain text or HTML]
  Attachment: [Optional: attach current document]
```

**Use Cases**:
- Error notifications (send from Catch path)
- Completion notifications
- Daily summary reports

**Example**:
```
Try/Catch
  └─→ Catch Path:
        → Message (send error email)
        → End
```

---

### Stop Shape

**Purpose**: Immediately halts process execution.

**Behavior**:
- Terminates execution for **ALL documents** in the batch
- No downstream steps are executed
- Process execution is marked as **failed**

**Use Cases** (rare):
- Critical validation failure (e.g., missing configuration)
- Emergency shutdown logic
- Testing/debugging

**Warning**: Stop is aggressive — prefer **Decision** shape with branching for conditional logic.

**Example**:
```
Decision (config missing?)
  ├─→ True: Stop (halt execution)
  └─→ False: Continue processing
```

---

## Connector Shapes

### HTTP Client Connector

**Purpose**: Send HTTP/HTTPS requests to external APIs.

**Operations**:
- **GET**: Retrieve data from server
- **POST/SEND**: Send data to server
- **QUERY**: Query-based retrieval

**See**: `http-client.md` for detailed configuration.

---

### DataHub Connector

**Purpose**: Access Boomi DataHub for master data management.

**Operations**:
- **Query Golden Records**: Retrieve records from universe
- **Update Golden Records**: Upsert records (create/update)
- **Delete Golden Records**: Delete records by ID

**See**: `datahub-connector.md` for detailed configuration.

---

### Database Connector

**Purpose**: Interact with SQL databases.

**Operations**:
- **QUERY**: Execute SELECT statement
- **EXECUTE**: Execute INSERT/UPDATE/DELETE statement
- **STORED PROCEDURE**: Call stored procedure

**Configuration**:
```yaml
Database Connection:
  Type: [MySQL | PostgreSQL | SQL Server | Oracle | ...]
  Host: db.example.com
  Port: 3306
  Database: production
  Username: boomi_user
  Password: [encrypted]

Database Operation:
  Type: QUERY
  SQL: SELECT * FROM orders WHERE status = 'NEW'
  Response Profile: OrderRecord (auto-generated from SQL)
```

---

### Salesforce Connector

**Purpose**: Interact with Salesforce CRM.

**Operations**:
- **CREATE**: Create new record
- **QUERY**: Execute SOQL query
- **UPDATE**: Update existing record
- **DELETE**: Delete record
- **UPSERT**: Create or update based on external ID

**Configuration**:
```yaml
Salesforce Connection:
  Type: [Production | Sandbox]
  Username: user@example.com
  Password + Security Token: [encrypted]
  API Version: v58.0

Salesforce Operation:
  Type: CREATE
  Object: Opportunity
  Request Profile: OpportunityCreate (auto-generated)
```

---

## Advanced Shapes

### Connector Call Shape

**Purpose**: Deprecated (use standard Connector shapes instead).

---

### Business Rules Shape

**Purpose**: Execute complex decision logic using a business rules engine.

**Use Cases**:
- Complex conditional logic (beyond Decision shape)
- Externalized business rules (non-technical users can modify)

**Configuration**: Requires Business Rules component (separate license).

---

### Disk Shape

**Purpose**: Read/write files to local disk (Atom/Molecule only, not Cloud).

**Use Cases**:
- Batch file processing
- Temporary file storage
- On-premise integrations

**Warning**: Not available on Cloud runtimes.

---

## Shape Connection Rules

### Valid Connections

- **Start** → Any shape (except End)
- **Connector** → Any shape (except Start)
- **Decision** → Any shape (except Start), splits into True/False paths
- **Branch** → Any shape (except Start), splits into multiple parallel paths
- **Try/Catch** → Any shape (except Start), splits into Try/Catch paths
- **Route** → Any shape (if passthrough), End (if non-passthrough)
- **End** → No outgoing connections

### Invalid Connections

- Cannot connect **End** → any shape
- Cannot connect any shape → **Start**
- Cannot create circular loops without **Route** shape (use Route for recursion)

---

## Best Practices

### Start Shape
- Use **No Data** for scheduled processes and routes
- Use **Listener** for HTTP endpoints, Flow Service endpoints
- Always assign response profile for listener processes

### Branch Shape
- Use for parallel execution (all branches run)
- Remember: document property changes are isolated per branch
- Use process properties (DPPs) for cross-branch communication

### Decision Shape
- Use for conditional routing (if-then-else)
- Prefer Decision over Stop shape for error handling
- Use **No Data** path for fallback logic

### Route Shape
- Use **Passthrough** for transformations/validations
- Use **Non-Passthrough** for async notifications/logging
- Map process properties explicitly (don't rely on auto-mapping)

### Try/Catch Shape
- Use to prevent process failures (not for flow control)
- Always handle Catch path (don't leave it empty)
- Read `trycatchmessage` property for error details

### Data Process Shape
- Always call `dataContext.storeStream()` (never skip output)
- Use logger for debugging (not `println`)
- Wrap scripts in try/catch for error handling

### Map Shape
- Use for profile-to-profile transformations
- Prefer Map over Data Process for simple field mappings
- Use custom Groovy functions for complex logic

### Set Properties Shape
- Set HTTP headers before HTTP Client connector
- Use for passing metadata between steps
- Use dynamic values (functions, profile fields) where possible

---

**Related References**:
- `http-client.md` — HTTP Client connector configuration
- `datahub-connector.md` — DataHub connector operations
- `flow-service-server.md` — Flow Service Server listener setup
- `process-properties.md` — Process property patterns
- `error-handling.md` — Try/Catch and error patterns

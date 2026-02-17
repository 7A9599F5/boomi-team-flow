# Deployment Reference

Complete guide to deploying Boomi Integration processes using Atoms, Molecules, Clouds, packaged components, and Integration Packs.

---

## Runtime Types

### Atom

**Description**: Single-node runtime (standalone Java process).

**Hosting**:
- On-premise (customer-managed VM/server)
- Cloud VM (AWS EC2, Azure VM, GCP Compute Engine)

**Use Cases**:
- Development/testing
- Low-volume integrations (<1000 executions/day)
- Single-tenant deployments
- On-premise data access (behind firewall)

**Characteristics**:
- **Single Java process**: One JVM running all deployed processes
- **No high availability**: If Atom crashes, all processes stop
- **Local file access**: Can read/write local disk
- **Manual scaling**: Requires VM resize for more resources

**Configuration**:
```yaml
Atom:
  Name: Dev Atom
  Type: Local Atom
  OS: Linux / Windows
  Installation: On-premise VM or cloud VM
```

---

### Molecule

**Description**: Multi-node cluster (2+ Atoms working together).

**Hosting**: On-premise or cloud VMs (customer-managed).

**Use Cases**:
- Production deployments (high availability required)
- High-volume integrations (>1000 executions/day)
- Load balancing across nodes
- Zero-downtime deployments

**Characteristics**:
- **Clustered Atoms**: 2-16 nodes in cluster
- **High availability**: If one node fails, others continue
- **Shared storage**: NFS or SAN for shared file access
- **Load balancing**: Process executions distributed across nodes
- **Automatic failover**: Process listeners failover to healthy nodes

**Configuration**:
```yaml
Molecule:
  Name: Production Molecule
  Nodes: 4 (4 Atoms in cluster)
  Shared Storage: NFS mount at /mnt/boomi-shared
  Installation: On-premise or cloud VMs
```

---

### Cloud (Public Boomi Cloud)

**Description**: Boomi-hosted multi-tenant runtime.

**Hosting**: Boomi-managed infrastructure (AWS).

**Use Cases**:
- **Flow Service endpoints** (recommended for Flow integration)
- HTTP listener processes (no firewall config required)
- SaaS integrations (Salesforce, NetSuite, Workday, etc.)
- Production deployments (no infrastructure management)

**Characteristics**:
- **Multi-tenant**: Shared infrastructure across customers
- **Auto-scaling**: Boomi manages capacity
- **Forked execution**: Each process runs in separate JVM (high security)
- **No local file access**: Cannot read/write local disk
- **No firewall config**: All connections outbound (HTTPS)

**Configuration**:
```yaml
Cloud:
  Name: Public Boomi Cloud
  Region: US East, EU West, APAC
  Type: [Standard | High Security]
  Installation: None (Boomi-managed)
```

**Key Differences vs Atom/Molecule**:
- **No Disk Shape**: Cannot use Disk shape (file read/write)
- **Forked Execution**: Each process execution isolated (more secure)
- **High Security Policy**: Restricted Java APIs (no network sockets, no reflection)

---

### Comparison Table

| Feature | Atom | Molecule | Cloud |
|---------|------|----------|-------|
| **HA** | No | Yes | Yes (Boomi-managed) |
| **Scalability** | Manual (resize VM) | Manual (add nodes) | Auto (Boomi-managed) |
| **Deployment** | On-premise/cloud VM | On-premise/cloud VMs | Boomi-hosted |
| **File Access** | Yes | Yes (shared storage) | No |
| **Firewall Config** | Required (inbound) | Required (inbound) | Not required |
| **Flow Service** | Yes (requires firewall) | Yes (requires firewall) | Yes (no firewall) |
| **Cost** | VM + license | VMs + license | License only |
| **Maintenance** | Customer | Customer | Boomi |

---

## Packaged Components

### Purpose

**Packaged Component**: Versioned, deployable unit of integration component.

**Use Cases**:
- Deploy process to runtime environment
- Version control (track changes over time)
- Rollback to previous version
- Share components via Integration Packs

---

### Creation

**Steps**:
1. Navigate to component (e.g., a process)
2. Click **Create Packaged Component**
3. Enter version number (e.g., `1.0.0`, `1.2.3`)
4. Add deployment notes (changelog)
5. Mark as **shareable** (if integrating into Integration Pack)

**Versioning**:
- **Semantic Versioning**: `MAJOR.MINOR.PATCH` (recommended)
  - `MAJOR`: Breaking changes
  - `MINOR`: New features (backward-compatible)
  - `PATCH`: Bug fixes
- **Sequential**: `1`, `2`, `3`, ... (simple)

**Example**:
```yaml
Packaged Component:
  Component: PROMO - Process C - Execute Promotion
  Version: 1.2.3
  Notes: |
    - Fixed connection mapping validation logic
    - Added retry logic for transient API errors
  Shareable: true
```

**Immutability**: Once created, packaged component **cannot be modified** (create new version instead).

---

### Dependencies

**Automatic Dependency Resolution**:
- Boomi auto-includes all referenced components
- Example: Process references Map → Map auto-included in package

**Dependency Tree**:
```
Process: PROMO - Process C
  ↓ References
Map: PROMO - Map - Transform Response
  ↓ References
Profile: PROMO - Profile - ExecutePromotionResponse
```

**Packaged Component** includes all 3 components (Process + Map + Profile).

---

## Deployment

### Deployment Process

**Steps**:
1. Navigate to **Deploy** → **Deployments**
2. Click **New Deployment**
3. Select **Packaged Component**
4. Choose **Environment** (e.g., "Production", "Test")
5. Choose **Runtime** (Atom, Molecule, Cloud)
6. Click **Deploy**

**Deployment States**:
- **Pending**: Deployment queued
- **Deploying**: Deployment in progress
- **Deployed**: Successfully deployed and running
- **Failed**: Deployment failed (check logs)

---

### Environments

**Environment**: Logical grouping of runtime configurations.

**Examples**:
- **Development**: Dev Atom, dev database, dev API keys
- **Test**: Test Atom, test database, test API keys
- **Production**: Production Molecule/Cloud, prod database, prod API keys

**Configuration**:
```yaml
Environment:
  Name: Production
  Runtime: Public Boomi Cloud
  Connections:
    - Database: prod-db.example.com
    - HTTP Client: https://api.boomi.com (prod API keys)
    - DataHub: Production DataHub repository
```

**Environment Extensions**:
- Override connection parameters per environment
- Example: Dev environment uses dev database URL, Prod uses prod database URL

---

### Listener Processes

**Listener Process**: Process that starts with a listener shape (HTTP, Flow Service, Database polling).

**Deployment Behavior**:
- Listener auto-starts when deployed
- Binds to endpoint (HTTP, Flow Service, etc.)
- Waits for incoming requests

**Verification**:
1. Navigate to **Runtime Management** → **Listeners**
2. Verify listener status = **Running**
3. Note endpoint URL (e.g., `https://cloud-base-url/fs/PromotionService`)

**Example** (Flow Service listener):
```yaml
Listener Process:
  Name: PROMO - Process A0 - Get Dev Accounts
  Listener Type: Flow Service Server
  Operation: getDevAccounts
  Status: Running
  Endpoint: https://c01-useast.integrate.boomi.com/fs/PromotionService
```

---

## Integration Packs

### Purpose

**Integration Pack**: Group multiple packaged components into a single installable unit.

**Use Cases**:
- Deploy entire solution (all 11 processes + shared components)
- Share solution with other accounts
- Versioned releases (e.g., v1.0.0, v2.0.0)

---

### Types

#### SINGLE

**Description**: Contains one root component and its dependencies.

**Use Case**: Deploy a single process with all dependencies.

**Example**:
```yaml
Integration Pack:
  Type: SINGLE
  Root Component: PROMO - Process C - Execute Promotion (v1.2.3)
  Included Components:
    - PROMO - Process C (v1.2.3)
    - PROMO - Map - Transform Response (v1.0.0)
    - PROMO - Profile - ExecutePromotionRequest (v1.0.0)
    - PROMO - Profile - ExecutePromotionResponse (v1.0.0)
    ... (all dependencies)
```

#### MULTI

**Description**: Contains multiple root components.

**Use Case**: Deploy entire solution with multiple processes + shared components.

**Example**:
```yaml
Integration Pack:
  Type: MULTI
  Root Components:
    - PROMO - Process A0 (v1.0.0)
    - PROMO - Process A (v1.0.0)
    - PROMO - Process B (v1.0.0)
    - PROMO - Process C (v1.2.3)
    - PROMO - Process D (v1.0.0)
    ... (11 total processes)
  Shared Components:
    - PROMO - Flow Service (v1.0.0)
    - PROMO - Config (v1.0.0)
    ... (connections, profiles, etc.)
```

---

### Creation

**Steps**:
1. Navigate to **Deploy** → **Integration Packs**
2. Click **Create Integration Pack**
3. Select type (SINGLE or MULTI)
4. Add packaged components
5. Set version and description
6. Click **Release** (makes it available for deployment)

**Versioning**:
- Integration Pack has its own version (separate from component versions)
- Example: Integration Pack v2.0.0 contains Process v1.2.3

**Example**:
```yaml
Integration Pack:
  Name: Boomi Promotion System
  Type: MULTI
  Version: 2.0.0
  Description: |
    Full dev-to-prod promotion system with 11 integration processes,
    Flow Service, DataHub models, and Flow dashboard.
  Components: [11 processes + shared components]
```

---

### Deployment

**Steps**:
1. Navigate to **Deploy** → **Deployments**
2. Click **New Deployment**
3. Select **Integration Pack**
4. Choose **Environment** + **Runtime**
5. Click **Deploy**

**Behavior**:
- All components in pack are deployed together
- Deployment is **atomic** (all succeed or all fail)
- Listeners auto-start after deployment

---

## Project-Specific Deployment

### Phase 6: Deploy Flow Service (from BUILD-GUIDE.md)

**Components to Deploy**:
- **Flow Service Component**: `PROMO - Flow Service`
- **11 Listener Processes**: A0, A–G, E2, E3, J
- **Supporting Components**: Profiles, Maps, Process Properties, Groovy scripts

**Deployment Strategy**:

#### Option 1: Single Integration Pack (Recommended)

**Benefit**: Deploy entire solution at once (atomic, versioned).

**Steps**:
1. Create packaged components for all 11 processes
2. Create packaged component for Flow Service
3. Create MULTI Integration Pack with all 11 processes + Flow Service
4. Deploy to Public Boomi Cloud

**Example**:
```yaml
Integration Pack:
  Name: Boomi Promotion System
  Type: MULTI
  Version: 1.0.0
  Components:
    - PROMO - Flow Service (v1.0.0)
    - PROMO - Process A0 (v1.0.0)
    - PROMO - Process A (v1.0.0)
    ... (11 processes total)

Deployment:
  Environment: Production
  Runtime: Public Boomi Cloud (US East)
```

#### Option 2: Individual Packaged Components

**Benefit**: Granular control (deploy processes independently).

**Steps**:
1. Create packaged component for Flow Service → Deploy
2. Create packaged components for each process → Deploy individually

**Example**:
```yaml
Deployment 1:
  Packaged Component: PROMO - Flow Service (v1.0.0)
  Runtime: Public Boomi Cloud

Deployment 2:
  Packaged Component: PROMO - Process A0 (v1.0.0)
  Runtime: Public Boomi Cloud

... (11 deployments total)
```

---

### Verify Deployment

**Steps**:
1. Navigate to **Runtime Management** → **Listeners**
2. Verify all 11 Flow Service operations are **Running**:
   - `getDevAccounts`
   - `listDevPackages`
   - `resolveDependencies`
   - `executePromotion`
   - `packageAndDeploy`
   - `queryStatus`
   - `queryPeerReviewQueue`
   - `submitPeerReview`
   - `manageMappings`
   - `generateComponentDiff`
   - `listIntegrationPacks`

**Test**:
```bash
# Test getDevAccounts endpoint
curl -X POST https://{cloud-base-url}/fs/PromotionService/getDevAccounts \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected response:
{
  "success": true,
  "devAccounts": [
    {"accountId": "sub-account-123", "accountName": "Dev Team A"}
  ],
  "errorCode": "",
  "errorMessage": ""
}
```

---

## Rollback

### Rollback to Previous Version

**Scenario**: Deployed v2.0.0, found critical bug, need to rollback to v1.0.0.

**Steps**:
1. Navigate to **Deploy** → **Deployments**
2. Select environment + runtime
3. Click **Deploy** → Select previous packaged component version (v1.0.0)
4. Click **Deploy**

**Behavior**:
- Previous version is deployed (overwrites current version)
- Listener processes restart with previous version
- No data loss (DataHub, databases unaffected)

---

## Best Practices

### Packaged Components

**Semantic Versioning**:
- Use `MAJOR.MINOR.PATCH` format
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

**Deployment Notes**:
- Include changelog in deployment notes
- List breaking changes, new features, bug fixes
- Reference ticket/issue numbers

**Shareable Flag**:
- Mark as shareable if integrating into Integration Pack
- Leave unchecked for internal/test components

---

### Integration Packs

**Use MULTI Packs for Solutions**:
- Bundle all related processes + shared components
- Deploy entire solution at once (atomic)
- Version the pack (track releases)

**Use SINGLE Packs for Individual Processes**:
- Deploy single process with dependencies
- Useful for hotfixes (deploy only changed process)

---

### Deployment

**Deploy to Cloud for Flow Service**:
- No firewall configuration required
- High availability (Boomi-managed)
- Auto-scaling (handles traffic spikes)

**Deploy to Molecule for On-Premise**:
- High availability (multi-node cluster)
- On-premise data access (databases behind firewall)
- Load balancing (distribute executions)

**Use Environment Extensions**:
- Override connection parameters per environment
- Avoid hardcoding URLs, credentials in components

---

### Listeners

**Verify Listener Status**:
- Always check **Runtime Management** → **Listeners** after deployment
- Verify status = **Running**
- Test endpoints (curl, Postman, Flow)

**Monitor Listener Logs**:
- Navigate to **Process Reporting** → **Execution Logs**
- Filter by listener process name
- Review logs for errors, warnings

---

## Troubleshooting

### Common Deployment Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Deployment Pending** | Runtime offline or busy | Wait for runtime to become available |
| **Deployment Failed** | Missing dependencies | Check packaged component dependencies |
| **Listener Not Running** | Process error on startup | Check execution logs for error details |
| **Endpoint 404** | Listener not deployed | Verify deployment status, check runtime |
| **Timeout on Deploy** | Large package or slow runtime | Deploy to Cloud (faster) or reduce package size |

---

### Debugging

**Check Deployment Logs**:
1. Navigate to **Deploy** → **Deployments**
2. Click on deployment
3. Review deployment log (shows progress, errors)

**Check Listener Logs**:
1. Navigate to **Runtime Management** → **Listeners**
2. Click on listener
3. Click **View Logs**
4. Review startup errors

**Test Endpoint**:
```bash
# Test Flow Service endpoint
curl -X POST https://{cloud-base-url}/fs/PromotionService/{operation} \
  -H "Content-Type: application/json" \
  -d '{...}'

# Expected: Valid JSON response (success or error)
```

---

## Related References

- `flow-service-server.md` — Flow Service deployment patterns
- `process-properties.md` — Environment-specific property configuration
- `error-handling.md` — Error handling in deployed processes

# Connection Folder Patterns (#Connections)

## What It Is

`#Connections` is a **shared folder** in the parent account containing connection components that are reused across multiple promoted processes.

**The `#` prefix** signals:
- Shared resource folder
- Do not move or rename without coordination
- Referenced by many components
- Alphabetically sorts to the top of folder listings

---

## Why Connections Are NOT Promoted

1. **Sensitive credentials** — passwords, API keys differ across environments
2. **Environment-specific config** — dev hostnames/URLs vs prod
3. **Admin control** — admins decide which prod connection each dev connection maps to
4. **One-to-many mapping** — one prod connection can be mapped from multiple dev accounts

---

## Folder Naming Convention

```
#Connections/
  SAP_ERP_Connection
  Salesforce_Connection
  Database_Connection
  SFTP_FileServer_Connection
```

---

## Connection Sharing Across Components

**How Components Reference Connections:**
- Process shapes have a "Connection" dropdown that lists available connections
- When you select a connection, the process XML embeds the connection's `componentId`
- Example: `<connectionId>abc-123-def-456</connectionId>` in process XML

**Cross-Account Sharing (Parent-Child):**
- Child accounts can **reference** parent account connections
- This is Boomi's built-in inheritance model
- Dev processes reference dev-local connections (which are mapped to parent `#Connections`)

---

## Connection Mapping Seeding Workflow

**Admin Workflow:**
1. Create connections in parent account under `#Connections` folder
2. For each dev account, identify the connection IDs that dev processes reference
3. Use Process F (manageMappings) with `action: "update"` to seed ComponentMapping records (DataHub upsert creates or updates):
   ```json
   {
     "devComponentId": "dev-conn-123",
     "devAccountId": "dev-account-001",
     "prodComponentId": "prod-conn-#connections-abc",
     "componentName": "SAP ERP Connection",
     "componentType": "connection",
     "mappingSource": "ADMIN_SEEDING"
   }
   ```
4. Repeat for all dev accounts and connections

**Why Seed Instead of Auto-Create:**
- Connections contain sensitive credentials (passwords, API keys)
- Different environments (dev, prod) require different connection config
- Admins control which prod connection each dev connection maps to
- One prod connection can be mapped from multiple dev accounts

---

## Connection Filtering in Process C

**After Dependency Resolution:**
1. Process B returns full dependency tree (including connections)
2. Process C loads ALL connection mappings for the dev account (batch query to DataHub)
3. Process C validates that every connection in the tree has a mapping
4. Process C filters connections OUT of the promotion list
5. Connections are NOT promoted — only non-connection components are created/updated

**Tracking:**
- `connectionsSkipped` counter in executePromotion response
- `sharedConnections` list in Flow values (displayed as pre-mapped in UI)

---

## Validation: Missing Connection Mappings

```groovy
def missingMappings = []

connections.each { conn ->
    String devId = conn.devComponentId
    if (!connCache.containsKey(devId)) {
        missingMappings << [
            devComponentId: devId,
            componentName: conn.name,
            componentType: conn.type
        ]
    }
}

if (missingMappings.size() > 0) {
    throw new Error("MISSING_CONNECTION_MAPPINGS: ${missingMappings}")
}
```

**Result:** If a dev process references a connection without a mapping, promotion fails with `MISSING_CONNECTION_MAPPINGS` error.

---

## Pitfalls

### Forgetting to Seed Connection Mappings

**Problem:** Dev process references a connection, but admin hasn't seeded the mapping.

**Error:** `MISSING_CONNECTION_MAPPINGS` with detailed list of unmapped connections.

**Solution:** Admin must seed the missing mappings before retry.

---

### Mapping Multiple Dev Connections to Same Prod Connection

**Valid and common pattern:**
- Dev accounts may have different connection names but map to the same prod `#Connections` entry
- Example: DevTeamA's "My SAP" → `#Connections/SAP_ERP`, DevTeamB's "SAP Production" → same `#Connections/SAP_ERP`

---

### Connection componentType String

**Correct:**
```json
{
  "componentType": "connection"  // Lowercase, no namespace
}
```

**Incorrect:**
```json
{
  "componentType": "bns:Connection"  // Wrong
}
```

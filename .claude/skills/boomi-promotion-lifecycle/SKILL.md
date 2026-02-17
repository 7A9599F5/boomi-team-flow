---
name: boomi-promotion-lifecycle
description: |
  Cross-cutting concepts for the Boomi dev-to-prod promotion engine. Use when
  working on component branching/merging, environment config stripping, component
  reference rewriting, Integration Pack lifecycle, versioning, account hierarchy,
  or connection folder patterns.
globs:
  - "integration/**"
  - "docs/**"
  - "flow/**"
  - "datahub/**"
---

# Boomi Promotion Lifecycle Reference

## Overview

This skill covers cross-cutting concepts specific to the Boomi dev-to-prod promotion workflow — concepts that span multiple domains (Platform API, Integration, DataHub, Flow) but are unique to this system.

**Core promotion flow:** Branch → Promote → Strip → Rewrite → Merge → Package → Deploy

---

## End-to-End Promotion Flow Summary

### Phase 1: List and Select (Process A)
- Query dev account's PackagedComponents using `overrideAccount`
- Return list to Flow dashboard for user selection

### Phase 2: Resolve Dependencies (Process B)
- Recursive BFS traversal of ComponentReference API
- Build full dependency tree (process → maps → operations → connections → profiles)
- Sort by type hierarchy (profiles first, root process last)

### Phase 3: Execute Promotion (Process C)
1. **Create branch** — `promo-{promotionId}` in parent account
2. **Poll ready state** — wait for `ready: true`
3. **For each component in dependency order:**
   - Fetch dev component XML (with `overrideAccount`)
   - Strip environment config (passwords, hosts, URLs)
   - Rewrite component references (dev IDs → prod IDs using mapping cache)
   - Create/update prod component on branch using tilde syntax (`{id}~{branchId}`)
4. **Record PromotionLog** — status `PENDING_PEER_REVIEW`

### Phase 4: Peer Review (Processes E2, E3, G)
- **E2** — queryPeerReviewQueue (exclude own submissions)
- **G** — generateComponentDiff (fetch branch vs main XML, normalize, return for diff viewer)
- **E3** — submitPeerReview (approve/reject, self-review prevention)

### Phase 5: Admin Approval (Process E)
- **E** — queryStatus (filter `reviewStage: PENDING_ADMIN_APPROVAL`)
- Admin approves/denies via Flow dashboard

### Phase 6: Package and Deploy (Process D)
1. **Merge branch → main** — OVERRIDE strategy, source wins
2. **Create PackagedComponent** — `shareable: true`, user-specified version
3. **Create/reuse Integration Pack** — `installationType: MULTI`
4. **Add package to pack** — link PackagedComponent to IntegrationPack
5. **Release pack** — create snapshot with version
6. **Deploy to environments** — one deployment per target environment
7. **Delete branch** — cleanup (critical for 20-branch limit)

---

## Branching Lifecycle Quick Reference

### Branch States
1. **CREATE** — `POST /Branch` → returns `branchId` with `ready: false`
2. **POLL** — `GET /Branch/{branchId}` until `ready: true` (typically 1-5 seconds)
3. **PROMOTE** — Write components via tilde syntax (`Component/{id}~{branchId}`)
4. **MERGE** — `POST /MergeRequest` + `POST /MergeRequest/execute/{id}`
5. **DELETE** — `DELETE /Branch/{branchId}` (mandatory cleanup)

### Tilde Syntax for Branch Operations

```http
POST /Component/{componentId}~{branchId}
```

**Effect:** Creates/updates component on the specified branch instead of main.

**Example:**
```http
POST /Component/abc-123~branch-456
Body: <Component XML>
```

Creates component `abc-123` on branch `branch-456`.

### 20-Branch Hard Limit

**Constraint:** Boomi enforces a maximum of 20 branches per account.

**Management Strategy:**
1. Check branch count before creation (query branches, count results)
2. Fail promotion with `BRANCH_LIMIT_REACHED` error if count >= 15 (leave buffer)
3. Delete branch on ALL terminal paths:
   - Peer approval → (continue to admin review)
   - Peer rejection → delete immediately
   - Admin approval → merge → delete
   - Admin denial → delete immediately
   - Process C failure → delete immediately

**Tracking:** `branchId` field in PromotionLog. Set to `null` after deletion.

---

## Environment Config Stripping

### What Gets Stripped

| Element | Why | Example |
|---------|-----|---------|
| `<password>` | Credentials are environment-specific | `secret123` |
| `<host>` | Server hostnames differ across environments | `dev-server.example.com` |
| `<url>` | Endpoint URLs differ across environments | `https://dev-api.example.com` |
| `<port>` | Port numbers may differ | `8080` |
| `<EncryptedValue>` | Encrypted with account-specific keys | (base64-encoded encrypted string) |

### Stripping Pattern (Groovy)

```groovy
def root = new XmlSlurper(false, false).parseText(xmlContent)

['password', 'host', 'url', 'port', 'EncryptedValue'].each { elemName ->
    def elements = root.depthFirst().findAll { it.name() == elemName }
    elements.each { it.replaceBody('') }  // Empty content, preserve element
}

String strippedXml = XmlUtil.serialize(root)
```

**Why preserve the element?** Deleting elements would break Boomi's XML schema validation. Empty elements preserve schema compliance.

**Post-Promotion:** Admins configure production values via Boomi UI.

### Pitfalls

- **Missing a field type** — sensitive data leaks to prod
- **EncryptedValue cannot be copied** — encrypted with source account's key, target account cannot decrypt
- **Element name is case-sensitive** — `it.name() == 'password'` matches `<password>`, not `<Password>`

---

## Reference Rewriting: The Mapping Cache Pattern

### Problem

Component XML embeds references to other components as UUIDs:

```xml
<connectionId>dev-conn-123</connectionId>
<operationId>dev-op-456</operationId>
<mapId>dev-map-789</mapId>
```

After promotion, prod components must reference prod component IDs, not dev IDs.

### Solution: Mapping Cache

**Pre-Load Mapping Cache:**
1. Process B resolves full dependency tree
2. Process C batch queries DataHub for ALL component mappings for this dev account
3. Process C validates all dependencies have mappings (except connections, which are pre-seeded)
4. Process C loads mappings into an in-memory cache (`componentMappingCache` DPP, stored as JSON)

**Cache Format (JSON):**
```json
{
  "dev-comp-123": "prod-comp-abc",
  "dev-comp-456": "prod-comp-def",
  "dev-conn-789": "prod-conn-#connections-xyz"
}
```

**Rewriting Pattern (Groovy):**
```groovy
mappingCache.each { devId, prodId ->
    if (xmlContent.contains(devId)) {
        xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
    }
}
```

**Connection References:** Even though connections are NOT promoted, their references MUST be rewritten. Dev processes reference dev connection IDs. After rewriting, prod processes reference prod `#Connections` IDs.

---

## Account Hierarchy: Parent/Child

### Structure

```
Primary Account (Parent) — accountId: primary-123
  ├── Dev Sub-Account A (Child) — accountId: dev-team-a-456
  ├── Dev Sub-Account B (Child) — accountId: dev-team-b-789
  └── Dev Sub-Account C (Child) — accountId: dev-team-c-012
```

### Access Rules

- **Parent can read child data** — via Platform API with `overrideAccount` parameter
- **Child cannot read parent data** — except inherited resources (connections in `#Connections`)
- **Child cannot read sibling data** — Dev Team A cannot access Dev Team B's components

### overrideAccount Query Parameter

```http
GET /partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}
```

**Effect:** Fetches component from `devAccountId` instead of `primaryAccountId`.

**Used In:**
- Process A: list dev packages
- Process B: resolve dev dependencies
- Process C: read dev component XML

---

## Connection Folder Convention (#Connections)

### What It Is

`#Connections` is a **shared folder** in the parent account containing connection components that are reused across multiple promoted processes.

### Why Connections Are NOT Promoted

1. **Sensitive credentials** — passwords, API keys differ across environments
2. **Environment-specific config** — dev hostnames/URLs vs prod
3. **Admin control** — admins decide which prod connection each dev connection maps to
4. **One-to-many mapping** — one prod connection can be mapped from multiple dev accounts

### Connection Mapping Seeding Workflow

**Admin Workflow:**
1. Create connections in parent account under `#Connections` folder
2. For each dev account, identify the connection IDs that dev processes reference
3. Use Process F (manageMappings) to seed ComponentMapping records:
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

### Connection Filtering in Process C

**After Dependency Resolution:**
1. Process B returns full dependency tree (including connections)
2. Process C loads ALL connection mappings for the dev account
3. Process C validates that every connection in the tree has a mapping
4. Process C filters connections OUT of the promotion list
5. Connections are NOT promoted — only non-connection components

**Tracking:**
- `connectionsSkipped` counter in executePromotion response
- `sharedConnections` list in Flow values (displayed in UI)

---

## Deep Reference Files

For detailed documentation:
- **Branching/Merging:** See `reference/branching-merging.md` for full branch→modify→merge lifecycle, tilde syntax, 20-branch limit, merge strategies
- **Env Config Stripping:** See `reference/env-config-stripping.md` for what gets stripped, regex patterns, pitfalls
- **Reference Rewriting:** See `reference/reference-rewriting.md` for component ID replacement, mapping cache, XML traversal
- **Integration Pack Lifecycle:** See `reference/ipack-lifecycle.md` for IntegrationPack create→version→deploy flow
- **Versioning:** See `reference/versioning.md` for PackagedComponent versioning mechanics, incrementing
- **Account Hierarchy:** See `reference/account-hierarchy.md` for parent/child accounts, Partner API crossover
- **Connection Patterns:** See `reference/connection-patterns.md` for #Connections folder, admin-seeded mappings, shared connections

**End-to-End Flow Example:** See `examples/promotion-workflow.md` for complete promotion walkthrough.

---

## Quick Tips

1. **Always poll branch ready state** — don't write components until `ready: true`
2. **Always delete branches** — on ALL terminal paths (approve, reject, deny, failure)
3. **Check branch count before creation** — enforce soft limit (18) to avoid hitting hard limit (20)
4. **Validate connection mappings first** — fail fast if mappings are missing
5. **Use OVERRIDE merge strategy** — `priorityBranch: sourceBranchId` ensures predictable merges
6. **shareable: true is REQUIRED** — PackagedComponents must have `shareable: true` to include in Integration Packs
7. **Folder path mirroring** — dev `/DevTeamA/Orders/` → prod `/Promoted/DevTeamA/Orders/`
8. **Connection references are rewritten but NOT promoted** — mapping cache includes connections

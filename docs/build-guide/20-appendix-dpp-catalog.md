## Appendix B: Dynamic Process Properties (DPP) Catalog

### Global DPPs

These properties are used across multiple integration processes.

| DPP Name | Type | Process(es) | Read/Write | Initial Value | Description |
|----------|------|-------------|------------|---------------|-------------|
| `primaryAccountId` | String | All (A0, A, B, C, D, E, F) | Read | (set via Flow Service component configuration) | Primary Boomi account ID used in all Partner API URLs |
| `devAccountId` | String | A0, A, B, C, D | Read | (from request JSON) | Dev sub-account ID; used for `overrideAccount` parameter |
| `currentComponentId` | String | B, C | Read/Write | (from loop iteration) | Component ID being processed in the current loop iteration |
| `rootComponentId` | String | B, C | Read | (from request JSON) | Root process component ID that initiated the dependency traversal |

### Process B DPPs (Resolve Dependencies)

| DPP Name | Type | Read/Write | Initial Value | Description |
|----------|------|------------|---------------|-------------|
| `visitedComponentIds` | String (JSON array) | Read/Write | `[]` | JSON array of component IDs already visited during BFS traversal |
| `componentQueue` | String (JSON array) | Read/Write | `[]` | BFS queue of component IDs remaining to visit |
| `alreadyVisited` | String | Write | `"false"` | Flag set by `build-visited-set.groovy`; `"true"` if current component was already in the visited set |
| `visitedCount` | String | Write | `"0"` | Count of components visited so far; used for progress tracking and loop diagnostics |
| `queueCount` | String | Write | `"0"` | Count of components remaining in the queue; reaches `"0"` when traversal is complete |

### Process C DPPs (Execute Promotion)

| DPP Name | Type | Read/Write | Initial Value | Description |
|----------|------|------------|---------------|-------------|
| `componentMappingCache` | String (JSON object) | Read/Write | `{}` | In-memory dev-to-prod ID mapping cache; keys are dev component IDs, values are prod component IDs |
| `configStripped` | String | Write | `"false"` | Flag set by `strip-env-config.groovy`; `"true"` if any environment elements were stripped |
| `strippedElements` | String | Write | `""` | Comma-separated list of element names stripped (e.g., `password,host,EncryptedValue`) |
| `referencesRewritten` | String | Write | `"0"` | Count of component references rewritten by `rewrite-references.groovy` |
| `prodComponentId` | String | Read/Write | (from DataHub query) | Prod component ID for the current component; empty if component is new |
| `promotionId` | String | Read/Write | (UUID generated at start) | Unique ID for this promotion run; written to PromotionLog |
| `connectionMappingCache` | String (JSON object) | Read/Write | `{}` | Connection mappings batch-queried from DataHub; keys are dev connection IDs, values are prod connection IDs |
| `missingConnectionMappings` | String (JSON array) | Write | `[]` | JSON array of objects for connections without mappings; each has devComponentId, name, type, devAccountId |
| `missingConnectionCount` | String | Write | `"0"` | Count of connections without mappings |
| `connectionMappingsValid` | String | Write | `"true"` | `"true"` if all connections have mappings, `"false"` otherwise |
| `currentFolderFullPath` | String | Read/Write | (from component) | Dev account folder path for current component; used to construct `/Promoted{currentFolderFullPath}` target path |

### Groovy Script to DPP Cross-Reference

| Script | File | Process | DPPs Read | DPPs Written |
|--------|------|---------|-----------|--------------|
| Build Visited Set | `integration/scripts/build-visited-set.groovy` | B (Resolve Dependencies) | `visitedComponentIds`, `componentQueue`, `currentComponentId` | `visitedComponentIds`, `componentQueue`, `alreadyVisited`, `visitedCount`, `queueCount` |
| Sort by Dependency | `integration/scripts/sort-by-dependency.groovy` | C (Execute Promotion) | `rootComponentId` | (none -- sorts document in-place) |
| Strip Env Config | `integration/scripts/strip-env-config.groovy` | C (Execute Promotion) | (none -- reads XML from document stream) | `configStripped`, `strippedElements` |
| Rewrite References | `integration/scripts/rewrite-references.groovy` | C (Execute Promotion) | `componentMappingCache` | `referencesRewritten` |
| Validate Connection Mappings | `integration/scripts/validate-connection-mappings.groovy` | C (Execute Promotion) | `connectionMappingCache`, `componentMappingCache`, `devAccountId` | `missingConnectionMappings`, `missingConnectionCount`, `connectionMappingsValid`, `componentMappingCache` |

### Type Priority Order (sort-by-dependency.groovy)

Components are sorted by type for bottom-up promotion. Lower priority number means promoted first.

| Priority | Type | Notes |
|----------|------|-------|
| 1 | `profile` | Promoted first -- no dependencies on other promoted components |
| 2 | `connection` | May reference profiles |
| 3 | `operation` | References connections and profiles |
| 4 | `map` | References profiles and operations |
| 5 | `process` (sub-process) | References all of the above |
| 6 | `process` (root) | Promoted last -- depends on everything; identified by matching `rootComponentId` |

---

---
Prev: [Appendix A: Naming & Inventory](19-appendix-naming-and-inventory.md) | Next: [Appendix C: Platform API Reference](21-appendix-platform-api-reference.md) | [Back to Index](index.md)

## Appendix B: Dynamic Process Properties (DPP) Catalog

This catalog documents every DPP used across all 13 integration processes. Use it for troubleshooting, debugging, and understanding data flow between shapes.

### Global DPPs

These properties are available to all processes via Flow Service component configuration.

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `primaryAccountId` | String | Flow Service config | All processes (A0, A, B, C, D, E, E2, E3, E4, E5, F, G, J) | N/A | Primary Boomi account ID; used in all Partner API URL parameters |

---

### Process A0: Get Dev Accounts

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `userSsoGroups` | String (JSON array) | Set Properties (step 2) | Data Process (step 3) | false | User's Azure AD/Entra SSO group names as JSON array string |

---

### Process A: List Dev Packages

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `devAccountId` | String | Set Properties (step 2) | HTTP Client Send (steps 3, 5, 6) | false | Dev sub-account to query for packages |
| `queryToken` | String | Data Process (step 5) | HTTP Client Send (step 5) | false | Pagination token for queryMore calls |

---

### Process B: Resolve Dependencies

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `rootComponentId` | String | Set Properties (step 2) | `sort-by-dependency.groovy` (step 11) | false | Root process component ID that initiated traversal |
| `devAccountId` | String | Set Properties (step 2) | HTTP Client Send (steps 6, 9), DataHub Query (step 10) | false | Dev sub-account for overrideAccount parameter |
| `visitedComponentIds` | String (JSON array) | Set Properties (step 3), `build-visited-set.groovy` (step 7) | `build-visited-set.groovy` (step 7) | false | JSON array of component IDs already visited during BFS |
| `componentQueue` | String (JSON array) | Set Properties (step 3), Pop Next (step 5), `build-visited-set.groovy` (step 7) | Pop Next (step 5), `build-visited-set.groovy` (step 7), Decision (step 4) | false | BFS queue of component IDs remaining to visit |
| `visitedCount` | String | `build-visited-set.groovy` (step 7) | Map (step 12) | false | Count of components visited; used for totalComponents in response |
| `queueCount` | String | Pop Next (step 5), `build-visited-set.groovy` (step 7) | Decision (step 4) | false | Count of queue items remaining; loop exits when `"0"` |
| `currentComponentId` | String | Pop Next (step 5) | HTTP Client Send (steps 6, 9), `build-visited-set.groovy` (step 7), DataHub Query (step 10) | false | Component ID being processed in the current BFS iteration |
| `alreadyVisited` | String | `build-visited-set.groovy` (step 7) | Decision (step 8) | false | `"true"` if current component was already in visited set |

---

### Process C: Execute Promotion

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `devAccountId` | String | Set Properties (step 2) | HTTP Client Send (step 10), DataHub Query (steps 5.5, 14), `validate-connection-mappings.groovy` | false | Source dev sub-account |
| `initiatedBy` | String | Set Properties (step 2) | DataHub Update (steps 4, 20, 21) | false | Email of user initiating promotion |
| `rootComponentId` | String | Set Properties (step 2) | `sort-by-dependency.groovy` (step 5) | false | Root process component ID for sort priority assignment |
| `promotionId` | String | Groovy script (step 3) | DataHub Update (steps 4, 21), Map (step 22) | false | UUID uniquely identifying this promotion run |
| `activeBranchCount` | String | HTTP Client Send (step 3.5) | Decision (step 3.6) | false | Current number of active branches; checked against limit of 15 |
| `branchId` | String | HTTP Client Send (step 3.7) | HTTP Client Send (steps 15a.2, 15b.2), Map (step 22), DataHub Update (step 4) | false | Promotion branch ID for tilde syntax writes |
| `branchName` | String | Set Properties (step 3.7) | Map (step 22), DataHub Update (step 4) | false | Promotion branch name (e.g., `"promo-{promotionId}"`) |
| `componentMappingCache` | String (JSON object) | Init as `{}`, `validate-connection-mappings.groovy` (step 5.6), Update Cache (step 16) | Check Cache (step 12), `rewrite-references.groovy` (step 15a.1/15b.1), Update Cache (step 16) | false | Accumulating dev-to-prod ID mapping; keys = dev IDs, values = prod IDs |
| `connectionMappingCache` | String (JSON object) | DataHub Query (step 5.5) | `validate-connection-mappings.groovy` (step 5.6) | false | Connection mappings batch-queried from DataHub |
| `missingConnectionMappings` | String (JSON array) | `validate-connection-mappings.groovy` (step 5.6) | Error Response (step 5.8), Map (step 22) | false | JSON array of connection mapping objects missing from DataHub |
| `missingConnectionCount` | String | `validate-connection-mappings.groovy` (step 5.6) | (diagnostics) | false | Count of missing connection mappings |
| `connectionMappingsValid` | String | `validate-connection-mappings.groovy` (step 5.6) | Decision (step 5.7) | false | `"true"` if all connections have mappings; `"false"` otherwise |
| `currentComponentId` | String | Set Properties (step 9) | HTTP Client Send (step 10), Check Cache (step 12), DataHub Query (step 14), Update Cache (step 16) | false | Dev component ID being processed in current loop iteration |
| `currentComponentName` | String | Set Properties (step 9) | Accumulate Result (step 17) | false | Name of current component |
| `currentComponentType` | String | Set Properties (step 9) | (diagnostics) | false | Type of current component |
| `currentFolderFullPath` | String | Set Properties (step 9) | HTTP Client Send (steps 15a.2, 15b.2) | false | Dev folder path; used to construct `/Promoted{path}` target |
| `prodComponentId` | String | Check Cache (step 12), DataHub Query (step 14), HTTP Client response (step 15b.2) | HTTP Client Send (step 15a.2), Update Cache (step 16), Accumulate Result (step 17) | false | Prod component ID for current component; empty if new |
| `mappingExists` | String | Check Cache (step 12), DataHub Query (step 14) | Decision (steps 13, 15) | false | `"true"` if a dev-to-prod mapping exists for current component |
| `configStripped` | String | `strip-env-config.groovy` (step 11) | Accumulate Result (step 17) | false | `"true"` if any env-specific elements were stripped from XML |
| `strippedElements` | String | `strip-env-config.groovy` (step 11) | (diagnostics) | false | Comma-separated list of stripped element names |
| `referencesRewritten` | String | `rewrite-references.groovy` (step 15a.1/15b.1) | (diagnostics) | false | Count of component references rewritten in XML |

---

### Process D: Package and Deploy

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `prodComponentId` | String | Set Properties (step 2) | HTTP Client Send (step 3) | false | Root process component ID in primary account |
| `prodAccountId` | String | Set Properties (step 2) | HTTP Client Send (various) | false | Primary account ID (usually same as `primaryAccountId`) |
| `branchId` | String | Set Properties (step 2) | HTTP Client Send (steps 2.5, 8.6), Map (step 9) | false | Promotion branch ID from Process C; merged and optionally deleted |
| `promotionId` | String | Set Properties (step 2) | DataHub Update (PromotionLog) | false | Promotion run ID for PromotionLog updates |
| `packageVersion` | String | Set Properties (step 2) | HTTP Client Send (steps 3, 7) | false | Version label for the PackagedComponent |
| `createNewPack` | String | Set Properties (step 2) | Decision (step 4) | false | `"true"` to create new Integration Pack; `"false"` to use existing |
| `integrationPackId` | String | Set Properties (step 2) or HTTP response (step 5) | HTTP Client Send (steps 5, 6, 7), Map (step 9) | false | Integration Pack ID (existing or newly created) |
| `newPackName` | String | Set Properties (step 2) | HTTP Client Send (step 5), Map (step 9) | false | Name for new Integration Pack |
| `newPackDescription` | String | Set Properties (step 2) | HTTP Client Send (step 5) | false | Description for new Integration Pack |
| `deploymentTarget` | String | Set Properties (step 2) | Decision (step 2.1), Decision (step 8.5), Map (step 9) | false | `"TEST"` or `"PRODUCTION"` -- determines deployment mode |
| `isHotfix` | String | Set Properties (step 2) | Decision (step 2.1), Map (step 9), DataHub Update | false | `"true"` / `"false"` -- flags emergency production bypass |
| `hotfixJustification` | String | Set Properties (step 2) | DataHub Update (PromotionLog) | false | Justification text for hotfix (up to 1000 chars) |
| `testPromotionId` | String | Set Properties (step 2) | Decision (step 2.1), DataHub Update (PromotionLog) | false | Links production deployment to preceding test deployment |
| `testIntegrationPackId` | String | Set Properties (step 2) | DataHub Update (PromotionLog) | false | Test Integration Pack ID from test deployment |
| `testIntegrationPackName` | String | Set Properties (step 2) | DataHub Update (PromotionLog) | false | Test Integration Pack name from test deployment |
| `mergeRequestId` | String | HTTP Client response (step 2.5) | HTTP Client Send (steps 2.6, polling) | false | Merge request ID for execute and status polling |
| `packagedComponentId` | String | HTTP Client response (step 3) | HTTP Client Send (steps 5, 6), Map (step 9) | false | Created PackagedComponent ID |

---

### Process E: Query Status

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `promotionId` | String | Set Properties (step 2) | DataHub Query filter (step 3) | false | Optional filter: specific promotion ID |
| `filterDevAccountId` | String | Set Properties (step 2) | DataHub Query filter (step 3) | false | Optional filter: dev account ID |
| `filterStatus` | String | Set Properties (step 2) | DataHub Query filter (step 3) | false | Optional filter: promotion status |
| `queryLimit` | String | Set Properties (step 2) | DataHub Query limit (step 3) | false | Maximum records to return (default 50) |

---

### Process E2: Query Peer Review Queue

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `requesterEmail` | String | Set Properties (step 2) | Data Process -- self-review filter (step 4) | false | Authenticated user's email; used to exclude own submissions via case-insensitive comparison |

---

### Process E3: Submit Peer Review

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `promotionId` | String | Set Properties (step 2) | DataHub Query (step 3), DataHub Update (step 6), Map (step 7) | false | Target promotion to review |
| `decision` | String | Set Properties (step 2) | DataHub Update (step 6), Map (step 7) | false | `"APPROVED"` or `"REJECTED"` |
| `reviewerEmail` | String | Set Properties (step 2) | Self-review check (step 4), DataHub Update (step 6) | false | Peer reviewer's email address |
| `reviewerName` | String | Set Properties (step 2) | DataHub Update (step 6) | false | Peer reviewer's display name |
| `comments` | String | Set Properties (step 2) | DataHub Update (step 6) | false | Reviewer comments (up to 500 chars) |
| `initiatedBy` | String | DataHub Query (step 3) | Self-review check (step 4) | false | Original submitter's email; compared case-insensitively with `reviewerEmail` |
| `currentPeerReviewStatus` | String | DataHub Query (step 3) | Decision -- already reviewed (step 5) | false | Current `peerReviewStatus`; must be `PENDING_PEER_REVIEW` to proceed |
| `isSelfReview` | String | Data Process (step 4) | Decision (step 4) | false | `"true"` if reviewer matches submitter (case-insensitive) |

---

### Process E4: Query Test Deployments

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `filterDevAccountId` | String | Set Properties (step 2) | DataHub Query filter (step 3) | false | Optional filter: dev account ID |
| `filterInitiatedBy` | String | Set Properties (step 2) | DataHub Query filter (step 3) | false | Optional filter: submitter email |

---

### Process E5: Withdraw Promotion

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `promotionId` | String | Set Properties (step 2) | DataHub Query (step 3), DataHub Update (step 7), Map (step 8) | false | Target promotion to withdraw |
| `initiatorEmail` | String | Set Properties (step 2) | Ownership Validation (step 5) | false | Requester's email |
| `reason` | String | Set Properties (step 2) | DataHub Update (step 7) | false | Optional withdrawal reason |
| `initiatedBy` | String | DataHub Query (step 3) | Ownership Validation (step 5) | false | Original submitter email |
| `currentStatus` | String | DataHub Query (step 3) | Status Validation (step 4) | false | Current promotion status |
| `branchId` | String | DataHub Query (step 3) | HTTP Client -- DELETE Branch (step 6) | false | Branch ID for deletion |
| `previousStatus` | String | DataHub Query (step 3) | Map (step 8) | false | Status before withdrawal |
| `isWithdrawable` | String | Status Validation (step 4) | Decision (step 4) | false | Whether status allows withdrawal |
| `isOwner` | String | Ownership Validation (step 5) | Decision (step 5) | false | Whether requester is initiator |
| `branchDeleted` | String | HTTP Client (step 6) | Map (step 8) | false | Whether branch was successfully deleted |
| `responseMessage` | String | Map (step 8) | Return Documents (step 9) | false | Human-readable confirmation |

---

### Process F: Manage Mappings

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `operation` | String | Set Properties (step 2) | Decision (step 3), Map (steps 5, 8) | false | CRUD operation: `"list"`, `"create"`, or `"update"` |
| `filterDevAccountId` | String | Set Properties (step 2) | DataHub Query filter (step 4) | false | Optional filter: dev account ID |
| `filterComponentType` | String | Set Properties (step 2) | DataHub Query filter (step 4) | false | Optional filter: component type |
| `filterComponentName` | String | Set Properties (step 2) | DataHub Query filter (step 4) | false | Optional filter: component name |

---

### Process G: Generate Component Diff

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `branchId` | String | Set Properties (step 1) | HTTP Client Send (step 2) | false | Promotion branch ID for tilde syntax URL |
| `prodComponentId` | String | Set Properties (step 1) | HTTP Client Send (steps 2, 5) | false | Component ID to diff |
| `componentAction` | String | Set Properties (step 1) | Decision (step 4) | false | `"CREATE"` or `"UPDATE"` -- determines whether to fetch main version |
| `branchXml` | String | HTTP Client response (step 2) | `normalize-xml.groovy` (step 3) | false | Raw component XML from promotion branch |
| `branchXmlNormalized` | String | `normalize-xml.groovy` (step 3) | Map (step 8) | false | Normalized XML from promotion branch |
| `branchVersion` | String | HTTP Client response (step 2) | Map (step 8) | false | Component version on the promotion branch |
| `mainXml` | String | HTTP Client response (step 5) | `normalize-xml.groovy` (step 6) | false | Raw component XML from main branch (UPDATE only) |
| `mainXmlNormalized` | String | `normalize-xml.groovy` (step 6) or Set Empty (step 7) | Map (step 8) | false | Normalized XML from main branch; empty string for CREATE |
| `mainVersion` | String | HTTP Client response (step 5) or Set Empty (step 7) | Map (step 8) | false | Component version on main; `0` for CREATE |

---

### Process J: List Integration Packs

| DPP Name | Type | Set By | Used By | Persist | Description |
|----------|------|--------|---------|---------|-------------|
| `suggestForProcess` | String | Set Properties (step 1) | Decision (step 4.5), DataHub Query (step 5) | false | Optional process name to look up pack suggestion for |
| `packPurpose` | String | Set Properties (step 1) | Decision (step 4) | false | Filter: `"TEST"`, `"PRODUCTION"`, or `"ALL"` (default) |
| `packList` | String (JSON array) | Map (step 3) | Decision (step 4), Map (step 6) | false | Array of Integration Pack objects from API query |
| `suggestedPackId` | String | DataHub Query (step 5) | Map (step 6) | false | Most recently used pack ID for the given process |
| `suggestedPackName` | String | DataHub Query (step 5) | Map (step 6) | false | Name of the suggested pack |

---

### Groovy Script to DPP Cross-Reference

| Script | File | Process | DPPs Read | DPPs Written |
|--------|------|---------|-----------|--------------|
| Build Visited Set | `integration/scripts/build-visited-set.groovy` | B | `visitedComponentIds`, `componentQueue`, `currentComponentId` | `visitedComponentIds`, `componentQueue`, `alreadyVisited`, `visitedCount`, `queueCount` |
| Sort by Dependency | `integration/scripts/sort-by-dependency.groovy` | C | `rootComponentId` | (none -- sorts document in-place) |
| Strip Env Config | `integration/scripts/strip-env-config.groovy` | C | (none -- reads XML from document stream) | `configStripped`, `strippedElements` |
| Validate Connection Mappings | `integration/scripts/validate-connection-mappings.groovy` | C | `connectionMappingCache`, `componentMappingCache`, `devAccountId` | `missingConnectionMappings`, `missingConnectionCount`, `connectionMappingsValid`, `componentMappingCache` |
| Rewrite References | `integration/scripts/rewrite-references.groovy` | C | `componentMappingCache` | `referencesRewritten` |
| Normalize XML | `integration/scripts/normalize-xml.groovy` | G | (none -- reads XML from document stream) | (none -- outputs normalized XML to document stream) |

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

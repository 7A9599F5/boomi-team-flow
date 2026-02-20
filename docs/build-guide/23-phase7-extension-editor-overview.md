## Phase 7: Extension Editor

Phase 7 adds fine-grained environment extension editing to the Promotion Dashboard. This feature enables process-level access control for Boomi Environment Extensions and Map Extensions, a custom React editor component, client account (sub-account) support, and Test-to-Prod extension copying.

### What Phase 7 Adds

| Category | New Components | Details |
|----------|---------------|---------|
| DataHub Models | +2 | ExtensionAccessMapping, ClientAccountConfig |
| HTTP Client Operations | +8 | Account, Environment, Extensions CRUD, MapExtension, ComponentReference |
| DataHub Operations | +4 | Query + Update for ExtensionAccessMapping and ClientAccountConfig |
| JSON Profiles | +12 | Request + Response for 6 new message actions (K-O, Q) |
| Integration Processes | +6 | K (listClientAccounts), L (getExtensions), M (updateExtensions), N (copyExtensionsTestToProd), O (updateMapExtension), Q (validateScript) |
| FSS Operations | +6 | One per new message action |
| Custom Component | +1 | ExtensionEditor (React 16 + hooks, process-centric tree, inline editing) |
| Flow Pages | +2 | Page 10 (Extension Manager), Page 11 (Extension Copy Confirmation) |
| Groovy Scripts | +4 | build-extension-access-cache, strip-connections-for-copy, merge-extension-data, validate-script |

### Phase 7 BOM Impact

| Category | Before | Added | After |
|----------|--------|-------|-------|
| DataHub Models | 3 | +2 | 5 |
| Connections | 2 | 0 | 2 |
| HTTP Client Ops | 20 | +8 | 28 |
| DataHub Ops | 8 | +4 | 12 |
| JSON Profiles | 30 | +12 | 42 |
| Integration Processes | 14 | +6 | 20 |
| FSS Operations | 15 | +6 | 21 |
| Flow Service | 1 | 0 | 1 |
| Custom Components | 1 | +1 | 2 |
| Flow Connector | 1 | 0 | 1 |
| Flow Application | 1 | 0 | 1 |
| **Total** | **96** | **+39** | **135** |

### New DataHub Models

#### ExtensionAccessMapping
- **Purpose**: Cached authorization chain — maps environment + component to authorized SSO groups
- **Match fields**: `environmentId` + `prodComponentId` (EXACT)
- **Source**: `PROMOTION_ENGINE`
- **Key fields**: `environmentId`, `prodComponentId`, `componentName`, `componentType`, `authorizedSsoGroups` (comma-separated), `isConnectionExtension`, `sharedProcessCount`
- **Spec file**: `datahub/models/ExtensionAccessMapping-model-spec.json`

#### ClientAccountConfig
- **Purpose**: Client account registry — maps client accounts to SSO groups and environment IDs
- **Match fields**: `clientAccountId` + `ssoGroupId` (EXACT)
- **Source**: `ADMIN_CONFIG`
- **Key fields**: `clientAccountId`, `clientAccountName`, `ssoGroupId`, `testEnvironmentId`, `prodEnvironmentId`
- **Spec file**: `datahub/models/ClientAccountConfig-model-spec.json`

### New HTTP Client Operations

| # | Operation Name | Method | Endpoint | Purpose |
|---|---------------|--------|----------|---------|
| 1 | `PROMO - HTTP Op - QUERY Account` | POST | `/partner/api/rest/v1/{1}/Account/query` | List sub-accounts |
| 2 | `PROMO - HTTP Op - QUERY Environment` | POST | `/partner/api/rest/v1/{1}/Environment/query` | List environments per account |
| 3 | `PROMO - HTTP Op - GET EnvironmentExtensions` | GET | `/partner/api/rest/v1/{1}/EnvironmentExtensions/{2}` | Read extensions |
| 4 | `PROMO - HTTP Op - UPDATE EnvironmentExtensions` | POST | `/partner/api/rest/v1/{1}/EnvironmentExtensions/{2}/update` | Write extensions (partial) |
| 5 | `PROMO - HTTP Op - QUERY EnvironmentMapExtensionsSummary` | POST | `/partner/api/rest/v1/{1}/EnvironmentMapExtensions/{2}/query` | List map extension IDs |
| 6 | `PROMO - HTTP Op - GET EnvironmentMapExtension` | GET | `/partner/api/rest/v1/{1}/EnvironmentMapExtension/{2}` | Read map extension detail |
| 7 | `PROMO - HTTP Op - UPDATE EnvironmentMapExtension` | POST | `/partner/api/rest/v1/{1}/EnvironmentMapExtension/{2}/update` | Write map extension (Phase 2) |
| 8 | `PROMO - HTTP Op - QUERY ComponentReference` | POST | `/partner/api/rest/v1/{1}/ComponentReference/query` | Find processes using a component |

### New DataHub Operations

| # | Operation Name | Model | Action |
|---|---------------|-------|--------|
| 1 | `PROMO - DH Op - Query ExtensionAccessMapping` | ExtensionAccessMapping | Query Golden Records |
| 2 | `PROMO - DH Op - Update ExtensionAccessMapping` | ExtensionAccessMapping | Update Golden Records |
| 3 | `PROMO - DH Op - Query ClientAccountConfig` | ClientAccountConfig | Query Golden Records |
| 4 | `PROMO - DH Op - Update ClientAccountConfig` | ClientAccountConfig | Update Golden Records |

### Phase 7 Build Order

```
Step 7A: DataHub Models (ExtensionAccessMapping, ClientAccountConfig)
    └── Step 7B: HTTP Client + DataHub Operations (12 new operations)
            └── Step 7C: Processes K-O (see next file)
                    └── Step 7D: Flow Service Update (add 5 message actions)
                            └── Step 7E: Flow Dashboard Update (Pages 10-11, ExtensionEditor component)
                                    └── Step 7F: Testing (extension-specific test scenarios)
```

### Key Design Decisions

1. **`partial="true"` always** — Environment Extensions UPDATE without `partial` wipes all omitted sections. Always set `partial="true"`.
2. **Map Extensions read-only in Phase 1** — UPDATE EnvironmentMapExtension deletes omitted field mappings. Phase 1 shows read-only data; Phase 2 adds editing with full mapping preservation.
3. **Process-centric tree** — Extensions organized by process (via ComponentReference and ExtensionAccessMapping), not Boomi's default flat tab/dropdown layout.
4. **JSON-serialized strings** — `extensionData` and `accessMappings` passed as opaque JSON strings in profiles to avoid deeply nested profile complexity. The custom component parses them client-side.
5. **Connection admin gate** — Connections require `ABC_BOOMI_FLOW_ADMIN` SSO group. Non-admins see connection extensions read-only.

---
Prev: [Appendix D: API Automation Guide](22-api-automation-guide.md) | Next: [Extension Processes K-O](24-extension-processes.md) | [Back to Index](index.md)

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Boomi Dev-to-Prod Component Promotion System** — a specification repository for a multi-account Boomi workflow that promotes packaged processes from dev sub-accounts to a primary (production) account via Platform API, maintaining single master components with incremental versions. A 2-layer approval workflow (peer review + admin review) gates Integration Pack deployment.

This is **not a traditional software codebase** — there is no build system, package manager, or test runner. It is an architectural specification and implementation guide for a Boomi iPaaS solution. "Building" means configuring Boomi AtomSphere (DataHub models, Integration processes, Flow dashboard) following the [Build Guide](docs/build-guide/index.md).

## Architecture

```
Flow Dashboard (3 swimlanes: Dev + Peer Review + Admin, 11 pages)
  ↓ Message Actions (Flow Service)
Integration Engine (20 processes A0–G, E2–E5, J, K–Q on Public Boomi Cloud Atom)
  ↓                    ↓
Platform API        DataHub
(Partner API)       (ComponentMapping, DevAccountAccess, PromotionLog, ExtensionAccessMapping, ClientAccountConfig)
```

**20 Integration Processes:**
- **A0** getDevAccounts — SSO group → dev account access lookup
- **A** listDevPackages — query dev account's PackagedComponents
- **B** resolveDependencies — recursive dependency traversal + mapping lookup
- **C** executePromotion — create branch → promote to branch (tilde syntax) → strip env config → rewrite refs
- **D** packageAndDeploy — 4-mode deploy (test/production-from-test/hotfix/pack-assignment), merge, package, Integration Pack, deploy
- **E** queryStatus — read PromotionLog from DataHub (supports reviewStage filter)
- **E2** queryPeerReviewQueue — query PENDING_PEER_REVIEW promotions, exclude own
- **E3** submitPeerReview — record peer approve/reject with self-review prevention
- **E4** queryTestDeployments — query test-deployed promotions ready for production
- **E5** withdrawPromotion — initiator-driven withdrawal of pending promotions
- **F** manageMappings — CRUD on ComponentMapping records
- **G** generateComponentDiff — fetch branch vs main component XML for diff rendering
- **J** listIntegrationPacks — query Integration Packs with smart suggestion from history
- **K** listClientAccounts — SSO group → accessible client accounts + environments
- **L** getExtensions — read env extensions + map extension summaries, merge with access data
- **M** updateExtensions — save env extension changes (partial update, access-validated)
- **N** copyExtensionsTestToProd — copy non-connection env extensions from Test to Prod
- **O** updateMapExtension — save map extension changes (Phase 2 editing; Phase 1 read-only)
- **P** checkReleaseStatus — poll ReleaseIntegrationPackStatus for release propagation tracking
- **Q** validateScript — syntax and security validation for map extension script functions (Groovy + JavaScript)

**21 Message Actions** (FSS Operations): one per process, plus `cancelTestDeployment` (E4 reuse). When adding a new action, update: FSS op table in `04-process-canvas-fundamentals.md`, message actions table in `14-flow-service.md`, listener list in `14-flow-service.md`, Flow types list in `15-flow-dashboard-developer.md`, troubleshooting counts in `18-troubleshooting.md`, and `22-api-automation-guide.md` FSS table.

**Key design decisions** (see `docs/architecture.md`):
- Message Actions over Data Actions (complex logic requires full process control)
- HTTP Client over AtomSphere API Connector (tilde syntax for branch operations, JSON support, immediate access to new API objects — official SOAP connectors can't construct `Component/{id}~{branchId}` URLs)
- Public Cloud Atom (no firewall issues, everything within Boomi infra)
- DataHub over external DB (no 30s+ latency from firewall/domain limitations)
- Connections NOT promoted — pre-configured in parent `#Connections` folder, shared via admin-seeded ComponentMapping records
- Mirrored folder paths: dev `/DevTeamA/Orders/Process/` → prod `/Promoted/DevTeamA/Orders/Process/`
- Integration Pack selection is an admin function (Page 7), not a developer function — test deployments auto-detect IP from PromotionLog history; brand-new packages get `PENDING_PACK_ASSIGNMENT` status for admin assignment

## Repository Structure

```
datahub/
  models/              5 DataHub model specs (JSON) — ComponentMapping, DevAccountAccess, PromotionLog, ExtensionAccessMapping, ClientAccountConfig
  api-requests/        Golden record test XML templates
integration/
  profiles/            42 JSON request/response profiles (21 message actions × 2)
  scripts/             11 Groovy scripts (dependency traversal, sorting, stripping, validation, rewriting, XML normalization, test deployment filtering, extension access cache, connection stripping for copy, extension data merging, script validation)
  api-requests/        28 XML/JSON Platform API templates (Component CRUD, PackagedComponent, IntegrationPack, Branch, MergeRequest, ReleaseIntegrationPackStatus, Environment Extensions, Map Extensions)
    component-types/   13 per-type <bns:object> XML reference examples (process, profiles, connectors, maps, scripts, etc.)
  flow-service/        Flow Service specification (message actions, config, error codes)
flow/
  flow-structure.md    App structure — 3 swimlanes, 11 pages, Flow values, navigation
  page-layouts/        11 page specs (Package Browser, Promotion Review, Status, Deployment, Peer Review Queue, Peer Review Detail, Admin Approval Queue, Mapping Viewer, Production Readiness, Extension Manager, Extension Copy Confirmation)
  custom-components/   Custom React component specs (XmlDiffViewer, ExtensionEditor)
docs/
  architecture.md      System design, decisions, constraints, error handling
  build-guide/         26 focused build-step files + index (split from BUILD-GUIDE.md)
```

## Key Files to Start With

1. `docs/architecture.md` — system design and key decisions
2. `docs/build-guide/index.md` — the implementation playbook (7 phases, 26 focused files)
3. `integration/flow-service/flow-service-spec.md` — complete API contract for all 21 message actions
4. `flow/flow-structure.md` — dashboard navigation, Flow values, swimlanes

## Groovy Scripts

Located in `integration/scripts/`, these run as Data Process steps inside Integration processes:

| Script | Used In | Purpose |
|--------|---------|---------|
| `build-visited-set.groovy` | Process B | Recursive dependency traversal |
| `sort-by-dependency.groovy` | Process B | Type-hierarchy ordering (profile→connection→operation→map→process) |
| `strip-env-config.groovy` | Process C | Remove passwords, hosts, URLs, encrypted values from component XML |
| `validate-connection-mappings.groovy` | Process C | Pre-promotion batch validation that all connection mappings exist |
| `rewrite-references.groovy` | Process C | Replace dev component IDs with prod IDs using mapping cache |
| `normalize-xml.groovy` | Process G | Pretty-print component XML for consistent line-by-line diff comparison |
| `filter-already-promoted.groovy` | Process E4 | Exclude test deployments already promoted to production |
| `build-extension-access-cache.groovy` | Process D | Build ExtensionAccessMapping records from extensions + ComponentMapping + DevAccountAccess |
| `strip-connections-for-copy.groovy` | Process N | Remove connections + PGP sections for Test-to-Prod copy |
| `merge-extension-data.groovy` | Process L | Merge env extensions + map summaries + access mappings |
| `validate-script.groovy` | Process Q | Syntax and security validation for Groovy/JavaScript scripts |

## DataHub Models

- **ComponentMapping** — dev→prod component ID mapping. Match: `devComponentId` + `devAccountId`. Sources: `PROMOTION_ENGINE`, `ADMIN_SEEDING`
- **DevAccountAccess** — SSO group → dev account access control. Match: `ssoGroupId` + `devAccountId`. Source: `ADMIN_CONFIG`
- **PromotionLog** — audit trail per promotion run. Match: `promotionId`. Source: `PROMOTION_ENGINE`
- **ExtensionAccessMapping** — cached authorization chain for extension editing. Match: `environmentId` + `prodComponentId`. Source: `PROMOTION_ENGINE`
- **ClientAccountConfig** — client account registry with environment mapping. Match: `clientAccountId` + `ssoGroupId`. Source: `ADMIN_CONFIG`

## Boomi Component API Type Values

When working with Component CRUD templates (`create-component.xml`, `update-component.xml`, `get-component.xml`), the `type` attribute on `<bns:Component>` uses these values. Per-type `<bns:object>` XML examples are in `integration/api-requests/component-types/`.

| Component | API `type` value | Inner XML root | Promoted? |
|-----------|-----------------|----------------|-----------|
| Process | `process` | `<process>` | Yes |
| JSON Profile | `profile.json` | `<JSONProfile>` | Yes |
| XML Profile | `profile.xml` | `<XMLProfile>` | Yes |
| Flat File Profile | `profile.flatfile` | `<FlatFileProfile>` | Yes |
| EDI Profile | `profile.edi` | `<EDIProfile>` | Yes |
| Database Profile | `profile.db` | `<DatabaseProfile>` | Yes |
| Connection | `connector-settings` | `<GenericConnectorConfig>` | **No** |
| Connector Operation | `connector-action` | `<Operation>` (HTTP Client) / varies by connector | Yes |
| Map | `transform.map` | `<map>` | Yes |
| Map Script | `script.mapping` | `<scripting>` (scriptType=mapscript) | Yes |
| Process Script | `script.processing` | `<ProcessingScript>` | Yes |
| Process Route | `processroute` | `<processRoute>` | Yes |
| Cross Ref Table | `crossref` | `<CrossRefTable>` | Yes |

> **Note:** The inner XML root varies by connector type. HTTP Client operations use `<Operation>` containing `<Http{Method}Action>` with named `<pathElements>` for URL construction. Other connector types (Database, Disk, etc.) may use `<GenericConnectorConfig>`. Always use the API-First Discovery workflow to capture the real XML structure.

## Conventions

- **Commit messages**: conventional commits — `feat(scope):`, `fix(scope):`, `docs:`, etc.
- **Spec files**: Markdown for documentation, JSON for data models/profiles, XML for API request templates, Groovy for scripts
- **Naming**: processes use letter codes (A0, A–G, E2–E5, J, K–Q); message actions use camelCase (`getDevAccounts`, `executePromotion`, `withdrawPromotion`)
- **Error codes**: uppercase snake_case (`MISSING_CONNECTION_MAPPINGS`, `COMPONENT_NOT_FOUND`, `BRANCH_LIMIT_REACHED`)
- **SSO group names** — always use claim format `ABC_BOOMI_FLOW_CONTRIBUTOR`, `ABC_BOOMI_FLOW_ADMIN`, etc. Never use display format (`"Boomi Developers"`) as authorization values
- **Branch limits** — operational threshold is 15, platform hard limit is 20. Grep for stale values (10, 18) when editing branch-related content
- **Fail-fast promotion** — Process C deletes the promotion branch on any component failure. Only `COMPLETED` or `FAILED` are valid Process C outcomes; `PARTIALLY_COMPLETED` is not a valid status. Process D gates on `COMPLETED`, `TEST_DEPLOYED`, or `PENDING_PACK_ASSIGNMENT` before proceeding.
- **Test deployment language** — describe the dev→test path as "automated validation, no manual gates/approval." Never use "no review required" or "without review" — this leaves room for future automated checks (e.g., missing connector mapping rejection) that aren't manual approval gates.

## Working with the Build Guide

- **Count references are scattered** — when changing component counts (processes, profiles, pages, actions, types), grep `docs/build-guide/`, `.claude/skills/`, `.claude/rules/`, and `CHANGELOG.md` for stale numbers. Key files: `00-overview.md`, `index.md`, `04-process-canvas-fundamentals.md`, `14-flow-service.md`, `15-flow-dashboard-developer.md`, `18-troubleshooting.md`, `19-appendix-naming-and-inventory.md`, `22-api-automation-guide.md` (has counts in BOTH a Markdown table AND a bash OPERATIONS array)
- **Current component counts** (verify before editing): 133 total — 5 models, 2 connections, 28 HTTP ops, 10 DH ops, 42 profiles, 20 processes, 21 FSS ops, 1 Flow Service, 2 custom components, 1 Flow connector, 1 Flow app, 11 scripts, 28 API request templates
- **BOM total must be recomputed** — the total in `00-overview.md` drifts when individual row counts change. Always sum the rows: Models + Connections + HTTP Ops + DH Ops + Profiles + Processes + FSS Ops + Flow Service + Custom Component + Flow Connector + Flow App
- **Inventory checklist must stay in sync** — `19-appendix-naming-and-inventory.md` has a numbered checklist that must match the BOM total. When inserting items, renumber ALL subsequent entries. The last item number must equal the BOM total.
- **Spec files are source of truth** — `datahub/models/*.json`, `integration/profiles/*.json`, `flow/flow-structure.md`, and `flow/page-layouts/` define the system. Build guide docs must match them.
- **Nav footer pattern** — every build guide file ends with `Prev: [...] | Next: [...] | [Back to Index](index.md)`
- **Verify plan items against current state** — planned changes may already be implemented in the codebase

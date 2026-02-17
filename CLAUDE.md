# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Boomi Dev-to-Prod Component Promotion System** — a specification repository for a multi-account Boomi workflow that promotes packaged processes from dev sub-accounts to a primary (production) account via Platform API, maintaining single master components with incremental versions. A 2-layer approval workflow (peer review + admin review) gates Integration Pack deployment.

This is **not a traditional software codebase** — there is no build system, package manager, or test runner. It is an architectural specification and implementation guide for a Boomi iPaaS solution. "Building" means configuring Boomi AtomSphere (DataHub models, Integration processes, Flow dashboard) following the [Build Guide](docs/build-guide/index.md).

## Architecture

```
Flow Dashboard (3 swimlanes: Dev + Peer Review + Admin, 9 pages)
  ↓ Message Actions (Flow Service)
Integration Engine (12 processes A0–G + E2, E3, E4, J on Public Boomi Cloud Atom)
  ↓                    ↓
Platform API        DataHub
(Partner API)       (ComponentMapping, DevAccountAccess, PromotionLog)
```

**12 Integration Processes:**
- **A0** getDevAccounts — SSO group → dev account access lookup
- **A** listDevPackages — query dev account's PackagedComponents
- **B** resolveDependencies — recursive dependency traversal + mapping lookup
- **C** executePromotion — create branch → promote to branch (tilde syntax) → strip env config → rewrite refs
- **D** packageAndDeploy — 3-mode deploy (test/production-from-test/hotfix), merge, package, Integration Pack, deploy
- **E** queryStatus — read PromotionLog from DataHub (supports reviewStage filter)
- **E2** queryPeerReviewQueue — query PENDING_PEER_REVIEW promotions, exclude own
- **E3** submitPeerReview — record peer approve/reject with self-review prevention
- **E4** queryTestDeployments — query test-deployed promotions ready for production
- **F** manageMappings — CRUD on ComponentMapping records
- **G** generateComponentDiff — fetch branch vs main component XML for diff rendering
- **J** listIntegrationPacks — query Integration Packs with smart suggestion from history

**Key design decisions** (see `docs/architecture.md`):
- Message Actions over Data Actions (complex logic requires full process control)
- Public Cloud Atom (no firewall issues, everything within Boomi infra)
- DataHub over external DB (no 30s+ latency from firewall/domain limitations)
- Connections NOT promoted — pre-configured in parent `#Connections` folder, shared via admin-seeded ComponentMapping records
- Mirrored folder paths: dev `/DevTeamA/Orders/Process/` → prod `/Promoted/DevTeamA/Orders/Process/`

## Repository Structure

```
datahub/
  models/              3 DataHub model specs (JSON) — ComponentMapping, DevAccountAccess, PromotionLog
  api-requests/        Golden record test XML templates
integration/
  profiles/            24 JSON request/response profiles (12 message actions × 2)
  scripts/             6 Groovy scripts (dependency traversal, sorting, stripping, validation, rewriting, XML normalization)
  api-requests/        13 XML/JSON Platform API templates (Component CRUD, PackagedComponent, DeployedPackage, IntegrationPack, Branch, MergeRequest)
  flow-service/        Flow Service specification (message actions, config, error codes)
flow/
  flow-structure.md    App structure — 3 swimlanes, 9 pages, Flow values, navigation
  page-layouts/        9 page specs (Package Browser, Promotion Review, Status, Deployment, Peer Review Queue, Peer Review Detail, Admin Approval Queue, Mapping Viewer, Production Readiness)
  custom-components/   Custom React component specs (XmlDiffViewer)
docs/
  architecture.md      System design, decisions, constraints, error handling
  build-guide/         22 focused build-step files + index (split from BUILD-GUIDE.md)
```

## Key Files to Start With

1. `docs/architecture.md` — system design and key decisions
2. `docs/build-guide/index.md` — the implementation playbook (6 phases, 22 focused files)
3. `integration/flow-service/flow-service-spec.md` — complete API contract for all 12 message actions
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

## DataHub Models

- **ComponentMapping** — dev→prod component ID mapping. Match: `devComponentId` + `devAccountId`. Sources: `PROMOTION_ENGINE`, `ADMIN_SEEDING`
- **DevAccountAccess** — SSO group → dev account access control. Match: `ssoGroupId` + `devAccountId`. Source: `ADMIN_CONFIG`
- **PromotionLog** — audit trail per promotion run. Match: `promotionId`. Source: `PROMOTION_ENGINE`

## Conventions

- **Commit messages**: conventional commits — `feat(scope):`, `fix(scope):`, `docs:`, etc.
- **Spec files**: Markdown for documentation, JSON for data models/profiles, XML for API request templates, Groovy for scripts
- **Naming**: processes use letter codes (A0, A–G, J); message actions use camelCase (`getDevAccounts`, `executePromotion`)
- **Error codes**: uppercase snake_case (`MISSING_CONNECTION_MAPPINGS`, `COMPONENT_NOT_FOUND`, `BRANCH_LIMIT_REACHED`)

## Working with the Build Guide

- **Count references are scattered** — when changing component counts (processes, profiles, pages, actions, types), grep the entire `docs/build-guide/` directory for stale numbers. Key files: `00-overview.md`, `index.md`, `14-flow-service.md`, `15-flow-dashboard-developer.md`, `18-troubleshooting.md`
- **Spec files are source of truth** — `datahub/models/*.json`, `integration/profiles/*.json`, `flow/flow-structure.md`, and `flow/page-layouts/` define the system. Build guide docs must match them.
- **Nav footer pattern** — every build guide file ends with `Prev: [...] | Next: [...] | [Back to Index](index.md)`
- **Verify plan items against current state** — planned changes may already be implemented in the codebase

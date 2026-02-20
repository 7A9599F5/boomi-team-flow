# Boomi Component Promotion System — Build Guide

This guide walks through building every component of the Promotion System step by step. It has been split into focused files for easier navigation. Follow the phases in order — each phase builds on the previous.

## Table of Contents

| # | File | Content |
|---|------|---------|
| 00 | [Overview & Prerequisites](00-overview.md) | Intro, how to use, prerequisites, BOM, naming convention, dependency build order, repo file reference |
| 01 | [Phase 1: DataHub Foundation](01-datahub-foundation.md) | 3 DataHub models, seed data, CRUD test & cleanup |
| 02 | [Phase 2a: HTTP Client Setup](02-http-client-setup.md) | HTTP Client connection + 20 HTTP Client operations |
| 03 | [Phase 2b: DataHub Connection Setup](03-datahub-connection-setup.md) | DataHub connection + 8 DataHub operations + Phase 2 verify & checklist |
| 04 | [Phase 3: Process Canvas Fundamentals](04-process-canvas-fundamentals.md) | Phase 3 intro: shapes, profile import, Groovy scripts, DPP pattern, general process skeleton |
| 05 | [Process F: Mapping CRUD](05-process-f-mapping-crud.md) | Process F — template "hello world" process, fully detailed shape-by-shape |
| 06 | [Process A0: Get Dev Accounts](06-process-a0-get-dev-accounts.md) | Process A0 — SSO group to dev account access lookup |
| 07 | [Process E: Query Status](07-process-e-status-and-review.md) | Processes E, E2-E5 — status queries, peer review, test deployments, withdrawal |
| 08 | [Process A: List Dev Packages](08-process-a-list-dev-packages.md) | Process A — query PackagedComponents with pagination + name enrichment |
| 09 | [Process B: Resolve Dependencies](09-process-b-resolve-dependencies.md) | Process B — recursive dependency traversal, mapping lookup, Groovy scripts |
| 10 | [Process C: Execute Promotion](10-process-c-execute-promotion.md) | Process C — core promotion engine (branch, strip, rewrite, Try/Catch, PromotionLog) |
| 11 | [Process D: Package and Deploy](11-process-d-package-and-deploy.md) | Process D — merge branch, create PackagedComponent, Integration Pack, deploy |
| 12 | [Process J: List Integration Packs](12-process-j-list-integration-packs.md) | Process J — query Integration Packs with smart suggestion |
| 13 | [Process G: Component Diff & Build Order](13-process-g-component-diff.md) | Process G — branch vs main XML diff + normalize-xml.groovy + build order checklist |
| 14 | [Phase 4: Flow Service Component](14-flow-service.md) | Create Flow Service (21 actions), deploy, configure, verify listeners |
| 15 | [Phase 5a: Flow Dashboard — Developer Swimlane](15-flow-dashboard-developer.md) | Install connector + Pages 1-4 (Developer Swimlane) |
| 16 | [Phase 5b: Flow Dashboard — Review & Admin](16-flow-dashboard-review-admin.md) | Pages 5-9, SSO config, wire navigation, XmlDiffViewer custom component |
| 17 | [Phase 6: Testing](17-testing.md) | Smoke test + 7 test scenarios |
| 18 | [Troubleshooting](18-troubleshooting.md) | Per-phase troubleshooting + diagnostic commands |
| 19 | [Appendix A: Naming & Inventory](19-appendix-naming-and-inventory.md) | Naming patterns + component inventory checklist |
| 20 | [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | DPP catalog, Groovy cross-reference, type priority |
| 21 | [Appendix C: Platform API Reference](21-appendix-platform-api-reference.md) | Auth, endpoints, rate limiting, response codes, curl/PS templates |
| 22 | [Appendix D: API Automation Guide](22-api-automation-guide.md) | Dependency-ordered API workflow, batch scripts, export/import, verification |
| 23 | [Phase 7: Extension Editor Overview](23-phase7-extension-editor-overview.md) | Phase 7 intro, new models, operations, BOM impact, design decisions |
| 24 | [Extension Processes K-O](24-extension-processes.md) | Processes K-O — extension CRUD, copy, map extensions, shape-by-shape |
| 25 | [Extension Flow Service & Dashboard](25-extension-flow-service-and-dashboard.md) | FSS ops update, ExtensionEditor component, Pages 10-11 |
| 26 | [Extension Testing](26-extension-testing.md) | 10 test scenarios for extension editor workflows |

## Quick Links by Phase

- **Phase 1** (DataHub): [01](01-datahub-foundation.md)
- **Phase 2** (Connections & Operations): [02](02-http-client-setup.md), [03](03-datahub-connection-setup.md)
- **Phase 3** (Integration Processes): [04](04-process-canvas-fundamentals.md), [05](05-process-f-mapping-crud.md)–[13](13-process-g-component-diff.md)
- **Phase 4** (Flow Service): [14](14-flow-service.md)
- **Phase 5** (Flow Dashboard): [15](15-flow-dashboard-developer.md), [16](16-flow-dashboard-review-admin.md)
- **Phase 6** (Testing): [17](17-testing.md)
- **Phase 7** (Extension Editor): [23](23-phase7-extension-editor-overview.md), [24](24-extension-processes.md), [25](25-extension-flow-service-and-dashboard.md), [26](26-extension-testing.md)
- **Reference**: [18](18-troubleshooting.md), [19](19-appendix-naming-and-inventory.md), [20](20-appendix-dpp-catalog.md), [21](21-appendix-platform-api-reference.md), [22](22-api-automation-guide.md)

# Changelog

All notable changes to the Boomi Component Promotion System are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

- **BUILD-GUIDE.md**: Enhanced from 410-line outline to 3,148-line step-by-step implementation manual
  - Section 0: Bill of materials (51 components), naming conventions, dependency build order
  - Phase 1: DataHub UI navigation breadcrumbs, dual-format CRUD verification commands (curl + PowerShell)
  - Phase 2: Detailed configuration for all 9 HTTP Client and 6 DataHub operations with DPP bindings
  - Phase 3: Shape-by-shape canvas instructions for all 7 integration processes, Groovy script DPP mappings, recommended build order (F, A0, E, A, B, C, D)
  - Phase 4: Flow Service Message Actions configuration table, deployment verification checklist
  - Phase 5: Page-by-page Flow dashboard build instructions for all 6 pages with Message step configs
  - Phase 6: Smoke test sequence, 7 enhanced test cases with dual-format API verification commands
  - Troubleshooting: Organized by phase with diagnostic commands
  - Appendix A: Complete 51-component inventory checklist with naming patterns
  - Appendix B: Full Dynamic Process Properties catalog with Groovy script cross-reference
  - Appendix C: Platform API quick reference with 6 reusable dual-format call templates

---

## [0.1.0] - 2026-02-16

### Added

- **DataHub models** (`/datahub/models/`): ComponentMapping, DevAccountAccess, PromotionLog model specifications
- **DataHub test requests** (`/datahub/api-requests/`): Golden record create and query XML templates
- **JSON profiles** (`/integration/profiles/`): 14 request/response profile pairs for all 7 processes
- **Groovy scripts** (`/integration/scripts/`): build-visited-set, sort-by-dependency, strip-env-config, rewrite-references
- **API request templates** (`/integration/api-requests/`): 9 templates for Platform API operations (Component CRUD, PackagedComponent, DeployedPackage, IntegrationPack, ComponentReference, ComponentMetadata)
- **Flow Service specification** (`/integration/flow-service/`): Complete spec for 7 message actions, configuration values, auto-generated Flow Types, deployment steps, error handling contract
- **Flow dashboard structure** (`/flow/`): Application structure with 2 swimlanes, 6 pages, Flow values, navigation map, email notifications
- **Page layout specs** (`/flow/page-layouts/`): Detailed UI specs for Package Browser, Promotion Review, Promotion Status, Deployment Submission, Approval Queue, Mapping Viewer
- **Architecture reference** (`/docs/architecture.md`): System overview, key design decisions, DataHub models, integration process descriptions, error handling strategy
- **Build guide** (`/docs/BUILD-GUIDE.md`): 6-phase build guide covering DataHub, connections, processes, Flow Service, Flow dashboard, and testing

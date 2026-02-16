# Changelog

All notable changes to the Boomi Component Promotion System are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

- **Mirrored folder structure**: Promoted components now mirror the dev account's folder hierarchy under `/Promoted/` instead of flat `/Promoted/{devAccountName}/{processName}/` paths (e.g., dev path `/DevTeamARoot/Orders/MyProcess/` becomes `/Promoted/DevTeamARoot/Orders/MyProcess/`)
- **Shared connection model**: Connection components are no longer promoted — they are pre-configured once in the parent account's `#Connections` folder and shared across all dev accounts via admin-seeded ComponentMapping records
- **Pre-promotion connection validation**: New `validate-connection-mappings.groovy` script validates ALL connection mappings exist before promotion begins; fails with complete error report (`MISSING_CONNECTION_MAPPINGS`) if any are missing
- **ADMIN_SEEDING source**: New DataHub source on ComponentMapping model for admin-seeded connection mappings, with `mappingSource` field to distinguish engine-created vs. admin-seeded records
- **Connection seeding UI**: Mapping Viewer (Page 6) now includes dedicated "Seed Connection Mapping" section and `mappingSource` column/filter
- **Promotion Review enhancements**: Connection rows show "(shared)" badge with MAPPED/UNMAPPED status; Promote button disabled when unmapped connections exist
- **Promotion Status updates**: New SKIPPED_CONNECTION/PRE_MAPPED badges; "Connections (Shared)" summary count; reduced credential warning prominence

### Changed

- **API templates**: `create-component.xml` and `update-component.xml` use `folderFullPath="/Promoted{devFolderFullPath}"` instead of `/Promoted/{devAccountName}/{processName}/`
- **executePromotion response**: Added `connectionsSkipped` and `missingConnectionMappings` fields
- **resolveDependencies response**: Added `folderFullPath` and `isSharedConnection` to component entries
- **executePromotion request**: Added `folderFullPath` to component entries
- **Architecture docs**: Updated promotion engine logic to include connection validation phase
- **BUILD-GUIDE.md**: Added connection validation steps, mirrored folder path instructions, updated DPP catalog and Groovy script cross-reference
- **Flow Service spec**: Added `MISSING_CONNECTION_MAPPINGS` error code, connection seeding workflow documentation
- **Flow structure**: Added `sharedConnections`, `unmappedConnections`, `connectionsSkipped` Flow values

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

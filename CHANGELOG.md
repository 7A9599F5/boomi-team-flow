# Changelog

All notable changes to the Boomi Component Promotion System are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

- **Boomi Branching integration**: Process C now promotes components to a temporary branch (not main) using tilde syntax (`Component/{id}~{branchId}`); admin approval merges branch → main via OVERRIDE merge strategy; rejection/denial deletes branch without touching main
- **Side-by-side component diff view**: New Process G (`generateComponentDiff`) fetches branch vs main XML for client-side diff rendering; available on Pages 3, 6, and 7 via "View Diff"/"View New" links
- **XmlDiffViewer custom component**: React component spec (`flow/custom-components/xml-diff-viewer.md`) using `diff`, `react-diff-view`, and `prismjs` for syntax-highlighted side-by-side/unified XML diffs with line numbers, expand/collapse, and copy buttons
- **Integration Pack listing**: New Process J (`listIntegrationPacks`) queries primary account for MULTI-type packs; returns pack list with smart suggestion based on PromotionLog history for same process name
- **Branch API templates**: `create-branch.json`, `create-merge-request.json`, `execute-merge-request.json` for Boomi Branching lifecycle management
- **Integration Pack query template**: `query-integration-packs.xml` for `POST /IntegrationPack/query`
- **XML normalization script**: `normalize-xml.groovy` pretty-prints component XML for consistent line-by-line diff comparison
- **Branch lifecycle management**: 20-branch hard limit enforced (fail at >= 18 with `BRANCH_LIMIT_REACHED`); all terminal paths (approve, reject, deny) delete branch and clear `branchId` in PromotionLog
- **Mirrored folder structure**: Promoted components now mirror the dev account's folder hierarchy under `/Promoted/` instead of flat `/Promoted/{devAccountName}/{processName}/` paths (e.g., dev path `/DevTeamARoot/Orders/MyProcess/` becomes `/Promoted/DevTeamARoot/Orders/MyProcess/`)
- **Shared connection model**: Connection components are no longer promoted — they are pre-configured once in the parent account's `#Connections` folder and shared across all dev accounts via admin-seeded ComponentMapping records
- **Pre-promotion connection validation**: New `validate-connection-mappings.groovy` script validates ALL connection mappings exist before promotion begins; fails with complete error report (`MISSING_CONNECTION_MAPPINGS`) if any are missing
- **ADMIN_SEEDING source**: New DataHub source on ComponentMapping model for admin-seeded connection mappings, with `mappingSource` field to distinguish engine-created vs. admin-seeded records
- **Connection seeding UI**: Mapping Viewer (Page 8) now includes dedicated "Seed Connection Mapping" section and `mappingSource` column/filter
- **Promotion Review enhancements**: Connection rows show "(shared)" badge with MAPPED/UNMAPPED status; Promote button disabled when unmapped connections exist
- **Promotion Status updates**: New SKIPPED_CONNECTION/PRE_MAPPED badges; "Connections (Shared)" summary count; reduced credential warning prominence

### Changed

- **Process C (executePromotion)**: Creates promotion branch → polls readiness → promotes to branch via tilde syntax → returns `branchId` and `branchName` in response; cleans up branch on failure
- **Page 3 (Promotion Status)**: Added "View Diff" column and Component Diff Panel with XmlDiffViewer; added branch info in summary section
- **Page 6 (Peer Review Detail)**: Added "View Diff" column and Component Diff Panel; Reject now deletes promotion branch
- **Page 7 (Admin Approval Queue)**: Added "View Diff" column and Component Diff Panel; Approve now follows merge → package → deploy → cleanup flow; Deny now deletes promotion branch
- **Page 4 (Deployment Submission)**: Integration Pack selector wired to `listIntegrationPacks` (Process J) with auto-suggestion from PromotionLog history
- **PromotionLog model**: Added 5 fields — `branchId`, `branchName`, `integrationPackId`, `integrationPackName`, `processName`
- **executePromotion response**: Added `branchId` and `branchName` fields
- **packageAndDeploy request**: Added `branchId` field for branch deletion after deploy
- **Flow Service spec**: Added actions #10 (`generateComponentDiff`) and #11 (`listIntegrationPacks`); added `BRANCH_LIMIT_REACHED` error code; updated process count to 11
- **Flow structure**: Added 7 new Flow values (`branchId`, `branchName`, `diffBranchXml`, `diffMainXml`, `selectedDiffComponent`, `availableIntegrationPacks`, `suggestedPackId`); added message steps #10 and #11
- **Architecture docs**: Added Boomi Branching strategy section, branch lifecycle diagram, 20-branch limit management, OVERRIDE merge strategy rationale; added Processes G and J
- **BUILD-GUIDE.md**: Added Process G and J build steps, branch API operations, XmlDiffViewer custom component deployment guide; updated BOM from 57 to 71 components; updated all counts (11 processes, 22 profiles, 12 HTTP ops)
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
- **JSON profiles** (`/integration/profiles/`): 18 request/response profile pairs for all 9 processes
- **Groovy scripts** (`/integration/scripts/`): build-visited-set, sort-by-dependency, strip-env-config, rewrite-references
- **API request templates** (`/integration/api-requests/`): 9 templates for Platform API operations (Component CRUD, PackagedComponent, DeployedPackage, IntegrationPack, ComponentReference, ComponentMetadata)
- **Flow Service specification** (`/integration/flow-service/`): Complete spec for 9 message actions, configuration values, auto-generated Flow Types, deployment steps, error handling contract
- **Flow dashboard structure** (`/flow/`): Application structure with 3 swimlanes, 8 pages, Flow values, navigation map, email notifications
- **Page layout specs** (`/flow/page-layouts/`): Detailed UI specs for Package Browser, Promotion Review, Promotion Status, Deployment Submission, Approval Queue, Mapping Viewer
- **Architecture reference** (`/docs/architecture.md`): System overview, key design decisions, DataHub models, integration process descriptions, error handling strategy
- **Build guide** (`/docs/BUILD-GUIDE.md`): 6-phase build guide covering DataHub, connections, processes, Flow Service, Flow dashboard, and testing

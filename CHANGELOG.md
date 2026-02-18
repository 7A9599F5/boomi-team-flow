# Changelog

All notable changes to the Boomi Component Promotion System are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.11.0] — 2026-02-18

### Added
- **Main branch protection**: Test deployments no longer merge to main — packaged directly from the promotion branch using `branchName` field on POST /PackagedComponent
- **Admin Integration Pack ownership**: Developers no longer select IPs; admin assigns on Page 7. Auto-detection from PromotionLog history for returning packages; `PENDING_PACK_ASSIGNMENT` status for brand-new packages
- **Mode 4 (PACK_ASSIGNMENT)**: New Process D mode for admin IP assignment to previously packaged components
- **Pack Assignment Queue tab on Page 7**: Admin tab for PENDING_PACK_ASSIGNMENT promotions with IP selector
- **Multi-package release safety**: Query IP state via GET /IntegrationPack before releasing; explicit `ReleasePackagedComponents` array prevents dropping packages
- **GET IntegrationPack HTTP operation**: New HTTP op for querying IP state (28 total HTTP ops, 129 BOM total)

### Changed
- **Process D rewritten**: 4 deployment modes (TEST, PRODUCTION, HOTFIX, PACK_ASSIGNMENT) with new branch lifecycle
- **Page 4 simplified**: Removed Integration Pack selector — developers submit version + notes only
- **Page 7 expanded**: Added IP selector, pack assignment queue, multi-package collapsible view
- **Page 9 updated**: Branch info removed (deleted after test packaging), "Branch Age" → "Deployment Age"
- **Branch lifecycle**: All modes now delete branches (test: after packaging; prod/hotfix: after release)
- **Production-from-test (Mode 2)**: Creates new branch from test PackagedComponent, merges to main, packages

### Fixed
- **Python setup script**: Replaced stale `DeployedPackage` references with `ReleaseIntegrationPackStatus`

---

## [0.10.0] - 2026-02-18

### Added

- **Mermaid diagrams throughout documentation**: 8 visual diagrams added — DataHub entity-relationship diagram, Flow 3-swimlane navigation map, process build order graph, phase dependency diagram, deployment modes decision tree, Process E family tree, dev swimlane navigation flow, promotion status lifecycle state machine
- **Process C detailed execution flowchart**: Step-by-step Mermaid flowchart covering branch creation → poll readiness → tilde-syntax promote → strip env config → rewrite references → error handling
- **End-to-end promotion sequence diagram**: Full lifecycle from developer package selection through peer review, admin approval, and deployment
- **Per-type Component XML reference templates**: 13 `<bns:object>` examples in `integration/api-requests/component-types/` covering all promotable component types (process, JSON/XML/flat-file/EDI/DB profiles, connector operations, maps, map scripts, process scripts, process routes, cross-reference tables) plus connections
- **Component API type values reference**: Documented non-obvious API `type` attribute values in CLAUDE.md (e.g., `connector-settings` for connections, `profile.json` for JSON profiles, `scripting` for both map and process scripts)
- **Profile XML generator**: Python generator (`setup/generators/profile_generator.py`) auto-creates Boomi XML profile definitions from JSON profile specs; includes tests
- **Script XML generator**: Python generator (`setup/generators/script_generator.py`) auto-creates Boomi script component XML from Groovy source files; includes tests
- **Diagrams README index**: `docs/diagrams/README.md` cataloging all diagrams with descriptions and locations

### Changed

- **Architecture docs**: Replaced ASCII art with Mermaid diagrams for system overview, data flow, and promotion lifecycle; added status lifecycle state machine
- **Build guide diagrams**: Added process build order, phase dependencies, deployment modes, Process E family, and dev swimlane navigation diagrams to relevant build-step files
- **Setup automation**: Updated all 6 phases for Phase 7 — added extension editor HTTP/DataHub operations (phase 2), processes and scripts step (phase 3), pages (phase 5/6); integrated profile and script generators; updated validator counts to 124 total components
- **API automation guide**: Updated counts and added generator documentation for profile/script XML generation

---

## [0.9.0] - 2026-02-17

### Added

- **Extension Editor (Phase 7)**: Complete environment extension management system enabling developers to view and edit process properties, dynamic process properties, and connection fields across client environments — without direct AtomSphere access
- **ExtensionAccessMapping model**: New DataHub model caching the authorization chain (environment → component → dev account → SSO group) for fast extension access validation; match on `environmentId` + `prodComponentId`; source `PROMOTION_ENGINE`
- **ClientAccountConfig model**: New DataHub model registering client accounts with environment mapping (Test/Prod environment IDs per account); match on `clientAccountId` + `ssoGroupId`; source `ADMIN_CONFIG`
- **Process K (listClientAccounts)**: SSO group → accessible client accounts with Test/Prod environment IDs; admin tier bypasses team check
- **Process L (getExtensions)**: Reads environment extensions + map extension summaries + access mapping data; merges into unified response via `merge-extension-data.groovy`
- **Process M (updateExtensions)**: Saves environment extension changes with partial update semantics; validates access via ExtensionAccessMapping before write
- **Process N (copyExtensionsTestToProd)**: Copies non-connection environment extensions from Test to Prod environment; strips connection and PGP sections via `strip-connections-for-copy.groovy`
- **Process O (updateMapExtension)**: Saves map extension changes (Phase 2 editing; Phase 1 read-only placeholder)
- **5 new FSS message actions**: `listClientAccounts`, `getExtensions`, `updateExtensions`, `copyExtensionsTestToProd`, `updateMapExtension`
- **10 new profiles**: Request/response pairs for all 5 extension editor processes
- **3 new Groovy scripts**: `build-extension-access-cache.groovy` (Process D — builds ExtensionAccessMapping records from extensions + ComponentMapping + DevAccountAccess), `strip-connections-for-copy.groovy` (Process N — removes connections + PGP sections), `merge-extension-data.groovy` (Process L — merges env extensions + map summaries + access data)
- **Environment Extensions API templates**: `get-environment-extensions.xml`, `update-environment-extensions.xml`, `get-map-extensions.xml`, `update-map-extensions.xml`
- **ExtensionEditor custom React component**: TypeScript + Webpack component for Boomi Flow — tabbed interface for process properties, dynamic process properties, and connection fields; inline editing with save/cancel; change tracking and unsaved-changes warnings
- **Page 10 (Extension Manager)**: Client account selector → environment picker → ExtensionEditor component; access-controlled by ExtensionAccessMapping; Test-to-Prod copy button
- **Page 11 (Extension Copy Confirmation)**: Review screen showing diff of extensions to copy from Test to Prod; excludes connections; confirm/cancel actions
- **Build guide Phase 7**: 5 new build-step files — `20-phase7-extension-overview.md`, `21-phase7-extension-processes.md` (Processes K–O), `23-phase7-fss-and-dashboard.md`, `24-phase7-testing.md`, plus updates to `22-api-automation-guide.md`
- **Process D cache refresh**: ExtensionAccessMapping records auto-rebuilt on every successful deployment

### Changed

- **Architecture docs**: Added Extension Editor section covering access control model, cache refresh strategy, and Test-to-Prod copy design
- **Flow structure**: Added Pages 10–11; added 5 message steps; expanded to 11 pages across 3 swimlanes; added extension-related Flow values (`clientAccounts`, `selectedClientAccount`, `selectedEnvironment`, `extensionData`, `extensionChanges`, `copyPreview`)
- **Flow Service spec**: Added 5 extension editor actions (#15–#19); updated action count to 19; added error codes `EXTENSION_ACCESS_DENIED`, `EXTENSION_UPDATE_FAILED`, `COPY_SOURCE_NOT_FOUND`
- **Component counts**: Updated to 124 total — 5 models (+2), 27 HTTP ops (+4), 10 DH ops (+5), 38 profiles (+10), 18 processes (+5), 19 FSS ops (+5), 2 custom components (+1), 11 pages (+2), 10 scripts (+3), 27 API templates (+4)

---

## [0.8.0] - 2026-02-17

### Added

- **Process E5 (withdrawPromotion)**: Initiator-driven withdrawal of pending promotions; deletes promotion branch, sets status to `WITHDRAWN`; only allowed before admin approval; enforces initiator-only access
- **Fail-fast partial promotion policy**: Process C deletes the promotion branch on any individual component failure; only `COMPLETED` or `FAILED` are valid outcomes; `PARTIALLY_COMPLETED` is explicitly not a valid status
- **API alternatives**: curl and PowerShell examples added alongside Boomi HTTP Client instructions in all build guide phases — enables testing API operations without building full processes first
- **51 user stories**: Comprehensive user story document (`docs/user-stories.md`) covering all roles (developer, peer reviewer, admin, operator) and all workflows (promotion, review, deployment, extension editing, mapping management)
- **Contributor FAQ**: `docs/FAQ-contributor.md` with developer-facing answers on setup, workflow, and troubleshooting
- **Team adoption guide**: `docs/team-adoption-guide.md` with rollout planning, training, and change management guidance
- **Python setup automation**: `setup/` directory with Python script automating build guide steps — DataHub model creation, connection/operation setup, profile creation, process scaffolding, Flow Service configuration, Flow dashboard deployment
- **New profiles**: `withdrawPromotion-request.json`, `withdrawPromotion-response.json`
- **New error codes**: `WITHDRAWAL_NOT_ALLOWED`, `PROMOTION_NOT_FOUND`, `INITIATOR_ONLY`

### Changed

- **PromotionLog model**: Added `withdrawnBy`, `withdrawnAt`, `withdrawalReason` fields; added `WITHDRAWN` status
- **Flow Service spec**: Added action #14 (`withdrawPromotion`); added `cancelTestDeployment` pseudo-action (reuses `queryTestDeployments` with cancel flag); documented fail-fast promotion policy
- **Flow structure**: Added withdraw button on Promotion Status page; added `withdrawalReason` Flow value
- **Page 3 (Promotion Status)**: Added "Withdraw" button for pending promotions (visible only to initiator, hidden after admin approval)
- **Process D status gate**: Now explicitly checks for `COMPLETED` or `TEST_DEPLOYED` before merging; rejects any other status
- **Build guide**: Added Build Approach section explaining specification-first methodology; expanded FAQ problem statement with organizational context and connection limit rationale

### Security

- **webpack-dev-server upgraded 4→5**: Resolves CVE-2025-30359 and CVE-2025-30360 in XmlDiffViewer dev dependency

---

## [0.7.0] - 2026-02-16

### Added

- **cancelTestDeployment action**: New FSS pseudo-action reusing Process E4 with cancel flag; `filter-already-promoted.groovy` script excludes test deployments already promoted to production
- **Comprehensive architectural review report**: `docs/architecture-review.md` documenting full system audit findings, remediation actions taken, and remaining recommendations
- **Platform API appendix**: Expanded `docs/build-guide/25-appendix-platform-api.md` with comprehensive endpoint reference, authentication patterns, and error handling examples
- **4 missing HTTP connector operations**: Added `DELETE /Branch`, `POST /MergeRequest`, `PUT /MergeRequest/execute`, `GET /IntegrationPack/query` operations to build guide
- **3 new API request templates**: Branch delete, merge request create, merge request execute

### Fixed

- **Profile field alignment**: All 24 JSON profiles realigned with flow-service-spec field names; added missing fields across request/response pairs
- **API template corrections**: Fixed merge request field name (`branchId` → `sourceBranchId`); added metadata to all JSON API templates
- **Critical script remediation**: Added cache reset logic to `build-visited-set.groovy`; added try/catch blocks to all scripts missing them; fixed case-sensitivity in self-review email comparison; strengthened credential stripping patterns in `strip-env-config.groovy`; corrected branch limit threshold from 18 to 15
- **XmlDiffViewer hooks bug**: Fixed React hooks ordering violation causing intermittent crashes; added error boundary
- **Navigation guards**: Added unsaved-changes warnings to Pages 2, 3, 4, and 6
- **Stale count references**: Corrected BOM counts and inventory across build guide, CLAUDE.md, and API automation guide for 19 HTTP operations

### Changed

- **Build guide restructured for multi-environment**: Integrated multi-env deployment content directly into existing build-step files (Processes C, D, E, J; Flow dashboard pages; testing) instead of standalone Phase 7 file; removed `22-phase7-multi-environment.md`
- **Build guide expanded**: Added tilde syntax and branch operations (ops 13–15) to HTTP client setup; added branch lifecycle to Process C; added merge and branch cleanup to Process D; added multi-env content to Process E, D, J, and testing docs; added multi-env to Flow dashboard pages
- **Documentation completeness**: Added E2/E3 build guide steps that were previously missing; expanded testing documentation with multi-env scenarios

---

## [0.6.0] - 2026-02-16

### Added

- **Multi-environment deployment model**: Three deployment paths — Dev→Test→Production (standard), Dev→Production emergency hotfix (with mandatory justification), and flexible rejection/retry at any stage
- **Page 9 (Production Readiness Queue)**: New developer swimlane page listing test-deployed promotions ready for production; branch age color-coding (green < 14d, amber 15–30d, red > 30d) encourages timely promotion
- **Process E4 (queryTestDeployments)**: Queries PromotionLog for `targetEnvironment="TEST"` AND `status="TEST_DEPLOYED"` records not yet promoted to production
- **Emergency hotfix audit trail**: `isHotfix` and `hotfixJustification` fields on PromotionLog; admin acknowledgment checkbox required before approving hotfix deployments; filterable for leadership reporting
- **Test/production Integration Pack separation**: Packs namespaced with "- TEST" suffix; `packPurpose` filter ("TEST", "PRODUCTION", "ALL") on `listIntegrationPacks`
- **New profiles**: `queryTestDeployments-request.json`, `queryTestDeployments-response.json`
- **New DataHub query template**: `query-test-deployed-promotions.xml` for Process E4
- **New error codes**: `TEST_DEPLOY_FAILED`, `HOTFIX_JUSTIFICATION_REQUIRED`, `INVALID_DEPLOYMENT_TARGET`, `TEST_PROMOTION_NOT_FOUND`
- **New email notifications**: "Test Deployment Complete" (to submitter) and "EMERGENCY HOTFIX — Peer Review Needed" (to dev + admin distribution lists)

### Changed

- **PromotionLog model**: Added 8 fields — `targetEnvironment`, `isHotfix`, `hotfixJustification`, `testPromotionId`, `testDeployedAt`, `testIntegrationPackId`, `testIntegrationPackName`, `promotedFromTestBy`; new statuses `TEST_DEPLOYING`, `TEST_DEPLOYED`, `TEST_DEPLOY_FAILED`
- **Process D (packageAndDeploy)**: Now supports 3 modes — TEST (merge + deploy + preserve branch), PRODUCTION from test (skip merge, content already on main + deploy + delete branch), and PRODUCTION hotfix (merge + deploy + delete branch); request adds `deploymentTarget`, `isHotfix`, `hotfixJustification`, `testPromotionId`, `testIntegrationPackId`, `testIntegrationPackName`; response adds `deploymentTarget`, `branchPreserved`, `isHotfix`
- **Process J (listIntegrationPacks)**: Added `packPurpose` request field; suggestion logic considers target environment
- **Branch lifecycle**: Branches now persist through test→production lifecycle (potentially weeks); branch limit threshold lowered from 18 to 15 for early warning; 30-day advisory warnings in UI
- **Page 3 (Promotion Status)**: Added deployment target radio group — "Deploy to Test" (default, recommended) vs "Deploy to Production (Emergency Hotfix)" with mandatory justification textarea
- **Page 4 (Deployment Submission)**: Three conditional modes — test deployment (blue banner, no reviews, branch preserved), production from test (green banner, test summary panel, peer review flow), emergency hotfix (red warning banner, justification display, peer review flow)
- **Pages 5–6 (Peer Review)**: Added `targetEnvironment` and `isHotfix` badges; hotfix justification displayed prominently on detail page
- **Page 7 (Admin Approval Queue)**: Added environment/hotfix badges; hotfix approvals require explicit acknowledgment checkbox; test deployment history shown when available
- **Flow structure**: Added 8 Flow values (`targetEnvironment`, `isHotfix`, `hotfixJustification`, `testPromotionId`, `testIntegrationPackId`, `testIntegrationPackName`, `testDeployments`, `selectedTestDeployment`); expanded to 9 pages; added message step #12 (`queryTestDeployments`)
- **Flow Service spec**: Added action #12 (`queryTestDeployments`); documented 3 deployment modes for `packageAndDeploy`; added 4 error codes; updated process count to 12
- **Architecture docs**: Added multi-environment deployment model section with branch lifecycle diagrams, Integration Pack strategy, hotfix audit trail
- **Build guide**: Added Phase 7 (`22-phase7-multi-environment.md`) with 8 build steps; updated BOM to ~69 components (12 processes, 24 profiles, 12 FSS operations, 9 pages)

---

## [0.5.0] - 2026-02-16

### Added

- **XmlDiffViewer implementation**: Built the React custom component for Boomi Flow — TypeScript + Webpack 5 production build; 6 sub-components (`DiffToolbar`, `DiffHeader`, `DiffContent`, `CreateView`, `LoadingState`, `ErrorState`), 3 custom hooks (`useResponsive`, `useDiffStats`, `useClipboard`), 4 utility modules; split/unified/create view modes, Prism.js XML syntax highlighting, context collapse, copy buttons, responsive breakpoints; 38 passing tests with 81% coverage; production bundle 64KB gzipped JS + 1.4KB gzipped CSS; React 16 compatibility via CJS alias for `react-diff-viewer-continued`
- **Two-axis SSO authorization model**: Authorization split into two independent axes — **Tier groups** (`ABC_BOOMI_FLOW_ADMIN`, `ABC_BOOMI_FLOW_CONTRIBUTOR`, `ABC_BOOMI_FLOW_READONLY`, `ABC_BOOMI_FLOW_OPERATOR`) control dashboard access level; **Team groups** (`ABC_BOOMI_FLOW_DEVTEAMA`, etc.) control which dev accounts a user can see; tiers resolved at runtime from SSO group names in Process A0, not stored in DataHub
- **Defense-in-depth tier validation**: Process C re-validates the user's tier from `userSsoGroups` before executing promotion; rejects with `INSUFFICIENT_TIER` if below CONTRIBUTOR
- **`INSUFFICIENT_TIER` error code**: Returned when user's SSO groups lack dashboard-access tier

### Changed

- **Process A0 (getDevAccounts)**: Implements tier resolution algorithm — ADMIN bypasses team check (sees all accounts), CONTRIBUTOR filtered by team groups, READONLY/OPERATOR rejected; response now includes `effectiveTier` field
- **executePromotion request**: Added `userSsoGroups` array field for defense-in-depth tier re-validation
- **Flow structure**: SSO group references updated to `ABC_BOOMI_FLOW_*` naming convention; swimlane authorization mapped to specific tier groups; added `userEffectiveTier` Flow value; added "Tier Groups (Dashboard Access)" documentation
- **DevAccountAccess model**: Description updated to document team-specific SSO groups and clarify that tier-level access is resolved at runtime
- **Build guide**: Restructured from single 3,599-line `BUILD-GUIDE.md` into `docs/build-guide/` directory with 22 focused step files plus index; each file self-contained with navigation footers; original file retained as redirect

---

## [0.4.0] - 2026-02-16

### Added

- **Boomi Branching integration**: Process C now promotes components to a temporary branch (not main) using tilde syntax (`Component/{id}~{branchId}`); admin approval merges branch → main via OVERRIDE merge strategy; rejection/denial deletes branch without touching main
- **Side-by-side component diff view**: New Process G (`generateComponentDiff`) fetches branch vs main XML for client-side diff rendering; available on Pages 3, 6, and 7 via "View Diff"/"View New" links
- **XmlDiffViewer custom component**: React component spec (`flow/custom-components/xml-diff-viewer.md`) using `diff`, `react-diff-view`, and `prismjs` for syntax-highlighted side-by-side/unified XML diffs with line numbers, expand/collapse, and copy buttons
- **Integration Pack listing**: New Process J (`listIntegrationPacks`) queries primary account for MULTI-type packs; returns pack list with smart suggestion based on PromotionLog history for same process name
- **Branch API templates**: `create-branch.json`, `create-merge-request.json`, `execute-merge-request.json` for Boomi Branching lifecycle management
- **Integration Pack query template**: `query-integration-packs.xml` for `POST /IntegrationPack/query`
- **XML normalization script**: `normalize-xml.groovy` pretty-prints component XML for consistent line-by-line diff comparison
- **Branch lifecycle management**: 20-branch hard limit enforced (fail at >= 15 with `BRANCH_LIMIT_REACHED`); all terminal paths (approve, reject, deny) delete branch and clear `branchId` in PromotionLog

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

---

## [0.3.0] - 2026-02-16

### Added

- **2-layer approval workflow**: Promotions now pass through two approval gates — peer review then admin review — before deployment
- **Peer Review swimlane**: Third swimlane added to Flow dashboard for peer review functions
- **Process E2 (queryPeerReviewQueue)**: Queries promotions in `PENDING_PEER_REVIEW` status, excluding the requester's own submissions to enforce self-review prevention
- **Process E3 (submitPeerReview)**: Records peer approve/reject decision with reviewer identity, comments, and timestamp; advances approved promotions to `PENDING_ADMIN_REVIEW`
- **Page 5 (Peer Review Queue)**: Data grid of promotions awaiting peer review, filtered to exclude own submissions; SSO-authenticated for developers and admins
- **Page 6 (Peer Review Detail)**: Full promotion detail view with component list, approve/reject actions, required comments on rejection, and client-side self-review guard
- **Peer review JSON profiles**: `queryPeerReviewQueue-request.json`, `queryPeerReviewQueue-response.json`, `submitPeerReview-request.json`, `submitPeerReview-response.json`
- **Executive FAQ**: `docs/FAQ-executive.md` with stakeholder-facing answers on system design, security, and workflow

### Changed

- **PromotionLog model**: Added 8 fields — `peerReviewStatus`, `peerReviewedBy`, `peerReviewedAt`, `peerReviewComments`, `adminReviewStatus`, `adminApprovedBy`, `adminApprovedAt`, `adminComments`; status lifecycle expanded to include `PENDING_PEER_REVIEW`, `PEER_APPROVED`, `PEER_REJECTED`, `PENDING_ADMIN_REVIEW`, `ADMIN_APPROVED`, `ADMIN_REJECTED`
- **Page numbering**: Pages renumbered for 8-page layout — old Approval Queue (5) → Admin Approval Queue (7), old Mapping Viewer (6) → Mapping Viewer (8)
- **Page 4 (Deployment Submission)**: Submission now sets initial status to `PENDING_PEER_REVIEW` instead of `PENDING_APPROVAL`
- **Page 7 (Admin Approval Queue)**: Renamed from "Approval Queue"; now only shows promotions that have passed peer review (`PENDING_ADMIN_REVIEW`)
- **queryStatus (Process E)**: Added `reviewStage` filter parameter to query by approval stage
- **Flow Service spec**: Added actions #8 (`queryPeerReviewQueue`) and #9 (`submitPeerReview`); updated status lifecycle documentation
- **Flow structure**: Expanded from 2 swimlanes to 3; added peer review Flow values (`pendingPeerReviews`, `selectedPeerReview`, `peerReviewerEmail`, `peerReviewerName`); updated navigation map for 9 pages
- **Architecture docs**: Added 2-layer approval workflow section, peer review process descriptions, self-review prevention strategy
- **BUILD-GUIDE.md**: Added peer review build steps, Process E2/E3 configuration, Page 5/6 layout instructions

---

## [0.2.0] - 2026-02-16

### Added

- **Shared connection model**: Connection components are no longer promoted — they are pre-configured once in the parent account's `#Connections` folder and shared across all dev accounts via admin-seeded ComponentMapping records
- **Mirrored folder structure**: Promoted components now mirror the dev account's folder hierarchy under `/Promoted/` instead of flat `/Promoted/{devAccountName}/{processName}/` paths (e.g., dev path `/DevTeamARoot/Orders/MyProcess/` becomes `/Promoted/DevTeamARoot/Orders/MyProcess/`)
- **Pre-promotion connection validation**: New `validate-connection-mappings.groovy` script validates ALL connection mappings exist before promotion begins; fails with complete error report (`MISSING_CONNECTION_MAPPINGS`) if any are missing
- **ADMIN_SEEDING source**: New DataHub source on ComponentMapping model for admin-seeded connection mappings, with `mappingSource` field to distinguish engine-created vs. admin-seeded records
- **Connection seeding UI**: Mapping Viewer (Page 8) now includes dedicated "Seed Connection Mapping" section and `mappingSource` column/filter
- **Promotion Review enhancements**: Connection rows show "(shared)" badge with MAPPED/UNMAPPED status; Promote button disabled when unmapped connections exist
- **Promotion Status updates**: New SKIPPED_CONNECTION/PRE_MAPPED badges; "Connections (Shared)" summary count; reduced credential warning prominence
- **Production package traceability**: `prodPackageId` field on PromotionLog for end-to-end dev→prod package tracking; `create-packaged-component` notes enriched with dev metadata (source account, package, creator, version)

### Changed

- **API templates**: `create-component.xml` and `update-component.xml` use `folderFullPath="/Promoted{devFolderFullPath}"` instead of `/Promoted/{devAccountName}/{processName}/`
- **executePromotion response**: Added `connectionsSkipped` and `missingConnectionMappings` fields
- **resolveDependencies response**: Added `folderFullPath` and `isSharedConnection` to component entries
- **executePromotion request**: Added `folderFullPath` to component entries
- **packageAndDeploy request/response**: Added dev metadata fields (`devAccountId`, `devPackageId`, `devPackageCreator`, `devPackageVersion`); added `prodPackageId` to response
- **listDevPackages response**: Added `createdBy` field
- **queryStatus response**: Added `prodPackageId` field
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
- **Flow dashboard structure** (`/flow/`): Application structure with 3 swimlanes, 9 pages, Flow values, navigation map, email notifications
- **Page layout specs** (`/flow/page-layouts/`): Detailed UI specs for Package Browser, Promotion Review, Promotion Status, Deployment Submission, Approval Queue, Mapping Viewer
- **Architecture reference** (`/docs/architecture.md`): System overview, key design decisions, DataHub models, integration process descriptions, error handling strategy
- **Build guide** (`/docs/BUILD-GUIDE.md`): 6-phase build guide covering DataHub, connections, processes, Flow Service, Flow dashboard, and testing

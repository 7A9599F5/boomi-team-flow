# Changelog

All notable changes to the Boomi Component Promotion System are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

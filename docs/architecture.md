# Boomi Dev-to-Prod Component Promotion System - Architecture

## Problem Statement

Boomi's built-in "Copy Component" creates duplicate components (all Version 1) when copying between accounts. No version continuity, no update-in-place.

## Solution

A Boomi Flow dashboard where devs promote packaged processes from a dev sub-account to the primary account via Platform API, maintaining a single master component with incremental versions. A 2-layer approval workflow (peer review + admin review) gates Integration Pack deployment.

## Architecture Overview

```
┌───────────────────────────────────────────────────────────┐
│                   BOOMI FLOW DASHBOARD                    │
│                                                           │
│  ┌─────────────┐ ┌───────────────┐ ┌──────────────────┐  │
│  │ DEV Swimlane│ │ PEER REVIEW   │ │ ADMIN Swimlane   │  │
│  │ Pkg Browser │ │ Swimlane      │ │ Approval Queue   │  │
│  │ Review      │ │ Review Queue  │ │ Mapping Viewer   │  │
│  │ Status      │ │ Review Detail │ │                  │  │
│  │ Deployment  │ │               │ │                  │  │
│  └──────┬──────┘ └──────┬────────┘ └────────┬─────────┘  │
│         │               │                   │             │
└─────────┼───────────────┼───────────────────┼─────────────┘
          │               │ Message Actions   │
          │ Message       │ (Flow Service)    │ Message
          │ Actions       │                   │ Actions
          ▼               ▼                   ▼
┌───────────────────────────────────────────────────────────┐
│              BOOMI INTEGRATION ENGINE                     │
│              (Public Boomi Cloud Atom)                    │
│                                                           │
│  Process A0: Get Dev Accounts                             │
│  Process A: List Dev Packages                             │
│  Process B: Resolve Dependencies                          │
│  Process C: Execute Promotion                             │
│  Process D: Package & Deploy to IPack                     │
│  Process E: Query Promotion Status                        │
│  Process E2: Query Peer Review Queue                      │
│  Process E3: Submit Peer Review                           │
│  Process F: Mapping CRUD                                  │
│                                                           │
│  ┌──────────────┐    ┌───────────────────┐                │
│  │ HTTP Client  │    │ DataHub Connector │                │
│  │ (Partner API)│    │ (Hub Auth Token)  │                │
│  └──────┬───────┘    └───────┬───────────┘                │
└─────────┼────────────────────┼────────────────────────────┘
          ▼                    ▼
┌──────────────────┐  ┌────────────────────────┐
│ Boomi Platform   │  │ Boomi DataHub          │
│ API              │  │ Repository             │
│ api.boomi.com    │  │                        │
│                  │  │ Model: ComponentMapping │
│ Partner API with │  │ Model: DevAccountAccess │
│ overrideAccount  │  │ Model: PromotionLog    │
└──────────────────┘  └────────────────────────┘
```

## Key Design Decisions

### Why Message Actions (Not Data Actions)
Logic is too complex for simple CRUD — recursive dependency traversal, XML manipulation, reference rewriting. Message Actions give full control over request/response JSON profiles and custom Integration process logic.

### Why Public Boomi Cloud Atom
No firewall issues. Flow → Integration → DataHub all within Boomi's cloud infrastructure.

### Why DataHub (Not External DB)
External databases have 30+ second latency due to firewall/domain limitations. DataHub is accessible without latency when Integration atom is on public Boomi cloud. Match rules provide built-in UPSERT behavior.

### Why Flow Services Server
Single Flow Service component defines the contract. Exposes all 9 processes as Message Actions. Handles connection management, timeout callbacks, and authentication automatically.

### Why Swimlanes for Approval
Built-in Flow authorization containers. Three swimlanes implement a 2-layer approval workflow: Dev swimlane for submission, Peer Review swimlane for first approval gate (any dev or admin except submitter), Admin swimlane for final approval and deployment. SSO group restrictions on each swimlane. Flow pauses at each boundary waiting for the next authenticated user.

### Why 2-Layer Approval (Peer Review + Admin)
Peer review catches process logic and configuration issues that automated checks miss. Self-review prevention enforced at both UI level (Flow business rules on `$User/Email`) and backend level (Process E3 compares `reviewerEmail` with `initiatedBy`). Admins only see promotions that have passed peer scrutiny, reducing their review burden.

## Constraints
- Flow State is temporary/auto-purged — not usable for persistent storage
- Starting fresh — no pre-existing components to seed
- Multiple dev sub-accounts — SSO groups determine access
- Existing private cloud atom handles current work; new public cloud atom for Flow Services
- Azure AD/Entra SSO already configured in Flow
- Partner API enabled on primary account
- Promoted components mirror the dev account's folder structure under `/Promoted/` (e.g., dev path `/DevTeamARoot/Orders/MyProcess/` becomes `/Promoted/DevTeamARoot/Orders/MyProcess/` in primary)
- Connection components are NOT promoted — they are pre-configured once in the parent account under `#Connections` folder and shared across all dev accounts
- Integration Packs: some exist already, system must also create new ones

## DataHub Models

### ComponentMapping
- Purpose: Dev→prod component ID mapping (core persistent data)
- Match: Exact on `devComponentId` AND `devAccountId`
- Sources: PROMOTION_ENGINE (contribute-only), ADMIN_SEEDING (contribute-only, for admin-seeded connection mappings)

### DevAccountAccess
- Purpose: Maps SSO groups to dev account IDs
- Match: Exact on `ssoGroupId` + `devAccountId`
- Source: ADMIN_CONFIG (admin-seeded)

### PromotionLog
- Purpose: Audit trail for each promotion run, including 2-layer approval workflow state
- Match: Exact on `promotionId`
- Source: PROMOTION_ENGINE (writes promotion data + peer/admin review updates)
- Key fields for approval workflow: `peerReviewStatus`, `peerReviewedBy`, `peerReviewedAt`, `peerReviewComments`, `adminReviewStatus`, `adminApprovedBy`, `adminApprovedAt`, `adminComments`

## Integration Processes

| # | Process | Message Action | Purpose |
|---|---------|---------------|---------|
| A0 | Get Dev Accounts | getDevAccounts | Query DevAccountAccess by SSO groups |
| A | List Dev Packages | listDevPackages | Query dev account PackagedComponents |
| B | Resolve Dependencies | resolveDependencies | Recursive dependency traversal + mapping lookup |
| C | Execute Promotion | executePromotion | Read → strip → rewrite refs → create/update |
| D | Package and Deploy | packageAndDeploy | Create PackagedComponent, IPack, deploy |
| E | Query Status | queryStatus | Read PromotionLog from DataHub (supports reviewStage filter) |
| E2 | Query Peer Review Queue | queryPeerReviewQueue | Query PENDING_PEER_REVIEW promotions, exclude own |
| E3 | Submit Peer Review | submitPeerReview | Record peer approve/reject with self-review prevention |
| F | Mapping CRUD | manageMappings | Read/write ComponentMapping records |

## Promotion Engine Logic (Process C)

1. Create PromotionLog (IN_PROGRESS)
2. Sort components bottom-up by type hierarchy (profiles → connections → operations → maps → processes)
3. **Connection Validation Phase:**
   a. Batch query DataHub for all connection mappings for this devAccountId
   b. For each connection in dependency tree, check mapping exists
   c. Collect ALL missing mappings (do not stop on first)
   d. If ANY missing → FAIL with full error report (MISSING_CONNECTION_MAPPINGS)
   e. If ALL found → pre-load into componentMappingCache
4. Filter connections OUT of promotion list
5. For each remaining non-connection component:
   a. GET component XML from dev (with overrideAccount)
   b. Extract folderFullPath from response
   c. Strip environment-specific values (passwords, hosts, URLs, encrypted values)
   d. Rewrite internal references (dev IDs → prod IDs using cache — includes pre-loaded connection mappings)
   e. Construct target path: /Promoted{devFolderFullPath}
   f. CREATE or UPDATE in primary account
   g. On error: mark dependents as SKIPPED
6. Update PromotionLog (COMPLETED/FAILED)
7. Return results (including connectionsSkipped count and any missingConnectionMappings)

## Error Handling
- Per-component failure isolation
- 120ms gap between API calls (~8 req/s, under limit)
- Retry on 429/503: up to 3 retries with exponential backoff
- Concurrency lock via PromotionLog IN_PROGRESS check
- No automated rollback — Boomi maintains version history

## Repository Structure

```
/datahub/           - DataHub model specs and test requests
/integration/       - JSON profiles, Groovy scripts, API templates
/flow/              - Flow dashboard structure and page layouts
/docs/              - Build guide and architecture reference
```

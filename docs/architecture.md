# Boomi Dev-to-Prod Component Promotion System - Architecture

## Problem Statement

Boomi's built-in "Copy Component" creates duplicate components (all Version 1) when copying between accounts. No version continuity, no update-in-place.

## Solution

A Boomi Flow dashboard where devs promote packaged processes from a dev sub-account to the primary account via Platform API, maintaining a single master component with incremental versions. Admin approval gates Integration Pack deployment.

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│            BOOMI FLOW DASHBOARD              │
│                                              │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ DEV Swimlane│  │ ADMIN Swimlane       │  │
│  │ Pkg Browser │  │ Approval Queue       │  │
│  │ Review      │  │ Mapping Viewer       │  │
│  │ Status      │  │                      │  │
│  └──────┬──────┘  └──────────┬───────────┘  │
│         │                    │               │
└─────────┼────────────────────┼───────────────┘
          │ Message Actions    │ Message Actions
          │ (Flow Service)     │ (Flow Service)
          ▼                    ▼
┌──────────────────────────────────────────────┐
│         BOOMI INTEGRATION ENGINE             │
│         (Public Boomi Cloud Atom)            │
│                                              │
│  Process A0: Get Dev Accounts                │
│  Process A: List Dev Packages                │
│  Process B: Resolve Dependencies             │
│  Process C: Execute Promotion                │
│  Process D: Package & Deploy to IPack        │
│  Process E: Query Promotion Status           │
│  Process F: Mapping CRUD                     │
│                                              │
│  ┌──────────────┐    ┌───────────────────┐   │
│  │ HTTP Client  │    │ DataHub Connector │   │
│  │ (Partner API)│    │ (Hub Auth Token)  │   │
│  └──────┬───────┘    └───────┬───────────┘   │
└─────────┼────────────────────┼───────────────┘
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
Single Flow Service component defines the contract. Exposes all 7 processes as Message Actions. Handles connection management, timeout callbacks, and authentication automatically.

### Why Swimlanes for Approval
Built-in Flow authorization containers. Dev swimlane for submission, Admin swimlane for approval. SSO group restrictions. Flow pauses waiting for approver.

## Constraints
- Flow State is temporary/auto-purged — not usable for persistent storage
- Starting fresh — no pre-existing components to seed
- Multiple dev sub-accounts — SSO groups determine access
- Existing private cloud atom handles current work; new public cloud atom for Flow Services
- Azure AD/Entra SSO already configured in Flow
- Partner API enabled on primary account
- Promoted components go to `/Promoted/{DevTeamName}/{ProcessName}/`
- Integration Packs: some exist already, system must also create new ones

## DataHub Models

### ComponentMapping
- Purpose: Dev→prod component ID mapping (core persistent data)
- Match: Exact on `devComponentId` AND `devAccountId`
- Source: PROMOTION_ENGINE (contribute-only)

### DevAccountAccess
- Purpose: Maps SSO groups to dev account IDs
- Match: Exact on `ssoGroupId` + `devAccountId`
- Source: ADMIN_CONFIG (admin-seeded)

### PromotionLog
- Purpose: Audit trail for each promotion run
- Match: Exact on `promotionId`
- Source: PROMOTION_ENGINE

## Integration Processes

| # | Process | Message Action | Purpose |
|---|---------|---------------|---------|
| A0 | Get Dev Accounts | getDevAccounts | Query DevAccountAccess by SSO groups |
| A | List Dev Packages | listDevPackages | Query dev account PackagedComponents |
| B | Resolve Dependencies | resolveDependencies | Recursive dependency traversal + mapping lookup |
| C | Execute Promotion | executePromotion | Read → strip → rewrite refs → create/update |
| D | Package and Deploy | packageAndDeploy | Create PackagedComponent, IPack, deploy |
| E | Query Status | queryStatus | Read PromotionLog from DataHub |
| F | Mapping CRUD | manageMappings | Read/write ComponentMapping records |

## Promotion Engine Logic (Process C)

1. Create PromotionLog (IN_PROGRESS)
2. Sort components bottom-up by type hierarchy (profiles → connections → operations → maps → processes)
3. For each component:
   a. GET component XML from dev (with overrideAccount)
   b. Strip environment-specific values (passwords, hosts, URLs, encrypted values)
   c. Rewrite internal references (dev IDs → prod IDs using in-memory mapping cache)
   d. Check DataHub mapping → CREATE (no mapping) or UPDATE (mapping exists)
   e. POST to primary account → write/update DataHub mapping
   f. On error: mark dependents as SKIPPED
4. Update PromotionLog (COMPLETED/FAILED)
5. Return results

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

# Boomi Component Promotion System — Build Guide

This guide walks through building every component of the Promotion System step by step. Follow the phases in order — each phase builds on the previous.

## How to Use This Guide

- **Linear build**: Follow Phases 1-6 sequentially for a first-time build
- **Reference lookup**: Jump to a specific phase/step using the table of contents
- **Validation**: Every major step ends with a "**Verify:**" checkpoint — do not skip these
- **API examples**: All verification commands are shown in both `curl` (Linux/macOS) and PowerShell (Windows) formats
- **File references**: Templates, profiles, and scripts are in this repository — the guide shows HOW to use them, not duplicates of their content

---

## Prerequisites

- Primary Boomi account with Partner API enabled
- One or more dev sub-accounts (children of the primary account)
- Azure AD/Entra SSO configured in Boomi Flow
- Access to DataHub in your Boomi account
- A public Boomi cloud atom (or ability to provision one)
- API token generated at **Settings → Account Information → Platform API Tokens**

---

## Bill of Materials

The system comprises **57 components** across 6 phases:

| Phase | Category | Count | Components |
|-------|----------|-------|------------|
| 1 | DataHub Models | 3 | ComponentMapping, DevAccountAccess, PromotionLog (26 fields incl. peer/admin review + branching) |
| 2 | Connections | 2 | HTTP Client (Partner API), DataHub |
| 2 | HTTP Client Operations | 12 | GET/POST/QUERY for Component, Reference, Metadata, Package, Deploy, IntegrationPack; Branch (create, query), MergeRequest (create, execute) |
| 2 | DataHub Operations | 6 | Query + Update for each of 3 models |
| 3 | JSON Profiles | 22 | Request + Response for each of 11 processes |
| 3 | Integration Processes | 11 | A0, A, B, C, D, E, E2, E3, F, G, J |
| 4 | FSS Operations | 11 | One per process |
| 4 | Flow Service | 1 | PROMO - Flow Service |
| 5 | Custom Component | 1 | XmlDiffViewer (React diff viewer for Flow custom player) |
| 5 | Flow Connector | 1 | Promotion Service Connector |
| 5 | Flow Application | 1 | Promotion Dashboard (3 swimlanes, 8 pages) |
| | **Total** | **64** | |

---

## Component Naming Convention

All Integration components use the `PROMO - ` prefix followed by a type-specific pattern:

| Type | Pattern | Example |
|------|---------|---------|
| Connection | `PROMO - {Description} Connection` | `PROMO - Partner API Connection` |
| HTTP Operation | `PROMO - HTTP Op - {Method} {Resource}` | `PROMO - HTTP Op - GET Component` |
| DataHub Operation | `PROMO - DH Op - {Action} {Model}` | `PROMO - DH Op - Query ComponentMapping` |
| JSON Profile | `PROMO - Profile - {Action}{Request\|Response}` | `PROMO - Profile - ExecutePromotionRequest` |
| Process | `PROMO - {Description}` | `PROMO - Execute Promotion` |
| FSS Operation | `PROMO - FSS Op - {ActionName}` | `PROMO - FSS Op - ExecutePromotion` |
| Flow Service | `PROMO - Flow Service` | |

DataHub models and Flow components use plain names without the prefix.

---

## Dependency Build Order

Build phases in order — each depends on the previous:

```
Phase 1: DataHub Models
    └── Phase 2: Connections & Operations (need DataHub for DH operations)
            └── Phase 3: Integration Processes (need connections, operations, profiles)
                    └── Phase 4: Flow Service (links processes to message actions)
                            └── Phase 5: Flow Dashboard (calls Flow Service via connector)
                                    └── Phase 6: Testing (validates entire stack)
```

Within Phase 3, build processes in this order (simplest → most complex):

```
F (Mapping CRUD) → A0 (Get Dev Accounts) → E (Query Status) → E2 (Query Peer Review Queue) → E3 (Submit Peer Review) → J (List Integration Packs) → G (Generate Component Diff) → A (List Packages) → B (Resolve Dependencies) → C (Execute Promotion) → D (Package & Deploy)
```

---

## Repository File Reference

| Directory | Contents | Used In |
|-----------|----------|---------|
| `/datahub/models/` | DataHub model specifications (3 JSON files) | Phase 1 |
| `/datahub/api-requests/` | Test XML for DataHub CRUD validation (2 files) | Phase 1, 6 |
| `/integration/profiles/` | JSON request/response profiles (22 files, 11 processes × 2) | Phase 3 |
| `/integration/scripts/` | Groovy scripts for XML manipulation (6 files) | Phase 3 |
| `/integration/api-requests/` | API request templates (13 files) | Phase 2, 3 |
| `/integration/flow-service/` | Flow Service component specification | Phase 4 |
| `/flow/` | Flow app structure and page layouts (9 files) | Phase 5 |
| `/docs/` | This guide and architecture reference | All |

---

---
Next: [Phase 1: DataHub Foundation](01-datahub-foundation.md) | [Back to Index](index.md)

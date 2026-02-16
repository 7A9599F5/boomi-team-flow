# Frequently Asked Questions — Executive Overview

This FAQ is written for managers and directors who may have limited familiarity with Boomi. It covers what this project is, why it exists, and what to expect.

---

## The Basics

### What is Boomi?

Boomi is a cloud-based integration platform (iPaaS — Integration Platform as a Service). Our organization uses it to connect systems, move data between applications, and automate business processes. Think of it as the plumbing between our software systems. Developers build integration "processes" in Boomi that run on a cloud runtime called an Atom.

### What problem does this project solve?

Today, when a developer finishes building an integration in their development account and it needs to go to production, Boomi's built-in copy tool creates a brand-new duplicate. Every copy starts over at Version 1 with no history, no link back to the original, and no way to push updates to the same component later. If a developer makes a fix, they have to copy the whole thing again — creating yet another duplicate.

This means production fills up with orphaned copies, there is no version trail, and no structured approval process before code reaches production.

### What does this system do instead?

It gives developers a self-service web dashboard where they:

1. **Pick** a packaged process from their dev account
2. **Review** all its dependencies (sub-processes, data maps, connection references, etc.)
3. **Promote** it to production — the system creates the component if it's new, or updates the existing one in place with a new version number
4. **Submit** the promoted component for packaging and deployment, which routes to an admin for approval

The result is a single master copy of every component in production with a clean version history, full audit trail, and an admin approval gate before anything goes live.

### Who uses this system?

Two groups:

- **Developers** — browse their packages, promote to production, submit for deployment
- **Admins** — review and approve (or deny) deployment requests, manage component mappings between dev and prod accounts

Access is controlled through existing Azure AD / Entra SSO groups, so no new credentials are needed.

---

## Architecture & Technology

### What technology does this use?

Everything is built entirely within the Boomi platform — no external servers, databases, or custom code outside of Boomi:

| Layer | Boomi Feature | Purpose |
|-------|--------------|---------|
| User interface | **Boomi Flow** | The web dashboard developers and admins use |
| Backend logic | **Boomi Integration** (9 processes) | Orchestrates the promotion workflow, API calls, peer review, and data transformations |
| Data storage | **Boomi DataHub** (3 data models) | Stores component mappings, access control lists, and audit logs |
| API communication | **Boomi Platform API** (Partner API) | Reads and writes components between accounts |

### Why not use an external database or custom application?

- **Latency:** External databases accessed from Boomi's cloud have 30+ second response times due to firewall and network routing. DataHub, being inside Boomi's infrastructure, responds instantly.
- **Maintenance:** No additional servers to patch, monitor, or pay for. No separate application to deploy or secure.
- **Licensing:** Everything uses features already included in our Boomi license.

### What is a "Public Boomi Cloud Atom"?

An Atom is the Boomi runtime engine that executes integration processes. A "public cloud" Atom runs inside Boomi's own cloud infrastructure (as opposed to behind our firewall). Since both the Flow dashboard and DataHub also live in Boomi's cloud, keeping the Atom there eliminates network complexity and firewall rules. It runs alongside — not replacing — our existing private Atom.

### Does this replace any existing systems?

No. This adds a new capability. Existing integrations running on our private Atom are unaffected. This system runs on a separate public cloud Atom dedicated to the promotion workflow.

---

## Workflow & Process

### What does the promotion workflow look like end-to-end?

```
Developer selects a package in their dev account
        |
        v
System resolves all dependencies (sub-processes, maps, profiles, etc.)
        |
        v
Developer reviews what will be promoted (new vs. update) and any shared connections
        |
        v
Developer clicks "Promote" — system copies each component to production,
maintaining existing versions and rewriting internal cross-references
        |
        v
Developer submits for Integration Pack deployment
        |
        v
Admin receives email notification
        |
        v
Admin reviews and approves (or denies) in the dashboard
        |
        v
On approval: system packages and deploys to the production environment
```

### What is an "Integration Pack" and why does it need approval?

An Integration Pack is Boomi's mechanism for bundling multiple related components into a single deployable unit. Deploying an Integration Pack makes the processes live — meaning they will start handling real data. Because of this impact, an admin must review and approve before deployment occurs.

### How are connections (database credentials, API keys, etc.) handled?

Connections are **never** promoted. Sensitive configuration like database passwords, API endpoints, and credentials must be different between dev and prod. Instead:

1. An admin pre-configures the production connection once in a shared folder
2. The admin creates a "mapping" record that links the dev connection ID to the prod connection ID
3. During promotion, the system automatically swaps references — dev connection IDs are replaced with their prod equivalents

If any required connection mapping is missing, the promotion is blocked with a clear error message listing exactly which mappings need to be created. No partial promotions occur.

### What is a "component mapping"?

Every Boomi component has a unique ID. When a dev component is promoted to production for the first time, a new prod component is created with its own ID. The mapping record links these two IDs together so that future promotions update the same prod component instead of creating another duplicate. Mappings are stored permanently in DataHub and are created automatically during promotion (or manually by admins for connections).

### Can multiple developers promote at the same time?

The system uses a concurrency lock. If a promotion is already in progress, a second attempt will be blocked until the first completes. This prevents conflicting writes to production.

---

## Security & Compliance

### Who can access what?

Access is governed by Azure AD / Entra SSO groups:

- **"Boomi Developers" group** — can browse packages and promote from their authorized dev accounts only
- **"Boomi Admins" group** — can approve deployments and manage component mappings
- Developers can only see dev accounts their SSO group is linked to (configured by admins in the DevAccountAccess model)

### Is there an audit trail?

Yes. Every promotion creates a **PromotionLog** record in DataHub that captures:

- Who initiated the promotion (SSO user)
- When it happened
- Which components were promoted (created, updated, failed, skipped)
- The promotion status (in-progress, completed, failed)
- The production package ID and version (after deployment)

These records are permanent and queryable.

### Are credentials or secrets ever exposed?

No. The promotion engine actively strips environment-specific data (passwords, hostnames, URLs, encrypted values) from component XML before writing to production. Connections are never copied — only references are rewritten to point to pre-configured production connections.

### What happens if something goes wrong during promotion?

- **Per-component isolation:** If one component fails, the others still complete. Failed components and anything that depends on them are marked as skipped.
- **No automated rollback needed:** Boomi maintains its own version history for every component. If a bad version is promoted, the previous version still exists and can be restored manually through Boomi's standard UI.
- **Rate limiting:** The system spaces API calls to stay under Boomi's rate limits (8 requests/second) and retries automatically on temporary failures.

---

## Scope & Effort

### How big is this project?

The system comprises **51 Boomi components** built across 6 phases:

| Phase | What Gets Built | Components |
|-------|----------------|------------|
| 1 | Data models in DataHub | 3 |
| 2 | API connections and operations | 17 |
| 3 | Integration processes and data profiles | 21 |
| 4 | Flow Service (API layer) | 8 |
| 5 | Flow dashboard (UI) | 2 |
| 6 | End-to-end testing | — |

Phases are sequential — each builds on the previous.

### Does this require any new licenses or infrastructure purchases?

No. The system uses Boomi Flow, Integration, DataHub, and Platform API — all features within the existing Boomi platform. The only new infrastructure is a public cloud Atom, which is provisioned within Boomi at no additional cost (subject to your account's Atom allocation).

### What are the dependencies / prerequisites?

- Partner API must be enabled on the primary Boomi account
- At least one dev sub-account must exist
- Azure AD / Entra SSO must be configured in Boomi Flow (already in place)
- DataHub must be accessible in the account
- A public cloud Atom must be provisioned (or already available)

---

## Risks & Considerations

### What are the main risks?

| Risk | Mitigation |
|------|-----------|
| Boomi Platform API changes or rate limit changes | System uses documented, stable Partner API endpoints; rate limiting is configurable |
| Accidental promotion of broken code | Admin approval gate prevents deployment; promotion itself doesn't make anything live |
| Lost component mappings | Mappings are stored in DataHub with match rules that prevent duplicates; they persist indefinitely |
| Developer promotes to wrong account | Developers can only see accounts linked to their SSO group; production account is a fixed system-level configuration |

### What does this NOT do?

- **Does not replace Boomi's native deployment mechanisms** — it adds a structured promotion layer on top of them
- **Does not handle rollbacks automatically** — Boomi's built-in version history serves this purpose
- **Does not promote connections** — these are managed separately by admins for security
- **Does not run scheduled/batch promotions** — all promotions are initiated manually by a developer through the dashboard
- **Does not support promoting between two dev accounts** — flow is always dev-to-production

### What happens if we need to change the workflow later?

Because everything is built with standard Boomi components (processes, Flow pages, DataHub models), modifications follow the same patterns as any other Boomi development. Adding a new approval step, changing the UI layout, or modifying business rules can all be done through Boomi's existing drag-and-drop builders.

---

## Glossary

| Term | Meaning |
|------|---------|
| **Atom** | Boomi's runtime engine that executes integration processes |
| **Component** | Any buildable item in Boomi — a process, connection, data map, profile, etc. |
| **DataHub** | Boomi's master data management feature, used here as a lightweight database |
| **Flow** | Boomi's low-code web application builder (the dashboard UI) |
| **Integration Pack** | A bundle of related Boomi components that can be deployed as a single unit |
| **iPaaS** | Integration Platform as a Service — a cloud service for connecting applications |
| **Message Action** | A named API endpoint within a Boomi Flow Service that triggers a backend process |
| **Packaged Component** | A versioned, immutable snapshot of a Boomi component ready for deployment |
| **Partner API** | Boomi's management API that allows programmatic control of components and deployments |
| **Platform API** | Same as Partner API — the REST API for managing Boomi account resources |
| **Promotion** | The act of copying a component from a dev account to production while preserving version history |
| **SSO** | Single Sign-On — users log in once via Azure AD and are authenticated across systems |
| **Swimlane** | A section of a Flow application restricted to users with specific authorization |

# Frequently Asked Questions — Executive Overview

This FAQ is written for managers and directors who may have limited familiarity with Boomi. It covers what this project is, why it exists, and what to expect.

---

## The Basics

### What is Boomi?

Boomi is a cloud-based integration platform (iPaaS — Integration Platform as a Service). Our organization uses it to connect systems, move data between applications, and automate business processes. Think of it as the plumbing between our software systems. Developers build integration "processes" in Boomi that run on a cloud runtime called an Atom.

### What problem does this project solve?

Today, all integration development is performed directly in the primary (production) Boomi account by a small team of Boomi Admins. There is no separation between development and production environments, no structured handoff process, and no self-service path for other teams — integration, technical, and tools teams within Operations — to build and promote their own work. This creates a resource bottleneck: the admin team handles every build and deployment request, which limits throughput and leaves the broader Boomi platform underutilized relative to what the organization is paying for.

Granting additional users direct access to the primary account is also impractical. The primary account has a fixed limit on deployed connections, and that limit cannot be easily increased. Developer accounts, by contrast, can have their connection limits raised freely and on demand — making them the natural place for teams to build and test without competing for constrained production resources.

Provisioning a new dev account is trivial — it takes minutes and requires no additional infrastructure or licensing. The barrier is not setup cost; it is the lack of a structured promotion path from dev to production. Boomi's built-in copy tool creates a brand-new duplicate every time. Each copy starts at Version 1 with no history, no link back to the original, and no way to push updates to the same component later. If a developer makes a fix, they must copy the entire component again, creating yet another duplicate. Over time, production fills up with orphaned copies, there is no version trail, and there is no structured approval process before changes reach production.

### What does this system do instead?

It removes the admin bottleneck by giving each development team a self-service web dashboard where they own their integration lifecycle end-to-end. Teams work freely in their own dev accounts and promote to production through the dashboard:

1. **Pick** a packaged process from their dev account
2. **Review** all its dependencies (sub-processes, data maps, connection references, etc.)
3. **Promote** it to production — the system creates the component if it's new, or updates the existing one in place with a new version number
4. **Submit** the promoted component for packaging and deployment, which routes to an admin for approval

The result is a single master copy of every component in production with a clean version history, full audit trail, and an admin approval gate before anything goes live — while freeing the admin team to focus on higher-value work instead of routine build-and-deploy requests.

### Who uses this system?

Three groups:

- **Developers** — browse their packages, promote to test and production, submit for deployment
- **Peer Reviewers** (other developers) — review and approve (or reject) promotions they did not submit themselves
- **Admins** — final approval authority for production deployments, manage component mappings between dev and prod accounts

Access is controlled through existing Azure AD / Entra SSO groups, so no new credentials are needed.

---

## Architecture & Technology

### What technology does this use?

Everything is built entirely within the Boomi platform — no external servers, databases, or custom code outside of Boomi:

| Layer | Boomi Feature | Purpose |
|-------|--------------|---------|
| User interface | **Boomi Flow** | The web dashboard developers and admins use |
| Backend logic | **Boomi Integration** (12 processes) | Orchestrates the promotion workflow, API calls, peer review, and data transformations |
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

The standard path goes through a test environment before production:

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
Developer reviews side-by-side XML diff of changes (branch vs. production)
        |
        v
Developer clicks "Promote" — system copies each component to a temporary
branch, maintaining existing versions and rewriting internal cross-references
        |
        v
Developer deploys to Test environment (no reviews required)
        |
        v
Developer validates in test, then initiates production promotion
        |
        v
A peer developer reviews and approves (cannot review their own submission)
        |
        v
An admin reviews and approves (or denies) in the dashboard
        |
        v
On approval: system packages and deploys to the production environment
```

An **emergency hotfix** path (Dev → Production) is also available when a critical fix must skip the test environment. Hotfixes still require both peer review and admin approval, plus a mandatory written justification that is logged for leadership audit.

### What is an "Integration Pack" and why does it need approval?

An Integration Pack is Boomi's mechanism for bundling multiple related components into a single deployable unit. Deploying an Integration Pack makes the processes live — meaning they will start handling real data. The system uses separate Integration Packs for test and production environments. Test deployments can proceed without reviews, but production deployment requires both a peer review and an admin approval before it occurs.

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

Access is governed by a **two-axis SSO model** using Azure AD / Entra groups:

**Axis 1 — Tier groups** control what level of dashboard access a user has:

- **ADMIN tier** — full access to all dashboard pages, including production approval and component mapping management
- **CONTRIBUTOR tier** — access to developer and peer review pages; can promote, submit, and review others' work
- **READONLY / OPERATOR tiers** — no dashboard access (Boomi AtomSphere access only)

**Axis 2 — Team groups** control which dev accounts a user can see:

- Each development team has its own SSO group (e.g., "Boomi Flow DevTeamA")
- A developer only sees the dev accounts linked to their team group(s)
- Admins bypass the team filter and can see all accounts

This separation means you can add a developer to a new team's accounts without changing their dashboard role, or promote someone to admin without modifying their team assignments.

### Is there an audit trail?

Yes. Every promotion creates a **PromotionLog** record in DataHub that captures:

- Who initiated the promotion (SSO user)
- When it happened
- Which components were promoted (created, updated, failed, skipped)
- The target environment (test or production)
- Whether it was an emergency hotfix (with written justification)
- Who performed the peer review (and their decision)
- Who performed the admin review (and their decision)
- The production package ID and version (after deployment)
- A link between the test deployment and the subsequent production deployment

These records are permanent and queryable. Emergency hotfixes are flagged with `isHotfix` and include the developer's written justification, making them easy to filter for leadership reporting.

### Are credentials or secrets ever exposed?

No. The promotion engine actively strips environment-specific data (passwords, hostnames, URLs, encrypted values) from component XML before writing to production. Connections are never copied — only references are rewritten to point to pre-configured production connections.

### What happens if something goes wrong during promotion?

- **Per-component isolation:** If one component fails, the others still complete. Failed components and anything that depends on them are marked as skipped.
- **No automated rollback needed:** Boomi maintains its own version history for every component. If a bad version is promoted, the previous version still exists and can be restored manually through Boomi's standard UI.
- **Rate limiting:** The system spaces API calls to stay under Boomi's rate limits (8 requests/second) and retries automatically on temporary failures.

---

## Scope & Effort

### How big is this project?

The system comprises approximately **69 Boomi components** built across 7 phases:

| Phase | What Gets Built | Components |
|-------|----------------|------------|
| 1 | Data models in DataHub | 3 |
| 2 | API connections and operations | 17 |
| 3 | Integration processes and data profiles | 24 |
| 4 | Flow Service (API layer) | 12 |
| 5 | Flow dashboard (9 pages) + custom diff viewer component | 3 |
| 6 | End-to-end testing | — |
| 7 | Multi-environment deployment (test → production pipeline) | 10 |

Phases are sequential — each builds on the previous. There is also a custom React component (the XML diff viewer) that is built separately and uploaded to the Flow dashboard.

### Does this require any new licenses or infrastructure purchases?

No. The system uses Boomi Flow, Integration, DataHub, and Platform API — all features within the existing Boomi platform. The only new infrastructure is a public cloud Atom, which is provisioned within Boomi at no additional cost (subject to your account's Atom allocation).

### What are the dependencies / prerequisites?

- Partner API must be enabled on the primary Boomi account
- At least one dev sub-account must exist
- Azure AD / Entra SSO must be configured in Boomi Flow (already in place), with tier and team groups defined
- DataHub must be accessible in the account
- A public cloud Atom must be provisioned (or already available)
- At least one test environment configured in the primary account (for the test deployment path)

---

## Risks & Considerations

### What are the main risks?

| Risk | Mitigation |
|------|-----------|
| Boomi Platform API changes or rate limit changes | System uses documented, stable Partner API endpoints; rate limiting is configurable |
| Accidental promotion of broken code | Test environment validates before production; peer review + admin approval gates prevent untested code from going live |
| Lost component mappings | Mappings are stored in DataHub with match rules that prevent duplicates; they persist indefinitely |
| Developer promotes to wrong account | Developers can only see accounts linked to their SSO team group; production account is a fixed system-level configuration |
| Emergency hotfix bypasses test environment | Both peer review and admin approval are still required; mandatory written justification is logged; admins must explicitly acknowledge the bypass |
| Stale promotion branches accumulate | Dashboard shows branch age warnings (amber at 15 days, red at 30 days); Boomi's 20-branch limit is monitored with early warnings at 15 |

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
| **Promotion Branch** | A temporary workspace in Boomi where promoted components are staged before merging to main; enables side-by-side diff review |
| **SSO** | Single Sign-On — users log in once via Azure AD and are authenticated across systems |
| **Swimlane** | A section of a Flow application restricted to users with specific authorization |
| **Target Environment** | Where a promoted component will be deployed — either Test (for validation) or Production (for live use) |
| **Tier Group** | An SSO group that controls a user's dashboard access level (Admin, Contributor, Readonly, Operator) |
| **Team Group** | An SSO group that controls which dev accounts a user can see (e.g., DevTeamA, DevTeamB) |

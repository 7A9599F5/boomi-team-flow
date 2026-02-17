# Frequently Asked Questions — Contributor Guide

This FAQ is written for Contributors — developers who use the Promotion Dashboard to promote components from dev to production. If you're looking for an executive overview of what this system is, see [FAQ-executive.md](FAQ-executive.md).

---

## Quick Reference

| Topic | Key Info |
|-------|----------|
| Dashboard access groups | `ABC_BOOMI_FLOW_CONTRIBUTOR` (tier) + `ABC_BOOMI_FLOW_DEVTEAM*` (team) |
| Pages you'll use | Page 1: Package Browser, Page 2: Promotion Review, Page 3: Promotion Status, Page 4: Deployment Submission, Page 9: Production Readiness Queue |
| Pages you can review on | Page 5: Peer Review Queue, Page 6: Peer Review Detail |
| Active branch limit | 15 (system warns), 20 (Boomi hard limit) |
| Self-review | Not allowed — blocked at UI and backend |
| Browser crashes | Safe — backend runs independently; session restores from cache |
| First-time setup | Contact your Boomi Admin — they must seed DevAccountAccess and connection mappings |
| Escalation path | Access issues → Azure AD admin; Mapping issues → Boomi Admin; System failures → Boomi Admin |

---

## Getting Started

### How do I get access to the Promotion Dashboard?

You need two SSO groups in Azure AD/Entra: (1) `ABC_BOOMI_FLOW_CONTRIBUTOR` — your "access badge" that unlocks the dashboard, and (2) at least one `ABC_BOOMI_FLOW_DEVTEAM*` group (e.g., `ABC_BOOMI_FLOW_DEVTEAMA`) — controls which dev accounts you can see. Contact your admin to get both assigned. Neither group alone is enough.

### What is the difference between `CONTRIBUTOR` and `DEVTEAM` groups?

They control different things. `ABC_BOOMI_FLOW_CONTRIBUTOR` is a tier group — it grants you dashboard access. The `DEVTEAM` group (e.g., `DEVTEAMA`, `DEVTEAMB`) is a team group — it determines which dev accounts appear in your dropdown. You must be in both. Admins have `ABC_BOOMI_FLOW_ADMIN` instead of `CONTRIBUTOR` and can see all accounts regardless of team group.

### I have `ABC_BOOMI_FLOW_READONLY` — can I use the dashboard?

No. `READONLY` and `OPERATOR` tiers have no dashboard access at all. You can work in Boomi AtomSphere directly, but the promotion workflow requires `CONTRIBUTOR` or `ADMIN` tier. Contact your admin to get the right group.

### Where do I find the dashboard URL?

Your Boomi Admin configures and publishes the Flow application URL. It is not auto-generated. Ask your admin for the URL.

### I get an "Access Denied" error when I log in — what's wrong?

The `getDevAccounts` call returned `INSUFFICIENT_TIER`. Your SSO groups don't include `ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN`. Contact your Azure AD admin or Boomi Admin to get the correct tier group assigned.

### I only see one dev account in the dropdown — is something wrong?

No, this is by design. If your team group maps to exactly one dev account in DataHub, the system auto-selects it and loads the package list immediately. You won't see a dropdown at all, which reduces friction.

### What do I need before my first promotion?

Before your first promotion, confirm with your Boomi Admin that all of these are in place:

1. You're in `ABC_BOOMI_FLOW_CONTRIBUTOR` (or ADMIN) in Azure AD
2. You're in an `ABC_BOOMI_FLOW_DEVTEAM*` group linked to your dev account
3. A DevAccountAccess record in DataHub links your team group to your dev account ID
4. You have at least one PackagedComponent in your dev account (packaged via Boomi AtomSphere)
5. Any shared connections your processes use have been pre-mapped by an admin in ComponentMapping
6. You have the dashboard URL

---

## The Promotion Workflow

### What are all the steps to promote a component to production?

The standard path (test → production):

1. **Page 1** — Select a packaged process from your dev account
2. **Page 2** — Review the resolved dependency tree (what's new vs. update, any unmapped connections)
3. **Page 2 → Page 3** — Click "Execute Promotion" — components are promoted to a temporary branch (30–120 seconds)
4. **Page 4** — Deploy to your test Integration Pack (no reviews needed)
5. **Page 9** — When ready, select the test deployment and click "Promote to Production"
6. **Page 4** — Select a production Integration Pack, add deployment notes, and submit for peer review
7. A colleague reviews your promotion on Pages 5–6
8. An admin approves and deploys to production (Admin Approval Queue, Page 7)

The emergency hotfix path skips steps 4–5 but still requires peer review and admin approval.

### What exactly does "promote" do?

It copies components from your dev account into a temporary staging branch (`promo-{promotionId}`) inside the production account. Nothing touches the production main branch directly. Sensitive values (passwords, hostnames, URLs) are stripped from component XML, and all internal references are rewritten to use production component IDs. Only after both peer and admin approval does the branch merge to main.

### Can I close my browser while a promotion is running?

Yes. The Integration process runs asynchronously on Boomi's cloud and continues regardless of what your browser does. The dashboard uses IndexedDB to cache your session state every 30 seconds. When you return to the same URL, it restores your session and shows the promotion result. Avoid incognito/private browsing windows, as IndexedDB is disabled there — use a regular browser window.

### How long does a promotion take?

For fewer than 50 components, expect under 10 minutes. Larger dependency trees take longer. The dependency resolution step (before promotion) takes 5–15 seconds. You can leave the tab open to watch status update, or close the browser and check back later.

### What happens after I deploy to test?

Your test deployment branch is preserved (not deleted). The status becomes `TEST_DEPLOYED` and the promotion appears in Page 9 (Production Readiness Queue). When you're ready, navigate to Page 9, select your entry, and click "Promote to Production" to start the production review process. The production path does not re-promote from dev — it uses the content already validated in test.

### Can I skip the test deployment and go straight to production?

Yes, but only via the Emergency Hotfix path. On Page 3, select "Deploy to Production (Emergency Hotfix)" and provide a mandatory written justification (up to 1000 characters). You still need both peer review and admin approval — hotfix only skips the test environment step, not the approval gates.

---

## Promotion Statuses

### What do all the status values mean?

| Status | Meaning |
|--------|---------|
| `IN_PROGRESS` | Promotion is currently running (Process C executing) |
| `COMPLETED` | Branch creation succeeded — no deployment yet |
| `FAILED` | Promotion failed; branch deleted; production unchanged |
| `TEST_DEPLOYED` | Components deployed to test Integration Pack; branch preserved |
| `TEST_CANCELLED` | You cancelled the test deployment; branch deleted |
| `PENDING_PEER_REVIEW` | Submitted for peer review; awaiting a colleague's decision |
| `PENDING_ADMIN_REVIEW` | Peer approved; awaiting admin approval and deployment |
| `DEPLOYED` | Approved and deployed to production — complete |
| `WITHDRAWN` | You retracted the promotion before reviews completed |

### Can a promotion be partially successful?

No. The system uses a fail-fast policy — if any single component fails, the entire promotion branch is deleted and the status is `FAILED`. Nothing is left in a partial state. The error page shows per-component results so you can see which component caused the failure.

### My promotion has been in `PENDING_PEER_REVIEW` for days — what do I do?

Check whether a colleague received the notification email (it goes to the dev and admin distribution lists). If no one has acted, you can wait, send a direct reminder to someone on those lists, or withdraw the promotion from Page 1 and resubmit when a reviewer is available.

---

## Packages & Dependencies

### What is a "Packaged Component"?

A versioned, immutable snapshot of an Integration process that can be deployed. You select a Packaged Component on Page 1 to start a promotion. Think of it as a "release artifact" from your dev account. Always package your latest changes in Boomi AtomSphere before using the dashboard — the system promotes whatever is in the package, not your uncommitted editor state.

### What does "resolving dependencies" do?

Before promotion, the system recursively walks all components your selected process depends on — operations, maps, connections, profiles — and builds a complete list. It also checks DataHub to determine whether each component already exists in production (UPDATE) or is brand new (CREATE). This typically takes 5–15 seconds and happens automatically after you select a package.

### What do "CREATE" and "UPDATE" mean next to components?

"CREATE" means no ComponentMapping record exists yet — a new component will be created in production. "UPDATE" means a mapping already exists linking the dev component to an existing production component — it will be updated in-place. After a successful promotion, the system writes a new mapping automatically, so subsequent promotions of the same component will show "UPDATE."

### What are "shared connections" and why aren't they promoted?

Connections contain credentials that differ between environments. Instead of promoting them, admins pre-configure the production connections once in a shared `#Connections` folder, then create ComponentMapping records linking dev connection IDs to their production equivalents. During promotion, the system rewrites references — your components end up pointing to the correct production connection without any credentials being copied.

### I see a red "UNMAPPED" badge next to a connection — what do I do?

You cannot resolve this yourself. Contact your Boomi Admin and give them: the connection name shown in the dependency tree, your dev account name, and the error message. The admin uses the Mapping Viewer (Page 8) to create the `devComponentId → prodComponentId` mapping. Once the admin seeds it, you can re-run the promotion without any other changes.

### What order are components promoted in?

Bottom-up by dependency: profiles → connections → operations → maps → processes. This ensures each dependency exists before the components that depend on it. If a component fails, everything that depends on it is marked `SKIPPED` to prevent broken references.

### What does "configStripped" mean in the diff view?

During promotion, environment-specific values (passwords, hostnames, URLs, encrypted values) are stripped from component XML. A "configStripped" badge on a component means some values were stripped. This is expected and safe — the production connection already has the correct credentials pre-configured.

---

## Test Deployments

### Why is there a test deployment step?

Test deployments let you validate your changes in a test environment before going through the peer and admin review process. The test path requires no reviews and can proceed immediately after promotion. The emergency hotfix path skips test, but both paths still require both approval steps before reaching production.

### What is the difference between a test pack and a production pack?

Integration Packs with names ending in "- TEST" (e.g., "Orders - TEST") are test packs. All others are production packs. The pack selector on Page 4 automatically filters to show only test packs for test deployments and only production packs for production deployments. The system remembers which pack you used previously for the same process and suggests it.

### When I deploy to test, does that go to the main branch?

Yes — the test deployment merges your promotion branch to main using an OVERRIDE strategy. But the branch is preserved after the merge (you'll see `branchPreserved=true` in the response). This matters because the branch is needed later for the production diff comparison. The branch is only deleted after production deployment, rejection, admin denial, or your cancellation.

### My test deployment row on Page 9 shows red — what does it mean?

Red "Branch Age" means the branch is over 30 days old. Amber means 15–30 days. A stale warning banner may also appear at the top of the page. You should either promote to production or cancel the test deployment to free the branch slot.

### Can I cancel a test deployment I no longer plan to promote?

Yes. On Page 9, select the row and click "Cancel Test Deployment." A confirmation dialog warns that this deletes the branch and cannot be undone. After cancellation, the status becomes `TEST_CANCELLED` and the branch slot is freed.

---

## Peer Review

### How does my reviewer know my promotion is ready?

When you click "Submit for Peer Review" on Page 4, an email goes to the dev and admin distribution lists (you're CC'd). The subject is "Peer Review Needed: {processName} v{version}". Emergency hotfixes include "⚠ EMERGENCY HOTFIX" in the subject line so reviewers can prioritize.

### Who can review my promotion?

Any user with `ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN` who didn't submit the promotion. There is no seniority filter. First to respond gets it. You cannot choose a specific reviewer.

### Why can't I review my own promotion?

Self-review is prevented at three layers: (1) your own submissions are hidden from the Peer Review Queue when you view it, (2) a UI check blocks navigation if it somehow appears, and (3) the backend returns `SELF_REVIEW_NOT_ALLOWED` even if called directly. Email comparison is case-insensitive to handle Azure AD capitalization variations.

### What happens if my promotion gets rejected?

You receive an email with the reviewer's rejection reason (required for rejections). The promotion branch is deleted. Nothing in production changed. Address the feedback, fix your components in dev, re-package, and start from Page 1. The rejection reason appears in your email and in PromotionLog.

### Can a reviewer leave comments without rejecting?

Yes. There is a comments field (up to 500 characters) on the review page. Comments are optional for approvals but required for rejections. For approvals, comments are included in the notification to the admin. For rejections, they're sent back to you.

### What does the peer reviewer see?

Submitter info, process name, version, component count, deployment notes, test history (if applicable), and whether it's an emergency hotfix (with your written justification displayed prominently in red). They can click "View Diff" on any component to see a side-by-side XML comparison of what changed between the promotion branch and production main.

### After peer approval, what happens next?

An email goes to the admin distribution list and to you. The promotion moves to `PENDING_ADMIN_REVIEW` and appears in the Admin Approval Queue (Page 7). An admin must review and either approve (which triggers packaging and production deployment) or deny it. You'll receive an email either way.

---

## Emergency Hotfixes

### When should I use the Emergency Hotfix path?

Only for critical production issues that genuinely cannot wait for test validation — for example, a broken integration causing data loss or blocking a business-critical workflow. The hotfix label and your justification are permanently logged for leadership review.

### What's different about the hotfix process?

You skip the test environment deployment. On Page 3, select "Deploy to Production (Emergency Hotfix)" and provide a mandatory written justification (up to 1000 characters). Peer and admin reviews are still required. Reviewers see a prominent red "EMERGENCY HOTFIX" badge and your justification throughout the review process.

### Can I use the hotfix path regularly to avoid the test step?

Technically yes, but it is tracked. Every `isHotfix=true` promotion is logged with justification and is queryable from PromotionLog. Admins and leadership can filter all hotfix events for review. Treating hotfix as a shortcut is an operational governance concern.

---

## Integration Packs

### What is an Integration Pack?

A deployment artifact — a container that groups one or more packaged processes for deployment to an environment. Think of it as a "release bundle." The promotion system creates or updates Integration Packs as part of the packaging step. You select which pack to add your promoted process to on Page 4.

### Do I create a new Integration Pack for every promotion?

Usually you reuse an existing one. The system suggests the pack most recently used for the same process. Select a test pack (name ends in "- TEST") for test deployments and a production pack for production deployments. You can create a new pack if needed.

### What are "Deployment Notes" and who sees them?

An optional text field on Page 4 describing what you're deploying and why. Notes are included in the peer review notification email, displayed to reviewers on Page 6, and stored in PromotionLog. Writing clear notes helps reviewers make faster decisions.

### What is a "Target Account Group"?

Account Groups in Boomi define which environments a deployed Integration Pack is available to. Select the account group that contains your target test or production environment. Ask your admin which account group to use for each environment — this is site-specific configuration.

---

## Branches

### What is a "promotion branch"?

When you execute a promotion, the system creates a temporary branch named `promo-{promotionId}` in the production account. Your components are written to this branch, not directly to main. This isolation means reviewers can see exactly what changed without any risk to production. The branch is merged to main on admin approval or deleted on rejection, denial, withdrawal, or failure.

### Why is there a 15-branch limit warning?

Boomi enforces a hard limit of 20 active branches per account. The system triggers `BRANCH_LIMIT_REACHED` at 15 active branches — an early warning 5 slots before the hard limit. Each in-review or test-deployed promotion holds one branch slot.

### What do I do if I get `BRANCH_LIMIT_REACHED`?

Three options: (1) Wait for pending reviews to complete (approvals and rejections free slots), (2) Withdraw one of your own pending promotions from the "Your Active Promotions" panel on Page 1, (3) Cancel a stale test deployment from Page 9. The error page will direct you to these options.

### Does the branch get deleted when I deploy to test?

No — the branch is preserved after a test deployment (`branchPreserved=true`). It is needed later for the production diff comparison. The branch is only deleted after a successful production deployment, rejection, admin denial, withdrawal, or cancellation.

---

## Withdrawing & Cancelling

### Can I cancel a promotion after submitting it for review?

Yes, if it's still in `PENDING_PEER_REVIEW` or `PENDING_ADMIN_REVIEW`. Go to Page 1 — the "Your Active Promotions" panel shows all your pending promotions. Click "Withdraw." You can optionally provide a reason, but it's not required.

### What happens when I withdraw?

The promotion branch is deleted, freeing a branch slot. The PromotionLog status updates to `WITHDRAWN`. No email is sent to reviewers or admins — the promotion silently disappears from their queue. You can re-promote from scratch after fixing anything that needed changing.

### Can I withdraw after peer review but before admin review?

Yes. Withdrawal is available in both `PENDING_PEER_REVIEW` and `PENDING_ADMIN_REVIEW` states.

### Can a reviewer or admin withdraw my promotion?

No. Only the original initiator can withdraw. The system validates your email against the `initiatedBy` field in PromotionLog (case-insensitive).

### I fixed a bug in dev after submitting — do I need to withdraw first?

Yes. If a promotion is pending review, there's already a branch holding the old version. Withdraw the old promotion to delete that branch, then run a fresh promotion with the fixed components. Running two promotions of the same process simultaneously would conflict.

---

## Errors & Troubleshooting

### Error code reference

| Error Code | What It Means | Who Fixes It |
|------------|---------------|--------------|
| `BRANCH_LIMIT_REACHED` | 15+ active branches — new promotions blocked | You (withdraw/cancel stale ones) or wait for reviews to complete |
| `MISSING_CONNECTION_MAPPINGS` | One or more connections have no prod mapping | Boomi Admin (via Mapping Viewer, Page 8) |
| `CONCURRENT_PROMOTION` | Another promotion from the same dev account is `IN_PROGRESS` | Wait for it to complete or fail, then retry |
| `PROMOTION_FAILED` | One or more components failed; branch deleted; production unchanged | You (fix root cause in dev, re-run from Page 1) |
| `COMPONENT_NOT_FOUND` | A component in your package no longer exists in dev (renamed/deleted) | You (re-package from current components in dev) |
| `DEPENDENCY_CYCLE` | Circular component reference detected during dependency traversal | You (break the circular reference in dev) |
| `AUTH_FAILED` | Backend API token is invalid or expired — system config issue | Boomi Admin (rotate the API token) |
| `API_RATE_LIMIT` | Boomi Platform API rate limit hit — retry logic active | Usually self-resolving; retry if it persists |
| `INSUFFICIENT_TIER` | Your SSO tier group doesn't grant dashboard access | Azure AD admin (add you to `ABC_BOOMI_FLOW_CONTRIBUTOR`) |
| `SELF_REVIEW_NOT_ALLOWED` | You tried to review your own submission | Find a different reviewer |
| `SELF_APPROVAL_NOT_ALLOWED` | An admin tried to approve their own submission | A different admin must approve |
| `PROMOTION_NOT_COMPLETED` | You tried to proceed without a required prior step completing | Check status on Page 3; complete the missing step |
| `DATAHUB_ERROR` | DataHub model not published/deployed, or DataHub service issue | Boomi Admin (check DataHub model deployment) |

### My promotion failed — what do I do?

The failure banner on Page 3 explains what happened. The branch was automatically deleted and production is unchanged. Fix the root cause, then go back to Page 1 and re-run the promotion. Previously promoted components will show as UPDATE rather than CREATE on the next run, so the system correctly identifies what already exists.

### I get `MISSING_CONNECTION_MAPPINGS` — who fixes it?

This is an admin task. Contact your Boomi Admin and provide: the connection name(s) from the error message and your dev account name. The admin uses the Mapping Viewer (Page 8) to create the `devComponentId → prodComponentId` mapping. Once seeded, re-run your promotion — no other changes needed.

### The error message isn't clear — where do I find more detail?

The Error Page has a collapsible "Technical Details" section with the full error code and stack trace. For backend details, check Boomi Process Reporting — filter by process name using the prefix `PROMO - FSS Op -`. Look for the execution around the time of your failure and check the step-by-step results and Groovy logger output. When escalating to your admin, include the Promotion ID and error code.

### Should I use "Retry" or "Back" on an error page?

Use "Retry" for transient errors (rate limits, brief network issues) to re-execute the same step with the same inputs. Use "Back" to return to the previous page and change your inputs. Use "Home" to go to Page 1 and start fresh. If you need to fix something in dev, use "Home," fix the issue, re-package, and start over.

### I don't see my dev account in the dropdown — did someone remove my access?

Either: (a) the DevAccountAccess record for your team group hasn't been seeded yet, (b) you're not in the right `ABC_BOOMI_FLOW_DEVTEAM*` SSO group, or (c) your `isActive` flag is false in DataHub. Contact your Boomi Admin to verify your SSO group memberships and the DataHub record for your account.

### Who do I contact for which type of issue?

| Issue Type | Contact |
|------------|---------|
| Can't log in, INSUFFICIENT_TIER, no accounts in dropdown | Azure AD / Entra admin or Boomi Admin |
| MISSING_CONNECTION_MAPPINGS, unmapped connections | Boomi Admin |
| AUTH_FAILED, DATAHUB_ERROR, persistent system errors | Boomi Admin / platform administrator |
| Unexplained process failures | Check Process Reporting, then escalate to Boomi Admin with Promotion ID + error code |
| Bug reports or feature requests | Raise with the team/project that owns this system |

---

## Email Notifications

### What emails will I receive during the promotion lifecycle?

| Event | Who Receives It |
|-------|----------------|
| Test deployment complete | You only |
| Peer review submitted (you submitted) | Dev + admin distribution lists; you CC'd |
| Peer review rejected | You only (includes rejection reason) |
| Peer approved — admin review now needed | Admin distribution list + you |
| Admin approved and deployed to production | You + peer reviewer (includes deployment ID and package ID) |
| Admin denied | You + peer reviewer (includes denial reason) |
| You withdraw a promotion | Nobody — silent operation |
| Emergency hotfix submitted | Dev + admin lists; you CC'd (subject includes "⚠ EMERGENCY HOTFIX") |

### If I miss an email, will my promotion get stuck?

No. You can always check status on Page 1's "Your Active Promotions" panel or navigate directly to Page 3 (Promotion Status). The dashboard is the authoritative source of truth — emails are supplementary notifications, not required to track progress.

### What if an email fails to deliver?

Email failure is non-blocking — the workflow continues regardless. The failure is logged in Boomi Process Reporting. The promotion itself is not affected.

---

## Browser & Session

### Can I close my browser while a promotion is running?

Yes. The backend process runs independently on Boomi's cloud. The dashboard caches session state in IndexedDB every 30 seconds. When you return to the same URL, it restores your session and shows the completed result.

### What if my browser crashes mid-promotion?

The backend process continues running. Reopen the dashboard URL — the session should restore from IndexedDB cache. If it doesn't fully restore, go to Page 1 and check "Your Active Promotions" to find the current status.

### Can I use incognito/private browsing?

Not recommended. If IndexedDB is disabled (as it is in some private/incognito configurations), browser state cannot be restored after closing the tab. The backend promotion still runs and completes, but you'll need to navigate back manually via Page 1. Use a regular browser window.

### Can I have two tabs open at the same time?

No. Two tabs sharing the same Flow session state can cause inconsistent behavior. Use one tab for the dashboard at a time.

---

## Security & Audit

### Will my database passwords or API keys be exposed during promotion?

No. The `strip-env-config.groovy` script removes environment-specific data (passwords, hostnames, URLs, encrypted values) from component XML before anything is written to production. Connections are never promoted at all — only the reference to the pre-configured production connection is rewritten.

### Who can see my promotions?

All users with `ABC_BOOMI_FLOW_ADMIN` can see all promotions across all teams. Users with `ABC_BOOMI_FLOW_CONTRIBUTOR` can see promotions that have been submitted for peer review. Your pending (not-yet-submitted) promotions are visible only to you on Page 1.

### Is there a permanent audit trail?

Yes. Every promotion creates a PromotionLog record in DataHub capturing: who initiated it, when, which components (created/updated/failed/skipped), target environment, whether it was a hotfix with written justification, peer reviewer decision, admin decision, and final production deployment IDs. These records are permanent. Emergency hotfixes are flagged with `isHotfix=true` and are easy to filter for leadership review.

### Can I accidentally promote to the wrong production account?

No. You can only see dev accounts linked to your own SSO team groups. The production account is a fixed system-level configuration — there is no way to redirect a promotion to a different production account. Admins see all accounts but still operate within the same single production account.

### If something bad gets promoted, is it reversible?

Boomi maintains its own component version history. If a bad version is promoted, the previous version still exists in production and can be restored manually through Boomi's standard component UI. The promotion system does not provide automated rollback, but it does not destroy previous versions.

---

## See Also

- [FAQ-executive.md](FAQ-executive.md) — Executive overview: what this system is and why it exists
- [docs/architecture.md](architecture.md) — System design, key decisions, error handling
- [docs/build-guide/index.md](build-guide/index.md) — Implementation playbook (for admins and builders)
- [integration/flow-service/flow-service-spec.md](../integration/flow-service/flow-service-spec.md) — Complete API contract for all message actions
- [flow/flow-structure.md](../flow/flow-structure.md) — Dashboard navigation, Flow values, swimlane structure

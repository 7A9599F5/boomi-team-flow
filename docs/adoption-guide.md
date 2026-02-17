# Team Adoption Guide: The Promotion Dashboard

*For development teams ready to own their Boomi integration lifecycle*

---

If you've ever waited days for an admin to copy your process to production, or discovered a dozen duplicate V1 components cluttering the primary account with no version history, this guide is for you.

---

## The Problem Today

The current process works — barely — but it has real costs:

- **The admin team is the bottleneck.** Every promotion requires their time. Every bug fix. Every hotfix. Every redeployment.
- **"Copy Component" creates duplicates.** Each copy starts at Version 1, with no link to the original. You can't push updates to the same component — you make another copy.
- **No structured review before production.** Changes go live when an admin has bandwidth, with no formal peer review step built in.
- **Connection limits hit production first.** The primary account has a fixed connection limit that dev accounts don't share. Every ad-hoc copy chews into that budget.
- **No self-service.** If you want to test a change end-to-end, you're in the admin queue.

The Promotion Dashboard changes this.

---

## What the Promotion Dashboard Gives You

This is not just a nicer version of "ask an admin." It's a complete shift in who owns the integration lifecycle.

- **Self-service promotions** — promote on your schedule. No queue. No waiting.
- **Version continuity** — one master component in production, updated in-place each time. No more orphaned copies.
- **Test before production** — deploy to a test environment with zero reviews required. Validate, then promote.
- **Side-by-side diffs** — see exactly what changed at the XML level before anyone approves. Reviewers know what they're looking at.
- **Full audit trail** — every promotion is logged with who, what, when, which components, who reviewed it, and what was approved. Emergency hotfixes include mandatory written justifications.
- **An emergency path that still has guardrails** — hotfixes skip test deployment but still require peer review and admin approval.
- **Email notifications** — you're kept informed at each handoff point without having to check the dashboard constantly.

---

## How It Works (The 60-Second Version)

```
Pick Package
  → Review Dependencies
    → Promote to Branch
      → Deploy to Test
        → Validate
          → Submit for Production
            → Peer Review
              → Admin Approval
                → Live
```

**Pick Package** — Browse your dev account's packaged processes on Page 1. Select the one you want to promote.

**Review Dependencies** — The system walks your process's full dependency tree (sub-processes, maps, connections) and shows you what's new vs. what already exists in production.

**Promote to Branch** — Components are copied to a temporary staging branch in the production account — not to main. Nothing in production changes yet.

**Deploy to Test** — Push to a test Integration Pack. Automated validation only — no manual approval gates. Validate it works.

**Validate** — Test in your test environment. When you're ready, come back to the dashboard.

**Submit for Production** — On Page 9 (Production Readiness Queue), initiate the production promotion and fill in deployment details.

**Peer Review** — A teammate (any contributor who isn't you) reviews the diff, the deployment notes, and approves or rejects.

**Admin Approval** — An admin does the final review and pulls the trigger on the production deployment.

**Live** — Components are merged to main, packaged, and deployed. You get an email with the deployment ID.

---

## Getting Your Team Started

Before your first promotion, make sure everything is in place. Most of this is a one-time admin task.

- [ ] SSO groups assigned: `ABC_BOOMI_FLOW_CONTRIBUTOR` (dashboard access) + your team group (e.g., `ABC_BOOMI_FLOW_DEVTEAMA`, controls which dev accounts you see)
- [ ] Dev account provisioned and linked in DataHub by an admin
- [ ] At least one packaged component ready in the dev account (package it in Boomi AtomSphere first)
- [ ] Connection mappings seeded by your admin for any shared connections (databases, APIs) your processes use
- [ ] Dashboard URL bookmarked (get this from your admin — it's set when the Flow app is published)
- [ ] Team knows who their peer reviewers are (anyone on `CONTRIBUTOR` or `ADMIN` tier can review your work)

**Note:** If you log in and see an "Access Denied" error or empty account list, your SSO groups likely need to be updated. Contact your admin with the error code shown.

---

## Your First Promotion (Step-by-Step Walkthrough)

Here's the standard path for a non-emergency promotion.

1. **Open the dashboard and log in with your Azure AD credentials.** No new passwords needed — it's your existing SSO login.

2. **On Page 1 (Package Browser), select your dev account.** If you only have one linked account, it auto-selects and loads your packages immediately.

3. **Select the packaged process you want to promote.** Make sure you've packaged your latest changes in Boomi AtomSphere first — the dashboard promotes what's in the package, not unsaved editor state.

4. **On Page 2 (Promotion Review), review the dependency tree.** You'll see each component marked as CREATE (new to production) or UPDATE (will update an existing component). If any connections show as UNMAPPED, stop here and contact your admin — they need to seed a connection mapping before you can proceed.

5. **Click "Execute Promotion."** The system creates a staging branch in the production account and promotes each component there. This typically takes 30–120 seconds. You can safely close the browser and come back — the backend runs independently and your session will restore.

6. **On Page 3 (Promotion Status), confirm success.** You'll see per-component results. From here, click "Deploy to Test" to push to a test Integration Pack.

7. **On Page 4 (Deployment Submission), select a test Integration Pack** (names ending in "- TEST") and submit. The system runs automated validation — no manual approval gates. You'll receive an email when the test deployment completes.

8. **Validate in your test environment.** When satisfied, go to Page 9 (Production Readiness Queue), select your deployment, and click "Promote to Production." Fill in deployment notes and select a production Integration Pack. Your submission goes to the peer review queue. From there, a peer reviews it, then an admin approves and deploys. You'll receive email updates at each step.

---

## Key Concepts in Plain English

**Package vs. Integration Pack**
A *package* (or Packaged Component) is a versioned snapshot of a single process, like a release candidate for one piece of work. An *Integration Pack* is a deployable bundle of one or more packages — the finished product that gets installed into an environment. You select a package to promote; you select an Integration Pack to deploy to.

**Promotion branch**
When you hit "Execute Promotion," the system creates a temporary branch in the production account (named `promo-{id}`). Your components are written there, not to production directly. This lets reviewers see exactly what changed. The branch is either merged to main on approval, or deleted on rejection — main is never touched until the admin approves.

**Component mapping**
Every Boomi component has a unique ID. When a dev component is promoted for the first time, a new production component is created and a mapping record links the two IDs. On future promotions, the system finds that mapping and updates the existing production component in-place — no duplicates.

**Shared connections**
Connections (database connectors, API connectors, etc.) are never promoted. They contain environment-specific credentials that differ between dev and prod. Instead, an admin pre-configures production connections once and creates mapping records linking dev connection IDs to their production equivalents. The system automatically swaps the references during promotion.

**Peer review vs. admin approval**
Peer review is a first-pass technical check by any other contributor — they look at the diff and deployment notes and confirm it's safe to deploy. Admin approval is the final gate before production deployment actually occurs. Two separate humans, two separate decisions. You cannot review your own submission at either stage.

**Test environment vs. production**
Test packs are Integration Packs with names ending in "- TEST." Deploying to test requires no approvals and is the recommended validation step before production. Production packs are everything else. The system filters the Integration Pack selector based on which path you're on.

---

## Frequently Asked Quick Hits

**"Do I need new credentials or a new account?"**
No. You log in with your existing Azure AD / Entra SSO. Access is controlled through groups your admin manages.

**"Can I close the browser during promotion?"**
Yes. The backend runs on Boomi's cloud independently of your browser. Your session state is saved. When you return to the dashboard URL, it restores where you left off.

**"Can I review my own promotion?"**
No. Self-review is blocked at the UI level, the API level, and the backend level. You need at least one other contributor available to review your work.

**"Do I have to deploy to test before production?"**
The standard path requires it. The only exception is the Emergency Hotfix path, which skips test but still requires both peer review and admin approval plus a written justification.

**"What if my admin is unavailable to approve?"**
Any user with the `ABC_BOOMI_FLOW_ADMIN` tier can approve. The notification email goes to the full admin distribution list, not one individual.

**"How many promotions can be in flight at once?"**
No per-user limit, but there's an account-level limit of 15 active branches (the Boomi platform hard limit is 20). If you have many pending reviews accumulating, you may hit this. Withdraw stale promotions to free up slots.

**"Will I be notified if my promotion is approved or rejected?"**
Yes. You receive email at each key transition: test deployment complete, peer rejection, peer approval, admin approval/denial.

**"What if I realize I submitted the wrong version?"**
Withdraw the promotion from the "Your Active Promotions" panel on Page 1, fix your components in dev, re-package, and resubmit.

**"Is there a way to see all my active promotions at once?"**
Yes — the "Your Active Promotions" panel on Page 1 lists everything currently in-flight with their statuses.

---

## What Happens When Things Go Wrong

Nothing the Promotion Dashboard does is permanent until an admin approves production deployment. The system is designed to be safe to fail.

**Promotion fails** — The staging branch is deleted automatically. Nothing changed in production. Zero cleanup needed. The error page shows which component caused the failure and why. Fix the root cause in your dev account and re-run from the Package Browser.

**Peer reviewer rejects** — You receive an email with the required rejection reason. The branch is deleted. Address the feedback in your dev account, re-package, and start a new promotion.

**Admin denies after peer approval** — Both the peer approval and admin review are reset. You'll need to re-run the full workflow including peer review again after fixing the issue.

**Branch limit hit** — You'll see a `BRANCH_LIMIT_REACHED` error before any work is done. Go to Page 1 and withdraw a stale pending promotion, or cancel a stale test deployment from Page 9. This frees a branch slot immediately.

**Wrong Integration Pack selected** — If you haven't submitted for peer review yet, you can go back and change it. If it's already in review, withdraw and resubmit.

The key mental model: **branches are cheap, main is safe.** Everything risky happens on a branch. Production is only touched when an admin explicitly approves.

---

## Support and Resources

**For access issues** (can't log in, no accounts visible, `INSUFFICIENT_TIER` error):
Contact your Azure AD / Entra admin or Boomi Admin to verify your SSO group assignments.

**For connection mapping issues** (`MISSING_CONNECTION_MAPPINGS` error):
Contact your Boomi Admin. They use the Mapping Viewer (Page 8) to seed the mapping — this is a one-time setup per connection. Give them the connection name shown in the error and your dev account name.

**For system-level errors** (`AUTH_FAILED`, `DATAHUB_ERROR`):
Contact your Boomi platform administrator. These are system configuration issues, not user errors.

**For anything else:**
The Error Page in the dashboard has a "Technical Details" section with the full error code and stack trace. Include the Promotion ID and error code when escalating.

**Documentation:**
- [FAQ for Contributors](FAQ-contributor.md) — detailed Q&A covering every stage of the workflow
- [FAQ for Leadership](FAQ-executive.md) — organizational context and architecture overview

---

*The goal of this system is to give your team full ownership of your integration work — from development through production — without depending on admin availability at every step. The first promotion takes some setup. The second one takes about ten minutes.*

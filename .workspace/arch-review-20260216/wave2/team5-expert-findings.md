# Team 5 -- Identity/Access Expert Findings

**Domain:** Authorization, Authentication, Access Control, SSO Model
**Reviewer:** Identity/Access Expert
**Date:** 2026-02-16

**Files Reviewed:**
- `docs/architecture.md` (SSO model, tier resolution, two-axis authorization)
- `integration/flow-service/flow-service-spec.md` (auth-related actions, security section)
- `flow/flow-structure.md` (swimlane authorization, Decision steps, Flow values)
- `flow/page-layouts/page5-peer-review-queue.md` (self-review prevention)
- `flow/page-layouts/page6-peer-review-detail.md` (peer review Decision step)
- `flow/page-layouts/page7-admin-approval-queue.md` (admin authorization)
- `flow/page-layouts/page9-production-readiness.md` (developer swimlane auth)
- `.claude/rules/flow-patterns.md` (authorization model documentation)
- `.workspace/arch-review-20260216/wave1/team4-consensus.md` (cross-reference)

---

## Critical Findings

### CRIT-1: Self-Review Prevention Vulnerable to Email Case Sensitivity

**Files:** `flow/page-layouts/page5-peer-review-queue.md:111-116`, `flow/page-layouts/page6-peer-review-detail.md:16-17`, `integration/flow-service/flow-service-spec.md:366-381`

**Issue:** Self-review prevention relies on string comparison between `$User/Email` and `initiatedBy` at three enforcement points:
1. Process E2 backend: `requesterEmail` filtered against `initiatedBy` (flow-service-spec.md:333)
2. Page 5 UI Decision step: `$User/Email != selectedPeerReview.initiatedBy` (page5:115)
3. Process E3 backend: `reviewerEmail` vs `initiatedBy` (flow-service-spec.md:381)

Azure AD/Entra returns email addresses with the casing configured in the directory (e.g., `John.Doe@Company.com`). However, the `initiatedBy` field in PromotionLog is populated from the `requestedBy` field in the `executePromotion` request (flow-service-spec.md:136), which comes from the Flow `$User/Email` context at *promotion time*. If the user's email casing changes between promotion and review (e.g., directory sync updates), or if a different SSO session returns different casing, all three comparison points fail silently -- the user's own submission appears in their peer review queue.

**Severity Justification:** Self-review bypass is a fundamental integrity violation. The 2-layer approval model explicitly exists to prevent single-person deployments to production.

**Fix:** Normalize all email comparisons to lowercase:
- Process E2: `toLowerCase()` on both `requesterEmail` and `initiatedBy` before filtering
- Process E3: `toLowerCase()` on both `reviewerEmail` and `initiatedBy` before comparison
- Page 5/6 Decision steps: Use Flow function `LOWERCASE({$User/Email})` == `LOWERCASE({selectedPeerReview.initiatedBy})`
- Store `initiatedBy` as lowercase in PromotionLog to prevent accumulation of mixed-case data

### CRIT-2: SSO Group Name Inconsistency Creates Authorization Failures (Cross-ref Wave 1)

**Files:** `flow/flow-structure.md:18`, `flow/page-layouts/page5-peer-review-queue.md:10`, `flow/page-layouts/page7-admin-approval-queue.md:10`, `docs/architecture.md:121-130`

**Issue:** Already identified as CRIT-2 in Wave 1 Team 4 consensus. From an identity perspective, the impact is more severe than documented: the tier resolution algorithm (architecture.md:127-130, flow-service-spec.md:46-48) uses `ABC_BOOMI_FLOW_*` claim values, but Pages 5, 7, and build guides reference `"Boomi Developers"` and `"Boomi Admins"` -- which are Azure AD *display names*, not claim values.

If a builder configures swimlane authorization using display names instead of claim values, **all swimlane access fails silently** -- users authenticate via SSO but the group membership check returns false because it's comparing the wrong identifier type. This is not a cosmetic inconsistency; it's a functional authorization failure.

**Fix:** As per Wave 1, standardize all references to `ABC_BOOMI_FLOW_*`. Additionally, add a validation step in the build guide: "Verify the group identifier format matches your Azure AD SSO claim configuration. Display names and claim values are distinct."

---

## Major Findings

### MAJ-1: No Token Rotation or Session Expiry Guidance

**Files:** `integration/flow-service/flow-service-spec.md:690-708` (Security Considerations section)

**Issue:** The Security Considerations section recommends rotating API tokens "every 90 days" (line 696) but provides zero operational guidance:
- No mechanism to rotate tokens without downtime (blue-green token rotation)
- No alert or monitoring for approaching token expiry
- No documentation of what happens when a token expires mid-operation (e.g., during a 2-minute `executePromotion` call)
- The Flow Service connector stores credentials as Basic Auth (line 549) -- rotating the token requires editing the connector config and redeploying

The Partner API token used by the HTTP Client connector is the single credential that gates ALL promotion operations. If it expires or is rotated incorrectly, the entire system halts.

**Fix:** Document a token rotation procedure: (1) Create new token, (2) Update connector config, (3) Test with a read-only call like `getDevAccounts`, (4) Revoke old token. Add a monitoring check for token age. Document graceful failure behavior on 401 responses.

### MAJ-2: No Defense-in-Depth Tier Re-Validation Beyond Process C

**Files:** `docs/architecture.md:125-137`, `integration/flow-service/flow-service-spec.md:125-138`

**Issue:** The architecture explicitly documents defense-in-depth tier re-validation in Process C (executePromotion), which re-validates `userSsoGroups` to ensure CONTRIBUTOR tier. However, no other process performs this check:

- **Process D (packageAndDeploy):** Does not accept or validate `userSsoGroups`. A compromised or replayed request to `packageAndDeploy` bypasses tier validation entirely. This is the most sensitive operation -- it deploys to production.
- **Process E3 (submitPeerReview):** No tier re-validation. Accepts `reviewerEmail` without verifying that the email belongs to a CONTRIBUTOR or ADMIN tier user.
- **Process F (manageMappings):** No tier validation. Mapping manipulation is admin-only from the UI (Page 8 is in Admin swimlane), but the backend accepts any caller.

The defense-in-depth principle is correctly applied in Process C but inconsistently applied elsewhere. An attacker who can craft a direct Flow Service API call (bypassing the Flow UI) can invoke `packageAndDeploy` or `manageMappings` without tier verification.

**Mitigation Context:** The Flow Service is behind Basic Auth, so direct API access requires the API token. The risk is elevated for insider threats or compromised tokens.

**Fix:** Add `userSsoGroups` parameter to Process D and Process F requests. Re-validate tier at the start of each process: D requires ADMIN, F requires ADMIN. For Process E3, validate that `reviewerEmail` corresponds to a CONTRIBUTOR or ADMIN tier user by querying SSO groups.

### MAJ-3: `userSsoGroups` Passed as Client-Supplied Data (Untrusted Input)

**Files:** `integration/flow-service/flow-service-spec.md:30-31`, `integration/flow-service/flow-service-spec.md:138`, `flow/flow-structure.md:215`

**Issue:** The `userSsoGroups` array is populated from the Flow authorization context (`$User` system values) and passed to the backend as a request field. While Flow populates these from the SSO session, the Flow Service receives them as regular JSON fields in the request payload -- there is no server-side verification that these groups are authentic.

In a normal flow, the SSO session is trustworthy because Flow validates it. However:
1. The Flow Service API is callable directly via HTTP (it's a standard REST endpoint with Basic Auth)
2. A caller with the API token can fabricate `userSsoGroups: ["ABC_BOOMI_FLOW_ADMIN"]` to gain ADMIN tier
3. The tier resolution algorithm in Process A0 and Process C trusts this array without cross-referencing the actual SSO provider

This is a design limitation of the Boomi Flow architecture -- there is no server-side SSO session validation inside Integration processes. The mitigation relies on the API token being the security boundary.

**Fix:** Document this as a known architectural constraint. Add to the Security Considerations section: "The API token is the sole authentication boundary for Flow Service calls. Protect the API token as a highly privileged credential. The `userSsoGroups` field is trusted because callers must possess the API token, which is equivalent to full system access." Consider IP allowlisting on the Flow Service if Boomi supports it.

### MAJ-4: Admin Swimlane Cannot Be Self-Approved (But No Spec Says So)

**Files:** `flow/page-layouts/page7-admin-approval-queue.md:9-12`, `flow/flow-structure.md:36-37`

**Issue:** The Admin Swimlane requires `ABC_BOOMI_FLOW_ADMIN` SSO group. There is no restriction preventing an admin from:
1. Submitting a promotion as a developer (they have CONTRIBUTOR access via swimlane auth)
2. Having a peer reviewer approve it
3. Approving their own deployment on Page 7

The self-review prevention only applies to the peer review layer (Pages 5-6). No equivalent check exists on Page 7 to prevent the original submitter (who is also an admin) from being the admin approver.

This means an admin-tier user needs only one collaborator (the peer reviewer) to deploy arbitrary code to production, rather than requiring two independent reviewers as the 2-layer model implies.

**Fix:** Add an admin self-approval check: on Page 7, compare `$User/Email` with `selectedPromotion.initiatedBy`. If equal, block with "You cannot approve your own submission." Implement at both UI (Decision step on Page 7) and backend (Process D should reject if `adminEmail == initiatedBy`).

### MAJ-5: DevAccountAccess Records Have No Expiry or Audit Mechanism

**Files:** `docs/architecture.md:158-162`, `datahub/models/` (DevAccountAccess model)

**Issue:** DevAccountAccess records are admin-seeded via ADMIN_CONFIG source and have an `isActive` flag, but:
- No documented process for periodic review of access grants
- No expiry date field on DevAccountAccess records
- No audit trail of who granted or revoked access
- No mechanism to detect stale access (e.g., when a team member leaves)

SSO group membership changes are immediate (Azure AD propagation), but DevAccountAccess records persist in DataHub indefinitely. If an SSO group is renamed or deleted, the corresponding DevAccountAccess records become orphaned but still exist -- they just won't match any user's groups anymore (safe failure). However, if a user is removed from an SSO group but the group itself persists, the system correctly denies access (SSO session won't contain the group).

The risk is operational: over time, stale DevAccountAccess records accumulate, making it hard to audit who has access to what.

**Fix:** Add `grantedBy`, `grantedDate`, and optional `expiresDate` fields to DevAccountAccess. Consider a periodic admin review workflow or a DataHub report that lists all active access grants.

---

## Minor Findings

### MIN-1: SSO Group Names Are Hardcoded Constants (Coupling Risk)

**Files:** `docs/architecture.md:115-130`, `integration/flow-service/flow-service-spec.md:46-48`

**Issue:** The tier resolution algorithm and team group matching use hardcoded string prefixes:
- `ABC_BOOMI_FLOW_ADMIN` (exact match)
- `ABC_BOOMI_FLOW_CONTRIBUTOR` (exact match)
- `ABC_BOOMI_FLOW_DEVTEAM*` (prefix match)

These are embedded in Process A0 logic and Process C logic. If the organization changes its SSO group naming convention (e.g., merges with another company and renames groups), every process and every build guide reference must be updated.

**Fix:** Extract group name prefixes into Dynamic Process Properties or a configuration model. Document the coupling in the build guide with a "Configuration Points" section.

### MIN-2: No Rate Limiting on Self-Review Bypass Attempts

**Files:** `integration/flow-service/flow-service-spec.md:380-383`

**Issue:** Process E3 returns `SELF_REVIEW_NOT_ALLOWED` error when a user attempts to review their own submission, but there is no rate limiting or logging of repeated bypass attempts. A user could probe the API to discover the exact email matching logic.

**Fix:** Log `SELF_REVIEW_NOT_ALLOWED` events in Process Reporting with the reviewer email and promotion ID. Consider a threshold alert (e.g., 5+ attempts from the same user within an hour).

### MIN-3: `reviewerEmail` Not Validated Against SSO Session

**Files:** `integration/flow-service/flow-service-spec.md:369-370`

**Issue:** The `submitPeerReview` action accepts `reviewerEmail` as a request field (line 369). This email is stored in PromotionLog as `peerReviewedBy`. There is no server-side validation that this email matches the actual authenticated user. In normal flow, Flow populates it from `$User/Email`, but a direct API caller could submit a fabricated reviewer email.

This is related to MAJ-3 (untrusted input from client) but specifically affects the audit trail rather than authorization.

**Fix:** Document the trust boundary. If reviewer attribution is critical for compliance, consider deriving the reviewer email from the API token context rather than accepting it as input.

### MIN-4: Peer Review Swimlane Has Same Authorization as Developer Swimlane

**Files:** `flow/flow-structure.md:18-30`, `.claude/rules/flow-patterns.md:27-29`

**Issue:** Both the Developer Swimlane and Peer Review Swimlane accept `ABC_BOOMI_FLOW_CONTRIBUTOR OR ABC_BOOMI_FLOW_ADMIN`. There is no additional authorization differentiation. Any developer can peer-review any other developer's work.

This is by design (the spec states "any dev or admin except submitter"), but it means a small team of two developers can mutually approve each other's work indefinitely. The 2-layer model provides diversity (peer + admin), but the peer layer has no rotation or quorum requirements.

**Fix:** This is acceptable for small teams but should be documented as a known limitation. For larger organizations, consider adding a "minimum reviewer count" or "reviewer rotation" policy note.

### MIN-5: No Session Timeout or Re-Authentication for Long-Running Reviews

**Files:** `flow/flow-structure.md:543-550`, `integration/flow-service/flow-service-spec.md:604-619`

**Issue:** The spec documents that users can close the browser and return later via IndexedDB state persistence. However, there is no documented session timeout or re-authentication requirement. A user who opens Page 7 could leave the tab open for days and still click "Approve and Deploy" without re-authenticating.

This depends on Boomi Flow's built-in session management (typically SSO session cookies with IdP-controlled timeouts). The spec does not document what happens when the SSO session expires while the user is on an approval page.

**Fix:** Document the expected SSO session timeout behavior. Clarify whether the swimlane transition forces re-authentication or relies on the existing session cookie. If the SSO cookie expires, Flow should redirect to the login page before executing the message action.

### MIN-6: Email Notifications Leak Promotion Metadata to Distribution Lists

**Files:** `flow/flow-structure.md:361-520`

**Issue:** Email notifications for peer review and admin approval are sent to distribution lists (`boomi-developers@company.com`, `boomi-admins@company.com`). These emails contain:
- Promotion IDs
- Process names
- Component counts
- Submitter and reviewer email addresses
- Hotfix justifications

All developers on the distribution list can see every promotion's metadata, regardless of their dev account access. This may leak information about projects or teams that a developer should not have visibility into.

**Fix:** Consider scoping notifications to the relevant dev team group rather than the global developer distribution list. Alternatively, document this as acceptable information sharing and ensure hotfix justifications do not contain sensitive data.

---

## Observations

### Positive Patterns

1. **Two-axis SSO model is well-designed:** The separation of team groups (account visibility) from tier groups (dashboard capability) is a strong identity architecture pattern. ADMIN bypasses team checks (correct for global oversight) while CONTRIBUTOR access is scoped by team membership.

2. **Defense-in-depth in Process C:** Re-validating the tier from `userSsoGroups` in the promotion engine (not just relying on swimlane auth) is excellent security hygiene, even if inconsistently applied elsewhere.

3. **Dual-layer self-review prevention:** Backend exclusion (Process E2) + UI Decision step fallback provides redundancy. Even if one layer fails, the other catches it (except for the case sensitivity issue in CRIT-1).

4. **Swimlane-based authorization:** Using Boomi Flow's built-in swimlane authorization containers for coarse-grained access control is architecturally sound and avoids custom auth implementations.

5. **Connection promotion exclusion:** Not promoting connections (which contain credentials) is a critical security decision that prevents credential leakage between environments.

---

## Multi-Environment Assessment

### Identity Implications of Multi-Environment Deployment

| Concern | Assessment |
|---------|-----------|
| Test deploy bypasses reviews | By design -- acceptable. Test environments have lower risk. |
| Emergency hotfix bypasses test | Reviews still required. Hotfix flag is logged. Admin must acknowledge. Acceptable. |
| Token shared across environments | Single API token for all Flow Service operations. If test and production use separate Integration Packs but the same Flow Service, the token boundary is the same. |
| Branch persistence exposes diff data | Branches preserved for test deployments remain readable via `generateComponentDiff` to anyone with the API token. No per-branch access control. |
| Admin self-approval | Possible for all deployment paths (test, production, hotfix). MAJ-4 applies across all modes. |

### Overall Identity/Access Posture

The system has a **good foundation** with the two-axis SSO model, swimlane authorization, and defense-in-depth patterns. The critical gaps are:
1. Case-sensitive email comparison undermines self-review prevention
2. Inconsistent tier re-validation across processes creates uneven security boundaries
3. Client-supplied `userSsoGroups` is a known architectural constraint of the Boomi platform

The most impactful fix is normalizing email comparisons (CRIT-1), which is low-cost and eliminates the most exploitable vulnerability.

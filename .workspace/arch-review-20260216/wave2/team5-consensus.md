# Team 5 -- Security & Authorization Consensus

**Participants**: Identity/Access Expert, Security Architect, Devil's Advocate
**Date**: 2026-02-16
**Scope**: Authorization model, credential protection, self-review enforcement, API security, SSO model

---

## Critical Findings (verified)

### CRIT-1: Self-Review Prevention Vulnerable to Email Case Sensitivity

**Files**: `flow/page-layouts/page5-peer-review-queue.md:115`, `flow/page-layouts/page6-peer-review-detail.md:16-17`, `integration/flow-service/flow-service-spec.md:333,381`
**Consensus**: Unanimous Critical -- all three reviewers agree.
**Source**: Expert CRIT-1, corroborated by Architect MAJ-2

Self-review prevention relies on string equality between `$User/Email` and `initiatedBy` at three enforcement points (Process E2 exclusion, Process E3 validation, UI Decision steps). None perform case normalization. Azure AD preserves directory casing in email claims, meaning a casing change between promotion and review time (e.g., directory sync, admin edit) causes the self-review check to fail silently -- the submitter's own promotion appears in their peer review queue.

**Impact**: Undermines the core 2-layer approval integrity model. A developer could bypass self-review prevention and approve their own code for production.

**Recommended Fix**:
1. Store `initiatedBy` as lowercase in PromotionLog at write time (Process C)
2. Apply `toLowerCase()` in Process E2 when filtering by `requesterEmail`
3. Apply `toLowerCase()` in Process E3 when comparing `reviewerEmail` with `initiatedBy`
4. Use `LOWERCASE()` Flow function in Decision steps on Pages 5 and 6

---

### CRIT-2: strip-env-config.groovy Has Incomplete Credential Stripping

**File**: `integration/scripts/strip-env-config.groovy:20-58`
**Consensus**: Unanimous Critical
**Source**: Architect CRIT-1

The script strips only 5 element patterns by exact name match: `password`, `host`, `url`, `port`, `EncryptedValue`. This misses common sensitive element categories including API keys/tokens (`apiKey`, `apiToken`, `secretKey`, `clientSecret`), connection strings (`connectionString`, `jdbcUrl`), certificate material (`privateKey`, `keystorePassword`), and proxy credentials (`proxyPassword`). The approach uses `it.name() == 'password'` exact matching, which is inherently fragile.

**Impact**: Dev credentials, API keys, or certificates could be promoted to the branch and visible in the XML diff viewer (Process G, Pages 3/6/7) to anyone with peer review or admin access. Combined with the normalize-xml.groovy fallback (MIN-3 below), raw unstripped content could be displayed.

**Compounding factor**: The script also lacks try/catch error handling (violating groovy-standards.md), meaning an exception during stripping could pass component XML through entirely unstripped.

**Recommended Fix**:
1. Expand the element name list to cover all known Boomi sensitive element patterns
2. Add regex-based catch-all: strip any element whose name contains `password`, `secret`, `key`, `token`, `credential` (case-insensitive)
3. Add top-level try/catch per groovy-standards.md -- on error, FAIL the promotion rather than passing through unstripped XML
4. Consider attribute-based stripping for connection-type components

---

## Major Findings (verified)

### MAJ-1: Client-Supplied `userSsoGroups` Is an Untrusted Security Input

**Files**: `integration/flow-service/flow-service-spec.md:30-31,138`, `docs/architecture.md:125-137`
**Consensus**: Major (Expert and DA agree; Architect rated Critical but DA provided compelling downgrade rationale)
**Source**: Expert MAJ-3, Architect CRIT-2, Architect MAJ-4 (consolidated)

The `userSsoGroups` array is populated from the Flow SSO context and passed as a regular request field to backend processes (A0 and C). The backend trusts this array for tier resolution without independent verification. A caller who possesses the Flow Service Basic Auth credentials can fabricate `userSsoGroups` to escalate their tier.

**Mitigating factors**: The Flow Service Basic Auth credential is the sole authentication boundary. Anyone who possesses it already has full API access, making group fabrication redundant for escalation. The `userSsoGroups` re-validation in Process C is defense-in-depth against the normal path, not a standalone control.

**Impact**: This is a known **platform constraint** of the Boomi architecture. The API token is the real security boundary.

**Recommended Fix**:
1. Document as an accepted architectural constraint in the Security Considerations section
2. Add explicit guidance: "The Flow Service Basic Auth credential grants full access to all operations. Protect it with the sensitivity of a database root password."
3. Consider IP allowlisting or mutual TLS between the Flow runtime and the Flow Service endpoint
4. Never expose the Flow Service endpoint directly to end users

---

### MAJ-2: Admin Self-Approval Not Prevented

**Files**: `flow/page-layouts/page7-admin-approval-queue.md` (entire file), `flow/flow-structure.md:150-157`
**Consensus**: Unanimous Major
**Source**: Expert MAJ-4

Self-review prevention exists only at the peer review layer (Pages 5-6). No equivalent check exists on Page 7 to prevent the original submitter (who is also an admin) from approving their own deployment. An admin-tier user needs only one collaborator (any peer reviewer) to deploy arbitrary code to production.

**Impact**: Weakens the 2-layer approval model. The admin approval layer provides no additional person-independence for admin-tier users.

**Recommended Fix**:
1. Add Decision step on Page 7: `$User/Email` (lowercased) != `selectedPromotion.initiatedBy` (lowercased)
2. Add backend validation in Process D: reject if `adminEmail == initiatedBy`
3. At minimum, log when admin approver matches submitter for audit trail

---

### MAJ-3: Blind String Replacement in Reference Rewriting May Corrupt Data

**File**: `integration/scripts/rewrite-references.groovy:29`
**Consensus**: Major (Architect and DA agree)
**Source**: Architect MAJ-3

The `replaceAll(Pattern.quote(devId), prodId)` call replaces ALL occurrences of a dev component GUID anywhere in the XML document -- including inside embedded Groovy scripts, comments, CDATA sections, and string literals. If a Groovy Data Process step references a component ID in a log message or comment, the rewrite silently corrupts the script.

**Mitigating factors**: GUIDs are 36-character strings making accidental collisions near-zero. `Pattern.quote()` prevents regex interpretation. The risk is low-probability but high-impact (silent data corruption).

**Recommended Fix**:
1. Ideal: Use XML-aware rewriting -- parse XML, identify reference element paths, replace only in those locations
2. Pragmatic: Add post-rewrite validation comparing XML structure before/after to detect corruption
3. Minimum: Log all replacement locations (element path, not just count) for audit

---

### MAJ-4: No IDOR Protection on Dev Account Access

**Files**: `integration/flow-service/flow-service-spec.md:69-70`
**Consensus**: Major
**Source**: Architect MAJ-5

Process A (`listDevPackages`) accepts `devAccountId` as a request field without backend validation that the requesting user is authorized to access that account. The IDOR chain extends through Processes A, B, and C -- a caller with the API token could view packages from and promote components from any dev account, not just their authorized ones.

**Mitigating factors**: Requires API token + knowledge of other account GUIDs. The Flow UI only shows accessible accounts. Practical exploitation is unlikely but the authorization gap is real.

**Recommended Fix**:
1. Add server-side validation in Process C (the most critical action) that cross-checks `devAccountId` against DevAccountAccess records for the user's SSO groups
2. Consider adding the same check to Process A for defense-in-depth

---

### MAJ-5: No Token Rotation Operational Guidance

**Files**: `integration/flow-service/flow-service-spec.md:690-708`
**Consensus**: Major
**Source**: Expert MAJ-1

The Security Considerations section recommends 90-day token rotation but provides no procedure: no blue-green rotation strategy, no monitoring for token age, no documentation of behavior during rotation (e.g., what happens to in-flight operations if the token changes mid-execution).

**Impact**: The API token is the sole security boundary (per MAJ-1). Lack of a rotation procedure means it will likely never be rotated, accumulating risk over time.

**Recommended Fix**:
1. Document step-by-step rotation procedure: (1) create new token, (2) update connector config, (3) test with read-only call, (4) revoke old token
2. Document graceful failure behavior on 401 responses
3. Add monitoring guidance for token age

---

## Minor Findings (verified)

### MIN-1: SSO Group Name Inconsistency Across Docs

**Files**: `flow/page-layouts/page5-peer-review-queue.md:10`, `flow/page-layouts/page7-admin-approval-queue.md:10`, vs. `docs/architecture.md:121-123`, `flow/flow-structure.md:18`
**Consensus**: Minor (Expert rated Critical; DA downgraded -- documentation inconsistency, not runtime vulnerability; already flagged in Wave 1)
**Source**: Expert CRIT-2

Pages 5 and 7 reference `"Boomi Developers"` / `"Boomi Admins"` (Azure AD display names) while architecture.md and flow-structure.md use `ABC_BOOMI_FLOW_CONTRIBUTOR` / `ABC_BOOMI_FLOW_ADMIN` (claim values). Could cause build-time configuration errors.

**Fix**: Standardize all references to `ABC_BOOMI_FLOW_*` claim values. Add a build guide note: "Verify group identifier format matches your Azure AD SSO claim configuration."

---

### MIN-2: SSO Group Names Are Hardcoded Constants

**Files**: `docs/architecture.md:115-130`, `integration/flow-service/flow-service-spec.md:46-48`
**Consensus**: Minor
**Source**: Expert MIN-1

The `ABC_BOOMI_FLOW_*` prefixes are hardcoded throughout processes and documentation. Acceptable for an enterprise application with stable naming conventions but creates coupling if the organization changes its group naming.

**Fix**: Document the coupling. Consider extracting to Dynamic Process Properties for maintainability.

---

### MIN-3: normalize-xml.groovy Fallback Passes Raw XML on Parse Failure

**File**: `integration/scripts/normalize-xml.groovy:58-62`
**Consensus**: Minor
**Source**: Architect MIN-4

On XML parse failure, the script passes raw (potentially unstripped) XML to the diff viewer. Combined with CRIT-2 (incomplete stripping), this could display credentials.

**Fix**: On parse failure, return an error placeholder (e.g., `"[XML parsing failed - content not available for diff]"`) rather than raw content.

---

### MIN-4: 5 of 6 Groovy Scripts Lack Required try/catch Error Handling

**Files**: `strip-env-config.groovy`, `rewrite-references.groovy`, `sort-by-dependency.groovy`, `validate-connection-mappings.groovy` (no try/catch); `build-visited-set.groovy` (partial)
**Consensus**: Minor
**Source**: Architect MIN-1

Violates the project's own `groovy-standards.md` which mandates top-level try/catch with `logger.severe()`. Only `normalize-xml.groovy` complies. Unhandled exceptions may expose stack traces in Process Reporting.

**Fix**: Add top-level try/catch to all scripts per groovy-standards.md. For `strip-env-config.groovy` specifically, the catch block should FAIL the promotion (not pass through unstripped XML).

---

### MIN-5: Email Notifications Contain Sensitive Metadata Sent to Broad Distribution Lists

**Files**: `flow/flow-structure.md:361-520`
**Consensus**: Minor
**Source**: Expert MIN-6, Architect MIN-3

Email notifications include promotion IDs, process names, component counts, submitter/reviewer emails, and hotfix justifications -- all sent to distribution lists. All developers see every promotion's metadata regardless of dev account access.

**Fix**: Consider scoping notifications to the relevant dev team group. For hotfix notifications, restrict to admins only. Document as acceptable information sharing if broad visibility is desired.

---

### MIN-6: No Rate Limiting on Peer Review Actions

**Files**: `integration/flow-service/flow-service-spec.md:355-384`
**Consensus**: Minor
**Source**: Expert MIN-2, Architect MIN-5

No documented rate limiting or replay protection on `submitPeerReview`. The `ALREADY_REVIEWED` error code prevents double-submission but no protection against rapid probing.

**Fix**: Log `SELF_REVIEW_NOT_ALLOWED` events with reviewer email and promotion ID. Consider threshold alerts.

---

### MIN-7: No Session Timeout or Re-Authentication Documentation

**Files**: `flow/flow-structure.md:543-550`
**Consensus**: Minor
**Source**: Expert MIN-5

No documented session timeout or re-authentication requirement. A user could leave an approval page open indefinitely and act without re-authenticating. Depends on Boomi Flow's built-in session management.

**Fix**: Document expected SSO session timeout behavior and whether swimlane transitions force re-authentication.

---

### MIN-8: Input Validation Not Documented for API Template Interpolation

**Files**: `integration/api-requests/create-component.xml:29`, `integration/api-requests/create-branch.json:28`
**Consensus**: Minor (Architect rated Major; DA downgraded -- input originates from trusted Boomi platform API, not user input)
**Source**: Architect MAJ-1

Component names and folder paths are interpolated into XML/JSON templates without documented sanitization. Theoretical XML injection and path traversal risks, but inputs originate from the Boomi Platform API which validates them at the source.

**Fix**: Add XML-escaping of `componentName` as defense-in-depth documentation note. Validate `promotionId` as UUID format before use in branch names.

---

## Observations

### Positive Patterns (Unanimous Agreement)

1. **Two-axis SSO model is well-designed**: Team groups (account visibility) separated from tier groups (dashboard capability). ADMIN bypasses team checks (correct for oversight). CONTRIBUTOR access scoped by team membership.

2. **Connection separation is a strong security pattern**: Not promoting connections prevents credential leakage between environments. Admin-seeded mappings via `#Connections` folder provides centralized control.

3. **Branching strategy provides natural isolation**: Promotion-to-branch means unapproved changes never touch production components. OVERRIDE merge strategy is safe because Process C is the sole writer.

4. **Dual-layer self-review prevention**: Backend exclusion (E2) + UI Decision step provides redundancy, even if both layers share the case sensitivity weakness.

5. **120ms API call gap as built-in rate limiting**: Provides both performance and abuse prevention.

6. **DataHub as authorization store is sound**: Match rules provide built-in integrity. ADMIN_CONFIG source ensures only admins modify access records.

---

## Areas of Agreement

All three reviewers agree on:

1. **Case-insensitive email normalization is the highest-priority fix** -- low cost, eliminates the most exploitable vulnerability.
2. **Credential stripping must be expanded** -- the current 5-element list is insufficient and the approach (exact match) is fragile.
3. **Client-supplied `userSsoGroups` is a platform constraint** -- document and mitigate rather than trying to solve at the process level.
4. **Admin self-approval is a genuine gap** in the 2-layer model.
5. **The API token is the real security boundary** -- all "direct API call" attack vectors are gated by possession of this credential.
6. **Groovy scripts need consistent error handling** per the project's own standards.
7. **The multi-environment model does not introduce significant new attack surfaces** beyond those in the single-path architecture.

---

## Unresolved Debates

### 1. Severity of `userSsoGroups` as Untrusted Input

**Expert position**: Major (platform constraint, mitigated by API token boundary)
**Architect position**: Critical (enables tier escalation, defense-in-depth is illusory)
**DA resolution**: Major. The API token grants full access regardless, making group fabrication redundant. Documented as accepted risk.

### 2. Severity of SSO Group Name Inconsistency

**Expert position**: Critical (functional authorization failure if builder uses display names)
**DA position**: Minor (documentation defect, not runtime vulnerability; builder follows primary docs)
**Resolution**: Minor for this review. Already flagged in Wave 1 Team 4 consensus.

### 3. Value of Adding Tier Re-Validation to Process D and F

**Expert position**: Major gap -- should validate in all sensitive processes
**DA position**: Minor -- re-validating the same untrusted input adds marginal security
**Resolution**: Minor. Document the inconsistency. If the platform adds server-side SSO validation in the future, extend validation across all processes at that time.

---

## Multi-Environment Coherence Assessment

### Test Deployment Path: Adequate Security

- Test deployments skip peer/admin review by design -- acceptable for non-production
- Branch preservation increases exposure window but 30-day stale warning mitigates
- All findings (credential stripping, self-review, IDOR) apply equally to test and production paths

### Hotfix Path: Well-Designed

- Hotfix path still requires 2-layer review (peer + admin) -- correctly maintained
- Mandatory justification and admin acknowledgment checkbox provide strong gating
- `isHotfix` and `hotfixJustification` logged for audit -- good compliance trail

### Branch Lifecycle: Strong

- All terminal paths delete branches -- no orphan risk
- `branchId` tracking with null-on-cleanup provides audit trail
- Branch limit lowered from 18 to 15 for multi-environment headroom

### Cross-Environment Consistency

The multi-environment model does not introduce new security vulnerabilities. The existing findings (CRIT-1, CRIT-2, MAJ-1 through MAJ-5) apply uniformly across all deployment paths. The hotfix path is appropriately gated with additional UX-level controls.

---

## Priority Recommendations (Ordered by Impact)

| Priority | Finding | Effort | Impact |
|----------|---------|--------|--------|
| 1 | CRIT-1: Email case normalization | Low (< 1 day) | Eliminates self-review bypass |
| 2 | CRIT-2: Expand credential stripping | Medium (2-3 days) | Prevents credential exposure in diffs |
| 3 | MAJ-2: Admin self-approval check | Low (< 1 day) | Enforces full 2-layer independence |
| 4 | MAJ-1: Document API token as security boundary | Low (< 1 day) | Clarifies threat model |
| 5 | MIN-4: Add try/catch to all Groovy scripts | Low (1 day) | Meets project standards |
| 6 | MAJ-3: Post-rewrite validation for reference rewriting | Medium (2-3 days) | Prevents silent data corruption |
| 7 | MAJ-5: Token rotation procedure | Low (< 1 day) | Operational security hygiene |
| 8 | MAJ-4: IDOR protection on devAccountId | Medium (2-3 days) | Enforces account authorization |

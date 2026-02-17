# Team 5 — Security Architect Findings

**Reviewer**: Security Architect
**Date**: 2026-02-16
**Scope**: Full attack surface analysis — credential protection, injection risks, authorization bypass, self-review enforcement, API security

---

## Critical Findings

### CRIT-1: strip-env-config.groovy Misses Multiple Sensitive Element Categories

**File**: `integration/scripts/strip-env-config.groovy:20-58`
**Severity**: Critical
**Category**: Credential Protection / Sensitive Data Exposure

The credential stripping script only targets 5 element name patterns: `password`, `host`, `url`, `port`, `EncryptedValue`. This is an allowlist approach applied via exact element name matching, which is inherently fragile and incomplete.

**Missing sensitive element patterns:**

1. **API keys and tokens**: Boomi component XML may contain elements named `apiKey`, `apiToken`, `token`, `accessKey`, `secretKey`, `accessToken`, `refreshToken`, `bearerToken`, `clientSecret`, `clientId` (when containing a secret value), `oauthToken`, `authToken`
2. **Username/credential pairs**: `username`, `user`, `login`, `credential`, `secret` — while `password` is caught, companion fields like `username` may reveal service accounts when paired with logs
3. **Connection strings**: `connectionString`, `connectionUrl`, `jdbcUrl`, `dsn` — these embed credentials in many database formats (e.g., `jdbc:mysql://user:pass@host/db`)
4. **Certificate/key material**: `privateKey`, `certificate`, `keystore`, `keystorePassword`, `truststorePassword`, `sslCertificate`, `pemKey`
5. **Proxy credentials**: `proxyPassword`, `proxyUser`, `proxyHost`
6. **Custom properties**: Boomi processes can store sensitive values in custom Extension Properties that use arbitrary element names not covered by any hardcoded pattern

**Root cause**: The script uses exact element name matching (`it.name() == 'password'`), not a regex or pattern-based approach. New component types added to Boomi (or custom extensions) will silently pass through without stripping.

**Risk**: Credentials, API keys, or certificates from dev environments could be promoted to the production branch and visible in the XML diff viewer (Process G, Pages 3/6/7) before being merged. Anyone with Peer Review or Admin access could view leaked dev credentials.

**Recommendation**:
1. Expand the element name list to cover all known Boomi sensitive element patterns (see list above)
2. Add regex-based matching for elements whose names contain `password`, `secret`, `key`, `token`, `credential` (case-insensitive) as a catch-all safety net
3. Add attribute-based stripping: Boomi XML sometimes stores sensitive values in attributes (e.g., `value=""` on configuration elements), not just element text
4. Consider a denylist+allowlist hybrid: strip ALL element text by default for connection-type components, then allowlist only known safe fields

---

### CRIT-2: Client-Supplied `userSsoGroups` Enables Tier Escalation

**File**: `integration/profiles/executePromotion-request.json:13`, `integration/flow-service/flow-service-spec.md:138`, `docs/architecture.md:125-137`
**Severity**: Critical
**Category**: Authorization Bypass / Privilege Escalation

The `userSsoGroups` array is passed as a **client-supplied request field** from the Flow application to backend processes (A0 and C). The architecture documents this as "defense-in-depth" re-validation, but the fundamental flaw is that the SSO group list is extracted at the Flow layer and forwarded as untrusted input to backend processes that trust it for authorization decisions.

**Attack vector**: If an attacker can call the Flow Service endpoint directly (bypassing the Flow UI) or manipulate the Flow state, they could inject `"ABC_BOOMI_FLOW_ADMIN"` into the `userSsoGroups` array and escalate their tier from CONTRIBUTOR to ADMIN or from READONLY to CONTRIBUTOR.

**Why this matters**:
- Process A0 uses `userSsoGroups` to determine `effectiveTier` and which dev accounts to return (architecture.md:126-130)
- Process C re-validates tier from the same client-supplied array (flow-service-spec.md:138) — re-validating against untrusted data provides zero additional security
- The Flow Service endpoint (`/fs/PromotionService`) uses Basic Auth with a shared credential, not per-user identity — so the backend has no independent way to verify the user's actual SSO groups

**Mitigations already in place**: Flow swimlane authorization restricts UI access by SSO group. However, the backend Flow Service endpoint is a standard HTTP endpoint accessible to anyone with the Basic Auth credentials.

**Recommendation**:
1. **Ideal**: Pass the authenticated user's SSO token (JWT or SAML assertion) to backend processes and validate group claims server-side against the identity provider
2. **Pragmatic**: Document this as an accepted risk with the understanding that Flow Service Basic Auth credentials must be treated as highly sensitive and never exposed. Add a security note that the Flow Service endpoint MUST NOT be exposed to end users — only Flow itself should call it
3. **Minimum**: Add IP allowlisting or mutual TLS between the Flow runtime and the Flow Service endpoint to prevent direct API calls

---

## Major Findings

### MAJ-1: No Input Validation on Component Names in API Templates

**File**: `integration/api-requests/create-component.xml:29`, `integration/api-requests/update-component.xml:30`, `integration/api-requests/create-branch.json:28`
**Severity**: Major
**Category**: Injection Risk

Component names (`{componentName}`), folder paths (`{devFolderFullPath}`), and promotion IDs (`{promotionId}`) are interpolated directly into XML templates and URL paths without sanitization or validation.

**XML injection vector**: A malicious component name containing XML metacharacters (e.g., `My Process" type="process" newAttribute="injected`) could break the XML structure in `create-component.xml` line 29:
```xml
<bns:Component ... name="{componentName}" type="{componentType}" ...>
```
If `{componentName}` contains unescaped quotes or angle brackets, it could inject attributes or elements.

**Path traversal vector**: The `folderFullPath` field is constructed as `/Promoted{devFolderFullPath}` (create-component.xml:14). A crafted `devFolderFullPath` like `/../../../SensitiveFolder/` could potentially write components outside the intended `/Promoted/` hierarchy.

**Mitigating factors**:
- Boomi Platform API likely performs its own XML parsing and would reject malformed XML
- The folder path `/Promoted{devFolderFullPath}` prefix provides some protection
- Component names originate from the Boomi platform (not arbitrary user input)

**Recommendation**:
1. Sanitize `componentName` by XML-escaping special characters (`&`, `<`, `>`, `"`, `'`) before template interpolation
2. Validate `devFolderFullPath` against a whitelist pattern (alphanumeric, forward slashes, hyphens, underscores only) and reject path traversal sequences (`..`)
3. Validate `promotionId` as UUID format before use in branch names and API URLs
4. Document that Boomi's HTTP Client connector handles XML encoding — if so, this is mitigated at the platform level, but defense-in-depth encoding in templates is still recommended

---

### MAJ-2: Self-Review Enforcement Relies on Client-Supplied Email

**File**: `flow/page-layouts/page5-peer-review-queue.md:107-118`, `flow/page-layouts/page6-peer-review-detail.md:16-17`, `integration/flow-service/flow-service-spec.md:333,369-370`
**Severity**: Major
**Category**: Self-Review Bypass

Self-review prevention has two layers, but both ultimately depend on client-supplied identity:

**Layer 1 — Backend (Process E2)**: `queryPeerReviewQueue` receives `requesterEmail` from the request payload (flow-service-spec.md:333). This email is extracted from `$User/Email` in the Flow runtime, but it arrives at the backend as a plain string field. If the Flow Service is called directly, any email address could be supplied.

**Layer 2 — Backend (Process E3)**: `submitPeerReview` receives `reviewerEmail` from the request payload (flow-service-spec.md:369). Process E3 compares `reviewerEmail` with the promotion's `initiatedBy` field. Again, `reviewerEmail` is client-supplied.

**Layer 3 — UI (Flow Decision step)**: Page 5 and 6 compare `$User/Email` with `selectedPeerReview.initiatedBy`. This is enforced at the Flow layer and harder to bypass, but the Flow state could theoretically be manipulated.

**Attack scenario**: A developer calls `submitPeerReview` directly against the Flow Service endpoint with a forged `reviewerEmail` different from their actual identity, bypassing the self-review check in Process E3.

**Mitigating factors**: Requires access to the Flow Service Basic Auth credentials and knowledge of the API contract.

**Recommendation**:
1. If the Flow runtime provides a trusted identity header or token, Process E3 should extract the reviewer identity from that trusted context rather than accepting it as a request field
2. At minimum, log the actual HTTP caller identity (from Basic Auth or HTTP headers) alongside the claimed `reviewerEmail` for audit trail purposes
3. Consider adding a `$User/Email` claim validation at the Flow Service operation level if the platform supports it

---

### MAJ-3: Broad Reference Rewriting via Blind String Replacement

**File**: `integration/scripts/rewrite-references.groovy:27-34`
**Severity**: Major
**Category**: Data Integrity / Unintended Modification

The reference rewriting script performs global string replacement of dev component IDs with prod IDs across the entire XML document:

```groovy
xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
```

This replaces ALL occurrences of the dev ID anywhere in the XML — including inside text content, comments, CDATA sections, and attribute values. If a dev component ID string coincidentally appears in a non-reference context (e.g., in a documentation comment, a log message template, or an error message string), it would be incorrectly rewritten.

**Risk scenarios**:
1. A GUID fragment that matches a dev component ID inside a Groovy script data process step (embedded in component XML) — the script code would be silently corrupted
2. A component name or description containing a GUID reference for documentation purposes
3. An XML comment containing a component ID for tracking purposes

**Mitigating factors**:
- GUIDs are 36 characters long, making accidental collisions unlikely
- The script uses `Pattern.quote()` to avoid regex interpretation issues
- Boomi components typically reference other components through specific XML element structures

**Recommendation**:
1. Use XML-aware rewriting instead of blind string replacement: parse the XML, identify known reference element paths (e.g., `componentId` attributes, `<referenceComponentId>` elements), and replace only in those locations
2. If XML-aware rewriting is too complex for the Boomi sandbox, add a post-rewrite validation step that compares the XML structure before and after to ensure no structural corruption occurred
3. Log all replacement locations (not just count) for audit purposes

---

### MAJ-4: Flow Service Basic Auth Credentials Shared Across All Users

**File**: `integration/flow-service/flow-service-spec.md:548-551`, `docs/architecture.md:69-70`
**Severity**: Major
**Category**: API Security / Authentication

The Flow Service uses a single Basic Auth credential pair (Shared Web Server User + API Token) for all requests from the Flow application. This means:

1. **No per-user identity at the API layer**: All requests arrive at the Flow Service with the same credential, regardless of which user initiated them. The backend cannot independently verify who the actual user is.
2. **Single credential compromise = full access**: If the Basic Auth token is leaked, an attacker gains access to all 12 message actions with no per-user restrictions.
3. **No granular revocation**: Rotating the token affects all users simultaneously.
4. **Audit gap**: Process Reporting logs show all executions under the same service account, making it impossible to trace actions to individual users at the platform level.

**Mitigating factors**:
- Flow runtime manages the credential and users never see it directly
- All communication is over HTTPS
- Flow swimlane authorization provides user-level gating at the UI layer

**Recommendation**:
1. Document that the Basic Auth token is a shared service credential and must be treated with the same sensitivity as a database root password
2. Implement token rotation policy (spec recommends 90 days — enforce this)
3. Consider API gateway or IP allowlisting to restrict Flow Service access to only the Flow runtime
4. Add user identity propagation via a custom HTTP header from Flow to Integration (e.g., `X-Flow-User-Email`) signed or hashed with a shared secret — even though it can be spoofed from direct calls, it creates an additional audit trail

---

### MAJ-5: No IDOR Protection on Dev Account Access

**File**: `integration/flow-service/flow-service-spec.md:69-70`, `flow/page-layouts/page1-package-browser.md:49-51`
**Severity**: Major
**Category**: IDOR (Insecure Direct Object Reference)

Process A (listDevPackages) accepts `devAccountId` as a request field and queries that account's packages using `overrideAccount`. There is no backend validation that the requesting user is authorized to access that specific dev account.

**Attack scenario**: A CONTRIBUTOR user who has access only to DevTeamA's account could:
1. Observe the request format from Page 1
2. Modify the `devAccountId` to DevTeamB's account ID
3. Call `listDevPackages` with DevTeamB's account ID
4. See packages from an account they should not have access to
5. Subsequently call `resolveDependencies` and `executePromotion` for components from that unauthorized account

**Authorization flow gap**: Process A0 correctly resolves accessible accounts based on SSO groups, but no subsequent process re-validates that the `devAccountId` in the request is one of the user's authorized accounts.

**Mitigating factors**:
- Requires knowledge of other account IDs (which are GUIDs, not guessable)
- Flow UI only shows accessible accounts in the dropdown
- Requires Flow Service Basic Auth credentials for direct API calls

**Recommendation**:
1. Processes A, B, and C should validate `devAccountId` against the user's authorized accounts (either by re-running the A0 lookup or by accepting a signed/verified account list)
2. At minimum, add server-side validation in Process C (the most critical action) that cross-checks `devAccountId` against DevAccountAccess records for the user's SSO groups

---

## Minor Findings

### MIN-1: Groovy Scripts Lack try/catch Error Handling

**Files**: `integration/scripts/strip-env-config.groovy` (entire file), `integration/scripts/rewrite-references.groovy` (entire file), `integration/scripts/build-visited-set.groovy:43-57` (partial), `integration/scripts/sort-by-dependency.groovy` (entire file), `integration/scripts/validate-connection-mappings.groovy` (entire file)
**Severity**: Minor
**Category**: Error Handling / Information Disclosure

Per `.claude/rules/groovy-standards.md`, all Groovy scripts MUST be wrapped in try/catch blocks. However, only `normalize-xml.groovy` follows this pattern. The other five scripts have no top-level error handling.

**Security implication**: Unhandled exceptions may expose stack traces, internal paths, or XML content in Process Reporting logs. While Process Reporting is internal, verbose error messages could leak sensitive information to anyone with AtomSphere access.

**Recommendation**: Wrap all scripts in try/catch with sanitized error messages per the groovy-standards rule.

---

### MIN-2: Branch Name Predictability

**File**: `integration/api-requests/create-branch.json:28`, `docs/architecture.md:87`
**Severity**: Minor
**Category**: Information Disclosure

Branch names follow the pattern `promo-{promotionId}` where `promotionId` is a UUID. While UUIDs are not guessable, the branch name pattern is predictable and publicly documented. If an attacker knows a `promotionId` (visible in email notifications and UI), they can derive the branch name and potentially the `branchId`.

**Risk**: Low — branch operations require Partner API credentials, and the `branchId` (separate from the branch name) is required for most operations.

**Recommendation**: Document this as an accepted risk. The branch name is informational, not a security boundary.

---

### MIN-3: Email Notifications Contain Sensitive Metadata

**File**: `flow/flow-structure.md:362-520`
**Severity**: Minor
**Category**: Information Disclosure

Email notifications include `promotionId`, `processName`, `packageVersion`, `componentCount`, submitter/reviewer names and emails, and hotfix justifications. These are sent to distribution lists.

**Risk**: If email distribution lists have broad membership, internal promotion details and personnel involved in hotfix decisions are disclosed to a wide audience.

**Recommendation**:
1. Review distribution list membership to ensure it is appropriately scoped
2. Consider omitting `promotionId` from email subject lines (keep it in the body for reference)
3. For hotfix notifications, consider restricting recipients to admins only rather than the full dev distribution list

---

### MIN-4: normalize-xml.groovy Fallback Passes Through Unparsed Content

**File**: `integration/scripts/normalize-xml.groovy:57-63`
**Severity**: Minor
**Category**: Sensitive Data Exposure

When XML parsing fails, the script falls through to pass the raw, un-normalized XML to the diff viewer:
```groovy
} catch (Exception e) {
    logger.severe("Failed to normalize XML: ${e.message}")
    dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
}
```

If the XML contains un-stripped sensitive values (due to CRIT-1 gaps in strip-env-config.groovy), the fallback path would display them raw in the diff viewer without any normalization or sanitization.

**Recommendation**: On parse failure, consider returning an error placeholder rather than raw XML, or apply string-level sanitization as a fallback.

---

### MIN-5: No Rate Limiting on Peer Review Actions

**File**: `integration/flow-service/flow-service-spec.md:355-384`
**Severity**: Minor
**Category**: Abuse Prevention

`submitPeerReview` has no documented rate limiting or replay protection. While the `ALREADY_REVIEWED` error code prevents double-submission, there is no protection against rapid successive calls attempting to race-condition the review state.

**Recommendation**: Add idempotency checks (e.g., compare `peerReviewedBy` on re-attempts) and consider a short cooldown between review actions per user.

---

## Observations

### OBS-1: Defense-in-Depth Strategy is Present but Incomplete

The architecture demonstrates awareness of defense-in-depth:
- Tier validation in both A0 and C
- Self-review prevention at both UI and backend
- Branch cleanup on all terminal paths

However, the defense-in-depth is undermined by relying on client-supplied identity data (`userSsoGroups`, `reviewerEmail`, `requesterEmail`) rather than server-verified identity. The "depth" layers all validate the same untrusted input rather than independent identity sources.

### OBS-2: DataHub as Authorization Store is Sound

Using DataHub for DevAccountAccess (SSO group -> account mapping) is architecturally appropriate. The match rules provide built-in integrity, and the ADMIN_CONFIG source ensures only admins can modify access control records.

### OBS-3: Connection Separation is a Strong Security Pattern

Not promoting connections and instead requiring admin-seeded mappings is an excellent security decision. This ensures:
- Dev credentials never reach production
- Connection configurations are centrally managed
- The `#Connections` folder provides a single audit point

### OBS-4: Branching Strategy Provides Natural Isolation

The promotion-to-branch (not main) pattern means unapproved changes never touch production components. The OVERRIDE merge strategy, while aggressive, is safe because Process C is the sole writer to each promotion branch.

### OBS-5: 120ms API Call Gap is Good but Undocumented as Security Measure

The 120ms gap between API calls (architecture.md:214) provides built-in rate limiting for promotion operations. This should be documented as both a performance and security measure.

---

## Multi-Environment Security Assessment

### Test Deployment Path Security: Adequate

- Test deployments skip peer/admin review by design (architecture.md:227) — this is acceptable because test environments are non-production
- Branch preservation for test deployments increases the window of exposure for branch content — the 30-day stale warning is a reasonable mitigation

### Hotfix Path Security: Well-Designed

- Hotfix path still requires both peer review AND admin review (architecture.md:236-239)
- Mandatory justification text provides audit trail
- Admin acknowledgment checkbox (page7-admin-approval-queue.md:294-298) is a strong UX-level gate
- `isHotfix` and `hotfixJustification` logged in PromotionLog for leadership review (architecture.md:292-295)

### Branch Lifecycle Security: Strong

- Branch limit of 15 (not 20) provides headroom for multi-environment
- All terminal paths delete branches — no orphaned branch risk
- `branchId` tracking in PromotionLog (set to null after cleanup) provides audit trail
- Test-to-production path skips merge because content is already on main from test — logically sound

### Overall Multi-Environment Security Verdict

The multi-environment model does not introduce significant new attack surfaces beyond those already present in the single-path architecture. The hotfix bypass is properly gated with 2-layer review, audit logging, and admin acknowledgment. The primary risk is branch slot exhaustion from stale test deployments, which is addressed with UI warnings.

---

## Summary Matrix

| # | Severity | Category | Finding | File(s) |
|---|----------|----------|---------|---------|
| CRIT-1 | Critical | Credential Protection | strip-env-config.groovy misses API keys, tokens, certificates, connection strings, proxy creds | `strip-env-config.groovy:20-58` |
| CRIT-2 | Critical | Authorization Bypass | Client-supplied `userSsoGroups` enables tier escalation via direct API calls | `executePromotion-request.json:13`, `flow-service-spec.md:138` |
| MAJ-1 | Major | Injection Risk | No input validation on component names/paths in XML API templates | `create-component.xml:29`, `update-component.xml:30` |
| MAJ-2 | Major | Self-Review Bypass | Self-review enforcement relies on client-supplied email addresses | `flow-service-spec.md:333,369-370` |
| MAJ-3 | Major | Data Integrity | Blind string replacement in reference rewriting may corrupt non-reference content | `rewrite-references.groovy:27-34` |
| MAJ-4 | Major | API Security | Single Basic Auth credential shared across all users — no per-user identity at API layer | `flow-service-spec.md:548-551` |
| MAJ-5 | Major | IDOR | No backend validation that user is authorized to access requested devAccountId | `flow-service-spec.md:69-70` |
| MIN-1 | Minor | Error Handling | 5 of 6 Groovy scripts lack required try/catch error handling | Multiple scripts |
| MIN-2 | Minor | Info Disclosure | Predictable branch naming from promotionId | `create-branch.json:28` |
| MIN-3 | Minor | Info Disclosure | Email notifications contain sensitive metadata sent to broad lists | `flow-structure.md:362-520` |
| MIN-4 | Minor | Sensitive Data | normalize-xml.groovy passes raw XML on parse failure | `normalize-xml.groovy:57-63` |
| MIN-5 | Minor | Abuse Prevention | No rate limiting on peer review actions | `flow-service-spec.md:355-384` |

---

## Cross-Reference with Wave 1 Findings

Team 1 (Data Architecture) identified profile-layer gaps (CC-1, CC-2, CM-1) that have security implications:

- **CC-1** (queryStatus missing multi-env fields): `targetEnvironment` absence means the UI cannot correctly distinguish test vs production records — while not directly a security issue, it could cause users to accidentally approve test records for production or vice versa.
- **CM-6** (`packageVersion` missing from PromotionLog): This is primarily a data completeness issue, not security-relevant.
- The data architecture findings are consistent with this security review — the model layer is sound, but the interface layers (profiles, specs, Flow UI) need tightening.

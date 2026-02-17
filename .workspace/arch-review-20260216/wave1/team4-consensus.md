# Team 4 -- Flow Dashboard Consensus

**Domain:** Flow Dashboard (flow-structure.md, page layouts 1-9, build guides 15-16-22, XmlDiffViewer, flow-service-spec cross-reference)
**Reviewers:** Flow Platform Expert, UX/Workflow Architect, Devil's Advocate
**Date:** 2026-02-16

---

## Critical Findings (verified)

### CRIT-1: React Hook Called Conditionally in XmlDiffViewer (Code Bug)

**Source:** Architect C1 | **DA Verdict:** Verified Critical
**File:** `flow/custom-components/xml-diff-viewer/src/XmlDiffViewer.tsx:59`

The `useDiffStats` hook is called after three early returns (lines 43-56), violating React's Rules of Hooks. When the component transitions between loading/error and data-present states, React will throw "Rendered fewer hooks than expected" and crash. The `useResponsive` and `useState` hooks at lines 26-32 are unconditional (correct), but `useDiffStats` at line 59 is conditional (broken).

**Fix:** Move `useDiffStats` above all early returns. Pass empty strings when data is unavailable.

**Impact:** Production crash on the diff viewer used on Pages 3, 6, and 7.

### CRIT-2: SSO Group Name Inconsistency Across Specifications

**Source:** Expert C1 | **DA Verdict:** Verified Critical
**Files:** flow-structure.md:18, page5-peer-review-queue.md:10, page7-admin-approval-queue.md:10, page9-production-readiness.md:9, build-guide/15:49, build-guide/16:99-101, page4-deployment-submission.md:560

Two naming conventions are mixed across the specification:
- Claim/identifier format: `ABC_BOOMI_FLOW_CONTRIBUTOR`, `ABC_BOOMI_FLOW_ADMIN` (flow-structure.md, page9, flow-service-spec tier algorithm)
- Display-name format: `"Boomi Developers"`, `"Boomi Admins"` (page5, page7, build guides 15/16, page4)

Azure AD SSO claim values and display names are distinct identifiers. Using the wrong one causes authorization failures. The flow-service-spec's tier resolution algorithm (lines 46-48) uses the `ABC_BOOMI_FLOW_*` format, which implies these are the actual claim values.

**Fix:** Standardize all references to `ABC_BOOMI_FLOW_*` format. Add a mapping table in flow-structure.md clarifying the display name equivalents.

---

## Major Findings (verified)

### MAJ-1: Build Guide and Navigation Missing Page 9 Wiring

**Source:** Expert C2/C3, Architect M4 | **DA Verdict:** Merged to Major
**Files:** build-guide/15:59, build-guide/16:113-128, build-guide/22:201-205, flow-structure.md:127, page4-deployment-submission.md:303

Build guide Step 5.2 says "Build the 8 pages in order." Step 5.4 lists 16 navigation outcomes covering Pages 1-8 only. Page 9 is absent from the core navigation wiring. Phase 7 (build-guide/22:201-205) adds Page 9 with 5 bullet points but no step-by-step outcome wiring.

Additionally, Page 9 has only one documented entry point: the "View in Production Readiness" button on Page 4 after a successful test deployment. There is no sidebar, tab, or link from Page 1 that allows developers to return to Page 9 independently (e.g., days after a test deployment). The test deployment email says "return to the Production Readiness page" but provides no direct link.

**Fix:** (1) Update build guide Step 5.2 to say "9 pages" and add Page 9 wiring to Step 5.4. (2) Add a "Tested Deployments" link/button on Page 1. (3) Include a direct Page 9 link in the test deployment email.

### MAJ-2: Error Page Underspecified (No Dedicated Layout, No Error Categorization)

**Source:** Expert M3, Architect M3 | **DA Verdict:** Merged Major
**Files:** flow-structure.md:522-541

The Error Page is specified inline in flow-structure.md (20 lines) with no dedicated `page-layouts/error-page.md` file, while all 9 content pages have full specifications. Key gaps:
- **Retry button**: No mechanism documented for preserving the original request payload on the Error Page
- **Back button**: "Flow history navigation" is undefined after swimlane transitions
- **No error categorization**: Transient errors (API_RATE_LIMIT) and permanent errors (MISSING_CONNECTION_MAPPINGS) both show the same Retry button, but retrying permanent errors always fails
- **No BRANCH_LIMIT_REACHED guidance**: The Error Page does not direct users to clean up stale branches on Page 9

**Fix:** Create a dedicated error page layout spec. Categorize errors as transient vs. permanent. Show Retry only for transient errors. For permanent errors, provide contextual recovery guidance.

### MAJ-3: Page 7 Merge Workflow Misleadingly Described as UI-Orchestrated

**Source:** Expert M4 | **DA Verdict:** Verified Major (with clarification)
**Files:** page7-admin-approval-queue.md:299-322, flow-service-spec.md:171, 213-240

Page 7's approve workflow describes 5 UI-orchestrated steps: POST MergeRequest, execute merge, poll status, call packageAndDeploy, DELETE Branch. However, the flow-service-spec.md confirms that Process D handles merge, package, deploy, and branch deletion internally for all 3 deployment modes (lines 213-240). Boomi Flow cannot make arbitrary HTTP calls -- it only supports Message Actions via the Integration Service connector.

The Page 7 spec should say: "Call `packageAndDeploy` message action. Show spinner. Display results." The merge/poll/delete steps happen inside Process D.

**Fix:** Rewrite Page 7 approve workflow to show a single `packageAndDeploy` call, not individual REST API steps.

### MAJ-4: Missing Direct-Navigation Guards for Deep Pages

**Source:** Expert M2 | **DA Verdict:** Verified Major (with nuance)
**Files:** All page layouts

No page layout specifies guard behavior when prerequisite Flow values are missing (e.g., bookmarked URL for Page 3 without `promotionResults`). Affected pages within the Developer swimlane (where no re-authentication is required):
- **Page 2**: Requires `selectedPackage` from Page 1
- **Page 3**: Requires `promotionResults` from executePromotion
- **Page 4**: Requires `promotionId`, `targetEnvironment`

Pages in other swimlanes (5-7) have partial protection through swimlane transition re-authentication. Page 9 is safe (loads own data on page load).

**Fix:** Add Decision steps on page load for Pages 2-4 that check required Flow values. If missing, redirect to Page 1.

### MAJ-5: `packageAndDeploy` Usage Misattributed to Page 5

**Source:** Expert M1 | **DA Verdict:** Verified Major
**File:** flow-structure.md:241

Message step 6 documentation says `packageAndDeploy` is "Used in: Page 5, on 'Approve' button click." Page 5 is the Peer Review Queue (no deploy). Correct usage: Page 7 (Admin Approval) and Page 4 (Test Deployment).

**Fix:** Update flow-structure.md:241 to say "Used in: Page 7 (admin approval) and Page 4 (test deployment)."

### MAJ-6: Process E4 Not in Canonical Architecture Documentation

**Source:** Expert M5 | **DA Verdict:** Verified Major
**Files:** CLAUDE.md, docs/architecture.md, integration-patterns.md, flow-service-spec.md:450

Process E4 (`queryTestDeployments`) is documented in flow-service-spec.md:450 and referenced by Page 9, but is absent from CLAUDE.md's 11-process list, architecture.md, and integration-patterns.md's build order. This creates confusion about whether E4 is part of the canonical architecture.

**Fix:** Add Process E4 to CLAUDE.md, architecture.md, and integration-patterns.md process lists. Update the build order to include E4 dependencies.

### MAJ-7: Branch Cleanup Failure Not Handled in Rejection/Denial Paths

**Source:** Architect M5 | **DA Verdict:** Verified Major
**Files:** page6-peer-review-detail.md:268-273, page7-admin-approval-queue.md:409-413

Both peer rejection (Page 6, step 6b) and admin denial (Page 7, step 4b) call `DELETE /Branch/{branchId}` but neither specifies error handling for deletion failure. Boomi has a 20-branch limit per account. Orphaned branches from failed deletions accumulate silently and eventually trigger BRANCH_LIMIT_REACHED errors.

Note: Approved deployments are safe -- Process D handles branch deletion internally for all deployment modes (flow-service-spec.md:219, 228-229, 238).

**Fix:** Add error handling for branch deletion failure on rejection/denial paths. Log `branchCleanupFailed` in PromotionLog. Surface orphaned branches to admins.

### MAJ-8: Page 3 Deployment Target Selection UI Not Formally Specified (DA-discovered)

**Source:** DA-2 | **Severity:** Major
**Files:** flow-structure.md:111-119, page3-promotion-status.md

flow-structure.md:111-119 describes three paths from Page 3 based on deployment target selection (Test, Production, Emergency Hotfix). The Architect references "Page 3's radio button group with card-style options" and "color-coded left borders." However, Page 3's spec (page3-promotion-status.md) is focused on promotion results display and does not clearly define the deployment target selection UI. The three-path branch is assumed but the actual selection mechanism (radio buttons? cards?) is not formally specified in the page layout.

**Fix:** Add a "Deployment Target Selection" section to page3-promotion-status.md with the radio button card UI, conditional rendering logic, and navigation outcomes for each mode.

---

## Minor Findings (verified)

### MIN-1: Page Count Inconsistency (8 vs 9)

**Source:** Expert m1, Architect m1
**Files:** flow-structure.md:8-10, flow-patterns.md:3-20, build-guide/15:59

Multiple documents say "8 pages" while the actual count is 9 (Page 9 added in Phase 7). flow-patterns.md lists only Pages 1-8.

### MIN-2: `selectedPromotion` Flow Value Missing from Values Table

**Source:** Expert m5
**Files:** page7-admin-approval-queue.md:101, flow-structure.md:46-86

Page 7 uses `selectedPromotion` but this Flow value is not declared in the Flow Values table.

### MIN-3: `manageMappings` Request Field Name Mismatch (DA-discovered)

**Source:** DA-1
**Files:** flow-structure.md:259, flow-service-spec.md:303

flow-structure.md calls the field `operation` with values "list"/"create"/"update"/"delete". flow-service-spec.md calls it `action` with values "query"/"update"/"delete" (no "create").

### MIN-4: `userEffectiveTier` Defined but Never Used in Page Guards

**Source:** Expert m2
**Files:** flow-structure.md:57, all page layouts

The `userEffectiveTier` Flow value is populated from getDevAccounts but no page layout uses it for conditional UI rendering.

### MIN-5: Page 9 Missing Explicit Loading State

**Source:** Expert m3
**File:** page9-production-readiness.md

Other pages explicitly specify loading spinners during API calls. Page 9 does not specify a loading state during `queryTestDeployments`.

### MIN-6: Page 8 Delete Mapping Missing Confirmation Modal

**Source:** Expert m8
**File:** page8-mapping-viewer.md:601-619

Deleting a component mapping is destructive (could break future promotions) but has no confirmation modal, unlike other destructive actions (Page 7 Deny, Page 6 Reject).

### MIN-7: `isHotfix` String-Boolean Type Confusion

**Source:** Architect m7
**File:** flow-structure.md:79

`isHotfix` is typed as String with values `"true"`/`"false"` but the `is` prefix implies boolean. This causes comparison bugs if someone checks `isHotfix == true` (boolean) instead of `isHotfix == "true"` (string).

### MIN-8: XML Diff Payload Size Not Bounded

**Source:** Architect C2 (downgraded)
**Files:** flow/custom-components/xml-diff-viewer.md:28-29, page3-promotion-status.md:137-143

No documented size limit for XML diff payloads. Large components (5000+ lines) could cause browser performance issues with client-side diff computation. Typical components are 500-2000 lines (acceptable), but edge cases exist.

### MIN-9: `resolveDependencies` Response Missing Summary Fields (DA-discovered)

**Source:** DA-4
**Files:** flow-service-spec.md:103-112, flow-structure.md:200-204

flow-structure.md expects output values `totalComponents`, `newCount`, `updateCount`, `envConfigCount` from resolveDependencies. The flow-service-spec only returns a `dependencies` array with no summary fields. These would need client-side computation or the spec needs updating.

### MIN-10: Pagination Thresholds Inconsistent

**Source:** Architect m4
**Files:** Multiple page layouts

Page sizes vary (50 for Page 1/8, 25 for Pages 5/7/9) without documented rationale.

### MIN-11: Page 4 Test Success Navigation Not in Build Guide Step 5.4

**Source:** Expert m4
**Files:** page4-deployment-submission.md:302-303, build-guide/16:113-128

"Return to Dashboard" (-> Page 1) and "View in Production Readiness" (-> Page 9) buttons after test deployment are only documented in the page layout, not in the build guide navigation wiring.

---

## Observations

### Positive Patterns
1. **Defense-in-depth self-review prevention**: Backend exclusion (Process E2) + UI Decision step fallback is well-designed
2. **Three-mode deployment architecture**: Test/Production-from-Test/Emergency-Hotfix paths are cleanly separated via `targetEnvironment` and `isHotfix` discriminators
3. **Flow Service async handling**: Proper use of wait responses, IndexedDB persistence, and browser-close resilience
4. **XmlDiffViewer implementation quality**: Good responsive behavior, ARIA attributes, clipboard fallback, and HOC wrapper integration (aside from the hooks bug)
5. **Branch age monitoring**: Color-coded branch age column on Page 9 provides visual governance without hard enforcement
6. **Connection mapping seeding workflow**: Dedicated admin UX on Page 8 for the connection-seeding use case

### Architecture Strengths
- Message Actions (not Data Actions) give full process control for complex orchestration
- Public Cloud Atom avoids firewall issues for all-Boomi infrastructure
- DataHub for state persistence avoids external DB latency issues
- Mirrored folder paths provide predictable organization

---

## Unresolved Debates

### 1. Severity of Page 9 Navigation Gap: Critical vs Major

**Expert position:** Critical (C2/C3) -- builder cannot wire Page 9, user may have no way to reach it
**DA position:** Major -- the build guide gap (C2) is Critical in isolation but the design gap (C3) is Major because there IS one entry point (Page 4 test success button); only independent navigation is missing
**Consensus:** Two distinct issues: (a) Build guide missing Page 9 wiring = need to update build guide (clear fix), (b) Missing independent entry point to Page 9 = design enhancement. Combined severity: **Major** with high priority.

### 2. Whether Process D or UI Orchestrates Merge on Page 7

**Expert position:** Ambiguous -- the spec does not clarify
**DA position:** Resolved -- flow-service-spec.md confirms Process D handles merge internally
**Consensus:** Resolved in favor of Process D. Page 7 spec needs rewriting.

### 3. `createdBy` Field Availability

**Architect position (m2):** `selectedPackage.createdBy` is used but never populated
**DA challenge:** `listDevPackages` response includes `createdBy` (flow-service-spec.md:81); it is available in the data, just not displayed as a column on Page 1
**Consensus:** The field IS available from the API. Page 1 does not show it as a column, but it is part of the `selectedPackage` object when a row is selected. No spec gap; Architect m2 is retracted.

---

## Multi-Environment Coherence Assessment

### Complete Paths
| Path | Pages | Email | Branch Lifecycle | Process D Mode | Status |
|------|-------|-------|-----------------|----------------|--------|
| Test Deploy | 1->2->3->4 (inline) | Email 6 | Preserved | Mode 1: merge+deploy, keep branch | Complete |
| Prod from Test | 9->4->5->6->7 | Email 1, 2/3, 4/5 | Deleted after deploy | Mode 2: skip merge, deploy, delete branch | Complete |
| Emergency Hotfix | 1->2->3->4->5->6->7 | Email 7, 2/3, 4/5 | Deleted after deploy | Mode 3: merge+deploy, delete branch | Complete |

### Multi-Environment Gaps
1. **No "Cancel Test Deployment" on Page 9**: Stale branch warning is advisory only. No mechanism to clean up abandoned test branches.
2. **No re-validation warning for old test deployments**: A 30-day-old test deployment can be promoted to production without warning that main branch may have diverged significantly since testing.
3. **No environment health pre-check**: No connectivity check before test deployment.
4. **Page 4 mode context lost on bookmark**: All three deployment modes share the same Page 4 URL; mode is determined by Flow values only.
5. **No persistent environment badge**: Once a user is on Pages 3-4, target environment is only visible in mode-specific UI, not in a global header.
6. **Phase 7 additions not backported to core docs**: Page 9, Process E4, new Flow values, email notifications 6/7 -- all added to their individual specs but not reflected in CLAUDE.md, integration-patterns.md, flow-patterns.md, or build guide Steps 5.2/5.4.

### Overall Assessment
The three deployment paths are architecturally sound and complete at the process level (Process D handles all modes correctly). The gaps are in the Flow Dashboard specification layer: navigation wiring, page guard conditions, and documentation consistency across the Phase 7 additions.

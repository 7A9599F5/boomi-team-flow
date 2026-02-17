# Team 4: UX/Workflow Architect Review -- Flow Dashboard

**Reviewer:** UX/Workflow Architect
**Date:** 2026-02-16
**Files Reviewed:**
- `flow/flow-structure.md` (550 lines)
- `flow/page-layouts/page1-package-browser.md` through `page9-production-readiness.md` (9 files)
- `docs/build-guide/15-flow-dashboard-developer.md`
- `docs/build-guide/16-flow-dashboard-review-admin.md`
- `flow/custom-components/xml-diff-viewer.md` (spec)
- `flow/custom-components/xml-diff-viewer/src/` (implementation: 16 TSX/TS source files)

---

## Critical Issues

### C1. React Hook Called Conditionally in XmlDiffViewer -- Violates Rules of Hooks

**File:** `flow/custom-components/xml-diff-viewer/src/XmlDiffViewer.tsx:59`

The `useDiffStats` hook is called after early returns (lines 43-56). React hooks must be called unconditionally at the top of a component, in the same order every render. This code will cause a runtime crash when the component transitions between loading/error and data-present states.

```tsx
// Lines 43-56: early returns BEFORE the hook call
if (state?.loading) {
    return <LoadingState />;
}
const data: IDiffData | null = extractDiffData(objectData);
if (!data) {
    return <ErrorState message="No component data available" />;
}
if (!data.branchXml) {
    return <ErrorState message="Branch XML data is missing" />;
}

// Line 59: hook called after conditional returns -- VIOLATION
const stats = useDiffStats(data.mainXml, data.branchXml);
```

**Fix:** Move `useDiffStats` above all early returns and pass empty strings when data is unavailable.

**Impact:** Will cause React "Rendered fewer hooks than expected" error in production when transitioning between loading/error states and data display.

### C2. No Size Limit or Truncation for XML Diff Payloads

**Files:** `flow/custom-components/xml-diff-viewer.md:28-29`, `flow/page-layouts/page3-promotion-status.md:137-143`

The `generateComponentDiff` response delivers full normalized XML strings (`branchXml`, `mainXml`) with no documented size limit. Boomi component XML can be tens of thousands of lines for complex processes. The `react-diff-viewer-continued` library performs line-by-line diffing in the browser -- for XML documents exceeding ~5000 lines, this will cause:
- Multi-second UI freezes during diff computation
- Browser memory pressure (DOM nodes per diff line)
- Potential browser tab crash for very large components

The spec mentions `max-height: 500px` for the scroll container, but DOM nodes are still created for all lines.

**Recommendation:** Add a size check at the `objectData.ts` extraction layer or in the DiffContent component. If XML exceeds a threshold (e.g., 200KB or 5000 lines), show a warning with options: "Show first 500 lines" / "Download raw XML" / "Show anyway (may be slow)." Also consider server-side diff computation for large documents.

---

## Major Issues

### M1. Swimlane Transition Model Produces Disconnected User Sessions

**File:** `flow/flow-structure.md:123-126`, `flow/page-layouts/page4-deployment-submission.md:371-388`

When the developer submits for peer review (Page 4), the flow "pauses at swimlane boundary" and the developer sees a confirmation page. The peer reviewer then starts a "fresh Flow session." This means:

1. The peer reviewer has no navigation history -- they cannot go "back" to see what the developer saw.
2. If the peer reviewer refreshes or returns later, they must re-authenticate and re-navigate to Page 5.
3. There is no mechanism documented for the developer to check the real-time status of their submission after the swimlane transition. They only learn about progress via email.

**Recommendation:** Add a "My Submissions" view accessible from Page 1 that queries the developer's own promotion history (via `queryStatus` with `initiatedBy` filter). This gives developers a way to check progress without waiting for email.

### M2. No Timeout or Cancellation for Long-Running Promotion Execution

**File:** `flow/page-layouts/page2-promotion-review.md:216-231`, `flow/page-layouts/page3-promotion-status.md:36-53`

The `executePromotion` message step can take "several minutes" (per the spec). While the spec correctly notes that Flow Service handles async wait responses and state is persisted, there is no documented:
- **Timeout threshold** -- what happens if the promotion hangs for 30+ minutes?
- **Cancel button** -- can the developer abort a running promotion?
- **Stale promotion detection** -- if a user returns to a URL for a promotion that timed out, what do they see?

**Recommendation:** Define a maximum execution timeout (e.g., 15 minutes). If the Flow Service wait loop exceeds this, transition to an error state with a clear message and retry option. Consider adding a "Cancel Promotion" action that triggers branch deletion and PromotionLog cleanup.

### M3. Error Page Is Underspecified for Context-Dependent Recovery

**File:** `flow/flow-structure.md:522-537`

The shared Error Page has three buttons: Back, Retry, Home. However:
- **Back** uses "Flow history navigation" -- but the spec does not define what this means after a swimlane transition. If a peer reviewer hits an error on Page 6, "Back" should go to Page 5, but flow history may not be available across swimlane boundaries.
- **Retry** "re-executes the failed Message step with same input values" -- but no mechanism is documented for preserving the original request payload on the Error Page. Flow values would need to be carried through the error navigation.
- The Error Page does not distinguish between transient errors (API timeout -- retry is appropriate) and permanent errors (MISSING_CONNECTION_MAPPINGS -- retry will always fail). Different error types should suggest different recovery paths.

**Recommendation:** Add error categorization (transient vs. permanent) in the flow-service error response. Show "Retry" only for transient errors. For permanent errors like `MISSING_CONNECTION_MAPPINGS`, show contextual guidance: "Contact an admin to seed the missing mappings in the Mapping Viewer."

### M4. Page 9 (Production Readiness) Not Reachable from Primary Navigation

**File:** `flow/flow-structure.md:89-133`, `docs/build-guide/16-flow-dashboard-review-admin.md:104-124`

Page 9 (Production Readiness) is listed in the flow-structure.md as step 14, but the build guide's navigation wiring (Step 5.4) only lists 16 outcomes connecting Pages 1-8. Page 9 is not wired into navigation. Additionally:
- The Page 4 test deployment success state mentions a "View in Production Readiness" button, but this is the only documented entry point.
- There is no nav link from Page 1 to Page 9, meaning developers cannot easily find their tested deployments without first completing a new promotion.
- The test deployment email (notification #6) tells the user to "return to the Production Readiness page" but does not provide a direct link to Page 9.

**Recommendation:** Add a "Tested Deployments" or "Production Readiness" link/tab on Page 1 (Package Browser) so developers can reach Page 9 at any time. Wire it into Step 5.4 navigation. Include a direct link in the test deployment email.

### M5. Branch Cleanup Inconsistency Between Peer Rejection and Admin Denial

**File:** `flow/page-layouts/page6-peer-review-detail.md:268-273`, `flow/page-layouts/page7-admin-approval-queue.md:409-413`

Both peer rejection (Page 6) and admin denial (Page 7) include branch deletion (`DELETE /Branch/{branchId}`). However:
- Page 6 rejection calls branch delete as step 6b, after the email notification (step 5).
- Page 7 denial calls branch delete as step 4b, after the email but before the confirmation message (step 5).
- Neither specifies what happens if the branch delete fails. The PromotionLog update (`branchId = null`) is mentioned but there is no Decision step checking branch deletion success.
- If branch deletion fails silently, the system accumulates orphaned branches. Boomi has a branch limit per account.

**Recommendation:** Add explicit error handling for branch deletion failure. If it fails, log a warning in PromotionLog (set `branchCleanupFailed = true`) and surface it to the admin in the Mapping Viewer or a new "Branch Management" section. Consider a periodic cleanup job for orphaned branches.

---

## Minor Issues

### m1. Inconsistent Page Count Between Overview and Body

**File:** `flow/flow-structure.md:10,19-39`

The overview states "9 pages total (4 developer pages + 1 production readiness page, 2 peer review pages, 2 admin pages)" but earlier in the same section says "8 pages" at line 8. The build guide (Step 5.2) says "Build the 8 pages in order" and Step 5.4 only wires Pages 1-8. Page 9 appears to have been added later without updating all references.

### m2. Flow Value `selectedPackage.createdBy` Used but Never Populated

**File:** `flow/flow-structure.md:50`, `flow/page-layouts/page4-deployment-submission.md:337`

The `deploymentRequest` object includes `devPackageCreator: "{selectedPackage.createdBy}"`, and `selectedPackage` is described as containing `createdBy`. However, Page 1 Package Browser (`page1-package-browser.md:71-78`) does not include a `createdBy` column in the data grid columns, and the `listDevPackages` response fields listed are: `componentName`, `packageVersion`, `componentType`, `createdDate`, `notes`. The `createdBy` field is referenced but not documented as part of the API response.

### m3. No Keyboard Shortcut for Common Actions

**File:** All page layouts

Each page layout includes an Accessibility section with keyboard tab navigation, but no keyboard shortcuts are defined for common actions like:
- Ctrl+Enter to submit forms (Pages 4, 6, 7, 8)
- Escape to dismiss modals (Pages 2, 6, 7)
- Arrow keys for grid navigation (Pages 1, 3, 5, 7, 8)

These are standard accessibility patterns for enterprise applications with repetitive workflows.

### m4. Pagination Thresholds Inconsistent Across Pages

**Files:** Multiple page layouts

| Page | Threshold | Page Size |
|------|-----------|-----------|
| Page 1 (Packages) | > 50 packages | 50 rows |
| Page 5 (Peer Review Queue) | > 25 requests | 25 rows |
| Page 7 (Admin Approval Queue) | > 25 requests | 25 rows |
| Page 8 (Mapping Viewer) | Always | 50 rows |
| Page 9 (Production Readiness) | > 25 records | 25 rows |

While different thresholds may be intentional (packages are more numerous), the inconsistency should be documented as a deliberate design decision. Consider a shared configuration constant.

### m5. Confirmation Modal Inconsistency

**File:** `flow/page-layouts/page2-promotion-review.md:196-214`, `flow/page-layouts/page7-admin-approval-queue.md:276-292`

Page 2 (Promote) and Page 7 (Approve and Deploy) both use confirmation modals, but:
- Page 2's modal shows component counts and root process name.
- Page 7's modal shows process name, version, target, and component count but not the peer reviewer info (which is visible in the detail panel below).
- Neither modal includes the package version, which is a key identifier.
- The hotfix acknowledgment checkbox on Page 7 (line 296-297) is a good pattern but is not used on Page 6 when a peer reviewer approves a hotfix.

### m6. Missing Loading State for `listIntegrationPacks` on Page 4

**File:** `flow/page-layouts/page4-deployment-submission.md:57-65`

Page 4 calls `listIntegrationPacks` on load to populate the Integration Pack combobox, but no loading state is specified for the combobox while this API call executes. The combobox would briefly show empty options. Specify a loading indicator (spinner inside the dropdown or disabled state with "Loading packs...").

### m7. `targetEnvironment` Flow Value Type Mismatch

**File:** `flow/flow-structure.md:78-79`

`targetEnvironment` is typed as `String` with values `"TEST"` or `"PRODUCTION"`. But `isHotfix` is also `String` with values `"true"` or `"false"` instead of being a Boolean. This is technically correct for Boomi Flow (which treats most values as strings), but the naming convention (`is` prefix) suggests boolean behavior. This could cause comparison bugs if someone checks `isHotfix == true` (boolean) instead of `isHotfix == "true"` (string).

---

## Observations (Positive)

### O1. Well-Structured 2-Layer Approval Workflow

The peer review + admin review pattern is well-designed with clear separation of concerns. Self-review prevention is enforced at both backend (Process E2 excludes own submissions) and UI (Decision step fallback) levels -- defense in depth is the right approach.

### O2. XmlDiffViewer Implementation Quality

The custom component is well-implemented with:
- Proper Boomi Flow integration via HOC wrapper (`utils/wrapper.tsx`)
- Responsive breakpoint handling (`useResponsive.ts`)
- Graceful degradation: desktop split -> tablet unified -> mobile unified-only
- Clipboard API with `execCommand` fallback (`useClipboard.ts`)
- Comprehensive test suite (38 tests documented)
- Good ARIA attributes: `role="table"`, `role="alert"`, `aria-label` on interactive elements

### O3. State Persistence via IndexedDB

The specification correctly leverages Flow Service's built-in IndexedDB caching for long-running operations. Users can close the browser during promotion execution and return later. This is a significant UX advantage over polling-based approaches.

### O4. Three-Mode Deployment Target Design

The Page 3 deployment target selection (Test / Production from Test / Emergency Hotfix) with conditional UI panels is well-thought-out. The visual hierarchy (green recommended badge vs. red emergency badge) clearly communicates the risk level of each option.

### O5. Connection Mapping Seeding Workflow

The dedicated "Seed Connection Mapping" section on Page 8, separate from the general mapping form, is a good UX decision. It guides admins through the specific connection-seeding workflow with context-appropriate field labels and helper text.

---

## Multi-Environment Assessment

### What Works Well

1. **Clear visual distinction between deployment targets:** Page 3's radio button group with card-style options, color-coded left borders (green for test, red for emergency), and conditional warning banners clearly communicates which environment the user is targeting.

2. **Test-first default:** "Deploy to Test" is pre-selected as default on Page 3, with "(Recommended)" badge. This nudges users toward the safe path.

3. **Audit trail continuity:** The `testPromotionId` flow value links production deployments back to their test predecessors, maintaining traceability across environments.

4. **Branch preservation for test-to-prod flow:** When deploying to test, the promotion branch is preserved so the same code can be promoted to production without re-running the promotion engine.

5. **Branch age monitoring on Page 9:** The color-coded Branch Age column (green 0-14 days, amber 15-30, red >30) with stale branch warnings proactively addresses branch accumulation.

### What Needs Improvement

1. **No environment indicator in global header:** Once a user is on Pages 3-4, the current target environment is only visible in the radio button selection or page header. There should be a persistent environment badge in the application header bar visible on ALL pages (similar to how cloud consoles display "PRODUCTION" in red at the top).

2. **No "test deployment results" carry-forward to peer review:** When a tested deployment goes through peer review (Page 5 -> 6), the peer reviewer can see the test deployment history panel, but there is no link to the actual test results or test deployment logs. The reviewer must trust the green "Previously Tested" badge without being able to verify test outcomes.

3. **Missing test environment health check:** Before deploying to test (Page 4, Mode 1), there is no pre-check to verify the test atom/environment is available and responsive. A failed test deployment wastes developer time. Consider adding a lightweight connectivity check before showing the "Deploy to Test" button.

4. **No rollback path for test deployments:** If a test deployment introduces issues in the test environment, there is no documented mechanism to revert. The branch is preserved for production promotion but there is no "Undo Test Deployment" action. While Boomi's deployment model makes atomic rollback difficult, a "Deploy Previous Version" shortcut would help.

5. **Page 4 mode distinction relies on flow values, not visual URL:** All three deployment modes (test, production-from-test, emergency hotfix) share the same Page 4 URL. If a user bookmarks or shares the Page 4 URL, the mode context is lost. Consider adding mode as a URL parameter or at minimum a very prominent header banner indicating which mode is active.

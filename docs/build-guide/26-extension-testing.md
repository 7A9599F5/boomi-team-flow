## Phase 7 (continued): Extension Editor Testing

This section provides test scenarios for the Extension Editor feature. Run these after completing all Phase 7 build steps.

### Prerequisites

Before testing:
- [ ] All 5 new processes (K-O) deployed and listeners running
- [ ] Flow Service redeployed with 19 message actions
- [ ] Flow connector re-retrieved (38 types visible)
- [ ] ExtensionEditor custom component assets uploaded
- [ ] Pages 10-11 built and published
- [ ] At least one ClientAccountConfig record seeded in DataHub
- [ ] At least one ExtensionAccessMapping record exists (created by Process D post-deployment)

### Test Scenario 1: Client Account Discovery

**Goal:** Verify Process K returns accessible client accounts based on SSO groups.

1. Log in as a user with `ABC_BOOMI_FLOW_CONTRIBUTOR` SSO group.
2. Navigate to Page 10 (Extension Manager).
3. **Expected:** Account selector populated with client accounts mapped to user's SSO group.
4. **Verify:** Each account shows name and environment count.
5. **Edge case:** User with no ClientAccountConfig records sees "No accessible accounts" message.

### Test Scenario 2: Extension Loading

**Goal:** Verify Process L loads environment extensions with access mappings.

1. Select a client account from the dropdown.
2. Select an environment.
3. **Expected:** ExtensionEditor renders with:
   - Tree panel showing Connections, Operations, Process Properties categories
   - Correct item counts per category
4. **Verify:** Access mappings applied — non-admin users see connections as read-only (lock icon, ConnectionBanner).
5. **Edge case:** Empty environment (no extensions configured) shows "No extensions found" message.

### Test Scenario 3: Inline Editing (Contributor)

**Goal:** Verify contributors can edit non-connection extensions within their authorized scope.

1. Log in as `ABC_BOOMI_FLOW_CONTRIBUTOR`.
2. Load extensions for an environment.
3. Select an operation extension in the tree.
4. Click a property value → inline input appears.
5. Change the value and blur/press Enter.
6. **Expected:**
   - Row shows amber "dirty" indicator
   - SaveToolbar shows "1 unsaved change"
   - Undo button enabled
7. Click Save.
8. **Expected:** `updateExtensions` called with `partial="true"`, success toast shown, dirty state cleared.

### Test Scenario 4: Connection Admin Gate

**Goal:** Verify connection extensions are admin-only.

1. Log in as `ABC_BOOMI_FLOW_CONTRIBUTOR`.
2. Select a connection extension in the tree.
3. **Expected:**
   - ConnectionBanner: "Connection extensions require admin access"
   - All property values are read-only (no click-to-edit)
   - Lock icon on the tree item
4. Log in as `ABC_BOOMI_FLOW_ADMIN`.
5. Select the same connection extension.
6. **Expected:**
   - ConnectionBanner: "Connection — admin-only extension"
   - Property values are editable
   - Encrypted fields still show masked values (cannot be edited)

### Test Scenario 5: Shared Resource Warning

**Goal:** Verify shared resource banner and confirmation dialog.

1. Find an extension used by 2+ processes (check `sharedProcessCount` > 1 in ExtensionAccessMapping).
2. Select it in the tree.
3. **Expected:** SharedResourceBanner: "This extension is shared by N processes: [list]"
4. Edit a value and click Save.
5. **Expected:** ConfirmationDialog appears: "This change affects N processes. Proceed?"
6. Click "Confirm" → save proceeds.
7. Click "Cancel" → save aborted, dirty state preserved.

### Test Scenario 6: Test-to-Prod Copy

**Goal:** Verify the copy workflow excludes connections and handles encrypted fields.

1. Log in as `ABC_BOOMI_FLOW_ADMIN`.
2. Navigate to Page 10, select an account with both Test and Prod environments.
3. Load the Test environment extensions.
4. Click "Copy Test → Prod" → navigates to Page 11.
5. **Expected on Page 11:**
   - Included panel: operations, process properties listed
   - Excluded panel: connections listed (with explanation)
   - Encrypted fields warning (if any encrypted values exist)
6. Click "Confirm Copy".
7. **Expected:** Success result showing `fieldsCopied`, `sectionsExcluded`, `encryptedFieldsSkipped`.
8. **Verify:** Load Prod environment — copied values match Test (except connections and encrypted fields).

### Test Scenario 7: DPP Banner for Process Properties

**Goal:** Verify process properties show environment-wide scope notice.

1. Select a process property extension in the tree.
2. **Expected:** DppBanner: "This is an environment-wide process property. Changes affect all processes."
3. Edit the value and save.
4. **Expected:** No shared resource confirmation (DPPs don't have reliable process tracing).

### Test Scenario 8: Undo/Redo

**Goal:** Verify undo/redo history works correctly.

1. Load extensions and select an editable extension.
2. Edit Field A → value "v1".
3. Edit Field A → value "v2".
4. Edit Field B → value "x1".
5. **Expected:** SaveToolbar shows "2 unsaved changes" (A changed + B changed).
6. Click Undo → Field B reverts to original.
7. **Expected:** "1 unsaved change", Redo button enabled.
8. Click Redo → Field B restored to "x1".
9. Edit Field A → value "v3" (should clear redo stack).
10. **Expected:** Redo button disabled.

### Test Scenario 9: Search

**Goal:** Verify fuzzy search filters tree and properties.

1. Load extensions.
2. Type "Salesforce" in the search bar.
3. **Expected:** Tree filters to show only extensions containing "Salesforce" in name or property names.
4. Categories with no matches collapse/hide.
5. Clear search → full tree restored.

### Test Scenario 10: Error Handling

**Goal:** Verify graceful error handling for various failure modes.

1. **Invalid credentials test:** Temporarily revoke API token → load extensions → expect error page with "Authentication failed" message.
2. **Network timeout test:** Simulate slow network → expect loading skeleton, then timeout error.
3. **Unauthorized access test:** Try to edit a connection as contributor via API manipulation → expect `UNAUTHORIZED_EXTENSION_EDIT` error.
4. **Map extension read-only test (Phase 1):** Attempt to trigger `updateMapExtension` → expect `MAP_EXTENSION_READONLY` response.

### Verification Checklist

```
[ ] Scenario 1: Client accounts load based on SSO groups
[ ] Scenario 2: Extensions load with correct categories and counts
[ ] Scenario 3: Contributor can edit non-connection extensions
[ ] Scenario 4: Connections are admin-only (read-only for contributors)
[ ] Scenario 5: Shared resource warning + confirmation dialog works
[ ] Scenario 6: Test-to-Prod copy excludes connections, reports results
[ ] Scenario 7: Process properties show DPP banner
[ ] Scenario 8: Undo/Redo works with correct history management
[ ] Scenario 9: Search filters tree correctly
[ ] Scenario 10: Error states handled gracefully
```

---
Prev: [Extension Flow Service & Dashboard](25-extension-flow-service-and-dashboard.md) | [Back to Index](index.md)

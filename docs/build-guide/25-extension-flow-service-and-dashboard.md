## Phase 7 (continued): Extension Flow Service & Dashboard

This section covers adding the 5 new message actions to the existing Flow Service, deploying the ExtensionEditor custom component, and building Pages 10-11 in the Flow Dashboard.

### Step 7D — Update Flow Service

Reference: `/integration/flow-service/flow-service-spec.md` (sections 15-19)

#### Via API

After adding the 5 new FSS Operations and 10 new profiles, update the Flow Service component to include the new message actions.

> **Note:** Updating the Flow Service requires retrieving the current component XML, adding the new message action entries, and POSTing the updated XML. Use `GET /Component/{flowServiceId}` to retrieve, modify locally, then `POST /Component/{flowServiceId}/update` to save.

#### Via UI (Manual Fallback)

1. Open `PROMO - Flow Service` in Build.
2. Navigate to the **Message Actions** tab.
3. Add 5 new actions (rows 15-19):

| # | Action Name | FSS Operation | Request Profile | Response Profile |
|---|-------------|---------------|-----------------|------------------|
| 15 | `listClientAccounts` | `PROMO - FSS Op - ListClientAccounts` | `PROMO - Profile - ListClientAccountsRequest` | `PROMO - Profile - ListClientAccountsResponse` |
| 16 | `getExtensions` | `PROMO - FSS Op - GetExtensions` | `PROMO - Profile - GetExtensionsRequest` | `PROMO - Profile - GetExtensionsResponse` |
| 17 | `updateExtensions` | `PROMO - FSS Op - UpdateExtensions` | `PROMO - Profile - UpdateExtensionsRequest` | `PROMO - Profile - UpdateExtensionsResponse` |
| 18 | `copyExtensionsTestToProd` | `PROMO - FSS Op - CopyExtensionsTestToProd` | `PROMO - Profile - CopyExtensionsTestToProdRequest` | `PROMO - Profile - CopyExtensionsTestToProdResponse` |
| 19 | `updateMapExtension` | `PROMO - FSS Op - UpdateMapExtension` | `PROMO - Profile - UpdateMapExtensionRequest` | `PROMO - Profile - UpdateMapExtensionResponse` |

4. Save the component.

#### Redeploy

After updating the Flow Service:

1. Create a new PackagedComponent with version `2.0.0` and notes "Added extension editor message actions".
2. Deploy to the same environment.
3. Verify all **19 listeners** appear in Runtime Management → Listeners.
4. Re-retrieve connector configuration in Flow to auto-discover the 10 new types.

**Verify:** Flow connector should now show **38 types** (19 actions × 2 types each).

### Step 7E — Deploy ExtensionEditor Custom Component

Reference: `/flow/custom-components/extension-editor-spec.md`

The ExtensionEditor is a React 16 custom component that provides:
- Process-centric tree navigation (left panel)
- Inline-editable property table with virtual scrolling (right panel)
- Role-based access control (admin vs contributor)
- Undo/redo with 50-level history
- Shared resource impact banners
- Connection admin-only gate

#### Build the Component

```bash
cd flow/custom-components/extension-editor/
npm install
npm run build
```

Output: `build/extension-editor.js` (~60KB gzipped) + `build/extension-editor.css` (~4KB)

#### Upload to Flow

1. Navigate to Boomi Flow → **Settings → Custom Resources**.
2. Upload `extension-editor.js` and `extension-editor.css` as tenant assets.
3. Note the asset URLs.
4. Add both URLs to the custom player's `customResources` array.

#### Register Component

The component registers itself via:
```javascript
manywho.component.register('ExtensionEditor', component(ExtensionEditor));
```

### Step 7E.2 — Build Pages 10-11

Reference: `/flow/page-layouts/page10-extension-manager.md` and `/flow/page-layouts/page11-extension-copy-confirmation.md`

#### Page 10: Extension Manager

1. Add a new page step in the Developer Swimlane.
2. Page name: `Extension Manager`.
3. Add page load message step → `listClientAccounts`.
4. Add layout components:
   - **Account Selector** (combobox) — bound to `clientAccounts` Flow value
   - **Environment Selector** (combobox) — bound to selected account's environments
   - **ExtensionEditor** (custom component) — bound to `extensionEditorPayload` Flow value
5. Add message step for account/environment change → `getExtensions`.
6. Add "Save" outcome → message step → `updateExtensions`.
7. Add "Copy Test → Prod" outcome → navigates to Page 11.
8. Both Developer and Admin swimlanes can access this page.

#### Page 11: Extension Copy Confirmation

1. Add a new page step navigated from Page 10.
2. Page name: `Extension Copy Confirmation`.
3. Display:
   - **Included sections panel**: operations, process properties, cross-references
   - **Excluded sections panel**: connections (with explanation), PGP certificates
   - **Encrypted fields warning**: fields with encrypted values will be skipped
   - **Preview table**: summary of what will be copied
4. Add "Confirm Copy" button → message step → `copyExtensionsTestToProd`.
5. Add "Cancel" button → returns to Page 10.
6. Results panel shows `fieldsCopied`, `sectionsExcluded`, `encryptedFieldsSkipped`.

### Phase 7E Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| ExtensionEditor doesn't render | Component not registered or assets not loaded | Verify `customResources` includes both JS and CSS URLs. Check browser console for 404 errors |
| "No extension data provided" error | objectData binding missing or null | Verify the page component is bound to `extensionEditorPayload` Flow value and the getExtensions message step populated it |
| Connection fields are editable by non-admins | Access control not enforced | Verify `isAdmin` Flow value is set from getDevAccounts response and passed to the component |
| Copy button not visible | `hasTestEnvironment` not set | Verify the client account has both Test and Prod environment IDs in ClientAccountConfig |

---
Prev: [Extension Processes K-O](24-extension-processes.md) | Next: [Extension Testing](26-extension-testing.md) | [Back to Index](index.md)

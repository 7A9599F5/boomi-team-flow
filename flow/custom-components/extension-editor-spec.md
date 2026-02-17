# ExtensionEditor — Custom Flow Component Specification

## Overview

The `ExtensionEditor` is a custom React component registered in the Boomi Flow custom player. It renders an inline editor for Boomi environment extension properties — connections, operations, process properties, and cross-reference overrides — using a two-panel tree/table layout with inline editing, undo/redo, and role-based access control.

**Used on:** Page 10 (Environment Extension Editor)

---

## NPM Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `react-window` | ^1.8 | Virtual scrolling for property tables with large property lists (~6KB gz) |

> **Note:** No AG Grid or other heavy table library. The property table is a custom lightweight implementation using `react-window`'s `FixedSizeList` for row virtualization.

---

## Props (via `element.objectData`)

The component receives data through Flow's `objectData` binding mechanism. All data is passed as string properties within a single objectData entry.

| Prop | Developer Name | Type | Required | Description |
|------|----------------|------|----------|-------------|
| `extensionData` | `extensionData` | JSON string | Yes | Serialized EnvironmentExtensions object (connections, operations, processProperties, crossReferenceOverrides) |
| `accessMappings` | `accessMappings` | JSON string | Yes | Array of `IAccessMapping` objects mapping processes to extension IDs |
| `isAdmin` | `isAdmin` | `"true"` / `"false"` | No | Whether the current user has admin privileges. Defaults to false. |
| `userSsoGroups` | `userSsoGroups` | Comma-separated string | No | User's Azure AD SSO group memberships (e.g., `ABC_BOOMI_FLOW_ADMIN,ABC_BOOMI_FLOW_CONTRIBUTOR`) |

### extensionData JSON Shape

```json
{
  "accountId": "ABC-PROD",
  "environmentId": "env-prod-001",
  "environmentName": "Production",
  "connections": {
    "conn-abc-123": {
      "name": "Salesforce CRM Connection",
      "extensionGroupId": "grp-sfdc",
      "properties": {
        "host": { "name": "Host", "value": "", "useDefault": true, "encrypted": false },
        "password": { "name": "Password", "value": "***", "useDefault": false, "encrypted": true }
      }
    }
  },
  "operations": { ... },
  "processProperties": {
    "pp-env-001": { "name": "BASE_URL", "value": "https://api.prod.co", "useDefault": false, "encrypted": false }
  }
}
```

### accessMappings JSON Shape

```json
[
  {
    "processId": "proc-order-001",
    "processName": "Order Processing",
    "extensionIds": ["conn-abc-123", "op-xyz-789", "pp-env-001"],
    "adminOnly": false
  }
]
```

---

## Features

### 1. Two-Panel Layout

- **Left panel (30% width)**: Extension tree navigation grouped by category.
- **Right panel (70% width)**: Inline-editable property table for the selected extension.
- Responsive: stacks vertically on mobile (< 768px).

### 2. Extension Tree Navigation

- Categories: Connections | Operations | Process Properties | Cross-Reference Overrides
- Each category is collapsible (expanded by default for the first three).
- Tree items show visual indicators:
  - Lock icon for connections (require admin to edit)
  - Shared icon for extensions used by 2+ processes (with tooltip listing process names)
- Click to select an extension — loads its properties in the right panel.
- Filtered in real-time by the search bar.

### 3. Inline Property Editing

- Click any editable cell to enter edit mode (input appears in-place).
- Press Enter or blur to commit the change; press Escape to cancel.
- Encrypted fields show masked values and cannot be edited (display-only badge).
- "Use Default" checkbox per property row to revert to the platform default.
- Read-only mode for connection extensions (non-admin) and admin-only processes.

### 4. Undo / Redo

- Full undo/redo history with up to 50 snapshots.
- Each SET_VALUE or TOGGLE_DEFAULT action pushes the previous state onto the undo stack.
- Undo/Redo buttons in SaveToolbar; disabled when stack is empty.
- New edits after undo clear the redo stack.

### 5. Search

- Fuzzy search (case-insensitive substring) across extension names and property names.
- Debounced 300ms to avoid excessive re-renders.
- Clear button when query is non-empty.
- Filters the tree in real-time; shows "No matches" in empty categories.

### 6. Context Banners

Three banners appear above the property table based on context:

- **ConnectionBanner**: Admin-only lock notice for connection extensions. Non-admins see read-only message.
- **DppBanner**: Info banner for process properties (environment-wide scope notice).
- **SharedResourceBanner**: Warning when 2+ processes share the selected extension — lists affected processes.

### 7. Save with Shared-Resource Guard

- **Single-process save**: Saves immediately on button click.
- **Multi-process save**: Shows a `ConfirmationDialog` listing all affected processes before saving.
- On save: calls `applyEdits()` to merge edits into model, serializes to JSON, logs payload (production: writes to Flow value + triggers "Save" outcome).
- Resets dirty state after save.

### 8. Copy Test to Production

- "Copy Test → Prod" button in SaveToolbar triggers the `CopyTestToProd` outcome, navigating to Page 11.
- Only shown when `hasTestEnvironment` is true (configurable per deployment).

### 9. Role-Based Access Control

Authorization rules (enforced by `useAccessControl` hook):

| User Group | Can Edit Connections | Can Edit Operations | Can Edit Process Props |
|------------|---------------------|---------------------|------------------------|
| `ABC_BOOMI_FLOW_ADMIN` | Yes | Yes | Yes |
| `ABC_BOOMI_FLOW_CONTRIBUTOR` | No (read-only) | Yes (if not adminOnly) | Yes (if not adminOnly) |
| No recognized group | No | No | No |

Admin-only extensions (those mapped only to `adminOnly: true` processes) are read-only for contributors.

### 10. Virtual Scrolling

- Property table uses `react-window`'s `FixedSizeList` for row virtualization.
- Row height: 48px; max 10 visible rows before scroll.
- Handles thousands of properties without DOM bloat.

---

## Component Structure

```
+-----------------------------------------------------------------------+
| ENVIRONMENT SELECTOR                                                   |
| Account: [ABC-PROD v]  Environment: [Production v]                    |
+-----------------------------------------------------------------------+
| SEARCH BAR                                                             |
| [Search icon] [_______________________] [x]                           |
+-----------------------------------------------------------------------+
|  EXTENSION TREE (30%)    |  PROPERTY TABLE (70%)                      |
|                           |                                            |
|  v CONNECTIONS (2)        |  [ConnectionBanner if connection]          |
|    [lock] CRM Connection  |  [DppBanner if processProperty]            |
|    [lock] SAP Connection  |  [SharedResourceBanner if shared]          |
|                           |                                            |
|  v OPERATIONS (1)         |  Property Name  | Value    | Default | *   |
|    Get Orders             |  ─────────────────────────────────────── |
|                           |  Host           | prod.srv | [ ]     |     |
|  v PROCESS PROPS (2)      |  Username       | api@co   | [ ]     |     |
|    BASE_URL               |  Password       | ●●●●●●  | [ ]     |     |
|    API_KEY                |                                            |
+-----------------------------------------------------------------------+
| SAVE TOOLBAR                                                           |
| 2 unsaved changes    [Undo] [Redo] [Copy Test→Prod] [Save (2)]       |
+-----------------------------------------------------------------------+
```

---

## Player Registration

The custom component JS and CSS bundles are uploaded as Flow tenant assets and registered via the custom player's `customResources` array.

```javascript
// Custom Flow Player initialization
manywho.initialize({
  tenantId: '{tenant-id}',
  flowId: '{flow-id}',
  customResources: [
    'https://{asset-host}/extension-editor.js',
    'https://{asset-host}/extension-editor.css'
  ]
});
```

### Component Registration (inside extension-editor.js)

```typescript
// src/index.tsx
import { component } from './utils/wrapper';
import { ExtensionEditor } from './ExtensionEditor';

manywho.component.register('ExtensionEditor', component(ExtensionEditor));
```

The `component()` HOC:
- Reads `model` and `state` from `manywho.model.getComponent()` / `manywho.state.getComponent()`
- Extracts `objectData` and passes it as typed props
- Respects Flow visibility (`model.isVisible`)
- Applies Flow CSS classes via `manywho.styling.getClasses()`

### Flow Page Binding

In the Flow page builder, add a **Custom Component** element:
- **Component name**: `ExtensionEditor`
- **Object Data binding**: Bound to a Flow value containing the combined extension data and access mapping output from the environment-management message action

---

## Styling

### CSS Classes

| Class | Purpose |
|-------|---------|
| `.extension-editor` | Root container |
| `.ee-env-selector` | Account + environment dropdown row |
| `.ee-search-bar` | Search input with icon and clear button |
| `.ee-panels` | Two-panel flex container |
| `.ee-panels__tree` | Left tree panel (30% width) |
| `.ee-panels__properties` | Right property panel (flex: 1) |
| `.ee-tree__category` | Collapsible category group |
| `.ee-tree__item` | Individual extension tree item |
| `.ee-tree__item--selected` | Selected tree item (blue highlight) |
| `.ee-tree__item-icon--lock` | Lock icon for connections |
| `.ee-tree__item-icon--shared` | Shared icon for multi-process extensions |
| `.ee-table` | Property table container |
| `.ee-table__row` | Property table row |
| `.ee-table__row--dirty` | Row with unsaved change (amber background) |
| `.ee-table__cell-value--editable` | Editable value cell (click to edit) |
| `.ee-table__cell-input` | Active inline edit input |
| `.ee-table__encrypted-mask` | Masked encrypted value display |
| `.ee-banner--warning` | Shared resource warning (amber) |
| `.ee-banner--info` | DPP info notice (blue) |
| `.ee-banner--admin` | Connection admin notice (grey) |
| `.ee-banner--readonly` | Connection read-only notice (red) |
| `.ee-save-toolbar` | Bottom save/undo/redo toolbar |
| `.ee-save-toolbar__dirty-indicator` | Unsaved change count (amber) |
| `.ee-btn--primary` | Primary save button (blue) |
| `.ee-btn--danger` | Confirm dialog danger button (red) |
| `.ee-dialog-overlay` | Modal confirmation dialog overlay |
| `.ee-dialog` | Confirmation dialog box |
| `.ee-loading__skeleton` | Shimmer loading skeleton |
| `.ee-error` | Error state container |

### Theme Support

- GitHub-style neutral colors for tree and table chrome (light theme).
- Amber (#d97706 / #fffbeb) for dirty/unsaved state indicators.
- Blue (#0969da / #ddf4ff) for selected items and primary actions.
- Red (#da3633 / #ffebe9) for read-only and destructive states.

---

## Responsive Behavior

**Desktop (> 1024px):**
- Full two-panel layout: tree 30%, properties 70%.
- All toolbar buttons visible inline.

**Tablet (768px - 1024px):**
- Tree widens slightly (35%); max-width 280px.
- Environment selector wraps if needed.
- Save toolbar stacks buttons if needed.

**Mobile (< 768px):**
- Two-panel stacks vertically: tree on top (max-height 200px), table below.
- Tree scrollable independently.
- Save toolbar stacks vertically, buttons full-width.
- Dialog widens to 95% screen width.

---

## Accessibility

- Keyboard navigation: Tab through tree items, Enter/Space to select.
- Property cells: Tab to cell, Enter/Space to activate edit mode, Escape to cancel.
- ARIA: `role="search"` on SearchBar, `role="navigation"` on tree, `role="table"` on property grid.
- Tree: `aria-expanded` on category headers, `role="listbox"` / `role="option"` on item lists.
- Banners: `role="alert"` for read-only/warning, `role="note"` for info notices.
- Toolbar: `role="toolbar"` with `aria-label`.
- Dialog: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby`.
- Dirty state: `aria-live="polite"` on unsaved change count.
- Screen reader only class `.ee-sr-only` for visually hidden labels.
- Focus: Inline edit input receives `autoFocus` on activation.

---

## Error Handling

- **Missing objectData**: Shows "No extension data provided" error state with icon.
- **Invalid extensionData JSON**: Shows parsed error message in error state.
- **Missing environmentId**: Shows validation error from `parseExtensionData`.
- **Loading state**: Shows shimmer skeleton while data is being fetched.
- **React error boundary**: Wraps entire editor in `ExtensionEditorErrorBoundary`; catches rendering errors and shows fallback.

---

## Build and Deploy

### Build Instructions

The implementation source lives in `extension-editor/`:

```bash
cd flow/custom-components/extension-editor/

# Install dependencies
npm install

# Run tests
npm test

# Development server (localhost:8081)
npm start

# Production build
npm run build

# Bundle analysis
npm run analyze
```

### Build Process

1. **Development**: `npm start` — Webpack dev server on port 8081 with template.html (React 16 loaded via CDN, manywho stub provided, sample extension data pre-loaded).
2. **Bundle**: `npm run build` — production bundle with CSS extraction.
3. **Upload**: Upload `build/extension-editor.js` + `build/extension-editor.css` to Boomi Flow tenant assets.
4. **Register**: Add asset URLs to custom player `customResources`.

### Build Configuration

- **Webpack 5** with `ts-loader` for TypeScript compilation.
- **React/ReactDOM externalized** — provided by Flow player at runtime.
- CSS extracted via `mini-css-extract-plugin` in production, inline via `style-loader` in development.
- Dev server on port 8081 (distinct from xml-diff-viewer's 8080 to allow both running simultaneously).
- Bundle size target: under 500KB gzipped (react-window is ~6KB gz; no AG Grid or other heavy deps).

### File Output

| File | Size (gzipped est.) | Contents |
|------|---------------------|----------|
| `extension-editor.js` | ~60KB | React component tree + react-window |
| `extension-editor.css` | ~4KB | Tree, table, banners, dialog, responsive |

---

## Source Structure

```
extension-editor/
  package.json                   # Dependencies, scripts, Jest config
  tsconfig.json                  # TypeScript strict, JSX react, ES2018 target
  webpack.config.js              # Dev server config (port 8081)
  webpack.production.config.js   # Production bundle config
  template.html                  # Local dev with manywho stub + sample extension data
  mocks/
    manywho.js                   # Jest mock for Flow runtime globals
    styles.js                    # CSS module stub
  src/
    index.tsx                    # Entry: registers component with Flow
    ExtensionEditor.tsx          # Main orchestrator (state init, layout, save logic)
    components/
      ExtensionTree.tsx          # Category tree with expand/collapse, search filter
      PropertyTable.tsx          # Virtual-scrolled property grid with inline editing
      SearchBar.tsx              # Debounced fuzzy search input
      EnvironmentSelector.tsx    # Account + environment dropdowns
      SaveToolbar.tsx            # Save, Undo, Redo, Copy Test→Prod buttons
      SharedResourceBanner.tsx   # Amber warning for multi-process extensions
      DppBanner.tsx              # Blue info for environment-wide process props
      ConnectionBanner.tsx       # Admin-only lock notice for connection extensions
      ConfirmationDialog.tsx     # Portal-based confirm modal for shared saves
    hooks/
      useExtensionState.ts       # useReducer: edit state, undo/redo (50 levels)
      useAccessControl.ts        # canEdit(), isConnectionExtension(), getAuthorizedProcesses()
    types/
      index.ts                   # IExtensionModel, IAccessMapping, IFieldEdit, ITreeNode, etc.
      manywho.d.ts               # Type declarations for manywho global
    utils/
      wrapper.tsx                # component() HOC (bridges Flow runtime to typed props)
      extensionParser.ts         # parseExtensionData(), serializeExtensionData(), extractEditorData()
    styles/
      extension-editor.css       # Two-panel layout, tree, table, banners, dialog, responsive
    __tests__/
      ExtensionEditor.test.tsx   # Integration tests (loading, error, selection, edit, save)
      extensionParser.test.ts    # Parser unit tests (valid, invalid, round-trip)
      useExtensionState.test.ts  # Reducer tests (setValue, undo, redo, reset)
      useAccessControl.test.ts   # Permission tests (admin, contributor, connection gate)
      SearchBar.test.tsx         # Search input, debounce, clear button tests
```

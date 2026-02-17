# Custom Components — Extending Flow with React

## Overview

Boomi Flow supports **custom React components** that can be registered and used in the page builder alongside standard components. This allows developers to extend Flow with custom UI elements, visualizations, and interactions not available in standard components.

---

## Use Cases

**When to create custom components:**
- Custom visualizations (charts, graphs, diff viewers, tree displays)
- Specialized input controls (code editors, signature pads, rich text editors)
- Third-party widget integrations (mapping widgets, calendar pickers)
- Domain-specific UI elements (process diagrams, network topology)

**When NOT to create custom components:**
- Standard UI elements available (use Data Grid instead of custom table)
- Simple text/image display (use Presentation component)
- Standard form inputs (use Text Input, Dropdown, etc.)

**Rule of thumb:** Use standard components first. Only create custom components when needed.

---

## Component Types

### 1. Standard Custom Components

General-purpose UI components for pages.

**Props type:** `IComponentProps`

**Use for:**
- Visualizations, displays, custom inputs
- Complex interactions not available in standard components

### 2. Column Custom Components

Designed for use in tables/datagrids (custom cell renderers).

**Props type:** `CustomCellElementProps`

**Use for:**
- Custom cell formatting (badges, progress bars, icons)
- Cell-level actions (edit, delete buttons within cells)

**Source:** [Build a custom component - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Setting_up_and_managing_flows/Components/flo-custom-components-creating_1b937a98-761d-4cfc-9ce7-c5e28a93867d)

---

## Creating a Custom Component

### Step 1: Development

Custom components are built as **React components** using TypeScript/JavaScript.

**Official boilerplate repository:**
- GitHub: `Boomi-PSO/ui-custom-component`
- Community (archived): `manywho/ui-custom-component`

**Source:** [GitHub - Boomi-PSO/ui-custom-component](https://github.com/Boomi-PSO/ui-custom-component)

#### Example Structure

**`src/XmlDiffViewer.tsx`:**

```tsx
import React from 'react';
import { IComponentProps } from '@boomi/flow-component-model';

interface DiffData {
  branchXml: string;
  mainXml: string;
  componentName: string;
  componentAction: 'CREATE' | 'UPDATE';
  branchVersion?: number;
  mainVersion?: number;
}

const XmlDiffViewer: React.FC<IComponentProps> = (props) => {
  // Get objectData using HOC helper
  const data = props.getObjectData<DiffData>();

  // Extract properties
  const branchXml = data[0]?.branchXml || '';
  const mainXml = data[0]?.mainXml || '';
  const componentName = data[0]?.componentName || '';
  const componentAction = data[0]?.componentAction || 'CREATE';

  // Component logic and rendering
  return (
    <div className="xml-diff-viewer">
      <h2>{componentName} - {componentAction}</h2>
      {/* Diff rendering */}
    </div>
  );
};

export default XmlDiffViewer;
```

#### TypeScript Benefits

- Type safety at build time
- Auto-completion in IDE
- Catch errors before runtime
- Better documentation via types

### Step 2: Registration

Components must be registered with the Flow runtime using `manywho.component.register`.

**`src/index.ts`:**

```typescript
import { component } from './wrapper';
import XmlDiffViewer from './XmlDiffViewer';

// Register component with Flow runtime
manywho.component.register('XmlDiffViewer', component(XmlDiffViewer, true));
```

**Registration parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| **Component name** | String | Unique identifier (e.g., `'XmlDiffViewer'`, `'signature-pad'`) |
| **Component** | React component | React component (optionally wrapped in HOC) |
| **Debug mode** | Boolean | Enable debug links in Flow (optional, default: false) |

#### Higher-Order Components (HOCs)

The boilerplate provides two HOCs in `wrapper.tsx`:

**1. `component` HOC — For standard components**

```typescript
import { component } from './wrapper';

manywho.component.register('XmlDiffViewer', component(XmlDiffViewer, true));
```

**What it provides:**
- Fetches model and state from Flow runtime
- Provides `onChange` and `onEvent` handlers
- Simplifies objectData access via `props.getObjectData()`
- Props type: `IComponentProps`

**2. `container` HOC — For container-type components**

```typescript
import { container } from './wrapper';

manywho.component.registerContainer('CustomLayout', container(CustomLayout));
```

**What it provides:**
- Container-specific props (children, layout config)
- Used for layout containers
- Register via `manywho.component.registerContainer`

### Step 3: Build and Bundle

**Build:**

```bash
npm install
npm run build
```

**Output:**
- `dist/custom-component.js` (bundled JavaScript)
- `dist/custom-component.css` (styles, optional)

**Bundle format:**
- UMD or CommonJS module
- Compatible with Flow player runtime
- Minified for production

### Step 4: Upload to Tenant

**Upload as tenant assets:**

```bash
npm run upload
```

**Asset storage:**
- Publicly accessible URLs
- **Security warning:** Do NOT include secrets or confidential information
- Assets visible to anyone with URL

**Example asset URLs:**

```
https://cdn.boomi.com/assets/my-tenant/xml-diff-viewer.js
https://cdn.boomi.com/assets/my-tenant/xml-diff-viewer.css
```

### Step 5: Register in Flow

**Two runtime options:**

#### Option A: Legacy Runtime (Older Flow Versions)

**Navigate to:** Flow > Components > New Component

**Configuration:**

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Display name | "XML Diff Viewer" |
| **Key** | Registry key (lowercase, must match registration key) | `xml-diff-viewer` or `XmlDiffViewer` |
| **Description** | Component description | "Side-by-side XML diff viewer with syntax highlighting" |
| **Legacy JS** | Upload `.js` file or enter asset URL | `https://cdn.boomi.com/.../xml-diff-viewer.js` |
| **Legacy CSS** | Upload `.css` file or enter asset URL (optional) | `https://cdn.boomi.com/.../xml-diff-viewer.css` |
| **Icon** | Icon for page builder | (upload icon image) |
| **Configuration Editors** | Available config options | (optional) |
| **Available Attributes** | Attributes that can be set on component | (optional) |
| **Preview Image** | Preview image for page builder (optional) | (upload preview image) |

**Source:** [Add a custom component - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Legacy_runtime/flo-custom-components-installing_legacy)

#### Option B: Custom Player (Recommended for Modern Flow)

Create a custom Flow player that references the component assets.

**`custom-player.js`:**

```javascript
manywho.initialize({
  tenantId: '{tenant-id}',
  flowId: '{flow-id}',
  customResources: [
    'https://cdn.boomi.com/assets/my-tenant/xml-diff-viewer.js',
    'https://cdn.boomi.com/assets/my-tenant/xml-diff-viewer.css'
  ]
});
```

**Benefits:**
- More control over component loading
- Easier to version and manage
- Can load multiple custom components at once

---

## ObjectData Binding

**ObjectData** is Flow's mechanism for passing data to custom components.

### How It Works

1. **In Flow page builder:** Add custom component to page
2. **Bind Object Data:** Set Object Data property to a Flow Value (e.g., `diffData` from `generateComponentDiff` response)
3. **Component receives data:** Component accesses data via `props.objectData`

### Without HOC (Raw Access)

```javascript
const propertyValue = manywho.utils.getObjectDataProperty(
  objectData[0].properties,
  'PropertyName'
).contentValue;
```

### With HOC (`component` Wrapper)

```javascript
const objectData = props.getObjectData();
const propertyValue = objectData[0].PropertyName; // Direct property access
objectData[0].PropertyName = 'New Value'; // Can also set values
```

### Type Safety (TypeScript)

```typescript
interface DiffData {
  branchXml: string;
  mainXml: string;
  componentName: string;
  componentAction: 'CREATE' | 'UPDATE';
  branchVersion?: number;
  mainVersion?: number;
}

const XmlDiffViewer: React.FC<IComponentProps> = (props) => {
  const data = props.getObjectData<DiffData>();
  const branchXml = data[0]?.branchXml || '';
  const mainXml = data[0]?.mainXml || '';
  // TypeScript ensures property names are correct
};
```

---

## Example: XmlDiffViewer (From Project)

### Purpose

Display side-by-side diff of component XML (branch vs. main) for peer review and admin approval.

### Dependencies

**NPM packages:**
- `diff` (Myers diff algorithm)
- `react-diff-view` (diff rendering UI)
- `prismjs` (XML syntax highlighting)

**Install:**

```bash
npm install diff react-diff-view prismjs
npm install --save-dev @types/diff
```

### Props (via objectData)

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `branchXml` | string | Yes | Normalized XML from promotion branch |
| `mainXml` | string | Yes | Normalized XML from main (empty for CREATE) |
| `componentName` | string | Yes | Component display name |
| `componentAction` | string | Yes | `CREATE` or `UPDATE` |
| `branchVersion` | number | No | Version on branch |
| `mainVersion` | number | No | Version on main (0 for CREATE) |

### Features

- **Diff views**: Side-by-side and unified diff views
- **Syntax highlighting**: XML syntax highlighting via Prism.js
- **Line numbers**: Show line numbers and change summary
- **Context collapse**: Show 3 lines around changes, hide unchanged sections
- **Expand all**: Button to expand all collapsed sections
- **Copy buttons**: Copy branch or main XML to clipboard
- **Responsive**: Mobile switches to unified-only view

### Implementation

**`src/XmlDiffViewer.tsx`:**

```tsx
import React, { useMemo, useState } from 'react';
import { parseDiff, Diff, Hunk } from 'react-diff-view';
import { diffLines, Change } from 'diff';
import { refractor } from 'refractor/lib/core';
import xml from 'refractor/lang/xml';
import 'prismjs/themes/prism.css';
import 'react-diff-view/style/index.css';

refractor.register(xml);

interface DiffData {
  branchXml: string;
  mainXml: string;
  componentName: string;
  componentAction: 'CREATE' | 'UPDATE';
  branchVersion?: number;
  mainVersion?: number;
}

const XmlDiffViewer: React.FC<IComponentProps> = (props) => {
  const data = props.getObjectData<DiffData>();
  const [viewType, setViewType] = useState<'split' | 'unified'>('split');

  // Extract data
  const branchXml = data[0]?.branchXml || '';
  const mainXml = data[0]?.mainXml || '';
  const componentName = data[0]?.componentName || '';
  const componentAction = data[0]?.componentAction || 'CREATE';

  // Compute diff
  const diffText = useMemo(() => {
    const changes: Change[] = diffLines(mainXml, branchXml);
    return changes.map(change => {
      const prefix = change.added ? '+' : change.removed ? '-' : ' ';
      return change.value.split('\n').map(line => prefix + line).join('\n');
    }).join('\n');
  }, [mainXml, branchXml]);

  const files = useMemo(() => parseDiff(diffText), [diffText]);

  // Render
  return (
    <div className="xml-diff-viewer">
      <div className="diff-header">
        <h3>{componentName} - {componentAction}</h3>
        <div className="view-controls">
          <button onClick={() => setViewType('split')}>Split</button>
          <button onClick={() => setViewType('unified')}>Unified</button>
        </div>
      </div>

      {files.map((file, idx) => (
        <Diff key={idx} viewType={viewType} diffType={file.type} hunks={file.hunks}>
          {hunks => hunks.map(hunk => <Hunk key={hunk.content} hunk={hunk} />)}
        </Diff>
      ))}
    </div>
  );
};

export default XmlDiffViewer;
```

### Integration in Flow

**Message Step: generateComponentDiff**

```
Request:
{
  "componentId": "abc-123",
  "branchId": "branch-456",
  "devAccountId": "dev-789"
}

Response:
{
  "branchXml": "<bns:Component ...>...</bns:Component>",
  "mainXml": "<bns:Component ...>...</bns:Component>",
  "componentName": "Orders Process",
  "componentAction": "UPDATE",
  "branchVersion": 11,
  "mainVersion": 10
}

Output Mapping:
  diffData ← response
```

**Page 6: Peer Review Detail**

```
Custom Component: XmlDiffViewer
  - Object Data: diffData
  - Component renders diff when diffData populated
```

---

## Best Practices

### 1. Component Design

- **Use standard components first**: Only create custom when needed
- **Keep components focused**: Single responsibility (e.g., XmlDiffViewer only renders diffs)
- **TypeScript for type safety**: Catch errors at build time
- **Responsive design**: Support desktop, tablet, mobile breakpoints
- **Accessibility**: Keyboard navigation, screen reader support, ARIA labels

### 2. Performance

- **Memoize expensive computations**: Use `useMemo` for diff calculations, parsing
- **Lazy-load heavy dependencies**: Load Prism.js syntax highlighting only when needed
- **Virtualize long lists**: For large diffs, use virtualization libraries (react-window, react-virtual)
- **Debounce updates**: If component accepts user input, debounce state updates

### 3. Testing

- **Test in debug mode**: Use Flow debug mode (`mode=DEBUG` in URL) to inspect state
- **Test with real data**: Use actual component XML from project
- **Test responsive breakpoints**: Verify mobile, tablet, desktop layouts
- **Test accessibility**: Keyboard navigation, screen reader compatibility

### 4. Security

- **Do NOT include secrets**: Custom components are publicly accessible via asset URLs
- **Validate objectData**: Check for null/undefined values, provide defaults
- **Sanitize HTML**: If rendering user-provided HTML, sanitize to prevent XSS
- **HTTPS only**: Ensure asset URLs use HTTPS (not HTTP)

### 5. Documentation

- **Props documentation**: Document all props with types and descriptions
- **Usage examples**: Provide example Flow configuration
- **README**: Include setup instructions, dependencies, build steps
- **Changelog**: Track changes across versions

---

## Troubleshooting

### Issue: Component not rendering in Flow

**Possible causes:**
1. Component not registered in Flow (check Components > Custom Components)
2. Asset URLs incorrect or inaccessible
3. JavaScript errors in console
4. Registration key mismatch

**Resolution:**
1. Verify component registered in Flow > Components
2. Check asset URLs are accessible (open in browser)
3. Open browser dev tools, check console for errors
4. Ensure registration key matches exactly (case-sensitive)

### Issue: ObjectData is null or undefined

**Possible causes:**
1. Object Data binding not configured on component in page builder
2. Flow Value is null or undefined
3. Message step hasn't populated Flow Value yet

**Resolution:**
1. Verify component's Object Data property is bound to Flow Value
2. Check that Flow Value is populated (use debug mode to inspect state)
3. Ensure message step completes before page renders component

### Issue: Component not receiving updates

**Possible causes:**
1. Flow Value updated but component not re-rendering
2. Component not using props correctly
3. React memoization preventing re-render

**Resolution:**
1. Use `useEffect` hook to watch for prop changes
2. Ensure component reads from `props.getObjectData()` (not cached value)
3. Check React DevTools for unnecessary memoization

### Issue: Styles not applied

**Possible causes:**
1. CSS file not loaded
2. CSS class name mismatch
3. CSS specificity conflict with Flow's styles

**Resolution:**
1. Verify CSS asset URL is correct and accessible
2. Check browser dev tools for CSS class names
3. Use more specific CSS selectors or `!important` (sparingly)

---

## Sources

- [Build a custom component - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Setting_up_and_managing_flows/Components/flo-custom-components-creating_1b937a98-761d-4cfc-9ce7-c5e28a93867d)
- [Add a custom component - Boomi Documentation](https://help.boomi.com/docs/Atomsphere/Flow/Topics/Legacy_runtime/flo-custom-components-installing_legacy)
- [GitHub - Boomi-PSO/ui-custom-component](https://github.com/Boomi-PSO/ui-custom-component)
- [Boomi Flow Custom Components - Boomi Community](https://community.boomi.com/s/article/Boomi-Flow-Custom-Components)

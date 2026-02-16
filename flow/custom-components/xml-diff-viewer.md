# XmlDiffViewer — Custom Flow Component Specification

## Overview

The `XmlDiffViewer` is a custom React component registered in the Boomi Flow custom player. It renders a side-by-side (or unified) diff view of two XML documents, used by reviewers to see exactly what changed in promoted components before approving.

**Used on:** Pages 3 (Promotion Status), 6 (Peer Review Detail), 7 (Admin Approval Queue)

---

## NPM Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `diff` | ^5.x | Myers diff algorithm — computes line-level differences between two strings |
| `react-diff-view` | ^3.x | Renders unified or split diff hunks with gutter, line numbers, and styling |
| `prismjs` | ^1.29 | XML/HTML syntax highlighting for diff content |

---

## Props (via `element.objectData`)

The component receives data through Flow's `objectData` binding mechanism.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `branchXml` | string | Yes | Normalized XML from the promotion branch (after strip/rewrite) |
| `mainXml` | string | Yes | Normalized XML from main branch. Empty string for CREATE (new component) |
| `componentName` | string | Yes | Display name of the component being diffed |
| `componentAction` | string | Yes | `"CREATE"` or `"UPDATE"` — determines diff mode |
| `branchVersion` | number | No | Component version on the promotion branch |
| `mainVersion` | number | No | Component version on main (0 for CREATE) |

---

## Features

### 1. View Modes
- **Side-by-side (split)**: Left = main (before), Right = branch (after). Default for UPDATE.
- **Unified**: Single column with additions (+) and deletions (-). Alternative toggle.
- **Single-pane (all green)**: For CREATE actions — shows branch XML only with all-green highlighting (no "before" to compare)

### 2. Syntax Highlighting
- XML syntax highlighted via Prism.js
- Tags, attributes, values, and comments colored distinctly
- Works in both light and dark Flow themes

### 3. Line Numbers
- Gutter on each side shows line numbers
- Line numbers from original source (not diff-relative)

### 4. Context Collapse
- Unchanged sections collapsed by default (show 3 context lines above/below each change)
- "Show N hidden lines" expander between collapsed sections
- "Expand All" button in toolbar to show full content

### 5. Change Summary
- Header bar: "{N} additions, {M} deletions, {K} unchanged lines"
- Badge: component name and action type
- Version info: "main v{mainVersion} → branch v{branchVersion}"

### 6. Copy Buttons
- "Copy Branch XML" — copies the full branch (new) XML to clipboard
- "Copy Main XML" — copies the full main (old) XML to clipboard
- Visible in toolbar area

### 7. Scrolling
- Container has `max-height: 500px` with vertical scroll
- Scroll sync between left and right panes in split view
- Horizontal scroll for long XML lines (no wrapping by default)
- Optional "Wrap Lines" toggle in toolbar

---

## Component Structure

```
+------------------------------------------------------------------+
| TOOLBAR                                                           |
| {componentName} ({componentAction})                               |
| main v3 → branch v4                                              |
| [Split | Unified]  [Expand All]  [Wrap Lines]  [Copy ▼]         |
| 12 additions, 3 deletions, 45 unchanged                         |
+------------------------------------------------------------------+
| DIFF VIEW (max-height: 500px, scrollable)                        |
|                                                                   |
| LEFT (main)                  | RIGHT (branch)                    |
| ─────────────────────────────|────────────────────────────────── |
|  1 | <Component id="abc">   |  1 | <Component id="abc">        |
|  2 | <Name>OrderProc</Name> |  2 | <Name>OrderProc</Name>      |
|    | ... 15 hidden lines ... |    | ... 15 hidden lines ...     |
| 18 | <host>old.server</host>| 18 | <host></host>               |  ← deletion (red) / addition (green)
| 19 | <timeout>30</timeout>  | 19 | <timeout>60</timeout>        |  ← change (yellow)
|    | ... 8 hidden lines ...  |    | ... 8 hidden lines ...      |
| 28 | </Component>           | 28 | </Component>                 |
|                                                                   |
+------------------------------------------------------------------+
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
    'https://{asset-host}/xml-diff-viewer.js',
    'https://{asset-host}/xml-diff-viewer.css'
  ]
});
```

### Component Registration (inside xml-diff-viewer.js)

```javascript
// Register with Flow runtime
manywho.component.register('XmlDiffViewer', class XmlDiffViewer extends React.Component {
  // Component implementation
  // Reads props from this.props.objectData
  // Renders diff view using react-diff-view
});
```

### Flow Page Binding

In the Flow page builder, add a **Custom Component** element:
- **Component name**: `XmlDiffViewer`
- **Object Data binding**: Bound to the Flow value containing diff data from `generateComponentDiff` response

---

## Styling

### CSS Classes

| Class | Purpose |
|-------|---------|
| `.xml-diff-viewer` | Root container |
| `.xml-diff-toolbar` | Toolbar with controls |
| `.xml-diff-summary` | Change summary line |
| `.xml-diff-content` | Scrollable diff container (max-height: 500px) |
| `.xml-diff-gutter` | Line number gutter |
| `.xml-diff-line--added` | Added line (green background #e6ffec) |
| `.xml-diff-line--removed` | Removed line (red background #ffebe9) |
| `.xml-diff-line--changed` | Changed line (yellow background #fff8c5) |
| `.xml-diff-expander` | Collapsed section expander |
| `.xml-diff-new-component` | Single-pane all-green view for CREATE |

### Theme Support

- Inherits Flow player theme colors where possible
- Provides both light and dark mode color schemes
- Diff colors follow GitHub's diff color conventions

---

## Responsive Behavior

**Desktop (> 1024px):**
- Full split view with synchronized scroll
- Toolbar inline

**Tablet (768px - 1024px):**
- Default to unified view (split view available via toggle)
- Toolbar wraps if needed

**Mobile (< 768px):**
- Unified view only (split view disabled)
- Toolbar stacked vertically
- Full-width container (no max-height constraint)

---

## Accessibility

- Keyboard navigation: Tab to toolbar controls, arrow keys within diff
- Screen reader: Announces change summary, line-by-line changes
- Focus indicators on all interactive elements
- ARIA labels: `role="table"` for diff grid, `aria-label` on controls
- High contrast mode: Diff colors meet WCAG AA contrast requirements

---

## Error Handling

- **Empty branchXml**: Show "No component data available" message
- **Invalid XML**: Show raw text diff (fallback from syntax highlighting)
- **Loading state**: Show skeleton/shimmer while `generateComponentDiff` is in progress
- **API failure**: Show error message with retry button

---

## Build and Deploy

### Build Process

1. **Development**: Standard React development with webpack/vite
2. **Bundle**: Build production bundle (single JS + CSS file)
3. **Upload**: Upload to Boomi Flow tenant as assets
4. **Register**: Add asset URLs to custom player `customResources`

### File Output

| File | Size Target | Contents |
|------|-------------|----------|
| `xml-diff-viewer.js` | < 150KB gzipped | React component + diff + prismjs |
| `xml-diff-viewer.css` | < 10KB | Component styles + diff colors |

# XmlDiffViewer — Custom Flow Component Specification

## Overview

The `XmlDiffViewer` is a custom React component registered in the Boomi Flow custom player. It renders a side-by-side (or unified) diff view of two XML documents, used by reviewers to see exactly what changed in promoted components before approving.

**Used on:** Pages 3 (Promotion Status), 6 (Peer Review Detail), 7 (Admin Approval Queue)

---

## NPM Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `react-diff-viewer-continued` | ^4.0 | Full-featured diff rendering — split/unified views, code folding, line numbers, word-level diffs |
| `prismjs` | ^1.29 | XML/HTML syntax highlighting via `renderContent` callback (core + markup only, ~6KB gz) |

> **Note:** `react-diff-viewer-continued` bundles the `diff` library internally. No separate `diff` dependency is needed.

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

The component uses a Higher-Order Component (HOC) wrapper that bridges the Flow runtime (`manywho.model`, `manywho.state`) with typed React props:

```typescript
// src/index.tsx
import { component } from './utils/wrapper';
import { XmlDiffViewer } from './XmlDiffViewer';

manywho.component.register('XmlDiffViewer', component(XmlDiffViewer));
```

The `component()` HOC:
- Reads `model` and `state` from `manywho.model.getComponent()` / `manywho.state.getComponent()`
- Extracts `objectData` and passes it as typed props
- Respects Flow visibility (`model.isVisible`)
- Applies Flow CSS classes via `manywho.styling.getClasses()`

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
| `.xml-diff-header` | Header with name/action badges and stats |
| `.xml-diff-toolbar__controls` | Toolbar with view mode and action controls |
| `.xml-diff-summary` | Change summary line |
| `.xml-diff-content` | Scrollable diff container (max-height: 500px) |
| `.xml-diff-badge` | Component name and action badges |
| `.xml-diff-toggle` | Split/Unified radio toggle |
| `.xml-diff-btn` | Toolbar action buttons |
| `.xml-diff-fold-message` | Collapsed section expander |
| `.xml-diff-content--create` | Single-pane all-green view for CREATE |
| `.xml-diff-content--wrap` | Wrap-lines mode override |

### Theme Support

- GitHub-style diff colors (light theme by default)
- Dark theme support via `diff-styles.ts` Emotion overrides
- Prism.js syntax token colors for XML elements
- Diff colors follow GitHub conventions: green (#e6ffec) for additions, red (#ffebe9) for deletions

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
- ARIA labels: `role="table"` for diff grid, `role="toolbar"` on controls, `aria-label` on all buttons
- `aria-pressed` on toggle buttons (Expand All, Wrap Lines)
- `role="radiogroup"` with `aria-checked` on Split/Unified toggle
- High contrast mode: Diff colors meet WCAG AA contrast requirements

---

## Error Handling

- **Empty branchXml**: Show "No component data available" message
- **Invalid XML**: Show raw text diff (fallback from syntax highlighting)
- **Loading state**: Show skeleton/shimmer while `generateComponentDiff` is in progress
- **API failure**: Show error message with retry button

---

## Build and Deploy

### Build Instructions

The implementation source lives in `xml-diff-viewer/`:

```bash
cd flow/custom-components/xml-diff-viewer/

# Install dependencies
npm install

# Run tests (38 tests, >80% coverage)
npm test

# Development server (localhost:8080)
npm start

# Production build
npm run build

# Bundle analysis
npm run analyze
```

### Build Process

1. **Development**: `npm start` — Webpack dev server with template.html (React 16 loaded via CDN, manywho stub provided)
2. **Bundle**: `npm run build` — production bundle with CSS extraction
3. **Upload**: Upload `build/xml-diff-viewer.js` + `build/xml-diff-viewer.css` to Boomi Flow tenant assets
4. **Register**: Add asset URLs to custom player `customResources`

### File Output

| File | Size (gzipped) | Contents |
|------|----------------|----------|
| `xml-diff-viewer.js` | ~64KB | React component + react-diff-viewer-continued + prismjs (markup) |
| `xml-diff-viewer.css` | ~1.4KB | Component styles + diff colors + responsive breakpoints |

### Build Configuration

- **Webpack 5** with `ts-loader` for TypeScript compilation
- **React/ReactDOM externalized** — provided by Flow player at runtime
- `react-diff-viewer-continued` aliased to CJS build for React 16 compatibility (avoids `react/jsx-runtime`)
- CSS extracted via `mini-css-extract-plugin` in production, inline via `style-loader` in development

---

## Source Structure

```
xml-diff-viewer/
  package.json              # Dependencies, scripts, Jest config
  tsconfig.json             # TypeScript strict, JSX react, ES2018 target
  webpack.config.js         # Dev server config
  webpack.production.config.js  # Production bundle config
  template.html             # Local dev with manywho stub + sample data
  mocks/
    manywho.js              # Jest mock for Flow runtime globals
    matchMedia.js           # Jest mock for window.matchMedia
    styles.js               # CSS module stub
  src/
    index.tsx               # Entry: registers component with Flow
    XmlDiffViewer.tsx        # Main orchestrator (toolbar state, routing)
    components/
      DiffToolbar.tsx        # View toggle, expand, wrap, copy buttons
      DiffHeader.tsx         # Name/action badges, version info, stats
      DiffContent.tsx        # Wraps ReactDiffViewer with Prism + themes
      CreateView.tsx         # All-green single-pane for CREATE
      LoadingState.tsx       # Skeleton shimmer
      ErrorState.tsx         # Error message + retry
    hooks/
      useResponsive.ts       # Breakpoint detection via matchMedia
      useDiffStats.ts        # LCS-based addition/deletion/unchanged counts
      useClipboard.ts        # Clipboard API with execCommand fallback
    types/
      index.ts               # IDiffData, IDiffStats, ViewMode, IToolbarState
      manywho.d.ts           # Type declarations for manywho global
    utils/
      wrapper.tsx            # component() HOC (bridges Flow runtime to typed props)
      objectData.ts          # Named property extraction from objectData
      xml-highlight.tsx      # Prism.js renderContent function
      diff-styles.ts         # GitHub-style light/dark theme overrides
    styles/
      xml-diff-viewer.css    # Toolbar, badges, responsive, loading, error CSS
    __tests__/
      XmlDiffViewer.test.tsx # Integration tests (loading, error, UPDATE, CREATE)
      DiffToolbar.test.tsx   # Toggle, expand, wrap, copy, ARIA tests
      DiffHeader.test.tsx    # Badge, version, stats, a11y tests
      useDiffStats.test.ts   # LCS computation edge cases
      useClipboard.test.ts   # Clipboard API + fallback tests
```

# Component Versioning Mechanics

## Version vs currentVersion

**version (integer):**
- The version number of the component (1, 2, 3, ...)
- Incremented automatically on every save/update
- Cannot be manually set or decremented

**currentVersion (boolean):**
- `true` if this is the latest version
- `false` for historical versions
- Only one version per component has `currentVersion: true` at any time

---

## Version Increment Behavior

### On Component Create

```http
POST /Component
Body: <Component XML without componentId>
```

**Result:** New component starts at `version: 1`, `currentVersion: true`

---

### On Component Update

```http
POST /Component/{id}
Body: <Updated Component XML>
```

**Before Update:**
- Component version: 3, `currentVersion: true`

**After Update:**
- Old version: 3, `currentVersion: false` (historical)
- New version: 4, `currentVersion: true` (active)

**You cannot specify the version number** — Boomi controls it.

---

### Via Branching

**Writing to a branch:**
```http
POST /Component/{id}~{branchId}
```

- Increments the branch version
- Main version remains unchanged until merge

**Before:**
- Main: `version: 3`, `currentVersion: true`

**After writing to branch:**
- Main: `version: 3`, `currentVersion: true` (unchanged)
- Branch: `version: 4`, `currentVersion: true` (on branch)

**After merge (OVERRIDE strategy):**
- Main: `version: 4`, `currentVersion: true` (adopted branch version)
- Old main version: `version: 3`, `currentVersion: false` (historical)

---

## Version History

### Retrieving Historical Versions

```http
GET /Component/{id}?version={versionNumber}
```

**Example:**
```http
GET /Component/abc-123?version=2
```

Returns version 2 of component `abc-123`.

**Without version parameter:**
```http
GET /Component/abc-123
```

Always fetches the current version (`currentVersion: true`).

---

### Version Retention

- Boomi retains all historical versions indefinitely
- No automatic purging or archiving
- Versions can be manually restored via the Boomi UI (not via API)

---

## Pitfalls

### Cannot Manually Set Version Numbers

```json
// BAD — Attempt to set version
{
  "@type": "Component",
  "componentId": "abc-123",
  "version": 5  // This is IGNORED by the API
}
```

**Boomi always auto-increments based on current version.**

---

### Branching Creates Separate Version Lineage

- Branch version and main version diverge
- After merge (OVERRIDE), main adopts branch's version
- Pre-merge main version is lost (overwritten, not merged)

**Example:**
```
Before Merge:
  Main: version 3
  Branch: version 4

After Merge (OVERRIDE):
  Main: version 4 (adopted from branch)
  Old Main version 3: currentVersion=false (historical)
```

---

### currentVersion is a Boolean, Not a Flag

- Only one version has `currentVersion: true` per component
- Do not query for "all current versions" — there is only one

```javascript
// BAD
const allCurrentVersions = await queryComponents({ currentVersion: true });
// This returns one version per component, not multiple
```

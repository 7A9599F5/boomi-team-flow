# Component CRUD Operations

Component GET, CREATE, UPDATE, DELETE operations and reference rewriting patterns.

---

## GET Component

Retrieve a single component by ID.

**Endpoint:**
```http
GET /partner/api/rest/v1/{accountId}/Component/{componentId}
```

**With `overrideAccount` (read from sub-account):**
```http
GET /partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}
```

**Headers:**
```http
Accept: application/xml
Content-Type: application/xml
Authorization: Basic {base64-credentials}
```

**Response:**
```xml
<bns:Component
  xmlns:bns="http://api.platform.boomi.com/"
  componentId="66d665d1-3ec7-479c-9e24-8df3fa728cf8"
  version="2"
  name="Order Processor"
  type="process"
  folderFullPath="/DevTeamA/Orders/Process">
  <bns:object>
    <!-- Component-specific configuration XML -->
  </bns:object>
</bns:Component>
```

**Use Cases:**
- **Process B:** Fetch component XML during dependency traversal
- **Process C:** Read dev component before promoting to prod
- **Process G:** Fetch branch and main versions for diff

---

## CREATE Component (Branch-Scoped)

Create or update a component on a specific branch using **tilde syntax**.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/Component/{componentId}~{branchId}
```

**Tilde Syntax:**
- Format: `{componentId}~{branchId}`
- Creates or updates component **on the specified branch**
- Branch-scoped components are isolated from main until merged

**Headers:**
```http
Accept: application/xml
Content-Type: application/xml
Authorization: Basic {base64-credentials}
```

**Request Body:**
```xml
<bns:Component
  xmlns:bns="http://api.platform.boomi.com/"
  componentId="{prodComponentId}"
  version="{version}"
  name="Order Processor"
  type="process"
  folderFullPath="/Promoted/DevTeamA/Orders/Process">
  <bns:object>
    <!-- Stripped and rewritten component configuration -->
  </bns:object>
</bns:Component>
```

**Use Case in Process C:**
1. Fetch dev component XML (GET with `overrideAccount`)
2. Strip environment config (Groovy: `strip-env-config.groovy`)
3. Rewrite component ID references (Groovy: `rewrite-references.groovy`)
4. Create/update on promotion branch using tilde syntax

**Response:**
```xml
<bns:Component
  componentId="{prodComponentId}"
  version="{newVersion}"
  name="Order Processor"
  type="process"
  ...
/>
```

---

## UPDATE Component (Main Branch)

Update an existing component on the main branch.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/Component/{componentId}
```

**Headers:**
```http
Accept: application/xml
Content-Type: application/xml
Authorization: Basic {base64-credentials}
```

**Request Body:**
Full component XML with updated configuration.

**Note:**
- POST to `/Component/{componentId}` updates **main branch**
- POST to `/Component/{componentId}~{branchId}` updates **specific branch**

---

## DELETE Component

Soft-delete a component (marks as deleted, but recoverable).

**Endpoint:**
```http
DELETE /partner/api/rest/v1/{accountId}/Component/{componentId}
```

**Response:**
```http
HTTP/1.1 204 No Content
```

**Important:**
- Components are **soft deleted** (not permanently removed)
- Can be restored by re-creating with the same `componentId`
- Deleted components are excluded from queries if `deleted=false` filter is used

---

## Component XML Structure

### Basic Structure

```xml
<bns:Component
  xmlns:bns="http://api.platform.boomi.com/"
  componentId="{UUID}"
  version="{integer}"
  name="{string}"
  type="{componentType}"
  folderFullPath="{path}">
  <bns:object>
    <!-- Component-specific configuration XML -->
  </bns:object>
</bns:Component>
```

### Component Types

- `process` — Integration processes
- `connection` — Connection configurations
- `connector` — Connector definitions
- `operation` — Connector operations
- `map` — Data mapping profiles
- `profile` — JSON/XML/flat file profiles
- `xslt` — XSLT transformations
- `flowservice` — Flow Service definitions

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `componentId` | UUID | Unique component identifier |
| `version` | Integer | Version number (incremented on each update) |
| `name` | String | Display name |
| `type` | String | Component type (see above) |
| `folderFullPath` | String | Full folder path (e.g., `/DevTeamA/Orders/Process`) |

---

## Reference Rewriting

### Overview

When promoting components from dev to prod, **component ID references** must be rewritten from dev IDs to prod IDs.

**Reference Types:**
- `<connectionId>` — Connection references in processes
- `<connectorId>` — Connector references
- `<operationId>` — Operation references
- `<mapId>` — Map references
- `<profileId>` — Profile references

### DataHub ComponentMapping

**Match Rule:**
- `devComponentId` + `devAccountId` → `prodComponentId`

**Source:**
- `PROMOTION_ENGINE` — Created during promotion
- `ADMIN_SEEDING` — Pre-configured by admin (e.g., connections in `#Connections` folder)

### Rewriting Strategy (Process C)

**Pseudocode:**
```javascript
function rewriteReferences(componentXml, mappingCache) {
  const refTypes = ['connectionId', 'connectorId', 'operationId', 'mapId', 'profileId'];

  for (const refType of refTypes) {
    const regex = new RegExp(`<${refType}>(.*?)</${refType}>`, 'g');
    const matches = componentXml.match(regex);

    for (const match of matches) {
      const devId = match.replace(`<${refType}>`, '').replace(`</${refType}>`, '');
      const prodId = mappingCache[devId];

      if (prodId) {
        componentXml = componentXml.replace(devId, prodId);
      } else {
        throw new Error(`MISSING_COMPONENT_MAPPING: No mapping found for ${refType}=${devId}`);
      }
    }
  }

  return componentXml;
}
```

**Groovy Implementation:**
See `/home/glitch/code/boomi_team_flow/integration/scripts/rewrite-references.groovy`

### Pre-Check Validation

**Before promoting batch:**
```javascript
function validateConnectionMappings(components, mappingCache) {
  const missingMappings = [];

  for (const component of components) {
    const connectionRefs = extractConnectionRefs(component.xml);

    for (const devId of connectionRefs) {
      if (!mappingCache[devId]) {
        missingMappings.push({
          devComponentId: component.id,
          missingConnectionId: devId
        });
      }
    }
  }

  if (missingMappings.length > 0) {
    throw new Error(`MISSING_CONNECTION_MAPPINGS: ${JSON.stringify(missingMappings)}`);
  }
}
```

**Groovy Implementation:**
See `/home/glitch/code/boomi_team_flow/integration/scripts/validate-connection-mappings.groovy`

---

## Environment Config Stripping

### What Gets Stripped

When promoting components, environment-specific configuration must be removed:

**Passwords and Encrypted Values:**
- `<password>...</password>`
- `<encryptedPassword>...</encryptedPassword>`
- `<apiKey>...</apiKey>`
- Any field containing sensitive credentials

**Hostnames and URLs:**
- `<host>dev-server.example.com</host>`
- `<url>https://dev.example.com/api</url>`
- `<endpoint>http://localhost:8080</endpoint>`

**Environment-Specific Properties:**
- Database connection strings
- File paths specific to dev environments
- Port numbers for dev services

### Stripping Strategy (Process C)

**Regex Patterns:**
```javascript
const stripPatterns = [
  /<password>.*?<\/password>/g,
  /<encryptedPassword>.*?<\/encryptedPassword>/g,
  /<host>.*?<\/host>/g,
  /<url>.*?<\/url>/g,
  /<endpoint>.*?<\/endpoint>/g,
  /<apiKey>.*?<\/apiKey>/g
];

function stripEnvConfig(componentXml) {
  let stripped = componentXml;

  for (const pattern of stripPatterns) {
    stripped = stripped.replace(pattern, (match) => {
      const tagName = match.match(/<(\w+)>/)[1];
      return `<${tagName}></${tagName}>`; // Empty the tag
    });
  }

  return stripped;
}
```

**Groovy Implementation:**
See `/home/glitch/code/boomi_team_flow/integration/scripts/strip-env-config.groovy`

### Post-Promotion Configuration

After promotion, **admin must manually configure** environment-specific values in prod:

1. Navigate to promoted component in AtomSphere UI
2. Update connection passwords/hosts
3. Test connection
4. Deploy to target environment

**Why Not Automated:**
- Prod credentials should **never** be stored in dev environments
- Manual review ensures security
- Forces validation of promoted components

---

## Component Folder Path Mirroring

### Convention

Dev folder paths are **mirrored** in prod under `/Promoted/`:

**Dev:**
```
/DevTeamA/Orders/Process/OrderProcessor
```

**Prod:**
```
/Promoted/DevTeamA/Orders/Process/OrderProcessor
```

**Benefits:**
- Maintains organizational structure
- Easy to identify promoted components
- Preserves team/project context

**Implementation:**
Process C sets `folderFullPath="/Promoted{devFolderFullPath}"` in component XML.

---

## Error Handling

### 404 Not Found

```json
{
  "@type": "Error",
  "statusCode": 404,
  "errorMessage": "Component not found."
}
```

**Causes:**
- Invalid `componentId`
- Component was deleted
- `overrideAccount` points to account without the component

**Resolution:**
- Verify `componentId` from ComponentMetadata query
- Check `deleted` status
- Verify account access

---

### 400 Bad Request

```json
{
  "@type": "Error",
  "statusCode": 400,
  "errorMessage": "Invalid component XML."
}
```

**Causes:**
- Malformed XML structure
- Missing required attributes (e.g., `componentId`, `type`)
- Invalid namespace declarations

**Resolution:**
- Validate XML against Boomi schema
- Check for unescaped special characters (`<`, `>`, `&`)
- Ensure namespace prefix `bns:` is used

---

### 403 Forbidden

```json
{
  "@type": "Error",
  "statusCode": 403,
  "errorMessage": "Access denied."
}
```

**Causes:**
- Insufficient permissions (missing `API` privilege)
- `overrideAccount` without management rights
- Attempting to modify read-only components

**Resolution:**
- Request `API` privilege from account administrator
- Verify account hierarchy for `overrideAccount`
- Check component permissions

---

## Best Practices

### Component Promotion

**DO:**
- ✅ Validate all component mappings exist before promotion
- ✅ Strip environment config before promoting
- ✅ Rewrite all component ID references
- ✅ Use tilde syntax for branch-scoped operations
- ✅ Mirror dev folder paths under `/Promoted/`

**DON'T:**
- ❌ Promote components with dev credentials
- ❌ Skip reference rewriting
- ❌ Assume mappings exist without validation
- ❌ Promote directly to main (always use branches)

### XML Manipulation

**DO:**
- ✅ Use XmlSlurper for parsing (Groovy)
- ✅ Use XmlUtil.serialize for pretty-printing
- ✅ Preserve XML namespaces and attributes
- ✅ Escape special characters in text content

**DON'T:**
- ❌ Use string replacement for complex XML modifications
- ❌ Strip whitespace from XML (formatting matters)
- ❌ Remove namespace declarations
- ❌ Modify component version numbers manually (auto-incremented)

---

## Related References

- **`authentication.md`** — `overrideAccount` usage for reading dev components
- **`branch-operations.md`** — Tilde syntax and branch lifecycle
- **`query-patterns.md`** — ComponentMetadata and ComponentReference queries
- **`error-handling.md`** — Retry patterns and error codes

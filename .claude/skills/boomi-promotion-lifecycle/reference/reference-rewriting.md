# Component Reference Rewriting

## The Problem

Component XML embeds references to other components as UUID strings:

```xml
<bns:Process>
  <bns:componentId>process-uuid-123</bns:componentId>
  <bns:connectionId>dev-conn-456</bns:connectionId>
  <bns:operationId>dev-op-789</bns:operationId>
  <bns:mapId>dev-map-012</bns:mapId>
  <bns:profileId>dev-profile-345</bns:profileId>
</bns:Process>
```

After promotion, prod components must reference prod component IDs, not dev IDs.

---

## The Solution: Mapping Cache Pattern

### Pre-Load Mapping Cache

**Before Rewriting:**
1. Process B resolves full dependency tree
2. Process C batch queries DataHub for ALL component mappings for this dev account
3. Process C validates all dependencies have mappings (except connections, pre-seeded)
4. Process C loads mappings into in-memory cache (`componentMappingCache` DPP, JSON)

**Cache Format:**
```json
{
  "dev-comp-123": "prod-comp-abc",
  "dev-comp-456": "prod-comp-def",
  "dev-conn-789": "prod-conn-#connections-xyz",
  "dev-map-012": "prod-map-ghi"
}
```

**Source:** DataHub `ComponentMapping` table, queried by `devAccountId`.

---

### Rewriting Pattern (Groovy)

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import java.util.regex.Pattern

// Load mapping cache from DPP
String mappingJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
def mappingCache = [:]
if (mappingJson && mappingJson.trim()) {
    mappingCache = new JsonSlurper().parseText(mappingJson)
}

String xmlContent = // ... fetched component XML

int rewriteCount = 0

// Replace each dev ID with its prod ID throughout the XML
mappingCache.each { devId, prodId ->
    if (xmlContent.contains(devId)) {
        xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
        rewriteCount++
        logger.info("Rewrote reference: ${devId} -> ${prodId}")
    }
}

logger.info("Total references rewritten: ${rewriteCount}")
```

**Key Method:** `Pattern.quote(devId)` — escapes special regex characters in UUIDs.

---

## Why Pattern.quote?

**UUID Format:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (contains hyphens)

**Without Pattern.quote:**
```groovy
// BAD — Hyphens are regex special chars (character class range)
xmlContent = xmlContent.replaceAll(devId, prodId)
```

**With Pattern.quote:**
```groovy
// GOOD — Hyphens are treated literally
xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
```

**Pattern.quote()** ensures any future UUID format changes don't break the script.

---

## Connection References Are Rewritten Too

**Key Point:** Even though connections are NOT promoted, their references MUST be rewritten.

**Dev Process XML:**
```xml
<connectionId>dev-conn-123</connectionId>
```

**After Rewriting:**
```xml
<connectionId>prod-conn-#connections-abc</connectionId>
```

**Why?**
- Dev processes reference dev connection IDs
- Prod processes must reference prod `#Connections` IDs
- Mapping cache includes connections (admin-seeded via Process F)

---

## Component Reference Fields

**Common Reference Elements:**
- `<connectionId>` — References to connection components
- `<operationId>` — References to operation components
- `<mapId>` — References to map components
- `<profileId>` — References to profile components
- `<processId>` — References to sub-process components

**UUID Format:** Boomi component IDs are GUIDs: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

**Example ID:** `3a5b7c9d-1e2f-3a4b-5c6d-7e8f9a0b1c2d`

---

## UUIDs Can Appear Anywhere in XML

Component IDs are not limited to specific elements. They can appear in:
- Element content (e.g., `<connectionId>abc-123</connectionId>`)
- Attribute values (e.g., `<ref id="abc-123">`)
- Comments (e.g., `<!-- Component abc-123 -->`)
- CDATA sections

**The replaceAll approach is global** — it catches all occurrences.

```groovy
// Global replacement throughout entire XML string
mappingCache.each { devId, prodId ->
    if (xmlContent.contains(devId)) {
        xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
    }
}
```

---

## Validation: Missing Mappings

**Before Rewriting:** Process C validates ALL dependencies have mappings.

```groovy
def missingMappings = []

components.each { comp ->
    String devId = comp.devComponentId
    if (!mappingCache.containsKey(devId) && comp.type != 'connection') {
        missingMappings << [
            devComponentId: devId,
            componentName: comp.name,
            componentType: comp.type
        ]
    }
}

if (missingMappings.size() > 0) {
    throw new Error("MISSING_COMPONENT_MAPPINGS: ${missingMappings}")
}
```

**Result:** If a dependency is missing from the mapping cache, promotion fails before any rewriting.

---

## Rewriting Happens AFTER Stripping

**Order Matters:**
1. **Strip first:** Remove sensitive config (passwords, hosts)
2. **Rewrite second:** Substitute component IDs

**Why?**
- Stripping doesn't affect IDs (only removes config values)
- Rewriting needs to operate on stripped XML (to avoid replacing IDs inside stripped values)

**Process C Flow:**
```javascript
for (const comp of sortedComponents) {
    const devXml = await getComponent(comp.devComponentId, devAccountId);

    // Step 1: Strip
    const strippedXml = stripEnvConfig(devXml);

    // Step 2: Rewrite
    const rewrittenXml = rewriteReferences(strippedXml, mappingCache);

    // Step 3: Create on branch
    await createComponentOnBranch(comp.prodComponentId, branchId, rewrittenXml);
}
```

---

## Complete Example

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import java.util.Properties
import java.util.regex.Pattern

def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String xmlContent = is.getText("UTF-8")

    // Load mapping cache from DPP
    String mappingJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
    def mappingCache = [:]
    if (mappingJson && mappingJson.trim()) {
        mappingCache = new JsonSlurper().parseText(mappingJson)
    }

    int rewriteCount = 0

    // Replace all dev IDs with prod IDs
    mappingCache.each { devId, prodId ->
        if (xmlContent.contains(devId)) {
            xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
            rewriteCount++
            logger.info("Rewrote reference: ${devId} -> ${prodId}")
        }
    }

    ExecutionUtil.setDynamicProcessProperty("referencesRewritten", rewriteCount.toString(), false)

    if (rewriteCount > 0) {
        logger.info("Total references rewritten: ${rewriteCount}")
    } else {
        logger.info("No references to rewrite")
    }

    dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
}
```

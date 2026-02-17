# Project Groovy Scripts — Annotated Guide

This document provides detailed annotations for all 6 Groovy scripts used in the Boomi dev-to-prod promotion system.

---

## 1. build-visited-set.groovy

**Used In:** Process B (resolveDependencies)

**Purpose:** Recursive BFS dependency traversal — builds a visited set to avoid infinite loops.

**Location:** `/integration/scripts/build-visited-set.groovy`

### Full Script with Annotations

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import groovy.xml.XmlSlurper
import java.util.Properties

def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String xmlContent = is.getText("UTF-8")

    // ==================== Load Current State from DPPs ====================
    // DPP: visitedComponentIds — JSON array of already-visited component IDs
    String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
    def visitedSet = []
    if (visitedJson && visitedJson.trim()) {
        visitedSet = new JsonSlurper().parseText(visitedJson)
    }

    // DPP: componentQueue — JSON array of queued component IDs to visit next
    String queueJson = ExecutionUtil.getDynamicProcessProperty("componentQueue")
    def queue = []
    if (queueJson && queueJson.trim()) {
        queue = new JsonSlurper().parseText(queueJson)
    }

    // DPP: currentComponentId — The component being processed in this iteration
    String currentId = ExecutionUtil.getDynamicProcessProperty("currentComponentId")

    // ==================== Check if Already Visited ====================
    if (visitedSet.contains(currentId)) {
        // Component already visited — skip to avoid infinite loop
        ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "true", false)
        logger.info("Component ${currentId} already visited - skipping")
    } else {
        // ==================== Add to Visited Set ====================
        visitedSet << currentId
        ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "false", false)
        logger.info("Component ${currentId} added to visited set (total: ${visitedSet.size()})")

        // ==================== Parse ComponentReference Response ====================
        // xmlContent contains Boomi ComponentReference API response
        // Each <componentId> or <referenceComponentId> is a child dependency
        try {
            def root = new XmlSlurper(false, false).parseText(xmlContent)

            root.depthFirst().findAll { it.name() == 'componentId' || it.name() == 'referenceComponentId' }.each { ref ->
                String childId = ref.text()?.trim()
                if (childId && !visitedSet.contains(childId) && !queue.contains(childId)) {
                    queue << childId
                    logger.info("  Queued child component: ${childId}")
                }
            }
        } catch (Exception e) {
            logger.warning("Could not parse ComponentReference XML: ${e.message}")
        }
    }

    // ==================== Update DPPs ====================
    ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
    ExecutionUtil.setDynamicProcessProperty("componentQueue", JsonOutput.toJson(queue), false)
    ExecutionUtil.setDynamicProcessProperty("visitedCount", visitedSet.size().toString(), false)
    ExecutionUtil.setDynamicProcessProperty("queueCount", queue.size().toString(), false)

    // ==================== Pass Through Original Document ====================
    dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
}
```

### Key Patterns

1. **Defensive DPP Reads:** Always check `if (visitedJson && visitedJson.trim())` before parsing
2. **DPP as State Storage:** Uses JSON-serialized arrays for visited set and queue
3. **XML Parsing:** Depth-first search for `<componentId>` elements
4. **Always Store Output:** Passes through original document even though content is unchanged

---

## 2. sort-by-dependency.groovy

**Used In:** Process B (resolveDependencies)

**Purpose:** Sorts dependency tree by type hierarchy — profiles first, root process last.

**Location:** `/integration/scripts/sort-by-dependency.groovy`

### Full Script with Annotations

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.Properties

def logger = ExecutionUtil.getBaseLogger()

// ==================== Type Priority Function ====================
// Lower priority = promoted first
// Root process must be last (depends on everything else)
def typePriority = { String type, String componentId, String rootId ->
    type = type?.toLowerCase() ?: ''
    if (type.contains('profile')) return 1        // Profiles first (no dependencies)
    if (type == 'connection') return 2            // Connections second
    if (type.contains('operation')) return 3      // Operations third
    if (type == 'map') return 4                   // Maps fourth
    if (type == 'process' && componentId == rootId) return 6  // Root process LAST
    if (type == 'process') return 5               // Sub-processes before root
    return 3  // Default: middle of the pack
}

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String jsonContent = is.getText("UTF-8")
    def components = new JsonSlurper().parseText(jsonContent)

    // ==================== Get Root Component ID ====================
    String rootComponentId = ExecutionUtil.getDynamicProcessProperty("rootComponentId") ?: ''

    // ==================== Sort by Type Hierarchy ====================
    components.sort { a, b ->
        int priorityA = typePriority(a.type, a.devComponentId, rootComponentId)
        int priorityB = typePriority(b.type, b.devComponentId, rootComponentId)
        priorityA <=> priorityB  // Spaceship operator for comparison
    }

    // ==================== Log Sorted Order ====================
    logger.info("Sorted ${components.size()} components by dependency order")
    components.eachWithIndex { comp, idx ->
        logger.info("  ${idx + 1}. [${comp.type}] ${comp.name} (${comp.devComponentId})")
    }

    // ==================== Output Sorted JSON ====================
    String output = JsonOutput.prettyPrint(JsonOutput.toJson(components))
    dataContext.storeStream(new ByteArrayInputStream(output.getBytes("UTF-8")), props)
}
```

### Key Patterns

1. **Closure as Function:** `typePriority` closure encapsulates sorting logic
2. **Spaceship Operator:** `<=>` for three-way comparison
3. **Logging with Index:** `eachWithIndex` for 1-based logging
4. **Pretty-Printed Output:** Uses `prettyPrint` for human-readable JSON

---

## 3. strip-env-config.groovy

**Used In:** Process C (executePromotion)

**Purpose:** Removes passwords, hosts, URLs, ports, and encrypted values from component XML.

**Location:** `/integration/scripts/strip-env-config.groovy`

### Full Script with Annotations

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil
import java.util.Properties

def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String xmlContent = is.getText("UTF-8")
    def root = new XmlSlurper(false, false).parseText(xmlContent)

    def strippedElements = []
    boolean configStripped = false

    // ==================== Strip Password Elements ====================
    def passwords = root.depthFirst().findAll { it.name() == 'password' }
    if (passwords.size() > 0) {
        passwords.each { it.replaceBody('') }  // Replace content with empty string
        strippedElements << 'password'
        configStripped = true
    }

    // ==================== Strip Host Elements ====================
    def hosts = root.depthFirst().findAll { it.name() == 'host' }
    if (hosts.size() > 0) {
        hosts.each { it.replaceBody('') }
        strippedElements << 'host'
        configStripped = true
    }

    // ==================== Strip URL Elements ====================
    def urls = root.depthFirst().findAll { it.name() == 'url' }
    if (urls.size() > 0) {
        urls.each { it.replaceBody('') }
        strippedElements << 'url'
        configStripped = true
    }

    // ==================== Strip Port Elements ====================
    def ports = root.depthFirst().findAll { it.name() == 'port' }
    if (ports.size() > 0) {
        ports.each { it.replaceBody('') }
        strippedElements << 'port'
        configStripped = true
    }

    // ==================== Strip Encrypted Values ====================
    def encrypted = root.depthFirst().findAll { it.name() == 'EncryptedValue' }
    if (encrypted.size() > 0) {
        encrypted.each { it.replaceBody('') }
        strippedElements << 'EncryptedValue'
        configStripped = true
    }

    // ==================== Track What Was Stripped ====================
    ExecutionUtil.setDynamicProcessProperty("configStripped", configStripped.toString(), false)
    ExecutionUtil.setDynamicProcessProperty("strippedElements", strippedElements.join(','), false)

    if (configStripped) {
        logger.info("Stripped environment config: ${strippedElements.join(', ')}")
    } else {
        logger.info("No environment config to strip")
    }

    // ==================== Serialize and Output ====================
    String outputXml = XmlUtil.serialize(root)
    dataContext.storeStream(new ByteArrayInputStream(outputXml.getBytes("UTF-8")), props)
}
```

### Key Patterns

1. **replaceBody vs Delete:** Replaces content with empty string, preserves element structure
2. **Audit Tracking:** Logs which elements were stripped for debugging
3. **XmlUtil.serialize:** Converts XmlSlurper result back to XML string

---

## 4. rewrite-references.groovy

**Used In:** Process C (executePromotion)

**Purpose:** Replaces all dev component IDs with prod component IDs using mapping cache.

**Location:** `/integration/scripts/rewrite-references.groovy`

### Full Script with Annotations

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

    // ==================== Load Mapping Cache from DPP ====================
    String mappingJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
    def mappingCache = [:]
    if (mappingJson && mappingJson.trim()) {
        mappingCache = new JsonSlurper().parseText(mappingJson)
    }

    int rewriteCount = 0
    def rewrittenIds = []

    // ==================== Replace All Dev IDs with Prod IDs ====================
    // Component IDs are GUIDs: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    // Pattern.quote ensures hyphens are treated literally, not as regex
    mappingCache.each { devId, prodId ->
        if (xmlContent.contains(devId)) {
            xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
            rewriteCount++
            rewrittenIds << "${devId} -> ${prodId}"
            logger.info("Rewrote reference: ${devId} -> ${prodId}")
        }
    }

    // ==================== Track Rewrite Count ====================
    ExecutionUtil.setDynamicProcessProperty("referencesRewritten", rewriteCount.toString(), false)

    if (rewriteCount > 0) {
        logger.info("Total references rewritten: ${rewriteCount}")
    } else {
        logger.info("No references to rewrite")
    }

    // ==================== Output Rewritten XML ====================
    dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
}
```

### Key Patterns

1. **Pattern.quote:** Escapes special regex characters in UUIDs
2. **String replaceAll:** Global replacement throughout entire XML string
3. **Map Iteration:** `mappingCache.each { devId, prodId -> ... }`

---

## 5. validate-connection-mappings.groovy

**Used In:** Process C (executePromotion)

**Purpose:** Pre-promotion validation that all connection mappings exist.

**Location:** `/integration/scripts/validate-connection-mappings.groovy`

### Full Script with Annotations

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.Properties

def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String jsonContent = is.getText("UTF-8")
    def components = new JsonSlurper().parseText(jsonContent)

    // ==================== Load Mapping Cache ====================
    String mappingJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
    def mappingCache = [:]
    if (mappingJson && mappingJson.trim()) {
        mappingCache = new JsonSlurper().parseText(mappingJson)
    }

    // ==================== Find Missing Connection Mappings ====================
    def missingMappings = []
    components.each { comp ->
        if (comp.type == 'connection') {
            String devId = comp.devComponentId
            if (!mappingCache.containsKey(devId)) {
                missingMappings << [
                    devComponentId: devId,
                    componentName: comp.name,
                    componentType: comp.type
                ]
                logger.warning("Missing mapping for connection: ${comp.name} (${devId})")
            }
        }
    }

    // ==================== Set Validation Result ====================
    if (missingMappings.size() > 0) {
        ExecutionUtil.setDynamicProcessProperty("validationResult", "FAILED", false)
        ExecutionUtil.setDynamicProcessProperty("missingMappings", JsonOutput.toJson(missingMappings), false)
        logger.severe("Validation FAILED: ${missingMappings.size()} connection mappings missing")
    } else {
        ExecutionUtil.setDynamicProcessProperty("validationResult", "PASSED", false)
        logger.info("Validation PASSED: All connection mappings exist")
    }

    // ==================== Output Original JSON ====================
    dataContext.storeStream(new ByteArrayInputStream(jsonContent.getBytes("UTF-8")), props)
}
```

### Key Patterns

1. **Filter + Check Pattern:** Filters connections, then checks mapping existence
2. **Validation Result DPP:** Sets `validationResult` for downstream decision shape
3. **Structured Error Output:** Builds array of missing mappings for error response

---

## 6. normalize-xml.groovy

**Used In:** Process G (generateComponentDiff)

**Purpose:** Pretty-prints component XML for consistent line-by-line diff comparison.

**Location:** `/integration/scripts/normalize-xml.groovy`

### Full Script with Annotations

```groovy
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil
import java.util.Properties

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String xmlContent = is.getText("UTF-8")

    // ==================== Parse and Re-Serialize ====================
    // This normalizes whitespace, indentation, and element ordering
    def root = new XmlSlurper(false, false).parseText(xmlContent)
    String normalizedXml = XmlUtil.serialize(root)

    // ==================== Output Normalized XML ====================
    dataContext.storeStream(new ByteArrayInputStream(normalizedXml.getBytes("UTF-8")), props)
}
```

### Key Patterns

1. **Simplest Script:** Just parse and re-serialize for consistent formatting
2. **No Error Handling:** Assumes valid XML input (upstream shapes validated)
3. **XmlUtil Normalization:** Handles all whitespace/indentation automatically

---

## Summary Table

| Script | Process | Purpose | Key Techniques |
|--------|---------|---------|----------------|
| `build-visited-set.groovy` | B | BFS visited set tracking | DPP state, XML parsing, defensive reads |
| `sort-by-dependency.groovy` | B | Type-hierarchy sorting | Closures, spaceship operator, logging |
| `strip-env-config.groovy` | C | Remove sensitive config | `replaceBody()`, audit tracking |
| `rewrite-references.groovy` | C | Dev → prod ID rewriting | `Pattern.quote()`, global replacement |
| `validate-connection-mappings.groovy` | C | Pre-promotion validation | Filter + check, validation result DPP |
| `normalize-xml.groovy` | G | Pretty-print for diff | Parse + re-serialize |

---

## Common Patterns Across All Scripts

1. **Always Read Stream Immediately:**
   ```groovy
   String content = is.getText("UTF-8")
   ```

2. **Always Store Output:**
   ```groovy
   dataContext.storeStream(new ByteArrayInputStream(output.getBytes("UTF-8")), props)
   ```

3. **Defensive DPP Reads:**
   ```groovy
   String dppValue = ExecutionUtil.getDynamicProcessProperty("key")
   def data = []
   if (dppValue && dppValue.trim()) {
       data = new JsonSlurper().parseText(dppValue)
   }
   ```

4. **Use Logger for Visibility:**
   ```groovy
   logger.info("Normal progress message")
   logger.warning("Recoverable issue")
   logger.severe("Critical error")
   ```

5. **XmlSlurper(false, false) for Speed:**
   ```groovy
   def root = new XmlSlurper(false, false).parseText(xmlContent)
   ```

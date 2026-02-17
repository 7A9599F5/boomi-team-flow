# JSON Handling in Boomi Groovy Scripts

## JsonSlurper — Parsing JSON

`JsonSlurper` is Groovy's JSON parser. It converts JSON strings into Groovy objects (Maps and Lists).

### Basic Parsing

```groovy
import groovy.json.JsonSlurper

String jsonContent = is.getText("UTF-8")
def data = new JsonSlurper().parseText(jsonContent)
```

**Returns:**
- JSON object `{...}` → Groovy Map
- JSON array `[...]` → Groovy List

---

### Accessing Parsed Data

#### JSON Object (Map)

```json
{
  "componentId": "abc-123",
  "name": "Order Processor",
  "type": "process",
  "dependencies": ["def-456", "ghi-789"]
}
```

```groovy
def data = new JsonSlurper().parseText(jsonContent)

String componentId = data.componentId
String name = data.name
String type = data.type
def dependencies = data.dependencies  // List
```

---

#### JSON Array (List)

```json
[
  {"id": "abc-123", "name": "Component A"},
  {"id": "def-456", "name": "Component B"}
]
```

```groovy
def components = new JsonSlurper().parseText(jsonContent)

components.each { comp ->
    println "Component: ${comp.name} (${comp.id})"
}

// Access by index
String firstId = components[0].id
```

---

### Nested JSON

```json
{
  "promotion": {
    "promotionId": "promo-123",
    "status": "IN_PROGRESS",
    "components": [
      {"id": "abc-123", "type": "process"}
    ]
  }
}
```

```groovy
def data = new JsonSlurper().parseText(jsonContent)

String promotionId = data.promotion.promotionId
String status = data.promotion.status
def components = data.promotion.components

components.each { comp ->
    println "Component ${comp.id} is a ${comp.type}"
}
```

---

## JsonOutput — Serialization

`JsonOutput` converts Groovy objects (Maps, Lists) back into JSON strings.

### Compact JSON

```groovy
import groovy.json.JsonOutput

def data = [
    componentId: "abc-123",
    name: "Order Processor",
    type: "process"
]

String json = JsonOutput.toJson(data)
// {"componentId":"abc-123","name":"Order Processor","type":"process"}
```

---

### Pretty-Printed JSON

```groovy
import groovy.json.JsonOutput

def data = [
    componentId: "abc-123",
    name: "Order Processor",
    dependencies: ["def-456", "ghi-789"]
]

String pretty = JsonOutput.prettyPrint(JsonOutput.toJson(data))
```

**Output:**
```json
{
    "componentId": "abc-123",
    "name": "Order Processor",
    "dependencies": [
        "def-456",
        "ghi-789"
    ]
}
```

**Use Case:** Human-readable output for debugging or Flow display.

---

## Array Manipulation

### Add to Array

```groovy
def visitedSet = []
visitedSet << "component-123"
visitedSet << "component-456"

// visitedSet is now ["component-123", "component-456"]
```

**Operator `<<`:** Append to the end of the list.

---

### Check if Array Contains

```groovy
if (visitedSet.contains("component-123")) {
    println "Already visited"
}

// Alternative: `in` operator
if ("component-123" in visitedSet) {
    println "Already visited"
}
```

---

### Iterate Array

```groovy
def components = ["abc-123", "def-456", "ghi-789"]

components.each { id ->
    println "Processing ${id}"
}

// With index
components.eachWithIndex { id, idx ->
    println "${idx + 1}. ${id}"
}
```

---

### Filter Array

```groovy
def components = [
    [id: "abc-123", type: "process"],
    [id: "def-456", type: "connection"],
    [id: "ghi-789", type: "process"]
]

// Find all processes
def processes = components.findAll { it.type == "process" }
// processes = [[id: "abc-123", type: "process"], [id: "ghi-789", type: "process"]]
```

---

### Sort Array

```groovy
def components = [
    [id: "abc-123", priority: 3],
    [id: "def-456", priority: 1],
    [id: "ghi-789", priority: 2]
]

// Sort by priority
components.sort { it.priority }

components.each { comp ->
    println "${comp.id} (priority: ${comp.priority})"
}
```

**Output:**
```
def-456 (priority: 1)
ghi-789 (priority: 2)
abc-123 (priority: 3)
```

---

## Map Manipulation

### Create Map

```groovy
def mappingCache = [:]

// Add entries
mappingCache['dev-id-123'] = 'prod-id-abc'
mappingCache['dev-id-456'] = 'prod-id-def'

// Alternative syntax
def cache = [
    'dev-id-123': 'prod-id-abc',
    'dev-id-456': 'prod-id-def'
]
```

---

### Access Map Values

```groovy
String prodId = mappingCache['dev-id-123']

// With default value if key doesn't exist
String prodId = mappingCache.get('dev-id-123', 'default-value')
```

---

### Iterate Map

```groovy
mappingCache.each { devId, prodId ->
    println "${devId} -> ${prodId}"
}

// Alternative: with entry
mappingCache.each { entry ->
    println "${entry.key} -> ${entry.value}"
}
```

---

### Check if Map Contains Key

```groovy
if (mappingCache.containsKey('dev-id-123')) {
    println "Mapping exists"
}
```

---

### Merge Maps

```groovy
def map1 = [a: 1, b: 2]
def map2 = [b: 3, c: 4]

def merged = map1 + map2
// merged = [a: 1, b: 3, c: 4]
```

**Note:** `map2` values overwrite `map1` values for duplicate keys.

---

## Complete Example: Dependency Sorting

This script reads a JSON array of components and sorts them by dependency order:

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.Properties

def logger = ExecutionUtil.getBaseLogger()

// Type priority mapping (lower = promoted first)
def typePriority = { String type, String componentId, String rootId ->
    type = type?.toLowerCase() ?: ''
    if (type.contains('profile')) return 1
    if (type == 'connection') return 2
    if (type.contains('operation')) return 3
    if (type == 'map') return 4
    if (type == 'process' && componentId == rootId) return 6  // Root process last
    if (type == 'process') return 5  // Sub-processes before root
    return 3  // Default
}

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String jsonContent = is.getText("UTF-8")
    def components = new JsonSlurper().parseText(jsonContent)

    String rootComponentId = ExecutionUtil.getDynamicProcessProperty("rootComponentId") ?: ''

    // Sort by type hierarchy
    components.sort { a, b ->
        int priorityA = typePriority(a.type, a.devComponentId, rootComponentId)
        int priorityB = typePriority(b.type, b.devComponentId, rootComponentId)
        priorityA <=> priorityB
    }

    logger.info("Sorted ${components.size()} components by dependency order")
    components.eachWithIndex { comp, idx ->
        logger.info("  ${idx + 1}. [${comp.type}] ${comp.name} (${comp.devComponentId})")
    }

    String output = JsonOutput.prettyPrint(JsonOutput.toJson(components))
    dataContext.storeStream(new ByteArrayInputStream(output.getBytes("UTF-8")), props)
}
```

---

## DPP Storage Pattern: JSON-Based State

Dynamic Process Properties (DPPs) can only store Strings. Use JSON serialization to store complex data structures.

### Store Array in DPP

```groovy
import groovy.json.JsonOutput

def visitedSet = ["abc-123", "def-456", "ghi-789"]

// Convert to JSON and store
ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
```

---

### Read Array from DPP

```groovy
import groovy.json.JsonSlurper

String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
def visitedSet = []
if (visitedJson && visitedJson.trim()) {
    visitedSet = new JsonSlurper().parseText(visitedJson)
}
```

---

### Store Map in DPP

```groovy
import groovy.json.JsonOutput

def mappingCache = [
    'dev-id-123': 'prod-id-abc',
    'dev-id-456': 'prod-id-def'
]

ExecutionUtil.setDynamicProcessProperty("componentMappingCache", JsonOutput.toJson(mappingCache), false)
```

---

### Read Map from DPP

```groovy
import groovy.json.JsonSlurper

String mappingJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
def mappingCache = [:]
if (mappingJson && mappingJson.trim()) {
    mappingCache = new JsonSlurper().parseText(mappingJson)
}
```

---

## Complete Example: Reference Rewriting

This script reads a mapping cache from a DPP and rewrites all dev component IDs to prod IDs in XML:

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

    // Load the in-memory mapping cache from DPP
    String mappingJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
    def mappingCache = [:]
    if (mappingJson && mappingJson.trim()) {
        mappingCache = new JsonSlurper().parseText(mappingJson)
    }

    int rewriteCount = 0

    // Replace each dev ID with its prod ID throughout the XML
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

---

## Pitfalls and Best Practices

### Pitfall: Null DPP Values

```groovy
// BAD
String json = ExecutionUtil.getDynamicProcessProperty("myData")
def data = new JsonSlurper().parseText(json)  // NPE if json is null!

// GOOD
String json = ExecutionUtil.getDynamicProcessProperty("myData")
def data = []
if (json && json.trim()) {
    data = new JsonSlurper().parseText(json)
}
```

---

### Pitfall: Empty String vs Null

```groovy
// BAD
String json = ExecutionUtil.getDynamicProcessProperty("myData")
if (json) {
    def data = new JsonSlurper().parseText(json)  // Fails if json is empty string!
}

// GOOD
if (json && json.trim()) {
    def data = new JsonSlurper().parseText(json)
}
```

---

### Best Practice: Use prettyPrint for Debugging

```groovy
def data = [componentId: "abc-123", dependencies: ["def-456"]]

// Compact (for storage)
String compact = JsonOutput.toJson(data)

// Pretty (for logging)
String pretty = JsonOutput.prettyPrint(JsonOutput.toJson(data))
logger.info("Data: ${pretty}")
```

---

### Best Practice: Defensive Parsing

```groovy
try {
    def data = new JsonSlurper().parseText(jsonContent)
    // ... process data ...
} catch (Exception e) {
    logger.warning("Could not parse JSON: ${e.message}")
    // Handle error (pass through original, set error flag, etc.)
}
```

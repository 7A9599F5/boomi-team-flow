# Boomi API Objects Full Reference

## dataContext

The `dataContext` object is automatically provided to all Groovy scripts in Data Process shapes. It represents the document stream flowing through the process.

### Methods

#### `int getDataCount()`

Returns the number of documents in the current stream.

**Example:**
```groovy
int docCount = dataContext.getDataCount()
logger.info("Processing ${docCount} documents")
```

**Use Case:** Loop over all documents in the stream.

---

#### `InputStream getStream(int index)`

Returns the input stream for the document at the specified index (0-based).

**Critical:** Each stream can only be read once. After calling `getText()` or reading the stream, it cannot be read again.

**Example:**
```groovy
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    String content = is.getText("UTF-8")  // Read immediately
    // ... process content ...
}
```

**Pitfall:** If you try to read the same stream twice, you'll get an empty result.

```groovy
// BAD
InputStream is = dataContext.getStream(0)
String content1 = is.getText("UTF-8")  // Works
String content2 = is.getText("UTF-8")  // Empty! Stream already consumed
```

---

#### `Properties getProperties(int index)`

Returns the properties object attached to the document at the specified index.

**Properties** are key-value pairs that:
- Travel with the document through the process
- Can be set by previous shapes and read by later shapes
- Are independent per document

**Example:**
```groovy
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)

    // Read a property
    String componentId = props.getProperty("componentId")

    // Set a property
    props.setProperty("processedAt", new Date().toString())
}
```

**Use Case:** Pass metadata between shapes without modifying the document content.

---

#### `void storeStream(InputStream is, Properties props)`

Outputs a document to the next shape in the process. This is how you "return" transformed data.

**Critical:** You MUST call `storeStream()` for each document you want to pass to the next shape. If you don't call it, the document is dropped.

**Example:**
```groovy
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String content = is.getText("UTF-8")
    String transformed = content.toUpperCase()

    // Output the transformed content
    dataContext.storeStream(
        new ByteArrayInputStream(transformed.getBytes("UTF-8")),
        props
    )
}
```

**Pattern for Pass-Through:**
```groovy
// Even if you don't modify the content, you must call storeStream
dataContext.storeStream(
    new ByteArrayInputStream(content.getBytes("UTF-8")),
    props
)
```

---

## ExecutionUtil

The `ExecutionUtil` class (from `com.boomi.execution.ExecutionUtil`) provides access to dynamic process properties and logging.

### Dynamic Process Property (DPP) Methods

#### `String getDynamicProcessProperty(String name)`

Reads a dynamic process property by name. Returns `null` if the property does not exist.

**Example:**
```groovy
import com.boomi.execution.ExecutionUtil

String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")

// Defensive check (property may not exist)
def visitedSet = []
if (visitedJson && visitedJson.trim()) {
    visitedSet = new JsonSlurper().parseText(visitedJson)
}
```

**Pitfall:** If the DPP doesn't exist, you get `null`. Always check before parsing.

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

#### `void setDynamicProcessProperty(String name, String value, boolean persistent)`

Sets a dynamic process property.

**Parameters:**
- `name`: Property name
- `value`: Property value (must be a String)
- `persistent`: Whether the property survives process execution

**Persistence Flag:**
- `false` (default): Property is cleared after execution completes. Use for runtime-only state (e.g., loop counters, visited sets).
- `true`: Property persists across executions. **Use sparingly** — can cause state leaks if not managed carefully.

**Example (Runtime-Only):**
```groovy
// Store a JSON array in a DPP for use within this execution
ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
```

**Example (Persistent):**
```groovy
// Store a counter that increments across executions
String countStr = ExecutionUtil.getDynamicProcessProperty("executionCounter") ?: "0"
int count = countStr.toInteger() + 1
ExecutionUtil.setDynamicProcessProperty("executionCounter", count.toString(), true)
```

**When to Use persistent=true:**
- Counters that should persist across runs
- Configuration loaded once and reused
- State that must survive process restarts

**When to Use persistent=false (default):**
- Loop variables
- Temporary caches (mapping cache, visited set)
- Intermediate results that are only relevant to the current execution

---

### Logging Methods

#### `Logger getBaseLogger()`

Returns a logger instance for logging messages.

**Example:**
```groovy
import com.boomi.execution.ExecutionUtil

def logger = ExecutionUtil.getBaseLogger()
```

#### Logger Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `logger.info(String message)` | Informational message | Normal flow, progress updates |
| `logger.warning(String message)` | Warning message | Recoverable issues, unexpected but handled |
| `logger.severe(String message)` | Error message | Failures, exceptions, critical issues |

**Example:**
```groovy
def logger = ExecutionUtil.getBaseLogger()

logger.info("Processing component ${componentId}")
logger.warning("Could not parse XML: ${e.message}")
logger.severe("Script execution failed: ${e.message}")
```

**Log Visibility:**
- Logs appear in Boomi process execution logs
- Can be viewed in AtomSphere under Process Reporting
- Use for debugging and auditing

---

## Properties

The `Properties` object is a standard Java `java.util.Properties` class. It stores key-value pairs attached to each document.

### Methods

#### `String getProperty(String key)`

Returns the value for the specified key, or `null` if not set.

**Example:**
```groovy
Properties props = dataContext.getProperties(i)
String componentId = props.getProperty("componentId")
```

---

#### `void setProperty(String key, String value)`

Sets the value for the specified key.

**Example:**
```groovy
props.setProperty("processedAt", new Date().toString())
props.setProperty("status", "SUCCESS")
```

---

#### `void remove(Object key)`

Removes the property with the specified key.

**Example:**
```groovy
props.remove("tempFlag")
```

---

### Use Cases for Properties

**Pass Metadata Between Shapes:**
```groovy
// Shape 1: Set property
props.setProperty("rootComponentId", "abc-123")

// Shape 2: Read property
String rootId = props.getProperty("rootComponentId")
```

**Track Document State:**
```groovy
// Mark document as processed
props.setProperty("processed", "true")

// Later shape: check if processed
if (props.getProperty("processed") == "true") {
    // Skip processing
}
```

**Error Handling:**
```groovy
try {
    // ... risky operation ...
    props.setProperty("status", "SUCCESS")
} catch (Exception e) {
    props.setProperty("status", "ERROR")
    props.setProperty("errorMessage", e.message)
}
```

---

## Complete Example: Dependency Traversal

This example combines all three API objects to build a visited set during recursive dependency traversal.

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

    // Read DPP (visited set)
    String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
    def visitedSet = []
    if (visitedJson && visitedJson.trim()) {
        visitedSet = new JsonSlurper().parseText(visitedJson)
    }

    // Read DPP (queue)
    String queueJson = ExecutionUtil.getDynamicProcessProperty("componentQueue")
    def queue = []
    if (queueJson && queueJson.trim()) {
        queue = new JsonSlurper().parseText(queueJson)
    }

    // Get current component ID from DPP
    String currentId = ExecutionUtil.getDynamicProcessProperty("currentComponentId")

    // Check if already visited
    if (visitedSet.contains(currentId)) {
        ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "true", false)
        logger.info("Component ${currentId} already visited - skipping")
    } else {
        // Add to visited set
        visitedSet << currentId
        ExecutionUtil.setDynamicProcessProperty("alreadyVisited", "false", false)
        logger.info("Component ${currentId} added to visited set")

        // Parse XML to find child components
        try {
            def root = new XmlSlurper(false, false).parseText(xmlContent)
            root.depthFirst().findAll { it.name() == 'componentId' }.each { ref ->
                String childId = ref.text()?.trim()
                if (childId && !visitedSet.contains(childId) && !queue.contains(childId)) {
                    queue << childId
                    logger.info("  Queued child component: ${childId}")
                }
            }
        } catch (Exception e) {
            logger.warning("Could not parse XML: ${e.message}")
        }
    }

    // Write DPPs back
    ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
    ExecutionUtil.setDynamicProcessProperty("componentQueue", JsonOutput.toJson(queue), false)

    // Store output (pass through original document)
    dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
}
```

**Key Takeaways:**
1. **Defensive DPP reads** — check for null before parsing
2. **Runtime-only DPPs** — use `persistent=false` for temporary state
3. **Always store output** — even if content is unchanged
4. **Log progress** — use logger for debugging and auditing

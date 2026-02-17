---
name: boomi-groovy
description: |
  Groovy scripting in Boomi Data Process shapes. Use when writing, debugging,
  or reviewing Groovy scripts for Boomi processes, working with dataContext,
  ExecutionUtil, dynamic process properties, XML/JSON manipulation, or
  understanding Boomi's script sandbox limitations.
globs:
  - "**/*.groovy"
  - "integration/scripts/**"
---

# Boomi Groovy Scripting Reference

## Quick Start

Boomi Data Process shapes support **Groovy 2.4 scripting** for in-process data transformation and business logic. Scripts execute within the Boomi runtime and have access to Boomi-specific APIs.

**Key Constraint:** Scripts are sandboxed — no network access, no file I/O, limited to Boomi-provided APIs.

---

## Boomi API Objects Quick Reference

### dataContext

The `dataContext` object provides access to document streams and properties.

| Method | Returns | Description |
|--------|---------|-------------|
| `getDataCount()` | `int` | Number of documents in stream |
| `getStream(int index)` | `InputStream` | Get document at index |
| `getProperties(int index)` | `Properties` | Get document properties |
| `storeStream(InputStream, Properties)` | `void` | Output transformed document |

**Critical:** Each `getStream(i)` can only be read once. Call `is.getText("UTF-8")` immediately.

### ExecutionUtil

The `ExecutionUtil` class provides dynamic process property (DPP) access and logging.

| Method | Returns | Description |
|--------|---------|-------------|
| `getDynamicProcessProperty(String name)` | `String` | Read DPP value (null if not set) |
| `setDynamicProcessProperty(String name, String value, boolean persistent)` | `void` | Write DPP (persistent=false for runtime-only) |
| `getBaseLogger()` | `Logger` | Get logger instance |

**Logger methods:** `logger.info(String)`, `logger.warning(String)`, `logger.severe(String)`

### Properties

Standard Java `java.util.Properties` — key-value pairs attached to each document. Survives across shapes in the same execution.

---

## Common Patterns

### Pattern 1: Read JSON → Process → Output JSON

```groovy
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String jsonContent = is.getText("UTF-8")
    def data = new JsonSlurper().parseText(jsonContent)

    // Transform data
    data.processedAt = new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'")

    // Output
    String output = JsonOutput.prettyPrint(JsonOutput.toJson(data))
    dataContext.storeStream(new ByteArrayInputStream(output.getBytes("UTF-8")), props)
}
```

### Pattern 2: Read/Write Dynamic Process Properties

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

// Defensive read (DPP may not be set)
String visitedJson = ExecutionUtil.getDynamicProcessProperty("visitedComponentIds")
def visitedSet = []
if (visitedJson && visitedJson.trim()) {
    visitedSet = new JsonSlurper().parseText(visitedJson)
}

// Update
visitedSet << "new-component-id"

// Write back (persistent=false for runtime-only)
ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
```

**Persistence Flag Guidance:**
- `false` (default): DPP cleared after execution completes. Use for runtime-only state.
- `true`: DPP persisted across executions. **Use sparingly** — can cause state leaks.

### Pattern 3: Parse and Modify XML

```groovy
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String xmlContent = is.getText("UTF-8")

    // Parse (false, false = no validation, no namespace awareness)
    def root = new XmlSlurper(false, false).parseText(xmlContent)

    // Modify
    def passwords = root.depthFirst().findAll { it.name() == 'password' }
    passwords.each { it.replaceBody('') }

    // Serialize
    String outputXml = XmlUtil.serialize(root)
    dataContext.storeStream(new ByteArrayInputStream(outputXml.getBytes("UTF-8")), props)
}
```

### Pattern 4: Iterate Documents and Always Store Output

```groovy
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String content = is.getText("UTF-8")

    // ALWAYS call storeStream, even if content is unchanged
    dataContext.storeStream(new ByteArrayInputStream(content.getBytes("UTF-8")), props)
}
```

**Why Always Store:** If you don't call `storeStream()`, the document is dropped from the execution. This can cause the process to fail or lose data.

---

## XML Manipulation Cheat Sheet

### XmlSlurper (Parsing)

```groovy
import groovy.xml.XmlSlurper

def root = new XmlSlurper(false, false).parseText(xmlContent)

// Access elements
String componentId = root.componentId.text()
String folderPath = root.folderFullPath.text()

// Depth-first search for all elements with name
def passwords = root.depthFirst().findAll { it.name() == 'password' }

// Modify element content
passwords.each { it.replaceBody('') }
```

**Constructor Args:** `new XmlSlurper(false, false)` disables validation and namespace awareness for speed.

### XmlUtil (Serialization)

```groovy
import groovy.xml.XmlUtil

// Serialize back to XML string
String outputXml = XmlUtil.serialize(root)
```

**Note:** XmlUtil preserves structure but may reformat whitespace.

### Component XML Structure

Boomi component XML typically has:
- `<componentId>` — UUID identifier
- `<name>` — Human-readable component name
- `<type>` — Component type (process, connection, map, etc.)
- `<version>` — Current version number
- `<folderFullPath>` — Folder location

**Reference Fields (contain component IDs):**
- `<connectionId>`, `<operationId>`, `<mapId>`, `<profileId>` — embed dev component IDs that must be rewritten during promotion

**Environment-Specific Fields (stripped during promotion):**
- `<password>`, `<host>`, `<url>`, `<port>`, `<EncryptedValue>`

---

## JSON Handling Patterns

### JsonSlurper (Parsing)

```groovy
import groovy.json.JsonSlurper

String jsonContent = is.getText("UTF-8")
def data = new JsonSlurper().parseText(jsonContent)

// Access fields
String componentId = data.componentId
def dependencies = data.dependencies  // Array
```

### JsonOutput (Serialization)

```groovy
import groovy.json.JsonOutput

// Serialize to compact JSON
String compact = JsonOutput.toJson(data)

// Serialize to pretty-printed JSON
String pretty = JsonOutput.prettyPrint(JsonOutput.toJson(data))
```

### Array/Map Manipulation

```groovy
// Add to array
def visitedSet = []
visitedSet << "new-id"

// Map operations
def mappingCache = [:]
mappingCache['dev-id-123'] = 'prod-id-456'

// Iterate
mappingCache.each { devId, prodId ->
    println "${devId} -> ${prodId}"
}
```

---

## Sandbox Limitations

### No Network Access
- Cannot make HTTP calls, open sockets, or access external systems
- All external communication must go through connector shapes (HTTP Client, DataHub, etc.)

### No File I/O
- Cannot read/write local filesystem
- Only access to document streams via `dataContext`

### No System Modifications
- Cannot modify system properties
- Cannot create threads or manipulate JVM

### Memory Constraints
- Scripts share JVM heap with Boomi runtime
- Large documents (>10MB) should be streamed, not loaded into memory
- Avoid creating large collections in loops

### DPP Persistence Pitfalls
- `persistent=true` DPPs remain after execution completes
- Can cause state leaks across executions
- Default to `persistent=false` unless you need cross-execution state

---

## Error Handling Best Practices

### Always Wrap Risky Operations

```groovy
import com.boomi.execution.ExecutionUtil

def logger = ExecutionUtil.getBaseLogger()

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)

    String content = is.getText("UTF-8")

    try {
        // Risky operation
        def data = new JsonSlurper().parseText(content)
        // ... transform ...
        String output = JsonOutput.toJson(data)
        dataContext.storeStream(new ByteArrayInputStream(output.getBytes("UTF-8")), props)
    } catch (Exception e) {
        logger.severe("Script error: ${e.message}")
        // Store original content to avoid data loss
        dataContext.storeStream(new ByteArrayInputStream(content.getBytes("UTF-8")), props)
    }
}
```

### Log Errors with Context

```groovy
logger.info("Processing component ${componentId}")
logger.warning("Could not parse ComponentReference XML: ${e.message}")
logger.severe("Script execution failed: ${e.message}")
```

---

## Deep Reference Files

For detailed documentation:
- **Boomi API Objects:** See `reference/boomi-api-objects.md` for full API reference (dataContext, ExecutionUtil, Properties)
- **XML Manipulation:** See `reference/xml-manipulation.md` for XmlSlurper patterns, component XML structure, pretty-printing
- **JSON Handling:** See `reference/json-handling.md` for JsonSlurper/JsonOutput, array/map manipulation
- **Limitations:** See `reference/limitations.md` for sandbox rules, memory constraints, DPP persistence pitfalls

**Project Script Examples:** See `examples/project-scripts.md` for annotated guide to all 6 project Groovy scripts.

---

## Quick Tips

1. **Defensive DPP Reads:** Always check `if (dppValue && dppValue.trim())` before parsing
2. **XmlSlurper Constructor:** Use `new XmlSlurper(false, false)` for speed
3. **Stream Consumption:** Read `is.getText("UTF-8")` immediately, store in String variable
4. **Always Store Output:** Call `dataContext.storeStream()` even on error to avoid data loss
5. **Logger Levels:** `info` for normal flow, `warning` for recoverable issues, `severe` for failures
6. **Pattern.quote for Regex:** Use `Pattern.quote(devId)` when replacing UUIDs to avoid regex special chars

---
globs:
  - "**/*.groovy"
  - "integration/scripts/**"
---

# Groovy Standards

## Output Handling

### Always Use dataContext.storeStream()
- **NEVER skip output** in a Data Process step
- All Groovy scripts MUST call `dataContext.storeStream()` to pass data to the next shape
- Even if the script doesn't modify the document, pass it through

**Example**:
```groovy
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    // ... process the stream ...
    dataContext.storeStream(is, props)
}
```

## Dynamic Process Properties (DPP)

### Persistence Flag Guidance
- **Default to `false`** for most DPPs (in-memory only, cleared after process completes)
- **Use `true`** only for values that MUST survive process execution for external access
- **Never persist** temporary calculations, intermediate results, or sensitive data

**Example**:
```groovy
import com.boomi.execution.ExecutionUtil

// Non-persistent (most common)
ExecutionUtil.setDynamicProcessProperty("tempCounter", "5", false)

// Persistent (use sparingly)
ExecutionUtil.setDynamicProcessProperty("promotionId", uuid, true)
```

## Error Handling

### Always Wrap in Try/Catch
- Use `try/catch` blocks for all Groovy scripts
- Log errors with `logger.severe()` for visibility in Process Reporting
- Throw meaningful exception messages

**Example**:
```groovy
import java.util.logging.Logger

Logger logger = Logger.getLogger("BoomiGroovyScript")

try {
    // Script logic here
} catch (Exception e) {
    logger.severe("Script failed: " + e.getMessage())
    throw new Exception("Failed to process component: " + e.getMessage())
}
```

## XML Handling

### Use XmlSlurper for Reading
- `XmlSlurper` for parsing XML documents
- `XmlUtil.serialize()` for writing XML back to stream

**Example**:
```groovy
import groovy.xml.XmlSlurper
import groovy.xml.XmlUtil

def slurper = new XmlSlurper()
def xml = slurper.parseText(inputXml)

// Modify XML
xml.Component.@name = "NewName"

// Serialize back
String output = XmlUtil.serialize(xml)
```

### Pretty-Printing XML
Use `XmlUtil.serialize()` for normalized, indented XML output (essential for diff operations).

## JSON Handling

### Use JsonSlurper for Parsing
- `JsonSlurper` for reading JSON
- `JsonOutput.prettyPrint()` for writing formatted JSON

**Example**:
```groovy
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

def slurper = new JsonSlurper()
def json = slurper.parseText(inputJson)

// Modify JSON
json.results.each { result ->
    result.status = "processed"
}

// Output pretty JSON
String output = JsonOutput.prettyPrint(JsonOutput.toJson(json))
```

## Boomi Script Sandbox Limitations

### What You CANNOT Do
- **No network access** — cannot make HTTP calls, open sockets
- **No file system access** — cannot read/write local files
- **Limited memory** — avoid loading massive documents into memory
- **No external libraries** — only built-in Groovy classes and Boomi API objects

### What You CAN Do
- Use `dataContext` to access document streams
- Use `ExecutionUtil` to manage DPPs
- Use `Properties` to pass metadata between shapes
- Parse/manipulate XML and JSON
- Perform string operations, regex, calculations

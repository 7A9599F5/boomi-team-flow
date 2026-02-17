# Boomi Groovy Sandbox Limitations

Groovy scripts in Boomi Data Process shapes execute within a **sandboxed environment** with strict limitations for security and stability.

---

## No Network Access

### What's Blocked

- **HTTP/HTTPS requests** — Cannot make outbound API calls
- **Socket connections** — Cannot open TCP/UDP sockets
- **DNS lookups** — Cannot resolve hostnames
- **SMTP/email** — Cannot send emails directly

### Why

Boomi enforces network isolation to:
1. Prevent scripts from bypassing connector-based access controls
2. Avoid unmonitored API calls (rate limits, credentials, logging)
3. Ensure all external communication flows through audited connector shapes

### How to Work Around It

Use connector shapes for all external communication:

**HTTP Calls:**
```
Data Process (Groovy) → HTTP Client Connector → External API
```

**DataHub Access:**
```
Data Process (Groovy) → DataHub Connector → DataHub
```

**Example:**
```groovy
// BAD — This will fail
try {
    def url = new URL("https://api.example.com/data")
    def connection = url.openConnection()
    // FAILS — Network access denied
} catch (Exception e) {
    logger.severe("Network access blocked: ${e.message}")
}

// GOOD — Use HTTP Client connector shape
// 1. Data Process sets DPP with request parameters
// 2. HTTP Client shape makes the API call
// 3. Next Data Process reads the response
```

---

## No File I/O

### What's Blocked

- **File reads** — Cannot read from local filesystem
- **File writes** — Cannot write to local filesystem
- **Directory operations** — Cannot list directories or create folders

### Why

Scripts run on Boomi Atoms/Clouds, which:
1. May not have persistent storage
2. Could be running in containers with ephemeral filesystems
3. Should not store state outside of Boomi's managed storage (DPPs, DataHub)

### How to Work Around It

Use Boomi-provided storage mechanisms:

**For Document Data:**
- Read from `dataContext.getStream(i)`
- Write to `dataContext.storeStream()`

**For Process State:**
- Use Dynamic Process Properties (DPPs)
- Store in DataHub for cross-execution persistence

**Example:**
```groovy
// BAD — This will fail
try {
    new File("/tmp/output.txt").write("data")
    // FAILS — File I/O not allowed
} catch (Exception e) {
    logger.severe("File I/O blocked: ${e.message}")
}

// GOOD — Use dataContext for document output
String output = "transformed data"
dataContext.storeStream(new ByteArrayInputStream(output.getBytes("UTF-8")), props)
```

---

## No System Modifications

### What's Blocked

- **System property changes** — Cannot set `System.setProperty()`
- **Environment variable access** — Cannot read/write env vars
- **JVM manipulation** — Cannot modify JVM settings
- **Class loading** — Cannot load custom classes or JARs

### Why

Scripts share the JVM with the Boomi runtime. Allowing system modifications could:
1. Break other processes running on the same Atom
2. Create security vulnerabilities
3. Cause unpredictable behavior

### How to Work Around It

Use Boomi's controlled configuration mechanisms:

**For Configuration:**
- Use Process Properties (static or dynamic)
- Store configuration in DataHub
- Use Atom-level environment extensions (configured via Boomi UI)

**Example:**
```groovy
// BAD — This will fail
System.setProperty("myconfig.value", "123")
// FAILS — System property modification blocked

// GOOD — Use Dynamic Process Property
ExecutionUtil.setDynamicProcessProperty("myconfig.value", "123", false)
```

---

## No Thread Creation or Manipulation

### What's Blocked

- **Thread creation** — Cannot use `new Thread()` or `Executors`
- **Thread pools** — Cannot create thread pools
- **Concurrency primitives** — Cannot use `synchronized`, `Lock`, etc.

### Why

Boomi manages threading internally. Scripts creating threads could:
1. Exhaust thread pools
2. Cause deadlocks
3. Interfere with Boomi's execution model

### How to Work Around It

Use Boomi's process flow for parallelism:

**For Parallel Processing:**
- Use Branch shape with parallel paths
- Use Map shape to split documents
- Each document in the stream is processed sequentially (no need for threads)

**Example:**
```groovy
// BAD — This will fail
Thread t = new Thread({
    println "Background task"
})
t.start()
// FAILS — Thread creation blocked

// GOOD — Use Boomi's document loop
for (int i = 0; i < dataContext.getDataCount(); i++) {
    // Each document is processed sequentially
    // Boomi handles concurrency at the process level
}
```

---

## Memory Constraints

### Heap Size Limits

Scripts share JVM heap with the Boomi runtime:
- **Local Atom:** Typically 2-4 GB heap
- **Cloud Atom:** Typically 4-8 GB heap
- **Molecule:** Varies by configuration

### What Happens on OOM

If a script exhausts memory:
1. The process fails with `OutOfMemoryError`
2. Other processes on the same Atom may be affected
3. The Atom may need to be restarted

### Best Practices

**Stream Large Documents:**
```groovy
// BAD — Loads entire document into memory
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    String content = is.getText("UTF-8")  // Could be 100MB+
    // ... process content ...
}

// BETTER — Process line-by-line if possible
// (Note: Boomi doesn't provide line-by-line streaming, but you can chunk)
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    BufferedReader reader = new BufferedReader(new InputStreamReader(is, "UTF-8"))
    String line
    while ((line = reader.readLine()) != null) {
        // Process line
    }
}
```

**Avoid Large Collections in Loops:**
```groovy
// BAD — Accumulates memory
def allComponents = []
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    String content = is.getText("UTF-8")
    def component = new JsonSlurper().parseText(content)
    allComponents << component  // Could be thousands of components
}
// allComponents now holds everything in memory

// BETTER — Process one at a time
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    String content = is.getText("UTF-8")
    def component = new JsonSlurper().parseText(content)
    // Process component immediately
    // ... transform ...
    dataContext.storeStream(...)
    // component is now eligible for garbage collection
}
```

---

## Dynamic Process Property (DPP) Persistence

### Persistent vs Non-Persistent DPPs

```groovy
// Non-persistent (cleared after execution)
ExecutionUtil.setDynamicProcessProperty("tempData", "value", false)

// Persistent (survives across executions)
ExecutionUtil.setDynamicProcessProperty("config", "value", true)
```

### When to Use persistent=true

**Valid Use Cases:**
- Configuration loaded once and reused (e.g., account IDs, environment names)
- Counters that increment across executions
- Cached data that is expensive to recompute

**Example:**
```groovy
// Load config once, reuse across executions
String apiToken = ExecutionUtil.getDynamicProcessProperty("apiToken")
if (!apiToken) {
    // Load from DataHub or external source
    apiToken = loadApiToken()
    ExecutionUtil.setDynamicProcessProperty("apiToken", apiToken, true)
}
```

### When to Use persistent=false (Default)

**Use for Runtime-Only State:**
- Loop counters
- Temporary caches (visited sets, mapping caches)
- Intermediate results that are only relevant to the current execution

**Example:**
```groovy
// Visited set for BFS traversal — only relevant to this execution
def visitedSet = []
// ... build visited set ...
ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
```

### Pitfall: Persistent DPP Leaks

**Problem:**
If you use `persistent=true` for state that should be cleared, it can leak across executions.

**Example of the Problem:**
```groovy
// Execution 1: Process component A
ExecutionUtil.setDynamicProcessProperty("currentComponentId", "component-A", true)

// Execution 2: Process component B (but DPP still has "component-A")
String currentId = ExecutionUtil.getDynamicProcessProperty("currentComponentId")
// currentId = "component-A" (wrong!)
```

**Solution:**
Use `persistent=false` for execution-specific state:
```groovy
ExecutionUtil.setDynamicProcessProperty("currentComponentId", "component-A", false)
// Cleared after execution completes
```

---

## DPP Size Limits

### Practical Limits

While Boomi doesn't document a hard DPP size limit, best practices:
- Keep DPPs under **1 MB** per property
- Avoid storing large XML/JSON documents in DPPs
- Use DataHub for large datasets

### What Happens on Overflow

If a DPP becomes too large:
1. Performance degrades (serialization overhead)
2. Process may fail with memory errors
3. Other processes on the same Atom may be affected

### Best Practices

**For Small Datasets:**
```groovy
// OK — Small JSON array (hundreds of IDs)
def visitedSet = ["id1", "id2", "id3"]
ExecutionUtil.setDynamicProcessProperty("visitedComponentIds", JsonOutput.toJson(visitedSet), false)
```

**For Large Datasets:**
```groovy
// BAD — Large JSON array (thousands of component XMLs)
def allComponentXmls = []
for (int i = 0; i < 10000; i++) {
    allComponentXmls << fetchComponentXml(i)
}
ExecutionUtil.setDynamicProcessProperty("allComponents", JsonOutput.toJson(allComponentXmls), false)
// This will likely fail or cause performance issues

// GOOD — Store in DataHub, keep only metadata in DPP
def processedIds = []
for (int i = 0; i < 10000; i++) {
    String componentXml = fetchComponentXml(i)
    storeInDataHub(componentXml)  // Use DataHub connector
    processedIds << extractComponentId(componentXml)
}
ExecutionUtil.setDynamicProcessProperty("processedIds", JsonOutput.toJson(processedIds), false)
```

---

## Summary of Limitations

| Feature | Allowed? | Workaround |
|---------|----------|------------|
| HTTP requests | ❌ No | Use HTTP Client connector |
| File I/O | ❌ No | Use dataContext streams or DataHub |
| System properties | ❌ No | Use Dynamic Process Properties |
| Thread creation | ❌ No | Use Boomi process flow (Branch, Map) |
| Large memory allocations | ⚠️ Limited | Stream data, avoid large collections |
| Persistent DPPs | ⚠️ Use sparingly | Default to `persistent=false` |
| External JARs | ❌ No | Use Boomi-provided libraries or Atom extensions |

---

## Best Practices Summary

1. **Always use connector shapes for external communication** — No direct HTTP, no database access
2. **Stream large documents** — Don't load entire documents into memory
3. **Default to persistent=false for DPPs** — Only use `persistent=true` for cross-execution state
4. **Keep DPPs small** — Use DataHub for large datasets
5. **Wrap risky operations in try/catch** — Always log errors and handle gracefully
6. **Always call dataContext.storeStream()** — Even on error, to avoid data loss

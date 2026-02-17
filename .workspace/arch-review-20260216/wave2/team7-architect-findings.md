# Team 7 — Data Transform Architect Findings

**Date:** 2026-02-16
**Reviewer:** Data Transform Architect
**Scope:** All 6 Groovy scripts in `/integration/scripts/`, evaluated against build guides, groovy standards, and integration context
**Cross-referenced:** Team 2 Integration Engine Consensus (wave1)

---

## Critical Findings

### CRIT-1: `strip-env-config.groovy` Strips by Element Name at Any Depth — Data Corruption Risk

**File:** `integration/scripts/strip-env-config.groovy:21-57`
**Context:** Process C step 11

The script uses `root.depthFirst().findAll { it.name() == 'password' }` (and similarly for `host`, `url`, `port`, `EncryptedValue`) to strip values. This matches ANY element with these names at ANY depth in the component XML tree.

**Problem:** Boomi component XML has legitimate, non-sensitive uses of these element names:
- A **Map** component may contain transformation functions that reference `url` or `host` as field names in profile definitions
- A **Process Property** component could define properties named `port` or `host` for application configuration (non-connection)
- Profile elements can contain `url` nodes describing endpoint metadata, not credentials

The script will empty these legitimate values, silently corrupting the promoted component. The component will appear "promoted successfully" but will be broken in production.

**Severity justification:** This is worse than a build guide bug because the Groovy script is the actual implementation, not documentation. Corrupted data will only be discovered after merge to main, potentially after deployment.

**Mitigation (existing):** Branch isolation means the diff viewer (Process G) can reveal damage before merge. However, reviewers must know what to look for.

**Recommendation:** Scope stripping to connection-type components only, or restrict to known Boomi connection XML paths (e.g., elements within `<connectionConfiguration>` or `<overridableConnectionConfig>` parent nodes):

```groovy
// Instead of:
root.depthFirst().findAll { it.name() == 'password' }

// Scope to connection config:
def connConfig = root.depthFirst().findAll {
    it.name() in ['connectionConfiguration', 'overridableConnectionConfig']
}
connConfig.each { config ->
    config.depthFirst().findAll { it.name() == 'password' }.each { it.replaceBody '' }
}
```

**Cross-reference:** Confirmed by Team 2 as MAJ-9. Upgrading to CRITICAL here because, from a data transformation perspective, silent data corruption in the transform pipeline is the highest-severity class of defect.

---

### CRIT-2: `rewrite-references.groovy` Performs Raw String Replacement on Serialized XML — Structural Integrity Risk

**File:** `integration/scripts/rewrite-references.groovy:27-29`
**Context:** Process C steps 15a.1 and 15b.1

```groovy
mappingCache.each { devId, prodId ->
    if (xmlContent.contains(devId)) {
        xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
```

The script replaces component IDs via string substitution on the full XML text rather than parsed XML node traversal.

**Problem 1 — CDATA and comment corruption:** If a dev component ID appears inside an XML comment (`<!-- reference: abc-123 -->`) or CDATA block, it will be rewritten. While comments are benign, CDATA values in Boomi maps (e.g., scripted map functions containing ID references as string literals) will be silently mutated.

**Problem 2 — Partial match in attribute values:** While `Pattern.quote()` prevents regex issues, component IDs could theoretically appear as substrings of longer values (e.g., URIs, composite keys). GUIDs make this extremely unlikely but the algorithm provides no structural guarantee.

**Problem 3 — Multiple passes create ordering dependency:** The `mappingCache.each` iterates over all mappings for every document. If a prod ID matches another dev ID (theoretically possible in multi-account scenarios where a component promoted from Account A has a prod ID that is a dev ID in Account B), the script could perform double-rewriting.

**Practical risk assessment:** Low for Problems 1-2 due to GUID format. Problem 3 is theoretically possible in multi-account environments where the same primary account receives promotions from multiple dev accounts.

**Recommendation:** For correctness, use XmlSlurper to traverse and rewrite only element text nodes and attribute values that match component ID patterns:

```groovy
def root = new XmlSlurper(false, false).parseText(xmlContent)
root.depthFirst().each { node ->
    // Rewrite element text
    String text = node.text()
    if (text && mappingCache.containsKey(text.trim())) {
        node.replaceBody(mappingCache[text.trim()])
        rewriteCount++
    }
    // Rewrite attributes
    node.attributes().each { attrName, attrValue ->
        if (mappingCache.containsKey(attrValue)) {
            node["@${attrName}"] = mappingCache[attrValue]
            rewriteCount++
        }
    }
}
```

**Cross-reference:** Team 2 MIN-4 and unresolved debate #2. Upgrading to CRITICAL from a data integrity perspective because a transform architect must guarantee structural validity of output documents.

---

## Major Findings

### MAJ-1: `build-visited-set.groovy` Uses O(n) List for Visited Set — Quadratic BFS

**File:** `integration/scripts/build-visited-set.groovy:17-19, 33, 50`
**Context:** Process B BFS loop

```groovy
def visitedSet = []  // Line 17: ArrayList, not Set
...
if (visitedSet.contains(currentId)) {  // Line 33: O(n) lookup
...
if (childId && !visitedSet.contains(childId) && !queue.contains(childId)) {  // Line 50: O(n) + O(n)
```

The visited set is a JSON array (ArrayList after parsing). Each `contains()` check is O(n). For a component tree of depth d with branching factor b:
- Total nodes: n = b^d
- Per-node: 1 visited check + k child checks (each O(n) on visited + O(n) on queue)
- Worst case: O(n^2) total contains operations

For a tree of 50 components, this is ~2500 contains operations. At 100 components, ~10,000. The API call latency (120ms per hop) dominates, but the DPP serialization overhead also grows: each iteration serializes the full visited set and queue to JSON, stores them as DPP strings, and deserializes on the next iteration.

**DPP serialization concern:** A visited set of 100 GUIDs serialized to JSON is ~4KB. The `componentQueue` similarly grows. Each BFS iteration does 2 JSON parses + 2 JSON serializations + 4 DPP writes. For 100 iterations, that is 800 DPP operations.

**Recommendation:** While a HashSet cannot be stored as a DPP (DPPs are strings), the JSON structure should use an object instead of an array for O(1) key lookup:

```groovy
// Use JSON object instead of array for O(1) lookup
def visitedSet = [:]  // map: componentId -> true
if (visitedJson && visitedJson.trim()) {
    visitedSet = new JsonSlurper().parseText(visitedJson)
}
...
if (visitedSet.containsKey(currentId)) { ... }
else {
    visitedSet[currentId] = true
    ...
}
```

**Cross-reference:** Team 2 MIN-7 (they rated it minor due to API latency dominance). Upgrading to MAJOR because the quadratic growth compounds with DPP serialization overhead, and 100+ component trees are realistic for large Boomi implementations.

---

### MAJ-2: `sort-by-dependency.groovy` Default Priority Hides Unknown Types

**File:** `integration/scripts/sort-by-dependency.groovy:17`
**Context:** Process C step 5

```groovy
return 3  // Default: middle of the pack
```

Unknown component types (e.g., `processroute`, `certificate`, `crossreference`, `flowservice`) get priority 3 (same as `operation`). This has two problems:

**Problem 1 — Silent misplacement:** An unknown type that depends on connections (priority 2) will be placed correctly, but one that should precede profiles (e.g., a `certificate` used by a connection) will be placed after profiles, causing the connection's reference rewrite to miss the certificate mapping.

**Problem 2 — No warning logged:** The script does not log or flag when it encounters an unknown type. Operators have no visibility into whether the sort is meaningful for all components.

**Problem 3 — `processroute` is a real Boomi type that references processes.** It should be at priority 5 alongside sub-processes, not 3.

**Recommendation:**
```groovy
def typePriority = { String type, String componentId, String rootId ->
    type = type?.toLowerCase() ?: ''
    if (type.contains('profile')) return 1
    if (type == 'connection') return 2
    if (type.contains('operation')) return 3
    if (type == 'map') return 4
    if (type == 'processroute') return 5
    if (type == 'process' && componentId == rootId) return 6
    if (type == 'process') return 5
    logger.warning("Unknown component type '${type}' for ${componentId} — defaulting to priority 5")
    return 5  // Conservative: promote later rather than earlier
}
```

**Cross-reference:** Team 2 MIN-6 (minor). Upgrading to MAJOR because incorrect sort order causes silent reference rewrite failures in Process C — the downstream impact is data corruption, not just a cosmetic issue.

---

### MAJ-3: `validate-connection-mappings.groovy` Discards Input Document Properties

**File:** `integration/scripts/validate-connection-mappings.groovy:72-75`
**Context:** Process C step 5.6

```groovy
dataContext.storeStream(
    new ByteArrayInputStream(JsonOutput.toJson(nonConnections).getBytes("UTF-8")),
    new Properties()  // <-- Empty properties, discards input metadata
)
```

The script creates a new `Properties()` object instead of preserving the input document's properties. In Boomi, document properties carry tracking metadata (document index, custom properties set by upstream shapes). While the current process flow may not rely on these, this violates the groovy-standards.md directive and is fragile:

> "Even if the script doesn't modify the document, pass it through"

Additionally, the script only reads `dataContext.getStream(0)` (line 26) rather than iterating over all documents. If the upstream shape (sort-by-dependency) produces multiple documents, only the first is processed and the rest are silently dropped.

**Recommendation:**
```groovy
def is = dataContext.getStream(0)
Properties props = dataContext.getProperties(0)  // Preserve properties
...
dataContext.storeStream(
    new ByteArrayInputStream(JsonOutput.toJson(nonConnections).getBytes("UTF-8")),
    props  // Pass through original properties
)
```

**Cross-reference:** Team 2 MIN-8. Upgrading to MAJOR because discarding document properties breaks the data contract between Boomi shapes and could cause subtle issues if process tracking properties are added later.

---

### MAJ-4: `build-visited-set.groovy` Missing Top-Level Try/Catch

**File:** `integration/scripts/build-visited-set.groovy` (entire file)
**Context:** Process B step 7

The groovy-standards.md mandates:

> "Always Wrap in Try/Catch — Use try/catch blocks for all Groovy scripts. Log errors with logger.severe() for visibility in Process Reporting."

The `build-visited-set.groovy` script has a try/catch only around the XML parsing block (lines 43-57), not the entire script body. If `JsonSlurper.parseText()` fails on a corrupted `visitedComponentIds` DPP (lines 19, 26), or if `dataContext.getStream()` returns null, the script throws an unhandled exception that appears as a generic "Data Process shape failed" error in Boomi Process Reporting with no diagnostic context.

**Affected scripts:** `build-visited-set.groovy` and `sort-by-dependency.groovy` both lack top-level try/catch. `validate-connection-mappings.groovy` also lacks it.

**Recommendation:** Wrap each script's body in a try/catch that logs the script name and error:

```groovy
try {
    // ... entire script body ...
} catch (Exception e) {
    logger.severe("build-visited-set.groovy failed: ${e.message}")
    throw new Exception("BFS visited set construction failed for component ${currentId}: ${e.message}")
}
```

---

### MAJ-5: `strip-env-config.groovy` Uses `replaceBody('')` Which May Produce Invalid XML for Required Elements

**File:** `integration/scripts/strip-env-config.groovy:23, 29, 35, 41, 47`
**Context:** Process C step 11

```groovy
passwords.each { it.replaceBody '' }
```

`GPathResult.replaceBody('')` sets the element's text content to empty string, producing XML like `<password></password>`. If the Boomi Platform API's component XML schema defines `password` as a required element with `minLength` constraints, the emptied element could fail schema validation when the component is updated via the API (steps 15a.2 or 15b.2).

**Specific risk:** The `EncryptedValue` element in Boomi connection XML may have internal validation that rejects empty values. The API might accept it (creating a broken connection) or reject it (causing the promotion to fail with an opaque API error).

**Recommendation:** Consider removing the element entirely rather than emptying it:

```groovy
passwords.each { it.replaceNode {} }
```

Or, if the element must be present for schema compliance, set a sentinel value:

```groovy
passwords.each { it.replaceBody '***STRIPPED***' }
```

The sentinel approach is more visible during diff review and clearly communicates that the value was intentionally removed.

---

## Minor Findings

### MIN-1: `normalize-xml.groovy` Claims "Sorted Attributes" but XmlUtil.serialize Does Not Sort Them

**File:** `integration/scripts/normalize-xml.groovy:18`
**Context:** Process G

The script's docstring states: "Normalized XML with consistent indentation (2-space indent, sorted attributes)". However, `XmlUtil.serialize()` does NOT sort XML attributes. Attribute ordering in serialized output depends on the parser's internal hash map ordering, which is not guaranteed to be consistent across JVM instances or Groovy versions.

**Impact:** Two identical components fetched in separate API calls could produce different attribute orderings, creating false positives in the diff viewer. This partially defeats the purpose of normalization.

**Recommendation:** If attribute sorting is required, use a custom serializer or post-process with a regex-based attribute sorter. Alternatively, update the docstring to remove the "sorted attributes" claim and document that attribute order differences are expected.

---

### MIN-2: `rewrite-references.groovy` Does Not Validate Mapping Cache Format

**File:** `integration/scripts/rewrite-references.groovy:16-20`
**Context:** Process C steps 15a.1, 15b.1

```groovy
String mappingJson = ExecutionUtil.getDynamicProcessProperty("componentMappingCache")
def mappingCache = [:]
if (mappingJson && mappingJson.trim()) {
    mappingCache = new JsonSlurper().parseText(mappingJson)
}
```

If `componentMappingCache` contains malformed JSON (e.g., due to the DPP size truncation risk identified in Team 2 MAJ-10), `JsonSlurper.parseText()` will throw an exception. The script has no try/catch and no validation that the parsed result is a Map.

**Recommendation:** Add defensive parsing:

```groovy
try {
    def parsed = new JsonSlurper().parseText(mappingJson)
    if (parsed instanceof Map) {
        mappingCache = parsed
    } else {
        logger.severe("componentMappingCache is not a JSON object: ${parsed.getClass()}")
    }
} catch (Exception e) {
    logger.severe("Failed to parse componentMappingCache: ${e.message}")
    throw new Exception("Reference rewriting aborted — corrupt mapping cache")
}
```

---

### MIN-3: `sort-by-dependency.groovy` Uses `contains()` for Type Matching — Overly Broad

**File:** `integration/scripts/sort-by-dependency.groovy:11, 13`

```groovy
if (type.contains('profile')) return 1
...
if (type.contains('operation')) return 3
```

`type.contains('profile')` will match `xmlprofile`, `jsonprofile`, `flatfileprofile`, etc. — which is intentionally broad. However, it also matches any hypothetical type containing "profile" as a substring (e.g., `profileroute`). Similarly, `type.contains('operation')` would match a type like `operationlog`.

**Practical risk:** Very low, since Boomi component types are well-defined. But the pattern trades specificity for brevity.

**Recommendation:** Use `startsWith` or explicit set membership for clarity:

```groovy
if (type in ['xmlprofile', 'jsonprofile', 'flatfileprofile', 'profile']) return 1
```

---

### MIN-4: `build-visited-set.groovy` Extracts Both `componentId` and `referenceComponentId` Without Deduplication Context

**File:** `integration/scripts/build-visited-set.groovy:48`

```groovy
root.depthFirst().findAll { it.name() == 'componentId' || it.name() == 'referenceComponentId' }.each { ref ->
```

The Boomi ComponentReference API returns both `componentId` (the parent) and `referenceComponentId` (the child). By extracting both, the script may re-queue the current component itself (since `componentId` refers to the parent component being queried). The visited set check on line 50 prevents duplicate processing, but it adds unnecessary entries to the queue.

**Recommendation:** Only extract `referenceComponentId` values, which are the actual children:

```groovy
root.depthFirst().findAll { it.name() == 'referenceComponentId' }.each { ref ->
```

---

### MIN-5: `normalize-xml.groovy` Returns Empty String for Empty Input — Inconsistent with Error Path

**File:** `integration/scripts/normalize-xml.groovy:31-35`

```groovy
if (xmlContent == null || xmlContent.trim().isEmpty()) {
    logger.info("Empty XML input — passing through as empty string")
    dataContext.storeStream(new ByteArrayInputStream("".getBytes("UTF-8")), props)
    continue
}
```

Empty input produces an empty output document. The error path (line 62) passes through the original content. This inconsistency means the diff viewer receives different types of "bad input" in different formats — one is empty, the other is raw unparseable XML. Neither is a valid diff input.

**Recommendation:** Treat empty input the same as parse failure — pass through as-is with a marker DPP:

```groovy
ExecutionUtil.setDynamicProcessProperty("normalizationFailed", "true", false)
```

---

## Observations

### OBS-1: Script Separation of Concerns is Well-Designed

Each script has a single, clear responsibility:
- `build-visited-set.groovy` — BFS state management
- `sort-by-dependency.groovy` — type-hierarchy ordering
- `strip-env-config.groovy` — credential removal
- `validate-connection-mappings.groovy` — pre-promotion validation
- `rewrite-references.groovy` — ID translation
- `normalize-xml.groovy` — XML normalization for diff

No script tries to do two things. Input/output contracts are clear through DPP naming conventions. This modularity makes the pipeline easy to reason about and modify.

### OBS-2: DPP-Based State Passing is Appropriate for Boomi Constraints

Given the Boomi sandbox limitations (no file I/O, no network, no external libraries), using DPPs to pass state between Data Process shapes is the correct pattern. The alternative (document properties) would require the state to travel with each document, which is more complex for BFS where multiple documents are processed in sequence. The choice of JSON serialization for structured DPP values is idiomatic.

### OBS-3: validate-connection-mappings.groovy is a Strong Fail-Fast Pattern

The batch pre-validation of connection mappings (step 5.5-5.7) is architecturally sound. It:
1. Queries all connection mappings in a single DataHub call
2. Validates the full set before entering the promotion loop
3. Collects ALL missing mappings (not just the first) for actionable error messages
4. Filters connections out of the promotion stream (they are not promoted, only mapped)

This prevents wasted API calls and branch pollution from partial promotions that would fail on missing connections.

### OBS-4: Logging is Consistent and Diagnostic

All scripts provide meaningful log output at key decision points (visited/not-visited, rewrite counts, stripped elements, sort order). This supports Boomi Process Reporting and operational debugging. The `rewrittenIds` array in `rewrite-references.groovy:31` provides a full audit trail.

---

## Multi-Environment Assessment

### Impact on Groovy Scripts

The Phase 7 multi-environment extension (TEST/PRODUCTION modes) does not directly modify any Groovy scripts. The scripts operate on component XML and DPPs, which are environment-agnostic. This is a strength — the scripts work identically regardless of whether the promotion targets a test environment or production.

### Potential Risks

1. **DPP size growth:** In multi-environment scenarios, the `componentMappingCache` may accumulate mappings across TEST and PRODUCTION promotions if the cache is not reset between runs. The current architecture resets per-process-execution, which is correct.

2. **Strip-env-config in TEST mode:** If TEST deployments are meant to preserve some environment configuration for testing (e.g., test URLs), the current blanket stripping prevents this. The script has no awareness of promotion mode.

3. **Branch ID in rewrite context:** For TEST-to-PRODUCTION promotions (where the branch is preserved), `rewrite-references.groovy` must ensure it operates on the correct branch version of the XML. This is controlled by the upstream HTTP Client call, not the script itself.

### Assessment

The scripts are **environment-agnostic by design**, which is correct. No script changes are needed for multi-environment support. The one gap is that `strip-env-config.groovy` cannot selectively strip based on promotion mode, but this is likely acceptable since credentials should never be promoted regardless of target environment.

---

## Idempotency Assessment

| Script | Idempotent? | Notes |
|--------|-------------|-------|
| `build-visited-set.groovy` | Yes | Visited set check prevents double-processing |
| `sort-by-dependency.groovy` | Yes | Pure function on input array |
| `strip-env-config.groovy` | Yes | Stripping an already-empty element is a no-op |
| `validate-connection-mappings.groovy` | Yes | Read-only check; DPP writes are deterministic |
| `rewrite-references.groovy` | **No** | Double-rewriting could occur if re-run after cache update. If devId A maps to prodId B, and prodId B happens to be another devId, re-running produces incorrect output. Mitigated by single-pass execution in Process C. |
| `normalize-xml.groovy` | Yes | Parse-serialize is deterministic |

**Key risk:** `rewrite-references.groovy` is safe only because Process C guarantees single-pass execution per component. If the process were modified to retry failed components, double-rewriting could occur.

---

## Testability Assessment

| Script | Unit Testable? | Barrier |
|--------|---------------|---------|
| `build-visited-set.groovy` | Partial | Depends on `ExecutionUtil` (Boomi API) and `dataContext` (Boomi runtime). Mock objects needed. |
| `sort-by-dependency.groovy` | Partial | Same `ExecutionUtil`/`dataContext` dependency. The `typePriority` closure could be extracted for pure testing. |
| `strip-env-config.groovy` | Good | Core logic (XmlSlurper parse, depthFirst, replaceBody) uses standard Groovy. Only logging and DPP writes need mocks. |
| `validate-connection-mappings.groovy` | Good | Same as above — standard JSON parsing with DPP reads/writes. |
| `rewrite-references.groovy` | Good | String replacement logic is pure Groovy. DPP read is the only Boomi dependency. |
| `normalize-xml.groovy` | Excellent | Core logic (XmlSlurper + XmlUtil.serialize) is standard Groovy with no Boomi dependencies except logging. |

**Recommendation:** Extract core transformation logic into pure functions that can be tested outside Boomi. Use a simple mock framework for `ExecutionUtil` and `dataContext`:

```groovy
// Testable pure function extracted from sort-by-dependency.groovy
static int getTypePriority(String type, String componentId, String rootId) {
    type = type?.toLowerCase() ?: ''
    if (type.contains('profile')) return 1
    // ...
}
```

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Major | 5 |
| Minor | 5 |
| Observations | 4 |

**Top 5 Recommendations (Priority Order):**

1. **Scope `strip-env-config.groovy` to connection configuration paths** — prevent silent data corruption of non-connection components (CRIT-1)
2. **Replace string-based ID rewriting with parsed XML traversal** in `rewrite-references.groovy` — guarantee structural XML integrity (CRIT-2)
3. **Switch `build-visited-set.groovy` visited set from array to object** for O(1) lookups — prevent quadratic scaling (MAJ-1)
4. **Add unknown type logging and conservative default to `sort-by-dependency.groovy`** — prevent silent misplacement (MAJ-2)
5. **Add top-level try/catch to all scripts lacking it** — comply with groovy-standards.md and enable diagnostic logging (MAJ-4)

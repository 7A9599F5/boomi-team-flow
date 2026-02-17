# Team 7: Boomi Groovy Expert Review — Deep Code Analysis

**Reviewer**: Boomi Groovy Expert (Team 7)
**Date**: 2026-02-16
**Scope**: All 6 Groovy scripts in `integration/scripts/`
**Reference**: `groovy-standards.md`, `20-appendix-dpp-catalog.md`, build guide processes B and C

---

## Critical Findings

### C-1: Missing Top-Level Try/Catch in 4 of 6 Scripts

**Severity**: Critical
**Files affected**:
- `integration/scripts/build-visited-set.groovy` (entire file)
- `integration/scripts/sort-by-dependency.groovy` (entire file)
- `integration/scripts/strip-env-config.groovy` (entire file)
- `integration/scripts/validate-connection-mappings.groovy` (entire file)

**Standards violation**: `groovy-standards.md` mandates: "Use `try/catch` blocks for **all** Groovy scripts. Log errors with `logger.severe()` for visibility in Process Reporting. Throw meaningful exception messages."

**Details**:

| Script | Has try/catch? | Risk |
|--------|---------------|------|
| `build-visited-set.groovy` | Partial — only around XML parsing (lines 43-57), NOT around JSON parsing (lines 18-27), DPP access, or storeStream | If `visitedComponentIds` DPP contains malformed JSON, `JsonSlurper.parseText()` at line 19 throws an unhandled exception. The entire BFS process fails with no diagnostic logging. |
| `sort-by-dependency.groovy` | None | If `JsonSlurper.parseText()` at line 25 fails (corrupt JSON from upstream), or if the components list is not an array, the process fails silently with a raw Groovy stack trace instead of a meaningful error. |
| `strip-env-config.groovy` | None | If `XmlSlurper.parseText()` at line 15 fails (malformed XML from Platform API), no `logger.severe()` call, no meaningful error message. Compare with `normalize-xml.groovy` which correctly wraps parsing in try/catch. |
| `validate-connection-mappings.groovy` | None | If `connCacheJson` DPP is missing or malformed, `JsonSlurper.parseText()` at line 30 throws an unhandled exception. Script also lacks a logger entirely — no `ExecutionUtil.getBaseLogger()` call. |

**Only compliant scripts**: `rewrite-references.groovy` (no explicit try/catch but uses safe `Pattern.quote()` and `contains` checks), `normalize-xml.groovy` (proper try/catch with `logger.severe()` and fallback).

**Note**: `rewrite-references.groovy` also lacks a top-level try/catch despite the standard requirement. Its operations are individually safe (string replacement), but a corrupt `componentMappingCache` DPP would cause an unhandled `JsonSlurper` exception at line 19.

**Recommendation**: Wrap each script's for-loop (or entire body) in a top-level try/catch that calls `logger.severe()` and throws a descriptive exception. Pattern:

```groovy
try {
    // existing script body
} catch (Exception e) {
    logger.severe("ScriptName failed: ${e.message}")
    throw new Exception("ScriptName failed for component ${currentId}: ${e.message}")
}
```

---

### C-2: validate-connection-mappings.groovy Only Processes First Document

**Severity**: Critical
**File**: `integration/scripts/validate-connection-mappings.groovy:25-26`

```groovy
def is = dataContext.getStream(0)
def components = new JsonSlurper().parseText(is.text)
```

**Problem**: Script uses `dataContext.getStream(0)` instead of iterating with `for (int i = 0; i < dataContext.getDataCount(); i++)`. If multiple documents arrive (e.g., due to upstream splitting or Boomi document batching), only the first is processed. All subsequent documents are silently dropped.

**Contrast**: All other scripts properly iterate: `build-visited-set.groovy:9`, `sort-by-dependency.groovy:20`, `strip-env-config.groovy:10`, `rewrite-references.groovy:9`, `normalize-xml.groovy:25`.

**Impact**: In the Process C canvas, `validate-connection-mappings.groovy` runs after `sort-by-dependency.groovy` (step 5.6). If for any reason the document count is > 1, components in documents 2+ are silently dropped from the promotion pipeline. This could cause incomplete promotions with no error indication.

**Additionally**: Line 74 creates a new `Properties()` instead of passing through original properties:
```groovy
dataContext.storeStream(
    new ByteArrayInputStream(JsonOutput.toJson(nonConnections).getBytes("UTF-8")),
    new Properties()  // Original document properties lost
)
```

This discards any document-level properties (tracking IDs, metadata) that downstream shapes may rely on.

**Recommendation**: Either (a) add a multi-document loop like the other scripts, or (b) add explicit documentation that this script is designed for single-document input only, with a guard:
```groovy
if (dataContext.getDataCount() > 1) {
    logger.warning("validate-connection-mappings received ${dataContext.getDataCount()} documents, expected 1")
}
```

Also preserve original properties: `Properties props = dataContext.getProperties(0)` and pass `props` to `storeStream()`.

---

### C-3: No Maximum Depth / Cycle Guard in BFS Traversal

**Severity**: Critical
**File**: `integration/scripts/build-visited-set.groovy`

**Problem**: The BFS traversal has a visited-set check (line 33: `if (visitedSet.contains(currentId))`) which prevents re-visiting nodes. However, there are two issues:

1. **No maximum depth or maximum component count limit**: A dev account with a deeply nested or wide dependency tree could cause the BFS to run indefinitely. Boomi processes have execution time limits (varies by plan), but a runaway traversal could consume the entire time quota before timing out, leaving the process in an indeterminate state.

2. **Circular references through metadata, not just component IDs**: The visited-set tracks `currentComponentId`, but the child extraction at line 48 looks for both `componentId` and `referenceComponentId` elements. If the Boomi Platform API returns self-references (component referencing itself), the script handles this correctly via the visited set. However, if the API returns a reference to a component that references back to an already-queued (but not yet visited) component, both could end up in the queue simultaneously. The queue de-duplication check at line 50 (`!queue.contains(childId)`) mitigates this, but only if the child ID hasn't been popped from the queue before the parent is processed.

**Risk**: In practice, Boomi component graphs are DAGs (directed acyclic graphs), so true cycles are unlikely. But a defensive depth limit is industry best practice for any graph traversal.

**Recommendation**: Add a maximum visited set size (e.g., 500 components) with a clear error:
```groovy
if (visitedSet.size() > 500) {
    throw new Exception("Dependency traversal exceeded 500 components — possible circular reference or overly complex dependency tree")
}
```

---

## Major Findings

### M-1: rewrite-references.groovy Has Partial GUID Match Risk

**Severity**: Major
**File**: `integration/scripts/rewrite-references.groovy:28-29`

```groovy
mappingCache.each { devId, prodId ->
    if (xmlContent.contains(devId)) {
        xmlContent = xmlContent.replaceAll(Pattern.quote(devId), prodId)
```

**Problem**: The script performs global string replacement of dev GUIDs with prod GUIDs across the entire XML document. While `Pattern.quote()` correctly escapes the GUID string for regex, the replacement is not bounded by word/element boundaries.

**Scenario**: Boomi component IDs are UUIDs (e.g., `abcdef12-3456-7890-abcd-ef1234567890`). In practice, UUIDs appearing as substrings of other UUIDs is extremely unlikely due to the dash-delimited format. However, GUIDs may appear in:
- XML attribute values (intended — these are component references)
- XML text content (intended)
- XML comments (unintended — could corrupt documentation)
- CDATA sections (unintended — could corrupt embedded scripts or expressions)

The more significant risk: if a dev GUID appears in the `name` attribute or description text of a component (e.g., a component named `"Process for abcdef12-3456-7890-abcd-ef1234567890"`), that text would also be rewritten.

**Practical likelihood**: Low for UUID-on-UUID collision, but moderate for GUIDs appearing in descriptive text.

**Recommendation**: Consider restricting replacements to known reference attributes/elements (e.g., `componentId`, `processId`, `connectionId` attributes), or document this as an accepted risk given that:
- Boomi UUIDs are unique across the platform
- The replacement is semantically correct even in text contexts (the dev ID is being remapped everywhere)

---

### M-2: strip-env-config.groovy May Miss Sensitive Elements

**Severity**: Major
**File**: `integration/scripts/strip-env-config.groovy:21-58`

**Currently stripped elements**: `password`, `host`, `url`, `port`, `EncryptedValue`

**Potentially missing elements** (based on Boomi connector configurations):
- `userName` / `username` — database/FTP/SFTP connections store usernames
- `apiKey` / `apiToken` — REST/API connections may store keys in named elements
- `certificate` / `privateKey` — SSL/TLS configuration elements
- `proxyHost` / `proxyPort` / `proxyUser` / `proxyPassword` — proxy configuration
- `accessKey` / `secretKey` — AWS/cloud connections
- `authToken` / `bearerToken` — OAuth/bearer auth tokens
- `connectionString` — JDBC connection strings containing embedded credentials
- `remoteDirectory` / `remoteHost` — FTP/SFTP paths that are environment-specific

**Important context**: The build guide (step 11 in Process C) documents only `password`, `host`, `url`, `port`, `EncryptedValue` as the target elements. So the script matches the spec. But the spec itself may be incomplete.

**Risk**: If a connector type stores credentials in an element not in this list, those credentials would be promoted to the production branch — visible via Process G's diff viewer to anyone with peer review or admin access.

**Recommendation**:
1. Add `userName`, `proxyPassword`, `proxyHost`, `proxyPort` at minimum
2. Consider a whitelist approach instead of blacklist: rather than stripping known-bad elements, strip ALL elements inside `<connectionSettings>` or similar container elements, preserving only structural/reference elements
3. Alternatively, document that this script is specifically designed for the known connector types in use and must be updated when new connector types are introduced

---

### M-3: sort-by-dependency.groovy Has Incomplete Type Coverage

**Severity**: Major
**File**: `integration/scripts/sort-by-dependency.groovy:9-18`

```groovy
def typePriority = { String type, String componentId, String rootId ->
    type = type?.toLowerCase() ?: ''
    if (type.contains('profile')) return 1
    if (type == 'connection') return 2
    if (type.contains('operation')) return 3
    if (type == 'map') return 4
    if (type == 'process' && componentId == rootId) return 6
    if (type == 'process') return 5
    return 3  // Default: middle of the pack
}
```

**Issue 1: `type.contains('profile')` is overly broad**. Any component type containing the substring "profile" matches priority 1. If Boomi ever introduces a type like "profileconnection" or "operationprofile", it would match incorrectly. Use exact match: `type == 'profile'`.

**Issue 2: Missing Boomi component types**. Boomi has additional component types not listed here:
- `processroute` (Process Route) — references processes, should be priority 5
- `flowservice` — references processes, profiles, operations
- `certificate` — environment-specific, similar to connections
- `crossreference` — lookup tables, no internal references, should be priority 1
- `customlibrary` — shared libraries, should be priority 1

These would all fall to the default priority 3 (same as operations), which may not be correct. For example, `processroute` references processes and should come after them, not before.

**Issue 3: Default priority 3 is risky**. Unknown types get the same priority as operations. If a new type has dependencies on other types, it could be promoted in the wrong order, causing reference rewriting to fail.

**Recommendation**: Use exact type matching and add a warning log for unknown types:
```groovy
default:
    logger.warning("Unknown component type '${type}' — using default priority 3")
    return 3
```

---

### M-4: validate-connection-mappings.groovy Lacks Logger

**Severity**: Major
**File**: `integration/scripts/validate-connection-mappings.groovy`

**Problem**: This is the only script that does not call `ExecutionUtil.getBaseLogger()`. There is no logging of:
- How many connections were found
- Which connections had mappings vs. which were missing
- The total component count before/after filtering

Compare with every other script which logs detailed diagnostic information.

**Impact**: When debugging promotion failures caused by missing connection mappings, there would be no Process Reporting entries from this script. The DPPs (`missingConnectionMappings`, etc.) provide the data, but without log entries, operators cannot see the script's decision-making in the execution log.

**Recommendation**: Add logger and diagnostic logging:
```groovy
def logger = ExecutionUtil.getBaseLogger()
logger.info("Validating ${connections.size()} connections against mapping cache")
connections.each { conn ->
    logger.info("  Connection ${conn.name} (${conn.devComponentId}): ${connCache.containsKey(conn.devComponentId) ? 'MAPPED' : 'MISSING'}")
}
logger.info("Connection validation: ${missingMappings.size()} missing, ${connections.size() - missingMappings.size()} mapped")
```

---

## Minor Findings

### m-1: build-visited-set.groovy Uses `logger.warning()` Instead of `logger.severe()`

**Severity**: Minor
**File**: `integration/scripts/build-visited-set.groovy:56`

```groovy
} catch (Exception e) {
    logger.warning("Could not parse ComponentReference XML: ${e.message}")
}
```

**Issue**: The `groovy-standards.md` specifies `logger.severe()` for error logging. A failed XML parse in the BFS traversal is significant — it means the component's dependencies are unknown and will be silently skipped.

**Impact**: The BFS continues but may miss dependent components. The warning level may not surface in Process Reporting filters set to SEVERE/ERROR.

**Recommendation**: Use `logger.severe()` and also consider setting a DPP flag (e.g., `parseErrors`) to let the response builder report partial dependency resolution.

---

### m-2: build-visited-set.groovy Silently Swallows XML Parse Errors

**Severity**: Minor
**File**: `integration/scripts/build-visited-set.groovy:55-57`

```groovy
} catch (Exception e) {
    logger.warning("Could not parse ComponentReference XML: ${e.message}")
}
```

**Related to m-1**: When the XML parse fails, the script logs a warning but **continues execution normally**. The component is added to the visited set (line 38), but its children are never discovered. This means:
- The component itself will be included in the dependency tree
- Any components it references will be **missing** from the dependency tree
- Downstream Process C will promote an incomplete set of components
- Reference rewriting will fail for the missing components, creating broken references in prod

**Recommendation**: At minimum, set a DPP flag indicating partial traversal. Ideally, re-throw the exception so the Process B Try/Catch (build guide step 8) can mark this component's traversal as `"ERROR"`.

---

### m-3: normalize-xml.groovy Does Not Sort Attributes

**Severity**: Minor
**File**: `integration/scripts/normalize-xml.groovy:12` (header comment) vs actual behavior

The header comment at line 18 states: "Normalized XML with consistent indentation (2-space indent, **sorted attributes**)". However, `XmlUtil.serialize()` does NOT guarantee attribute sorting. The Groovy `XmlUtil.serialize()` method preserves the order attributes appear in the parsed tree, which may or may not match the source order.

**Impact**: If the Boomi Platform API returns attributes in different orders between the branch and main versions, the diff viewer would show false positives on attribute reordering — exactly what normalization is supposed to prevent.

**Recommendation**: Either:
1. Remove "sorted attributes" from the comment (accurately document actual behavior), or
2. Implement actual attribute sorting using a custom serializer or SAX-based approach (significant complexity)

Given that Boomi's API typically returns attributes in a consistent order for the same component type, this is low-risk in practice.

---

### m-4: sort-by-dependency.groovy Uses Groovy `sort()` — Not Guaranteed Stable in All Groovy Versions

**Severity**: Minor
**File**: `integration/scripts/sort-by-dependency.groovy:30`

```groovy
components.sort { a, b -> ... }
```

**Issue**: Groovy's `List.sort()` with a closure uses `Collections.sort()` under the hood, which is stable in Java 8+ (TimSort). Boomi's runtime uses Java 8+, so this is stable in practice. However, the sort is **in-place** (`sort()` without `false` as first argument), which modifies the original list.

**Impact**: Negligible. In-place sort is actually correct here since the script immediately serializes the result. Stability matters if two components of the same type need to preserve their original order — which they do (e.g., two profiles should stay in the order they were discovered by BFS).

**Recommendation**: No action needed. Document that stability is relied upon for same-priority components.

---

### m-5: Inconsistent Stream Handling — getText() Loads Entire Document into Memory

**Severity**: Minor
**Files**: All 6 scripts

Every script calls `is.getText("UTF-8")` (or `is.text`) to load the entire document into a String:
- `build-visited-set.groovy:13`
- `sort-by-dependency.groovy:24`
- `strip-env-config.groovy:14`
- `validate-connection-mappings.groovy:26`
- `rewrite-references.groovy:13`
- `normalize-xml.groovy:29`

**Issue**: For very large component XML documents (e.g., a complex process with hundreds of shapes), this loads the entire document into memory as a Java String. In the Boomi sandbox environment with limited memory, processing multiple large documents simultaneously could cause `OutOfMemoryError`.

**Risk**: Low in practice. Boomi component XML documents are typically 10-500KB. The Boomi sandbox typically allows 256MB-1GB of heap. But if a batch contains 50+ large documents, memory pressure could be significant.

**Recommendation**: No immediate action. For the current use case (promoting individual components one at a time in Process C's loop), memory usage is bounded. Document this as a scalability consideration if the system is ever extended to bulk-promote hundreds of components in a single request.

---

## Observations

### O-1: DPP Persistence Flags Are Correctly Set to `false`

All scripts use `ExecutionUtil.setDynamicProcessProperty(..., false)` for their DPPs. This matches the `groovy-standards.md` guidance: "Default to `false` for most DPPs." None of the DPPs in these scripts need to survive process execution boundaries.

### O-2: No Sandbox Violations Detected

None of the 6 scripts use:
- Network access (HTTP, sockets)
- File system I/O
- External libraries
- Reflection or classloader manipulation
- Thread creation

All imports are from standard Groovy and Boomi APIs. Full compliance with sandbox limitations.

### O-3: Good Use of Pattern.quote() in rewrite-references.groovy

Line 29: `xmlContent.replaceAll(Pattern.quote(devId), prodId)` correctly escapes the dev ID for regex use. Without `Pattern.quote()`, a UUID containing special regex characters (unlikely but defensive) could cause regex failures.

However, note that `prodId` is used as the replacement string, which could theoretically contain `$` characters that `replaceAll()` interprets as backreferences. UUIDs don't contain `$`, so this is safe, but `Matcher.quoteReplacement(prodId)` would be maximally defensive.

### O-4: XmlSlurper Namespace Handling Is Correct

Scripts that parse XML use `new XmlSlurper(false, false)` — disabling both validation and namespace awareness. This is correct for Boomi component XML, which uses custom namespaces that would require explicit namespace configuration. The non-namespace-aware parser handles all element names as simple strings.

### O-5: normalize-xml.groovy Has Best Error Handling Pattern

This script (lines 31-63) demonstrates the ideal pattern:
1. Null/empty input check with early return
2. Try/catch around parsing
3. `logger.severe()` on failure
4. Graceful fallback (pass through original content)

This pattern should be replicated in all other scripts.

---

## Multi-Environment Assessment

### DPP Lifecycle and Ordering

**Concern**: Process C runs these scripts in sequence: `sort-by-dependency.groovy` -> `validate-connection-mappings.groovy` -> (per-component loop) -> `strip-env-config.groovy` -> `rewrite-references.groovy`. The `componentMappingCache` DPP flows through this chain:

1. Initialized as `{}` in step 6 (Set Properties)
2. **But wait** — step 6 reinitializes to `{}`, which would **overwrite** the connection mappings written by `validate-connection-mappings.groovy` in step 5.6

**Potential bug**: According to build guide step 6: "DPP `componentMappingCache` = `{}`". But step 5.6 (`validate-connection-mappings.groovy`) writes connection mappings into `componentMappingCache`. If step 6 runs **after** step 5.6 and resets the cache to `{}`, all pre-loaded connection mappings are lost, and `rewrite-references.groovy` will fail to rewrite connection references.

**Resolution needed**: Either (a) step 6 should NOT reset `componentMappingCache` (it should only be initialized before step 5.6), or (b) the build guide ordering is: init cache -> sort -> batch query connections -> validate connections (which writes to cache) -> step 6 should be removed or moved before 5.6. The build guide text suggests step 6 happens after 5.7's YES branch, which would indeed destroy the connection mapping data.

**This is likely a build guide sequencing error, not a script error.** The scripts themselves are correct — the issue is in the Process C canvas orchestration.

### Cross-Script Data Contract

The JSON structure flowing between scripts is implicit — there is no schema validation:
- `sort-by-dependency.groovy` expects: `[{type, devComponentId, name, ...}]`
- `validate-connection-mappings.groovy` expects: `[{type, devComponentId, name, ...}]`

If an upstream process changes the JSON structure, these scripts would fail with cryptic Groovy errors. Adding a lightweight schema check (e.g., verify required fields exist) would improve debuggability.

---

## Summary Table

| ID | Severity | Script | Issue |
|----|----------|--------|-------|
| C-1 | Critical | 4 scripts | Missing top-level try/catch per groovy-standards.md |
| C-2 | Critical | validate-connection-mappings.groovy | Only processes first document; drops subsequent documents |
| C-3 | Critical | build-visited-set.groovy | No max depth/component count limit on BFS traversal |
| M-1 | Major | rewrite-references.groovy | Global string replacement has partial GUID match risk in text/comments |
| M-2 | Major | strip-env-config.groovy | Potentially incomplete list of sensitive elements |
| M-3 | Major | sort-by-dependency.groovy | Incomplete type coverage; overly broad `contains('profile')` match |
| M-4 | Major | validate-connection-mappings.groovy | No logger — zero diagnostic logging |
| m-1 | Minor | build-visited-set.groovy | `logger.warning()` should be `logger.severe()` |
| m-2 | Minor | build-visited-set.groovy | XML parse errors silently swallowed; dependencies lost |
| m-3 | Minor | normalize-xml.groovy | Comment claims attribute sorting not implemented by XmlUtil.serialize() |
| m-4 | Minor | sort-by-dependency.groovy | Sort stability assumption (valid but undocumented) |
| m-5 | Minor | All scripts | Full document loaded into memory via getText() |

**Multi-Environment Note**: Build guide step 6 may reset `componentMappingCache` after `validate-connection-mappings.groovy` writes to it — potential orchestration bug.

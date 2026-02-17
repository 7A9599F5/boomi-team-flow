# Team 7: Groovy Scripts — Consensus Findings

**Date**: 2026-02-16
**Participants**: Boomi Groovy Expert, Data Transform Architect, Devil's Advocate
**Scope**: All 6 Groovy scripts in `integration/scripts/`

---

## Consensus Summary

| Severity | Count |
|----------|-------|
| Critical | 3 |
| Major | 5 |
| Minor | 7 |
| Observations | 5 |

---

## Critical Findings (Must Fix Before Go-Live)

### CRIT-1: Missing Top-Level Try/Catch in 5 of 6 Scripts

**Sources**: Expert C-1, Architect MAJ-4, DA confirmed
**Agreement**: All three reviewers agree this is a standards violation with production impact.

**Files affected**:
- `integration/scripts/build-visited-set.groovy` — partial try/catch only around XML parsing (lines 43-57)
- `integration/scripts/sort-by-dependency.groovy` — no try/catch anywhere
- `integration/scripts/strip-env-config.groovy` — no try/catch anywhere
- `integration/scripts/validate-connection-mappings.groovy` — no try/catch anywhere
- `integration/scripts/rewrite-references.groovy` — no try/catch anywhere

**Only compliant script**: `normalize-xml.groovy` (lines 37-63) — proper try/catch with `logger.severe()` and graceful fallback.

**Impact**: Any unhandled exception (malformed JSON DPP, null stream, corrupt XML) produces a generic "Data Process shape failed" error in Process Reporting with no diagnostic context. Operators cannot identify which script failed or why, increasing MTTR in production.

**Remediation**: Wrap each script body in:
```groovy
try {
    // existing script body
} catch (Exception e) {
    logger.severe("script-name.groovy failed: ${e.message}")
    throw new Exception("script-name failed: ${e.message}")
}
```

---

### CRIT-2: strip-env-config.groovy Strips Elements by Name at Any XML Depth — Silent Data Corruption Risk

**Sources**: Architect CRIT-1, Expert M-2 (upgraded by DA)
**Agreement**: Architect and DA agree at Critical. Expert rated Major but acknowledged the scope issue.

**File**: `integration/scripts/strip-env-config.groovy:21-57`

**Issue**: `root.depthFirst().findAll { it.name() == 'password' }` (and similarly for `host`, `url`, `port`, `EncryptedValue`) matches ANY element with these names at ANY depth in the component XML tree, regardless of context.

**Key context verified by DA**: Connections are filtered out at Process C step 5.6 before this script runs (step 11). So this script operates on operations, maps, profiles, and processes only. Operations DO have legitimate `host`/`url`/`port` elements that SHOULD be stripped. But Process Property components with properties named "host" or "url" would have their values silently emptied — corrupting the component.

**DA counter-evidence**: Profile field definitions use attribute-based naming (`<element name="url" type="string"/>`), so `it.name() == 'url'` would NOT match them. This narrows the practical risk but does not eliminate it.

**Remediation** (recommended):
```groovy
String componentType = ExecutionUtil.getDynamicProcessProperty("currentComponentType")
def stripTargetTypes = ['process', 'operation']
if (!stripTargetTypes.contains(componentType?.toLowerCase())) {
    logger.info("Skipping env config strip for type: ${componentType}")
    dataContext.storeStream(new ByteArrayInputStream(xmlContent.getBytes("UTF-8")), props)
    continue
}
```

---

### CRIT-3: Build Guide Step 6 Resets componentMappingCache After Connection Mappings Are Loaded

**Sources**: Expert multi-environment note (not elevated), DA new finding
**Agreement**: DA identified and confirmed. Expert noted it but did not flag as a formal finding.

**File**: Build guide `docs/build-guide/10-process-c-execute-promotion.md`, step 6 vs. steps 5.6-5.7

**Issue**: Step 5.6 (`validate-connection-mappings.groovy`, lines 67-69) writes connection mappings into `componentMappingCache`. Step 5.7 YES branch proceeds to step 6. Step 6 says `DPP componentMappingCache = {}`, which would DESTROY all pre-loaded connection mappings.

**Evidence of intent**: Step 5.7 parenthetical says "now only needs non-connection mappings since connection mappings are pre-loaded" — confirming the author did NOT intend step 6 to reset the cache.

**Impact**: If implemented as written, `rewrite-references.groovy` would have no connection mappings, so connection references in promoted components would never be rewritten. This produces components with broken references in production.

**Note**: This is a BUILD GUIDE bug, not a script bug. The scripts themselves are correct.

**Remediation**: Remove the `componentMappingCache = {}` line from step 6 (it was already initialized in the DPP Initialization table at the top of the build guide), or move the initialization to before step 5.5.

---

## Major Findings (Should Fix Before Go-Live)

### MAJ-1: BFS Traversal Has No Component Count Limit

**Sources**: Expert C-3 (downgraded from Critical by DA)
**Agreement**: Expert says Critical, DA says Major. Resolved at Major because Boomi's execution timeout provides a natural backstop.

**File**: `integration/scripts/build-visited-set.groovy`

**DA note**: Expert's claim about circular reference risk through queued-but-not-visited nodes is incorrect — line 50 explicitly checks `!queue.contains(childId)`, preventing duplicate queueing. The BFS IS cycle-safe.

**Remediation**: Add guard after line 38:
```groovy
if (visitedSet.size() > 200) {
    throw new Exception("Dependency traversal exceeded 200 components — possible overly complex dependency tree")
}
```

---

### MAJ-2: rewrite-references.groovy Uses Global String Replacement on XML

**Sources**: Expert M-1, Architect CRIT-2 (downgraded from Critical by DA)
**Agreement**: Expert says Major, Architect says Critical. Resolved at Major because UUID format makes practical risk very low, and the Architect's proposed XML traversal fix introduces its own problems.

**File**: `integration/scripts/rewrite-references.groovy:27-29`

**Risks**: GUIDs in comments/CDATA could be rewritten (low probability). `prodId` not escaped for regex backreferences (safe for UUIDs but not maximally defensive).

**DA challenge to Architect's fix**: (1) XML traversal with exact text match would miss compound references (comma-separated IDs in attributes). (2) XmlSlurper round-trip changes whitespace/attribute order, which matters for API compatibility. (3) Double-rewriting requires identical v4 UUIDs across accounts — probability ~1/2^122.

**Consensus**: Keep string-based approach. Add `Matcher.quoteReplacement()`:
```groovy
xmlContent = xmlContent.replaceAll(Pattern.quote(devId), java.util.regex.Matcher.quoteReplacement(prodId))
```

Document the trade-off in code comments.

---

### MAJ-3: validate-connection-mappings.groovy Single-Document Pattern and Missing Logger

**Sources**: Expert C-2 (downgraded from Critical by DA), Expert M-4, Architect MAJ-3
**Agreement**: Expert says Critical for single-doc, DA says Major because pipeline guarantees single document input. All agree on missing logger.

**File**: `integration/scripts/validate-connection-mappings.groovy:25-26, 72-75`

**Issues**:
1. `dataContext.getStream(0)` instead of multi-document loop — fragile but not a bug given pipeline guarantees
2. `new Properties()` at line 74 discards document-level metadata
3. No `ExecutionUtil.getBaseLogger()` — only script without logging

**Remediation**:
```groovy
def logger = ExecutionUtil.getBaseLogger()

if (dataContext.getDataCount() > 1) {
    logger.warning("Expected 1 document, received ${dataContext.getDataCount()}")
}
def is = dataContext.getStream(0)
Properties props = dataContext.getProperties(0)
// ... existing logic ...
logger.info("Validating ${connections.size()} connections, ${nonConnections.size()} non-connections")
logger.info("Connection validation: ${missingMappings.size()} missing, ${connections.size() - missingMappings.size()} mapped")
// ...
dataContext.storeStream(
    new ByteArrayInputStream(JsonOutput.toJson(nonConnections).getBytes("UTF-8")),
    props  // Preserve original properties
)
```

---

### MAJ-4: sort-by-dependency.groovy Has Incomplete Type Coverage and Unsafe Default

**Sources**: Expert M-3, Architect MAJ-2
**Agreement**: Both reviewers agree at Major. DA confirms.

**File**: `integration/scripts/sort-by-dependency.groovy:9-18`

**Issues**:
1. `type.contains('profile')` (line 11) and `type.contains('operation')` (line 13) are overly broad substring matches
2. Missing types: `processroute` (should be priority 5), `certificate` (priority 2), `crossreference`/`customlibrary` (priority 1)
3. Default priority 3 (line 17) is unsafe — unknown types that depend on connections could be promoted too early
4. No warning logged for unknown types

**Consensus remediation**: Change default from 3 to 5 (conservative — unknown types promoted later). Add `processroute` and warning logging:
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
    return 5
}
```

---

### MAJ-5: BFS Visited Set Uses O(n) ArrayList Instead of Map

**Sources**: Architect MAJ-1
**Agreement**: DA confirms. Practical performance impact is near-zero (API latency dominates), but the fix is trivial.

**File**: `integration/scripts/build-visited-set.groovy:17, 33, 50`

**Issue**: `def visitedSet = []` creates an ArrayList. Each `contains()` check at lines 33 and 50 is O(n). For a tree of n components, total lookup operations are O(n^2).

**Remediation**: Use JSON object for O(1) key lookup:
```groovy
def visitedSet = [:]  // Map: componentId -> true
if (visitedJson && visitedJson.trim()) {
    visitedSet = new JsonSlurper().parseText(visitedJson)
}
// Change contains() to containsKey():
if (visitedSet.containsKey(currentId)) { ... }
// Change add to:
visitedSet[currentId] = true
```

Note: Queue should remain as ArrayList (FIFO ordering required for BFS).

---

## Minor Findings

### MIN-1: build-visited-set.groovy Uses warning() Instead of severe() for Parse Errors

**Sources**: Expert m-1
**File**: `integration/scripts/build-visited-set.groovy:56`
**Fix**: Change `logger.warning()` to `logger.severe()` per groovy-standards.md.

### MIN-2: build-visited-set.groovy Silently Swallows XML Parse Errors

**Sources**: Expert m-2
**File**: `integration/scripts/build-visited-set.groovy:55-57`
**Impact**: Component added to visited set but its children never discovered. Downstream promotion may have incomplete dependency tree.
**Fix**: Set DPP flag `traversalPartial = "true"` on parse failure to surface in Process B response.

### MIN-3: normalize-xml.groovy Comment Claims Attribute Sorting Not Implemented

**Sources**: Expert m-3, Architect MIN-1
**File**: `integration/scripts/normalize-xml.groovy:17`
**Fix**: Remove "sorted attributes" from the docstring. `XmlUtil.serialize()` does not sort attributes.

### MIN-4: strip-env-config.groovy replaceBody('') May Produce Empty Required Elements

**Sources**: Architect MAJ-5 (downgraded by DA)
**File**: `integration/scripts/strip-env-config.groovy:23, 29, 35, 41, 47`
**DA note**: Boomi's Platform API accepts empty elements. Connections are filtered out before this script runs, reducing risk. No immediate action needed; document as known behavior.

### MIN-5: rewrite-references.groovy Does Not Validate Mapping Cache Format

**Sources**: Architect MIN-2
**File**: `integration/scripts/rewrite-references.groovy:16-20`
**Fix**: Subsumed by CRIT-1 (top-level try/catch will catch malformed JSON). No separate fix needed.

### MIN-6: build-visited-set.groovy Extracts Both componentId and referenceComponentId

**Sources**: Architect MIN-4
**File**: `integration/scripts/build-visited-set.groovy:48`
**Fix**: Verify against Boomi ComponentReference API which field contains child IDs. If only `referenceComponentId`, restrict extraction.

### MIN-7: normalize-xml.groovy Empty Input Handling Inconsistent with Error Path

**Sources**: Architect MIN-5
**File**: `integration/scripts/normalize-xml.groovy:31-35`
**Fix**: Cosmetic inconsistency. Both behaviors (empty output vs. raw passthrough) are acceptable for the diff viewer. No action needed.

---

## Observations (No Action Needed)

### OBS-1: DPP Persistence Flags Correctly Set to false
All scripts use `false` for DPP persistence. Compliant with groovy-standards.md.

### OBS-2: No Sandbox Violations
No network access, no file I/O, no external libraries, no thread creation. Full sandbox compliance across all 6 scripts.

### OBS-3: Script Separation of Concerns is Well-Designed
Each script has a single responsibility with clear DPP-based input/output contracts. The pipeline is modular and easy to reason about.

### OBS-4: rewrite-references.groovy is Not Idempotent
Safe only because Process C guarantees single-pass execution per component. If retry logic is ever added, double-rewriting could occur (devId A -> prodId B, where prodId B matches another devId C -> prodId D). Document this constraint in code comments.

### OBS-5: normalize-xml.groovy Demonstrates Best-Practice Error Handling
Lines 37-63: try/catch, logger.severe(), graceful fallback (pass through original content). This pattern should be replicated in all other scripts as part of the CRIT-1 remediation.

---

## Areas of Agreement (All Three Reviewers)

1. **Try/catch violations** are real and widespread (5 of 6 scripts)
2. **normalize-xml.groovy** is the gold standard for error handling — use as template
3. **validate-connection-mappings.groovy** has the most issues (single-doc, no logger, discarded properties)
4. **DPP persistence flags** are all correctly set to false
5. **No sandbox violations** in any script
6. **Script modularity** and separation of concerns is well-designed
7. **sort-by-dependency.groovy** needs unknown-type handling and missing types added

---

## Unresolved Debates

### Debate 1: String vs. XML Traversal for Reference Rewriting

**Architect position**: Replace string-based rewriting with parsed XML traversal for structural correctness guarantee.

**Expert + DA position**: Keep string-based approach because:
1. XML round-trip changes whitespace and attribute order, affecting API compatibility
2. Compound references (multiple IDs in one attribute) would be missed by exact-match traversal
3. UUID format makes substring collision virtually impossible
4. Original XML structure preservation is important

**Resolution**: Keep string-based approach. Add `Matcher.quoteReplacement()`. Document as accepted trade-off. Revisit if CDATA corruption is ever observed in practice.

### Debate 2: Severity of strip-env-config Depth Stripping

**Expert**: Major (matches spec; spec may be incomplete)
**Architect**: Critical (silent data corruption class)
**DA**: Critical (silent corruption outweighs low probability)

**Resolution**: Critical. The failure mode (silently emptied legitimate values in promoted components, discovered only post-deployment) warrants the highest severity regardless of probability.

### Debate 3: validate-connection-mappings Single-Document Severity

**Expert**: Critical (violates multi-document pattern, drops documents)
**DA**: Major (pipeline guarantees single document; no documents are actually dropped in current architecture)

**Resolution**: Major. The code is fragile and non-standard, but it is not a functional bug given the current pipeline design. Add a guard log for `dataContext.getDataCount() > 1`.

---

## Multi-Environment Assessment

### Script Impact
The Groovy scripts are **environment-agnostic by design**. No script references environment names, deployment targets, or promotion modes. All scripts operate on component XML and DPPs, which are environment-independent. This is architecturally correct.

### Gaps for Multi-Environment
1. **strip-env-config.groovy in TEST mode**: If TEST deployments should preserve some environment config (e.g., test URLs), the current blanket stripping prevents this. The script has no awareness of promotion mode. However, credentials should never be promoted regardless of target, so this is likely acceptable.
2. **DPP cache sizing**: In multi-environment scenarios, `componentMappingCache` accumulates mappings per process execution. Since DPPs reset per execution, there is no cross-environment accumulation risk.
3. **Branch operations**: Scripts do not interact with branch operations directly — that is controlled by the Process C canvas. No script changes needed for multi-environment.

### Assessment
No script modifications required for multi-environment support. The one consideration (strip-env-config mode awareness) is an acceptable limitation since credentials should be stripped in all environments.

---

## Priority-Ordered Remediation Plan

| Priority | ID | Effort | Description |
|----------|----|--------|-------------|
| P1 | CRIT-1 | Low | Add try/catch to all 5 non-compliant scripts |
| P1 | CRIT-2 | Low | Add component-type guard to strip-env-config.groovy |
| P1 | CRIT-3 | Low | Fix build guide step 6 cache reset sequencing |
| P2 | MAJ-1 | Low | Add 200-component limit guard to BFS |
| P2 | MAJ-2 | Low | Add Matcher.quoteReplacement to rewrite-references |
| P2 | MAJ-3 | Low | Fix validate-connection-mappings: add logger, guard, preserve Properties |
| P2 | MAJ-4 | Low | Add processroute type, change default to 5, add warning logging |
| P2 | MAJ-5 | Low | Convert BFS visited set from array to object |
| P3 | MIN-1-7 | Low | Assorted minor fixes |

**Total effort**: All P1-P2 fixes are small changes (1-15 lines each). No architectural rework needed. The scripts are fundamentally sound — they need hardening and edge-case protection, not redesign.

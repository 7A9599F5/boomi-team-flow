# Team 7: Devil's Advocate Response — Groovy Scripts

**Date**: 2026-02-16
**Role**: Devil's Advocate (independent source-code verification)
**Scope**: Verify all claims from Expert and Architect against the 6 Groovy source files

---

## Methodology

I read all 6 scripts line-by-line and cross-referenced every claim made by the Expert and Architect, checking exact line numbers, code patterns, and severity justifications. I also read the Process C build guide (`docs/build-guide/10-process-c-execute-promotion.md`) to verify orchestration claims.

---

## Expert Findings Verification

### C-1: Missing Top-Level Try/Catch in 4+ Scripts — CONFIRMED

Verified line-by-line:

| Script | try/catch? | Expert's claim | Verified? |
|--------|-----------|----------------|-----------|
| `build-visited-set.groovy` | Partial — lines 43-57 only (XML parsing) | Partial | YES |
| `sort-by-dependency.groovy` | None anywhere in file | None | YES |
| `strip-env-config.groovy` | None anywhere in file | None | YES |
| `validate-connection-mappings.groovy` | None anywhere in file | None | YES |
| `rewrite-references.groovy` | None anywhere in file | Expert initially says "no explicit try/catch but safe", then note at line 34 acknowledges the gap | YES — Expert is correct that this script ALSO lacks try/catch |
| `normalize-xml.groovy` | Lines 37-63, full coverage | Compliant | YES |

**Result: 5 of 6 scripts lack top-level try/catch, not 4.** Expert initially said 4 but then noted `rewrite-references.groovy` also lacks it. The count should be 5.

**Severity challenge**: Should this be Critical or Major? Boomi wraps Data Process shapes in its own exception handler — unhandled exceptions surface as "Data Process shape failed" in Process Reporting. The process DOES fail, it just lacks diagnostic context. I lean toward **Critical** because groovy-standards.md explicitly mandates this pattern and because poor diagnostics in production cause extended MTTR (mean time to resolve).

**Verdict: CONFIRMED at Critical.** Count is 5, not 4.

---

### C-2: validate-connection-mappings.groovy Single-Document Issue — CONFIRMED, CHALLENGE SEVERITY

Verified: Line 25 `def is = dataContext.getStream(0)` — confirmed hardcoded to index 0.
Verified: Line 74 `new Properties()` — confirmed creates empty properties, discards originals.

**Severity challenge**: The build guide step 5.6 explicitly states input is "the sorted components array from step 5". Step 5 (`sort-by-dependency.groovy`, line 42) outputs one document per input document via the standard for-loop. In the Process C canvas, components arrive as a single JSON array document. So `dataContext.getDataCount()` will be 1 in normal operation.

The script was designed for single-document input and the pipeline guarantees it. The only failure scenario requires misconfigured Boomi canvas (e.g., inserting a Splitter shape).

**Verdict: DOWNGRADE to Major.** The code is fragile and violates the multi-document pattern (a standards issue), but it is not a functional bug in the current architecture. The `new Properties()` issue at line 74 is a separate, real problem that should be fixed.

---

### C-3: BFS No Max Depth — CONFIRMED WITH NUANCE

Verified: Line 33 checks `visitedSet.contains(currentId)` — prevents revisiting.
Verified: Line 50 checks `!visitedSet.contains(childId) && !queue.contains(childId)` — prevents duplicate queueing.

**Challenge on circular references**: Expert claims at line 95-96 that "if the API returns a reference to a component that references back to an already-queued (but not yet visited) component, both could end up in the queue simultaneously." This is INCORRECT. Line 50 explicitly checks `!queue.contains(childId)`. If a child is already in the queue, it will NOT be added again. The BFS is cycle-safe for any graph structure.

**Challenge on severity**: Boomi processes have execution time limits (5-30 minutes depending on plan). A runaway BFS of 500 components at 200ms per API call = 100 seconds — well within limits. The timeout provides a natural backstop. This is a hardening improvement, not a Critical gap.

**Verdict: DOWNGRADE to Major.** Recommend a 200-component guard.

---

### M-1: rewrite-references.groovy Partial GUID Match Risk — CONFIRMED at Major

Verified: Lines 27-29 do global `replaceAll` on entire XML string. Expert correctly identifies comment/CDATA/text risk scenarios.

Expert's Observation O-3 notes `Matcher.quoteReplacement()` is not used for `prodId`. This is a valid one-line improvement. UUIDs cannot contain `$` or `\`, so current code is safe, but defense-in-depth is cheap.

**Verdict: CONFIRMED at Major.**

---

### M-2: strip-env-config.groovy Incomplete Element Coverage — CONFIRMED with QUALIFICATION

Verified: Lines 21-57 strip only `password`, `host`, `url`, `port`, `EncryptedValue`.

**Qualification**: Expert says spec may be incomplete and lists `userName`, `apiKey`, `bearerToken`, etc. However, Boomi typically stores API keys and tokens as `EncryptedValue` elements internally. The `EncryptedValue` catch-all covers most credential types. The gap is primarily `userName`/`username` which is stored as a plain-text element in database/FTP connector XML.

The Architect's CRIT-1 (unbounded depth stripping) is a more significant problem than missing element names.

**Verdict: CONFIRMED at Major.**

---

### M-3: sort-by-dependency.groovy Incomplete Types — CONFIRMED at Major

Verified lines 9-18:
- Line 11: `type.contains('profile')` — intentionally broad for `xmlprofile`, `jsonprofile`, etc. But would also match hypothetical types containing "profile" substring.
- Line 13: `type.contains('operation')` — same broad matching.
- Line 17: `return 3` default — no warning logged for unknown types.
- Missing: `processroute` (should be priority 5), `certificate`, `crossreference`, `customlibrary`.

**Verdict: CONFIRMED at Major.** Both Expert and Architect agree.

---

### M-4: validate-connection-mappings.groovy Lacks Logger — CONFIRMED at Major

Verified: No `ExecutionUtil.getBaseLogger()` call anywhere in the script. Compare with every other script: `build-visited-set.groovy:7`, `sort-by-dependency.groovy:6`, `strip-env-config.groovy:8`, `rewrite-references.groovy:7`, `normalize-xml.groovy:7`.

**Verdict: CONFIRMED at Major.** Clear omission.

---

### Minor Findings — ALL CONFIRMED

- **m-1**: Line 56 `logger.warning()` — confirmed. Standard mandates `logger.severe()`.
- **m-2**: Lines 55-57 catch-and-continue — confirmed. Component's children silently lost from dependency tree.
- **m-3**: Line 17 docstring claims "sorted attributes" — confirmed. `XmlUtil.serialize()` does NOT sort attributes.
- **m-4**: Line 30 `components.sort { ... }` — confirmed in-place. TimSort stability in Java 8+ is guaranteed.
- **m-5**: All scripts use `getText("UTF-8")` or `.text` — confirmed at stated locations.

---

## Architect Findings Verification

### CRIT-1: strip-env-config.groovy Depth-First Stripping — CONFIRMED, AGREE at CRITICAL

Verified: Lines 21, 29, 37, 45, 53 all use `root.depthFirst().findAll { it.name() == '...' }`. This matches ANY element with these names at ANY depth.

**Key verification against build guide**: Step 11 runs on "component XML from step 10", and step 5.6 filters out connections. So this script runs on operations, maps, profiles, and processes — NOT connections.

**Cross-check**: Operations DO contain `host`, `url`, `port` elements in their configuration sections. These ARE environment-specific and SHOULD be stripped. But a Map component with a profile field named "url" could be a false positive.

**Counter-evidence**: Profile field definitions in Boomi use attribute-based naming: `<element name="url" type="string"/>`. The element NAME here is `element`, not `url`. So `it.name() == 'url'` would NOT match profile field definitions. This reduces the practical scope of the Architect's concern.

However: Process Property components CAN have properties named "host" or "url" represented as XML elements. Stripping these would corrupt the component.

**Verdict: CONFIRMED at Critical.** Silent data corruption risk is the most dangerous class of defect in a promotion pipeline. Even if the practical frequency is low, the impact when it occurs (broken production components discovered post-merge) is severe.

---

### CRIT-2: rewrite-references.groovy String Replacement — CHALLENGE, DOWNGRADE to Major

The Architect upgrades from Expert's Major to Critical and proposes XML traversal as a fix.

**Challenges to the Architect's proposed fix**:
1. The suggested `if (text && mappingCache.containsKey(text.trim()))` only matches when the ENTIRE text of an element is a single component ID. Boomi component XML can contain compound references (e.g., comma-separated IDs in configuration attributes). The string approach handles these; the XML approach does not.
2. XmlSlurper parse + XmlUtil serialize changes whitespace, attribute ordering, and namespace declarations. The modified XML is sent back to the Platform API, and preserving the original structure is important for API compatibility.
3. The Architect's "Problem 3" (double-rewriting via transitive prod-to-dev matches) requires two independently generated v4 UUIDs to be identical. This probability is 1 in 2^122, effectively zero.

**Verdict: DOWNGRADE to Major.** The string approach is a pragmatic trade-off. Add `Matcher.quoteReplacement()` for defense-in-depth.

---

### MAJ-1: BFS O(n) Visited Set — CONFIRMED at Major

Verified: Line 17 `def visitedSet = []` is ArrayList. Lines 33, 50 use `.contains()` which is O(n).

The Architect's recommendation to use JSON object (map) for O(1) lookup is simple and correct. The practical performance impact is near-zero (API latency dominates), but the fix is trivial and improves algorithmic correctness.

**Verdict: CONFIRMED at Major.** Trivial fix, do it.

---

### MAJ-2: sort-by-dependency.groovy Default Priority — CONFIRMED, DUPLICATE of Expert M-3

Both reviewers agree. The Architect adds depth on `processroute` type. The recommendation to default to priority 5 (conservative/later) instead of 3 is better than the Expert's keep-3-with-warning approach.

**Verdict: CONFIRMED at Major.**

---

### MAJ-3: validate-connection-mappings.groovy Properties — CONFIRMED, SUBSET of Expert C-2

Line 74 `new Properties()` confirmed. Duplicate finding.

**Verdict: CONFIRMED at Major** (merged with CRIT-2 in consensus).

---

### MAJ-4: Missing Try/Catch — DUPLICATE of Expert C-1

Already verified.

---

### MAJ-5: replaceBody('') Invalid XML — CHALLENGE, DOWNGRADE to Minor

The Architect claims `replaceBody('')` could produce invalid XML for required elements.

**Counter-evidence**:
1. Boomi's Platform API UPDATE endpoint does NOT enforce XML schema validation on component XML bodies during updates. It stores what it receives.
2. Empty `<password></password>` is functionally equivalent to "no password" in Boomi's UI. This is standard behavior.
3. Connections (the primary target of password/EncryptedValue elements) are filtered out at step 5.6 before this script runs.

**Verdict: DOWNGRADE to Minor.** The empty-element approach is correct for Boomi.

---

### Architect Minor Findings — ALL CONFIRMED

- **MIN-1**: Duplicate of Expert m-3 (normalize-xml attribute sorting). Confirmed.
- **MIN-2**: rewrite-references.groovy no cache validation. Lines 16-20 confirmed. Valid Minor, subsumed by try/catch fix.
- **MIN-3**: Duplicate of Expert M-3 (broad `contains`). Confirmed.
- **MIN-4**: build-visited-set.groovy line 48 extracts both `componentId` and `referenceComponentId`. Confirmed. The visited-set/queue dedup prevents functional issues, but extracting only `referenceComponentId` would be cleaner.
- **MIN-5**: normalize-xml.groovy empty input handling (lines 31-35). Confirmed. Cosmetic inconsistency.

---

## Build Guide Orchestration Bug — NEW FINDING

**Source**: Expert raised as "Multi-Environment Note" but did not elevate to a finding.

**Issue**: Build guide step 6 says `DPP componentMappingCache = {}`. Step 5.6 (`validate-connection-mappings.groovy`) writes connection mappings INTO `componentMappingCache` (lines 67-69). Step 5.7 YES branch proceeds to step 6. Step 6 would RESET the cache to `{}`, destroying all pre-loaded connection mappings.

**Verification**: Read the build guide section for step 5.7: "YES branch: continue to step 6 (Initialize Mapping Cache — now only needs non-connection mappings since connection mappings are pre-loaded)". The parenthetical REVEALS THE INTENT — step 6 should NOT reset the cache. But the instruction "DPP `componentMappingCache` = `{}`" contradicts this.

**Verdict: CRITICAL build guide bug.** Not a script bug. If an implementer follows step 6 literally, connection references will never be rewritten, causing broken components in production.

**Fix**: Remove the `componentMappingCache = {}` line from step 6, or move it before step 5.5.

---

## Consensus Severity Recommendations

| Finding | Expert | Architect | DA Verdict |
|---------|--------|-----------|------------|
| Try/catch violations (5 scripts) | Critical | Major | **Critical** |
| validate-connection-mappings single-doc + Properties | Critical | Major | **Major** (pipeline guarantees single doc) |
| BFS max depth limit | Critical | Not raised | **Major** (timeout backstop) |
| strip-env-config depth-first scope | Major | Critical | **Critical** (silent corruption) |
| rewrite-references string replacement | Major | Critical | **Major** (GUID format mitigates) |
| BFS O(n) visited set | Not raised | Major | **Major** (trivial fix) |
| sort-by-dependency unknown types | Major | Major | **Major** |
| validate-connection-mappings no logger | Major | Not raised | **Major** |
| replaceBody('') validity | Not raised | Major | **Minor** (Boomi accepts empty) |
| Build guide step 6 cache reset | Multi-env note | Not raised | **Critical** (build guide bug) |

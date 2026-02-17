### Process G: Generate Component Diff (`PROMO - Generate Component Diff`)

**Purpose:** Fetch component XML from promotion branch and main branch, normalize both for consistent formatting, return to UI for client-side diff rendering.

**Components Used:**
- HTTP Client Connection: `PROMO - Partner API Connection`
- HTTP Client Operation: `PROMO - HTTP Op - GET Component` (reused — URL parameterized)
- Groovy Script: `normalize-xml.groovy`
- JSON Profile: `PROMO - Profile - GenerateComponentDiffRequest`
- JSON Profile: `PROMO - Profile - GenerateComponentDiffResponse`

**Process Flow:**

1. **Start Shape**
   - Receives JSON request from Flow Service with:
     - `primaryAccountId` (string, required)
     - `branchId` (string, required) — promotion branch ID
     - `prodComponentId` (string, required) — component ID in primary account
     - `componentAction` (string, required) — "CREATE" or "UPDATE"

2. **HTTP Client Send — GET Component (Branch)**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - GET Component`
   - URL: `/partner/api/rest/v1/{1}/Component/{2}~{3}`
   - URL parameters:
     - `{1}` = DPP `primaryAccountId`
     - `{2}` = DPP `prodComponentId`
     - `{3}` = DPP `branchId` (tilde syntax for branch-specific component)
   - Response returns component XML from branch
   - Set DPP `branchXml` from response
   - Set DPP `branchVersion` from response `<version>` element

3. **Data Process — Normalize Branch XML**
   - Script: `normalize-xml.groovy`
   - Input: DPP `branchXml`
   - Output: normalized XML with consistent indentation, attribute ordering, whitespace
   - Set DPP `branchXmlNormalized`

4. **Decision — Component Action**
   - Condition: DPP `componentAction` EQUALS `"UPDATE"`
   - **UPDATE** branch: fetch main version
   - **CREATE** branch: skip main fetch

5. **UPDATE Branch — HTTP Client Send — GET Component (Main)**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - GET Component`
   - URL: `/partner/api/rest/v1/{1}/Component/{2}`
   - URL parameters:
     - `{1}` = DPP `primaryAccountId`
     - `{2}` = DPP `prodComponentId`
   - Response returns component XML from main branch
   - Set DPP `mainXml` from response
   - Set DPP `mainVersion` from response `<version>` element

6. **UPDATE Branch — Data Process — Normalize Main XML**
   - Script: `normalize-xml.groovy`
   - Input: DPP `mainXml`
   - Output: normalized XML
   - Set DPP `mainXmlNormalized`

7. **CREATE Branch — Set Empty Main**
   - Set DPP `mainXmlNormalized` = empty string
   - Set DPP `mainVersion` = 0

8. **Map — Build Response**
   - Response structure:
     ```json
     {
       "success": true,
       "branchXml": "...",
       "mainXml": "...",
       "branchVersion": 5,
       "mainVersion": 4,
       "componentId": "...",
       "componentName": "..."
     }
     ```

9. **Return Document**
   - Returns JSON response to Flow Service

**Key Implementation Notes:**

- **Tilde syntax** `~{branchId}` in the URL is how Boomi Branching addresses branch-specific component versions
- The same HTTP Client Operation can be reused — just parameterize the URL with or without tilde
- `normalize-xml.groovy` ensures consistent formatting so diffs only show real content changes (not whitespace/attribute order differences)
- For CREATE actions, skip the main fetch entirely — there's no existing version to compare

**Error Handling:**

Wrap HTTP Client steps in a **Try/Catch**:
- **Branch fetch failure**: return error with `errorCode = "COMPONENT_NOT_FOUND"`, `errorMessage = "Component not found in branch"`
- **Main fetch failure** (UPDATE only): return error with `errorCode = "COMPONENT_NOT_FOUND"`, `errorMessage = "Component not found in main"`
- **Normalization failure**: return error with `errorCode = "XML_PARSE_ERROR"`, `errorMessage = "Failed to normalize XML"`

**Verify:**

- Test with a component that exists on both branch and main → returns both XMLs, correctly normalized
- Test with a CREATE (new component) → returns `branchXml` and empty `mainXml`, `mainVersion = 0`
- Verify normalized XML has consistent indentation (e.g., 2 spaces per level)
- Verify attributes are alphabetically sorted within each element

---

### Summary: Process Build Order Checklist

Use this checklist to track your progress. Build and verify each process before moving to the next.

| Order | Process | Component Name | FSS Operation | Status |
|-------|---------|---------------|---------------|--------|
| 1 | F | `PROMO - Mapping CRUD` | `PROMO - FSS Op - ManageMappings` | [ ] |
| 2 | A0 | `PROMO - Get Dev Accounts` | `PROMO - FSS Op - GetDevAccounts` | [ ] |
| 3 | E | `PROMO - Query Status` | `PROMO - FSS Op - QueryStatus` | [ ] |
| 4 | E2 | `PROMO - Query Peer Review Queue` | `PROMO - FSS Op - QueryPeerReviewQueue` | [ ] |
| 5 | E3 | `PROMO - Submit Peer Review` | `PROMO - FSS Op - SubmitPeerReview` | [ ] |
| 6 | J | `PROMO - List Integration Packs` | `PROMO - FSS Op - ListIntegrationPacks` | [ ] |
| 7 | G | `PROMO - Generate Component Diff` | `PROMO - FSS Op - GenerateComponentDiff` | [ ] |
| 8 | A | `PROMO - List Dev Packages` | `PROMO - FSS Op - ListDevPackages` | [ ] |
| 9 | B | `PROMO - Resolve Dependencies` | `PROMO - FSS Op - ResolveDependencies` | [ ] |
| 10 | C | `PROMO - Execute Promotion` | `PROMO - FSS Op - ExecutePromotion` | [ ] |
| 11 | D | `PROMO - Package and Deploy` | `PROMO - FSS Op - PackageAndDeploy` | [ ] |

After completing all eleven processes, proceed to Phase 4 to create the Flow Service component that ties them together.

---

---
Prev: [Process J: List Integration Packs](12-process-j-list-integration-packs.md) | Next: [Phase 4: Flow Service Component](14-flow-service.md) | [Back to Index](index.md)

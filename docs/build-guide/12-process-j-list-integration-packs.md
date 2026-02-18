### Process J: List Integration Packs (`PROMO - List Integration Packs`)

> **API Alternative:** This process can be created programmatically via `POST /Component` with `type="process"`. Due to the complexity of process canvas XML (shapes, routing, DPP mappings, script references), the recommended workflow is: (1) build the process manually following the steps below, (2) use `GET /Component/{processId}` to export the XML, (3) store the XML as a template for automated recreation. See [Appendix D: API Automation Guide](22-api-automation-guide.md) for the full workflow.

**Purpose:** Query existing MULTI-type Integration Packs from primary account and suggest the most recently used pack for a given process. Called from **Page 7 (Admin Approval Queue)** where admins select or assign an Integration Pack during the approval and deployment step.

**Components Used:**
- HTTP Client Connection: `PROMO - Partner API Connection`
- HTTP Client Operation: `PROMO - HTTP Op - QUERY IntegrationPack`
- DataHub Operation: `PROMO - DH Op - Query PromotionLog`
- JSON Profile: `PROMO - Profile - ListIntegrationPacksRequest`
- JSON Profile: `PROMO - Profile - ListIntegrationPacksResponse`

**Process Flow:**

1. **Start Shape**
   - Receives JSON request from Flow Service with:
     - `primaryAccountId` (string, required)
     - `suggestForProcess` (string, optional) — process name to suggest pack for
     - `packPurpose` (string, optional) — filter packs: `"TEST"` (packs with "- TEST" suffix), `"PRODUCTION"` (packs without "- TEST" suffix), or `"ALL"` (default, no filter)

2. **HTTP Client Send — QUERY IntegrationPack**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - QUERY IntegrationPack`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - Request body: JSON with filter `installationType = "MULTI"`
   - Response returns array of Integration Packs

3. **Map — Parse IntegrationPack Results**
   - Transform API response into array of pack objects
   - Each pack includes: `id`, `name`, `version`, `installationType`
   - Set DPP `packList` (array)

4. **Decision — Filter by Pack Purpose?**
   - Condition: DPP `packPurpose` IS NOT EMPTY AND NOT `"ALL"`
   - **YES** branch (`"TEST"`): Filter `packList` to only packs whose `name` ends with `" - TEST"`
   - **YES** branch (`"PRODUCTION"`): Filter `packList` to only packs whose `name` does NOT end with `" - TEST"`
   - **NO** branch (empty or `"ALL"`): Keep all packs, skip to step 5

4.5. **Decision — Suggest for Process?**
   - Condition: DPP `suggestForProcess` IS NOT EMPTY
   - **YES** branch: query PromotionLog for suggestion
   - **NO** branch: skip to response

5. **YES Branch — DataHub Query — Query PromotionLog**
   - Connector: `PROMO - DataHub Connection`
   - Operation: `PROMO - DH Op - Query PromotionLog`
   - Filter: `processName = DPP.suggestForProcess AND status = "DEPLOYED"`
   - Order: `promotionTimestamp DESC`
   - Limit: 1
   - Response returns most recent deployed promotion for that process
   - Set DPP `suggestedPackId` and `suggestedPackName` from result
   - If no result, leave suggestion fields empty
   - **Note:** When `packPurpose` is set, the suggestion should come from the matching environment's history (e.g., suggest the most recent TEST pack when `packPurpose = "TEST"`)

6. **Map — Build Response**
   - Combine `packList` array with optional suggestion fields
   - Response structure:
     ```json
     {
       "success": true,
       "packs": [...],
       "suggestedPackId": "...",
       "suggestedPackName": "..."
     }
     ```

7. **Return Document**
   - Returns JSON response to Flow Service

**Error Handling:**

Wrap HTTP Client and DataHub steps in a **Try/Catch**:
- **HTTP failure**: return error with `errorCode = "API_ERROR"`, `errorMessage = "Failed to query Integration Packs"`
- **DataHub failure** (suggestion query): log warning but continue — return pack list without suggestion

**Verify:**

- Test with empty primary account (no packs) → returns `success: true`, empty `packs` array
- Test with existing packs → returns full list with correct `installationType = "MULTI"`
- Test with `suggestForProcess` matching a deployed promotion → returns `suggestedPackId` and `suggestedPackName`
- Test with `suggestForProcess` with no matching promotions → returns pack list without suggestion fields
- Test with `packPurpose = "TEST"` → returns only packs with "- TEST" suffix in name
- Test with `packPurpose = "PRODUCTION"` → returns only packs without "- TEST" suffix
- Test with `packPurpose = "ALL"` or empty → returns all packs (same as no filter)

---

---
Prev: [Process D: Package and Deploy](11-process-d-package-and-deploy.md) | Next: [Process G: Component Diff & Build Order](13-process-g-component-diff.md) | [Back to Index](index.md)

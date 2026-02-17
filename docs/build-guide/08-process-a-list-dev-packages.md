### Process A: List Dev Packages (`PROMO - List Dev Packages`)

This process queries the Boomi Platform API for PackagedComponents in a specified dev account, handles pagination, and enriches each package with its component name.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - ListDevPackagesRequest` | `/integration/profiles/listDevPackages-request.json` |
| `PROMO - Profile - ListDevPackagesResponse` | `/integration/profiles/listDevPackages-response.json` |

The request JSON contains:
- `devAccountId` (string): the dev sub-account to query

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `packages` (array): each entry has `packageId`, `packageVersion`, `componentId`, `componentName`, `componentType`, `createdDate`, `notes`

#### FSS Operation

Create `PROMO - FSS Op - ListDevPackages` per Section 3.B, using `PROMO - Profile - ListDevPackagesRequest` and `PROMO - Profile - ListDevPackagesResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — same pattern as Process F: Operation = `PROMO - FSS Op - ListDevPackages`

2. **Set Properties** (read request fields)
   - DPP `devAccountId` = document path: `devAccountId`

3. **HTTP Client Send — Query PackagedComponents (first page)**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - QUERY PackagedComponent`
   - The operation URL includes `{1}` for account ID. In the operation's Parameters tab, set `{1}` = DPP `primaryAccountId`
   - Add query parameter: `overrideAccount` = DPP `devAccountId`
   - This sends a POST to `/partner/api/rest/v1/{primaryAccountId}/PackagedComponent/query` with `overrideAccount` targeting the dev sub-account
   - The response is XML containing `<PackagedComponent>` elements and optionally a `queryToken` for pagination

4. **Decision — Pagination Check**
   - Check the response XML for a `queryToken` element
   - Condition: document content contains `<queryToken>` (use a Decision shape with document property check, or a preceding Data Process that extracts the token into a DPP)
   - **YES** branch: continue to pagination loop
   - **NO** branch: skip to step 6 (enrich packages)

5. **Pagination Loop**
   - Add a **Data Process** shape with Groovy that extracts the `queryToken` from the response and sets DPP `queryToken`
   - Add a **Set Properties** shape or Groovy snippet with `Thread.sleep(120)` to enforce the 120ms rate-limit gap between API calls
   - Add another **HTTP Client Send** — POST to `/partner/api/rest/v1/{primaryAccountId}/PackagedComponent/queryMore` with the `queryToken` value and `overrideAccount` = DPP `devAccountId`
   - Loop back to the Decision in step 4: check for another `queryToken` in the new response
   - Accumulate all `<PackagedComponent>` elements across pages

6. **For Each Package — Enrich with Component Name**
   - For each `<PackagedComponent>` in the accumulated results:
   - Add an **HTTP Client Send** shape:
     - Operation: `PROMO - HTTP Op - GET ComponentMetadata`
     - URL parameter `{2}` = the `componentId` from the current PackagedComponent
     - Query parameter: `overrideAccount` = DPP `devAccountId`
   - This returns the component's `name` and `type` metadata
   - Add a 120ms gap between calls (Data Process with `Thread.sleep(120)`)

7. **Map — Build Response JSON**
   - Source: accumulated XML data (PackagedComponent + ComponentMetadata results)
   - Destination: `PROMO - Profile - ListDevPackagesResponse`
   - Map each package to a `packages` array entry:
     - `packageId` from PackagedComponent response
     - `packageVersion` from PackagedComponent response
     - `componentId` from PackagedComponent response
     - `componentName` from ComponentMetadata response
     - `componentType` from ComponentMetadata response
     - `createdDate` from PackagedComponent response
     - `notes` from PackagedComponent response
   - Set `success` = `true`

8. **Return Documents** — same as Process F

#### Error Handling

Wrap the entire HTTP Client sequence (steps 3-6) in a **Try/Catch**. Catch block handles:
- API authentication failures (`errorCode = "AUTH_FAILED"`)
- Rate limit errors on 429/503 (`errorCode = "API_RATE_LIMIT"`)
- Invalid account (`errorCode = "ACCOUNT_NOT_FOUND"`)

**Verify:**

- Ensure you have at least one PackagedComponent in a dev sub-account (create one manually if needed: Build --> Packaged Components --> Create)
- Send a request with `devAccountId` set to that sub-account's ID
- **Expected**: response with `success = true` and a `packages` array containing the packaged component with its `componentName` populated
- Send a request with a `devAccountId` that has no packages
- **Expected**: `success = true`, `packages = []`
- If the dev account has more than 100 packages, verify pagination works by checking that all packages appear in the response

---

---
Prev: [Process E: Query Status](07-process-e-status-and-review.md) | Next: [Process B: Resolve Dependencies](09-process-b-resolve-dependencies.md) | [Back to Index](index.md)

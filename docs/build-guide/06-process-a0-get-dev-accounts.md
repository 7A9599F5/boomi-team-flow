### Process A0: Get Dev Accounts (`PROMO - Get Dev Accounts`)

This process retrieves development sub-accounts accessible to the current user based on their SSO group memberships.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - GetDevAccountsRequest` | `/integration/profiles/getDevAccounts-request.json` |
| `PROMO - Profile - GetDevAccountsResponse` | `/integration/profiles/getDevAccounts-response.json` |

The request JSON contains:
- `userSsoGroups` (array of strings): the user's Azure AD group IDs

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `accounts` (array): each entry has `devAccountId` and `devAccountName`

#### FSS Operation

Create `PROMO - FSS Op - GetDevAccounts` per the pattern in Section 3.B, using `PROMO - Profile - GetDevAccountsRequest` and `PROMO - Profile - GetDevAccountsResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — same as Process F: Connector = Boomi Flow Services Server, Action = Listen, Operation = `PROMO - FSS Op - GetDevAccounts`

2. **Set Properties** (read request fields)
   - DPP `userSsoGroups` = read from document path: `userSsoGroups` (this is a JSON array; store it as a string for later parsing)

3. **Data Process — Parse SSO Groups**
   - Add a **Data Process** shape with a short Groovy script that splits the `userSsoGroups` JSON array into individual documents — one document per SSO group ID:
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import groovy.json.JsonSlurper

   String groupsJson = ExecutionUtil.getDynamicProcessProperty("userSsoGroups")
   def groups = new JsonSlurper().parseText(groupsJson)

   for (int i = 0; i < dataContext.getDataCount(); i++) {
       Properties props = dataContext.getProperties(i)
       groups.each { groupId ->
           dataContext.storeStream(
               new ByteArrayInputStream(groupId.getBytes("UTF-8")), props)
       }
   }
   ```
   - This produces N documents, one per SSO group

4. **For Each SSO Group — DataHub Query**
   - The multiple documents flow naturally into the next connector shape (Boomi processes each document)
   - Add a **Connector** shape (DataHub):
     - Connector: `PROMO - DataHub Connection`
     - Operation: `PROMO - DH Op - Query DevAccountAccess`
     - Filter: `ssoGroupId EQUALS` the current document content, `AND isActive EQUALS "true"`
   - Each query returns the DevAccountAccess records for that SSO group

5. **Data Process — Deduplicate Accounts**
   - Add a **Data Process** shape with Groovy that collects all results and deduplicates by `devAccountId`:
   ```groovy
   import com.boomi.execution.ExecutionUtil
   import groovy.json.JsonOutput
   import groovy.xml.XmlSlurper

   def seen = new HashSet()
   def uniqueAccounts = []

   for (int i = 0; i < dataContext.getDataCount(); i++) {
       InputStream is = dataContext.getStream(i)
       Properties props = dataContext.getProperties(i)
       String xml = is.getText("UTF-8")
       def root = new XmlSlurper(false, false).parseText(xml)
       root.depthFirst().findAll { it.name() == 'DevAccountAccess' }.each { rec ->
           String accId = rec.devAccountId?.text()?.trim()
           if (accId && seen.add(accId)) {
               uniqueAccounts << [
                   devAccountId: accId,
                   devAccountName: rec.devAccountName?.text()?.trim() ?: ''
               ]
           }
       }
   }

   String output = JsonOutput.toJson(uniqueAccounts)
   dataContext.storeStream(
       new ByteArrayInputStream(output.getBytes("UTF-8")),
       dataContext.getProperties(0))
   ```
   - A user who belongs to multiple SSO groups may have access to the same dev account through more than one group. The `HashSet` on `devAccountId` eliminates these duplicates.

6. **Map — Build Response JSON**
   - Source: the deduplicated JSON array from step 5
   - Destination: `PROMO - Profile - GetDevAccountsResponse`
   - Map the `uniqueAccounts` array to the `accounts` array in the response
   - Set `success` = `true`

7. **Return Documents** — same as Process F

#### Error Handling

Wrap steps 4 and 5 in a **Try/Catch**. Catch block builds an error response with `errorCode = "DATAHUB_ERROR"`.

**Verify:**

- Seed at least one DevAccountAccess golden record in DataHub (see Phase 1, Step 1.4)
- Send a request with `userSsoGroups` containing the SSO group ID you seeded
- **Expected**: response with `success = true` and an `accounts` array containing the matching dev account
- Send a request with an SSO group ID that has no matching records
- **Expected**: response with `success = true` and `accounts = []` (empty array)

---

---
Prev: [Process F: Mapping CRUD](05-process-f-mapping-crud.md) | Next: [Process E: Query Status](07-process-e-status-and-review.md) | [Back to Index](index.md)

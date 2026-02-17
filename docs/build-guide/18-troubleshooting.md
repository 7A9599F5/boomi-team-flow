## Troubleshooting

### Phase 1 Issues

**"Model not visible after creation"**
The model must be Published AND Deployed to the repository. Creating and saving the model is not sufficient. Navigate to DataHub, open the model, click Publish, then click Deploy and select the target repository.

**"Match rule not working (duplicates created)"**
Verify the compound match rule uses the correct fields. ComponentMapping must match on `devComponentId` AND `devAccountId` (both fields). DevAccountAccess must match on `ssoGroupId` AND `devAccountId`. PromotionLog must match on `promotionId`. If the match rule is missing a field, records that should upsert will instead create duplicates. Delete duplicates manually and re-publish the corrected model.

**"Source name rejected when posting records"**
The source must be registered on the model before posting records. ComponentMapping and PromotionLog use source `PROMOTION_ENGINE`. DevAccountAccess uses source `ADMIN_CONFIG`. Add the source on the model's Sources tab, then Publish and Deploy again.

**Diagnostic -- check model state:**

```bash
# Linux/macOS -- query to verify model accepts records
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -X POST "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" \
  -H "Content-Type: application/xml" \
  -d '<RecordQueryRequest limit="1"><view><fieldId>devComponentId</fieldId></view></RecordQueryRequest>'
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; "Content-Type" = "application/xml" }
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{accountId}/DataHub/record/query" `
  -Method POST -Headers $headers -Body '<RecordQueryRequest limit="1"><view><fieldId>devComponentId</fieldId></view></RecordQueryRequest>'
```

If this returns a valid response (even with `totalCount="0"`), the model is deployed correctly. If it returns an error, the model is not deployed.

---

### Phase 2 Issues

**"Test connection fails for HTTP Client"**
Verify the URL is exactly `https://api.boomi.com` with no trailing path segments. The path is set on each operation, not the connection. Verify the username follows the format `BOOMI_TOKEN.user@company.com` and the API token is current (tokens can expire or be revoked in Settings, Account Information, Platform API Tokens).

**"overrideAccount not authorized"**
Three conditions must be met: (1) Partner API must be enabled on the primary account (Settings, Account Information, Partner API section). (2) The API token user must have Partner-level access or higher. (3) The dev account must be a sub-account of the primary account. If any condition is missing, the API returns HTTP 403.

**"HTTP 404 on operation execution"**
Verify the URL pattern uses `{1}` and `{2}` placeholder syntax correctly. `{1}` maps to `primaryAccountId` DPP. `{2}` maps to the component-specific ID DPP (e.g., `currentComponentId` or `prodComponentId`). Verify the DPP names match EXACTLY (case-sensitive) in the operation's Parameters tab. Also verify the operation names match the convention: `PROMO - HTTP Op - GET Component`, `PROMO - HTTP Op - POST Component Create`, etc.

**"HTTP 429 Too Many Requests"**
The Partner API enforces approximately 10 requests per second. Add a 120ms gap between consecutive API calls (yields approximately 8 requests per second with safety margin). Implement retry logic: up to 3 retries with exponential backoff (1 second, 2 seconds, 4 seconds). If 429 errors persist, reduce the call rate further.

**Diagnostic -- test an operation with curl:**

```bash
# Linux/macOS -- test GET Component with overrideAccount
curl -s -u "BOOMI_TOKEN.user@company.com:your-api-token" \
  -H "Accept: application/xml" \
  "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}"
```

```powershell
# Windows
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("BOOMI_TOKEN.user@company.com:your-api-token"))
$headers = @{ Authorization = "Basic $cred"; Accept = "application/xml" }
Invoke-RestMethod -Uri "https://api.boomi.com/partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}" `
  -Method GET -Headers $headers
```

---

### Phase 3 Issues

**"Groovy script error: property not found"**
Verify the DPP name matches EXACTLY (case-sensitive) in both the Set Properties shape and the Groovy script. The canonical names are:
- `visitedComponentIds` (not `visitedIds` or `visited_component_ids`)
- `componentQueue` (not `queue` or `component_queue`)
- `componentMappingCache` (not `mappingCache` or `component_mapping_cache`)
- `alreadyVisited` (not `already_visited`)
- `currentComponentId` (not `current_component_id`)
- `rootComponentId` (not `root_component_id`)
- `configStripped` (not `config_stripped`)
- `strippedElements` (not `stripped_elements`)
- `referencesRewritten` (not `references_rewritten`)
- `prodComponentId` (not `prod_component_id`)
- `promotionId` (not `promotion_id`)

**"Component references not rewritten"**
The `rewrite-references.groovy` script reads the `componentMappingCache` DPP and replaces each dev component ID with its corresponding prod component ID in the XML. If references are not being rewritten: (1) Verify `componentMappingCache` is being populated -- add a temporary logger.info statement to print its contents. (2) Verify that `sort-by-dependency.groovy` places dependencies before dependents in the processing order (profiles first, root process last). If a parent is processed before its dependency, the cache will not yet contain the mapping.

**"Infinite loop in dependency resolution"**
The `build-visited-set.groovy` script has cycle detection via the `visitedComponentIds` set. If a component has already been visited, the `alreadyVisited` DPP is set to `"true"` and the component is skipped. Check that the `visitedCount` DPP is growing with each iteration. If `visitedCount` stalls and `queueCount` does not decrease, there may be a self-referencing component. Inspect the `componentQueue` DPP to identify the repeating ID.

**"strip-env-config removes too much or too little"**
The `strip-env-config.groovy` script strips these elements by clearing their text content: `password`, `host`, `url`, `port`, `EncryptedValue`. Review the `strippedElements` DPP output after execution to see which elements were stripped. If additional elements need stripping, add them to the script. If an element is being stripped incorrectly, verify the element name is not colliding with a legitimate configuration element.

**Debugging tip:** Enable process logging in Boomi (Manage, Process Reporting). The Groovy scripts use `logger.info()` to write diagnostic messages. Check these logs to trace DPP values and processing steps.

**Debugging tip:** Add temporary Set Properties shapes between process steps to write DPP values to document properties. This makes them visible in Process Reporting without modifying Groovy code.

---

### Phase 4 Issues

**"No listeners found after deployment"**
Three conditions must be met: (1) The atom must be running (check Runtime Management, Atom Status). (2) The `PROMO - Flow Service` must be deployed as a Packaged Component to the atom. (3) The atom must be a public Boomi cloud atom (not a private cloud or local atom). Private atoms cannot receive inbound Flow Service requests.

**"Operation not found in Flow Service"**
Each FSS Operation must be linked in the Message Actions tab of the `PROMO - Flow Service` component. Verify all 11 operations are listed: `PROMO - FSS Op - GetDevAccounts`, `PROMO - FSS Op - ListDevPackages`, `PROMO - FSS Op - ResolveDependencies`, `PROMO - FSS Op - ExecutePromotion`, `PROMO - FSS Op - PackageAndDeploy`, `PROMO - FSS Op - QueryStatus`, `PROMO - FSS Op - ManageMappings`, `PROMO - FSS Op - QueryPeerReviewQueue`, `PROMO - FSS Op - SubmitPeerReview`, `PROMO - FSS Op - ListIntegrationPacks`, `PROMO - FSS Op - GenerateComponentDiff`. If an operation is missing from the list, add it, re-save, re-package, and re-deploy.

**"Configuration value not set"**
The `primaryAccountId` configuration value must be set after deployment via component configuration (Manage, Deployed Components, select the Flow Service, Configuration tab). This value is NOT set at build time -- it is set per deployment. If this value is empty, all HTTP operations using `{1}` in their URL will fail.

**Diagnostic:** Check Runtime Management, Listeners tab. All 11 processes should appear as active listeners. If fewer than 11 appear, verify each FSS Operation is correctly linked and the deployment is current.

---

### Phase 5 Issues

**"Retrieve Connector Configuration Data fails"**
Verify all of the following: (1) The atom is running. (2) The `PROMO - Flow Service` is deployed to the atom. (3) The Path to Service is exactly `/fs/PromotionService` (case-sensitive, no trailing slash). (4) Basic Auth credentials match the Shared Web Server User Management settings on the atom. If any of these are wrong, the retrieval will fail silently or return an error.

**"Flow Types not generated (fewer than 14)"**
After a successful "Retrieve Connector Configuration Data," Flow should auto-generate 24 types (2 per message action: request and response). If fewer than 24 appear, the Flow Service may have fewer than 12 message actions linked. Fix the Flow Service (Phase 4), re-deploy, then re-retrieve connector configuration data in Flow.

**"Message step returns empty response"**
Check the Flow value bindings on the Message step. Both input values (request type) and output values (response type) must be bound. The connector action name must match the message action name exactly (e.g., `executePromotion`, not `ExecutePromotion`). Verify the Flow Value type matches the auto-generated type name (e.g., `executePromotion REQUEST - executePromotionRequest`).

**"Swimlane transition fails (unauthorized)"**
Verify SSO groups are configured correctly in Azure AD/Entra. The Developer swimlane requires membership in "Boomi Developers." The Admin swimlane requires membership in "Boomi Admins." If the user does not belong to the correct group, the swimlane transition is blocked. Check the Identity connector configuration in Flow.

**"Email notification not sent at deployment submission"**
Check the email step configuration on the transition from Page 4 to Page 5. Verify the distribution list or recipient address is correct. Verify the Flow environment has email sending enabled. Test with a direct email address before using a distribution list.

**Debugging tip:** Use the Flow canvas Debug mode (Run, Debug) to trace step execution. Each step shows its inputs, outputs, and any errors. This is the fastest way to identify binding mismatches or connector failures.

---

### Phase 6 Issues

**"Promotion creates duplicate components instead of updating"**
The DataHub match rule on ComponentMapping is not functioning correctly, or the `devComponentId` and `devAccountId` fields are not populated in the promotion request. Verify the match rule is an exact compound match on both fields. Verify that Process C reads from the DataHub cache before creating -- if it skips the DataHub lookup, it will always create new components.

**"Version not incrementing on re-promotion"**
Verify Process C uses POST Component Update (`PROMO - HTTP Op - POST Component Update`) and not POST Component Create for existing components. The update URL includes the `{prodComponentId}` in the path: `/partner/api/rest/v1/{1}/Component/{2}`. Verify `prodComponentId` is correctly read from the `componentMappingCache` DPP or DataHub query result.

**"State not restored after browser close"**
Flow uses IndexedDB for client-side state caching. Verify the browser allows IndexedDB (some privacy modes disable it). The Integration process continues executing regardless of browser state -- the Flow Service is asynchronous. Reopening the same Flow URL should restore state. If it does not, check that the Flow is using the correct state ID in the URL hash.

---

---
Prev: [Phase 6: Testing](17-testing.md) | Next: [Appendix A: Naming & Inventory](19-appendix-naming-and-inventory.md) | [Back to Index](index.md)

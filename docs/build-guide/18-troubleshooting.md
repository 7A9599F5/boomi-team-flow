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
Each FSS Operation must be linked in the Message Actions tab of the `PROMO - Flow Service` component. Verify all 12 operations are listed: `PROMO - FSS Op - GetDevAccounts`, `PROMO - FSS Op - ListDevPackages`, `PROMO - FSS Op - ResolveDependencies`, `PROMO - FSS Op - ExecutePromotion`, `PROMO - FSS Op - PackageAndDeploy`, `PROMO - FSS Op - QueryStatus`, `PROMO - FSS Op - ManageMappings`, `PROMO - FSS Op - QueryPeerReviewQueue`, `PROMO - FSS Op - SubmitPeerReview`, `PROMO - FSS Op - ListIntegrationPacks`, `PROMO - FSS Op - GenerateComponentDiff`, `PROMO - FSS Op - QueryTestDeployments`. If an operation is missing from the list, add it, re-save, re-package, and re-deploy.

**"Configuration value not set"**
The `primaryAccountId` configuration value must be set after deployment via component configuration (Manage, Deployed Components, select the Flow Service, Configuration tab). This value is NOT set at build time -- it is set per deployment. If this value is empty, all HTTP operations using `{1}` in their URL will fail.

**Diagnostic:** Check Runtime Management, Listeners tab. All 12 processes should appear as active listeners. If fewer than 12 appear, verify each FSS Operation is correctly linked and the deployment is current.

---

### Phase 5 Issues

**"Retrieve Connector Configuration Data fails"**
Verify all of the following: (1) The atom is running. (2) The `PROMO - Flow Service` is deployed to the atom. (3) The Path to Service is exactly `/fs/PromotionService` (case-sensitive, no trailing slash). (4) Basic Auth credentials match the Shared Web Server User Management settings on the atom. If any of these are wrong, the retrieval will fail silently or return an error.

**"Flow Types not generated (fewer than 14)"**
After a successful "Retrieve Connector Configuration Data," Flow should auto-generate 24 types (2 per message action: request and response). If fewer than 24 appear, the Flow Service may have fewer than 12 message actions linked. Fix the Flow Service (Phase 4), re-deploy, then re-retrieve connector configuration data in Flow.

**"Message step returns empty response"**
Check the Flow value bindings on the Message step. Both input values (request type) and output values (response type) must be bound. The connector action name must match the message action name exactly (e.g., `executePromotion`, not `ExecutePromotion`). Verify the Flow Value type matches the auto-generated type name (e.g., `executePromotion REQUEST - executePromotionRequest`).

**"Swimlane transition fails (unauthorized)"**
Verify SSO groups are configured correctly in Azure AD/Entra. The Developer swimlane requires membership in `ABC_BOOMI_FLOW_CONTRIBUTOR`. The Admin swimlane requires membership in `ABC_BOOMI_FLOW_ADMIN`. If the user does not belong to the correct group, the swimlane transition is blocked. Check the Identity connector configuration in Flow.

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

### Multi-Environment Deployment Issues

**"Test deployment fails — atom not responding"**
Verify the test environment's atom is running and accessible. Navigate to Runtime Management, Atom Status and check the test atom. If the atom is stopped or unreachable, restart it. Also verify the `environmentId` passed in the `targetEnvironments` array matches an actual environment associated with the test atom. Mismatched environment IDs cause silent deployment failures.

**"Test deployment succeeds but wrong environment"**
The `targetEnvironments` array in the `packageAndDeploy` request must contain the correct test environment ID. If a production environment ID is passed with `deploymentTarget = "TEST"`, the deployment will target the wrong environment. Always verify the environment ID matches the intended deployment target. The PromotionLog `targetEnvironment` field reflects the deployment mode, not which environment was targeted.

**"Branch deleted prematurely before production promotion"**
When deploying from test to production (`deploymentTarget = "PRODUCTION"` with `testPromotionId`), Process D expects the promotion branch to still exist. If the branch was manually deleted or cleaned up by a stale branch cleanup process, the production deployment will fail. Verify the branch exists via `GET /Branch/{branchId}` before initiating production promotion. If the branch is gone, the developer must re-execute the full promotion (Process C) and test deployment cycle.

**"queryTestDeployments returns stale entries"**
Process E4 queries PromotionLog for `targetEnvironment = "TEST"` AND `status = "TEST_DEPLOYED"` records without a matching production promotion. If a test deployment's branch has been manually deleted but the PromotionLog was not updated, the entry will still appear in the queue. Verify branch existence before promoting from the test queue. If the branch no longer exists, update the PromotionLog status to `TEST_DEPLOY_FAILED` to remove it from the queue.

**"Hotfix deployment rejected — missing justification"**
When `deploymentTarget = "PRODUCTION"` and `isHotfix = true`, the `hotfixJustification` field is required. If omitted, Process D returns `errorCode = HOTFIX_JUSTIFICATION_REQUIRED`. The Flow dashboard enforces this via a required text field on the hotfix submission page, but direct API calls may omit it. Always include a meaningful justification (up to 1000 characters).

**"Hotfix with dependencies not present in production"**
Emergency hotfixes bypass test deployment. If the hotfixed process references components that have never been promoted to production (no ComponentMapping records exist), the promotion will fail with `MISSING_CONNECTION_MAPPINGS` or `COMPONENT_NOT_FOUND`. Before submitting a hotfix, verify all dependencies have existing production mappings. If not, either seed the missing mappings via `manageMappings` or follow the standard test-to-production path instead.

**"Production promotion fails — TEST_PROMOTION_NOT_FOUND"**
When deploying from test to production, the `testPromotionId` must reference a valid PromotionLog record with `status = "TEST_DEPLOYED"`. If the referenced promotion has a different status (e.g., `TEST_DEPLOY_FAILED`) or does not exist, Process D returns `errorCode = TEST_PROMOTION_NOT_FOUND`. Verify the test promotion status before submitting for production.

---

### Error Code Cross-Reference

Complete mapping of all error codes to their source processes, causes, and resolutions.

| Error Code | Process(es) | Cause | Resolution |
|------------|-------------|-------|------------|
| `AUTH_FAILED` | All | API authentication failed — invalid or expired API token | Verify API token in HTTP Client connection; rotate if expired (see Token Rotation Procedure in flow-service-spec) |
| `ACCOUNT_NOT_FOUND` | A, A0 | Dev account ID does not exist or is not a sub-account of the primary account | Verify `devAccountId` is a valid sub-account; check Partner API access |
| `COMPONENT_NOT_FOUND` | B, C, G | Referenced component ID does not exist in the target account | Verify component exists in the dev account; check for renamed or deleted components |
| `DATAHUB_ERROR` | E, E2, E3, E4, F | DataHub query or update operation failed | Check DataHub model deployment status; verify the model is Published and Deployed to the repository |
| `API_RATE_LIMIT` | All (API calls) | Partner API rate limit exceeded (approximately 10 req/s) | Wait and retry; ensure 120ms gap between consecutive calls; check for parallel processes creating excessive load |
| `DEPENDENCY_CYCLE` | B | Circular dependency detected during BFS traversal | Review component references in the dev account; break the circular reference |
| `INVALID_REQUEST` | All | Request validation failed — missing required fields or invalid field values | Check required fields in the flow-service-spec for the specific action |
| `PROMOTION_FAILED` | C | Component promotion failed during branch creation or component write | Review `errorMessage` for specific failure details; check component XML validity |
| `PROMOTION_IN_PROGRESS` | C | Another promotion is already running for the same dev account (concurrency guard) | Wait for the current promotion to complete before starting a new one |
| `DEPLOYMENT_FAILED` | D | Environment deployment failed — atom unreachable or environment invalid | Verify target environment exists and atom is running; check environment associations |
| `MISSING_CONNECTION_MAPPINGS` | C | One or more connection references lack prod mappings in DataHub | Admin seeds missing mappings via `manageMappings` action or Mapping Viewer (Page 8); `missingConnectionMappings` array in response lists the specific missing mappings |
| `BRANCH_LIMIT_REACHED` | C | 15+ active promotion branches exist in the primary account | Clean up completed branches; wait for pending reviews to complete; admin can delete stale branches via Platform API |
| `SELF_REVIEW_NOT_ALLOWED` | E3 | Reviewer email matches promotion initiator email (case-insensitive) | A different team member must perform the peer review |
| `ALREADY_REVIEWED` | E3 | Promotion has already been peer-reviewed (`peerReviewStatus` is not `PENDING_PEER_REVIEW`) | No action needed; check current promotion status via `queryStatus` |
| `INVALID_REVIEW_STATE` | E3 | Promotion is not in the expected state for the review action (e.g., still IN_PROGRESS or already FAILED) | Verify the promotion completed successfully and is in PENDING_PEER_REVIEW status |
| `INSUFFICIENT_TIER` | A0, C | User's SSO groups do not include a dashboard-access tier group | User must be assigned `ABC_BOOMI_FLOW_CONTRIBUTOR` or `ABC_BOOMI_FLOW_ADMIN` group in Azure AD/Entra |
| `SELF_APPROVAL_NOT_ALLOWED` | D | Admin email matches the promotion initiator email (case-insensitive) | A different admin must approve and deploy the promotion |
| `MERGE_FAILED` | D | Branch merge request returned `MERGE_FAILED` status | Review merge error details; may indicate conflicting changes on main; check branch status via `GET /Branch/{branchId}` |
| `MERGE_TIMEOUT` | D | Merge request did not complete within 60 seconds (12 polling attempts at 5s intervals) | Retry the deployment; if persistent, check platform status and branch state manually |
| `TEST_DEPLOY_FAILED` | D | Test environment deployment failed | Check test environment atom status; verify environment ID; retry the test deployment |
| `HOTFIX_JUSTIFICATION_REQUIRED` | D | Emergency hotfix submitted without justification text | Provide `hotfixJustification` field (up to 1000 characters) in the request |
| `INVALID_DEPLOYMENT_TARGET` | D | `deploymentTarget` field is not `"TEST"` or `"PRODUCTION"` | Correct the `deploymentTarget` value in the request |
| `TEST_PROMOTION_NOT_FOUND` | D | `testPromotionId` references a non-existent or non-`TEST_DEPLOYED` promotion | Verify the test promotion exists and is in `TEST_DEPLOYED` status before promoting to production |

---

---

## Operational Monitoring

### Key Metrics to Track

| Metric | Description | Collection Method |
|--------|-------------|-------------------|
| **Promotion throughput** | Promotions completed per day/week, average duration | Process Reporting — filter by `PROMO - FSS Op - ExecutePromotion` |
| **API error rates** | 4xx and 5xx responses per process, with 429 rate limit hits highlighted | Process Reporting error logs; custom Groovy logger.info counters |
| **Branch utilization** | Active branches vs 15-branch threshold (alert at 12+) | Scheduled process: `POST /Branch/query` daily, count results |
| **DataHub query latency** | Average and P95 query times for PromotionLog, ComponentMapping | Process Reporting execution step timings |
| **Process execution times** | Per-process average duration, with anomaly detection for >2x normal | Process Reporting — compare against baseline durations |
| **DPP cache sizes** | `componentMappingCache` character count (warn at >500KB, Boomi DPP limit is ~1MB) | Groovy logger.info of cache size before/after population |

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Active branches | 12 | 15 |
| API 5xx rate | >5% per hour | >15% per hour |
| 429 rate limit hits | >10 per hour | >50 per hour |
| Process C duration | >5 minutes | >15 minutes |
| Failed promotions | >2 per day | >5 per day |

### Suggested SLAs

| Operation | Target |
|-----------|--------|
| Promotion completion (<50 components) | <10 minutes |
| Peer review queue refresh | <30 seconds |
| Status query response | <5 seconds |
| System availability (business hours) | 99.5% |

### Implementation Guidance

- **Process Reporting**: Use Boomi's built-in Process Reporting for execution tracking. Filter by process name prefix `PROMO - FSS Op -` to isolate promotion system executions.
- **Custom alerts**: Set up alerts via the Process Reporting API or AtomSphere scheduled reports. Configure email notifications for critical threshold breaches.
- **Branch utilization monitoring**: Create a scheduled Integration Process that runs daily, queries `POST /Branch/query` to count active branches, and sends an alert email when the count exceeds the warning threshold (12).
- **DPP cache monitoring**: Add `logger.info("componentMappingCache size: " + cache.length())` to the `rewrite-references.groovy` script to track cache size growth over time in Process Reporting logs.

---
Prev: [Phase 6: Testing](17-testing.md) | Next: [Appendix A: Naming & Inventory](19-appendix-naming-and-inventory.md) | [Back to Index](index.md)

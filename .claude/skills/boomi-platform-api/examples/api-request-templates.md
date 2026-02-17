# API Request Templates

Common curl and request patterns for all 11 promotion processes.

---

## Authentication Setup

**Environment Variables:**
```bash
export BOOMI_ACCOUNT_ID="primary-account-uuid"
export BOOMI_USERNAME="user@boomi.com"
export BOOMI_API_TOKEN="BOOMI_TOKEN.user@boomi.com:abc123def456"
export DEV_ACCOUNT_ID="dev-account-uuid"
```

**Base64 Encode Credentials:**
```bash
echo -n "${BOOMI_USERNAME}:${BOOMI_API_TOKEN}" | base64
```

---

## Process A0: getDevAccounts

Query dev accounts accessible to SSO group.

**Query DevAccountAccess (DataHub):**
```http
POST https://api.boomi.com/api/rest/v1/{accountId}/DataHub/query/DevAccountAccess

Authorization: Basic {base64-credentials}
Content-Type: application/json

{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "ssoGroupId",
      "argument": ["{ssoGroupId}"]
    }
  }
}
```

---

## Process A: listDevPackages

Query PackagedComponents from dev account.

**Query PackagedComponents:**
```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/PackagedComponent/query?overrideAccount=${DEV_ACCOUNT_ID}" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "QueryFilter": {
      "expression": {
        "operator": "and",
        "nestedExpression": [
          {"operator": "EQUALS", "property": "componentType", "argument": ["process"]},
          {"operator": "EQUALS", "property": "deleted", "argument": ["false"]}
        ]
      }
    }
  }'
```

**Response:**
```json
{
  "@type": "QueryResult",
  "numberOfResults": 2,
  "result": [
    {
      "@type": "PackagedComponent",
      "packageId": "pkg-uuid-1",
      "componentId": "comp-uuid-1",
      "componentType": "process",
      "componentVersion": "2",
      "packageVersion": "1.5",
      "shareable": true
    }
  ]
}
```

---

## Process B: resolveDependencies

Query component dependencies recursively.

**Step 1: Query ComponentReference:**
```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/ComponentReference/query?overrideAccount=${DEV_ACCOUNT_ID}" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "QueryFilter": {
      "expression": {
        "operator": "and",
        "nestedExpression": [
          {"operator": "EQUALS", "property": "parentComponentId", "argument": ["{componentId}"]},
          {"operator": "EQUALS", "property": "parentVersion", "argument": ["{version}"]}
        ]
      }
    }
  }'
```

**Response:**
```json
{
  "@type": "QueryResult",
  "result": [
    {
      "@type": "ComponentReference",
      "parentComponentId": "process-uuid",
      "parentVersion": "2",
      "componentId": "connection-uuid",
      "type": "connection"
    }
  ]
}
```

**Step 2: GET Component XML (for each dependency):**
```bash
curl -X GET \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/Component/{componentId}?overrideAccount=${DEV_ACCOUNT_ID}" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Accept: application/xml"
```

**Repeat recursively** for each dependency.

---

## Process C: executePromotion

Promote components to branch in primary account.

### Step 1: Pre-Check Branch Count

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/Branch/query" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/xml" \
  -d '<QueryFilter xmlns="http://api.platform.boomi.com/"/>'
```

**Check:** If `numberOfResults >= 15`, abort with `BRANCH_LIMIT_REACHED`.

### Step 2: Create Branch

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/Branch" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "promo-12345",
    "description": "Promotion branch for 12345"
  }'
```

**Response:**
```json
{
  "@type": "Branch",
  "branchId": "branch-uuid-abc123",
  "name": "promo-12345",
  "ready": false,
  "stage": "CREATING"
}
```

### Step 3: Poll for Ready State

```bash
curl -X GET \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/Branch/{branchId}" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)"
```

**Poll every 5 seconds until `ready: true`.**

### Step 4: Promote Component to Branch (Tilde Syntax)

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/Component/{prodComponentId}~{branchId}" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/xml" \
  -d @component-stripped-rewritten.xml
```

**component-stripped-rewritten.xml:**
```xml
<bns:Component
  xmlns:bns="http://api.platform.boomi.com/"
  componentId="{prodComponentId}"
  version="{version}"
  name="Order Processor"
  type="process"
  folderFullPath="/Promoted/DevTeamA/Orders/Process">
  <bns:object>
    <!-- Stripped and rewritten component configuration -->
  </bns:object>
</bns:Component>
```

**Repeat for each component in dependency order.**

---

## Process D: packageAndDeploy

Merge branch, package, deploy.

### Step 1: Create MergeRequest

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/MergeRequest" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "sourceBranchId": "{branchId}",
    "destinationBranchId": "main",
    "strategy": "OVERRIDE",
    "priorityBranch": "{branchId}"
  }'
```

**Response:**
```json
{
  "@type": "MergeRequest",
  "id": "merge-request-uuid",
  "stage": "DRAFTED"
}
```

### Step 2: Execute MergeRequest

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/MergeRequest/execute/{mergeRequestId}" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)"
```

### Step 3: Create PackagedComponent

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/PackagedComponent" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "componentId": "{prodComponentId}",
    "packageVersion": "1.2",
    "notes": "Promoted from dev account",
    "shareable": true
  }'
```

**Response:**
```json
{
  "@type": "PackagedComponent",
  "packageId": "pkg-uuid-123",
  "packageVersion": "1.2"
}
```

### Step 4: Create Integration Pack (if new)

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/IntegrationPack" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Order Processing Pack",
    "description": "Complete order processing solution",
    "installationType": "MULTI"
  }'
```

### Step 5: Add to Integration Pack

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/IntegrationPack/{packId}/addPackagedComponent" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "packageId": "{packageId}"
  }'
```

### Step 6: Release Integration Pack

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/IntegrationPack/{packId}/release" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)"
```

### Step 7: Deploy to Environments

```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/DeployedPackage" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "environmentId": "{envId}",
    "packageId": "{packageId}",
    "notes": "Deployed via Integration Pack",
    "listenerStatus": "RUNNING"
  }'
```

### Step 8: Delete Branch

```bash
curl -X DELETE \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/Branch/{branchId}" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)"
```

---

## Process E: queryStatus

Query PromotionLog from DataHub.

**Query PromotionLog:**
```bash
curl -X POST \
  "https://api.boomi.com/api/rest/v1/${BOOMI_ACCOUNT_ID}/DataHub/query/PromotionLog" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "QueryFilter": {
      "expression": {
        "operator": "EQUALS",
        "property": "promotionId",
        "argument": ["{promotionId}"]
      }
    }
  }'
```

**With reviewStage filter:**
```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "reviewStage",
      "argument": ["PENDING_PEER_REVIEW"]
    }
  }
}
```

---

## Process E2: queryPeerReviewQueue

Query promotions pending peer review (exclude own).

**Query PromotionLog:**
```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "reviewStage", "argument": ["PENDING_PEER_REVIEW"]},
        {"operator": "NOT_EQUALS", "property": "submittedBy", "argument": ["{currentUser}"]}
      ]
    }
  }
}
```

---

## Process E3: submitPeerReview

Record peer review decision in PromotionLog.

**Update PromotionLog (DataHub):**
```bash
curl -X POST \
  "https://api.boomi.com/api/rest/v1/${BOOMI_ACCOUNT_ID}/DataHub/update/PromotionLog" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/xml" \
  -d '<PromotionLog>
    <promotionId>{promotionId}</promotionId>
    <reviewStage>PENDING_ADMIN_REVIEW</reviewStage>
    <peerReviewedBy>{reviewerEmail}</peerReviewedBy>
    <peerReviewDate>{timestamp}</peerReviewDate>
    <peerReviewDecision>APPROVED</peerReviewDecision>
  </PromotionLog>'
```

---

## Process F: manageMappings

CRUD on ComponentMapping records.

**CREATE ComponentMapping:**
```bash
curl -X POST \
  "https://api.boomi.com/api/rest/v1/${BOOMI_ACCOUNT_ID}/DataHub/update/ComponentMapping" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/xml" \
  -d '<ComponentMapping>
    <devComponentId>{devComponentId}</devComponentId>
    <devAccountId>{devAccountId}</devAccountId>
    <prodComponentId>{prodComponentId}</prodComponentId>
    <componentType>connection</componentType>
    <source>PROMOTION_ENGINE</source>
  </ComponentMapping>'
```

**QUERY ComponentMapping:**
```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "devComponentId", "argument": ["{devComponentId}"]},
        {"operator": "EQUALS", "property": "devAccountId", "argument": ["{devAccountId}"]}
      ]
    }
  }
}
```

---

## Process G: generateComponentDiff

Fetch branch and main versions for diff.

**GET Branch Version:**
```bash
curl -X GET \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/Component/{componentId}~{branchId}" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Accept: application/xml"
```

**GET Main Version:**
```bash
curl -X GET \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/Component/{componentId}" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Accept: application/xml"
```

**Post-Processing:**
Use `normalize-xml.groovy` to pretty-print both XMLs for consistent diff.

---

## Process J: listIntegrationPacks

Query Integration Packs for suggestions.

**Query All Integration Packs:**
```bash
curl -X POST \
  "https://api.boomi.com/partner/api/rest/v1/${BOOMI_ACCOUNT_ID}/IntegrationPack/query" \
  -H "Authorization: Basic $(echo -n ${BOOMI_USERNAME}:${BOOMI_API_TOKEN} | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "QueryFilter": {
      "expression": {
        "operator": "LIKE",
        "property": "name",
        "argument": ["%Order%"]
      }
    }
  }'
```

**Combine with PromotionLog query** to find historically used packs.

---

## Postman Collection Structure

**Collections:**
1. **Authentication** — Token generation, base URL setup
2. **Process A0** — getDevAccounts
3. **Process A** — listDevPackages
4. **Process B** — resolveDependencies (recursive)
5. **Process C** — executePromotion (branch lifecycle)
6. **Process D** — packageAndDeploy (merge, package, deploy, cleanup)
7. **Process E** — queryStatus
8. **Process E2** — queryPeerReviewQueue
9. **Process E3** — submitPeerReview
10. **Process F** — manageMappings
11. **Process G** — generateComponentDiff
12. **Process J** — listIntegrationPacks

**Environment Variables:**
- `{{baseUrl}}`: `https://api.boomi.com/partner/api/rest/v1`
- `{{accountId}}`: Primary account UUID
- `{{devAccountId}}`: Dev account UUID
- `{{auth}}`: Base64-encoded credentials

---

## Related Project Files

**Request Templates (XML/JSON):**
- `/home/glitch/code/boomi_team_flow/integration/api-requests/get-component.xml`
- `/home/glitch/code/boomi_team_flow/integration/api-requests/create-branch.json`
- `/home/glitch/code/boomi_team_flow/integration/api-requests/create-merge-request.json`
- `/home/glitch/code/boomi_team_flow/integration/api-requests/execute-merge-request.json`
- `/home/glitch/code/boomi_team_flow/integration/api-requests/create-packaged-component.json`
- `/home/glitch/code/boomi_team_flow/integration/api-requests/create-deployed-package.json`
- `/home/glitch/code/boomi_team_flow/integration/api-requests/create-integration-pack.json`

**JSON Profiles:**
- `/home/glitch/code/boomi_team_flow/integration/profiles/` (22 request/response profiles)

### Process D: Package and Deploy (`PROMO - Package and Deploy`)

This process creates a PackagedComponent from a promoted component, optionally creates or updates an Integration Pack, and deploys to target environments.

#### Profiles

| Profile | Source File |
|---------|------------|
| `PROMO - Profile - PackageAndDeployRequest` | `/integration/profiles/packageAndDeploy-request.json` |
| `PROMO - Profile - PackageAndDeployResponse` | `/integration/profiles/packageAndDeploy-response.json` |

The request JSON contains:
- `prodComponentId` (string): the promoted root process component in the primary account
- `prodAccountId` (string): the primary account ID
- `packageVersion` (string): version label for the package (e.g., `"1.2.0"`)
- `integrationPackId` (string): existing Integration Pack ID (used when `createNewPack = false`)
- `createNewPack` (boolean): `true` to create a new Integration Pack, `false` to add to existing
- `newPackName` (string): name for new pack (required if `createNewPack = true`)
- `newPackDescription` (string): description for new pack
- `targetAccountGroupId` (string): account group to deploy to

The response JSON contains:
- `success`, `errorCode`, `errorMessage` (standard error contract)
- `packagedComponentId` (string): ID of the created PackagedComponent
- `integrationPackId` (string): ID of the Integration Pack (new or existing)
- `integrationPackName` (string): name of the Integration Pack
- `releaseVersion` (string): the released pack version
- `deploymentStatus` (string): overall deployment status
- `deployedEnvironments` (array): each entry has `environmentId`, `environmentName`, `status`

#### FSS Operation

Create `PROMO - FSS Op - PackageAndDeploy` per Section 3.B, using `PROMO - Profile - PackageAndDeployRequest` and `PROMO - Profile - PackageAndDeployResponse`.

#### Canvas — Shape by Shape

1. **Start shape** — Operation = `PROMO - FSS Op - PackageAndDeploy`

2. **Set Properties — Read Request**
   - DPP `prodComponentId` = document path: `prodComponentId`
   - DPP `prodAccountId` = document path: `prodAccountId`
   - DPP `packageVersion` = document path: `packageVersion`
   - DPP `createNewPack` = document path: `createNewPack`
   - DPP `integrationPackId` = document path: `integrationPackId`
   - DPP `newPackName` = document path: `newPackName`
   - DPP `newPackDescription` = document path: `newPackDescription`
   - DPP `targetAccountGroupId` = document path: `targetAccountGroupId`

3. **HTTP Client Send — POST PackagedComponent**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - POST PackagedComponent`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - Request body: JSON containing `componentId` = DPP `prodComponentId`, `packageVersion` = DPP `packageVersion`, `notes` = promotion metadata, `shareable` = `true`
   - Build the request JSON with a Map shape before this connector:
     - Source: DPPs
     - Destination: PackagedComponent create JSON
   - Response returns the new `packagedComponentId`
   - Extract `packagedComponentId` into a DPP

4. **Decision — Create New Pack?**
   - Condition: DPP `createNewPack` **EQUALS** `"true"`
   - **YES** branch: step 5 (create new Integration Pack)
   - **NO** branch: step 6 (add to existing pack)

5. **YES Branch — HTTP Client Send — POST IntegrationPack**
   - Connector: `PROMO - Partner API Connection`
   - Operation: `PROMO - HTTP Op - POST IntegrationPack`
   - URL parameter `{1}` = DPP `primaryAccountId`
   - Request body: JSON with `name` = DPP `newPackName`, `description` = DPP `newPackDescription`
   - Response returns the new `integrationPackId`
   - Set DPP `integrationPackId` from the response
   - After creating the pack, add the PackagedComponent to it (Platform API call to add component to pack)
   - Continue to step 7

6. **NO Branch — Add to Existing Pack**
   - The `integrationPackId` DPP already holds the existing pack ID
   - Add the PackagedComponent (from step 3) to the existing Integration Pack via the Platform API
   - Continue to step 7

7. **HTTP Client Send — Release Integration Pack**
   - POST to release the Integration Pack (makes it deployable)
   - This may use an existing HTTP operation or a generic HTTP Client Send with the release endpoint
   - URL: `/partner/api/rest/v1/{primaryAccountId}/IntegrationPackRelease`
   - Request body includes `integrationPackId` and release notes
   - Response returns the `releaseVersion`

8. **For Each Target Environment — Deploy**
   - If `targetAccountGroupId` is provided, deploy the released pack:
   - **HTTP Client Send** — POST DeployedPackage
     - Connector: `PROMO - Partner API Connection`
     - Operation: `PROMO - HTTP Op - POST DeployedPackage`
     - URL parameter `{1}` = DPP `primaryAccountId`
     - Request body: JSON with `packageId`, `environmentId`, and deployment parameters
   - Accumulate deployment results for each environment (success/failure per environment)
   - Add 120ms gap between deployment calls

9. **Map — Build Response JSON**
   - Source: accumulated results and DPPs
   - Destination: `PROMO - Profile - PackageAndDeployResponse`
   - Map:
     - `packagedComponentId` from DPP
     - `integrationPackId` from DPP
     - `integrationPackName` = DPP `newPackName` (or queried name for existing pack)
     - `releaseVersion` from step 7 response
     - `deploymentStatus` = `"DEPLOYED"` if all succeeded, `"PARTIAL"` if some failed
     - `deployedEnvironments` array from step 8 results
     - `success` = `true`

10. **Return Documents** — same as Process F

#### Error Handling

Wrap the entire process (steps 3-8) in a **Try/Catch**:
- **PackagedComponent creation failure**: return error with `errorCode = "PROMOTION_FAILED"`
- **Integration Pack failure**: return error with `errorCode = "PROMOTION_FAILED"`
- **Deployment failure**: per-environment — mark individual environments as failed in the `deployedEnvironments` array, but continue deploying to remaining environments. Set `deploymentStatus = "PARTIAL"`.

**Verify:**

- First, promote a component using Process C so you have a `prodComponentId` in the primary account
- Send a Package and Deploy request with `createNewPack = true`, a `newPackName`, and a `targetAccountGroupId`
- **Expected**:
  - Response with `success = true`
  - `packagedComponentId` is populated (new PackagedComponent created)
  - `integrationPackId` is populated (new Integration Pack created)
  - `releaseVersion` is populated
  - `deployedEnvironments` shows each target with `status = "DEPLOYED"`
- Verify in Boomi AtomSphere:
  - The PackagedComponent appears under the promoted component
  - The Integration Pack exists with the component included
  - The deployment appears in Deploy --> Deployments

---

---
Prev: [Process C: Execute Promotion](10-process-c-execute-promotion.md) | Next: [Process J: List Integration Packs](12-process-j-list-integration-packs.md) | [Back to Index](index.md)

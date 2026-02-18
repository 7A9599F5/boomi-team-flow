---
globs:
  - "integration/**"
---

# Integration Patterns

## Naming Conventions

### Processes
- **Prefix all Integration processes with `PROMO - `**
- Example: `PROMO - FSS Op - GetDevAccounts`

### Process Letter Codes
- **A0**: getDevAccounts — SSO group → dev account access lookup
- **A**: listDevPackages — query dev account's PackagedComponents
- **B**: resolveDependencies — recursive dependency traversal + mapping lookup
- **C**: executePromotion — create branch → promote to branch → strip env config → rewrite refs
- **D**: packageAndDeploy — merge branch → main, create PackagedComponent, Integration Pack, deploy
- **E**: queryStatus — read PromotionLog from DataHub
- **E2**: queryPeerReviewQueue — query PENDING_PEER_REVIEW promotions, exclude own
- **E3**: submitPeerReview — record peer approve/reject with self-review prevention
- **E4**: queryTestDeployments — query TEST_DEPLOYED promotions ready for production promotion
- **E5**: withdrawPromotion — initiator withdraws pending promotion, deletes branch
- **F**: manageMappings — CRUD on ComponentMapping records
- **G**: generateComponentDiff — fetch branch vs main component XML for diff rendering
- **J**: listIntegrationPacks — query Integration Packs with smart suggestion from history
- **K**: listClientAccounts — SSO group → accessible client accounts + environments
- **L**: getExtensions — read env extensions + map extension summaries + access data
- **M**: updateExtensions — save env extension changes (partial update, access-validated)
- **N**: copyExtensionsTestToProd — copy non-connection extensions from Test to Prod
- **O**: updateMapExtension — save map extension changes (Phase 2; Phase 1 read-only)
- **P**: checkReleaseStatus — poll ReleaseIntegrationPackStatus for release propagation tracking

### Profile Naming
- **Pattern**: `PROMO - Profile - {ActionName}Request` / `PROMO - Profile - {ActionName}Response`
- Examples:
  - `PROMO - Profile - GetDevAccountsRequest`
  - `PROMO - Profile - ExecutePromotionResponse`

### Error Codes
- **Format**: UPPER_SNAKE_CASE
- Examples:
  - `MISSING_CONNECTION_MAPPINGS`
  - `COMPONENT_NOT_FOUND`
  - `BRANCH_LIMIT_REACHED`
  - `SELF_REVIEW_NOT_ALLOWED`

## Build Order Dependencies

### Phase 3: Integration Process Build Order
1. **Process A0** (no dependencies) — foundation for dev account access
2. **Process A** (no dependencies) — package listing
3. **Process B** (depends on A) — dependency resolution
4. **Process C** (depends on B) — promotion execution
5. **Process E** (no dependencies) — status queries
6. **Process E4** (depends on E) — test deployment queries
7. **Process E2** (depends on E) — peer review queue
8. **Process E3** (depends on E2) — peer review submission
9. **Process E5** (depends on E) — promotion withdrawal
10. **Process F** (no dependencies) — mapping management
11. **Process G** (depends on C) — component diff generation
12. **Process J** (no dependencies) — Integration Pack listing
13. **Process D** (depends on C) — final packaging and deployment
14. **Process K** (no dependencies) — client account listing
15. **Process L** (depends on K context) — extension reading
16. **Process M** (depends on L context) — extension writing
17. **Process N** (depends on L context) — Test-to-Prod copy
18. **Process O** (depends on L context) — map extension writing
19. **Process P** (depends on D context) — release status polling

### Why This Order Matters
- Process C creates the promotion branch; Processes G and D depend on branch operations
- Processes E2, E3, E4, and E5 extend Process E's status query logic for 2-layer approval, test deployment tracking, and withdrawal
- Process B must exist before C (dependency tree feeds into promotion)

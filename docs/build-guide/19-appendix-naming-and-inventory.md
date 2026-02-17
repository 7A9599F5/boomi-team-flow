## Appendix A: Naming Conventions

### Component Naming Patterns

| Component Type | Pattern | Example |
|---------------|---------|---------|
| DataHub Model | `{ModelName}` | `ComponentMapping` |
| HTTP Client Connection | `PROMO - {Description} Connection` | `PROMO - Partner API Connection` |
| DataHub Connection | `PROMO - DataHub Connection` | `PROMO - DataHub Connection` |
| HTTP Client Operation | `PROMO - HTTP Op - {METHOD} {Resource}` | `PROMO - HTTP Op - GET Component` |
| DataHub Operation | `PROMO - DH Op - {Action} {Model}` | `PROMO - DH Op - Query ComponentMapping` |
| JSON Profile | `PROMO - Profile - {ActionName}{Request\|Response}` | `PROMO - Profile - ExecutePromotionRequest` |
| Integration Process | `PROMO - {Description}` | `PROMO - Execute Promotion` |
| FSS Operation | `PROMO - FSS Op - {ActionName}` | `PROMO - FSS Op - ExecutePromotion` |
| Flow Service | `PROMO - Flow Service` | `PROMO - Flow Service` |
| Flow Connector | `Promotion Service Connector` | `Promotion Service Connector` |
| Flow Application | `Promotion Dashboard` | `Promotion Dashboard` |

### Folder Structure for Promoted Components

```
/Promoted/{DevAccountName}/{ProcessName}/
```

All components promoted by the system are placed in this folder hierarchy. Boomi auto-creates folders that do not exist.

### Complete 51-Component Inventory Checklist

```
Phase 1 -- DataHub Models (3):
[ ] 1. ComponentMapping
[ ] 2. DevAccountAccess
[ ] 3. PromotionLog

Phase 2 -- Connections (2):
[ ] 4. PROMO - Partner API Connection
[ ] 5. PROMO - DataHub Connection

Phase 2 -- HTTP Client Operations (12):
[ ] 6.  PROMO - HTTP Op - GET Component
[ ] 7.  PROMO - HTTP Op - POST Component Create
[ ] 8.  PROMO - HTTP Op - POST Component Update
[ ] 9.  PROMO - HTTP Op - GET ComponentReference
[ ] 10. PROMO - HTTP Op - GET ComponentMetadata
[ ] 11. PROMO - HTTP Op - QUERY PackagedComponent
[ ] 12. PROMO - HTTP Op - POST PackagedComponent
[ ] 13. PROMO - HTTP Op - POST DeployedPackage
[ ] 14. PROMO - HTTP Op - POST IntegrationPack
[ ] 15. PROMO - HTTP Op - POST Branch
[ ] 16. PROMO - HTTP Op - QUERY Branch
[ ] 17. PROMO - HTTP Op - POST MergeRequest

Phase 2 -- DataHub Operations (6):
[ ] 18. PROMO - DH Op - Query ComponentMapping
[ ] 19. PROMO - DH Op - Update ComponentMapping
[ ] 20. PROMO - DH Op - Query DevAccountAccess
[ ] 21. PROMO - DH Op - Update DevAccountAccess
[ ] 22. PROMO - DH Op - Query PromotionLog
[ ] 23. PROMO - DH Op - Update PromotionLog

Phase 3 -- JSON Profiles (22):
[ ] 24. PROMO - Profile - GetDevAccountsRequest
[ ] 25. PROMO - Profile - GetDevAccountsResponse
[ ] 26. PROMO - Profile - ListDevPackagesRequest
[ ] 27. PROMO - Profile - ListDevPackagesResponse
[ ] 28. PROMO - Profile - ResolveDependenciesRequest
[ ] 29. PROMO - Profile - ResolveDependenciesResponse
[ ] 30. PROMO - Profile - ExecutePromotionRequest
[ ] 31. PROMO - Profile - ExecutePromotionResponse
[ ] 32. PROMO - Profile - PackageAndDeployRequest
[ ] 33. PROMO - Profile - PackageAndDeployResponse
[ ] 34. PROMO - Profile - QueryStatusRequest
[ ] 35. PROMO - Profile - QueryStatusResponse
[ ] 36. PROMO - Profile - ManageMappingsRequest
[ ] 37. PROMO - Profile - ManageMappingsResponse
[ ] 38. PROMO - Profile - QueryPeerReviewQueueRequest
[ ] 39. PROMO - Profile - QueryPeerReviewQueueResponse
[ ] 40. PROMO - Profile - SubmitPeerReviewRequest
[ ] 41. PROMO - Profile - SubmitPeerReviewResponse
[ ] 42. PROMO - Profile - ListIntegrationPacksRequest
[ ] 43. PROMO - Profile - ListIntegrationPacksResponse
[ ] 44. PROMO - Profile - GenerateComponentDiffRequest
[ ] 45. PROMO - Profile - GenerateComponentDiffResponse

Phase 3 -- Integration Processes (11):
[ ] 46. PROMO - Get Dev Accounts
[ ] 47. PROMO - List Dev Packages
[ ] 48. PROMO - Resolve Dependencies
[ ] 49. PROMO - Execute Promotion
[ ] 50. PROMO - Package and Deploy
[ ] 51. PROMO - Query Status
[ ] 52. PROMO - Mapping CRUD
[ ] 53. PROMO - Query Peer Review Queue
[ ] 54. PROMO - Submit Peer Review
[ ] 55. PROMO - List Integration Packs
[ ] 56. PROMO - Generate Component Diff

Phase 4 -- Flow Service Components (12):
[ ] 57. PROMO - FSS Op - GetDevAccounts
[ ] 58. PROMO - FSS Op - ListDevPackages
[ ] 59. PROMO - FSS Op - ResolveDependencies
[ ] 60. PROMO - FSS Op - ExecutePromotion
[ ] 61. PROMO - FSS Op - PackageAndDeploy
[ ] 62. PROMO - FSS Op - QueryStatus
[ ] 63. PROMO - FSS Op - ManageMappings
[ ] 64. PROMO - FSS Op - QueryPeerReviewQueue
[ ] 65. PROMO - FSS Op - SubmitPeerReview
[ ] 66. PROMO - FSS Op - ListIntegrationPacks
[ ] 67. PROMO - FSS Op - GenerateComponentDiff
[ ] 68. PROMO - Flow Service

Phase 5 -- Flow Dashboard (3):
[ ] 69. XmlDiffViewer (Custom Component)
[ ] 70. Promotion Service Connector
[ ] 71. Promotion Dashboard
```

---

---
Prev: [Troubleshooting](18-troubleshooting.md) | Next: [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | [Back to Index](index.md)

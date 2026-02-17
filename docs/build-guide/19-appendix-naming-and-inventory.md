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

### Complete 78-Component Inventory Checklist

```
Phase 1 -- DataHub Models (3):
[ ] 1. ComponentMapping
[ ] 2. DevAccountAccess
[ ] 3. PromotionLog

Phase 2 -- Connections (2):
[ ] 4. PROMO - Partner API Connection
[ ] 5. PROMO - DataHub Connection

Phase 2 -- HTTP Client Operations (19):
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
[ ] 18. PROMO - HTTP Op - POST MergeRequest Execute
[ ] 19. PROMO - HTTP Op - GET Branch
[ ] 20. PROMO - HTTP Op - DELETE Branch
[ ] 21. PROMO - HTTP Op - QUERY IntegrationPack
[ ] 22. PROMO - HTTP Op - POST Add To IntegrationPack
[ ] 23. PROMO - HTTP Op - POST ReleaseIntegrationPack
[ ] 24. PROMO - HTTP Op - GET MergeRequest

Phase 2 -- DataHub Operations (6):
[ ] 25. PROMO - DH Op - Query ComponentMapping
[ ] 26. PROMO - DH Op - Update ComponentMapping
[ ] 27. PROMO - DH Op - Query DevAccountAccess
[ ] 28. PROMO - DH Op - Update DevAccountAccess
[ ] 29. PROMO - DH Op - Query PromotionLog
[ ] 30. PROMO - DH Op - Update PromotionLog

Phase 3 -- JSON Profiles (22):
[ ] 31. PROMO - Profile - GetDevAccountsRequest
[ ] 32. PROMO - Profile - GetDevAccountsResponse
[ ] 33. PROMO - Profile - ListDevPackagesRequest
[ ] 34. PROMO - Profile - ListDevPackagesResponse
[ ] 35. PROMO - Profile - ResolveDependenciesRequest
[ ] 36. PROMO - Profile - ResolveDependenciesResponse
[ ] 37. PROMO - Profile - ExecutePromotionRequest
[ ] 38. PROMO - Profile - ExecutePromotionResponse
[ ] 39. PROMO - Profile - PackageAndDeployRequest
[ ] 40. PROMO - Profile - PackageAndDeployResponse
[ ] 41. PROMO - Profile - QueryStatusRequest
[ ] 42. PROMO - Profile - QueryStatusResponse
[ ] 43. PROMO - Profile - ManageMappingsRequest
[ ] 44. PROMO - Profile - ManageMappingsResponse
[ ] 45. PROMO - Profile - QueryPeerReviewQueueRequest
[ ] 46. PROMO - Profile - QueryPeerReviewQueueResponse
[ ] 47. PROMO - Profile - SubmitPeerReviewRequest
[ ] 48. PROMO - Profile - SubmitPeerReviewResponse
[ ] 49. PROMO - Profile - ListIntegrationPacksRequest
[ ] 50. PROMO - Profile - ListIntegrationPacksResponse
[ ] 51. PROMO - Profile - GenerateComponentDiffRequest
[ ] 52. PROMO - Profile - GenerateComponentDiffResponse

Phase 3 -- Integration Processes (11):
[ ] 53. PROMO - Get Dev Accounts
[ ] 54. PROMO - List Dev Packages
[ ] 55. PROMO - Resolve Dependencies
[ ] 56. PROMO - Execute Promotion
[ ] 57. PROMO - Package and Deploy
[ ] 58. PROMO - Query Status
[ ] 59. PROMO - Mapping CRUD
[ ] 60. PROMO - Query Peer Review Queue
[ ] 61. PROMO - Submit Peer Review
[ ] 62. PROMO - List Integration Packs
[ ] 63. PROMO - Generate Component Diff

Phase 4 -- Flow Service Components (12):
[ ] 64. PROMO - FSS Op - GetDevAccounts
[ ] 65. PROMO - FSS Op - ListDevPackages
[ ] 66. PROMO - FSS Op - ResolveDependencies
[ ] 67. PROMO - FSS Op - ExecutePromotion
[ ] 68. PROMO - FSS Op - PackageAndDeploy
[ ] 69. PROMO - FSS Op - QueryStatus
[ ] 70. PROMO - FSS Op - ManageMappings
[ ] 71. PROMO - FSS Op - QueryPeerReviewQueue
[ ] 72. PROMO - FSS Op - SubmitPeerReview
[ ] 73. PROMO - FSS Op - ListIntegrationPacks
[ ] 74. PROMO - FSS Op - GenerateComponentDiff
[ ] 75. PROMO - Flow Service

Phase 5 -- Flow Dashboard (3):
[ ] 76. XmlDiffViewer (Custom Component)
[ ] 77. Promotion Service Connector
[ ] 78. Promotion Dashboard
```

---

---
Prev: [Troubleshooting](18-troubleshooting.md) | Next: [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | [Back to Index](index.md)

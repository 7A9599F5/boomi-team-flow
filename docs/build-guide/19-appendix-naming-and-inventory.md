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

### Complete 124-Component Inventory Checklist

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

Phase 3 -- JSON Profiles (28):
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
[ ] 53. PROMO - Profile - QueryTestDeploymentsRequest
[ ] 54. PROMO - Profile - QueryTestDeploymentsResponse
[ ] 55. PROMO - Profile - CancelTestDeploymentRequest
[ ] 56. PROMO - Profile - CancelTestDeploymentResponse
[ ] 57. PROMO - Profile - WithdrawPromotionRequest
[ ] 58. PROMO - Profile - WithdrawPromotionResponse

Phase 3 -- Integration Processes (13):
[ ] 59. PROMO - Get Dev Accounts
[ ] 60. PROMO - List Dev Packages
[ ] 61. PROMO - Resolve Dependencies
[ ] 62. PROMO - Execute Promotion
[ ] 63. PROMO - Package and Deploy
[ ] 64. PROMO - Query Status
[ ] 65. PROMO - Mapping CRUD
[ ] 66. PROMO - Query Peer Review Queue
[ ] 67. PROMO - Submit Peer Review
[ ] 68. PROMO - List Integration Packs
[ ] 69. PROMO - Generate Component Diff
[ ] 70. PROMO - Query Test Deployments
[ ] 71. PROMO - Withdraw Promotion

Phase 4 -- FSS Operations + Flow Service (15):
[ ] 72. PROMO - FSS Op - GetDevAccounts
[ ] 73. PROMO - FSS Op - ListDevPackages
[ ] 74. PROMO - FSS Op - ResolveDependencies
[ ] 75. PROMO - FSS Op - ExecutePromotion
[ ] 76. PROMO - FSS Op - PackageAndDeploy
[ ] 77. PROMO - FSS Op - QueryStatus
[ ] 78. PROMO - FSS Op - ManageMappings
[ ] 79. PROMO - FSS Op - QueryPeerReviewQueue
[ ] 80. PROMO - FSS Op - SubmitPeerReview
[ ] 81. PROMO - FSS Op - ListIntegrationPacks
[ ] 82. PROMO - FSS Op - GenerateComponentDiff
[ ] 83. PROMO - FSS Op - QueryTestDeployments
[ ] 84. PROMO - FSS Op - CancelTestDeployment
[ ] 85. PROMO - FSS Op - WithdrawPromotion
[ ] 86. PROMO - Flow Service

Phase 5 -- Flow Dashboard (3):
[ ] 87. XmlDiffViewer (Custom Component)
[ ] 88. Promotion Service Connector
[ ] 89. Promotion Dashboard

Phase 7 -- DataHub Models (+2):
[ ] 90. ExtensionAccessMapping
[ ] 91. ClientAccountConfig

Phase 7 -- HTTP Client Operations (+8):
[ ] 92.  PROMO - HTTP Op - QUERY Account
[ ] 93.  PROMO - HTTP Op - QUERY Environment
[ ] 94.  PROMO - HTTP Op - GET EnvironmentExtensions
[ ] 95.  PROMO - HTTP Op - UPDATE EnvironmentExtensions
[ ] 96.  PROMO - HTTP Op - QUERY EnvironmentMapExtensionsSummary
[ ] 97.  PROMO - HTTP Op - GET EnvironmentMapExtension
[ ] 98.  PROMO - HTTP Op - UPDATE EnvironmentMapExtension
[ ] 99.  PROMO - HTTP Op - QUERY ComponentReference

Phase 7 -- DataHub Operations (+4):
[ ] 100. PROMO - DH Op - Query ExtensionAccessMapping
[ ] 101. PROMO - DH Op - Upsert ExtensionAccessMapping
[ ] 102. PROMO - DH Op - Query ClientAccountConfig
[ ] 103. PROMO - DH Op - Upsert ClientAccountConfig

Phase 7 -- JSON Profiles (+10):
[ ] 104. PROMO - Profile - ListClientAccountsRequest
[ ] 105. PROMO - Profile - ListClientAccountsResponse
[ ] 106. PROMO - Profile - GetExtensionsRequest
[ ] 107. PROMO - Profile - GetExtensionsResponse
[ ] 108. PROMO - Profile - UpdateExtensionsRequest
[ ] 109. PROMO - Profile - UpdateExtensionsResponse
[ ] 110. PROMO - Profile - CopyExtensionsTestToProdRequest
[ ] 111. PROMO - Profile - CopyExtensionsTestToProdResponse
[ ] 112. PROMO - Profile - UpdateMapExtensionRequest
[ ] 113. PROMO - Profile - UpdateMapExtensionResponse

Phase 7 -- Integration Processes (+5):
[ ] 114. PROMO - List Client Accounts
[ ] 115. PROMO - Get Extensions
[ ] 116. PROMO - Update Extensions
[ ] 117. PROMO - Copy Extensions Test to Prod
[ ] 118. PROMO - Update Map Extension

Phase 7 -- FSS Operations (+5):
[ ] 119. PROMO - FSS Op - ListClientAccounts
[ ] 120. PROMO - FSS Op - GetExtensions
[ ] 121. PROMO - FSS Op - UpdateExtensions
[ ] 122. PROMO - FSS Op - CopyExtensionsTestToProd
[ ] 123. PROMO - FSS Op - UpdateMapExtension

Phase 7 -- Custom Component (+1):
[ ] 124. ExtensionEditor
```

---

---
Prev: [Troubleshooting](18-troubleshooting.md) | Next: [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | [Back to Index](index.md)

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

### Complete 129-Component Inventory Checklist

```
Phase 1 -- DataHub Models (3):
[ ] 1. ComponentMapping
[ ] 2. DevAccountAccess
[ ] 3. PromotionLog

Phase 2 -- Connections (2):
[ ] 4. PROMO - Partner API Connection
[ ] 5. PROMO - DataHub Connection

Phase 2 -- HTTP Client Operations (20):
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
[ ] 25. PROMO - HTTP Op - GET IntegrationPack

Phase 2 -- DataHub Operations (6):
[ ] 26. PROMO - DH Op - Query ComponentMapping
[ ] 27. PROMO - DH Op - Update ComponentMapping
[ ] 28. PROMO - DH Op - Query DevAccountAccess
[ ] 29. PROMO - DH Op - Update DevAccountAccess
[ ] 30. PROMO - DH Op - Query PromotionLog
[ ] 31. PROMO - DH Op - Update PromotionLog

Phase 3 -- JSON Profiles (28):
[ ] 32. PROMO - Profile - GetDevAccountsRequest
[ ] 33. PROMO - Profile - GetDevAccountsResponse
[ ] 34. PROMO - Profile - ListDevPackagesRequest
[ ] 35. PROMO - Profile - ListDevPackagesResponse
[ ] 36. PROMO - Profile - ResolveDependenciesRequest
[ ] 37. PROMO - Profile - ResolveDependenciesResponse
[ ] 38. PROMO - Profile - ExecutePromotionRequest
[ ] 39. PROMO - Profile - ExecutePromotionResponse
[ ] 40. PROMO - Profile - PackageAndDeployRequest
[ ] 41. PROMO - Profile - PackageAndDeployResponse
[ ] 42. PROMO - Profile - QueryStatusRequest
[ ] 43. PROMO - Profile - QueryStatusResponse
[ ] 44. PROMO - Profile - ManageMappingsRequest
[ ] 45. PROMO - Profile - ManageMappingsResponse
[ ] 46. PROMO - Profile - QueryPeerReviewQueueRequest
[ ] 47. PROMO - Profile - QueryPeerReviewQueueResponse
[ ] 48. PROMO - Profile - SubmitPeerReviewRequest
[ ] 49. PROMO - Profile - SubmitPeerReviewResponse
[ ] 50. PROMO - Profile - ListIntegrationPacksRequest
[ ] 51. PROMO - Profile - ListIntegrationPacksResponse
[ ] 52. PROMO - Profile - GenerateComponentDiffRequest
[ ] 53. PROMO - Profile - GenerateComponentDiffResponse
[ ] 54. PROMO - Profile - QueryTestDeploymentsRequest
[ ] 55. PROMO - Profile - QueryTestDeploymentsResponse
[ ] 56. PROMO - Profile - CancelTestDeploymentRequest
[ ] 57. PROMO - Profile - CancelTestDeploymentResponse
[ ] 58. PROMO - Profile - WithdrawPromotionRequest
[ ] 59. PROMO - Profile - WithdrawPromotionResponse

Phase 3 -- Integration Processes (13):
[ ] 60. PROMO - Get Dev Accounts
[ ] 61. PROMO - List Dev Packages
[ ] 62. PROMO - Resolve Dependencies
[ ] 63. PROMO - Execute Promotion
[ ] 64. PROMO - Package and Deploy
[ ] 65. PROMO - Query Status
[ ] 66. PROMO - Mapping CRUD
[ ] 67. PROMO - Query Peer Review Queue
[ ] 68. PROMO - Submit Peer Review
[ ] 69. PROMO - List Integration Packs
[ ] 70. PROMO - Generate Component Diff
[ ] 71. PROMO - Query Test Deployments
[ ] 72. PROMO - Withdraw Promotion

Phase 4 -- FSS Operations + Flow Service (15):
[ ] 73. PROMO - FSS Op - GetDevAccounts
[ ] 74. PROMO - FSS Op - ListDevPackages
[ ] 75. PROMO - FSS Op - ResolveDependencies
[ ] 76. PROMO - FSS Op - ExecutePromotion
[ ] 77. PROMO - FSS Op - PackageAndDeploy
[ ] 78. PROMO - FSS Op - QueryStatus
[ ] 79. PROMO - FSS Op - ManageMappings
[ ] 80. PROMO - FSS Op - QueryPeerReviewQueue
[ ] 81. PROMO - FSS Op - SubmitPeerReview
[ ] 82. PROMO - FSS Op - ListIntegrationPacks
[ ] 83. PROMO - FSS Op - GenerateComponentDiff
[ ] 84. PROMO - FSS Op - QueryTestDeployments
[ ] 85. PROMO - FSS Op - CancelTestDeployment
[ ] 86. PROMO - FSS Op - WithdrawPromotion
[ ] 87. PROMO - Flow Service

Phase 5 -- Flow Dashboard (3):
[ ] 88. XmlDiffViewer (Custom Component)
[ ] 89. Promotion Service Connector
[ ] 90. Promotion Dashboard

Phase 7 -- DataHub Models (+2):
[ ] 91. ExtensionAccessMapping
[ ] 92. ClientAccountConfig

Phase 7 -- HTTP Client Operations (+8):
[ ] 93.  PROMO - HTTP Op - QUERY Account
[ ] 94.  PROMO - HTTP Op - QUERY Environment
[ ] 95.  PROMO - HTTP Op - GET EnvironmentExtensions
[ ] 96.  PROMO - HTTP Op - UPDATE EnvironmentExtensions
[ ] 97.  PROMO - HTTP Op - QUERY EnvironmentMapExtensionsSummary
[ ] 98.  PROMO - HTTP Op - GET EnvironmentMapExtension
[ ] 99.  PROMO - HTTP Op - UPDATE EnvironmentMapExtension
[ ] 100. PROMO - HTTP Op - QUERY ComponentReference

Phase 7 -- DataHub Operations (+4):
[ ] 101. PROMO - DH Op - Query ExtensionAccessMapping
[ ] 102. PROMO - DH Op - Upsert ExtensionAccessMapping
[ ] 103. PROMO - DH Op - Query ClientAccountConfig
[ ] 104. PROMO - DH Op - Upsert ClientAccountConfig

Phase 7 -- JSON Profiles (+10):
[ ] 105. PROMO - Profile - ListClientAccountsRequest
[ ] 106. PROMO - Profile - ListClientAccountsResponse
[ ] 107. PROMO - Profile - GetExtensionsRequest
[ ] 108. PROMO - Profile - GetExtensionsResponse
[ ] 109. PROMO - Profile - UpdateExtensionsRequest
[ ] 110. PROMO - Profile - UpdateExtensionsResponse
[ ] 111. PROMO - Profile - CopyExtensionsTestToProdRequest
[ ] 112. PROMO - Profile - CopyExtensionsTestToProdResponse
[ ] 113. PROMO - Profile - UpdateMapExtensionRequest
[ ] 114. PROMO - Profile - UpdateMapExtensionResponse

Phase 7 -- Integration Processes (+5):
[ ] 115. PROMO - List Client Accounts
[ ] 116. PROMO - Get Extensions
[ ] 117. PROMO - Update Extensions
[ ] 118. PROMO - Copy Extensions Test to Prod
[ ] 119. PROMO - Update Map Extension

Phase 7 -- FSS Operations (+5):
[ ] 120. PROMO - FSS Op - ListClientAccounts
[ ] 121. PROMO - FSS Op - GetExtensions
[ ] 122. PROMO - FSS Op - UpdateExtensions
[ ] 123. PROMO - FSS Op - CopyExtensionsTestToProd
[ ] 124. PROMO - FSS Op - UpdateMapExtension

Phase 7 -- Custom Component (+1):
[ ] 125. ExtensionEditor
```

---

---
Prev: [Troubleshooting](18-troubleshooting.md) | Next: [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | [Back to Index](index.md)

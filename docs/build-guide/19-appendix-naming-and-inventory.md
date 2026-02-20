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

### Complete 134-Component Inventory Checklist

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

Phase 2 -- DataHub Operations (7):
[ ] 26. PROMO - DH Op - Query ComponentMapping
[ ] 27. PROMO - DH Op - Update ComponentMapping
[ ] 28. PROMO - DH Op - Delete ComponentMapping
[ ] 29. PROMO - DH Op - Query DevAccountAccess
[ ] 30. PROMO - DH Op - Update DevAccountAccess
[ ] 31. PROMO - DH Op - Query PromotionLog
[ ] 32. PROMO - DH Op - Update PromotionLog

Phase 3 -- JSON Profiles (30):
[ ] 33. PROMO - Profile - GetDevAccountsRequest
[ ] 34. PROMO - Profile - GetDevAccountsResponse
[ ] 35. PROMO - Profile - ListDevPackagesRequest
[ ] 36. PROMO - Profile - ListDevPackagesResponse
[ ] 37. PROMO - Profile - ResolveDependenciesRequest
[ ] 38. PROMO - Profile - ResolveDependenciesResponse
[ ] 39. PROMO - Profile - ExecutePromotionRequest
[ ] 40. PROMO - Profile - ExecutePromotionResponse
[ ] 41. PROMO - Profile - PackageAndDeployRequest
[ ] 42. PROMO - Profile - PackageAndDeployResponse
[ ] 43. PROMO - Profile - QueryStatusRequest
[ ] 44. PROMO - Profile - QueryStatusResponse
[ ] 45. PROMO - Profile - ManageMappingsRequest
[ ] 46. PROMO - Profile - ManageMappingsResponse
[ ] 47. PROMO - Profile - QueryPeerReviewQueueRequest
[ ] 48. PROMO - Profile - QueryPeerReviewQueueResponse
[ ] 49. PROMO - Profile - SubmitPeerReviewRequest
[ ] 50. PROMO - Profile - SubmitPeerReviewResponse
[ ] 51. PROMO - Profile - ListIntegrationPacksRequest
[ ] 52. PROMO - Profile - ListIntegrationPacksResponse
[ ] 53. PROMO - Profile - GenerateComponentDiffRequest
[ ] 54. PROMO - Profile - GenerateComponentDiffResponse
[ ] 55. PROMO - Profile - QueryTestDeploymentsRequest
[ ] 56. PROMO - Profile - QueryTestDeploymentsResponse
[ ] 57. PROMO - Profile - CancelTestDeploymentRequest
[ ] 58. PROMO - Profile - CancelTestDeploymentResponse
[ ] 59. PROMO - Profile - WithdrawPromotionRequest
[ ] 60. PROMO - Profile - WithdrawPromotionResponse
[ ] 61. PROMO - Profile - CheckReleaseStatusRequest
[ ] 62. PROMO - Profile - CheckReleaseStatusResponse

Phase 3 -- Integration Processes (14):
[ ] 63. PROMO - Get Dev Accounts
[ ] 64. PROMO - List Dev Packages
[ ] 65. PROMO - Resolve Dependencies
[ ] 66. PROMO - Execute Promotion
[ ] 67. PROMO - Package and Deploy
[ ] 68. PROMO - Query Status
[ ] 69. PROMO - Mapping CRUD
[ ] 70. PROMO - Query Peer Review Queue
[ ] 71. PROMO - Submit Peer Review
[ ] 72. PROMO - List Integration Packs
[ ] 73. PROMO - Generate Component Diff
[ ] 74. PROMO - Query Test Deployments
[ ] 75. PROMO - Withdraw Promotion
[ ] 76. PROMO - Check Release Status

Phase 4 -- FSS Operations + Flow Service (16):
[ ] 77. PROMO - FSS Op - GetDevAccounts
[ ] 78. PROMO - FSS Op - ListDevPackages
[ ] 79. PROMO - FSS Op - ResolveDependencies
[ ] 80. PROMO - FSS Op - ExecutePromotion
[ ] 81. PROMO - FSS Op - PackageAndDeploy
[ ] 82. PROMO - FSS Op - QueryStatus
[ ] 83. PROMO - FSS Op - ManageMappings
[ ] 84. PROMO - FSS Op - QueryPeerReviewQueue
[ ] 85. PROMO - FSS Op - SubmitPeerReview
[ ] 86. PROMO - FSS Op - ListIntegrationPacks
[ ] 87. PROMO - FSS Op - GenerateComponentDiff
[ ] 88. PROMO - FSS Op - QueryTestDeployments
[ ] 89. PROMO - FSS Op - CancelTestDeployment
[ ] 90. PROMO - FSS Op - WithdrawPromotion
[ ] 91. PROMO - FSS Op - CheckReleaseStatus
[ ] 92. PROMO - Flow Service

Phase 5 -- Flow Dashboard (3):
[ ] 93. XmlDiffViewer (Custom Component)
[ ] 94. Promotion Service Connector
[ ] 95. Promotion Dashboard

Phase 7 -- DataHub Models (+2):
[ ] 96. ExtensionAccessMapping
[ ] 97. ClientAccountConfig

Phase 7 -- HTTP Client Operations (+8):
[ ] 98.  PROMO - HTTP Op - QUERY Account
[ ] 99.  PROMO - HTTP Op - QUERY Environment
[ ] 100. PROMO - HTTP Op - GET EnvironmentExtensions
[ ] 101. PROMO - HTTP Op - UPDATE EnvironmentExtensions
[ ] 102. PROMO - HTTP Op - QUERY EnvironmentMapExtensionsSummary
[ ] 103. PROMO - HTTP Op - GET EnvironmentMapExtension
[ ] 104. PROMO - HTTP Op - UPDATE EnvironmentMapExtension
[ ] 105. PROMO - HTTP Op - QUERY ComponentReference

Phase 7 -- DataHub Operations (+4):
[ ] 106. PROMO - DH Op - Query ExtensionAccessMapping
[ ] 107. PROMO - DH Op - Update ExtensionAccessMapping
[ ] 108. PROMO - DH Op - Query ClientAccountConfig
[ ] 109. PROMO - DH Op - Update ClientAccountConfig

Phase 7 -- JSON Profiles (+10):
[ ] 110. PROMO - Profile - ListClientAccountsRequest
[ ] 111. PROMO - Profile - ListClientAccountsResponse
[ ] 112. PROMO - Profile - GetExtensionsRequest
[ ] 113. PROMO - Profile - GetExtensionsResponse
[ ] 114. PROMO - Profile - UpdateExtensionsRequest
[ ] 115. PROMO - Profile - UpdateExtensionsResponse
[ ] 116. PROMO - Profile - CopyExtensionsTestToProdRequest
[ ] 117. PROMO - Profile - CopyExtensionsTestToProdResponse
[ ] 118. PROMO - Profile - UpdateMapExtensionRequest
[ ] 119. PROMO - Profile - UpdateMapExtensionResponse

Phase 7 -- Integration Processes (+5):
[ ] 120. PROMO - List Client Accounts
[ ] 121. PROMO - Get Extensions
[ ] 122. PROMO - Update Extensions
[ ] 123. PROMO - Copy Extensions Test to Prod
[ ] 124. PROMO - Update Map Extension

Phase 7 -- FSS Operations (+5):
[ ] 125. PROMO - FSS Op - ListClientAccounts
[ ] 126. PROMO - FSS Op - GetExtensions
[ ] 127. PROMO - FSS Op - UpdateExtensions
[ ] 128. PROMO - FSS Op - CopyExtensionsTestToProd
[ ] 129. PROMO - FSS Op - UpdateMapExtension

Phase 7 -- JSON Profiles (+2, validateScript):
[ ] 130. PROMO - Profile - ValidateScriptRequest
[ ] 131. PROMO - Profile - ValidateScriptResponse

Phase 7 -- Integration Process (+1, validateScript):
[ ] 132. PROMO - Validate Script

Phase 7 -- FSS Operation (+1, validateScript):
[ ] 133. PROMO - FSS Op - ValidateScript

Phase 7 -- Custom Component (+1):
[ ] 134. ExtensionEditor
```

---

---
Prev: [Troubleshooting](18-troubleshooting.md) | Next: [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | [Back to Index](index.md)

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

### Complete 135-Component Inventory Checklist

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

Phase 2 -- DataHub Operations (8):
[ ] 26. PROMO - DH Op - Query ComponentMapping
[ ] 27. PROMO - DH Op - Update ComponentMapping
[ ] 28. PROMO - DH Op - Delete ComponentMapping
[ ] 29. PROMO - DH Op - Query DevAccountAccess
[ ] 30. PROMO - DH Op - Update DevAccountAccess
[ ] 31. PROMO - DH Op - Query PromotionLog
[ ] 32. PROMO - DH Op - Update PromotionLog
[ ] 33. PROMO - DH Op - Delete PromotionLog

Phase 3 -- JSON Profiles (30):
[ ] 34. PROMO - Profile - GetDevAccountsRequest
[ ] 35. PROMO - Profile - GetDevAccountsResponse
[ ] 36. PROMO - Profile - ListDevPackagesRequest
[ ] 37. PROMO - Profile - ListDevPackagesResponse
[ ] 38. PROMO - Profile - ResolveDependenciesRequest
[ ] 39. PROMO - Profile - ResolveDependenciesResponse
[ ] 40. PROMO - Profile - ExecutePromotionRequest
[ ] 41. PROMO - Profile - ExecutePromotionResponse
[ ] 42. PROMO - Profile - PackageAndDeployRequest
[ ] 43. PROMO - Profile - PackageAndDeployResponse
[ ] 44. PROMO - Profile - QueryStatusRequest
[ ] 45. PROMO - Profile - QueryStatusResponse
[ ] 46. PROMO - Profile - ManageMappingsRequest
[ ] 47. PROMO - Profile - ManageMappingsResponse
[ ] 48. PROMO - Profile - QueryPeerReviewQueueRequest
[ ] 49. PROMO - Profile - QueryPeerReviewQueueResponse
[ ] 50. PROMO - Profile - SubmitPeerReviewRequest
[ ] 51. PROMO - Profile - SubmitPeerReviewResponse
[ ] 52. PROMO - Profile - ListIntegrationPacksRequest
[ ] 53. PROMO - Profile - ListIntegrationPacksResponse
[ ] 54. PROMO - Profile - GenerateComponentDiffRequest
[ ] 55. PROMO - Profile - GenerateComponentDiffResponse
[ ] 56. PROMO - Profile - QueryTestDeploymentsRequest
[ ] 57. PROMO - Profile - QueryTestDeploymentsResponse
[ ] 58. PROMO - Profile - CancelTestDeploymentRequest
[ ] 59. PROMO - Profile - CancelTestDeploymentResponse
[ ] 60. PROMO - Profile - WithdrawPromotionRequest
[ ] 61. PROMO - Profile - WithdrawPromotionResponse
[ ] 62. PROMO - Profile - CheckReleaseStatusRequest
[ ] 63. PROMO - Profile - CheckReleaseStatusResponse

Phase 3 -- Integration Processes (14):
[ ] 64. PROMO - Get Dev Accounts
[ ] 65. PROMO - List Dev Packages
[ ] 66. PROMO - Resolve Dependencies
[ ] 67. PROMO - Execute Promotion
[ ] 68. PROMO - Package and Deploy
[ ] 69. PROMO - Query Status
[ ] 70. PROMO - Mapping CRUD
[ ] 71. PROMO - Query Peer Review Queue
[ ] 72. PROMO - Submit Peer Review
[ ] 73. PROMO - List Integration Packs
[ ] 74. PROMO - Generate Component Diff
[ ] 75. PROMO - Query Test Deployments
[ ] 76. PROMO - Withdraw Promotion
[ ] 77. PROMO - Check Release Status

Phase 4 -- FSS Operations + Flow Service (16):
[ ] 78. PROMO - FSS Op - GetDevAccounts
[ ] 79. PROMO - FSS Op - ListDevPackages
[ ] 80. PROMO - FSS Op - ResolveDependencies
[ ] 81. PROMO - FSS Op - ExecutePromotion
[ ] 82. PROMO - FSS Op - PackageAndDeploy
[ ] 83. PROMO - FSS Op - QueryStatus
[ ] 84. PROMO - FSS Op - ManageMappings
[ ] 85. PROMO - FSS Op - QueryPeerReviewQueue
[ ] 86. PROMO - FSS Op - SubmitPeerReview
[ ] 87. PROMO - FSS Op - ListIntegrationPacks
[ ] 88. PROMO - FSS Op - GenerateComponentDiff
[ ] 89. PROMO - FSS Op - QueryTestDeployments
[ ] 90. PROMO - FSS Op - CancelTestDeployment
[ ] 91. PROMO - FSS Op - WithdrawPromotion
[ ] 92. PROMO - FSS Op - CheckReleaseStatus
[ ] 93. PROMO - Flow Service

Phase 5 -- Flow Dashboard (3):
[ ] 94. XmlDiffViewer (Custom Component)
[ ] 95. Promotion Service Connector
[ ] 96. Promotion Dashboard

Phase 7 -- DataHub Models (+2):
[ ] 97. ExtensionAccessMapping
[ ] 98. ClientAccountConfig

Phase 7 -- HTTP Client Operations (+8):
[ ] 99.  PROMO - HTTP Op - QUERY Account
[ ] 100. PROMO - HTTP Op - QUERY Environment
[ ] 101. PROMO - HTTP Op - GET EnvironmentExtensions
[ ] 102. PROMO - HTTP Op - UPDATE EnvironmentExtensions
[ ] 103. PROMO - HTTP Op - QUERY EnvironmentMapExtensionsSummary
[ ] 104. PROMO - HTTP Op - GET EnvironmentMapExtension
[ ] 105. PROMO - HTTP Op - UPDATE EnvironmentMapExtension
[ ] 106. PROMO - HTTP Op - QUERY ComponentReference

Phase 7 -- DataHub Operations (+4):
[ ] 107. PROMO - DH Op - Query ExtensionAccessMapping
[ ] 108. PROMO - DH Op - Update ExtensionAccessMapping
[ ] 109. PROMO - DH Op - Query ClientAccountConfig
[ ] 110. PROMO - DH Op - Update ClientAccountConfig

Phase 7 -- JSON Profiles (+10):
[ ] 111. PROMO - Profile - ListClientAccountsRequest
[ ] 112. PROMO - Profile - ListClientAccountsResponse
[ ] 113. PROMO - Profile - GetExtensionsRequest
[ ] 114. PROMO - Profile - GetExtensionsResponse
[ ] 115. PROMO - Profile - UpdateExtensionsRequest
[ ] 116. PROMO - Profile - UpdateExtensionsResponse
[ ] 117. PROMO - Profile - CopyExtensionsTestToProdRequest
[ ] 118. PROMO - Profile - CopyExtensionsTestToProdResponse
[ ] 119. PROMO - Profile - UpdateMapExtensionRequest
[ ] 120. PROMO - Profile - UpdateMapExtensionResponse

Phase 7 -- Integration Processes (+5):
[ ] 121. PROMO - List Client Accounts
[ ] 122. PROMO - Get Extensions
[ ] 123. PROMO - Update Extensions
[ ] 124. PROMO - Copy Extensions Test to Prod
[ ] 125. PROMO - Update Map Extension

Phase 7 -- FSS Operations (+5):
[ ] 126. PROMO - FSS Op - ListClientAccounts
[ ] 127. PROMO - FSS Op - GetExtensions
[ ] 128. PROMO - FSS Op - UpdateExtensions
[ ] 129. PROMO - FSS Op - CopyExtensionsTestToProd
[ ] 130. PROMO - FSS Op - UpdateMapExtension

Phase 7 -- JSON Profiles (+2, validateScript):
[ ] 131. PROMO - Profile - ValidateScriptRequest
[ ] 132. PROMO - Profile - ValidateScriptResponse

Phase 7 -- Integration Process (+1, validateScript):
[ ] 133. PROMO - Validate Script

Phase 7 -- FSS Operation (+1, validateScript):
[ ] 134. PROMO - FSS Op - ValidateScript

Phase 7 -- Custom Component (+1):
[ ] 135. ExtensionEditor
```

---

---
Prev: [Troubleshooting](18-troubleshooting.md) | Next: [Appendix B: DPP Catalog](20-appendix-dpp-catalog.md) | [Back to Index](index.md)

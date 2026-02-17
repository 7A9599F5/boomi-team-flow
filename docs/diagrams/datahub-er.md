# DataHub Entity Relationship Diagram

> Referenced from [`architecture.md`](../architecture.md). See model specs in [`datahub/models/`](../../datahub/models/) for complete field definitions.

```mermaid
erDiagram
    ComponentMapping {
        string devComponentId PK "match field"
        string devAccountId PK "match field"
        string prodComponentId "prod account component ID"
        string componentName "human-readable name"
        string componentType "process, connection, map, etc."
        string mappingSource "PROMOTION_ENGINE or ADMIN_SEEDING"
        date lastPromotedAt "last promotion timestamp"
    }

    DevAccountAccess {
        string ssoGroupId PK "match field"
        string devAccountId PK "match field"
        string ssoGroupName "Azure AD display name"
        string devAccountName "human-readable account name"
        string isActive "true or false"
    }

    PromotionLog {
        string promotionId PK "match field (UUID)"
        string devAccountId "source dev account"
        string devPackageId "dev PackagedComponent ID"
        string initiatedBy "SSO user email"
        string status "IN_PROGRESS, COMPLETED, FAILED, etc."
        string targetEnvironment "TEST or PRODUCTION"
        date initiatedAt "promotion start timestamp"
        string testPromotionId "links prod record to test record"
    }

    ExtensionAccessMapping {
        string environmentId PK "match field"
        string prodComponentId PK "match field"
        string componentType "connection, operation, etc."
        string ownerProcessId "prod process using this component"
        string devAccountId "originating dev account"
        string authorizedSsoGroups "JSON array of SSO group IDs"
        string isConnectionExtension "true or false"
    }

    ClientAccountConfig {
        string clientAccountId PK "match field"
        string ssoGroupId PK "match field"
        string clientAccountName "human-readable name"
        string testEnvironmentId "Test env ID"
        string prodEnvironmentId "Production env ID"
        string isActive "true or false"
    }

    DevAccountAccess ||--o{ PromotionLog : "devAccountId"
    DevAccountAccess ||--o{ ExtensionAccessMapping : "devAccountId"
    ComponentMapping ||--o{ ExtensionAccessMapping : "prodComponentId"
    ClientAccountConfig ||--o{ ExtensionAccessMapping : "testEnvironmentId / prodEnvironmentId"
    PromotionLog ||--o| PromotionLog : "testPromotionId (prod links to test)"
```

## Legend

- **PK** fields form the match rule (unique record identity in DataHub MDM)
- Only key fields shown — see individual model specs for complete field definitions
- Relationships show logical references (not enforced foreign keys — DataHub is MDM, not RDBMS)
- Cardinality: `||--o{` = one-to-many, `||--o|` = one-to-zero-or-one

## Model Specs

| Entity | Spec File | Match Rule | Source(s) |
|--------|-----------|------------|-----------|
| ComponentMapping | [`ComponentMapping-model-spec.json`](../../datahub/models/ComponentMapping-model-spec.json) | `devComponentId` + `devAccountId` | PROMOTION_ENGINE, ADMIN_SEEDING |
| DevAccountAccess | [`DevAccountAccess-model-spec.json`](../../datahub/models/DevAccountAccess-model-spec.json) | `ssoGroupId` + `devAccountId` | ADMIN_CONFIG |
| PromotionLog | [`PromotionLog-model-spec.json`](../../datahub/models/PromotionLog-model-spec.json) | `promotionId` | PROMOTION_ENGINE |
| ExtensionAccessMapping | [`ExtensionAccessMapping-model-spec.json`](../../datahub/models/ExtensionAccessMapping-model-spec.json) | `environmentId` + `prodComponentId` | PROMOTION_ENGINE, ADMIN_SYNC |
| ClientAccountConfig | [`ClientAccountConfig-model-spec.json`](../../datahub/models/ClientAccountConfig-model-spec.json) | `clientAccountId` + `ssoGroupId` | ADMIN_CONFIG, EXTENSION_ENGINE |

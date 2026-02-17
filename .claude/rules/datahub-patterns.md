---
globs:
  - "datahub/**"
---

# DataHub Patterns

## Model Field Naming

### Standard Field Types
- **String fields**: camelCase (e.g., `devComponentId`, `componentName`)
- **Date fields**: Suffix with `Date` or `At` (e.g., `createdDate`, `promotedAt`)
- **Boolean fields**: Prefix with `is` or verb (e.g., `isDeployed`, `deployed`)
- **Integer fields**: Descriptive names (e.g., `componentCount`, `version`)

## Match Rule Field Requirements

### ComponentMapping
- **Match fields**: `devComponentId` + `devAccountId`
- Both fields MUST be included in match rule configuration
- Match rule type: EXACT

### DevAccountAccess
- **Match fields**: `ssoGroupId` + `devAccountId`
- Both fields MUST be included in match rule configuration
- Match rule type: EXACT

### PromotionLog
- **Match field**: `promotionId`
- Single field match rule
- Match rule type: EXACT

## Source Naming

### Allowed Source Values
- **PROMOTION_ENGINE** — records created by Integration processes during promotion
- **ADMIN_SEEDING** — records created manually by admins (e.g., connection mappings)
- **ADMIN_CONFIG** — records created by admins for configuration (e.g., dev account access)

### Source Field Requirements
All models MUST include a `source` field to track record origin.

## Golden Record API Request XML Format

### Standard Structure
```xml
<?xml version="1.0" encoding="UTF-8"?>
<bns:SourceRecords xmlns:bns="..." xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <bns:SourceRecord>
    <bns:ModelFieldName1>value1</bns:ModelFieldName1>
    <bns:ModelFieldName2>value2</bns:ModelFieldName2>
    ...
  </bns:SourceRecord>
</bns:SourceRecords>
```

### Required Attributes
- `xmlns:bns` must match the DataHub model namespace
- `xmlns:xsi` always set to `http://www.w3.org/2001/XMLSchema-instance`

### Field Order
- Field order in XML MUST match the model definition order
- Missing optional fields can be omitted
- Required fields MUST be present

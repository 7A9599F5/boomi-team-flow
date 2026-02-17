# Query Patterns Reference

Pagination, QueryToken, query filters, and query operators.

---

## Pagination Overview

All **QUERY** operations return a **maximum of 100 results** per response.

**Response with More Results:**
```json
{
  "@type": "QueryResult",
  "numberOfResults": 100,
  "queryToken": "EXAMPLE_QUERY_TOKEN",
  "result": [...]
}
```

**Last Page (No More Results):**
```json
{
  "@type": "QueryResult",
  "numberOfResults": 50,
  "result": [...]
}
```

**Key:** If `queryToken` is **present**, more results exist. If **absent**, last page reached.

---

## queryMore Operation

Retrieve additional results using the `queryToken`.

**Endpoint:**
```http
POST /partner/api/rest/v1/{accountId}/{ObjectType}/queryMore
```

**Request Body:**
```json
{
  "queryToken": "EXAMPLE_QUERY_TOKEN"
}
```

**Response:**
```json
{
  "@type": "QueryResult",
  "numberOfResults": 100,
  "queryToken": "NEXT_PAGE_TOKEN",
  "result": [...]
}
```

**Continue calling `queryMore` until no `queryToken` is returned.**

---

## Pagination Implementation Pattern

### JavaScript Example

```javascript
async function queryAllResults(objectType, filter) {
  let allResults = [];
  let queryToken = null;

  // Initial query
  const response1 = await query(objectType, filter);
  allResults.push(...response1.result);
  queryToken = response1.queryToken;

  // Fetch remaining pages
  while (queryToken) {
    const response = await queryMore(objectType, queryToken);
    allResults.push(...response.result);
    queryToken = response.queryToken;
  }

  return allResults;
}
```

### Groovy Example (Boomi Data Process)

```groovy
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper

def allResults = []
def queryToken = null

// Initial query
def response1 = makeQuery(filter)
def parsed1 = new JsonSlurper().parseText(response1)
allResults.addAll(parsed1.result)
queryToken = parsed1.queryToken

// Fetch remaining pages
while (queryToken) {
    def response = queryMore(queryToken)
    def parsed = new JsonSlurper().parseText(response)
    allResults.addAll(parsed.result)
    queryToken = parsed.queryToken
}

// Output all results
dataContext.storeStream(outputAllResults(allResults), props)
```

---

## Platform API Connector Auto-Pagination

**Important:** The Boomi-provided **Platform API Connector** and **Partner API Connector** automatically handle pagination.

**Behavior:**
- Returns all results regardless of count
- No need to manually call `queryMore`
- Transparent to the process

**When to Implement Manual Pagination:**
- Using HTTP Client connector (manual API calls)
- Custom integrations outside Boomi

**For This Project:**
- Use Platform API Connector for all queries
- Pagination is automatic

---

## Query Filter Structure

### Basic Query (Single Expression)

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "name",
      "argument": ["ComponentName"]
    }
  }
}
```

### Grouping Expression (AND)

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "currentVersion", "argument": ["true"]},
        {"operator": "EQUALS", "property": "deleted", "argument": ["false"]},
        {"operator": "EQUALS", "property": "componentType", "argument": ["process"]}
      ]
    }
  }
}
```

### Grouping Expression (OR)

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "or",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "componentType", "argument": ["process"]},
        {"operator": "EQUALS", "property": "componentType", "argument": ["flowservice"]}
      ]
    }
  }
}
```

### Empty Filter (All Results)

```xml
<QueryFilter xmlns='http://api.platform.boomi.com/'/>
```

Used for Branch query (no filters needed).

---

## Query Operators

| Operator | Description | Example |
|----------|-------------|---------|
| **EQUALS** | Exact match | `property: "name", argument: ["Orders"]` |
| **NOT_EQUALS** | Not equal | `property: "deleted", argument: ["true"]` |
| **LIKE** | Pattern match with wildcards | `argument: ["%Order%"]` |
| **STARTS_WITH** | Prefix match | `argument: ["Order"]` |
| **IS_NULL** | Field is null | No argument needed |
| **IS_NOT_NULL** | Field is not null | No argument needed |
| **BETWEEN** | Range (dates, numbers) | `argument: ["2024-01-01", "2024-12-31"]` |
| **GREATER_THAN** | > | `argument: ["2024-01-01"]` |
| **GREATER_THAN_OR_EQUAL** | >= | `argument: ["2024-01-01"]` |
| **LESS_THAN** | < | `argument: ["2024-12-31"]` |
| **LESS_THAN_OR_EQUAL** | <= | `argument: ["2024-12-31"]` |

---

## Common Query Patterns

### Find Current, Non-Deleted Components

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "and",
      "nestedExpression": [
        {"operator": "EQUALS", "property": "currentVersion", "argument": ["true"]},
        {"operator": "EQUALS", "property": "deleted", "argument": ["false"]}
      ]
    }
  }
}
```

**Why:**
- `currentVersion = true`: Avoids previous versions
- `deleted = false`: Avoids soft-deleted components

**Best Practice:** Always include these filters for ComponentMetadata queries.

### Find Components by Name Pattern

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "LIKE",
      "property": "name",
      "argument": ["%Order%"]
    }
  }
}
```

**Wildcards:**
- `%`: Matches zero or more characters
- `_`: Matches exactly one character

**Examples:**
- `%Order%`: Contains "Order" anywhere
- `Order%`: Starts with "Order"
- `%Order`: Ends with "Order"

### Find Components in Folder

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "folderFullPath",
      "argument": ["/DevTeamA/Orders/Process"]
    }
  }
}
```

### Find Components Created in Date Range

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "BETWEEN",
      "property": "createdDate",
      "argument": ["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"]
    }
  }
}
```

**Date Format:** ISO 8601 with timezone (`YYYY-MM-DDTHH:MM:SSZ`)

### Find Components by Type

```json
{
  "QueryFilter": {
    "expression": {
      "operator": "EQUALS",
      "property": "componentType",
      "argument": ["process"]
    }
  }
}
```

**Component Types:**
- `process`, `connection`, `connector`, `operation`, `map`, `profile`, `xslt`, `flowservice`

---

## Object-Specific Queryable Fields

### ComponentMetadata

- `componentId`, `name`, `type`, `subType`
- `folderId`, `folderName`, `folderFullPath`
- `createdDate`, `createdBy`, `modifiedDate`, `modifiedBy`
- `currentVersion` (boolean), `deleted` (boolean)
- `version` (must be paired with `componentId`)

### ComponentReference

- `parentComponentId`, `parentVersion`
- `componentId`, `type`

### PackagedComponent

- `packageId`, `componentId`, `componentType`, `packageVersion`
- `deleted`, `shareable`, `createdDate`, `createdBy`

### DeployedPackage

- `deploymentId`, `packageId`, `componentId`, `environmentId`
- `componentType`, `deployedDate`, `deployedBy`, `active`, `listenerStatus`

### IntegrationPack

- `name`, `description`, `installationType`
- `status` (`DRAFT`, `RELEASED`, `DEPLOYED`)
- `createdDate`, `createdBy`

### Branch

- `branchId`, `name`, `ready`, `createdDate`, `createdBy`

---

## Best Practices

### Query Filters

**DO:**
- ✅ Always filter `currentVersion = true` for ComponentMetadata
- ✅ Always filter `deleted = false` to avoid soft-deleted items
- ✅ Use `LIKE` for name searches (supports wildcards)
- ✅ Use `BETWEEN` for date ranges
- ✅ Use `and` operator for multiple conditions

**DON'T:**
- ❌ Query without `currentVersion` filter (gets all versions)
- ❌ Query without `deleted` filter (gets deleted components)
- ❌ Use `EQUALS` for partial name matches (use `LIKE` instead)

### Pagination

**DO:**
- ✅ Use Platform API Connector for automatic pagination
- ✅ Implement `queryMore` loop for HTTP Client
- ✅ Handle `queryToken` presence/absence correctly
- ✅ Aggregate all results before processing

**DON'T:**
- ❌ Assume first page is all results
- ❌ Ignore `queryToken` in response
- ❌ Process results incrementally (may cause state issues)

---

## Error Handling

### 400 Bad Request (Invalid Filter)

```json
{
  "@type": "Error",
  "statusCode": 400,
  "errorMessage": "Invalid query filter."
}
```

**Causes:**
- Malformed JSON structure
- Invalid operator
- Invalid property name
- Missing required fields

**Resolution:**
- Validate JSON structure
- Check operator spelling
- Verify property names against queryable fields
- Ensure `argument` is always an array

---

### 400 Bad Request (Invalid QueryToken)

```json
{
  "@type": "Error",
  "statusCode": 400,
  "errorMessage": "Invalid query token."
}
```

**Causes:**
- Expired `queryToken` (tokens have limited lifetime)
- Invalid token format
- Token from different query

**Resolution:**
- Re-run initial query (don't reuse old tokens)
- Store tokens temporarily during pagination
- Don't persist tokens across sessions

---

## Related References

- **`component-crud.md`** — ComponentMetadata and ComponentReference queries
- **`packaged-components.md`** — PackagedComponent queries
- **`integration-packs.md`** — IntegrationPack queries
- **`deployed-packages.md`** — DeployedPackage queries
- **`branch-operations.md`** — Branch queries
- **`error-handling.md`** — Error handling patterns

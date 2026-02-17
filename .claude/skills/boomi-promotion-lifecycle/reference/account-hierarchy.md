# Boomi Account Hierarchy (Parent-Child)

## Structure

```
Primary Account (Parent) — accountId: primary-123
  ├── Dev Sub-Account A (Child) — accountId: dev-team-a-456
  ├── Dev Sub-Account B (Child) — accountId: dev-team-b-789
  └── Dev Sub-Account C (Child) — accountId: dev-team-c-012
```

---

## Access Rules

- **Parent can read child data** — via Platform API with `overrideAccount` parameter
- **Child cannot read parent data** — except inherited resources (connections in `#Connections`)
- **Child cannot read sibling data** — Dev Team A cannot access Dev Team B's components

---

## overrideAccount Query Parameter

```http
GET /partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}
```

**Effect:** Fetches component from `devAccountId` instead of `primaryAccountId`.

**How It Works:**
1. Authenticate as the **primary account** (using primary account credentials)
2. Add `overrideAccount={devAccountId}` as a query parameter
3. The API executes the request **as if** you were authenticated as the dev account
4. The primary account must be in the hierarchy of the dev account (parent/child relationship)

---

## Use Cases in This Project

**Process A (listDevPackages):**
```http
POST /partner/api/rest/v1/{primaryAccountId}/PackagedComponent/query?overrideAccount={devAccountId}
```

**Process B (resolveDependencies):**
```http
POST /partner/api/rest/v1/{primaryAccountId}/ComponentReference/query?overrideAccount={devAccountId}
```

**Process C (executePromotion):**
```http
GET /partner/api/rest/v1/{primaryAccountId}/Component/{componentId}?overrideAccount={devAccountId}
```

---

## Resource Inheritance

### What Children Inherit from Parent

- Connections in parent's `#Connections` folder (visible to child processes)
- Shared libraries and JAR files
- Atoms and Molecules (if configured for inheritance)

### What Children Do NOT Inherit

- Processes, maps, profiles, operations (these are account-specific)
- DataHub models (each account has its own DataHub instance)

---

## Partner API Scope

### Enablement

- Partner API must be enabled on the **parent account**
- Child accounts do not need Partner API enabled (accessed via parent)

### Authentication

- API tokens are generated from the parent account
- Format: `BOOMI_TOKEN.{parent-account-email}:token`

### Rate Limits

- Shared across parent and all child accounts
- 10 requests/second per parent account

---

## Pitfalls

### overrideAccount Only Works on Read Operations

**Can:**
- Query, read, and list components from child accounts

**Cannot:**
- Create/update components in child accounts via overrideAccount
- Writes always go to the account specified in the URL path (`{accountId}`)

---

### DataHub is NOT Shared Across Accounts

- Each account has its own DataHub instance
- Parent's ComponentMapping records are not visible to child accounts
- This is why DevAccountAccess and ComponentMapping are stored in the parent's DataHub

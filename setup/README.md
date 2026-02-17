# Boomi Build Guide Setup Automation

A Python CLI tool that automates the creation and configuration of Boomi components as described in the [Build Guide](../docs/build-guide/index.md). It walks through all 6 build phases — from DataHub foundation to end-to-end testing — combining fully automated API calls with guided manual steps where Boomi requires UI interaction.

## Prerequisites

- **Python 3.10+**
- **Boomi Platform API credentials** — a user with API access and a token generated from AtomSphere > Settings > Account Information and Setup > AtomSphere API Tokens
- **Boomi account** with:
  - DataHub enabled (MDM feature)
  - At least one Atom or Cloud Atom for deployment
  - A target environment configured

## Installation

```bash
cd boomi_team_flow
pip install -r setup/requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP client for Boomi API calls |
| `rich` | Formatted console output (tables, panels, progress) |
| `click` | CLI framework (commands, options, help text) |
| `pydantic` | Configuration validation |
| `pytest` | Test runner |
| `pytest-mock` | Test mocking utilities |

## Quick Start

```bash
# 1. Configure credentials and account details
python -m setup.main configure

# 2. Preview what will happen (no API calls)
python -m setup.main setup --dry-run

# 3. Run the full setup
python -m setup.main setup

# 4. Check progress at any time
python -m setup.main status
```

## Configuration

Configuration is loaded from three sources, in priority order:

1. **Environment variables** (highest priority)
2. **State file** (persisted non-credential config)
3. **Interactive prompts** (fallback for missing values)

### Environment Variables

| Variable | Config Field | Description |
|----------|-------------|-------------|
| `BOOMI_USER` | `boomi_user` | API username (email address) |
| `BOOMI_TOKEN` | `boomi_token` | API token from AtomSphere |
| `BOOMI_ACCOUNT` | `boomi_account_id` | Boomi account ID |
| `BOOMI_REPO` | `boomi_repo_id` | DataHub repository ID |
| `BOOMI_ENVIRONMENT` | `target_environment_id` | Target environment for deployment |

```bash
# Example: export all credentials before running
export BOOMI_USER="admin@example.com"
export BOOMI_TOKEN="your-api-token"
export BOOMI_ACCOUNT="account-abc123"
export BOOMI_REPO="repo-xyz789"
export BOOMI_ENVIRONMENT="env-prod-001"
```

> **Security note:** Credentials (`BOOMI_USER`, `BOOMI_TOKEN`) are never written to the state file. They must be provided via environment variables or interactive prompt on each run.

## Commands

### `configure`

Interactive configuration wizard. Prompts for all required fields and saves non-credential values to the state file.

```bash
python -m setup.main configure
```

### `setup`

Run all 30 steps in dependency order. Skips previously completed steps (resume-safe).

```bash
python -m setup.main setup            # Full run
python -m setup.main setup --dry-run  # Preview without API calls
```

### `status`

Display a table of all steps with their current status (pending, in_progress, completed, failed, skipped).

```bash
python -m setup.main status
```

```
Step                                     Type       Status
--------------------------------------------------------------
Create DataHub Repository                auto       completed
Create DataHub Sources                   auto       completed
Create Model — ComponentMapping          auto       completed
...
Build Flow Dashboard                     manual     pending
```

### `run-step`

Run a specific step and its unmet dependencies.

```bash
python -m setup.main run-step 2.3          # Run step 2.3 (and deps)
python -m setup.main run-step 2.3 --dry-run
```

### `verify`

Re-run all validation steps against completed work to confirm everything is still in order.

```bash
python -m setup.main verify
```

### `reset`

Delete all progress and start over.

```bash
python -m setup.main reset             # Prompts for confirmation
python -m setup.main reset --confirm   # Skip confirmation
```

### Global Options

```bash
python -m setup.main --state-file /path/to/state.json <command>
```

| Option | Default | Description |
|--------|---------|-------------|
| `--state-file` | `.boomi-setup-state.json` | Path to the state persistence file |

## The 30 Build Steps

### Phase 1: DataHub Foundation

| Step | Name | Type | Dependencies | What It Does |
|------|------|------|-------------|--------------|
| 1.0 | Create DataHub Repository | auto | — | Creates the `PromotionHub` DataHub repository |
| 1.1 | Create DataHub Sources | auto | 1.0 | Batch-creates 3 sources: `PROMOTION_ENGINE`, `ADMIN_SEEDING`, `ADMIN_CONFIG` |
| 1.2a | Create Model — ComponentMapping | auto | 1.1 | Creates, publishes, and deploys the ComponentMapping model; polls until deployed |
| 1.2b | Create Model — DevAccountAccess | auto | 1.1 | Creates, publishes, and deploys the DevAccountAccess model; polls until deployed |
| 1.2c | Create Model — PromotionLog | auto | 1.1 | Creates, publishes, and deploys the PromotionLog model; polls until deployed |
| 1.3 | Seed Dev Account Access Records | semi | 1.2c | Interactive loop to create DevAccountAccess records (SSO group to dev account mappings) |
| 1.4 | Validate DataHub CRUD | validate | 1.2a | Creates, queries, and deletes a test ComponentMapping record to verify CRUD works |

### Phase 2a: HTTP Client

| Step | Name | Type | Dependencies | What It Does |
|------|------|------|-------------|--------------|
| 2.0 | Create Folder Structure | auto | — | Creates `/Promoted/` folder tree with Profiles, Connections, Operations subfolders |
| 2.1 | Create HTTP Client Connection | semi | 2.0 | Collects API credentials; creates the `PROMO - Partner API Connection` component |
| 2.2 | Discover HTTP Operation Template | manual | 2.1 | Guides you to manually create the first HTTP operation in the UI; exports its XML as a template |
| 2.3 | Create HTTP Client Operations | auto | 2.2 | Batch-creates the remaining 18 HTTP operations from the template |

### Phase 2b: DataHub Connection

| Step | Name | Type | Dependencies | What It Does |
|------|------|------|-------------|--------------|
| 2.4 | Obtain DataHub Auth Token | manual | 1.0 | Guides you to retrieve the DataHub auth token from the UI; verifies with a test API call |
| 2.5 | Create DataHub Connection | semi | 2.4 | Creates the `PROMO - DataHub Connection` component with repo ID and auth token |
| 2.6 | Discover DataHub Operation Template | manual | 2.5 | Guides you to create the first DataHub operation (Query ComponentMapping); exports XML template |
| 2.7 | Create DataHub Operations | auto | 2.6 | Batch-creates the remaining 5 DataHub operations from the template |
| 2.8 | Verify Phase 2 Components | validate | 2.3, 2.7 | Counts HTTP ops (19), DataHub ops (6), connections (2); reports pass/fail |

### Phase 3: Integration

| Step | Name | Type | Dependencies | What It Does |
|------|------|------|-------------|--------------|
| 3.0 | Discover Profile Template | manual | 2.5 | Guides you to create one JSON profile in the UI; fetches its XML as a template |
| 3.1 | Create Profiles | auto | 3.0 | Batch-creates all 28 JSON profiles from the template |
| 3.2 | Discover FSS Operation Template | manual | 3.1 | Guides you to create one FSS operation; exports XML template |
| 3.3 | Create FSS Operations | auto | 3.2 | Batch-creates all 14 FSS operations; links request/response profiles |
| 3.4 | Build Integration Processes | manual | 3.3 | Guides you through building 12 processes (A0, A-G, E2-E5, J) in dependency order; collects component IDs |
| 3.5 | Verify Phase 3 | validate | 3.4 | Counts profiles (28), FSS ops (14), processes (12); reports pass/fail |

### Phase 4: Flow Service

| Step | Name | Type | Dependencies | What It Does |
|------|------|------|-------------|--------------|
| 4.0 | Create Flow Service | manual | 3.5 | Guides you to create the Flow Service in the UI and link all 14 message actions to FSS operations |
| 4.1 | Package and Deploy Flow Service | auto | 4.0 | Creates PackagedComponent, Integration Pack, releases it, and deploys to environment |
| 4.2 | Configure Primary Account ID | manual | 4.1 | Guides you to set the `com.boomi.flow.primary.account.id` Atom property |
| 4.3 | Verify Phase 4 | validate | 4.2 | Tests the live Flow Service endpoint via a `getDevAccounts` call |

### Phase 5: Flow Dashboard

| Step | Name | Type | Dependencies | What It Does |
|------|------|------|-------------|--------------|
| 5.0 | Build Flow Dashboard | manual | 4.3 | Guides you through 9 pages across 3 swimlanes, SSO config, XmlDiffViewer custom component, and navigation wiring |

### Phase 6: Testing

| Step | Name | Type | Dependencies | What It Does |
|------|------|------|-------------|--------------|
| 6.0 | Smoke Test | semi | 5.0 | Log into Flow Dashboard, select a dev account, verify `getDevAccounts` responds |
| 6.1 | Full Test Scenarios | semi | 6.0 | Walk through 17 test scenarios covering all message actions (packages, deps, promotion, peer review, deploy, withdraw) |
| 6.2 | Final Verification | validate | 6.1 | Verifies total component count (85) via API query |

## Step Types

| Type | Meaning | User Interaction |
|------|---------|-----------------|
| **auto** | Fully automated | None — the tool makes API calls and proceeds |
| **semi** | Partially automated | Prompts for input (credentials, record data), then automates the rest |
| **manual** | User-driven | Displays step-by-step instructions; you perform the action in the Boomi UI, then confirm |
| **validate** | Verification check | Queries Boomi APIs to confirm prior steps completed correctly |

## State Management

All progress is persisted to `.boomi-setup-state.json` (write-through — saved after every mutation). This enables:

- **Resume after interruption** — rerun `setup` and completed steps are skipped
- **Crash recovery** — steps marked `in_progress` at crash time are re-executed on next run
- **Batch resume** — within batch-creation steps (e.g., creating 18 HTTP ops), individual items are tracked so only remaining items are created
- **Component ID tracking** — every created component's ID is stored for use by later steps

### State File Structure

```json
{
  "version": "1.0.0",
  "created_at": "2026-02-17T...",
  "updated_at": "2026-02-17T...",
  "config": {
    "boomi_account_id": "...",
    "boomi_repo_id": "...",
    "cloud_base_url": "https://api.boomi.com",
    "target_environment_id": "..."
  },
  "component_ids": {
    "models": { "ComponentMapping": "model-id-1", "...": "..." },
    "sources": {},
    "folders": {},
    "connections": {},
    "http_operations": {},
    "dh_operations": {},
    "profiles": {},
    "fss_operations": {},
    "processes": {},
    "flow_service": null
  },
  "steps": {
    "1.0": { "status": "completed", "updated_at": "..." },
    "1.1": { "status": "completed", "updated_at": "..." }
  },
  "api_first_discovery": {
    "http_operation_template_xml": "<Component .../>",
    "dh_operation_template_xml": null,
    "fss_operation_template_xml": null,
    "profile_template_xml": null
  }
}
```

## API-First Discovery Pattern

Several component types in Boomi cannot be fully created via API alone — they require an initial manual creation in the UI to capture the correct XML structure. The tool uses an **API-first discovery** pattern:

1. **Manual step**: guides you to create one component of a type in the Boomi UI
2. **Discovery**: fetches that component's XML via `GET /Component/{id}`
3. **Template storage**: caches the XML in the state file under `api_first_discovery`
4. **Batch creation**: parameterizes the template (regex substitution of names, IDs) to create all remaining components of that type via API

This applies to: HTTP operations (step 2.2→2.3), DataHub operations (2.6→2.7), profiles (3.0→3.1), and FSS operations (3.2→3.3).

## API Client Details

### Authentication

Uses Boomi's standard Basic Auth: `BOOMI_TOKEN.{user}:{token}`, Base64-encoded in the `Authorization` header.

### Rate Limiting

Enforces a minimum 120ms gap between API calls to stay within Boomi's rate limits.

### Retry Logic

| Status Code | Behavior |
|-------------|----------|
| 429 (Rate Limited) | Retry up to 3 times with exponential backoff (1s, 2s, 4s) |
| 503 (Service Unavailable) | Retry up to 3 times with exponential backoff |
| 401 (Unauthorized) | Fail immediately (no retry) |
| Other 4xx/5xx | Fail immediately |

### Polling

Long-running operations (model deployment, branch readiness, merge execution) are polled at configurable intervals until a terminal status is reached or a timeout fires.

## Templates

The tool loads spec files directly from this repository:

| Template Type | Location | Format |
|---------------|----------|--------|
| DataHub model specs | `datahub/models/{name}-model-spec.json` | JSON |
| Integration profiles | `integration/profiles/{name}.json` | JSON |
| API request templates | `integration/api-requests/{name}` | XML |

The `parameterize(template, params)` function replaces `{KEY}` placeholders with provided values.

## Running Tests

```bash
# All tests
pytest setup/tests/ -v

# Specific module
pytest setup/tests/test_engine.py -v
pytest setup/tests/test_api_client.py -v
pytest setup/tests/test_state.py -v
pytest setup/tests/test_validators.py -v
pytest setup/tests/test_templates.py -v

# With coverage
pytest setup/tests/ --cov=setup
```

### What's Tested

| Module | Coverage |
|--------|----------|
| Engine & StepRegistry | Dependency resolution, cycle detection, dry-run, resume, target step, error handling |
| BoomiClient | Auth header format, rate limiting, retry on 429/503, no retry on 401, JSON/XML parsing |
| SetupState | Create/load/save, write-through persistence, component ID storage, step status transitions, crash recovery, batch item tracking, discovery templates |
| Validators | Model deployment verification, source existence, component count checks (HTTP ops, DataHub ops, profiles, FSS ops, total BOM) |
| Template Loader | Repo root detection, model/profile loading, parameterization, profile listing |

## Expected Component Counts

When fully built, the system should contain:

| Component Type | Count |
|---------------|-------|
| DataHub Models | 3 |
| Connections | 2 |
| HTTP Operations | 19 |
| DataHub Operations | 6 |
| Profiles | 28 |
| Integration Processes | 12 |
| FSS Operations | 14 |
| Flow Service | 1 |
| **Total** | **85** |

## Troubleshooting

### "Configuration is incomplete"

Run `configure` first, or set all required environment variables. Credentials are required for every run.

### Step stuck in `in_progress`

This means the previous run was interrupted. Rerun `setup` — the engine will re-execute `in_progress` steps.

### Step shows `failed`

Check the error in the state file (`steps.{id}.error`). Fix the underlying issue and rerun — failed steps are re-attempted.

### "Unknown step" error with `run-step`

Step IDs use the format `{phase}.{number}` with optional letter suffix, e.g., `1.2a`, `2.3`, `3.4`. Run `status` to see all valid step IDs.

### Rate limit errors

The client enforces 120ms between calls and retries on 429. If you still hit limits, wait a few minutes and retry — Boomi rate limits reset quickly.

### Template discovery fails

If a discovery step fails to fetch the template XML, verify the component was created successfully in the Boomi UI and that the component ID entered is correct (must be a valid UUID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

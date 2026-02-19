"""Phase 1 — DataHub setup steps (1.0 through 1.4)."""
from __future__ import annotations

import time

from setup.api.client import BoomiApiError
from setup.engine import StepStatus, StepType
from setup.state import SetupState
from setup.steps.base import BaseStep
from setup.templates.loader import load_model_spec
from setup.ui import console as ui
from setup.ui.prompts import guide_and_collect, guide_and_confirm, prompt_choice


class CreateRepo(BaseStep):
    """Step 1.0 — Create the PromotionHub DataHub repository.

    Uses the Platform API endpoint:
      POST /clouds/{cloudId}/repositories/{repoName}/create
    which requires first fetching available Hub Clouds via GET /clouds.
    Repository creation is async — polls GET /repositories/{repoId}/status
    until SUCCESS.
    """

    REPO_NAME = "PromotionHub"

    @property
    def step_id(self) -> str:
        return "1.0"

    @property
    def name(self) -> str:
        return "Create DataHub Repository"

    @property
    def step_type(self) -> StepType:
        return StepType.SEMI

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        # Skip if already configured, but still ensure hub_cloud_url and hub_cloud_name are populated
        existing = state.config.get("boomi_repo_id", "")
        if existing:
            ui.print_success(f"Repository already exists (ID: {existing})")
            if not dry_run:
                # C2a fix: ensure hub_cloud_url is populated from list_repositories
                # so that record operations can use the correct Repository API host.
                if not state.config.get("hub_cloud_url"):
                    try:
                        self.datahub_api.list_repositories()
                        if self.datahub_api._config.hub_cloud_url:
                            state.update_config({"hub_cloud_url": self.datahub_api._config.hub_cloud_url})
                            ui.print_info(f"Hub cloud URL refreshed: {self.datahub_api._config.hub_cloud_url}")
                    except BoomiApiError:
                        pass  # Non-fatal; will fail later when record ops are called
                # Backfill hub_cloud_name for DataHub Connection creation (step 2.5)
                if not state.config.get("hub_cloud_name"):
                    try:
                        clouds = self.datahub_api.get_hub_clouds()
                        if len(clouds) == 1:
                            state.update_config({"hub_cloud_name": clouds[0]["name"]})
                            ui.print_info(f"Hub cloud name: {clouds[0]['name']}")
                        elif clouds:
                            idx = prompt_choice(
                                "Select the Hub Cloud used for the PromotionHub repository:",
                                [f"{c['name']} ({c['cloudId']})" for c in clouds],
                            )
                            state.update_config({"hub_cloud_name": clouds[idx]["name"]})
                    except BoomiApiError:
                        pass  # Non-fatal; step 2.5 will report the missing name
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info("Would create DataHub repository 'PromotionHub'")
            return StepStatus.COMPLETED

        # Step 1: Fetch available Hub Clouds
        try:
            ui.print_info("Fetching available Hub Clouds...")
            clouds = self.datahub_api.get_hub_clouds()
        except BoomiApiError as exc:
            ui.print_error(f"Failed to fetch Hub Clouds: {exc}")
            return StepStatus.FAILED

        if not clouds:
            ui.print_error(
                "No Hub Clouds found. Ensure your account has DataHub "
                "provisioned and the API user has MDM - Repository Management privilege."
            )
            return StepStatus.FAILED

        # Step 2: Select a Hub Cloud
        if len(clouds) == 1:
            cloud = clouds[0]
            ui.print_info(f"Using Hub Cloud: {cloud['name']} ({cloud['cloudId']})")
        else:
            choices = [f"{c['name']} ({c['cloudId']})" for c in clouds]
            idx = prompt_choice("Select a Hub Cloud for the repository:", choices)
            cloud = clouds[idx]
            ui.print_info(f"Selected Hub Cloud: {cloud['name']}")

        # Persist cloud name for DataHub Connection creation (step 2.5)
        state.update_config({"hub_cloud_name": cloud["name"]})

        # Step 3: Create the repository (async)
        try:
            ui.print_info(f"Creating repository '{self.REPO_NAME}' on {cloud['name']}...")
            repo_id = self.datahub_api.create_repository(
                cloud["cloudId"], self.REPO_NAME
            )
            if not repo_id:
                ui.print_error("No repository ID returned from API")
                return StepStatus.FAILED
            ui.print_info(f"Repository creation initiated (ID: {repo_id})")
        except BoomiApiError as exc:
            ui.print_error(f"Failed to create repository: {exc}")
            return StepStatus.FAILED

        # Persist repo ID immediately so re-runs don't create duplicates
        state.update_config({"boomi_repo_id": repo_id})
        self.config.boomi_repo_id = repo_id

        # Step 4: Manual confirmation (polling is unreliable — status API returns UNKNOWN)
        confirmed = guide_and_confirm(
            "Verify the repository was created successfully in AtomSphere:\n\n"
            "1. Navigate to Services > DataHub > Repositories\n"
            "2. Look for the 'PromotionHub' repository in the list\n\n"
            "Is the PromotionHub repository visible?",
            "Repository created?",
        )
        if not confirmed:
            ui.print_error("Repository creation not confirmed — re-run this step after verifying")
            return StepStatus.FAILED

        # Step 5: Fetch repository list to extract hub_cloud_url (repositoryBaseUrl)
        # C2a fix: hub_cloud_url is required for Repository API record operations.
        try:
            ui.print_info("Fetching repository details to obtain hub cloud URL...")
            self.datahub_api.list_repositories()
            if self.datahub_api._config.hub_cloud_url:
                state.update_config({"hub_cloud_url": self.datahub_api._config.hub_cloud_url})
                ui.print_info(f"Hub cloud URL: {self.datahub_api._config.hub_cloud_url}")
            else:
                ui.print_warning(
                    "Could not extract hub cloud URL from repository response. "
                    "Record operations may fail."
                )
        except BoomiApiError as exc:
            ui.print_warning(f"Could not fetch repository details: {exc}")

        ui.print_success(f"Created repository '{self.REPO_NAME}' (ID: {repo_id})")
        return StepStatus.COMPLETED


class CreateSources(BaseStep):
    """Step 1.1 — Create the three DataHub sources."""

    SOURCES = ["PROMOTION_ENGINE", "ADMIN_SEEDING", "ADMIN_CONFIG"]

    @property
    def step_id(self) -> str:
        return "1.1"

    @property
    def name(self) -> str:
        return "Create DataHub Sources"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    @property
    def depends_on(self) -> list[str]:
        return ["1.0"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)
        remaining = state.get_remaining_items(self.step_id, self.SOURCES)

        if not remaining:
            ui.print_success("All sources already created")
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info(f"Would create {len(remaining)} sources: {', '.join(remaining)}")
            return StepStatus.COMPLETED

        for source_name in remaining:
            try:
                self.datahub_api.create_source(source_name)
                # DataHub sourceId = the name we provide; API returns <true/>
                state.store_component_id("sources", source_name, source_name)
                state.mark_step_item_complete(self.step_id, source_name)
                ui.print_success(f"Created source '{source_name}'")
            except BoomiApiError as exc:
                ui.print_error(f"Failed to create source '{source_name}': {exc}")
                return StepStatus.FAILED

        return StepStatus.COMPLETED


class CreateModel(BaseStep):
    """Step 1.2x — Create, publish, and deploy a single DataHub model.

    Instantiate one per model: ComponentMapping (1.2a), DevAccountAccess (1.2b),
    PromotionLog (1.2c).
    """

    def __init__(self, *args, model_name: str, sub_id: str, **kwargs) -> None:  # type: ignore[override]
        super().__init__(*args, **kwargs)
        self._model_name = model_name
        self._sub_id = sub_id

    @property
    def step_id(self) -> str:
        return f"1.2{self._sub_id}"

    @property
    def name(self) -> str:
        return f"Create Model — {self._model_name}"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    @property
    def depends_on(self) -> list[str]:
        return ["1.1"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        existing = state.get_component_id("models", self._model_name)
        if existing:
            ui.print_success(
                f"Model '{self._model_name}' already exists (ID: {existing})"
            )
            # Ensure universe_id is populated in both state and in-memory config
            # so downstream steps (SeedDevAccess, TestCrud) use the correct ID.
            current_uid = state.config.get("universe_ids", {}).get(self._model_name)
            if current_uid != existing:
                state.store_universe_id(self._model_name, existing)
                ui.print_info(f"Re-synced universe_id for '{self._model_name}': {existing}")
            self.datahub_api._config.universe_ids[self._model_name] = existing
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info(f"Would create model '{self._model_name}'")
            return StepStatus.COMPLETED

        try:
            spec = load_model_spec(self._model_name)

            # Try to create; recover if model already exists in Boomi but
            # not in our state (e.g. state was reset after a prior run).
            try:
                model_id = self.datahub_api.create_model(spec)
                ui.print_info(f"Created model '{self._model_name}' (ID: {model_id})")
            except BoomiApiError as create_exc:
                if create_exc.status_code in (400, 409) and "already" in create_exc.body.lower():
                    ui.print_info(
                        f"Model '{self._model_name}' already exists in Boomi — recovering ID..."
                    )
                    model_id = self.datahub_api.find_model_by_name(self._model_name)
                    if not model_id:
                        ui.print_error(
                            f"Model '{self._model_name}' reportedly exists but "
                            "could not be found via GET /models"
                        )
                        return StepStatus.FAILED
                    ui.print_info(f"Recovered model ID: {model_id}")
                else:
                    raise

            # Publish (idempotent — ignore "already published" errors)
            try:
                self.datahub_api.publish_model(model_id)
                ui.print_info(f"Published model '{self._model_name}'")
            except BoomiApiError as pub_exc:
                if pub_exc.status_code == 400:
                    ui.print_info(f"Model '{self._model_name}' already published")
                else:
                    raise

            # Deploy (may already be deployed — 400 is acceptable)
            try:
                deployment_id = self.datahub_api.deploy_model(model_id)
                ui.print_info(f"Deploying model '{self._model_name}'...")
                self.datahub_api.poll_model_deployed(model_id, deployment_id)
                ui.print_success(f"Model '{self._model_name}' deployed (ID: {model_id})")
            except BoomiApiError as dep_exc:
                if dep_exc.status_code == 400:
                    ui.print_info(
                        f"Model '{self._model_name}' already deployed (ID: {model_id})"
                    )
                else:
                    raise

            state.store_component_id("models", self._model_name, model_id)
            # C2a fix: store universe_id (= model_id) so record operations can build
            # the correct Repository API URL: /mdm/universes/{universeId}/records
            state.store_universe_id(self._model_name, model_id)
            self.datahub_api._config.universe_ids[self._model_name] = model_id
            return StepStatus.COMPLETED
        except BoomiApiError as exc:
            ui.print_error(f"Failed to create model '{self._model_name}': {exc}")
            return StepStatus.FAILED


class StageSources(BaseStep):
    """Step 1.2d — Enable Initial Load, create staging areas, and finish load for all source-model pairs.

    After models are deployed to the repository (steps 1.2a-c), each source
    must be put into Initial Load mode before a staging area can be created.
    The per-source lifecycle is:
      1. enableInitialLoad  — puts the source in a valid state
      2. stagingArea/create — creates the staging area (allows record batches)
      3. finishInitialLoad  — releases the lock for the next source

    Only one source per universe can be in Initial Load mode at a time, so we
    must fully cycle (enable → stage → finish) each source before starting the next.

    Reads the source lists from model specs to build the pairs dynamically.
    """

    # The three models deployed in steps 1.2a-c and their spec names
    _MODELS = ["ComponentMapping", "DevAccountAccess", "PromotionLog"]

    @property
    def step_id(self) -> str:
        return "1.2d"

    @property
    def name(self) -> str:
        return "Stage Sources and Initialize Load Mode"

    @property
    def step_type(self) -> StepType:
        return StepType.AUTO

    @property
    def depends_on(self) -> list[str]:
        return ["1.2a", "1.2b", "1.2c"]

    def _build_pairs(self) -> list[tuple[str, str]]:
        """Build (source_name, model_name) pairs from model specs.

        Returns e.g.:
          [("PROMOTION_ENGINE", "ComponentMapping"),
           ("ADMIN_SEEDING", "ComponentMapping"),
           ("ADMIN_CONFIG", "DevAccountAccess"),
           ("PROMOTION_ENGINE", "PromotionLog")]
        """
        pairs: list[tuple[str, str]] = []
        for model_name in self._MODELS:
            spec = load_model_spec(model_name)
            for src in spec.get("sources", []):
                pairs.append((src["name"], model_name))
        return pairs

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        pairs = self._build_pairs()
        # Item key = "SOURCE:Model" for resumability tracking
        all_items = [f"{src}:{model}" for src, model in pairs]
        remaining = state.get_remaining_items(self.step_id, all_items)

        if not remaining:
            ui.print_success("All staging areas already created")
            return StepStatus.COMPLETED

        if dry_run:
            ui.print_info(f"Would create {len(remaining)} staging areas: {', '.join(remaining)}")
            return StepStatus.COMPLETED

        # Build lookup from remaining keys back to (source, model) pairs
        remaining_set = set(remaining)

        for source_name, model_name in pairs:
            item_key = f"{source_name}:{model_name}"
            if item_key not in remaining_set:
                continue

            universe_id = state.config.get("universe_ids", {}).get(model_name, "")
            if not universe_id:
                ui.print_error(
                    f"No universe_id for model '{model_name}' — "
                    "ensure steps 1.2a-c completed successfully"
                )
                return StepStatus.FAILED

            try:
                # Step 1: Enable Initial Load — puts source in valid state
                try:
                    self.datahub_api.enable_initial_load(universe_id, source_name)
                    ui.print_info(
                        f"Enabled Initial Load for '{source_name}' in '{model_name}'"
                    )
                except BoomiApiError as exc:
                    # Already in Initial Load mode is fine (idempotent)
                    if exc.status_code == 400:
                        ui.print_info(
                            f"Initial Load already active for '{source_name}' in '{model_name}'"
                        )
                    else:
                        raise

                # Step 2: Create staging area (retry — enableInitialLoad has variable propagation delay)
                system_id = None
                last_exc = None
                for attempt in range(6):
                    try:
                        system_id = self.datahub_api.add_staging_area(
                            universe_id=universe_id,
                            source_id=source_name,
                            name=source_name,
                            staging_id=source_name,
                        )
                        break
                    except BoomiApiError as staging_exc:
                        last_exc = staging_exc
                        if staging_exc.status_code == 400 and "not in a valid state" in staging_exc.body.lower():
                            wait = 2 * (attempt + 1)
                            ui.print_info(
                                f"Source not ready yet, retrying in {wait}s "
                                f"(attempt {attempt + 1}/6)..."
                            )
                            time.sleep(wait)
                            continue
                        raise  # Non-retryable error — propagate to outer handler
                if system_id is None:
                    raise last_exc  # type: ignore[misc]

                # Step 3: Finish Initial Load — release lock for next source
                try:
                    self.datahub_api.finish_initial_load(universe_id, source_name)
                    ui.print_info(
                        f"Finished Initial Load for '{source_name}' in '{model_name}'"
                    )
                except BoomiApiError as exc:
                    # Already finished is fine (idempotent)
                    if exc.status_code == 400:
                        ui.print_info(
                            f"Initial Load already finished for '{source_name}' in '{model_name}'"
                        )
                    else:
                        raise

                state.mark_step_item_complete(self.step_id, item_key)
                # Persist system staging area ID for potential future use
                state.store_component_id(
                    "staging_areas", item_key, system_id,
                )
                ui.print_success(
                    f"Staged source '{source_name}' for model '{model_name}'"
                )
            except BoomiApiError as exc:
                # "Already exists" is success — the staging area was created previously
                if exc.status_code == 400 and "already" in exc.body.lower():
                    # Still need to finish initial load in case it's hanging
                    try:
                        self.datahub_api.finish_initial_load(universe_id, source_name)
                    except BoomiApiError:
                        pass  # Best-effort cleanup
                    state.mark_step_item_complete(self.step_id, item_key)
                    ui.print_success(
                        f"Staging area for '{source_name}' in '{model_name}' already exists"
                    )
                    continue
                ui.print_error(
                    f"Failed to stage source '{source_name}' "
                    f"for model '{model_name}': {exc}"
                )
                return StepStatus.FAILED

        return StepStatus.COMPLETED


class SeedDevAccess(BaseStep):
    """Step 1.3 — Seed DevAccountAccess records via interactive prompts."""

    @property
    def step_id(self) -> str:
        return "1.3"

    @property
    def name(self) -> str:
        return "Seed Dev Account Access Records"

    @property
    def step_type(self) -> StepType:
        return StepType.SEMI

    @property
    def depends_on(self) -> list[str]:
        return ["1.2d", "2.4"]

    def _build_record_xml(
        self, sso_group_id: str, group_name: str, dev_account_id: str, dev_account_name: str
    ) -> str:
        # C2c fix: include <id> source entity ID so DataHub does not quarantine the record.
        # The composite key uses the two match fields separated by colon.
        # NOTE: No XML declaration — Boomi docs show batch XML without <?xml?> header,
        # and some parsers may mis-detect the entity type when the declaration is present.
        entity_id = f"{sso_group_id}:{dev_account_id}"
        return (
            '<batch src="ADMIN_CONFIG">\n'
            "  <DevAccountAccess>\n"
            f"    <id>{entity_id}</id>\n"
            f"    <ssoGroupId>{sso_group_id}</ssoGroupId>\n"
            f"    <ssoGroupName>{group_name}</ssoGroupName>\n"
            f"    <devAccountId>{dev_account_id}</devAccountId>\n"
            f"    <devAccountName>{dev_account_name}</devAccountName>\n"
            "  </DevAccountAccess>\n"
            "</batch>"
        )

    def _validate_universe_ids(self, state: SetupState) -> bool:
        """Pre-flight check: verify universe_ids are populated and unique.

        Returns True if valid, False if misconfigured.
        """
        uids = self.datahub_api._config.universe_ids
        state_uids = state.config.get("universe_ids", {})

        ui.print_info("Pre-flight universe_id check:")
        ui.print_info(f"  config.universe_ids: {dict(uids)}")
        ui.print_info(f"  state.universe_ids:  {dict(state_uids)}")

        # Check DevAccountAccess specifically
        da_uid = uids.get("DevAccountAccess", "")
        if not da_uid:
            ui.print_error(
                "universe_id for DevAccountAccess is MISSING from config. "
                "Steps 1.2a-c may have been skipped without populating IDs."
            )
            # Attempt live recovery via GET /models
            ui.print_info("Attempting live recovery via GET /models...")
            recovered_id = self.datahub_api.find_model_by_name("DevAccountAccess")
            if recovered_id:
                ui.print_info(f"Recovered DevAccountAccess universe_id: {recovered_id}")
                state.store_universe_id("DevAccountAccess", recovered_id)
                self.datahub_api._config.universe_ids["DevAccountAccess"] = recovered_id
                state.store_component_id("models", "DevAccountAccess", recovered_id)
            else:
                ui.print_error("Could not find DevAccountAccess via GET /models")
                return False

        # Check for duplicates (different models sharing same universe_id)
        seen: dict[str, str] = {}
        for model_name, uid in uids.items():
            if uid in seen:
                ui.print_error(
                    f"DUPLICATE universe_id detected: '{model_name}' and "
                    f"'{seen[uid]}' both have universe_id '{uid}'"
                )
                return False
            seen[uid] = model_name

        # Verify actual model name matches expected name via GET /models/{id}
        da_uid = uids.get("DevAccountAccess", "")
        if da_uid:
            try:
                model_resp = self.datahub_api.get_model(da_uid)
                if isinstance(model_resp, str):
                    import re
                    name_match = re.search(r'name="([^"]+)"', model_resp)
                    if not name_match:
                        name_match = re.search(r"<mdm:name>([^<]+)</mdm:name>", model_resp)
                    actual_name = name_match.group(1) if name_match else "UNKNOWN"
                    ui.print_info(f"  Model {da_uid} actual name: '{actual_name}'")
                    if actual_name != "DevAccountAccess":
                        ui.print_error(
                            f"NAME MISMATCH: universe {da_uid} contains model "
                            f"'{actual_name}', not 'DevAccountAccess'. "
                            f"The state has the wrong model ID stored."
                        )
                        # Attempt to find the real DevAccountAccess model
                        real_id = self.datahub_api.find_model_by_name("DevAccountAccess")
                        if real_id:
                            ui.print_info(
                                f"  Found real DevAccountAccess model: {real_id}"
                            )
                            state.store_universe_id("DevAccountAccess", real_id)
                            state.store_component_id("models", "DevAccountAccess", real_id)
                            self.datahub_api._config.universe_ids["DevAccountAccess"] = real_id
                            ui.print_success("  Auto-corrected universe_id — retrying")
                        else:
                            ui.print_error(
                                "  Could not find 'DevAccountAccess' in GET /models. "
                                "Check the model name in DataHub UI."
                            )
                            return False
                else:
                    ui.print_info(f"  Model response (non-XML): {model_resp}")
            except BoomiApiError as exc:
                ui.print_warning(f"  Could not verify model name: {exc}")

        # Log the URL that will be used
        hub_url = self.datahub_api._config.hub_cloud_url
        final_uid = uids.get("DevAccountAccess", "MISSING")
        ui.print_info(
            f"  Record URL: {hub_url}/mdm/universes/{final_uid}/records"
        )
        return True

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would prompt for DevAccountAccess records and insert via DataHub API")
            return StepStatus.COMPLETED

        # Validate universe_ids before attempting record creation
        if not self._validate_universe_ids(state):
            ui.print_error(
                "Universe ID validation failed. Check the IDs above against "
                "your DataHub UI (Services > DataHub > Models > click model > URL contains the ID)"
            )
            return StepStatus.FAILED

        record_count = 0
        while True:
            sso_group_id = guide_and_collect(
                "Enter the SSO group ID for this dev account access record.\n"
                "Example: ABC_BOOMI_FLOW_CONTRIBUTOR",
                "SSO Group ID",
            )
            group_name = guide_and_collect(
                "Enter the SSO group display name.",
                "SSO Group Name",
            )
            dev_account_id = guide_and_collect(
                "Enter the Boomi dev sub-account ID.",
                "Dev Account ID",
            )
            dev_account_name = guide_and_collect(
                "Enter the dev account display name.",
                "Dev Account Name",
            )

            record_xml = self._build_record_xml(
                sso_group_id, group_name, dev_account_id, dev_account_name
            )

            try:
                # Retry on "entity of unknown type" — model may not yet be
                # recognized by the Repository API after deployment.
                last_exc = None
                created = False
                for attempt in range(4):
                    try:
                        self.datahub_api.create_record(
                            "DevAccountAccess", record_xml, "ADMIN_CONFIG"
                        )
                        created = True
                        break
                    except BoomiApiError as exc:
                        last_exc = exc
                        if exc.status_code == 400 and "entity of unknown type" in exc.body.lower():
                            wait = 3 * (attempt + 1)
                            ui.print_info(
                                f"Model not yet recognized by Repository API, retrying in {wait}s "
                                f"(attempt {attempt + 1}/4)..."
                            )
                            time.sleep(wait)
                            continue
                        raise  # Non-retryable error

                # Fallback: try staging endpoint if /records kept failing
                if not created:
                    ui.print_info(
                        "All /records attempts failed — trying staging endpoint "
                        "(/staging/ADMIN_CONFIG) as fallback..."
                    )
                    try:
                        self.datahub_api.create_record_staging(
                            "DevAccountAccess", record_xml, "ADMIN_CONFIG"
                        )
                        ui.print_info("Staging endpoint succeeded")
                    except BoomiApiError as staging_exc:
                        ui.print_error(f"Staging endpoint also failed: {staging_exc}")
                        raise last_exc  # type: ignore[misc]

                record_count += 1
                ui.print_success(
                    f"Created DevAccountAccess record #{record_count} "
                    f"({sso_group_id} -> {dev_account_name})"
                )
            except BoomiApiError as exc:
                ui.print_error(f"Failed to create record: {exc}")
                return StepStatus.FAILED

            if not guide_and_confirm(
                "Add another DevAccountAccess record?",
                "Add another?",
            ):
                break

        ui.print_success(f"Seeded {record_count} DevAccountAccess record(s)")
        return StepStatus.COMPLETED


class TestCrud(BaseStep):
    """Step 1.4 — Validate DataHub CRUD by creating, querying, and deleting a test record."""

    @property
    def step_id(self) -> str:
        return "1.4"

    @property
    def name(self) -> str:
        return "Validate DataHub CRUD"

    @property
    def step_type(self) -> StepType:
        return StepType.VALIDATE

    @property
    def depends_on(self) -> list[str]:
        return ["1.2d", "2.4"]

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        ui.print_step(self.step_id, self.name, self.step_type.value)

        if dry_run:
            ui.print_info("Would create, query, and delete a test ComponentMapping record")
            return StepStatus.COMPLETED

        # Print credential diagnostics before attempting CRUD
        acct = self.config.boomi_account_id
        tok = self.config.hub_auth_token
        hub = self.config.hub_cloud_url
        uids = self.config.universe_ids
        ui.print_info(
            f"Auth context: account={acct[:8] + '...' if acct else 'EMPTY'} "
            f"({len(acct)} chars), "
            f"token={tok[:4] + '...' if tok else 'EMPTY'} "
            f"({len(tok)} chars), "
            f"hub={hub or 'EMPTY'}, "
            f"universes={list(uids.keys()) if uids else 'NONE'}"
        )

        test_dev_id = "test-crud-00000000"
        test_account_id = "test-account-00000000"
        # C2c fix: include <id> source entity ID (composite of match fields)
        # NOTE: No XML declaration — Boomi docs show batch XML without <?xml?> header.
        test_entity_id = f"{test_dev_id}:{test_account_id}"
        record_xml = (
            '<batch src="PROMOTION_ENGINE">\n'
            "  <ComponentMapping>\n"
            f"    <id>{test_entity_id}</id>\n"
            f"    <devComponentId>{test_dev_id}</devComponentId>\n"
            f"    <devAccountId>{test_account_id}</devAccountId>\n"
            "    <prodComponentId>test-prod-00000000</prodComponentId>\n"
            "    <componentName>CRUD Test Record</componentName>\n"
            "    <componentType>process</componentType>\n"
            "  </ComponentMapping>\n"
            "</batch>"
        )

        try:
            # Create (retry on "entity of unknown type" propagation delay)
            ui.print_info("Creating test ComponentMapping record...")
            last_exc = None
            created = False
            for attempt in range(4):
                try:
                    self.datahub_api.create_record(
                        "ComponentMapping", record_xml, "PROMOTION_ENGINE"
                    )
                    created = True
                    break
                except BoomiApiError as exc:
                    last_exc = exc
                    if exc.status_code == 400 and "entity of unknown type" in exc.body.lower():
                        wait = 3 * (attempt + 1)
                        ui.print_info(
                            f"Model not yet recognized by Repository API, retrying in {wait}s "
                            f"(attempt {attempt + 1}/4)..."
                        )
                        time.sleep(wait)
                        continue
                    raise  # Non-retryable error

            # Fallback: try staging endpoint if /records kept failing
            if not created:
                ui.print_info(
                    "All /records attempts failed — trying staging endpoint "
                    "(/staging/PROMOTION_ENGINE) as fallback..."
                )
                try:
                    self.datahub_api.create_record_staging(
                        "ComponentMapping", record_xml, "PROMOTION_ENGINE"
                    )
                except BoomiApiError as staging_exc:
                    ui.print_error(f"Staging endpoint also failed: {staging_exc}")
                    raise last_exc  # type: ignore[misc]
            ui.print_success("Test record created")

            # Query
            # M3 fix: fieldId values must use UPPER_SNAKE_CASE uniqueId format
            # (DEV_COMPONENT_ID, DEV_ACCOUNT_ID) to match the model's field uniqueId.
            ui.print_info("Querying test record...")
            query_xml = (
                '<RecordQueryRequest limit="10">\n'
                "  <view>\n"
                "    <fieldId>DEV_COMPONENT_ID</fieldId>\n"
                "    <fieldId>DEV_ACCOUNT_ID</fieldId>\n"
                "  </view>\n"
                '  <filter op="AND">\n'
                "    <fieldValue>\n"
                "      <fieldId>DEV_COMPONENT_ID</fieldId>\n"
                "      <operator>EQUALS</operator>\n"
                f"      <value>{test_dev_id}</value>\n"
                "    </fieldValue>\n"
                "  </filter>\n"
                "</RecordQueryRequest>"
            )
            query_result = self.datahub_api.query_records("ComponentMapping", query_xml)
            if not query_result:
                ui.print_error("Query returned no result")
                return StepStatus.FAILED
            ui.print_success("Test record queried successfully")

            # Delete — extract record ID from query result
            # DataHub query returns XML; parse for recordId
            record_id = self._extract_record_id(query_result)
            if record_id:
                ui.print_info("Deleting test record...")
                self.datahub_api.delete_record("ComponentMapping", record_id)
                ui.print_success("Test record deleted")
            else:
                ui.print_warning("Could not extract record ID for cleanup; manual cleanup may be needed")

            ui.print_success("DataHub CRUD validation passed")
            return StepStatus.COMPLETED
        except BoomiApiError as exc:
            ui.print_error(f"CRUD validation failed: {exc}")
            return StepStatus.FAILED

    @staticmethod
    def _extract_record_id(result: dict | str) -> str | None:
        """Extract the first recordId from a DataHub query response."""
        if isinstance(result, str):
            # XML response — look for recordId attribute or element
            import re
            match = re.search(r'recordId="([^"]+)"', result)
            if match:
                return match.group(1)
            match = re.search(r"<recordId>([^<]+)</recordId>", result)
            if match:
                return match.group(1)
        elif isinstance(result, dict):
            records = result.get("records", [])
            if records:
                return records[0].get("recordId")
        return None

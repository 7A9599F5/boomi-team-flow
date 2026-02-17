"""Click CLI entry point for Boomi Build Guide Setup Automation."""
from __future__ import annotations

from pathlib import Path

import click

from setup.api.datahub_api import DataHubApi
from setup.api.platform_api import PlatformApi
from setup.config import BoomiConfig, load_config
from setup.engine import Engine, StepRegistry, StepStatus
from setup.state import DEFAULT_STATE_FILE, SetupState


def _build_registry(
    config: BoomiConfig,
    platform_api: PlatformApi | None,
    datahub_api: DataHubApi | None,
) -> StepRegistry:
    """Build the step registry with all 30 steps across 6 phases."""
    from setup.steps.phase1_datahub import (
        CreateModel, CreateRepo, CreateSources, SeedDevAccess, TestCrud,
    )
    from setup.steps.phase2a_http import (
        CreateFolders, CreateHttpConn, CreateHttpOps, DiscoverHttpTemplate,
    )
    from setup.steps.phase2b_datahub_conn import (
        CreateDhConn, CreateDhOps, DiscoverDhTemplate, GetDhToken, VerifyPhase2,
    )
    from setup.steps.phase3_integration import (
        BuildProcesses, CreateFssOps, CreateProfiles,
        DiscoverFssTemplate, DiscoverProfileTemplate, VerifyPhase3,
    )
    from setup.steps.phase4_flow_service import (
        ConfigPrimaryId, CreateFlowService, PackageAndDeployFlowService, VerifyPhase4,
    )
    from setup.steps.phase5_flow_dashboard import FlowDashboard
    from setup.steps.phase6_testing import FinalVerify, FullTests, SmokeTest

    def _make(cls, **kwargs):
        return cls(config=config, platform_api=platform_api, datahub_api=datahub_api, **kwargs)

    registry = StepRegistry()

    # Phase 1: DataHub Foundation
    registry.register(_make(CreateRepo))
    registry.register(_make(CreateSources))
    registry.register(_make(CreateModel, model_name="ComponentMapping", sub_id="a"))
    registry.register(_make(CreateModel, model_name="DevAccountAccess", sub_id="b"))
    registry.register(_make(CreateModel, model_name="PromotionLog", sub_id="c"))
    registry.register(_make(SeedDevAccess))
    registry.register(_make(TestCrud))

    # Phase 2a: HTTP Client
    registry.register(_make(CreateFolders))
    registry.register(_make(CreateHttpConn))
    registry.register(_make(DiscoverHttpTemplate))
    registry.register(_make(CreateHttpOps))

    # Phase 2b: DataHub Connection
    registry.register(_make(GetDhToken))
    registry.register(_make(CreateDhConn))
    registry.register(_make(DiscoverDhTemplate))
    registry.register(_make(CreateDhOps))
    registry.register(_make(VerifyPhase2))

    # Phase 3: Integration
    registry.register(_make(DiscoverProfileTemplate))
    registry.register(_make(CreateProfiles))
    registry.register(_make(DiscoverFssTemplate))
    registry.register(_make(CreateFssOps))
    registry.register(_make(BuildProcesses))
    registry.register(_make(VerifyPhase3))

    # Phase 4: Flow Service
    registry.register(_make(CreateFlowService))
    registry.register(_make(PackageAndDeployFlowService))
    registry.register(_make(ConfigPrimaryId))
    registry.register(_make(VerifyPhase4))

    # Phase 5: Flow Dashboard
    registry.register(_make(FlowDashboard))

    # Phase 6: Testing
    registry.register(_make(SmokeTest))
    registry.register(_make(FullTests))
    registry.register(_make(FinalVerify))

    return registry


def _init_apis(config: BoomiConfig):
    """Initialize API clients from config. Returns (platform_api, datahub_api) or (None, None)."""
    if not config.has_credentials:
        return None, None
    from setup.api.client import BoomiClient
    from setup.api.datahub_api import DataHubApi
    from setup.api.platform_api import PlatformApi

    client = BoomiClient(config.boomi_user, config.boomi_token)
    platform_api = PlatformApi(client, config)
    datahub_api = DataHubApi(client, config)
    return platform_api, datahub_api


def _load_state(state_file: str) -> SetupState:
    """Load or create the state file."""
    path = Path(state_file)
    return SetupState.load_or_create(path)


@click.group()
@click.option(
    "--state-file",
    default=DEFAULT_STATE_FILE,
    show_default=True,
    help="Path to the state file.",
)
@click.pass_context
def cli(ctx: click.Context, state_file: str) -> None:
    """Boomi Build Guide Setup Automation.

    Automates the creation and configuration of Boomi components
    as described in the Build Guide.
    """
    ctx.ensure_object(dict)
    ctx.obj["state_file"] = state_file


@cli.command()
@click.pass_context
def configure(ctx: click.Context) -> None:
    """Configure Boomi connection settings interactively."""
    state = _load_state(ctx.obj["state_file"])
    config = load_config(existing_state_config=state.config, interactive=True)

    if not config.is_complete:
        click.echo("Warning: configuration is incomplete.")

    state.update_config(config.to_state_dict())
    click.echo(f"Configuration saved to {state.path}")


@cli.command()
@click.option("--dry-run", is_flag=True, help="Print what would happen without calling APIs.")
@click.pass_context
def setup(ctx: click.Context, dry_run: bool) -> None:
    """Run all setup steps in dependency order."""
    state = _load_state(ctx.obj["state_file"])
    config = load_config(existing_state_config=state.config, interactive=not dry_run)

    if not dry_run and not config.is_complete:
        click.echo("Error: configuration is incomplete. Run 'configure' first.")
        raise SystemExit(1)

    state.update_config(config.to_state_dict())
    platform_api, datahub_api = _init_apis(config)
    registry = _build_registry(config, platform_api, datahub_api)
    engine = Engine(registry, state)
    engine.run(dry_run=dry_run)
    click.echo("Setup complete.")


@cli.command()
@click.pass_context
def verify(ctx: click.Context) -> None:
    """Verify all completed steps are still valid."""
    state = _load_state(ctx.obj["state_file"])
    config = load_config(existing_state_config=state.config, interactive=True)
    platform_api, datahub_api = _init_apis(config)
    registry = _build_registry(config, platform_api, datahub_api)
    ordered = registry.resolve_order()

    for step in ordered:
        current = state.get_step_status(step.step_id)
        if current == StepStatus.COMPLETED.value:
            click.echo(f"  [verify] {step.name}")
            if step.step_type.value == "validate":
                result = step.execute(state, dry_run=False)
                status_label = "OK" if result == StepStatus.COMPLETED else "FAIL"
                click.echo(f"    -> {status_label}")
            else:
                click.echo("    -> skipped (not a validation step)")


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show the current status of all setup steps."""
    state = _load_state(ctx.obj["state_file"])
    # Status doesn't need real APIs — use dummy config
    config = BoomiConfig()
    registry = _build_registry(config, None, None)
    engine = Engine(registry, state)
    summary = engine.get_status_summary()

    if not summary:
        click.echo("No steps registered.")
        return

    click.echo(f"{'Step':<40} {'Type':<10} {'Status':<12}")
    click.echo("-" * 62)
    for entry in summary:
        click.echo(f"{entry['name']:<40} {entry['type']:<10} {entry['status']:<12}")


@cli.command("run-step")
@click.argument("step_id")
@click.option("--dry-run", is_flag=True, help="Print what would happen without calling APIs.")
@click.pass_context
def run_step(ctx: click.Context, step_id: str, dry_run: bool) -> None:
    """Run a specific step (and its dependencies if needed)."""
    state = _load_state(ctx.obj["state_file"])
    config = load_config(existing_state_config=state.config, interactive=not dry_run)

    if not dry_run and not config.is_complete:
        click.echo("Error: configuration is incomplete. Run 'configure' first.")
        raise SystemExit(1)

    state.update_config(config.to_state_dict())
    platform_api, datahub_api = _init_apis(config)
    registry = _build_registry(config, platform_api, datahub_api)

    try:
        registry.get(step_id)
    except KeyError:
        click.echo(f"Error: unknown step '{step_id}'")
        raise SystemExit(1)

    engine = Engine(registry, state)
    engine.run(dry_run=dry_run, target_step=step_id)


@cli.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def reset(ctx: click.Context, confirm: bool) -> None:
    """Reset all progress (deletes state file and recreates it)."""
    state_path = Path(ctx.obj["state_file"])
    if not state_path.exists():
        click.echo("No state file found. Nothing to reset.")
        return

    if not confirm:
        click.confirm("This will delete all setup progress. Continue?", abort=True)

    state_path.unlink()
    SetupState.create(state_path)
    click.echo("State reset. All progress cleared.")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()

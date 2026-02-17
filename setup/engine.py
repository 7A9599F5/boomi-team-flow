"""Step registry and execution engine for Boomi Build Guide Setup Automation."""
from __future__ import annotations

from collections import deque
from enum import Enum
from typing import Protocol, runtime_checkable

import click

from setup.state import SetupState


class StepType(str, Enum):
    """Automation level for a build step."""

    AUTO = "auto"          # Fully automated — no user interaction
    SEMI = "semi"          # Partially automated — may prompt for input
    MANUAL = "manual"      # Manual — prints instructions, user performs action
    VALIDATE = "validate"  # Validation — checks that a prior step was done correctly


class StepStatus(str, Enum):
    """Execution status of a step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@runtime_checkable
class Step(Protocol):
    """Protocol that all build steps must satisfy."""

    @property
    def step_id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def step_type(self) -> StepType: ...

    @property
    def depends_on(self) -> list[str]: ...

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus: ...


class StepRegistry:
    """Maintains an ordered collection of build steps."""

    def __init__(self) -> None:
        self._steps: dict[str, Step] = {}
        self._order: list[str] = []

    def register(self, step: Step) -> None:
        """Register a step instance. Duplicate IDs raise ValueError."""
        if step.step_id in self._steps:
            raise ValueError(f"Duplicate step ID: {step.step_id}")
        self._steps[step.step_id] = step
        self._order.append(step.step_id)

    def get(self, step_id: str) -> Step:
        return self._steps[step_id]

    @property
    def step_ids(self) -> list[str]:
        return list(self._order)

    @property
    def steps(self) -> list[Step]:
        return [self._steps[sid] for sid in self._order]

    def resolve_order(self) -> list[Step]:
        """Return steps in topologically sorted order based on depends_on.

        Raises ValueError on missing dependencies or cycles.
        """
        # Build adjacency and in-degree
        in_degree: dict[str, int] = {sid: 0 for sid in self._order}
        dependents: dict[str, list[str]] = {sid: [] for sid in self._order}

        for sid in self._order:
            step = self._steps[sid]
            for dep in step.depends_on:
                if dep not in self._steps:
                    raise ValueError(
                        f"Step '{sid}' depends on unknown step '{dep}'"
                    )
                in_degree[sid] += 1
                dependents[dep].append(sid)

        # Kahn's algorithm — prefer registration order for stable sorting
        queue: deque[str] = deque()
        for sid in self._order:
            if in_degree[sid] == 0:
                queue.append(sid)

        sorted_ids: list[str] = []
        while queue:
            sid = queue.popleft()
            sorted_ids.append(sid)
            for dependent in dependents[sid]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(sorted_ids) != len(self._order):
            raise ValueError("Cycle detected in step dependencies")

        return [self._steps[sid] for sid in sorted_ids]


class Engine:
    """Executes registered steps in dependency order, with resume support."""

    def __init__(self, registry: StepRegistry, state: SetupState) -> None:
        self.registry = registry
        self.state = state

    def _is_satisfied(self, step: Step) -> bool:
        """Check if all dependencies of a step are completed."""
        for dep_id in step.depends_on:
            dep_status = self.state.get_step_status(dep_id)
            if dep_status != StepStatus.COMPLETED.value:
                return False
        return True

    def run(
        self,
        dry_run: bool = False,
        target_step: str | None = None,
    ) -> None:
        """Execute steps in dependency order.

        Args:
            dry_run: If True, print what would happen without calling APIs.
            target_step: If set, run only up to and including this step.
        """
        ordered = self.registry.resolve_order()

        for step in ordered:
            current_status = self.state.get_step_status(step.step_id)

            # Skip completed steps
            if current_status == StepStatus.COMPLETED.value:
                click.echo(f"  [skip] {step.name} (already completed)")
                continue

            # Block on unmet dependencies
            if not self._is_satisfied(step):
                unmet = [
                    d for d in step.depends_on
                    if self.state.get_step_status(d) != StepStatus.COMPLETED.value
                ]
                click.echo(
                    f"  [blocked] {step.name} — waiting on: {', '.join(unmet)}"
                )
                break

            # Dry-run mode
            if dry_run:
                click.echo(f"  [dry-run] Would execute: {step.name} ({step.step_type.value})")
                if step.step_id == target_step:
                    break
                continue

            # Execute (handles pending, in_progress, and failed)
            click.echo(f"  [run] {step.name} ({step.step_type.value})")
            self.state.set_step_status(step.step_id, StepStatus.IN_PROGRESS.value)

            try:
                result = step.execute(self.state, dry_run=dry_run)
                self.state.set_step_status(step.step_id, result.value)

                if result == StepStatus.FAILED:
                    click.echo(f"  [FAILED] {step.name} — stopping execution")
                    break

                click.echo(f"  [done] {step.name} -> {result.value}")

            except Exception as exc:
                self.state.set_step_status(
                    step.step_id, StepStatus.FAILED.value, error=str(exc)
                )
                click.echo(f"  [ERROR] {step.name}: {exc}")
                break

            if step.step_id == target_step:
                break

    def get_status_summary(self) -> list[dict[str, str]]:
        """Return a summary of all steps and their statuses."""
        ordered = self.registry.resolve_order()
        summary = []
        for step in ordered:
            status = self.state.get_step_status(step.step_id) or "pending"
            summary.append({
                "step_id": step.step_id,
                "name": step.name,
                "type": step.step_type.value,
                "status": status,
            })
        return summary

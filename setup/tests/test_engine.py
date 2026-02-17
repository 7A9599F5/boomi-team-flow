"""Tests for setup.engine — StepRegistry and Engine."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from setup.engine import Engine, StepRegistry, StepStatus, StepType
from setup.state import SetupState


class ConcreteStep:
    """Minimal concrete step for testing the engine."""

    def __init__(
        self,
        step_id: str,
        name: str = "",
        step_type: StepType = StepType.AUTO,
        depends_on: list[str] | None = None,
        execute_result: StepStatus = StepStatus.COMPLETED,
    ) -> None:
        self._step_id = step_id
        self._name = name or f"Test Step {step_id}"
        self._step_type = step_type
        self._depends_on = depends_on or []
        self._execute_result = execute_result
        self.execute_called = False

    @property
    def step_id(self) -> str:
        return self._step_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def step_type(self) -> StepType:
        return self._step_type

    @property
    def depends_on(self) -> list[str]:
        return self._depends_on

    def execute(self, state: SetupState, dry_run: bool = False) -> StepStatus:
        self.execute_called = True
        return self._execute_result


class TestStepRegistry:
    def test_step_registration(self) -> None:
        """Register steps, verify they're stored."""
        registry = StepRegistry()
        step_a = ConcreteStep("a")
        step_b = ConcreteStep("b")

        registry.register(step_a)
        registry.register(step_b)

        assert registry.step_ids == ["a", "b"]
        assert registry.get("a") is step_a
        assert registry.get("b") is step_b
        assert len(registry.steps) == 2

    def test_duplicate_step_id_raises(self) -> None:
        """Registering same ID twice raises ValueError."""
        registry = StepRegistry()
        registry.register(ConcreteStep("dup"))

        with pytest.raises(ValueError, match="Duplicate step ID: dup"):
            registry.register(ConcreteStep("dup"))

    def test_dependency_resolution_order(self) -> None:
        """Steps with deps come after their deps."""
        registry = StepRegistry()
        # Register in reverse dependency order
        step_c = ConcreteStep("c", depends_on=["b"])
        step_b = ConcreteStep("b", depends_on=["a"])
        step_a = ConcreteStep("a")

        registry.register(step_c)
        registry.register(step_b)
        registry.register(step_a)

        ordered = registry.resolve_order()
        ids = [s.step_id for s in ordered]

        assert ids.index("a") < ids.index("b")
        assert ids.index("b") < ids.index("c")

    def test_missing_dependency_raises(self) -> None:
        """Dependency on unknown step raises ValueError."""
        registry = StepRegistry()
        registry.register(ConcreteStep("x", depends_on=["nonexistent"]))

        with pytest.raises(ValueError, match="unknown step 'nonexistent'"):
            registry.resolve_order()

    def test_cycle_detection(self) -> None:
        """Circular deps raise ValueError."""
        registry = StepRegistry()
        registry.register(ConcreteStep("a", depends_on=["b"]))
        registry.register(ConcreteStep("b", depends_on=["a"]))

        with pytest.raises(ValueError, match="Cycle detected"):
            registry.resolve_order()

    def test_independent_steps_preserve_registration_order(self) -> None:
        """Independent steps appear in registration order."""
        registry = StepRegistry()
        registry.register(ConcreteStep("z"))
        registry.register(ConcreteStep("m"))
        registry.register(ConcreteStep("a"))

        ordered = registry.resolve_order()
        ids = [s.step_id for s in ordered]
        assert ids == ["z", "m", "a"]


class TestEngine:
    def _make_engine(
        self, tmp_path: Path, steps: list[ConcreteStep]
    ) -> tuple[Engine, SetupState, list[ConcreteStep]]:
        """Helper to create engine with steps and a fresh state."""
        state_path = tmp_path / "state.json"
        state = SetupState.create(path=state_path)
        registry = StepRegistry()
        for step in steps:
            registry.register(step)
        engine = Engine(registry, state)
        return engine, state, steps

    @patch("setup.engine.click.echo")
    def test_skip_completed_steps(self, mock_echo: MagicMock, tmp_path: Path) -> None:
        """Engine skips steps already marked completed in state."""
        step_a = ConcreteStep("a")
        step_b = ConcreteStep("b")
        engine, state, _ = self._make_engine(tmp_path, [step_a, step_b])

        # Pre-mark step_a as completed
        state.set_step_status("a", StepStatus.COMPLETED.value)

        engine.run()

        assert not step_a.execute_called
        assert step_b.execute_called

    @patch("setup.engine.click.echo")
    def test_block_on_unmet_dependencies(self, mock_echo: MagicMock, tmp_path: Path) -> None:
        """Engine stops at steps with incomplete deps."""
        step_a = ConcreteStep("a", execute_result=StepStatus.FAILED)
        step_b = ConcreteStep("b", depends_on=["a"])
        engine, state, _ = self._make_engine(tmp_path, [step_a, step_b])

        engine.run()

        # step_a executed but failed; step_b should not execute
        assert step_a.execute_called
        assert not step_b.execute_called

    @patch("setup.engine.click.echo")
    def test_dry_run_mode(self, mock_echo: MagicMock, tmp_path: Path) -> None:
        """Engine doesn't call execute in dry run."""
        step_a = ConcreteStep("a")
        step_b = ConcreteStep("b", depends_on=["a"])
        engine, state, _ = self._make_engine(tmp_path, [step_a, step_b])

        engine.run(dry_run=True)

        assert not step_a.execute_called
        assert not step_b.execute_called

        # Verify dry-run messages were printed
        call_args = [str(call) for call in mock_echo.call_args_list]
        dry_run_msgs = [c for c in call_args if "dry-run" in c]
        assert len(dry_run_msgs) >= 1

    @patch("setup.engine.click.echo")
    def test_target_step_stops_execution(self, mock_echo: MagicMock, tmp_path: Path) -> None:
        """Engine stops after target_step."""
        step_a = ConcreteStep("a")
        step_b = ConcreteStep("b")
        step_c = ConcreteStep("c")
        engine, state, _ = self._make_engine(tmp_path, [step_a, step_b, step_c])

        engine.run(target_step="b")

        assert step_a.execute_called
        assert step_b.execute_called
        assert not step_c.execute_called

    @patch("setup.engine.click.echo")
    def test_exception_in_step_stops_engine(self, mock_echo: MagicMock, tmp_path: Path) -> None:
        """Engine stops and marks step FAILED on exception."""
        step_a = ConcreteStep("a")
        step_a.execute = MagicMock(side_effect=RuntimeError("boom"))  # type: ignore[assignment]
        step_b = ConcreteStep("b")
        engine, state, _ = self._make_engine(tmp_path, [step_a, step_b])

        engine.run()

        assert state.get_step_status("a") == StepStatus.FAILED.value
        assert not step_b.execute_called

    @patch("setup.engine.click.echo")
    def test_get_status_summary(self, mock_echo: MagicMock, tmp_path: Path) -> None:
        """get_status_summary returns all steps with their statuses."""
        step_a = ConcreteStep("a", name="Step Alpha")
        step_b = ConcreteStep("b", name="Step Beta")
        engine, state, _ = self._make_engine(tmp_path, [step_a, step_b])
        state.set_step_status("a", "completed")

        summary = engine.get_status_summary()
        assert len(summary) == 2
        assert summary[0] == {
            "step_id": "a",
            "name": "Step Alpha",
            "type": "auto",
            "status": "completed",
        }
        assert summary[1] == {
            "step_id": "b",
            "name": "Step Beta",
            "type": "auto",
            "status": "pending",
        }

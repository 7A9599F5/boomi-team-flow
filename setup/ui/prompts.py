"""Manual step interaction handler for Boomi Build Guide Setup Automation."""
from __future__ import annotations

import os
import re
from typing import Callable, Optional

from rich.panel import Panel
from rich.prompt import Prompt

from setup.ui.console import console, print_build_guide_ref, print_error

# Boomi component UUID pattern: 8-4-4-4-12 hex
_BOOMI_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def guide_and_wait(
    instructions: str, build_guide_ref: str | None = None
) -> None:
    """Display instructions panel, optionally reference build guide, wait for Enter."""
    console.print(Panel(instructions, border_style="cyan"))
    if build_guide_ref:
        print_build_guide_ref(build_guide_ref)
    console.input("[dim]Press Enter to continue...[/dim]")


def guide_and_confirm(
    instructions: str, question: str = "Have you completed this step?"
) -> bool:
    """Display instructions and ask y/n confirmation."""
    console.print(Panel(instructions, border_style="cyan"))
    from rich.prompt import Confirm

    return Confirm.ask(question)


def guide_and_collect(
    instructions: str,
    prompt: str,
    validator: Callable[[str], bool] | None = None,
) -> str:
    """Display instructions, collect text input, optionally validate."""
    console.print(Panel(instructions, border_style="cyan"))
    while True:
        value = Prompt.ask(prompt)
        if validator is None or validator(value):
            return value
        print_error("Invalid input. Please try again.")


def guide_wait_verify(
    instructions: str,
    verify_fn: Callable[[], bool],
    retry_message: str = "Verification failed. Please check and try again.",
) -> bool:
    """Display instructions, wait, run verify_fn. Loop on failure."""
    console.print(Panel(instructions, border_style="cyan"))
    while True:
        console.input("[dim]Press Enter to verify...[/dim]")
        if verify_fn():
            return True
        print_error(retry_message)
        from rich.prompt import Confirm

        if not Confirm.ask("Retry?"):
            return False


def prompt_credential(
    name: str, env_var: str, is_secret: bool = False
) -> str:
    """Check env var first; if missing, prompt user (mask input if is_secret)."""
    value = os.environ.get(env_var, "")
    if value:
        console.print(f"  [green]{name}[/green] loaded from ${env_var}")
        return value
    return Prompt.ask(name, password=is_secret)


def prompt_choice(question: str, choices: list[str]) -> int:
    """Display numbered list of choices, return selected index."""
    console.print(f"\n{question}")
    for i, choice in enumerate(choices, 1):
        console.print(f"  [bold]{i}[/bold]. {choice}")
    while True:
        raw = Prompt.ask("Select", default="1")
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return idx
        except ValueError:
            pass
        print_error(f"Please enter a number between 1 and {len(choices)}.")


def collect_component_id(prompt_text: str) -> str:
    """Prompt for and validate a Boomi component UUID format."""
    while True:
        value = Prompt.ask(prompt_text)
        if _BOOMI_UUID_RE.match(value.strip()):
            return value.strip()
        print_error(
            "Invalid Boomi component ID. Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        )

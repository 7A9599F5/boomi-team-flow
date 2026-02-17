"""Rich-based console output for Boomi Build Guide Setup Automation."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

console = Console()


def print_header(text: str) -> None:
    """Display a header panel with bold title."""
    console.print(Panel(Text(text, style="bold"), border_style="blue"))


def print_step(step_id: str, name: str, step_type: str) -> None:
    """Display a formatted step header like '[2.3] Create HTTP Operations [AUTO]'."""
    label = Text()
    label.append(f"[{step_id}] ", style="bold cyan")
    label.append(name, style="bold")
    label.append(f" [{step_type}]", style="dim")
    console.print(label)


def print_success(text: str) -> None:
    """Display a success message with green checkmark."""
    console.print(f"[green]  {text}[/green]")


def print_error(text: str) -> None:
    """Display an error message with red X."""
    console.print(f"[red]  {text}[/red]")


def print_warning(text: str) -> None:
    """Display a warning message with yellow prefix."""
    console.print(f"[yellow]  {text}[/yellow]")


def print_info(text: str) -> None:
    """Display an info message with blue prefix."""
    console.print(f"[blue]  {text}[/blue]")


def print_table(title: str, columns: list[str], rows: list[list[str]]) -> None:
    """Display a Rich table with the given columns and rows."""
    table = Table(title=title)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def print_progress(current: int, total: int, description: str) -> None:
    """Display a single-line progress indicator."""
    console.print(f"  [{current}/{total}] {description}")


def print_status_table(steps: dict) -> None:
    """Display an overview table of all steps with colored status."""
    table = Table(title="Build Progress")
    table.add_column("Step", style="bold")
    table.add_column("Name")
    table.add_column("Status")

    status_styles = {
        "completed": "green",
        "in_progress": "yellow",
        "failed": "red",
        "pending": "dim",
    }

    for step_id, info in steps.items():
        status = info.get("status", "pending")
        style = status_styles.get(status, "dim")
        name = info.get("name", step_id)
        table.add_row(step_id, name, Text(status, style=style))

    console.print(table)


def print_component_table(component_ids: dict) -> None:
    """Display all stored component IDs grouped by category."""
    for category, items in component_ids.items():
        if items is None:
            continue
        if isinstance(items, str):
            # Scalar value (e.g., flow_service)
            console.print(f"  [bold]{category}[/bold]: {items}")
            continue
        if not items:
            continue
        table = Table(title=category)
        table.add_column("Name")
        table.add_column("Component ID")
        for name, comp_id in items.items():
            table.add_row(name, comp_id)
        console.print(table)


def print_build_guide_ref(file: str, section: str = "") -> None:
    """Display a build guide reference."""
    ref = f"docs/build-guide/{file}"
    if section:
        ref += f" {section}"
    console.print(f"  [dim]See: {ref}[/dim]")


def confirm(question: str) -> bool:
    """Prompt for y/n confirmation."""
    return Confirm.ask(question)

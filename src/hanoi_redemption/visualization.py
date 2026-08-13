"""Rich terminal rendering and animated replay for evaluated move sequences."""

from __future__ import annotations

import time

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .game import HanoiGame, IllegalMove
from .models import BenchmarkResult, HanoiMove
from .protocols import protocol_label

COLORS = ["bright_cyan", "bright_magenta", "bright_green", "yellow", "blue", "red"]


def render_game(game: HanoiGame, title: str, subtitle: str = "") -> RenderableType:
    width = max(9, (game.disks * 2) + 3)
    table = Table.grid(expand=False, padding=(0, 1))
    for _ in range(3):
        table.add_column(width=width, justify="center")

    for level in range(game.disks - 1, -1, -1):
        row: list[RenderableType] = []
        for peg in game.pegs:
            if level < len(peg):
                disk = peg[level]
                disk_text = "█" * ((disk * 2) + 1)
                row.append(Text(disk_text, style=f"bold {COLORS[(disk - 1) % len(COLORS)]}"))
            else:
                row.append(Text("│", style="dim"))
        table.add_row(*row)

    table.add_row(*(Text("━" * width, style="dim") for _ in range(3)))
    table.add_row(*(Text(f"PEG {index}", style="bold") for index in range(3)))
    content: RenderableType = Align.center(table)
    if subtitle:
        content = Group(content, Align.center(Text(subtitle, style="dim")))
    return Panel(content, title=title, border_style="bright_blue")


def replay(
    result: BenchmarkResult,
    *,
    console: Console | None = None,
    delay: float = 0.08,
) -> None:
    console = console or Console()
    game = HanoiGame(result.config.disks)
    title = (
        f"{result.config.model} · {result.config.reasoning_effort} · "
        f"{protocol_label(result.config.protocol)} · {result.config.disks} disks"
    )

    def frame(move_number: int, move: HanoiMove | None = None, error: str | None = None):
        if error:
            subtitle = f"Move {move_number}: {error}"
        elif move:
            subtitle = f"Move {move_number}/{len(result.moves)} · {move.compact()}"
        else:
            subtitle = "Initial state"
        return render_game(game, title, subtitle)

    with Live(frame(0), console=console, refresh_per_second=30, transient=False) as live:
        if delay:
            time.sleep(delay)
        for index, move in enumerate(result.moves, start=1):
            try:
                game.apply(move)
            except IllegalMove as exc:
                live.update(frame(index, move, f"INVALID · {exc}"), refresh=True)
                break
            live.update(frame(index, move), refresh=True)
            if delay:
                time.sleep(delay)

    status_style = "bold green" if result.validation.solved else "bold red"
    console.print(
        f"Result: [{status_style}]{result.validation.status.upper()}[/] · "
        f"{result.validation.valid_moves}/{result.validation.returned_moves} valid moves · "
        f"minimum {result.validation.optimal_moves}"
    )


def result_summary(result: BenchmarkResult) -> str:
    usage = result.total_usage
    return (
        f"{result.validation.status.upper()} · moves "
        f"{result.validation.valid_moves}/{result.validation.returned_moves} · "
        f"{result.processing_time_seconds:.2f}s · {usage.total_tokens:,} tokens · "
        f"run {result.run_id[:10]}"
    )

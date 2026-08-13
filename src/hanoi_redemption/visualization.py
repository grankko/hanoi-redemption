"""Rich terminal rendering and animated replay for evaluated move sequences."""

from __future__ import annotations

import os
import select
import sys
import time
from collections.abc import Callable
from types import TracebackType

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - exercised on non-POSIX systems
    termios = None
    tty = None

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


class _ReplayControls:
    def __init__(
        self,
        *,
        enabled: bool,
        skip_requested: Callable[[], bool] | None = None,
    ) -> None:
        self.enabled = enabled or skip_requested is not None
        self._skip_requested = skip_requested
        self._fd: int | None = None
        self._original_terminal_settings: list | None = None

    def __enter__(self) -> _ReplayControls:
        if (
            not self.enabled
            or self._skip_requested is not None
            or termios is None
            or tty is None
            or not sys.stdin.isatty()
        ):
            self.enabled = self._skip_requested is not None
            return self
        try:
            self._fd = sys.stdin.fileno()
            self._original_terminal_settings = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        except (AttributeError, OSError, termios.error):
            self._fd = None
            self._original_terminal_settings = None
            self.enabled = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if (
            termios is not None
            and self._fd is not None
            and self._original_terminal_settings is not None
        ):
            termios.tcsetattr(
                self._fd,
                termios.TCSADRAIN,
                self._original_terminal_settings,
            )

    def wait(self, delay: float) -> bool:
        if self._skip_requested is not None and self._skip_requested():
            return True
        if self._fd is None:
            if delay:
                time.sleep(delay)
            return self._skip_requested is not None and self._skip_requested()

        ready, _, _ = select.select([self._fd], [], [], delay)
        while ready:
            if os.read(self._fd, 1).lower() == b"s":
                return True
            ready, _, _ = select.select([self._fd], [], [], 0)
        return False


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
    skip_requested: Callable[[], bool] | None = None,
) -> None:
    console = console or Console()
    game = HanoiGame(result.config.disks)
    title = (
        f"{result.config.model} · {result.config.reasoning_effort} · "
        f"{protocol_label(result.config.protocol)} · {result.config.disks} disks"
    )

    def frame(
        move_number: int,
        move: HanoiMove | None = None,
        error: str | None = None,
        *,
        show_skip_hint: bool = False,
        skipped: bool = False,
    ):
        if error:
            subtitle = f"Move {move_number}: {error}"
        elif move:
            subtitle = f"Move {move_number}/{len(result.moves)} · {move.compact()}"
        else:
            subtitle = "Initial state"
        if show_skip_hint:
            subtitle += " · press s to skip animation"
        elif skipped:
            subtitle += " · animation skipped"
        return render_game(game, title, subtitle)

    controls_enabled = delay > 0 and console.is_terminal
    with _ReplayControls(
        enabled=controls_enabled,
        skip_requested=skip_requested,
    ) as controls:
        with Live(
            frame(0, show_skip_hint=controls.enabled),
            console=console,
            refresh_per_second=30,
            transient=False,
        ) as live:
            skipped = controls.wait(delay)
            last_move: HanoiMove | None = None
            last_index = 0
            for index, move in enumerate(result.moves, start=1):
                last_move = move
                last_index = index
                try:
                    game.apply(move)
                except IllegalMove as exc:
                    live.update(frame(index, move, f"INVALID · {exc}"), refresh=True)
                    break
                if skipped:
                    continue
                live.update(
                    frame(index, move, show_skip_hint=controls.enabled),
                    refresh=True,
                )
                skipped = controls.wait(delay)
            else:
                if skipped:
                    live.update(
                        frame(last_index, last_move, skipped=True),
                        refresh=True,
                    )

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

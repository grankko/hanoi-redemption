"""Deterministic Towers of Hanoi state machine and solution validator."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from .models import HanoiMove, OutcomeStatus, ValidationReport


class IllegalMove(ValueError):
    """Raised when a move violates the puzzle contract."""


@dataclass(slots=True)
class HanoiGame:
    """Three pegs stored bottom-to-top, matching the paper's notation."""

    disks: int
    pegs: list[list[int]]

    def __init__(self, disks: int):
        if not 1 <= disks <= 20:
            raise ValueError("disk count must be between 1 and 20")
        self.disks = disks
        self.pegs = [list(range(disks, 0, -1)), [], []]

    def copy(self) -> HanoiGame:
        game = HanoiGame(self.disks)
        game.pegs = [peg.copy() for peg in self.pegs]
        return game

    def snapshot(self) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
        return tuple(tuple(peg) for peg in self.pegs)  # type: ignore[return-value]

    @property
    def solved(self) -> bool:
        return self.pegs == [[], [], list(range(self.disks, 0, -1))]

    def apply(self, move: HanoiMove) -> None:
        if move.source == move.destination:
            raise IllegalMove(f"source and destination are both peg {move.source}")

        source = self.pegs[move.source]
        destination = self.pegs[move.destination]
        if not source:
            raise IllegalMove(f"source peg {move.source} is empty")

        top_disk = source[-1]
        if move.disk != top_disk:
            raise IllegalMove(
                f"move names disk {move.disk}, but the top of peg {move.source} is disk {top_disk}"
            )
        if destination and destination[-1] < move.disk:
            raise IllegalMove(
                f"disk {move.disk} cannot be placed on smaller disk {destination[-1]}"
            )

        source.pop()
        destination.append(move.disk)


def optimal_move_count(disks: int) -> int:
    return (2**disks) - 1


def optimal_solution(disks: int) -> list[HanoiMove]:
    return list(_optimal_moves(disks, 0, 2, 1))


def _optimal_moves(disks: int, source: int, target: int, auxiliary: int) -> Iterator[HanoiMove]:
    if disks == 0:
        return
    yield from _optimal_moves(disks - 1, source, auxiliary, target)
    yield HanoiMove(disk=disks, source=source, destination=target)
    yield from _optimal_moves(disks - 1, auxiliary, target, source)


def evaluate_moves(
    disks: int,
    moves: Iterable[HanoiMove],
    *,
    move_budget: int | None = None,
) -> ValidationReport:
    """Apply every returned move and report the first failure or final goal state."""

    materialized = list(moves)
    game = HanoiGame(disks)
    valid_moves = 0
    status: OutcomeStatus
    error: str | None = None
    error_move: int | None = None

    for index, move in enumerate(materialized, start=1):
        if move_budget is not None and index > move_budget:
            status = "move_budget_exceeded"
            error = f"move budget of {move_budget} exceeded"
            error_move = index
            break
        try:
            game.apply(move)
        except IllegalMove as exc:
            status = "invalid_move"
            error = str(exc)
            error_move = index
            break
        valid_moves += 1
    else:
        status = "pass" if game.solved else "incomplete"
        if not game.solved:
            error = "all returned moves were legal, but the target state was not reached"

    minimum = optimal_move_count(disks)
    solved = status == "pass"
    return ValidationReport(
        status=status,
        solved=solved,
        returned_moves=len(materialized),
        valid_moves=valid_moves,
        optimal_moves=minimum,
        optimal=solved and len(materialized) == minimum,
        efficiency_percent=round((minimum / len(materialized)) * 100, 2)
        if solved and materialized
        else None,
        disks_on_target=len(game.pegs[2]),
        first_error_move=error_move,
        error=error,
    )

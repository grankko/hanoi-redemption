import pytest

from hanoi_redemption.game import (
    HanoiGame,
    IllegalMove,
    evaluate_moves,
    optimal_move_count,
    optimal_solution,
)
from hanoi_redemption.models import HanoiMove


@pytest.mark.parametrize("disks", range(1, 9))
def test_optimal_solution_is_valid_and_complete(disks: int) -> None:
    moves = optimal_solution(disks)

    report = evaluate_moves(disks, moves)

    assert len(moves) == optimal_move_count(disks)
    assert report.status == "pass"
    assert report.solved is True
    assert report.optimal is True
    assert report.efficiency_percent == 100.0


def test_game_uses_paper_bottom_to_top_notation() -> None:
    game = HanoiGame(3)

    assert game.pegs == [[3, 2, 1], [], []]
    game.apply(HanoiMove(disk=1, source=0, destination=2))
    assert game.pegs == [[3, 2], [], [1]]


def test_named_disk_must_match_top_disk() -> None:
    game = HanoiGame(3)

    with pytest.raises(IllegalMove, match="names disk 3"):
        game.apply(HanoiMove(disk=3, source=0, destination=2))


def test_larger_disk_cannot_land_on_smaller_disk() -> None:
    game = HanoiGame(3)
    game.apply(HanoiMove(disk=1, source=0, destination=2))

    with pytest.raises(IllegalMove, match="smaller disk 1"):
        game.apply(HanoiMove(disk=2, source=0, destination=2))


def test_validator_reports_first_invalid_move() -> None:
    moves = [
        HanoiMove(disk=1, source=0, destination=2),
        HanoiMove(disk=3, source=0, destination=1),
    ]

    report = evaluate_moves(3, moves)

    assert report.status == "invalid_move"
    assert report.valid_moves == 1
    assert report.first_error_move == 2
    assert "top of peg 0 is disk 2" in (report.error or "")


def test_validator_distinguishes_legal_but_incomplete_solution() -> None:
    report = evaluate_moves(3, optimal_solution(3)[:3])

    assert report.status == "incomplete"
    assert report.valid_moves == 3
    assert report.first_error_move is None

from hanoi_redemption.game import HanoiGame
from hanoi_redemption.prompts import apple_prompt, interactive_prompt


def test_apple_prompt_preserves_paper_contract() -> None:
    system, user = apple_prompt(4)

    assert "zero-indexed" in system
    assert "complete, explicit list of moves" in system
    assert "[[3, 2, 1], [], []]" in system
    assert "Peg 0: [4, 3, 2, 1]" in user
    assert "Peg 2: [4, 3, 2, 1]" in user


def test_algorithm_variant_includes_recursive_ablation() -> None:
    system, _ = apple_prompt(4, "algorithm")

    assert "Solve(n - 1, source, auxiliary, target)" in system
    assert "complete explicit move list" in system


def test_interactive_prompt_contains_current_state() -> None:
    game = HanoiGame(3)
    system, user = interactive_prompt(game, 1, [])

    assert "one move at a time" in system
    assert "Peg 0: [3, 2, 1]" in user
    assert "Turn: 1" in user

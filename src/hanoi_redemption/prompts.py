"""Auditable prompts derived from the Tower of Hanoi setup in Apple's paper."""

from __future__ import annotations

from .game import HanoiGame
from .models import HanoiMove, PromptVariant

PROMPT_VERSION = "apple-hanoi-v1"

APPLE_SYSTEM_PROMPT = """You are a helpful assistant. Solve this puzzle for me.

There are three pegs and n disks of different sizes stacked on the first peg. The disks are
numbered from 1 (smallest) to n (largest). Disk moves must follow these rules:

1. Only one disk can be moved at a time.
2. Each move takes the top disk from one peg and places it on top of another peg.
3. A larger disk may not be placed on top of a smaller disk.

The goal is to move the entire stack to the third peg.

Example: with 3 disks, the initial state is [[3, 2, 1], [], []], and a solution is:
[[1, 0, 2], [2, 0, 1], [1, 2, 1], [3, 0, 2],
 [1, 1, 0], [2, 1, 2], [1, 0, 2]]

Peg positions are zero-indexed. Return the complete, explicit list of moves. Do not return code,
pseudocode, an abbreviated pattern, or an algorithm in place of the moves. Each move must identify
the disk, source peg, and destination peg."""

ALGORITHM_APPENDIX = """

You may use this recursive algorithm as a scratchpad:

Solve(n, source, target, auxiliary):
  if n == 1: move disk 1 from source to target
  otherwise:
    Solve(n - 1, source, auxiliary, target)
    move disk n from source to target
    Solve(n - 1, auxiliary, target, source)

Even with this algorithm, return the complete explicit move list rather than code."""

INTERACTIVE_SYSTEM_PROMPT = """You are playing Towers of Hanoi one move at a time in a validated
environment. Move all disks from peg 0 to peg 2. Only the top disk may move, only one disk may move
at a time, and a larger disk may never be placed on a smaller disk. Return exactly one legal next
move. The environment will apply it and show you the next state. Do not return a full solution."""


def apple_prompt(disks: int, variant: PromptVariant = "standard") -> tuple[str, str]:
    system = APPLE_SYSTEM_PROMPT
    if variant == "algorithm":
        system += ALGORITHM_APPENDIX

    stack = ", ".join(str(disk) for disk in range(disks, 0, -1))
    user = f"""I have a puzzle with {disks} disks of different sizes.

Initial configuration (bottom to top):
- Peg 0: [{stack}]
- Peg 1: []
- Peg 2: []

Goal configuration (bottom to top):
- Peg 0: []
- Peg 1: []
- Peg 2: [{stack}]

Find the complete sequence of moves that transforms the initial configuration into the goal
configuration while obeying every rule."""
    return system, user


def interactive_prompt(
    game: HanoiGame,
    turn: int,
    recent_moves: list[HanoiMove],
) -> tuple[str, str]:
    recent = recent_moves[-10:]
    history = "\n".join(
        f"- {index}: [{move.disk}, {move.source}, {move.destination}]"
        for index, move in enumerate(recent, start=max(1, turn - len(recent)))
    )
    if not history:
        history = "- none"

    user = f"""Puzzle size: {game.disks} disks
Turn: {turn}
Current configuration, bottom to top:
- Peg 0: {game.pegs[0]}
- Peg 1: {game.pegs[1]}
- Peg 2: {game.pegs[2]}

Recent accepted moves:
{history}

Choose exactly one legal next move toward the goal."""
    return INTERACTIVE_SYSTEM_PROMPT, user

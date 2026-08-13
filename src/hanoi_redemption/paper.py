"""Concise, honest comparison with the paper's reported Hanoi results."""

from __future__ import annotations

from .models import BenchmarkResult

PAPER_BASELINE = (
    "Apple's 2025 paper used a strict one-response test: one illegal move failed the entire "
    "solution. Models were generally strong at 1–4 disks, degraded across 5–7 disks, and began "
    "collapsing around 7–8 disks. By roughly 9–10 disks, complete solutions were near zero.\n"
    "Interactive play keeps the same puzzle rules but changes the interaction: the model sees the "
    "updated board after every move. The paper did not test that setup, so its score is not "
    "directly comparable to the paper's one-response results."
)


def paper_comparison(result: BenchmarkResult) -> str:
    """Describe a single result against the paper without implying exact replication."""

    disks = result.config.disks
    solved = result.validation.solved
    if result.config.protocol == "interactive":
        return (
            "Not directly comparable: the paper required the complete move list in one response; "
            "it did not let the model observe the board and choose one move at a time."
        )
    if disks <= 4:
        if solved:
            return "Matches the paper's generally strong low-complexity region (1–4 disks)."
        return "Below the paper baseline: its tested models were generally strong at 1–4 disks."
    if disks <= 7:
        if solved:
            return "A pass in the paper's 5–7 disk transition region, where accuracy was degrading."
        return "Consistent with the paper's 5–7 disk transition region, where failures increased."
    if solved:
        return (
            "Notable: this model solved an 8+ disk instance, where the paper reported "
            "near-zero accuracy."
        )
    return (
        "Falls within the paper's reported collapse region (8+ disks), where its tested models "
        "had near-zero accuracy."
    )

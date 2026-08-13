"""Benchmark orchestration for one-shot and interactive Hanoi protocols."""

from __future__ import annotations

import math
import time
import uuid
from datetime import UTC, datetime
from typing import Protocol

from .game import HanoiGame, IllegalMove, evaluate_moves, optimal_move_count
from .models import (
    ApiCall,
    BenchmarkResult,
    HanoiMove,
    OutcomeStatus,
    RunConfig,
    ValidationReport,
    aggregate_token_usage,
)
from .providers import ProviderError, ProviderResponse


class HanoiProvider(Protocol):
    def solve(self, config: RunConfig) -> ProviderResponse: ...

    def next_move(
        self,
        config: RunConfig,
        game: HanoiGame,
        turn: int,
        moves: list[HanoiMove],
    ) -> ProviderResponse: ...


class BenchmarkRunner:
    def __init__(self, provider: HanoiProvider):
        self.provider = provider

    def run(self, config: RunConfig) -> BenchmarkResult:
        started = time.perf_counter()
        try:
            if config.protocol == "apple":
                moves, explanations, calls, validation = self._run_apple(config)
            else:
                moves, explanations, calls, validation = self._run_interactive(config)
        except ProviderError as exc:
            moves = []
            explanations = []
            calls = [exc.call] if exc.call else []
            validation = _error_report(config.disks, "api_error", str(exc))
        except Exception as exc:
            moves = []
            explanations = []
            calls = []
            validation = _error_report(config.disks, "malformed_response", str(exc))

        return BenchmarkResult(
            run_id=uuid.uuid4().hex,
            created_at=datetime.now(UTC),
            config=config,
            validation=validation,
            moves=moves,
            explanations=explanations,
            api_calls=calls,
            processing_time_seconds=time.perf_counter() - started,
            token_usage=aggregate_token_usage(calls),
        )

    def _run_apple(
        self, config: RunConfig
    ) -> tuple[list[HanoiMove], list[str], list[ApiCall], ValidationReport]:
        response = self.provider.solve(config)
        moves = response.value.moves
        return moves, [], [response.call], evaluate_moves(config.disks, moves)

    def _run_interactive(
        self, config: RunConfig
    ) -> tuple[list[HanoiMove], list[str], list[ApiCall], ValidationReport]:
        game = HanoiGame(config.disks)
        moves: list[HanoiMove] = []
        explanations: list[str] = []
        calls: list[ApiCall] = []
        budget = math.ceil(optimal_move_count(config.disks) * config.move_budget_multiplier)

        for turn in range(1, budget + 1):
            try:
                response = self.provider.next_move(config, game.copy(), turn, moves.copy())
            except ProviderError as exc:
                if exc.call:
                    calls.append(exc.call)
                report = evaluate_moves(config.disks, moves, move_budget=budget)
                report.status = "api_error"
                report.error = str(exc)
                return moves, explanations, calls, report
            decision = response.value
            calls.append(response.call)
            moves.append(decision.move)
            explanations.append(decision.explanation)
            try:
                game.apply(decision.move)
            except IllegalMove:
                return (
                    moves,
                    explanations,
                    calls,
                    evaluate_moves(config.disks, moves, move_budget=budget),
                )
            if game.solved:
                return (
                    moves,
                    explanations,
                    calls,
                    evaluate_moves(config.disks, moves, move_budget=budget),
                )

        report = evaluate_moves(config.disks, moves, move_budget=budget)
        if not report.solved and report.status == "incomplete":
            report.status = "move_budget_exceeded"
            report.error = f"target state not reached within {budget} moves"
        return moves, explanations, calls, report


def _error_report(disks: int, status: OutcomeStatus, error: str) -> ValidationReport:
    return ValidationReport(
        status=status,
        solved=False,
        returned_moves=0,
        valid_moves=0,
        optimal_moves=optimal_move_count(disks),
        optimal=False,
        disks_on_target=0,
        error=error,
    )

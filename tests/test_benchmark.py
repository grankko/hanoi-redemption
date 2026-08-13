import pytest

from hanoi_redemption.benchmark import BenchmarkRunner
from hanoi_redemption.models import ApiCall, HanoiMove, MoveDecision, RunConfig
from hanoi_redemption.providers import MockProvider, ProviderError, ProviderResponse


def config(protocol: str, disks: int = 3) -> RunConfig:
    return RunConfig(
        model="mock-optimal",
        reasoning_effort="none",
        disks=disks,
        trial=1,
        protocol=protocol,
        max_output_tokens=64_000,
        move_budget_multiplier=2.0,
    )


@pytest.mark.parametrize("protocol", ["apple", "interactive"])
def test_optimal_mock_passes_both_protocols(protocol: str) -> None:
    result = BenchmarkRunner(MockProvider("optimal")).run(config(protocol))

    assert result.validation.status == "pass"
    assert result.validation.optimal is True
    assert len(result.api_calls) == (1 if protocol == "apple" else 7)
    assert len(result.moves) == 7


@pytest.mark.parametrize("protocol", ["apple", "interactive"])
def test_invalid_mock_is_preserved_as_eval_failure(protocol: str) -> None:
    result = BenchmarkRunner(MockProvider("invalid")).run(config(protocol))

    assert result.validation.status == "invalid_move"
    assert result.validation.first_error_move == 1
    assert result.validation.error


def test_incomplete_apple_response_is_not_an_api_error() -> None:
    result = BenchmarkRunner(MockProvider("incomplete")).run(config("apple"))

    assert result.validation.status == "incomplete"
    assert result.validation.valid_moves > 0


def test_output_limited_apple_response_keeps_partial_game_and_call_usage() -> None:
    partial_moves = [
        HanoiMove(disk=1, source=0, destination=2),
        HanoiMove(disk=2, source=0, destination=1),
    ]

    class OutputLimitedProvider:
        def solve(self, config):
            raise ProviderError(
                "output limit reached",
                ApiCall(
                    response_id="resp_partial",
                    requested_model=config.model,
                    actual_model=config.model,
                    status="incomplete",
                    latency_seconds=1,
                ),
                outcome_status="incomplete",
                partial_moves=partial_moves,
            )

    result = BenchmarkRunner(OutputLimitedProvider()).run(config("apple"))

    assert result.validation.status == "incomplete"
    assert result.validation.solved is False
    assert result.validation.valid_moves == 2
    assert result.moves == partial_moves
    assert result.api_calls[0].response_id == "resp_partial"
    assert result.api_calls[0].status == "incomplete"


def test_result_accumulates_usage_without_special_cases() -> None:
    result = BenchmarkRunner(MockProvider("optimal")).run(config("apple"))

    assert result.total_usage.total_tokens == 0


def test_interactive_api_error_keeps_partial_game_and_call_history() -> None:
    class FailingProvider:
        calls = 0

        def next_move(self, config, game, turn, moves):
            self.calls += 1
            if self.calls == 1:
                return ProviderResponse(
                    MoveDecision(
                        move=HanoiMove(disk=1, source=0, destination=2),
                        explanation="first move",
                    ),
                    ApiCall(
                        requested_model=config.model,
                        status="completed",
                        latency_seconds=0,
                    ),
                )
            raise ProviderError(
                "connection lost",
                ApiCall(
                    requested_model=config.model,
                    status="error",
                    latency_seconds=0,
                ),
            )

    result = BenchmarkRunner(FailingProvider()).run(config("interactive"))

    assert result.validation.status == "api_error"
    assert result.validation.valid_moves == 1
    assert result.moves == [HanoiMove(disk=1, source=0, destination=2)]
    assert len(result.api_calls) == 2
    assert result.api_calls[-1].status == "error"


def test_interactive_output_limit_is_not_labeled_as_api_error() -> None:
    class OutputLimitedProvider:
        def next_move(self, config, game, turn, moves):
            raise ProviderError(
                "output limit reached",
                ApiCall(
                    response_id="resp_partial",
                    requested_model=config.model,
                    actual_model=config.model,
                    status="incomplete",
                    latency_seconds=1,
                ),
                outcome_status="incomplete",
            )

    result = BenchmarkRunner(OutputLimitedProvider()).run(config("interactive"))

    assert result.validation.status == "incomplete"
    assert result.validation.error == "output limit reached"
    assert result.api_calls[0].status == "incomplete"

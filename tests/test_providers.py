from types import SimpleNamespace

import pytest

from hanoi_redemption.models import HanoiMove, HanoiSolution, RunConfig
from hanoi_redemption.providers import OpenAIProvider, ProviderError


def config(reasoning: str = "medium") -> RunConfig:
    return RunConfig(
        model="test-model",
        reasoning_effort=reasoning,
        disks=3,
        trial=1,
        protocol="apple",
        max_output_tokens=64_000,
        move_budget_multiplier=2.0,
    )


class FakeResponses:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.request = None

    def parse(self, **request):
        self.request = request
        if self.error:
            raise self.error
        return self.response


def fake_response(parsed):
    return SimpleNamespace(
        id="resp_test",
        model="actual-test-model",
        status="completed",
        usage=SimpleNamespace(
            input_tokens=11,
            input_tokens_details=SimpleNamespace(cached_tokens=3),
            output_tokens=22,
            output_tokens_details=SimpleNamespace(reasoning_tokens=7),
            total_tokens=33,
        ),
        output_parsed=parsed,
        incomplete_details=None,
    )


def provider_with(fake: FakeResponses) -> OpenAIProvider:
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.client = SimpleNamespace(responses=fake)
    return provider


def test_openai_provider_records_request_and_usage() -> None:
    solution = HanoiSolution(moves=[HanoiMove(disk=1, source=0, destination=2)])
    responses = FakeResponses(fake_response(solution))

    result = provider_with(responses).solve(config())

    assert responses.request["reasoning"] == {"effort": "medium"}
    assert responses.request["store"] is False
    assert responses.request["max_output_tokens"] == 64_000
    assert result.call.response_id == "resp_test"
    assert result.call.actual_model == "actual-test-model"
    assert result.call.usage.reasoning_tokens == 7
    assert result.call.usage.cached_input_tokens == 3


def test_default_reasoning_omits_reasoning_parameter() -> None:
    responses = FakeResponses(fake_response(HanoiSolution(moves=[])))

    provider_with(responses).solve(config("default"))

    assert "reasoning" not in responses.request


def test_unparsed_response_preserves_call_metadata() -> None:
    responses = FakeResponses(fake_response(None))

    with pytest.raises(ProviderError) as error:
        provider_with(responses).solve(config())

    assert error.value.call is not None
    assert error.value.call.response_id == "resp_test"
    assert error.value.call.usage.total_tokens == 33


def test_transport_error_still_records_attempt() -> None:
    responses = FakeResponses(error=RuntimeError("network down"))

    with pytest.raises(ProviderError) as error:
        provider_with(responses).solve(config())

    assert error.value.call is not None
    assert error.value.call.status == "error"
    assert error.value.call.requested_model == "test-model"

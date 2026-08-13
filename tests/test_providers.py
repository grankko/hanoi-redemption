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

    def create(self, **request):
        self.request = request
        if self.error:
            raise self.error
        return self.response


def fake_response(
    parsed=None,
    *,
    status: str = "completed",
    output_text: str | None = None,
    incomplete_reason: str | None = None,
    output: list | None = None,
    response_error=None,
):
    if output_text is None:
        output_text = parsed.model_dump_json() if parsed is not None else ""
    return SimpleNamespace(
        id="resp_test",
        model="actual-test-model",
        status=status,
        usage=SimpleNamespace(
            input_tokens=11,
            input_tokens_details=SimpleNamespace(cached_tokens=3),
            output_tokens=22,
            output_tokens_details=SimpleNamespace(reasoning_tokens=7),
            total_tokens=33,
        ),
        output_text=output_text,
        output=output or [],
        error=response_error,
        incomplete_details=(
            SimpleNamespace(reason=incomplete_reason) if incomplete_reason else None
        ),
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
    assert "max_output_tokens" not in responses.request
    assert responses.request["text"]["format"]["type"] == "json_schema"
    assert responses.request["text"]["format"]["strict"] is True
    assert responses.request["text"]["format"]["name"] == "HanoiSolution"
    assert result.call.response_id == "resp_test"
    assert result.call.actual_model == "actual-test-model"
    assert result.call.usage.reasoning_tokens == 7
    assert result.call.usage.cached_input_tokens == 3


def test_default_reasoning_omits_reasoning_parameter() -> None:
    responses = FakeResponses(fake_response(HanoiSolution(moves=[])))

    provider_with(responses).solve(config("default"))

    assert "reasoning" not in responses.request


def test_output_limit_preserves_call_metadata_and_partial_moves() -> None:
    responses = FakeResponses(
        fake_response(
            status="incomplete",
            output_text=(
                '{"moves":[{"disk":1,"source":0,"destination":2},'
                '{"disk":2,"source":0'
            ),
            incomplete_reason="max_output_tokens",
        )
    )

    with pytest.raises(ProviderError) as error:
        provider_with(responses).solve(config())

    assert error.value.call is not None
    assert error.value.call.response_id == "resp_test"
    assert error.value.call.status == "incomplete"
    assert error.value.call.usage.total_tokens == 33
    assert error.value.outcome_status == "incomplete"
    assert error.value.partial_moves == [HanoiMove(disk=1, source=0, destination=2)]
    assert "output-token limit" in str(error.value)


def test_completed_malformed_response_preserves_metadata() -> None:
    responses = FakeResponses(fake_response(output_text='{"moves": nope}'))

    with pytest.raises(ProviderError) as error:
        provider_with(responses).solve(config())

    assert error.value.call is not None
    assert error.value.call.response_id == "resp_test"
    assert error.value.call.status == "completed"
    assert error.value.call.usage.total_tokens == 33
    assert error.value.outcome_status == "malformed_response"
    assert "malformed structured output" in str(error.value)


def test_failed_response_preserves_api_error_detail() -> None:
    responses = FakeResponses(
        fake_response(
            status="failed",
            response_error=SimpleNamespace(message="server could not complete request"),
        )
    )

    with pytest.raises(ProviderError) as error:
        provider_with(responses).solve(config())

    assert error.value.call is not None
    assert error.value.call.status == "failed"
    assert error.value.outcome_status == "api_error"
    assert "server could not complete request" in str(error.value)


def test_refusal_is_not_labeled_as_api_error() -> None:
    responses = FakeResponses(
        fake_response(
            output=[
                SimpleNamespace(
                    type="message",
                    content=[SimpleNamespace(type="refusal", refusal="not allowed")],
                )
            ]
        )
    )

    with pytest.raises(ProviderError) as error:
        provider_with(responses).solve(config())

    assert error.value.call is not None
    assert error.value.call.status == "completed"
    assert error.value.outcome_status == "malformed_response"
    assert str(error.value) == "OpenAI refused the request: not allowed"


def test_transport_error_still_records_attempt() -> None:
    responses = FakeResponses(error=RuntimeError("network down"))

    with pytest.raises(ProviderError) as error:
        provider_with(responses).solve(config())

    assert error.value.call is not None
    assert error.value.call.status == "error"
    assert error.value.call.requested_model == "test-model"

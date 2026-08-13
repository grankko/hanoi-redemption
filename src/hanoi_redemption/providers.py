"""OpenAI and deterministic mock providers for benchmark runs."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from openai import AuthenticationError, OpenAI
from pydantic import BaseModel, ValidationError
from pydantic_core import from_json

from .game import optimal_solution
from .models import (
    ApiCall,
    HanoiMove,
    HanoiSolution,
    MoveDecision,
    OutcomeStatus,
    RunConfig,
    TokenUsage,
)
from .prompts import apple_prompt, interactive_prompt

ResponseT = TypeVar("ResponseT", bound=BaseModel)


@dataclass(slots=True)
class ProviderResponse(Generic[ResponseT]):
    value: ResponseT
    call: ApiCall


class ProviderError(RuntimeError):
    """An API or parsing error that should be recorded as benchmark data."""

    def __init__(
        self,
        message: str,
        call: ApiCall | None = None,
        *,
        outcome_status: OutcomeStatus = "api_error",
        partial_moves: list[HanoiMove] | None = None,
    ):
        super().__init__(message)
        self.call = call
        self.outcome_status = outcome_status
        self.partial_moves = partial_moves or []


class OpenAIProvider:
    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key)

    def solve(self, config: RunConfig) -> ProviderResponse[HanoiSolution]:
        system, user = apple_prompt(config.disks, config.prompt_variant)
        return self._parse(
            config=config,
            instructions=system,
            input_text=user,
            response_format=HanoiSolution,
        )

    def next_move(
        self,
        config: RunConfig,
        game: Any,
        turn: int,
        moves: list[HanoiMove],
    ) -> ProviderResponse[MoveDecision]:
        system, user = interactive_prompt(game, turn, moves)
        return self._parse(
            config=config,
            instructions=system,
            input_text=user,
            response_format=MoveDecision,
        )

    def _parse(
        self,
        *,
        config: RunConfig,
        instructions: str,
        input_text: str,
        response_format: type[ResponseT],
    ) -> ProviderResponse[ResponseT]:
        request: dict[str, Any] = {
            "model": config.model,
            "instructions": instructions,
            "input": input_text,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": response_format.__name__,
                    "schema": response_format.model_json_schema(),
                    "strict": True,
                }
            },
            "store": False,
        }
        if config.reasoning_effort != "default":
            request["reasoning"] = {"effort": config.reasoning_effort}

        started = time.perf_counter()
        try:
            response = self.client.responses.create(**request)
        except Exception as exc:  # SDK errors vary by transport and API status.
            call = ApiCall(
                requested_model=config.model,
                status="error",
                latency_seconds=time.perf_counter() - started,
            )
            if isinstance(exc, AuthenticationError):
                message = (
                    "OpenAI authentication failed (HTTP 401). "
                    "The selected API key is invalid."
                )
            else:
                message = str(exc)
            raise ProviderError(message, call) from exc
        latency = time.perf_counter() - started

        call = ApiCall(
            response_id=response.id,
            requested_model=config.model,
            actual_model=str(response.model),
            status=str(response.status or "unknown"),
            latency_seconds=latency,
            usage=_usage_from_response(response.usage),
        )
        if response.status == "incomplete":
            reason = getattr(response.incomplete_details, "reason", None)
            if reason == "max_output_tokens":
                message = (
                    "OpenAI stopped the response after reaching its output-token limit."
                )
            else:
                suffix = f" ({reason})" if reason else ""
                message = f"OpenAI returned an incomplete response{suffix}."
            raise ProviderError(
                message,
                call,
                outcome_status="incomplete",
                partial_moves=_partial_moves(response.output_text, response_format),
            )
        if response.status != "completed":
            response_error = getattr(response, "error", None)
            detail = getattr(response_error, "message", None)
            suffix = f": {detail}" if detail else "."
            raise ProviderError(
                f"OpenAI returned response status {response.status or 'unknown'}{suffix}",
                call,
            )
        refusal = _refusal_from_response(response)
        if refusal:
            raise ProviderError(
                f"OpenAI refused the request: {refusal}",
                call,
                outcome_status="malformed_response",
            )
        try:
            value = response_format.model_validate_json(response.output_text)
        except ValidationError as exc:
            raise ProviderError(
                f"OpenAI returned malformed structured output: {exc}",
                call,
                outcome_status="malformed_response",
                partial_moves=_partial_moves(response.output_text, response_format),
            ) from exc
        return ProviderResponse(value=value, call=call)


class MockProvider:
    """Predictable local provider used for tests and CLI demonstrations."""

    def __init__(self, mode: str = "optimal"):
        self.mode = mode

    def solve(self, config: RunConfig) -> ProviderResponse[HanoiSolution]:
        moves = optimal_solution(config.disks)
        if self.mode == "invalid":
            moves = [HanoiMove(disk=config.disks, source=0, destination=2)]
        elif self.mode == "incomplete":
            moves = moves[: max(1, len(moves) // 2)]
        return ProviderResponse(HanoiSolution(moves=moves), self._call(config))

    def next_move(
        self,
        config: RunConfig,
        game: Any,
        turn: int,
        moves: list[HanoiMove],
    ) -> ProviderResponse[MoveDecision]:
        solution = optimal_solution(config.disks)
        if self.mode == "invalid":
            move = HanoiMove(disk=config.disks, source=0, destination=2)
        elif self.mode == "incomplete" and turn > max(1, len(solution) // 2):
            move = HanoiMove(disk=config.disks, source=1, destination=2)
        else:
            move = solution[min(turn - 1, len(solution) - 1)]
        decision = MoveDecision(move=move, explanation=f"mock {self.mode} move {turn}")
        return ProviderResponse(decision, self._call(config))

    def _call(self, config: RunConfig) -> ApiCall:
        return ApiCall(
            response_id=None,
            requested_model=config.model,
            actual_model=f"mock-{self.mode}",
            status="completed",
            latency_seconds=0,
        )


def _usage_from_response(usage: Any) -> TokenUsage:
    if usage is None:
        return TokenUsage()
    input_details = getattr(usage, "input_tokens_details", None)
    output_details = getattr(usage, "output_tokens_details", None)
    return TokenUsage(
        input_tokens=getattr(usage, "input_tokens", 0) or 0,
        cached_input_tokens=getattr(input_details, "cached_tokens", 0) or 0,
        output_tokens=getattr(usage, "output_tokens", 0) or 0,
        reasoning_tokens=getattr(output_details, "reasoning_tokens", 0) or 0,
        total_tokens=getattr(usage, "total_tokens", 0) or 0,
    )


def _partial_moves(text: str, response_format: type[BaseModel]) -> list[HanoiMove]:
    """Recover fully formed paper-protocol moves from truncated structured output."""
    if response_format is not HanoiSolution or not text:
        return []
    try:
        value = from_json(text, allow_partial=True)
    except ValueError:
        return []
    if not isinstance(value, dict) or not isinstance(value.get("moves"), list):
        return []

    moves: list[HanoiMove] = []
    for candidate in value["moves"]:
        try:
            moves.append(HanoiMove.model_validate(candidate))
        except ValidationError:
            break
    return moves


def _refusal_from_response(response: Any) -> str | None:
    for output in getattr(response, "output", []):
        if getattr(output, "type", None) != "message":
            continue
        for content in getattr(output, "content", []):
            if getattr(content, "type", None) == "refusal":
                return str(getattr(content, "refusal", "refused without details"))
    return None

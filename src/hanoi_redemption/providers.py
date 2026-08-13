"""OpenAI and deterministic mock providers for benchmark runs."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from openai import AuthenticationError, OpenAI
from pydantic import BaseModel

from .game import optimal_solution
from .models import (
    ApiCall,
    HanoiMove,
    HanoiSolution,
    MoveDecision,
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

    def __init__(self, message: str, call: ApiCall | None = None):
        super().__init__(message)
        self.call = call


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
            max_output_tokens=config.max_output_tokens,
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
            max_output_tokens=config.max_output_tokens,
        )

    def _parse(
        self,
        *,
        config: RunConfig,
        instructions: str,
        input_text: str,
        response_format: type[ResponseT],
        max_output_tokens: int,
    ) -> ProviderResponse[ResponseT]:
        request: dict[str, Any] = {
            "model": config.model,
            "instructions": instructions,
            "input": input_text,
            "max_output_tokens": max_output_tokens,
            "text_format": response_format,
            "store": False,
        }
        if config.reasoning_effort != "default":
            request["reasoning"] = {"effort": config.reasoning_effort}

        started = time.perf_counter()
        try:
            response = self.client.responses.parse(**request)
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
        if response.output_parsed is None:
            detail = getattr(response.incomplete_details, "reason", None)
            suffix = f" ({detail})" if detail else ""
            raise ProviderError(f"model response could not be parsed{suffix}", call)
        return ProviderResponse(value=response.output_parsed, call=call)


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

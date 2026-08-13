"""Shared data contracts for benchmark requests and persisted results."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

ProtocolName = Literal["apple", "interactive"]
PromptVariant = Literal["standard", "algorithm"]
OutcomeStatus = Literal[
    "pass",
    "invalid_move",
    "incomplete",
    "move_budget_exceeded",
    "malformed_response",
    "api_error",
]


class HanoiMove(BaseModel):
    """A paper-compatible move: disk identifier and zero-indexed peg numbers."""

    model_config = ConfigDict(extra="forbid")

    disk: int = Field(ge=1, description="Disk number, where 1 is the smallest")
    source: int = Field(ge=0, le=2, description="Zero-indexed source peg")
    destination: int = Field(ge=0, le=2, description="Zero-indexed destination peg")

    def compact(self) -> str:
        return f"disk {self.disk}: {self.source} -> {self.destination}"


class HanoiSolution(BaseModel):
    """Complete solution returned by the Apple-style one-shot protocol."""

    model_config = ConfigDict(extra="forbid")
    moves: list[HanoiMove] = Field(description="The complete move sequence")


class MoveDecision(BaseModel):
    """One move returned by the interactive protocol."""

    model_config = ConfigDict(extra="forbid")
    move: HanoiMove
    explanation: str = Field(description="A brief explanation of this move")


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    reasoning_effort: str
    disks: int = Field(ge=1, le=20)
    trial: int = Field(ge=1)
    protocol: ProtocolName
    prompt_variant: PromptVariant = "standard"
    max_output_tokens: int = Field(gt=0)
    move_budget_multiplier: float = Field(ge=1.0)
    prompt_version: str = "apple-hanoi-v1"


class TokenUsage(BaseModel):
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            cached_input_tokens=self.cached_input_tokens + other.cached_input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class ApiCall(BaseModel):
    response_id: str | None = None
    requested_model: str
    actual_model: str | None = None
    status: str
    latency_seconds: float = Field(ge=0)
    usage: TokenUsage = Field(default_factory=TokenUsage)


class ValidationReport(BaseModel):
    status: OutcomeStatus
    solved: bool
    returned_moves: int = Field(ge=0)
    valid_moves: int = Field(ge=0)
    optimal_moves: int = Field(ge=1)
    optimal: bool
    efficiency_percent: float | None = None
    disks_on_target: int = Field(ge=0)
    first_error_move: int | None = Field(default=None, ge=1)
    error: str | None = None


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 2
    run_id: str
    created_at: datetime
    config: RunConfig
    validation: ValidationReport
    moves: list[HanoiMove] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
    api_calls: list[ApiCall] = Field(default_factory=list)
    processing_time_seconds: float = Field(
        ge=0,
        validation_alias=AliasChoices("processing_time_seconds", "elapsed_seconds"),
    )
    token_usage: TokenUsage | None = None

    @model_validator(mode="after")
    def populate_legacy_token_usage(self) -> BenchmarkResult:
        if self.token_usage is None:
            self.token_usage = aggregate_token_usage(self.api_calls)
        return self

    @property
    def total_usage(self) -> TokenUsage:
        return self.token_usage or aggregate_token_usage(self.api_calls)

    @property
    def elapsed_seconds(self) -> float:
        """Compatibility accessor for code using the schema-v1 field name."""

        return self.processing_time_seconds


def aggregate_token_usage(calls: list[ApiCall]) -> TokenUsage:
    total = TokenUsage()
    for call in calls:
        total = total + call.usage
    return total

"""Command-line interface for running, comparing, inspecting, and replaying evals."""

from __future__ import annotations

import argparse
import itertools
import math
import statistics
import sys
from collections import defaultdict
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm as RichConfirm
from rich.prompt import IntPrompt as RichIntPrompt
from rich.prompt import Prompt as RichPrompt
from rich.table import Table

from .benchmark import BenchmarkRunner
from .credentials import find_openai_credentials
from .models import BenchmarkResult, RunConfig
from .paper import PAPER_BASELINE, paper_comparison
from .prompts import apple_prompt
from .protocols import normalize_protocol, protocol_label
from .providers import MockProvider, OpenAIProvider
from .storage import ResultEntry, ResultStore
from .visualization import replay, result_summary

DEFAULT_MODEL = "gpt-5.6-sol"
OPENAI_MODELS = (
    (
        "gpt-5.6-sol",
        "current flagship capability",
        ("none", "low", "medium", "high", "xhigh", "max"),
    ),
    (
        "gpt-5.6-terra",
        "current balance of capability and cost",
        ("none", "low", "medium", "high", "xhigh", "max"),
    ),
    (
        "gpt-5.6-luna",
        "current fast, efficient model",
        ("none", "low", "medium", "high", "xhigh", "max"),
    ),
    ("o3", "legacy reasoning model, succeeded by GPT-5", ("low", "medium", "high")),
    (
        "o3-mini",
        "paper-era model; deprecated, shuts down 2026-10-23",
        ("low", "medium", "high"),
    ),
)
REASONING_LEVELS = (
    "default",
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)


class QuitRequested(Exception):
    """Raised when the user enters q at an interactive prompt."""


class _QuitPromptMixin:
    def process_response(self, value: str):
        if value.strip().casefold() == "q":
            raise QuitRequested
        return super().process_response(value)


class Prompt(_QuitPromptMixin, RichPrompt):
    pass


class IntPrompt(_QuitPromptMixin, RichIntPrompt):
    pass


class Confirm(_QuitPromptMixin, RichConfirm):
    pass


class _TimedProvider:
    """Add terminal request timing without coupling providers to Rich."""

    def __init__(self, provider: Any, console: Console):
        self.provider = provider
        self.console = console

    def solve(self, config: RunConfig):
        with _request_timer(self.console):
            return self.provider.solve(config)

    def next_move(self, config: RunConfig, game: Any, turn: int, moves: list):
        with _request_timer(self.console):
            return self.provider.next_move(config, game, turn, moves)


@contextmanager
def _request_timer(console: Console):
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("Waiting for model response"),
        TextColumn("[dim]elapsed"),
        TimeElapsedColumn(),
        console=console,
        refresh_per_second=4,
        transient=True,
    ) as progress:
        progress.add_task("request", total=None)
        yield


def _add_evaluation_arguments(
    command: argparse.ArgumentParser,
    *,
    require_experiment: bool,
    animate_default: bool,
    allow_mock: bool,
) -> None:
    requirement = {"required": True} if require_experiment else {}
    command.add_argument(
        "--model",
        action="append",
        metavar="MODEL",
        help=(
            "OpenAI model ID; repeat or comma-separate to create a matrix"
            + ("" if require_experiment else f" (default: {DEFAULT_MODEL})")
        ),
        **requirement,
    )
    command.add_argument(
        "--reasoning",
        action="append",
        choices=REASONING_LEVELS,
        help=(
            "reasoning effort; repeat to create a matrix"
            + ("" if require_experiment else " (default: medium)")
        ),
        **requirement,
    )
    command.add_argument(
        "--disks",
        default=None if require_experiment else "3-8",
        required=require_experiment,
        metavar="COUNT_OR_SET",
        help=(
            "one count or a set such as 7, 3-8, or 3,5,7"
            + ("" if require_experiment else " (default: 3-8)")
        ),
    )
    command.add_argument(
        "--protocol",
        action="append",
        choices=("paper", "apple", "interactive"),
        help=(
            "paper is one API call returning the complete move list; "
            "interactive is one API call per move; apple is the legacy paper alias"
        ),
        **requirement,
    )
    command.add_argument(
        "--prompt",
        action="append",
        choices=("standard", "algorithm"),
        help="paper prompt variant; repeat to compare (default: standard; ignored by interactive)",
    )
    command.add_argument(
        "--trials",
        type=int,
        default=1,
        help="independent attempts per configuration (default: 1)",
    )
    command.add_argument(
        "--move-budget-multiplier",
        type=float,
        default=2.0,
        help="interactive move limit relative to the optimum (default: 2.0)",
    )
    command.add_argument(
        "--animate",
        action=argparse.BooleanOptionalAction,
        default=animate_default,
        help=f"animate returned moves (default: {'enabled' if animate_default else 'disabled'})",
    )
    command.add_argument(
        "--delay",
        type=float,
        default=0.08,
        help="seconds between animated moves (default: 0.08)",
    )
    command.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="directory that will contain runs/*.json (default: results)",
    )
    if allow_mock:
        command.add_argument(
            "--mock",
            choices=("optimal", "invalid", "incomplete"),
            help="make deterministic local responses instead of API calls",
        )
    else:
        command.set_defaults(mock=None)
    command.add_argument(
        "--allow-large",
        action="store_true",
        help="allow disk counts above 12 despite exponential output/call growth",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hanoi",
        description=(
            "Evaluate whether OpenAI models can solve or interactively play Towers of Hanoi."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("menu", help="open the guided interactive menu")

    browse = subparsers.add_parser("browse", help="browse and open stored results")
    browse.add_argument("--results-dir", type=Path, default=Path("results"))

    run = subparsers.add_parser(
        "run",
        help="start a fully specified evaluation without prompts",
        description=(
            "Run a Towers of Hanoi evaluation without opening the menu or asking for input. "
            "The model, reasoning effort, protocol, and disk count must be explicit. "
            "After validation, potentially paid API calls begin immediately."
        ),
        epilog=(
            "example:\n"
            "  hanoi run --model gpt-5.6-luna --reasoning medium --protocol paper "
            "--prompt standard --disks 7 --trials 1\n\n"
            "API calls:\n"
            "  paper       one call per model/reasoning/disk/prompt/trial configuration\n"
            "  interactive up to move-budget-multiplier * (2^disks - 1) calls per trial\n\n"
            "exit status:\n"
            "  0  every requested API call completed and each result was saved; a puzzle may "
            "still be unsolved\n"
            "  1  an API call failed or ended incomplete; the result was saved\n"
            "  2  invalid arguments, configuration, or missing credentials"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_evaluation_arguments(
        run,
        require_experiment=True,
        animate_default=False,
        allow_mock=False,
    )

    evaluate = subparsers.add_parser(
        "eval",
        help="run a non-interactive evaluation matrix using optional defaults",
    )
    _add_evaluation_arguments(
        evaluate,
        require_experiment=False,
        animate_default=True,
        allow_mock=True,
    )

    compare = subparsers.add_parser("compare", help="summarize stored results")
    compare.add_argument("--results-dir", type=Path, default=Path("results"))
    compare.add_argument("--model", help="only include this requested model")
    compare.add_argument("--protocol", choices=("paper", "apple", "interactive"))

    replay_parser = subparsers.add_parser("replay", help="animate a stored run")
    replay_parser.add_argument("run", help="result path, full run ID, or unique ID prefix")
    replay_parser.add_argument("--results-dir", type=Path, default=Path("results"))
    replay_parser.add_argument("--delay", type=float, default=0.08)

    prompt_parser = subparsers.add_parser("prompt", help="print the exact Apple-style prompt")
    prompt_parser.add_argument("--disks", type=int, default=4)
    prompt_parser.add_argument("--variant", choices=("standard", "algorithm"), default="standard")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console()
    try:
        if args.command in (None, "menu"):
            return _menu(console)
        if args.command in ("run", "eval"):
            return _eval(args, console)
        if args.command == "browse":
            return _browse_results(args, console)
        if args.command == "compare":
            return _compare(args, console)
        if args.command == "replay":
            return _replay(args, console)
        if args.command == "prompt":
            return _prompt(args, console)
        return 2
    except (QuitRequested, EOFError, KeyboardInterrupt):
        console.print("\nGoodbye.")
        return 0


def _menu(console: Console) -> int:
    console.print(
        Panel(
            "Test whether modern OpenAI models can solve Towers of Hanoi, "
            "then compare and replay their games.\n"
            "Choose [bold]Run an evaluation[/] to select a model and reasoning level.",
            title="Hanoi Redemption",
            border_style="cyan",
        )
    )
    console.print(Panel(PAPER_BASELINE, title="What the paper found", border_style="magenta"))
    while True:
        console.print(
            "\n[bold]1[/]  Run an evaluation "
            "[dim]— choose model, reasoning, and disks[/]"
        )
        console.print("[bold]2[/]  Browse saved results [dim]— open details or replay[/]")
        console.print("[bold]3[/]  Compare stored results")
        console.print(
            "[bold]4[/]  Preview the benchmark prompt "
            "[dim]— choose a sample disk count[/]"
        )
        console.print("[bold]q[/]  Quit")
        choice = Prompt.ask("\nChoose", choices=("1", "2", "3", "4", "q"), default="1")
        if choice == "1":
            _interactive_eval(console)
        elif choice == "2":
            _browse_results(argparse.Namespace(results_dir=Path("results")), console)
        elif choice == "3":
            compare_args = argparse.Namespace(
                results_dir=Path("results"), model=None, protocol=None
            )
            _compare(compare_args, console)
        elif choice == "4":
            _interactive_prompt(console)
        else:
            return 0


def _interactive_eval(console: Console) -> int:
    console.print("\n[bold cyan]New evaluation[/]")
    for index, (model, description, _) in enumerate(OPENAI_MODELS, start=1):
        console.print(f"  [bold]{index}[/]  {model} [dim]— {description}[/]")
    custom_choice = str(len(OPENAI_MODELS) + 1)
    console.print(f"  [bold]{custom_choice}[/]  Enter another model ID")
    model_choices = tuple(str(index) for index in range(1, len(OPENAI_MODELS) + 2))
    model_choice = Prompt.ask("Model", choices=model_choices, default="1")
    if model_choice == custom_choice:
        model = Prompt.ask("OpenAI model ID").strip()
        if not model:
            console.print("[bold red]A model ID is required.[/]")
            return 2
    else:
        model = OPENAI_MODELS[int(model_choice) - 1][0]

    efforts = _reasoning_efforts_for_model(model)
    console.print("\n[bold]Reasoning effort[/]")
    for index, effort in enumerate(efforts, start=1):
        suffix = " [dim]— balanced starting point[/]" if effort == "medium" else ""
        console.print(f"  [bold]{index}[/]  {effort}{suffix}")
    effort_choice = Prompt.ask(
        "Reasoning",
        choices=tuple(str(index) for index in range(1, len(efforts) + 1)),
        default=str(efforts.index("medium") + 1) if "medium" in efforts else "1",
    )
    effort = efforts[int(effort_choice) - 1]

    console.print("\n[bold]Protocol[/]")
    console.print(
        "  [bold]1[/]  Paper protocol (one shot) "
        "[dim]— one API call returns the complete move list[/]"
    )
    console.print(
        "  [bold]2[/]  Interactive play "
        "[dim]— one API call per move, with the updated board[/]"
    )
    protocol_choice = Prompt.ask("Protocol", choices=("1", "2"), default="1")
    protocol = "apple" if protocol_choice == "1" else "interactive"

    disk_default = "3-8" if protocol == "apple" else "3-5"
    disk_spec = Prompt.ask(
        "Disk count(s) [dim](one value like 7, or a range like 3-8)[/]",
        default=disk_default,
    )
    trials = IntPrompt.ask("Trials per disk count", default=1)
    prompt_variant = "standard"
    if protocol == "apple":
        prompt_choice = Prompt.ask(
            "Prompt",
            choices=("standard", "algorithm"),
            default="standard",
        )
        prompt_variant = prompt_choice
    animate = Confirm.ask("Animate returned games", default=True)

    try:
        disks = parse_disk_spec(disk_spec)
    except ValueError as exc:
        console.print(f"[bold red]Invalid disk counts:[/] {exc}")
        return 2
    estimated_calls = sum(
        1 if protocol == "apple" else math.ceil(((2**count) - 1) * 2.0)
        for count in disks
    ) * max(trials, 0)
    console.print(
        Panel(
            f"{model} · {effort} reasoning · {protocol_label(protocol)} · "
            f"disks {disk_spec} · {trials} trial(s)\n"
            f"Up to {estimated_calls:,} paid API call(s)\n"
            f"{_protocol_explanation(protocol)}",
            title="Ready to run",
            border_style="yellow",
        )
    )
    if not Confirm.ask("Start evaluation", default=True):
        console.print("Cancelled.")
        return 0

    return _eval(
        argparse.Namespace(
            model=[model],
            reasoning=[effort],
            disks=disk_spec,
            protocol=[protocol],
            prompt=[prompt_variant],
            trials=trials,
            move_budget_multiplier=2.0,
            animate=animate,
            delay=0.08,
            results_dir=Path("results"),
            mock=None,
            allow_large=False,
        ),
        console,
    )


def _browse_results(args: argparse.Namespace, console: Console) -> int:
    entries = ResultStore(args.results_dir).entries()
    if not entries:
        console.print("No stored results found.")
        return 0

    page_size = 10
    page = 0
    while True:
        start = page * page_size
        page_entries = entries[start : start + page_size]
        pages = math.ceil(len(entries) / page_size)
        table = Table(title=f"Saved results · {len(entries)} total · page {page + 1}/{pages}")
        for column in (
            "#",
            "When (UTC)",
            "Model",
            "Reasoning",
            "Protocol",
            "Disks",
            "Status",
            "Moves",
            "Time",
            "Tokens",
        ):
            numeric = column in ("#", "Disks", "Moves", "Time", "Tokens")
            table.add_column(column, justify="right" if numeric else "left")
        for index, entry in enumerate(page_entries, start=1):
            result = entry.result
            table.add_row(
                str(index),
                result.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                result.config.model,
                result.config.reasoning_effort,
                protocol_label(result.config.protocol),
                str(result.config.disks),
                result.validation.status.upper(),
                f"{result.validation.valid_moves}/{result.validation.optimal_moves}",
                f"{result.processing_time_seconds:.1f}s",
                f"{result.total_usage.total_tokens:,}",
            )
        console.print(table)
        commands = [str(index) for index in range(1, len(page_entries) + 1)]
        if page + 1 < pages:
            commands.append("n")
        if page > 0:
            commands.append("p")
        commands.append("b")
        choice = Prompt.ask(
            "Open a result number, or enter n (next), p (previous), b (back)",
            choices=tuple(commands),
        )
        if choice == "b":
            return 0
        if choice == "n":
            page += 1
            continue
        if choice == "p":
            page -= 1
            continue
        _open_result(page_entries[int(choice) - 1], console)


def _open_result(entry: ResultEntry, console: Console) -> None:
    result = entry.result
    usage = result.total_usage
    details = Table.grid(padding=(0, 2))
    details.add_column(style="bold")
    details.add_column()
    rows = (
        ("Run ID", result.run_id),
        ("Created", result.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Requested model", result.config.model),
        ("Actual model", _actual_models(result)),
        ("Reasoning", result.config.reasoning_effort),
        ("Protocol", protocol_label(result.config.protocol)),
        ("Prompt", f"{result.config.prompt_variant} · {result.config.prompt_version}"),
        ("Puzzle", f"{result.config.disks} disks · trial {result.config.trial}"),
        ("Outcome", result.validation.status.upper()),
        (
            "Moves",
            f"{result.validation.valid_moves} valid / {result.validation.returned_moves} returned "
            f"/ {result.validation.optimal_moves} minimum",
        ),
        ("Optimal", "yes" if result.validation.optimal else "no"),
        ("Disks on target", f"{result.validation.disks_on_target}/{result.config.disks}"),
        ("Processing time", f"{result.processing_time_seconds:.2f} seconds"),
        (
            "Tokens",
            f"{usage.total_tokens:,} total · {usage.input_tokens:,} input · "
            f"{usage.output_tokens:,} output · {usage.reasoning_tokens:,} reasoning",
        ),
        ("API calls", str(len(result.api_calls))),
    )
    for label, value in rows:
        details.add_row(label, value)
    style = "green" if result.validation.solved else "red"
    console.print(Panel(details, title=f"Result {result.run_id[:10]}", border_style=style))
    console.print(Panel(entry.path.name, title="Result file", border_style="dim"))
    console.print(f"[dim]Paper comparison:[/] {paper_comparison(result)}")
    if result.validation.error:
        console.print(Panel(result.validation.error, title="Failure details", border_style="red"))
    while True:
        action = Prompt.ask("Enter r to replay or b to return", choices=("r", "b"), default="b")
        if action == "b":
            return
        replay(result, console=console, delay=0.08)


def _actual_models(result: BenchmarkResult) -> str:
    models = list(
        dict.fromkeys(call.actual_model for call in result.api_calls if call.actual_model)
    )
    return ", ".join(models) if models else "not returned"


def _interactive_prompt(console: Console) -> int:
    console.print("\n[bold cyan]Benchmark prompt preview[/]")
    console.print(
        "[dim]The prompt describes a concrete puzzle, so choose the disk count "
        "to insert into it. This does not run an evaluation or call the API.[/]"
    )
    disks = IntPrompt.ask("Disk count to show in the prompt", default=4)
    variant = Prompt.ask("Prompt", choices=("standard", "algorithm"), default="standard")
    return _prompt(argparse.Namespace(disks=disks, variant=variant), console)


def _eval(args: argparse.Namespace, console: Console) -> int:
    try:
        disks = parse_disk_spec(args.disks)
    except ValueError as exc:
        console.print(f"[bold red]Invalid --disks:[/] {exc}")
        return 2
    if args.trials < 1:
        console.print("[bold red]--trials must be at least 1[/]")
        return 2
    if args.move_budget_multiplier < 1 or args.delay < 0:
        console.print("[bold red]multiplier must be >= 1; delay must be >= 0[/]")
        return 2
    if max(disks) > 12 and not args.allow_large:
        console.print(
            "[bold red]Disk counts above 12 require --allow-large.[/] "
            "Hanoi output grows as 2^n - 1."
        )
        return 2

    models = [f"mock-{args.mock}"] if args.mock else _split_values(args.model or [DEFAULT_MODEL])
    efforts = args.reasoning or ["medium"]
    protocols = [normalize_protocol(protocol) for protocol in (args.protocol or ["paper"])]
    prompts = args.prompt or ["standard"]
    configs = _build_configs(
        models=models,
        efforts=efforts,
        disks=disks,
        protocols=protocols,
        prompts=prompts,
        trials=args.trials,
        move_budget_multiplier=args.move_budget_multiplier,
    )

    provider = MockProvider(args.mock) if args.mock else _openai_provider(console)
    if provider is None:
        return 2
    runner = BenchmarkRunner(_TimedProvider(provider, console))
    store = ResultStore(args.results_dir)

    max_calls = sum(
        1
        if config.protocol == "apple"
        else math.ceil(((2**config.disks) - 1) * config.move_budget_multiplier)
        for config in configs
    )
    console.print(
        Panel(
            f"{len(configs)} run(s) · up to {max_calls:,} API call(s) · "
            f"results in {store.runs_dir}",
            title="Hanoi evaluation",
            border_style="cyan",
        )
    )

    had_request_error = False
    for index, config in enumerate(configs, start=1):
        label = (
            f"[{index}/{len(configs)}] {config.model} · {config.reasoning_effort} · "
            f"{protocol_label(config.protocol)} · {config.disks} disks · trial {config.trial}"
        )
        console.print(f"[bold]{label}[/]")
        result = runner.run(config)
        path = store.save(result)
        style = "green" if result.validation.solved else "red"
        console.print(f"[{style}]{result_summary(result)}[/] · {path}")
        console.print(f"[dim]Paper comparison:[/] {paper_comparison(result)}")
        if result.validation.error:
            console.print(
                Panel(result.validation.error, title="Failure details", border_style="red")
            )
        request_failed = result.validation.status == "api_error" or any(
            call.status != "completed" for call in result.api_calls
        )
        if request_failed:
            had_request_error = True
            authentication_failed = (
                result.validation.error
                and "authentication failed" in result.validation.error.lower()
            )
            if authentication_failed:
                remaining = len(configs) - index
                if remaining:
                    console.print(
                        f"[yellow]Stopped {remaining} remaining run(s): "
                        "the same key would fail.[/]"
                    )
                break
        if args.animate and result.moves:
            replay(result, console=console, delay=args.delay)

    return 1 if had_request_error else 0


def _openai_provider(console: Console) -> OpenAIProvider | None:
    credentials = find_openai_credentials()
    if credentials is None:
        console.print("[bold red]No OpenAI API key was found.[/]")
        console.print("Export OPENAI_API_KEY or add it to the ignored project .env file.")
        return None
    try:
        provider = OpenAIProvider(api_key=credentials.api_key)
    except Exception as exc:
        console.print(f"[bold red]Could not initialize OpenAI client:[/] {exc}")
        return None
    console.print(f"[dim]Using OpenAI credentials from {credentials.source}.[/]")
    return provider


def _build_configs(
    *,
    models: list[str],
    efforts: list[str],
    disks: list[int],
    protocols: list[str],
    prompts: list[str],
    trials: int,
    move_budget_multiplier: float,
) -> list[RunConfig]:
    configs: list[RunConfig] = []
    for model, effort, disk_count, protocol in itertools.product(models, efforts, disks, protocols):
        variants = prompts if protocol == "apple" else ["standard"]
        for prompt_variant, trial in itertools.product(variants, range(1, trials + 1)):
            configs.append(
                RunConfig(
                    model=model,
                    reasoning_effort=effort,
                    disks=disk_count,
                    trial=trial,
                    protocol=protocol,
                    prompt_variant=prompt_variant,
                    max_output_tokens=None,
                    move_budget_multiplier=move_budget_multiplier,
                )
            )
    return configs


def _compare(args: argparse.Namespace, console: Console) -> int:
    results = ResultStore(args.results_dir).load_all()
    if args.model:
        results = [result for result in results if result.config.model == args.model]
    if args.protocol:
        requested_protocol = normalize_protocol(args.protocol)
        results = [
            result for result in results if result.config.protocol == requested_protocol
        ]
    if not results:
        console.print("No matching results found.")
        return 0

    grouped: dict[tuple[str, str, str, str, int], list[BenchmarkResult]] = defaultdict(list)
    for result in results:
        key = (
            result.config.protocol,
            result.config.prompt_variant,
            result.config.model,
            result.config.reasoning_effort,
            result.config.disks,
        )
        grouped[key].append(result)

    table = Table(title="Towers of Hanoi results")
    for column in (
        "Protocol",
        "Prompt",
        "Model",
        "Reasoning",
        "Disks",
        "Pass",
        "Avg valid",
        "Avg seconds",
        "Avg tokens",
    ):
        numeric = column.startswith(("Disks", "Pass", "Avg"))
        table.add_column(column, justify="right" if numeric else "left")

    for key, group in sorted(grouped.items()):
        protocol, prompt_variant, model, effort, disks = key
        passed = sum(result.validation.solved for result in group)
        table.add_row(
            protocol_label(protocol),
            prompt_variant,
            model,
            effort,
            str(disks),
            f"{passed}/{len(group)}",
            f"{statistics.mean(result.validation.valid_moves for result in group):.1f}",
            f"{statistics.mean(result.processing_time_seconds for result in group):.2f}",
            f"{statistics.mean(result.total_usage.total_tokens for result in group):,.0f}",
        )
    console.print(table)
    console.print(Panel(PAPER_BASELINE, title="Paper baseline", border_style="magenta"))
    return 0


def _replay(args: argparse.Namespace, console: Console) -> int:
    try:
        result = ResultStore(args.results_dir).resolve(args.run)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[bold red]{exc}[/]")
        return 2
    replay(result, console=console, delay=args.delay)
    console.print(f"[dim]Paper comparison:[/] {paper_comparison(result)}")
    return 0


def _prompt(args: argparse.Namespace, console: Console) -> int:
    if not 1 <= args.disks <= 20:
        console.print("[bold red]--disks must be between 1 and 20[/]")
        return 2
    system, user = apple_prompt(args.disks, args.variant)
    console.print(Panel(system, title="System prompt", border_style="cyan"))
    console.print(Panel(user, title="User prompt", border_style="magenta"))
    return 0


def parse_disk_spec(value: str) -> list[int]:
    values: set[int] = set()
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_text, end_text = chunk.split("-", maxsplit=1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError(f"descending range {chunk!r} is not supported")
            values.update(range(start, end + 1))
        else:
            values.add(int(chunk))
    if not values or min(values) < 1 or max(values) > 20:
        raise ValueError("choose one or more disk counts between 1 and 20")
    return sorted(values)


def _split_values(values: list[str]) -> list[str]:
    split = [item.strip() for value in values for item in value.split(",") if item.strip()]
    if not split:
        raise ValueError("at least one value is required")
    return list(dict.fromkeys(split))


def _reasoning_efforts_for_model(model: str) -> tuple[str, ...]:
    for model_id, _, efforts in OPENAI_MODELS:
        if model == model_id:
            return efforts
    return REASONING_LEVELS


def _protocol_explanation(protocol: str) -> str:
    if normalize_protocol(protocol) == "apple":
        return (
            "Each trial is exactly one API call: the model must return every move "
            "before the solution is validated."
        )
    return (
        "The Hanoi rules are unchanged, but the model receives the updated board "
        "before choosing each move."
    )


if __name__ == "__main__":
    sys.exit(main())

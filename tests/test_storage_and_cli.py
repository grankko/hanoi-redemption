import json
from io import StringIO
from pathlib import Path

from rich.console import Console

from hanoi_redemption import cli
from hanoi_redemption.benchmark import BenchmarkRunner
from hanoi_redemption.cli import (
    OPENAI_MODELS,
    _reasoning_efforts_for_model,
    build_parser,
    main,
    parse_disk_spec,
)
from hanoi_redemption.models import RunConfig
from hanoi_redemption.paper import PAPER_BASELINE, paper_comparison
from hanoi_redemption.protocols import normalize_protocol, protocol_label
from hanoi_redemption.providers import MockProvider
from hanoi_redemption.storage import ResultStore
from hanoi_redemption.visualization import replay


def test_parse_disk_spec_supports_ranges_and_lists() -> None:
    assert parse_disk_spec("3-5,7") == [3, 4, 5, 7]


def test_paper_cli_defaults_through_the_reported_collapse_region() -> None:
    args = build_parser().parse_args(["eval", "--mock", "optimal"])

    assert args.disks == "3-8"


def test_bare_command_opens_menu(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_menu", lambda console: 17)

    assert main([]) == 17


def test_main_menu_explains_where_model_selection_lives(monkeypatch) -> None:
    output = StringIO()
    console = Console(file=output, force_terminal=False)
    monkeypatch.setattr(cli.Prompt, "ask", lambda *args, **kwargs: "q")

    assert cli._menu(console) == 0

    rendered = output.getvalue()
    assert "choose model, reasoning, and disks" in rendered
    assert "choose a sample disk count" in rendered


def test_menu_includes_current_and_paper_era_models() -> None:
    models = {model for model, _, _ in OPENAI_MODELS}

    assert {"gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "o3", "o3-mini"} <= models
    assert _reasoning_efforts_for_model("o3") == ("low", "medium", "high")
    assert _reasoning_efforts_for_model("o3-mini") == ("low", "medium", "high")
    assert "max" in _reasoning_efforts_for_model("gpt-5.6-sol")


def test_paper_protocol_has_clear_public_name_and_stable_storage_name() -> None:
    assert normalize_protocol("paper") == "apple"
    assert normalize_protocol("interactive") == "interactive"
    assert protocol_label("apple") == "paper (one-shot)"


def test_paper_comparison_marks_collapse_and_interactive_protocol() -> None:
    apple_config = RunConfig(
        model="mock-optimal",
        reasoning_effort="none",
        disks=8,
        trial=1,
        protocol="apple",
        max_output_tokens=64_000,
        move_budget_multiplier=2.0,
    )
    interactive_config = apple_config.model_copy(update={"protocol": "interactive"})

    apple_result = BenchmarkRunner(MockProvider()).run(apple_config)
    interactive_result = BenchmarkRunner(MockProvider()).run(interactive_config)

    assert "collapse region" in paper_comparison(apple_result)
    assert "Not directly comparable" in paper_comparison(interactive_result)
    assert "7–8 disks" in PAPER_BASELINE


def test_store_round_trip_and_prefix_resolution(tmp_path: Path) -> None:
    config = RunConfig(
        model="mock-optimal",
        reasoning_effort="none",
        disks=3,
        trial=1,
        protocol="apple",
        max_output_tokens=64_000,
        move_budget_multiplier=2.0,
    )
    result = BenchmarkRunner(MockProvider()).run(config)
    store = ResultStore(tmp_path)

    path = store.save(result)
    stored = json.loads(path.read_text(encoding="utf-8"))

    assert path.exists()
    assert path.name.startswith(result.created_at.strftime("%Y-%m-%d_%H-%M-%SZ_mock-optimal"))
    assert "_none_paper_3d_t1_pass_" in path.name
    assert stored["schema_version"] == 2
    assert stored["processing_time_seconds"] >= 0
    assert stored["token_usage"]["total_tokens"] == 0
    assert "elapsed_seconds" not in stored
    assert store.resolve(result.run_id[:10]).run_id == result.run_id
    assert [item.run_id for item in store.load_all()] == [result.run_id]


def test_store_keeps_legacy_run_id_filenames_browseable(tmp_path: Path) -> None:
    config = RunConfig(
        model="mock-optimal",
        reasoning_effort="none",
        disks=3,
        trial=1,
        protocol="apple",
        max_output_tokens=64_000,
        move_budget_multiplier=2.0,
    )
    result = BenchmarkRunner(MockProvider()).run(config)
    store = ResultStore(tmp_path)
    descriptive_path = store.save(result)
    legacy_path = descriptive_path.with_name(f"{result.run_id}.json")
    descriptive_path.rename(legacy_path)

    entries = store.entries()

    assert entries[0].path == legacy_path
    assert store.resolve(result.run_id[:10]).run_id == result.run_id


def test_result_browser_opens_details(monkeypatch, tmp_path: Path) -> None:
    config = RunConfig(
        model="mock-optimal",
        reasoning_effort="none",
        disks=3,
        trial=1,
        protocol="apple",
        max_output_tokens=64_000,
        move_budget_multiplier=2.0,
    )
    ResultStore(tmp_path).save(BenchmarkRunner(MockProvider()).run(config))
    answers = iter(("1", "b", "b"))
    monkeypatch.setattr(cli.Prompt, "ask", lambda *args, **kwargs: next(answers))
    output = StringIO()

    assert cli._browse_results(
        cli.argparse.Namespace(results_dir=tmp_path),
        Console(file=output, force_terminal=False),
    ) == 0

    rendered = output.getvalue()
    assert "Saved results" in rendered
    assert "Requested model" in rendered
    assert "mock-optimal" in rendered
    assert "Tokens" in rendered
    assert "Processing time" in rendered


def test_schema_v1_time_and_per_call_tokens_are_migrated(tmp_path: Path) -> None:
    config = RunConfig(
        model="legacy-model",
        reasoning_effort="medium",
        disks=3,
        trial=1,
        protocol="apple",
        max_output_tokens=64_000,
        move_budget_multiplier=2.0,
    )
    result = BenchmarkRunner(MockProvider()).run(config)
    document = result.model_dump(mode="json")
    document["schema_version"] = 1
    document["elapsed_seconds"] = document.pop("processing_time_seconds")
    document.pop("token_usage")
    document["api_calls"][0]["usage"]["total_tokens"] = 123
    legacy_path = tmp_path / "runs" / f"{result.run_id}.json"
    legacy_path.parent.mkdir()
    legacy_path.write_text(json.dumps(document), encoding="utf-8")

    loaded = ResultStore(tmp_path).resolve(result.run_id[:10])

    assert loaded.processing_time_seconds == result.processing_time_seconds
    assert loaded.total_usage.total_tokens == 123


def test_mock_cli_eval_compare_and_replay(tmp_path: Path) -> None:
    assert (
        main(
            [
                "eval",
                "--mock",
                "optimal",
                "--protocol",
                "apple",
                "--protocol",
                "interactive",
                "--disks",
                "3",
                "--results-dir",
                str(tmp_path),
                "--no-animate",
            ]
        )
        == 0
    )
    results = ResultStore(tmp_path).load_all()
    assert len(results) == 2
    assert main(["compare", "--results-dir", str(tmp_path)]) == 0
    replay_args = [
        "replay",
        results[0].run_id[:10],
        "--results-dir",
        str(tmp_path),
        "--delay",
        "0",
    ]
    assert main(replay_args) == 0


def test_renderer_handles_invalid_sequence_without_crashing() -> None:
    config = RunConfig(
        model="mock-invalid",
        reasoning_effort="none",
        disks=3,
        trial=1,
        protocol="apple",
        max_output_tokens=64_000,
        move_budget_multiplier=2.0,
    )
    result = BenchmarkRunner(MockProvider("invalid")).run(config)
    output = StringIO()

    replay(result, console=Console(file=output, force_terminal=False), delay=0)

    assert "INVALID" in output.getvalue()
    assert "INVALID_MOVE" in output.getvalue()

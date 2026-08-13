# Repository guidance for coding agents

## Mission

Hanoi Redemption evaluates whether OpenAI models can produce valid Towers of Hanoi solutions as
complexity grows. Preserve the experiment, not merely a generic Hanoi solver. The primary user
experience is the guided terminal interface opened by bare `hanoi`; subcommands exist for
automation. Use `hanoi run` for a prompt-free run with explicit experiment parameters; retain
`hanoi eval` as the backward-compatible matrix command with defaults.

Read `README.md` before making product changes. Inspect the working tree and preserve unrelated
user changes.

## Experimental invariants

- Public `paper` and persisted `apple` identify the same paper-style one-shot protocol. It must make
  one API call per trial and ask for the complete explicit move list in that response. Do not replace
  the answer with code, a recurrence, or an abbreviated pattern. Keep `apple` persistence compatible
  with existing results.
- The `standard` prompt must not reveal the recursive algorithm. Only the explicit `algorithm`
  variant may supply it.
- `interactive` requests exactly one move from the current board state. It is useful but was not in
  the Apple paper, so never present it as a direct reproduction.
- The deterministic simulator is the source of truth. Never accept the model's statement that it
  solved the puzzle without validating every move and the final board.
- Paper comparisons are directional: 1–4 disks were generally strong, 5–7 were a transition, and
  collapse began around 7–8. Keep the caveat that models, APIs, and extraction differ.
- Hanoi grows exponentially: the optimal sequence is `2^n - 1` moves. Preserve the large-run guard
  and the paid-call estimate.
- Persist enough metadata to reproduce comparisons. If a result contract changes incompatibly,
  update its schema/prompt version and add compatibility tests.
- Store run-level `processing_time_seconds` and aggregate `token_usage` explicitly. Continue loading
  schema-v1 files that used `elapsed_seconds` and only per-call token usage.

## Architecture

- `src/hanoi_redemption/cli.py`: argparse commands and the guided Rich menu.
- `src/hanoi_redemption/game.py`: legal-move engine and deterministic optimal solver.
- `src/hanoi_redemption/prompts.py`: paper-style and interactive prompt construction.
- `src/hanoi_redemption/protocols.py`: public aliases and user-facing protocol names.
- `src/hanoi_redemption/providers.py`: OpenAI Responses API and deterministic mock providers.
- `src/hanoi_redemption/benchmark.py`: protocol orchestration and failure capture.
- `src/hanoi_redemption/models.py`: request, response, validation, and persistence contracts.
- `src/hanoi_redemption/storage.py`: atomic local JSON storage.
- `src/hanoi_redemption/visualization.py`: terminal board rendering and replay.
- `src/hanoi_redemption/paper.py`: paper baseline and per-run comparison wording.
- `src/hanoi_redemption/credentials.py`: local credential resolution without logging secrets.

Keep business rules out of terminal rendering when practical. Prefer pure functions for parsing,
validation, and comparison language so they are easy to test.

## OpenAI models and credentials

- Model availability, deprecation dates, reasoning efforts, and API behavior change. Verify current
  official OpenAI documentation before changing the curated model menu.
- Keep model-specific reasoning choices accurate. Custom model IDs may expose the broader list and
  preserve unsupported combinations as recorded API errors.
- The paper-era `o3-mini` option is historically useful but deprecated. Update or remove its warning
  when its availability changes; do not silently route it to another model.
- Credential precedence is the `OPENAI_API_KEY` environment variable, then the project `.env`.
  Do not search unrelated user configuration files. Never print, persist, copy, or expose an API
  key, and do not inspect secret values during routine work.
- Tests and ordinary verification must not make paid API calls. Use `--mock`. Make a real API call
  only when the user explicitly requests live verification; use the smallest meaningful run and
  report that a paid call was made.

## Local data and generated files

- `results/` is the product's local result database and is ignored by Git. Do not delete real runs as
  cleanup. Use a temporary results directory in tests and diagnostics.
- New result filenames must remain descriptive and sortable; legacy run-ID-only filenames must stay
  loadable. Result lookup should use the JSON `run_id`, not assume it is the whole filename.
- `.env`, `.venv`, caches, and `*.egg-info` are local/generated and ignored.
- Do not commit research PDFs, screenshots, rendered pages, test results, or temporary output.
- Keep `pyproject.toml` and `uv.lock` as the dependency sources of truth. Do not reintroduce parallel
  `requirements.txt` files without a concrete compatibility need.

## Development and verification

Use uv from the repository root:

```bash
uv sync --dev
uv run ruff check .
uv run pytest
```

For a terminal smoke test without API calls, use a temporary results directory or cancel before the
confirmation prompt. Useful examples:

```bash
HANOI_SMOKE_RESULTS=$(mktemp -d)
uv run hanoi eval --mock optimal --disks 3 --no-animate --results-dir "$HANOI_SMOKE_RESULTS"
printf 'q\n' | uv run hanoi
```

Add focused tests for every behavior change. At handoff, run Ruff, the complete test suite, and
`git diff --check`. If terminal UX changed, exercise the installed or `uv run` command itself and
inspect its rendered output.

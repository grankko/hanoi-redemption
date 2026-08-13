# Hanoi Redemption

Can modern language models solve Towers of Hanoi as the puzzle grows? Hanoi Redemption is an
interactive terminal benchmark for running that experiment against OpenAI models, validating every
move, storing the results, and replaying games as terminal animations.

The project is inspired by Apple's 2025 paper [*The Illusion of
Thinking*](https://machinelearning.apple.com/research/illusion-of-thinking). In its strict
one-response Hanoi experiment, models were generally strong at 1–4 disks, degraded across 5–7,
began collapsing around 7–8, and produced near-zero complete solutions by roughly 9–10 disks. A
solution requires `2^n - 1` legal moves, and one bad move fails the whole attempt.

This is not a claim that an LLM can never solve Hanoi. It is a test of how reliably a model can
execute a long, exact plan. The application keeps the paper baseline visible so each run has useful
context.

## Install and run

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required.

```bash
uv tool install --editable .
hanoi
```

Bare `hanoi` opens the guided interface. From there you can:

- choose a model and a model-compatible reasoning level;
- select disk counts, trial count, and benchmark protocol;
- see the maximum number of paid API calls before confirming;
- watch returned solutions play in the terminal;
- browse saved runs, open their full details, compare them, or replay a game; and
- preview the exact prompt without calling the API.

The model menu includes the current GPT-5.6 family, paper-era `o3` and `o3-mini`, and a custom
model-ID option. Lifecycle warnings are shown for known deprecated models.

## Credentials

The application looks for an API key in this order:

1. the `OPENAI_API_KEY` environment variable;
2. `OPENAI_API_KEY` in the repository's ignored `.env` file.

You can start from `.env.example`. Keys are never written to benchmark results or printed by the
application.

## The two protocols

`paper` is the paper-style benchmark. Each trial makes exactly one API call. The model receives the
rules and a concrete initial state, then must return the entire explicit move sequence in that one
response. The optional `algorithm` prompt also supplies the recursive solution procedure, mirroring
the paper's algorithm-guided ablation. Results retain the original internal name `apple` for backward
compatibility.

`interactive` asks for one move at a time and sends the resulting board state back to the model.
This tests whether a model can play when it does not have to serialize an exponentially long answer
in one generation. The paper did not test this protocol, so interactive results are not directly
comparable to its headline result.

The guided menu defaults to disks 3–8 for the paper protocol, covering the reported transition and
collapse region. Interactive play defaults to 3–5 because it makes one paid call per move. These are
starting values, not limits: the field accepts a single count such as `7`, a range such as `3-8`, or
a list such as `3,5,7`.

Both protocols use the same deterministic simulator. The validator checks the named disk, source
and destination pegs, legality of every move, and final state. It does not trust the model's own claim
that a puzzle was solved.

## Results

Each attempt is saved atomically under `results/runs/`. The local `results/` directory is ignored by
Git. New filenames carry useful context while retaining a short unique run ID, for example:

```text
2026-08-13_20-59-34Z_gpt-5.6-luna_medium_paper_7d_t1_incomplete_5861e99c06.json
```

Older files named with only a run ID remain supported. Each JSON result contains:

- model, reasoning effort, protocol, prompt variant, disk count, and trial;
- every returned move and interactive move explanation;
- pass/failure status, first invalid move, optimality, and efficiency;
- total processing time, aggregate token usage, per-call latency and token usage, and response IDs;
  and
- schema and prompt versions.

Use **Browse saved results** in the interactive menu to see newest-first results, open a run's full
configuration, outcome, token usage, error, and filename, or replay its moves. Automation-friendly
subcommands remain available:

```bash
hanoi eval --protocol paper --model gpt-5.6-luna --reasoning medium --disks 3-8 --no-animate
hanoi browse
hanoi compare
hanoi replay RUN_ID_PREFIX
hanoi prompt --disks 8
```

Reasoning support varies by model. The guided menu limits known models to compatible choices. A
custom or unsupported command-line combination is stored as an `api_error` instead of silently
disappearing from the experiment.

## Cost and experimental limits

The Apple protocol needs one API call per trial. Interactive play may need up to twice the optimal
move count, so its call count grows exponentially. The app shows this upper bound before an
interactive run starts.

The default output budget is 64,000 tokens, matching the scale used in the paper. Disk counts above
12 require explicit command-line opt-in. Results are directional rather than an exact paper
replication: this project uses current OpenAI APIs and structured outputs, does not expose private
reasoning traces, and lets the user choose models and reasoning settings.

## Development

Install the locked project and development tools, then run the checks:

```bash
uv sync --dev
uv run ruff check .
uv run pytest
```

Use deterministic mock runs for local end-to-end testing without spending API credits:

```bash
uv run hanoi eval --mock optimal --disks 4
uv run hanoi eval --mock invalid --disks 4
uv run hanoi eval --mock incomplete --disks 4
```

See `AGENTS.md` for repository invariants and guidance for automated contributors.

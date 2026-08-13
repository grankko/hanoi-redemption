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

## Non-interactive runs and AI agents

Use `hanoi run` to start an evaluation without opening the menu, asking for confirmation, or reading
from standard input. The four experiment-defining flags are required, and animation is disabled by
default. After validating the flags and credentials, it begins potentially paid API calls
immediately, so an agent should only execute it when the run has been authorized:

```bash
hanoi run \
  --model gpt-5.6-luna \
  --reasoning medium \
  --protocol paper \
  --prompt standard \
  --disks 7 \
  --trials 1 \
  --max-output-tokens 64000 \
  --results-dir results
```

The command reads `OPENAI_API_KEY` from the environment or the repository's ignored `.env` file.
An automated caller should supply these flags explicitly:

| Flag | Meaning |
| --- | --- |
| `--model MODEL` | Exact OpenAI model ID to request. |
| `--reasoning LEVEL` | `default`, `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, or `max`; support depends on the model. |
| `--protocol paper\|interactive` | `paper` requests the complete move list in one API call; `interactive` makes one call per move. |
| `--disks COUNT_OR_SET` | A count such as `7`, range such as `3-8`, or list such as `3,5,7`. |
| `--prompt standard\|algorithm` | Paper prompt variant; defaults to `standard` and is ignored by the interactive protocol. |
| `--trials N` | Independent attempts per configuration; defaults to `1`. |
| `--max-output-tokens N` | Output-plus-reasoning limit per API request; defaults to `64000`. |
| `--results-dir PATH` | Storage root; JSON files are written below `PATH/runs/`. |

Repeat `--model`, `--reasoning`, `--protocol`, or `--prompt` to run their Cartesian product. `eval`
is the backward-compatible matrix command and supplies defaults when those flags are omitted. Run
`hanoi run --help` for the complete flag list and a cost-relevant explanation of each protocol.

Exit status `0` means every requested API call completed and its result was saved; it does **not**
mean the model solved the puzzle. Status `1` means an API call failed, and status `2` means the
invocation, configuration, or credentials were invalid. To determine puzzle success, open the path
printed by the command and inspect `validation.solved` and `validation.status` in the saved JSON.

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
configuration, outcome, token usage, error, and filename, or replay its moves. Additional
automation-friendly subcommands are available:

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
12 require explicit command-line opt-in. This recreates the paper's core puzzle test, not every
experimental control: the paper generated 25 samples per puzzle setting and extracted move lists
from free-form responses, while this project uses schema-constrained output and lets you choose the
model, reasoning setting, and number of trials. OpenAI models also do not expose their private
reasoning traces through this application.

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

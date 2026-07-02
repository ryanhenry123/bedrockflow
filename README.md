# orchflow

Composable quality gates for Bedrock scripts. Call a model, run an eval panel, retry with feedback until the output passes or you hit a hard stop.

## Install

```bash
uv sync --all-groups --extra aws
```

Requires Python 3.13+. AWS credentials and Bedrock model access for the live example.

## Quick start

```python
from orchflow import Context, EvalVerdict, converse_with_evals

def eval_has_answer(_ctx, result) -> EvalVerdict:
    if len(result.text.strip()) < 20:
        _ctx.feedback("answer in at least one full sentence")
        return EvalVerdict.RETRY
    return EvalVerdict.OK

ctx = Context(question="What is 2+2?")
out = converse_with_evals(
    "us.anthropic.claude-sonnet-4-6",
    initial=ctx["question"],
    evals=[eval_has_answer],
    ctx=ctx,
    max_tokens=256,
)
print(out.result.text)
```

Orchflow owns message threading on retries — you never wire `Turn.build()` yourself.

## Trade memo example

```bash
export AWS_REGION=us-east-1
export ORCHFLOW_MODEL=us.anthropic.claude-sonnet-4-6
uv run orchflow run
# or: ./src/orchflow/examples/run.sh
```

## Offline eval harness

Tune eval panels against saved drafts without calling Bedrock:

```bash
uv run orchflow eval tests/fixtures/good_memo.md
uv run orchflow eval tests/fixtures/ --ctx '{"max_words":600,"min_words":100,"min_trades":1,"evidence_years":[2024,2026]}'
uv run orchflow eval my_draft.md --panel orchflow.examples.evals:DRAFT_EVALS
```

Exit code is 0 when all fixtures pass, 1 when any eval returns retry or fail.

## API

| Export | Role |
|--------|------|
| `converse_with_evals()` | **Primary path** — Bedrock Converse + eval loop + retry threading |
| `run_with_evals()` | Lower-level loop when you own the `call` function |
| `Context` | Shared state; `feedback()` queues retry reasons |
| `EvalVerdict` | `OK`, `RETRY`, or `FAIL` |
| `converse()` | Thin wrapper around `BedrockRuntime.Client.converse` |

CLI: `orchflow run` (live example), `orchflow eval <paths>` (offline fixtures).

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHFLOW_MODEL` | `us.anthropic.claude-sonnet-4-6` | Inference profile model ID |
| `ORCHFLOW_VISIBLE_TURNS` | `true` | Show tqdm progress and retry reasons |
| `ORCHFLOW_PRINT_LAST_DRAFT` | `true` | Print last draft to stderr on max turns |

## Tests

```bash
uv run pytest
uv run orchflow eval tests/fixtures/
```

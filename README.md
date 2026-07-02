# orchflow

Composable quality gates for Bedrock scripts. Call a model, run an eval panel, retry with feedback until the output passes or you hit a hard stop.

## Install

```bash
uv sync --all-groups --extra aws
```

Requires Python 3.13+. AWS credentials and Bedrock model access for the live example.

## Quick start

```python
from orchflow import Context, EvalVerdict, run_with_evals
from orchflow.providers.aws.bedrockruntime import converse

def eval_has_answer(_ctx, result) -> EvalVerdict:
    if len(result.text.strip()) < 20:
        _ctx.feedback("answer in at least one full sentence")
        return EvalVerdict.RETRY
    return EvalVerdict.OK

ctx = Context(question="What is 2+2?")
out = run_with_evals(
    call=lambda turn: converse(
        "us.anthropic.claude-sonnet-4-6",
        turn.build(initial=ctx["question"]),
        max_tokens=256,
    ),
    evals=[eval_has_answer],
    ctx=ctx,
)
print(out.result.text)
```

## Trade memo example

Runs a PM trade memo through a domain eval panel (structure, sizing, triggers, brevity):

```bash
export AWS_REGION=us-east-1
export ORCHFLOW_MODEL=us.anthropic.claude-sonnet-4-6
./src/orchflow/examples/run.sh
```

Or: `uv run orchflow`

## API

| Export | Role |
|--------|------|
| `run_with_evals()` | Main loop: call → eval panel → retry |
| `Turn.build()` | Builds Bedrock messages; retries send initial prompt + latest draft + feedback |
| `Context` | Shared state; `feedback()` queues retry reasons |
| `EvalVerdict` | `OK`, `RETRY`, or `FAIL` |
| `converse()` | Thin wrapper around `BedrockRuntime.Client.converse` |

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHFLOW_MODEL` | `us.anthropic.claude-sonnet-4-6` | Inference profile model ID |
| `ORCHFLOW_VISIBLE_TURNS` | `true` | Show tqdm progress and retry reasons |
| `ORCHFLOW_PRINT_LAST_DRAFT` | `true` | Print last draft to stderr on max turns |

## Tests

```bash
uv run pytest
```

# AWS Bedrock Examples

Orchflow workflows that call Amazon Bedrock through the runtime client, with **eval** gates and **failure** handlers wired into the DAG executor.

## File map

| Path | Purpose |
|------|---------|
| [`examples/aws/tasks.py`](tasks.py) | Registered `CALLER` / `EVAL` / `FAILURE` step functions |
| [`examples/aws/_runner.py`](_runner.py) | Loads AWS task module and prints memo / eval / failure outcomes |
| [`examples/aws/run_python.py`](run_python.py) | Happy path — Python `WorkflowSpec` + live Bedrock |
| [`examples/aws/run_yaml.py`](run_yaml.py) | Happy path — YAML workflow + live Bedrock |
| [`examples/aws/run_json.py`](run_json.py) | Happy path — JSON workflow + live Bedrock |
| [`examples/aws/run_mock.py`](run_mock.py) | Happy path — mock Bedrock (no AWS creds) |
| [`examples/aws/run_eval_fail.py`](run_eval_fail.py) | **Eval loop** — model returns, validator rejects, downstream skipped |
| [`examples/aws/run_failure.py`](run_failure.py) | **Failure loop** — caller raises, `on_failure` runs, downstream skipped |
| [`examples/aws/workflows/risk_summary.yaml`](workflows/risk_summary.yaml) | Declarative workflow (YAML) |
| [`examples/aws/workflows/risk_summary.json`](workflows/risk_summary.json) | Declarative workflow (JSON) |
| [`modelprovider/bedrockruntimeclient.py`](../modelprovider/bedrockruntimeclient.py) | Bedrock Runtime facade (`converse`, stream, token count) |
| [`modelprovider/runtime/types.py`](../modelprovider/runtime/types.py) | Typed request/response models |
| [`modelprovider/runtime/parsing.py`](../modelprovider/runtime/parsing.py) | Response + stream parsing |
| [`modelprovider/bedrockclient.py`](../modelprovider/bedrockclient.py) | Foundation model catalog / enum generation |
| [`src/executor.py`](../src/executor.py) | DAG executor — eval fail vs failure handler semantics |
| [`src/models/roles.py`](../src/models/roles.py) | `Role.CALLER`, `Role.EVAL`, `Role.FAILURE` contracts |

## Workflow: `aws_risk_summary`

```
load_thesis
    └── summarize_risk  (eval: validate_summary, on_failure: handle_bedrock_failure)
            └── format_memo
```

1. **`load_thesis`** — normalizes `symbol`, `thesis`, `model_id` in context.
2. **`summarize_risk`** — calls Bedrock Converse (or mock) and stores token usage + text.
3. **`validate_summary`** — eval gate: non-empty text, minimum length, not content-filtered.
4. **`handle_bedrock_failure`** — failure handler when Converse raises.
5. **`format_memo`** — final string output (only runs if summarize + eval pass).

### Eval vs failure (executor behavior)

| Outcome | Trigger | Downstream steps |
|---------|---------|------------------|
| **Eval fail** | Caller succeeds, `validate_summary` returns `False` | Skipped (`format_memo` never runs). Caller output remains in context under the step key. |
| **Failure handled** | Caller raises, `handle_bedrock_failure` runs | Skipped |
| **Success** | Caller succeeds, eval passes | Continue |

See [`src/executor.py`](../src/executor.py) (`_apply_outcome`).

## Prerequisites (live runs)

```bash
uv sync --extra aws --extra ui
```

- AWS credentials configured (`aws configure`, SSO, or env vars).
- Bedrock model access enabled in your region.
- Default model: `amazon.nova-lite-v1:0` (override via context `model_id`).

Verify Bedrock connectivity:

```bash
uv run python -m modelprovider.bedrockruntimeclient
```

Anthropic and other models may require an [inference profile](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html) ID instead of a raw foundation model ID.

## Run commands

From repo root:

```bash
# Live Bedrock (default for workflow YAML, UI, and run_python/yaml/json)
uv run python -m examples.aws.run_python
uv run python -m examples.aws.run_yaml
uv run python -m examples.aws.run_json
uv run python -m src.ui

# Offline mock (no AWS credentials)
uv run python -m examples.aws.run_mock

# Control-flow demos (mock)
uv run python -m examples.aws.run_eval_fail
uv run python -m examples.aws.run_failure
```

## Context keys

| Key | Default | Description |
|-----|---------|-------------|
| `symbol` | `AAPL` | Ticker for the risk memo |
| `thesis` | `Long gamma into earnings` | Position thesis sent to the model |
| `model_id` | `amazon.nova-lite-v1:0` | Bedrock foundation model or inference profile |
| `mock_bedrock` | `false` | Skip AWS; use canned response |
| `mock_response_text` | built-in string | Override mock model output |
| `force_bedrock_error` | `false` | Raise in mock/live caller for failure demo |
| `min_response_chars` | `40` | Eval length threshold; raise to force retry/fail |

## Extending

- Add steps in [`tasks.py`](tasks.py) with `@register(..., Role.CALLER|EVAL|FAILURE)`.
- Reference them in [`workflows/risk_summary.yaml`](workflows/risk_summary.yaml).
- Use [`BedrockRuntimeClass.converse_stream`](../modelprovider/bedrockruntimeclient.py) for streaming steps.
- Regenerate provider enums: `uv run python -m modelprovider.bedrockclient`.

## Tests

Mock-mode tests live in [`tests/test_aws_examples.py`](../tests/test_aws_examples.py) — no AWS credentials in CI.

## UI

Workflows under `examples/**/workflows/` are auto-discovered by the pipeline console. `aws_risk_summary` uses live Bedrock by default (`model_id: amazon.nova-lite-v1:0`). Install the AWS extra, then restart after YAML changes:

```bash
uv sync --extra ui --extra aws
uv run python -m src.ui
```

Set `mock_bedrock: true` in `default_context` only for offline UI demos.

Optional YAML metadata (see [`src/ui/discovery.py`](../src/ui/discovery.py)):

- `task_module` — override task module resolution
- `default_context` — initial context passed to the DAG
- `report_key` — step name whose output becomes the run report (inferred from sink step if omitted)
- `max_workers` — parallel executor cap (inferred from DAG width if omitted)

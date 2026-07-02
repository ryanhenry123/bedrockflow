# orchflow

**CI for Bedrock outputs** — composable gates, correct retries, offline fixtures.

MIT License. See [LICENSE](LICENSE).

## Install

```bash
pip install "orchflow[aws]"
# or: uv sync --all-groups --extra aws
```

Python 3.11+.

## Quick start

```python
from orchflow import Context, converse_with_evals, markdown_sections

out = converse_with_evals(
    "us.anthropic.claude-sonnet-4-6",
    initial="Summarize tail risk in vol selling.",
    evals=markdown_sections("## Summary", "## Risks", max_words=300),
    ctx=Context(),
    max_tokens=512,
)
print(out.trace)  # per-turn named eval failures + tokens
```

See [docs/COOKBOOK.md](docs/COOKBOOK.md) for JSON gates, tables, model compare, prompt caching.

## CLI

```bash
# Live Bedrock
orchflow run --example simple
orchflow run --example trade_memo --record drafts/latest.md --trace runs/latest.json
orchflow run --cache-initial   # Bedrock prompt cache on initial message

# Offline fixture CI (no AWS)
orchflow eval tests/fixtures/trade_memo/ --verbose
orchflow eval tests/fixtures/simple/ --panel orchflow.examples.simple_evals:SIMPLE_EVALS
orchflow eval draft.md --only verdict_actionable --json

# Model A/B on the same panel
orchflow compare us.anthropic.claude-sonnet-4-6 us.amazon.nova-pro-v1:0 --example simple
```

## Starter panels

```python
from orchflow import markdown_sections, json_object, no_preamble, csv_table
```

## Trace artifacts

`--trace runs/latest.json` writes turns, named eval steps, token totals (including cache read/write).

## CI

Fixture eval job runs on every PR — see [.github/workflows/ci.yml](.github/workflows/ci.yml).

```bash
uv run pytest
uv run black --check .
```

## PyPI

```bash
uv build && uv publish
```

Launch draft: [docs/LAUNCH.md](docs/LAUNCH.md)

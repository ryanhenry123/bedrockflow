# AWS examples index

Bedrock workflow examples live under **`examples/aws/`**.

Start here: [`examples/aws/README.md`](aws/README.md)

Workflows are auto-discovered by the UI from `examples/**/workflows/`. Restart `uv run python -m src.ui` after adding one.

Quick runs:

```bash
uv sync --extra aws --extra ui
uv run python -m src.ui                    # live Bedrock in UI
uv run python -m examples.aws.run_python   # live Bedrock CLI
uv run python -m examples.aws.run_mock       # offline mock
```

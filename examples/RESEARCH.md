# Research report examples

Multi-turn Bedrock eval loops that draft institutional research notes.

Start: [`examples/research/run_mock.py`](research/run_mock.py) (offline) or [`examples/research/run_python.py`](research/run_python.py) (live).

Workflow specs (aligned):

- [`examples/research/workflows/research_report.yaml`](research/workflows/research_report.yaml)
- [`examples/research/workflows/research_report.json`](research/workflows/research_report.json)
- [`examples/research/run_python.py`](research/run_python.py) (`RESEARCH_REPORT`)

The `draft_research_report` step runs up to **4 model turns** with **4 eval gates** (structure, recency, references, depth).

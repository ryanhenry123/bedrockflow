#!/bin/bash
set -e

export AWS_REGION="us-east-1"
export ORCHFLOW_MODEL="us.anthropic.claude-sonnet-4-6"
uv run python -m orchflow.examples.research_note
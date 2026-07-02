#!/bin/bash
set -e

export AWS_REGION="${AWS_REGION:-us-east-1}"
export BEDROCKFLOW_MODEL="${BEDROCKFLOW_MODEL:-us.anthropic.claude-sonnet-4-6}"
uv run python -m bedrockflow.examples.trade_memo

from orchflow.providers.aws.bedrockruntime import parse_converse_response

SAMPLE_RESPONSE = {
    "output": {
        "message": {
            "role": "assistant",
            "content": [{"text": "Hello world."}],
        }
    },
    "stopReason": "end_turn",
    "usage": {
        "inputTokens": 10,
        "outputTokens": 5,
        "totalTokens": 15,
    },
    "metrics": {"latencyMs": 42},
}


def test_parse_converse_response():
    result = parse_converse_response(SAMPLE_RESPONSE)
    assert result.text == "Hello world."
    assert result.stop_reason == "end_turn"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 5
    assert result.metrics is not None
    assert result.metrics.latency_ms == 42

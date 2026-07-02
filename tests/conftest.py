from dataclasses import dataclass


@dataclass(frozen=True)
class MockResult:
    text: str
    stop_reason: str = "end_turn"

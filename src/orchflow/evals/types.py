from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EvalResult(Protocol):
    """Minimal model output surface for eval functions."""

    text: str
    stop_reason: str

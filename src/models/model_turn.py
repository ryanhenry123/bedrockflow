from __future__ import annotations

from dataclasses import dataclass

from src.registry import Context


@dataclass(frozen=True, slots=True)
class ModelTurnSession:
    step_name: str
    turn: int
    max_turns: int

    @classmethod
    def read(
        cls, ctx: Context, step_name: str, *, max_turns: int = 1
    ) -> ModelTurnSession:
        raw_turn = ctx.get_shared(f"{step_name}__turn")
        turn = int(raw_turn) if isinstance(raw_turn, int) and raw_turn > 0 else 1
        return cls(step_name=step_name, turn=turn, max_turns=max_turns)

    @property
    def is_retry(self) -> bool:
        return self.turn > 1

    def feedback(self, ctx: Context) -> list[str]:
        raw = ctx.get_shared(f"{self.step_name}__feedback")
        if isinstance(raw, list):
            return [str(item) for item in raw if str(item).strip()]
        return []

    def prior_result(self, ctx: Context) -> object | None:
        if not self.is_retry:
            return None
        return ctx.get_shared(self.step_name)

    @staticmethod
    def request_retry(ctx: Context, step_name: str, reason: str) -> None:
        ctx.set_shared(f"{step_name}__retry_reason", reason.strip())

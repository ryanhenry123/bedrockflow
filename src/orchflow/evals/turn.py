from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from orchflow.providers.aws.bedrockruntime import assistant_message, user_message


@dataclass(frozen=True, slots=True)
class Turn:
    turn: int
    messages: list[dict[str, Any]]
    feedback: list[str]

    @property
    def is_retry(self) -> bool:
        return self.turn > 1

    def build(self, *, initial: str) -> list[dict[str, Any]]:
        if not self.is_retry:
            return [user_message(initial)]
        # Only the latest draft — stacking every prior turn bloats context and
        # the model truncates tail sections on long retries.
        msgs = [user_message(initial), self.messages[-1]]
        msgs.append(
            user_message(
                "Revise your full memo (all sections). Address:\n- "
                + "\n- ".join(self.feedback)
            )
        )
        return msgs

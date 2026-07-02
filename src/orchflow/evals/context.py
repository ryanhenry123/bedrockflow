from __future__ import annotations


class Context(dict):
    def feedback(self, msg: str) -> None:
        self["_pending_feedback"] = msg

    def pop_feedback(self) -> str | None:
        msg = self.pop("_pending_feedback", None)
        return msg.strip() if isinstance(msg, str) and msg.strip() else None

    def set_feedback(self, reasons: list[str]) -> None:
        self["_feedback"] = reasons

    @property
    def feedback_items(self) -> list[str]:
        raw = self.get("_feedback")
        return [str(x) for x in raw if str(x).strip()] if isinstance(raw, list) else []

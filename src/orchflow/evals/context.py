from __future__ import annotations


class Context(dict):
    def feedback(self, msg: str) -> None:
        if msg.strip():
            self.setdefault("_pending_feedback", []).append(msg.strip())

    def drain_feedback(self) -> list[str]:
        items = self.pop("_pending_feedback", [])
        return (
            [str(x).strip() for x in items if str(x).strip()]
            if isinstance(items, list)
            else []
        )

    def set_feedback(self, reasons: list[str]) -> None:
        self["_feedback"] = reasons

    @property
    def feedback_items(self) -> list[str]:
        raw = self.get("_feedback")
        return [str(x) for x in raw if str(x).strip()] if isinstance(raw, list) else []

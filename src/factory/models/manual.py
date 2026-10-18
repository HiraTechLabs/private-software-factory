"""Manual provider: the Factory writes the prompt and waits for a pasted answer."""

from __future__ import annotations


class ManualAnswerRequired(Exception):
    """Raised when a manual role has no answer yet; the change waits for the owner."""

    def __init__(self, prompt: str) -> None:
        super().__init__("waiting for a pasted answer")
        self.prompt = prompt


def answer(prompt: str, existing: str | None) -> str:
    if existing and existing.strip():
        return existing
    raise ManualAnswerRequired(prompt)

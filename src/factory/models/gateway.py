"""One interface for the planning, build, and review roles (ADR 0011).

Providers: `manual` (the owner pastes), `ollama` (a local server), `demo` (scripted).
"""

from __future__ import annotations

from dataclasses import dataclass

from factory.models import demo, manual, ollama
from factory.models.manual import ManualAnswerRequired

PROVIDERS = ("manual", "ollama", "demo")

__all__ = ["Answer", "ManualAnswerRequired", "ask", "test_provider"]


@dataclass
class Answer:
    text: str
    provider: str


def ask(
    role: str,
    prompt: str,
    *,
    provider: str,
    model: str = "",
    settings: dict | None = None,
    existing_answer: str | None = None,
    demo_context: dict | None = None,
    transport=None,
) -> Answer:
    settings = settings or {}
    if provider == "demo":
        return Answer(demo.answer(role, demo_context or {}), "demo")
    if provider == "ollama":
        text = ollama.chat(
            model,
            prompt,
            settings.get("ollama_url", "http://127.0.0.1:11434"),
            float(settings.get("model_timeout_seconds", 900)),
            transport=transport,
        )
        return Answer(text, "ollama")
    # default and fallback: manual
    return Answer(manual.answer(prompt, existing_answer), "manual")


def test_provider(
    provider: str,
    model: str,
    settings: dict | None = None,
    transport=None,
) -> tuple[bool, str]:
    settings = settings or {}
    if provider == "demo":
        return True, "The demo model is always ready (scripted answers)."
    if provider == "ollama":
        return ollama.test_connection(
            model,
            settings.get("ollama_url", "http://127.0.0.1:11434"),
            transport=transport,
        )
    return True, (
        "Manual mode is ready: the Factory writes the prompt and you paste the answer."
    )

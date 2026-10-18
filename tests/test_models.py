"""Model provider tests: manual round trip, the demo model, Ollama via MockTransport."""

from __future__ import annotations

import httpx
import pytest

from factory.models import gateway, manual, ollama


def test_manual_round_trip():
    with pytest.raises(manual.ManualAnswerRequired):
        gateway.ask("plan", "a prompt", provider="manual")
    answer = gateway.ask("plan", "a prompt", provider="manual", existing_answer="hello")
    assert answer.text == "hello"
    assert answer.provider == "manual"
    assert gateway.test_provider("manual", "")[0] is True


def test_demo_answers():
    context = {
        "request_title": "Add a greeting",
        "request_text": "please",
        "change_id": "c-0001",
    }
    plan = gateway.ask("plan", "p", provider="demo", demo_context=context)
    assert "Add a greeting" in plan.text
    build = gateway.ask("build", "p", provider="demo", demo_context=context)
    assert "<<<FILE notes/c-0001.md>>>" in build.text
    review = gateway.ask("review", "p", provider="demo", demo_context=context)
    assert review.text.startswith("VERDICT: approve")
    assert gateway.test_provider("demo", "")[0] is True


def _transport(handler):
    return httpx.MockTransport(handler)


def test_ollama_chat_ok():
    def handler(request):
        assert request.url.path == "/api/chat"
        return httpx.Response(200, json={"message": {"content": "the answer"}})

    answer = gateway.ask(
        "plan",
        "p",
        provider="ollama",
        model="llama3",
        settings={"ollama_url": "http://local"},
        transport=_transport(handler),
    )
    assert answer.text == "the answer"


def test_ollama_test_connection_model_missing():
    def handler(request):
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": "llama3:latest"}]})

    ok, message = gateway.test_provider(
        "ollama",
        "mistral",
        settings={"ollama_url": "http://local"},
        transport=_transport(handler),
    )
    assert ok is False
    assert "mistral" in message


def test_ollama_test_connection_ok():
    def handler(request):
        return httpx.Response(200, json={"models": [{"name": "llama3:latest"}]})

    ok, message = gateway.test_provider(
        "ollama",
        "llama3",
        settings={"ollama_url": "http://local"},
        transport=_transport(handler),
    )
    assert ok is True
    assert "llama3" in message


def test_ollama_timeout():
    def handler(request):
        raise httpx.TimeoutException("too slow")

    with pytest.raises(ollama.OllamaError):
        gateway.ask(
            "plan",
            "p",
            provider="ollama",
            model="llama3",
            settings={"ollama_url": "http://local"},
            transport=_transport(handler),
        )


def test_ollama_requires_model_name():
    with pytest.raises(ollama.OllamaError):
        gateway.ask("plan", "p", provider="ollama", model="", settings={})

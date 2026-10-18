"""Ollama provider: POST {url}/api/chat; connection test via GET /api/tags."""

from __future__ import annotations

import httpx


class OllamaError(Exception):
    pass


def chat(
    model: str,
    prompt: str,
    url: str,
    timeout: float = 900,
    transport: httpx.BaseTransport | None = None,
) -> str:
    if not model:
        raise OllamaError("No model name is set for this role on the Models page.")
    try:
        with httpx.Client(timeout=timeout, transport=transport) as client:
            response = client.post(
                f"{url.rstrip('/')}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.TimeoutException as exc:
        raise OllamaError(f"The local model took longer than {timeout:.0f}s.") from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaError(
            f"The local model server answered {exc.response.status_code}."
        ) from exc
    except httpx.HTTPError as exc:
        raise OllamaError(f"Could not reach the local model server at {url}.") from exc
    message = payload.get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise OllamaError("The local model returned an empty answer.")
    return content


def test_connection(
    model: str,
    url: str,
    timeout: float = 10,
    transport: httpx.BaseTransport | None = None,
) -> tuple[bool, str]:
    try:
        with httpx.Client(timeout=timeout, transport=transport) as client:
            response = client.get(f"{url.rstrip('/')}/api/tags")
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        return False, f"Could not reach {url}. Is the local model server running?"
    names = [str(item.get("name", "")) for item in (payload.get("models") or [])]
    if not names:
        return False, "The server answered, but it has no models loaded."
    if model and not any(
        name == model or name.split(":")[0] == model for name in names
    ):
        return False, (
            f"The server is running, but it does not list the model {model!r}. "
            f"Available: {', '.join(names)}."
        )
    if model:
        return True, f"Connected. The server lists {model!r}."
    return True, f"Connected. The server lists {len(names)} model(s)."

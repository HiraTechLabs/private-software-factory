"""Scripted demo provider: deterministic answers for the demo project and tests."""

from __future__ import annotations

DEMO_LABEL = "Demo model (scripted)"


def plan_answer(context: dict) -> str:
    title = context.get("request_title", "the request")
    body = context.get("request_text", "").strip()
    return (
        "# Plan\n\n"
        f"We will implement: **{title}**.\n\n"
        "## What changes\n"
        "- Add one notes file that records this request.\n\n"
        "## Files\n"
        "- `notes/" + context.get("change_id", "c-0000") + ".md` (new)\n\n"
        "## Risks\n"
        "- None: this only adds a file and touches nothing else.\n\n"
        "## Records to update\n"
        "- None for the demo project.\n\n"
        "## How to test\n"
        "- Read the new notes file; it should contain the request text.\n\n"
        "## Request text\n"
        f"{body or '(empty)'}\n"
    )


def build_answer(context: dict) -> str:
    change_id = context.get("change_id", "c-0000")
    title = context.get("request_title", "the request")
    body = context.get("request_text", "").strip()
    content = f"# {title}\n\n{body}\n"
    path = f"notes/{change_id}.md"
    return f"<<<FILE {path}>>>\n{content}<<<END>>>\n"


def review_answer(context: dict) -> str:
    return (
        "VERDICT: approve\n\n"
        "## Findings\n"
        "- The change adds a single notes file and matches the plan.\n"
    )


def answer(role: str, context: dict) -> str:
    if role == "plan":
        return plan_answer(context)
    if role == "build":
        return build_answer(context)
    if role == "review":
        return review_answer(context)
    return "(the demo model has no answer for this step)\n"

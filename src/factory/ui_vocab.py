"""Plain-word vocabulary for the Factory UI (closed; ADR 0010, docs/ui/UI_SYSTEM.md).

Templates and pages take status labels, status kinds, and provider words from here;
never hard-code them. scripts/ui_lint.py enforces this.
"""

from __future__ import annotations

# Status kinds: what color a Status shows, always with a text label, never color alone.
STATUS_KINDS: tuple[str, ...] = ("idle", "work", "need", "done", "fail")

KIND_LABELS: dict[str, str] = {
    "idle": "Not started",
    "work": "Working",
    "need": "Needs you",
    "done": "Done",
    "fail": "Failed",
}

# Change states (closed enum) and the status kind each one shows.
STATE_KINDS: dict[str, str] = {
    "draft": "idle",
    "planning": "work",
    "planned": "work",
    "implementing": "work",
    "checking": "work",
    "in_review": "work",
    "awaiting_approval": "need",
    "merged": "done",
    "deployed_dev": "done",
    "awaiting_prod": "need",
    "live": "done",
    "waiting_for_you": "need",
    "interrupted": "need",
    "blocked": "need",
    "failed": "fail",
    "cancelled": "idle",
}

# Status labels shown next to the colored dot.
STATE_LABELS: dict[str, str] = {
    "draft": "Request received",
    "planning": "Planning",
    "planned": "Plan ready",
    "implementing": "Building",
    "checking": "Checking",
    "in_review": "Being reviewed",
    "awaiting_approval": "Needs your approval to merge",
    "merged": "Merged",
    "deployed_dev": "On dev",
    "awaiting_prod": "Needs your approval for production",
    "live": "Live",
    "waiting_for_you": "Waiting for your pasted answer",
    "interrupted": "Stopped by a restart",
    "blocked": "Blocked",
    "failed": "Failed",
    "cancelled": "Cancelled",
}

# Provider words the owner reads (never the old mode jargon).
PROVIDER_LABELS: dict[str, str] = {
    "manual": "You paste",
    "ollama": "Local model",
    "demo": "Demo model",
}

# The one fixed flow: id, label, and who does each step.
FLOW_STEPS: tuple[tuple[str, str, str], ...] = (
    ("request", "Request", "You"),
    ("plan", "Plan", "Model"),
    ("build", "Build", "Model"),
    ("checks", "Checks", "Machine"),
    ("review", "Review", "Model"),
    ("merge", "Merge", "Needs you"),
    ("dev", "Dev", "Machine"),
    ("production", "Production", "Needs you"),
    ("live", "Live", "Machine"),
)

# Which pipeline step is current for each state, so the Request page can mark it.
STATE_STEP: dict[str, str] = {
    "draft": "request",
    "planning": "plan",
    "planned": "plan",
    "implementing": "build",
    "checking": "checks",
    "in_review": "review",
    "awaiting_approval": "merge",
    "merged": "merge",
    "deployed_dev": "dev",
    "awaiting_prod": "production",
    "live": "live",
    "waiting_for_you": "plan",
    "interrupted": "plan",
    "blocked": "plan",
    "failed": "checks",
    "cancelled": "request",
}


def kind_for_state(state: str) -> str:
    return STATE_KINDS.get(state, "idle")


def label_for_state(state: str) -> str:
    return STATE_LABELS.get(state, "Not available yet")


def provider_label(provider: str) -> str:
    return PROVIDER_LABELS.get(provider, "Not available yet")

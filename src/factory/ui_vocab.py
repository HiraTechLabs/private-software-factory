"""State vocabulary for the Factory UI (closed; ADR 0005, docs/ui/UI_SYSTEM.md).

Templates and pages must take state labels, light kinds, and modes from here — never
hard-code them. scripts/ui_lint.py enforces this.
"""

from __future__ import annotations

# Light kinds: what a StateLight shows.
LIGHT_KINDS: tuple[str, ...] = ("idle", "run", "hold", "stop", "shadow", "done")

# Display labels for the light kinds themselves.
LIGHT_KIND_LABELS: dict[str, str] = {
    "idle": "Idle",
    "run": "Running",
    "hold": "Waiting",
    "stop": "Stopped",
    "shadow": "Shadowed",
    "done": "Done",
}

# Task states (closed enum) and the light kind each one shows.
TASK_STATES: dict[str, str] = {
    "draft": "idle",
    "planned": "idle",
    "implementing": "run",
    "checking": "run",
    "in_review": "run",
    "awaiting_approval": "hold",
    "merged": "done",
    "deployed_dev": "done",
    "awaiting_prod": "hold",
    "live": "done",
    "blocked": "hold",
    "failed": "stop",
    "cancelled": "idle",
}

# Task state labels shown next to the StateLight.
TASK_STATE_LABELS: dict[str, str] = {
    "draft": "Draft",
    "planned": "Planned",
    "implementing": "Implementing",
    "checking": "Checking",
    "in_review": "In review",
    "awaiting_approval": "Awaiting approval",
    "merged": "Merged",
    "deployed_dev": "Dev deployed",
    "awaiting_prod": "Awaiting prod",
    "live": "Live",
    "blocked": "Blocked",
    "failed": "Failed",
    "cancelled": "Cancelled",
}

# Modes of autonomy for a step (closed enum).
MODES: tuple[str, ...] = ("manual", "shadow", "live")

MODE_LABELS: dict[str, str] = {
    "manual": "Manual",
    "shadow": "Shadow",
    "live": "Live",
}

# Registry readiness for a project directory (used now, on the dashboard).
READINESS: dict[str, str] = {
    "registered": "done",
    "invalid": "stop",
}

READINESS_LABELS: dict[str, str] = {
    "registered": "Registered",
    "invalid": "Invalid",
}

# LineRail steps for the Factory flow (planned pages will drive this further).
FLOW_STEPS: tuple[str, ...] = (
    "intake",
    "plan",
    "build",
    "checks",
    "review",
    "merge",
    "dev",
    "prod",
)


def light_for_task_state(state: str) -> str | None:
    return TASK_STATES.get(state)


def light_for_readiness(state: str) -> str | None:
    return READINESS.get(state)


def task_state_list() -> list[tuple[str, str]]:
    """All task states with their label, sorted by enum order."""
    return [(state, TASK_STATE_LABELS[state]) for state in TASK_STATES]

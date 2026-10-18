"""The one fixed flow: steps, change states, and the only legal transitions (ADR 0002).

Pure functions, no I/O. Nothing else may set a change state; the orchestrator and
approvals both go through `can_move` / `assert_move`.
"""

from __future__ import annotations

# The nine steps, in order, with who does each one.
STEPS: tuple[tuple[str, str], ...] = (
    ("request", "you"),
    ("plan", "model"),
    ("build", "model"),
    ("checks", "machine"),
    ("review", "model"),
    ("merge", "you"),
    ("dev", "machine"),
    ("production", "you"),
    ("live", "machine"),
)

STEP_ORDER: tuple[str, ...] = tuple(step for step, _ in STEPS)
STEP_ACTOR: dict[str, str] = dict(STEPS)

# States that mean "a machine step is running right now". A restart turns these into
# `interrupted` (ADR 0013).
RUNNING_STATES: frozenset[str] = frozenset(
    {"planning", "implementing", "checking", "in_review"}
)

TERMINAL_STATES: frozenset[str] = frozenset({"live", "cancelled"})

# States a failed, interrupted, or blocked change may be retried into.
_RETRY_TARGETS: set[str] = {
    "draft",
    "planned",
    "checking",
    "in_review",
    "awaiting_approval",
    "deployed_dev",
    "awaiting_prod",
    "cancelled",
}

# Map a running state to the settled state to retry from.
RUNNING_TO_SETTLED: dict[str, str] = {
    "planning": "draft",
    "implementing": "planned",
    "checking": "checking",
    "in_review": "in_review",
}

# state -> states it may move to.
LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"planning", "cancelled"},
    "planning": {
        "planned",
        "waiting_for_you",
        "failed",
        "blocked",
        "cancelled",
        "interrupted",
    },
    "waiting_for_you": {
        "planning",
        "implementing",
        "in_review",
        "cancelled",
        "failed",
    },
    "planned": {"implementing", "failed", "blocked", "cancelled", "interrupted"},
    "implementing": {
        "checking",
        "waiting_for_you",
        "failed",
        "blocked",
        "cancelled",
        "interrupted",
    },
    "checking": {
        "in_review",
        "planned",
        "implementing",
        "failed",
        "cancelled",
        "interrupted",
    },
    "in_review": {
        "awaiting_approval",
        "waiting_for_you",
        "failed",
        "cancelled",
        "interrupted",
    },
    "awaiting_approval": {"merged", "planned", "blocked", "cancelled"},
    "merged": {"deployed_dev", "failed", "blocked", "cancelled", "interrupted"},
    "deployed_dev": {"awaiting_prod", "failed", "cancelled"},
    "awaiting_prod": {"live", "failed", "cancelled"},
    "live": set(),
    "failed": _RETRY_TARGETS,
    "interrupted": _RETRY_TARGETS,
    "blocked": _RETRY_TARGETS,
    "cancelled": set(),
}

# Which state means "this step is running".
STEP_RUNNING_STATE: dict[str, str] = {
    "plan": "planning",
    "build": "implementing",
    "checks": "checking",
    "review": "in_review",
    "merge": "merged",
    "dev": "deployed_dev",
    "production": "live",
}

# The step to run next for a settled state.
NEXT_STEP: dict[str, str] = {
    "draft": "plan",
    "planned": "build",
    "checking": "checks",
    "in_review": "review",
    "merged": "merge",
    "deployed_dev": "dev",
    "awaiting_prod": "production",
}


def can_move(current: str, target: str) -> bool:
    return target in LEGAL_TRANSITIONS.get(current, set())


def assert_move(current: str, target: str) -> None:
    if not can_move(current, target):
        raise ValueError(f"illegal transition: {current} -> {target}")


def is_running(state: str) -> bool:
    return state in RUNNING_STATES


def is_terminal(state: str) -> bool:
    return state in TERMINAL_STATES


def next_step(state: str) -> str | None:
    return NEXT_STEP.get(state)


def running_state(step: str) -> str:
    return STEP_RUNNING_STATE[step]

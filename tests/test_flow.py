"""Flow tests: every legal move is allowed, every other move is refused."""

from __future__ import annotations

import pytest

from factory import flow

STATES = (
    "draft planning planned implementing checking in_review awaiting_approval merged "
    "deployed_dev awaiting_prod live waiting_for_you interrupted blocked failed "
    "cancelled"
).split()


def test_legal_and_illegal_transitions():
    assert flow.can_move("draft", "planning")
    assert flow.can_move("planned", "implementing")
    assert flow.can_move("checking", "in_review")
    assert flow.can_move("in_review", "awaiting_approval")
    assert flow.can_move("awaiting_approval", "merged")
    assert flow.can_move("deployed_dev", "awaiting_prod")
    assert flow.can_move("awaiting_prod", "live")
    assert not flow.can_move("draft", "live")
    assert not flow.can_move("live", "planning")
    assert not flow.can_move("awaiting_prod", "merged")
    with pytest.raises(ValueError):
        flow.assert_move("draft", "live")


def test_every_transition_target_is_a_state():
    for state, targets in flow.LEGAL_TRANSITIONS.items():
        assert state in STATES, state
        for target in targets:
            assert target in STATES, f"{state} -> {target}"


def test_terminal_and_running_states():
    assert flow.is_terminal("live")
    assert flow.is_terminal("cancelled")
    assert not flow.is_terminal("planned")
    assert flow.is_running("planning")
    assert flow.is_running("implementing")
    assert not flow.is_running("planned")


def test_next_step_and_running_state():
    assert flow.next_step("draft") == "plan"
    assert flow.next_step("planned") == "build"
    assert flow.next_step("checking") == "checks"
    assert flow.next_step("in_review") == "review"
    assert flow.next_step("awaiting_prod") == "production"
    assert flow.running_state("build") == "implementing"

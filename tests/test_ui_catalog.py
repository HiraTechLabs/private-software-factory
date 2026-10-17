"""The /ui catalog must render every component, light kind, task state, and mode.

Adding an enum value to factory.ui_vocab forces a catalog update: these tests read the
vocab directly, so a new state breaks the suite until the catalog shows it.
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from factory import ui_vocab
from factory.main import app

client = TestClient(app)
RESPONSE = client.get("/ui")
HTML = RESPONSE.text


def test_ui_page_renders():
    assert RESPONSE.status_code == 200


def test_every_component_appears():
    for component in (
        "state-light",
        "mode-tag",
        "line-rail",
        "gate",
        "evidence-row",
        "ref-chip",
        "data-table",
        "filter-bar",
        "diff-view",
        "log-view",
        "button",
        "field",
        "empty-state",
        "error-state",
        "page-header",
    ):
        assert f'data-component="{component}"' in HTML, (
            f"missing component: {component}"
        )


def test_every_light_kind_appears():
    for kind in ui_vocab.LIGHT_KINDS:
        assert f"state-light--{kind}" in HTML, f"missing light kind: {kind}"


def test_every_task_state_appears():
    for state, label in ui_vocab.task_state_list():
        assert ui_vocab.TASK_STATES[state] in ui_vocab.LIGHT_KINDS
        assert label in HTML, f"missing task state label: {label}"


def test_every_mode_appears():
    for mode in ui_vocab.MODES:
        assert f"mode-tag--{mode}" in HTML, f"missing mode: {mode}"


def test_every_readiness_state_appears():
    for readiness, label in ui_vocab.READINESS_LABELS.items():
        assert ui_vocab.READINESS[readiness] in ui_vocab.LIGHT_KINDS
        assert label in HTML, f"missing readiness label: {label}"

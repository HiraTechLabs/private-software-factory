"""UI lint tests: the repository passes, and the rules catch real problems."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load_ui_lint():
    spec = importlib.util.spec_from_file_location("ui_lint", SCRIPTS / "ui_lint.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def ui_lint(monkeypatch, tmp_path):
    module = _load_ui_lint()
    templates = tmp_path / "templates"
    templates.mkdir()
    static = tmp_path / "static"
    static.mkdir()
    docs = tmp_path / "docs_ui"
    docs.mkdir()
    monkeypatch.setattr(module, "TEMPLATES", templates)
    monkeypatch.setattr(module, "STATIC", static)
    monkeypatch.setattr(module, "DOCS_UI", docs)
    monkeypatch.setattr(module, "TOKENS_CSS", static / "tokens.css")
    return module


def test_ui_lint_passes_on_repo():
    assert _load_ui_lint().main() == 0


def test_ui_lint_catches_dead_controls(ui_lint):
    (ui_lint.TEMPLATES / "bad.html").write_text(
        '<button disabled>No</button>\n<a href="#">nowhere</a>\n', encoding="utf-8"
    )
    assert ui_lint.main() == 1


def test_ui_lint_catches_banned_term(ui_lint):
    (ui_lint.TEMPLATES / "bad.html").write_text("<p>LineRail</p>\n", encoding="utf-8")
    assert ui_lint.main() == 1


def test_ui_lint_catches_literal_color(ui_lint):
    (ui_lint.STATIC / "bad.css").write_text(
        ".x { color: #abcdef; }\n", encoding="utf-8"
    )
    assert ui_lint.main() == 1


def test_ui_lint_catches_physical_property(ui_lint):
    (ui_lint.STATIC / "bad.css").write_text(
        ".x { margin-left: 4px; }\n", encoding="utf-8"
    )
    assert ui_lint.main() == 1

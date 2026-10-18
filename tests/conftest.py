"""Shared test fixtures: an isolated data/ directory and a TestClient on the app.

Every test that touches the store runs against a temporary `data/` tree, so nothing is
written into the real repository. `orchestrator.SYNC` is forced on so runs happen inline
(no background threads in tests).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import factory.main as main_module
import factory.orchestrator as orchestrator
import factory.store as store
from factory.main import app


@pytest.fixture(autouse=True)
def _inline_orchestrator(monkeypatch):
    monkeypatch.setattr(orchestrator, "SYNC", True)


@pytest.fixture()
def data_root(tmp_path, monkeypatch):
    data = tmp_path / "data"
    projects = data / "projects"
    projects.mkdir(parents=True)
    monkeypatch.setattr(store, "DATA_DIR", data)
    monkeypatch.setattr(store, "PROJECTS_DIR", projects)
    monkeypatch.setattr(store, "SHARED_PRINCIPLES_DIR", data / "shared" / "principles")
    monkeypatch.setattr(store, "FACTORY_YAML", data / "factory.yaml")
    monkeypatch.setattr(main_module, "PROJECTS_DIR", projects)
    return data


@pytest.fixture()
def client(data_root):
    """TestClient that does not follow redirects, so a 303 is visible."""
    return TestClient(app, base_url="http://testserver", follow_redirects=False)


@pytest.fixture()
def web(data_root):
    """TestClient that follows redirects, for reading rendered pages."""
    return TestClient(app)

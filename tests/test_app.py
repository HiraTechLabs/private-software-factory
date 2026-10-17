"""App tests: registration, loading, dashboard truthfulness, health, UI catalog."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import factory.main as main_module
from factory.main import app
from factory.manifest import Manifest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    projects_dir = tmp_path / "projects-1"
    projects_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(main_module, "PROJECTS_DIR", projects_dir)
    return TestClient(
        app=app,
        base_url="http://testserver",
        follow_redirects=False,
    )


@pytest.fixture()
def browser_client(tmp_path, monkeypatch):
    """TestClient that follows redirects (for dashboard content assertions)."""
    projects_dir = tmp_path / "projects-2"
    projects_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(main_module, "PROJECTS_DIR", projects_dir)
    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "private-software-factory"}


def test_ui_renders(client):
    response = client.get("/ui")
    assert response.status_code == 200
    assert "UI catalog" in response.text


def test_create_project_valid(client):
    response = client.post(
        "/projects",
        data={
            "name": "Order System",
            "description": "Sells things.",
        },
    )
    assert response.status_code == 303
    config = main_module.PROJECTS_DIR / "order-system" / "project.yaml"
    assert config.exists()
    text = config.read_text(encoding="utf-8")
    assert "principles_version: null" in text
    assert "human_approval_required_for_merge: true" in text


def test_create_project_duplicate(client, browser_client):
    client.post("/projects", data={"name": "Same"})
    response = client.post("/projects", data={"name": "Same"})
    assert response.status_code == 303
    assert "error=duplicate" in response.headers["location"]


def test_duplicate_error_visible(browser_client):
    browser_client.post("/projects", data={"name": "Twice"})
    browser_client.post("/projects", data={"name": "Twice"})
    response = browser_client.get("/?error=duplicate")
    assert response.status_code == 200
    assert "already exists" in response.text


def test_create_project_invalid_name(client):
    response = client.post("/projects", data={"name": "   "})
    assert response.status_code == 303
    assert "error=invalid_name" in response.headers["location"]


def test_arabic_name_with_explicit_id(client):
    response = client.post(
        "/projects",
        data={"name": "نظام الطلبات", "project_id": "orders-ar"},
    )
    assert response.status_code == 303
    config = main_module.PROJECTS_DIR / "orders-ar" / "project.yaml"
    assert config.exists()
    assert "نظام الطلبات" in config.read_text(encoding="utf-8")


def test_arabic_name_without_id_returns_error(client):
    response = client.post("/projects", data={"name": "نظام الطلبات"})
    assert response.status_code == 303
    assert "error=missing_id" in response.headers["location"]


def test_arabic_name_without_id_error_visible(browser_client):
    browser_client.post("/projects", data={"name": "مشروع جديد"})
    response = browser_client.get("/?error=missing_id")
    assert response.status_code == 200
    assert "lowercase letters, numbers, and hyphens" in response.text


def test_path_traversal_id_rejected(client):
    response = client.post("/projects", data={"name": "Escape", "project_id": "../x"})
    assert response.status_code == 303
    assert "error=invalid_id" in response.headers["location"]
    assert not (main_module.PROJECTS_DIR.parent / "x").exists()


def test_invalid_yaml_shows_error_state(client, browser_client):
    directory = main_module.PROJECTS_DIR / "broken"
    directory.mkdir()
    (directory / "project.yaml").write_text(
        "schema_version: 1\nname: Broken\n  id: [unclosed{",
        encoding="utf-8",
    )
    response = browser_client.get("/")
    assert response.status_code == 200
    assert "data/projects/broken/project.yaml" in response.text
    assert "error-state" in response.text


def test_invalid_manifest_shows_error_state(client, browser_client):
    directory = main_module.PROJECTS_DIR / "bad-id"
    directory.mkdir()
    (directory / "project.yaml").write_text(
        "schema_version: 1\nid: Bad_ID\nname: Bad\n",
        encoding="utf-8",
    )
    response = browser_client.get("/")
    assert response.status_code == 200
    assert "error-state" in response.text
    assert "data/projects/bad-id/project.yaml" in response.text


def test_stats_are_computed(client, browser_client):
    client.post(
        "/projects",
        data={"name": "Alpha", "stack": "Python"},
    )
    directory = main_module.PROJECTS_DIR / "broken"
    directory.mkdir()
    (directory / "project.yaml").write_text("[{", encoding="utf-8")
    manifest_dir = main_module.PROJECTS_DIR / "bravo"
    manifest_dir.mkdir()
    (manifest_dir / "project.yaml").write_text(
        "schema_version: 1\nid: bravo\nname: Bravo\n"
        "ai_roles:\n"
        "  planning:\n    enabled: true\n    model: demo\n"
        "  execution:\n    enabled: true\n    model: demo\n",
        encoding="utf-8",
    )
    html = browser_client.get("/").text
    assert "<strong>2</strong>" in html  # registered: alpha + bravo
    assert "<strong>1</strong>" in html  # config errors: broken
    assert "<strong>2</strong>" in html  # ai roles enabled: planning + execution
    assert "Pending reviews" not in html


def test_principles_not_set_when_null(client, browser_client):
    client.post("/projects", data={"name": "Gamma"})
    html = browser_client.get("/").text
    assert "Not set" in html


def test_approval_flag_false_without_waiver_is_invalid(browser_client):
    manifest = {
        "schema_version": 1,
        "id": "no-gate",
        "name": "No gate",
        "approval_policy": {"human_approval_required_for_merge": False},
    }
    with pytest.raises(ValidationError):
        Manifest.model_validate(manifest)
    # and it shows as an error record on the dashboard, not a loaded project
    directory = main_module.PROJECTS_DIR / "no-gate"
    directory.mkdir()
    (directory / "project.yaml").write_text(
        "schema_version: 1\nid: no-gate\nname: No gate\n"
        "approval_policy:\n  human_approval_required_for_merge: false\n",
        encoding="utf-8",
    )
    html = browser_client.get("/").text
    assert "waiver" in html


def test_approval_flag_false_with_accepted_waiver_is_valid():
    manifest = Manifest.model_validate(
        {
            "schema_version": 1,
            "id": "waived",
            "name": "Waived",
            "approval_policy": {
                "human_approval_required_for_merge": False,
                "waiver_adr": "0002",
            },
        }
    )
    assert manifest.approval_policy.human_approval_required_for_merge is False


def test_manifest_id_pattern_rejects_traversal():
    with pytest.raises(ValidationError):
        Manifest.model_validate({"schema_version": 1, "id": "../x", "name": "x"})

"""Web app tests: pages render, forms work, and numbers come from real data."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

import factory.main as main_module
import factory.store as store
from factory.manifest import Manifest


def _demo_request(client, title="Add a greeting"):
    client.post("/demo")
    response = client.post(
        "/projects/demo-shop/requests",
        data={"title": title, "kind": "feature", "description": "Please add it."},
    )
    return response.headers["location"].rsplit("/", 1)[-1]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "private-software-factory"}


def test_today_empty(web):
    response = web.get("/")
    assert response.status_code == 200
    assert "Nothing needs you" in response.text
    assert "Choose how models answer" in response.text


def test_projects_page_empty(web):
    response = web.get("/projects")
    assert response.status_code == 200
    assert "No projects yet" in response.text


def test_create_project_valid(client):
    response = client.post(
        "/projects",
        data={
            "name": "Order System",
            "description": "Sells things.",
            "stack": "Python",
        },
    )
    assert response.status_code == 303
    config = main_module.PROJECTS_DIR / "order-system" / "project.yaml"
    assert config.exists()
    text = config.read_text(encoding="utf-8")
    assert "human_approval_required_for_merge: true" in text
    assert "human_approval_required_for_production: true" in text
    assert (main_module.PROJECTS_DIR / "order-system" / "repo" / ".git").exists()
    principles = main_module.PROJECTS_DIR / "order-system" / "principles"
    assert (principles / "security.md").exists()


def test_create_project_duplicate(client):
    client.post("/projects", data={"name": "Same"})
    response = client.post("/projects", data={"name": "Same"})
    assert response.status_code == 303
    assert "error=duplicate" in response.headers["location"]


def test_create_project_invalid_name(client):
    response = client.post("/projects", data={"name": "   "})
    assert response.status_code == 303
    assert "error=invalid_name" in response.headers["location"]


def test_arabic_name_with_explicit_id(client):
    response = client.post(
        "/projects", data={"name": "نظام الطلبات", "project_id": "orders-ar"}
    )
    assert response.status_code == 303
    config = main_module.PROJECTS_DIR / "orders-ar" / "project.yaml"
    assert config.exists()
    assert "نظام الطلبات" in config.read_text(encoding="utf-8")


def test_arabic_name_without_id_returns_error(client):
    response = client.post("/projects", data={"name": "نظام الطلبات"})
    assert response.status_code == 303
    assert "error=missing_id" in response.headers["location"]


def test_path_traversal_id_rejected(client):
    response = client.post("/projects", data={"name": "Escape", "project_id": "../x"})
    assert response.status_code == 303
    assert "error=invalid_id" in response.headers["location"]
    assert not (main_module.PROJECTS_DIR.parent / "x").exists()


def test_create_demo_project(client):
    response = client.post("/demo")
    assert response.status_code == 303
    assert response.headers["location"] == "/projects/demo-shop"
    assert store.project_yaml("demo-shop").exists()
    assert (store.repo_dir("demo-shop") / ".git").exists()


def test_today_lists_computed(web):
    web.post("/demo")
    web.post(
        "/projects/demo-shop/requests",
        data={"title": "Add a greeting", "kind": "feature", "description": "hi"},
    )
    html = web.get("/").text
    assert "1 thing needs you" in html
    assert "Add a greeting" in html
    assert "Needs your approval" in html


def test_request_page_reaches_approval(web):
    web.post("/demo")
    change_id = web.post(
        "/projects/demo-shop/requests",
        data={"title": "Add a greeting", "kind": "feature", "description": "hi"},
    ).url.path.rsplit("/", 1)[-1]
    change = store.load_change("demo-shop", change_id)
    assert change["state"] == "awaiting_approval"
    page = web.get(f"/projects/demo-shop/requests/{change_id}")
    assert page.status_code == 200
    assert "Approve merge" in page.text
    assert "notes/" in page.text


def test_status_json(web):
    web.post("/demo")
    change_id = web.post(
        "/projects/demo-shop/requests",
        data={"title": "Add a greeting", "kind": "feature", "description": "hi"},
    ).url.path.rsplit("/", 1)[-1]
    data = web.get(f"/projects/demo-shop/requests/{change_id}/status.json").json()
    assert data["state"] == "awaiting_approval"
    assert data["kind"] == "need"


def test_all_pages_return_200(web):
    for path in ("/", "/projects", "/models", "/guide"):
        assert web.get(path).status_code == 200
    web.post("/demo")
    assert web.get("/projects/demo-shop").status_code == 200


def test_project_settings_saved(client):
    client.post("/projects", data={"name": "Shop"})
    response = client.post(
        "/projects/shop/settings",
        data={
            "name": "Shop",
            "description": "Sells",
            "stack": "Python",
            "repo_path": "",
            "checks_text": "tests: python -m pytest",
            "dev_command": "echo dev",
            "prod_command": "echo prod",
        },
    )
    assert response.status_code == 303
    manifest = store.read_yaml(store.project_yaml("shop"))
    assert manifest["checks"] == [{"name": "tests", "command": "python -m pytest"}]
    assert manifest["environments"]["prod"]["command"] == "echo prod"


def test_models_role_saved(client):
    client.post(
        "/models/roles/planning",
        data={"provider": "ollama", "model": "llama3"},
    )
    settings = store.load_settings()
    assert settings["planning_provider"] == "ollama"
    assert settings["planning_model"] == "llama3"


def test_local_model_settings_saved(client):
    client.post(
        "/models",
        data={"ollama_url": "http://localhost:1234", "model_timeout_seconds": "60"},
    )
    settings = store.load_settings()
    assert settings["ollama_url"] == "http://localhost:1234"
    assert settings["model_timeout_seconds"] == 60


def test_guide_page(web):
    english = web.get("/guide")
    assert english.status_code == 200
    assert "Guide" in english.text
    arabic = web.get("/guide?lang=ar")
    assert arabic.status_code == 200


def test_missing_project_redirects(client):
    response = client.get("/projects/does-not-exist")
    assert response.status_code == 303
    assert "error=invalid_id" in response.headers["location"]


def test_approval_flag_false_without_waiver_is_invalid():
    manifest = {
        "schema_version": 1,
        "id": "no-gate",
        "name": "No gate",
        "approval_policy": {"human_approval_required_for_merge": False},
    }
    with pytest.raises(ValidationError):
        Manifest.model_validate(manifest)


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


def test_registered_project_with_invalid_manifest_is_not_a_record(data_root):
    directory = main_module.PROJECTS_DIR / "bad-id"
    directory.mkdir()
    (directory / "project.yaml").write_text(
        "schema_version: 1\nid: Bad_ID\nname: Bad\n", encoding="utf-8"
    )
    records = main_module.load_project_records()
    assert len(records) == 1
    assert records[0]["manifest"] is None
    assert records[0]["error"]

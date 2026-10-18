"""Store tests: atomic file writes, the change store, the audit log, and principles."""

from __future__ import annotations

from factory import store


def test_settings_defaults_and_save(data_root):
    settings = store.load_settings()
    assert settings["ollama_url"].startswith("http://127.0.0.1")
    settings["ollama_url"] = "http://example:1"
    store.save_settings(settings)
    assert store.load_settings()["ollama_url"] == "http://example:1"


def test_change_store_round_trip(data_root):
    assert store.next_change_id("demo") == "c-0001"
    store.save_change("demo", "c-0001", {"id": "c-0001", "state": "draft"})
    store.write_artifact("demo", "c-0001", "request.md", "hello")
    assert store.load_change("demo", "c-0001")["state"] == "draft"
    assert store.read_artifact("demo", "c-0001", "request.md") == "hello"
    assert store.artifact_exists("demo", "c-0001", "request.md")
    assert store.next_change_id("demo") == "c-0002"
    assert [c["id"] for c in store.list_changes("demo")] == ["c-0001"]


def test_audit_append(data_root):
    store.append_audit("demo", {"change": "c-0001", "to": "draft", "actor": "owner"})
    store.append_audit("demo", {"change": "c-0002", "to": "draft", "actor": "owner"})
    events = store.read_audit("demo", "c-0001")
    assert len(events) == 1
    assert events[0]["to"] == "draft"
    assert events[0]["time"]
    assert len(store.read_audit("demo")) == 2


def test_registry_lists_projects(data_root):
    (store.PROJECTS_DIR / "alpha").mkdir()
    store.write_yaml_atomic(
        store.project_yaml("alpha"),
        {"schema_version": 1, "id": "alpha", "name": "Alpha"},
    )
    assert store.list_project_ids() == ["alpha"]


def test_starter_principles_written(data_root):
    store.write_starter_principles("p1")
    for category in store.PRINCIPLE_CATEGORIES:
        assert (store.principles_dir("p1") / f"{category}.md").exists()
    store.write_shared_principles()
    for category in store.SHARED_PRINCIPLE_CATEGORIES:
        assert (store.SHARED_PRINCIPLES_DIR / f"{category}.md").exists()

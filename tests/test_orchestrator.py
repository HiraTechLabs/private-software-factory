"""Orchestrator and approvals tests: full flow, failures, restart recovery, retry."""

from __future__ import annotations

from factory import approvals, demo, orchestrator, store


def _draft(project_id, change_id="c-0001", **extra):
    now = store.utc_now()
    change = {
        "id": change_id,
        "project": project_id,
        "title": "Add a greeting",
        "kind": "feature",
        "description": "please add it",
        "state": "draft",
        "attempt": 0,
        "created": now,
        "updated": now,
    }
    change.update(extra)
    store.save_change(project_id, change_id, change)
    store.write_artifact(project_id, change_id, "request.md", "# Add a greeting\n")
    return change


def _edit_manifest(project_id, mutate):
    data = store.read_yaml(store.project_yaml(project_id))
    mutate(data)
    store.write_yaml_atomic(store.project_yaml(project_id), data)


def _state(project_id, change_id="c-0001"):
    return store.load_change(project_id, change_id)["state"]


def test_happy_path_demo(data_root):
    demo.create_demo_project()
    _draft("demo-shop")
    orchestrator.start("demo-shop", "c-0001")
    assert _state("demo-shop") == "awaiting_approval"

    ok, _ = approvals.approve_merge("demo-shop", "c-0001")
    assert ok
    assert _state("demo-shop") == "awaiting_prod"

    ok, _ = approvals.approve_production("demo-shop", "c-0001")
    assert ok
    assert _state("demo-shop") == "live"
    assert (store.repo_dir("demo-shop") / "notes" / "c-0001.md").exists()


def test_production_is_refused_before_production_approval(data_root):
    demo.create_demo_project()
    _draft("demo-shop")
    orchestrator.start("demo-shop", "c-0001")
    assert _state("demo-shop") == "awaiting_approval"
    ok, message = approvals.approve_production("demo-shop", "c-0001")
    assert ok is False
    assert "production" in message
    assert _state("demo-shop") == "awaiting_approval"


def test_approval_refused_in_wrong_state(data_root):
    demo.create_demo_project()
    _draft("demo-shop")
    ok, message = approvals.approve_merge("demo-shop", "c-0001")
    assert ok is False
    assert message
    assert _state("demo-shop") == "draft"


def test_restart_recovery_marks_interrupted(data_root):
    demo.create_demo_project()
    _draft("demo-shop", state="checking")
    interrupted = orchestrator.recover_on_start()
    assert interrupted == ["demo-shop/c-0001"]
    change = store.load_change("demo-shop", "c-0001")
    assert change["state"] == "interrupted"
    assert change["resume_state"] == "checking"
    assert "restarted" in change["interrupt_reason"]


def test_send_back_note_reaches_prompt(data_root):
    demo.create_demo_project()
    _draft("demo-shop")
    orchestrator.start("demo-shop", "c-0001")
    assert _state("demo-shop") == "awaiting_approval"

    def make_execution_manual(data):
        data["ai_roles"]["execution"] = {
            "enabled": True,
            "provider": "manual",
            "model": "",
        }

    _edit_manifest("demo-shop", make_execution_manual)
    ok, _ = approvals.send_back("demo-shop", "c-0001", "Please rename the notes file")
    assert ok
    assert _state("demo-shop") == "waiting_for_you"
    prompt = store.read_artifact("demo-shop", "c-0001", "prompt-build.md")
    assert "Please rename the notes file" in prompt


def test_checks_fail_then_failed(data_root):
    demo.create_demo_project()
    _edit_manifest(
        "demo-shop",
        lambda data: data.update(
            {"checks": [{"name": "always fails", "command": "exit 1"}]}
        ),
    )
    _draft("demo-shop")
    orchestrator.start("demo-shop", "c-0001")
    change = store.load_change("demo-shop", "c-0001")
    assert change["state"] == "failed"
    assert change["attempt"] == 2
    assert "checks failed" in change["failure_reason"]


def test_dirty_repo_blocks_build_then_retry_succeeds(data_root):
    demo.create_demo_project()
    (store.repo_dir("demo-shop") / "loose.txt").write_text("x", encoding="utf-8")
    _draft("demo-shop")
    orchestrator.start("demo-shop", "c-0001")
    change = store.load_change("demo-shop", "c-0001")
    assert change["state"] == "blocked"
    assert "uncommitted" in change["failure_reason"]

    (store.repo_dir("demo-shop") / "loose.txt").unlink()
    ok, _ = approvals.retry("demo-shop", "c-0001")
    assert ok
    assert _state("demo-shop") == "awaiting_approval"


def test_production_deploy_failure(data_root):
    demo.create_demo_project()
    _edit_manifest(
        "demo-shop",
        lambda data: data["environments"].__setitem__("prod", {"command": "exit 3"}),
    )
    _draft("demo-shop")
    orchestrator.start("demo-shop", "c-0001")
    approvals.approve_merge("demo-shop", "c-0001")
    assert _state("demo-shop") == "awaiting_prod"
    approvals.approve_production("demo-shop", "c-0001")
    change = store.load_change("demo-shop", "c-0001")
    assert change["state"] == "failed"
    assert "production deploy failed" in change["failure_reason"]


def test_cancel_stops_a_request(data_root):
    demo.create_demo_project()
    _draft("demo-shop")
    orchestrator.start("demo-shop", "c-0001")
    ok, _ = approvals.cancel("demo-shop", "c-0001")
    assert ok
    assert _state("demo-shop") == "cancelled"
    again, message = approvals.cancel("demo-shop", "c-0001")
    assert again is False
    assert "already finished" in message

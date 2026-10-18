"""Background runner: executes steps, saves state, and stops at every human approval.

The orchestrator is the only writer of change state besides `approvals`; both pass
through `flow.py`'s legal transitions (ADR 0013). Set `orchestrator.SYNC = True` to
run inline (tests).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from factory import (
    check_runner,
    context_builder,
    deployer,
    flow,
    git_ops,
    patch_applier,
    store,
)
from factory.manifest import Manifest, validate_manifest
from factory.models import gateway

SYNC = False
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()

MODEL_STEP_ROLE = {"plan": "planning", "build": "execution", "review": "review"}
OUTPUT_ARTIFACT = {
    "plan": "plan.md",
    "build": "build-answer.txt",
    "review": "review.md",
}


def _lock_for(project_id: str) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(project_id, threading.Lock())


def start(project_id: str, change_id: str) -> None:
    if SYNC:
        advance(project_id, change_id)
        return
    threading.Thread(target=advance, args=(project_id, change_id), daemon=True).start()


def advance(project_id: str, change_id: str) -> None:
    with _lock_for(project_id):
        _advance(project_id, change_id)


def load_manifest(project_id: str) -> Manifest | None:
    data = store.read_yaml(store.project_yaml(project_id))
    if data is None:
        return None
    manifest = validate_manifest(data)
    return manifest if isinstance(manifest, Manifest) else None


def repo_path_for(project_id: str, manifest: Manifest) -> Path:
    if manifest.repo_path:
        return Path(manifest.repo_path)
    return store.repo_dir(project_id)


def recover_on_start() -> list[str]:
    """A change in a running state when the app restarts becomes `interrupted`."""
    interrupted: list[str] = []
    for change in store.all_changes():
        if flow.is_running(change.get("state", "")):
            _interrupt(change["project"], change["id"], change)
            interrupted.append(f"{change['project']}/{change['id']}")
    return interrupted


def _interrupt(project_id: str, change_id: str, change: dict) -> None:
    previous = change.get("state")
    change["state"] = "interrupted"
    change["interrupt_reason"] = "The Factory restarted while this step was running"
    change["resume_state"] = previous
    change["updated"] = store.utc_now()
    store.save_change(project_id, change_id, change)
    store.append_audit(
        project_id,
        {
            "change": change_id,
            "actor": "machine",
            "from": previous,
            "to": "interrupted",
            "note": change["interrupt_reason"],
        },
    )


def _set_state(
    project_id: str,
    change_id: str,
    change: dict,
    target: str,
    actor: str,
    note: str = "",
) -> None:
    current = change.get("state")
    flow.assert_move(current, target)
    change["state"] = target
    change["updated"] = store.utc_now()
    store.save_change(project_id, change_id, change)
    store.append_audit(
        project_id,
        {
            "change": change_id,
            "actor": actor,
            "from": current,
            "to": target,
            "note": note,
        },
    )


def _fail(
    project_id: str, change_id: str, change: dict, reason: str, target: str = "failed"
) -> str:
    change["failure_reason"] = reason
    try:
        _set_state(project_id, change_id, change, target, "machine", reason)
    except ValueError:
        pass
    return "stop"


def _advance(project_id: str, change_id: str) -> None:
    while True:
        change = store.load_change(project_id, change_id)
        if change is None:
            return
        state = change.get("state")
        if state in flow.TERMINAL_STATES or state in {
            "failed",
            "blocked",
            "interrupted",
            "waiting_for_you",
        }:
            return
        manifest = load_manifest(project_id)
        if manifest is None:
            _fail(project_id, change_id, change, "the project manifest is invalid")
            return

        if state == "draft":
            if _plan_step(project_id, change_id, manifest, change) == "stop":
                return
        elif state == "planned":
            if _build_step(project_id, change_id, manifest, change) == "stop":
                return
        elif state == "checking":
            if _checks_step(project_id, change_id, manifest, change) == "stop":
                return
        elif state == "in_review":
            if _review_step(project_id, change_id, manifest, change) == "stop":
                return
        elif state == "awaiting_approval":
            if not change.get("approved_merge"):
                return
            if _merge_step(project_id, change_id, manifest, change) == "stop":
                return
        elif state == "merged":
            if _dev_step(project_id, change_id, manifest, change) == "stop":
                return
        elif state == "deployed_dev":
            _set_state(
                project_id,
                change_id,
                change,
                "awaiting_prod",
                "machine",
                "dev is done; waiting for your production approval",
            )
        elif state == "awaiting_prod":
            if not change.get("approved_prod"):
                return
            if _production_step(project_id, change_id, manifest, change) == "stop":
                return
        else:
            return


# ------------------------------------------------------------------ prompt helper
def _ask_role(
    project_id: str,
    change_id: str,
    manifest: Manifest,
    change: dict,
    step: str,
    repo: Path,
):
    role = MODEL_STEP_ROLE[step]
    provider = manifest.role_provider(role)
    model = manifest.role_model(role)
    prompt, sources = context_builder.build_prompt(
        project_id,
        repo,
        manifest.records.model_dump(),
        change,
        step,
        change.get("owner_note", ""),
    )
    context_builder.write_context_files(project_id, change_id, step, prompt, sources)
    existing = None
    if provider == "manual":
        existing = store.read_artifact(project_id, change_id, f"{step}-answer.txt")
    answer = gateway.ask(
        step,
        prompt,
        provider=provider,
        model=model,
        settings=store.load_settings(),
        existing_answer=existing,
        demo_context={
            "request_title": change.get("title", ""),
            "request_text": change.get("description", ""),
            "change_id": change_id,
        },
    )
    return answer, prompt


def _wait_for_answer(
    project_id: str, change_id: str, change: dict, step: str, waiting_from: str
) -> str:
    change["pending_step"] = step
    change["waiting_from"] = waiting_from
    _set_state(
        project_id,
        change_id,
        change,
        "waiting_for_you",
        "machine",
        f"the {step} step needs your pasted answer",
    )
    return "stop"


# ------------------------------------------------------------------ plan / review
def _plan_step(
    project_id: str, change_id: str, manifest: Manifest, change: dict
) -> str:
    _set_state(project_id, change_id, change, "planning", "machine", "planning started")
    repo = repo_path_for(project_id, manifest)
    try:
        answer, _prompt = _ask_role(
            project_id, change_id, manifest, change, "plan", repo
        )
    except gateway.ManualAnswerRequired:
        return _wait_for_answer(project_id, change_id, change, "plan", "draft")
    except Exception as exc:
        return _fail(project_id, change_id, change, f"the plan step failed: {exc}")
    store.write_artifact(project_id, change_id, "plan.md", answer.text)
    change["plan"] = answer.text
    _set_state(project_id, change_id, change, "planned", "model", "the plan is ready")
    return "continue"


def _review_step(
    project_id: str, change_id: str, manifest: Manifest, change: dict
) -> str:
    repo = repo_path_for(project_id, manifest)
    try:
        answer, _prompt = _ask_role(
            project_id, change_id, manifest, change, "review", repo
        )
    except gateway.ManualAnswerRequired:
        return _wait_for_answer(project_id, change_id, change, "review", "in_review")
    except Exception as exc:
        return _fail(project_id, change_id, change, f"the review step failed: {exc}")
    store.write_artifact(project_id, change_id, "review.md", answer.text)
    verdict = _parse_verdict(answer.text)
    change["review_verdict"] = verdict
    _set_state(
        project_id,
        change_id,
        change,
        "awaiting_approval",
        "model",
        f"the review verdict is {verdict}",
    )
    return "continue"


def _parse_verdict(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().upper()
        if stripped.startswith("VERDICT:"):
            value = stripped.split(":", 1)[1].strip()
            if value.startswith("APPROVE"):
                return "approve"
            if value.startswith("CHANGES"):
                return "changes"
    return "changes"


# ------------------------------------------------------------------ build
def _build_step(
    project_id: str, change_id: str, manifest: Manifest, change: dict
) -> str:
    repo = repo_path_for(project_id, manifest)
    if not git_ops.is_repo(repo):
        return _fail(
            project_id,
            change_id,
            change,
            "the project has no git repository to build in",
            "blocked",
        )
    if git_ops.has_uncommitted(repo):
        return _fail(
            project_id,
            change_id,
            change,
            "the repository has uncommitted changes; commit or stash them first",
            "blocked",
        )
    _set_state(
        project_id, change_id, change, "implementing", "machine", "build started"
    )
    worktree = store.work_dir(project_id, change_id)
    if not worktree.exists():
        result = git_ops.add_worktree(
            repo, worktree, f"change/{change_id}", manifest.default_branch
        )
        if not result.ok:
            return _fail(
                project_id,
                change_id,
                change,
                f"could not create the change worktree: {result.output}",
                "blocked",
            )
    try:
        answer, prompt = _ask_role(
            project_id, change_id, manifest, change, "build", worktree
        )
    except gateway.ManualAnswerRequired:
        return _wait_for_answer(project_id, change_id, change, "build", "planned")
    except Exception as exc:
        return _fail(project_id, change_id, change, f"the build step failed: {exc}")
    store.write_artifact(project_id, change_id, "build-answer.txt", answer.text)
    store.write_artifact(project_id, change_id, "prompt-build.md", prompt)
    try:
        written, _commit = patch_applier.apply(
            answer.text,
            worktree,
            manifest.protected_paths,
            manifest.limits.model_dump(),
            message=f"{change.get('title', change_id)} ({change_id})",
        )
    except patch_applier.PatchError as exc:
        return _fail(project_id, change_id, change, f"the build was rejected: {exc}")
    change["files_changed"] = written
    change["diff"] = git_ops.diff_against(worktree, manifest.default_branch)[:20000]
    store.write_artifact(project_id, change_id, "diff.patch", change["diff"])
    _set_state(
        project_id,
        change_id,
        change,
        "checking",
        "model",
        f"the build wrote {len(written)} file(s)",
    )
    return "continue"


# ------------------------------------------------------------------ checks
def _checks_step(
    project_id: str, change_id: str, manifest: Manifest, change: dict
) -> str:
    worktree = store.work_dir(project_id, change_id)
    commands = [check.model_dump() for check in manifest.checks]
    if not commands:
        note = "No checks are configured for this project."
        store.write_artifact(
            project_id,
            change_id,
            "checks.json",
            json.dumps({"checks": [], "passed": True, "note": note}, indent=2),
        )
        store.write_artifact(project_id, change_id, "checks.log", note + "\n")
        change["checks_log"] = note
        change["checks_summary"] = note
        _set_state(project_id, change_id, change, "in_review", "machine", note)
        return "continue"
    timeout = int(store.load_settings().get("check_timeout_seconds", 600))
    data = check_runner.run_checks(commands, worktree, timeout=timeout)
    store.write_artifact(
        project_id, change_id, "checks.json", json.dumps(data, indent=2)
    )
    store.write_artifact(project_id, change_id, "checks.log", data["log"])
    change["checks_log"] = data["log"]
    change["checks_summary"] = check_runner.summary(data)
    if data["passed"]:
        _set_state(
            project_id,
            change_id,
            change,
            "in_review",
            "machine",
            check_runner.summary(data),
        )
        return "continue"
    attempt = int(change.get("attempt", 0)) + 1
    change["attempt"] = attempt
    if attempt < int(manifest.limits.max_attempts):
        _set_state(
            project_id,
            change_id,
            change,
            "planned",
            "machine",
            f"checks failed (attempt {attempt}); building again",
        )
        return "continue"
    return _fail(
        project_id, change_id, change, f"checks failed after {attempt} attempt(s)"
    )


# ------------------------------------------------------------------ merge / dev
def _merge_step(
    project_id: str, change_id: str, manifest: Manifest, change: dict
) -> str:
    repo = repo_path_for(project_id, manifest)
    result = git_ops.merge_no_ff(repo, f"change/{change_id}")
    if not result.ok:
        return _fail(
            project_id,
            change_id,
            change,
            f"the merge hit a conflict: {result.output}",
            "blocked",
        )
    git_ops.remove_worktree(repo, store.work_dir(project_id, change_id))
    git_ops.delete_branch(repo, f"change/{change_id}")
    _set_state(
        project_id,
        change_id,
        change,
        "merged",
        "machine",
        "merged into " + manifest.default_branch,
    )
    return "continue"


def _dev_step(project_id: str, change_id: str, manifest: Manifest, change: dict) -> str:
    repo = repo_path_for(project_id, manifest)
    outcome = deployer.deploy(
        project_id,
        change_id,
        "dev",
        manifest.environments.dev.command,
        repo,
        int(store.load_settings().get("deploy_timeout_seconds", 600)),
    )
    if outcome["configured"] and outcome["exit_code"] != 0:
        return _fail(
            project_id,
            change_id,
            change,
            f"the dev deploy failed (exit {outcome['exit_code']})",
        )
    note = (
        "deployed to dev"
        if outcome["configured"]
        else "no dev command is set, so this step was skipped"
    )
    _set_state(project_id, change_id, change, "deployed_dev", "machine", note)
    return "continue"


def _production_step(
    project_id: str, change_id: str, manifest: Manifest, change: dict
) -> str:
    repo = repo_path_for(project_id, manifest)
    outcome = deployer.deploy(
        project_id,
        change_id,
        "prod",
        manifest.environments.prod.command,
        repo,
        int(store.load_settings().get("deploy_timeout_seconds", 600)),
    )
    if outcome["configured"] and outcome["exit_code"] != 0:
        return _fail(
            project_id,
            change_id,
            change,
            f"the production deploy failed (exit {outcome['exit_code']})",
        )
    note = (
        "live"
        if outcome["configured"]
        else "no production command is set, so this step was skipped; it is live"
    )
    _set_state(project_id, change_id, change, "live", "machine", note)
    return "stop"

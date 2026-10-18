"""The only place an approval is accepted, and only from a human click (ADR 0013)."""

from __future__ import annotations

from factory import flow, orchestrator, store


def _move(
    project_id: str, change_id: str, change: dict, target: str, note: str
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
            "actor": "owner",
            "from": current,
            "to": target,
            "note": note,
        },
    )


def approve_merge(project_id: str, change_id: str) -> tuple[bool, str]:
    change = store.load_change(project_id, change_id)
    if change is None:
        return False, "This request does not exist."
    if change.get("state") != "awaiting_approval":
        return False, "This request is not waiting for merge approval right now."
    change["approved_merge"] = True
    change["merge_decision"] = {"by": "owner", "at": store.utc_now()}
    store.save_change(project_id, change_id, change)
    store.append_audit(
        project_id,
        {
            "change": change_id,
            "actor": "owner",
            "from": "awaiting_approval",
            "to": "awaiting_approval",
            "note": "approved the merge",
        },
    )
    orchestrator.start(project_id, change_id)
    return True, "Approved. The change is merging and going to dev."


def approve_production(project_id: str, change_id: str) -> tuple[bool, str]:
    change = store.load_change(project_id, change_id)
    if change is None:
        return False, "This request does not exist."
    if change.get("state") != "awaiting_prod":
        return False, "This request is not waiting for production approval right now."
    change["approved_prod"] = True
    change["prod_decision"] = {"by": "owner", "at": store.utc_now()}
    store.save_change(project_id, change_id, change)
    store.append_audit(
        project_id,
        {
            "change": change_id,
            "actor": "owner",
            "from": "awaiting_prod",
            "to": "awaiting_prod",
            "note": "approved production",
        },
    )
    orchestrator.start(project_id, change_id)
    return True, "Approved. The change is going to production."


def send_back(project_id: str, change_id: str, note: str) -> tuple[bool, str]:
    note = (note or "").strip()
    if not note:
        return False, "Write a note so the model knows what to change."
    change = store.load_change(project_id, change_id)
    if change is None:
        return False, "This request does not exist."
    if change.get("state") != "awaiting_approval":
        return False, (
            "You can only send back a request that is waiting for merge approval."
        )
    change["owner_note"] = note
    change["approved_merge"] = False
    store.delete_artifact(project_id, change_id, "build-answer.txt")
    _move(project_id, change_id, change, "planned", "sent back with a note")
    orchestrator.start(project_id, change_id)
    return True, "Sent back to build with your note."


def cancel(project_id: str, change_id: str) -> tuple[bool, str]:
    change = store.load_change(project_id, change_id)
    if change is None:
        return False, "This request does not exist."
    if change.get("state") in flow.TERMINAL_STATES:
        return False, "This request is already finished."
    _move(project_id, change_id, change, "cancelled", "cancelled by the owner")
    return True, "Request cancelled."


def retry(project_id: str, change_id: str) -> tuple[bool, str]:
    change = store.load_change(project_id, change_id)
    if change is None:
        return False, "This request does not exist."
    state = change.get("state")
    if state not in {"failed", "interrupted", "blocked"}:
        return False, "This request is not stopped, so there is nothing to retry."
    resume = change.get("resume_state") or "planned"
    target = flow.RUNNING_TO_SETTLED.get(resume, resume)
    if not flow.can_move(state, target):
        target = "planned"
    change["failure_reason"] = ""
    _move(project_id, change_id, change, target, "trying this step again")
    orchestrator.start(project_id, change_id)
    return True, "Trying this step again."


def submit_answer(project_id: str, change_id: str, text: str) -> tuple[bool, str]:
    text = (text or "").strip()
    if not text:
        return False, "Paste the model's answer before submitting."
    change = store.load_change(project_id, change_id)
    if change is None:
        return False, "This request does not exist."
    if change.get("state") != "waiting_for_you":
        return False, "This request is not waiting for a pasted answer."
    step = change.get("pending_step") or "plan"
    target = change.get("waiting_from") or "planned"
    store.write_artifact(project_id, change_id, f"{step}-answer.txt", text)
    change.pop("pending_step", None)
    change.pop("waiting_from", None)
    if not flow.can_move("waiting_for_you", target):
        target = "planned"
    _move(project_id, change_id, change, target, f"pasted the {step} answer")
    orchestrator.start(project_id, change_id)
    return True, "Answer submitted."

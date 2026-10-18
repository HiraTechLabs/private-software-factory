"""Run the dev or production deploy command after the matching approval (ADR 0011)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from factory import store


def deploy(
    project_id: str,
    change_id: str,
    environment: str,
    command: str,
    repo_path: Path,
    timeout: int = 600,
) -> dict:
    command = (command or "").strip()
    if not command:
        reason = (
            f"No {environment} deploy command is set for this project, so this "
            "step was skipped. Add one in the project settings to deploy here."
        )
        store.write_artifact(
            project_id, change_id, f"deploy-{environment}.log", reason + "\n"
        )
        return {"configured": False, "exit_code": None, "log": reason}
    try:
        completed = subprocess.run(
            command,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=True,
        )
        exit_code = completed.returncode
        log = (completed.stdout + completed.stderr).strip()
    except subprocess.TimeoutExpired:
        exit_code = 124
        log = f"Deploy timed out after {timeout}s."
    log = f"$ {command}\n{log}\n-> exit {exit_code}\n"
    store.write_artifact(project_id, change_id, f"deploy-{environment}.log", log)
    return {"configured": True, "exit_code": exit_code, "log": log}

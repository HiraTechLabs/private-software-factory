"""Run only the commands the project manifest declares, with a timeout (ADR 0011)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_checks(commands: list[dict], cwd: Path, timeout: int = 600) -> dict:
    results: list[dict] = []
    log_lines: list[str] = []
    passed = True
    for item in commands:
        name = str(item.get("name") or "check")
        command = str(item.get("command") or "").strip()
        if not command:
            results.append(
                {
                    "name": name,
                    "command": "",
                    "exit_code": None,
                    "output": "No command was given for this check.",
                }
            )
            passed = False
            log_lines.append(f"$ {name}: (no command)")
            continue
        log_lines.append(f"$ {command}")
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                shell=True,
            )
            exit_code = completed.returncode
            output = (completed.stdout + completed.stderr).strip()
        except subprocess.TimeoutExpired:
            exit_code = 124
            output = f"Timed out after {timeout}s."
        if exit_code != 0:
            passed = False
        results.append(
            {
                "name": name,
                "command": command,
                "exit_code": exit_code,
                "output": output,
            }
        )
        log_lines.append(output)
        log_lines.append(f"-> exit {exit_code}\n")
    return {"checks": results, "passed": passed, "log": "\n".join(log_lines)}


def summary(data: dict) -> str:
    checks = data.get("checks", [])
    if not checks:
        return "No checks are configured for this project."
    passed = sum(1 for check in checks if check.get("exit_code") == 0)
    return f"{passed} of {len(checks)} checks passed."

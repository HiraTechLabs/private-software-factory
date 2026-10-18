"""Check runner tests: pass, fail, timeout, and a missing command."""

from __future__ import annotations

import sys

from factory import check_runner

PY = f'"{sys.executable}"'


def test_run_pass(tmp_path):
    data = check_runner.run_checks(
        [{"name": "ok", "command": f'{PY} -c "print(1)"'}], tmp_path
    )
    assert data["passed"] is True
    assert data["checks"][0]["exit_code"] == 0
    assert check_runner.summary(data) == "1 of 1 checks passed."


def test_run_fail(tmp_path):
    data = check_runner.run_checks(
        [{"name": "bad", "command": f'{PY} -c "import sys; sys.exit(1)"'}], tmp_path
    )
    assert data["passed"] is False
    assert data["checks"][0]["exit_code"] == 1
    assert check_runner.summary(data) == "0 of 1 checks passed."


def test_timeout(tmp_path):
    data = check_runner.run_checks(
        [{"name": "slow", "command": f'{PY} -c "import time; time.sleep(5)"'}],
        tmp_path,
        timeout=1,
    )
    assert data["passed"] is False
    assert data["checks"][0]["exit_code"] == 124
    assert "Timed out" in data["checks"][0]["output"]


def test_missing_command(tmp_path):
    data = check_runner.run_checks([{"name": "empty", "command": ""}], tmp_path)
    assert data["passed"] is False
    assert "No command" in data["checks"][0]["output"]

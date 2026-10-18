"""Run every check in order and stop at the first failure (protected core, ADR 0009).

This is the one command CI and a developer run: `python scripts/check_all.py`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

STEPS: list[tuple[str, list[str]]] = [
    ("ruff check", [PY, "-m", "ruff", "check", "."]),
    ("ruff format", [PY, "-m", "ruff", "format", "--check", "."]),
    ("pytest", [PY, "-m", "pytest", "-q"]),
    ("graph_check", [PY, "scripts/graph_check.py", "--check"]),
    ("ui_lint", [PY, "scripts/ui_lint.py"]),
    ("build_tokens", [PY, "scripts/build_tokens.py", "--check"]),
    ("features_check", [PY, "scripts/features_check.py"]),
    ("smoke", [PY, "scripts/smoke.py"]),
]


def main() -> int:
    for label, command in STEPS:
        result = subprocess.run(command, cwd=str(ROOT))
        ok = result.returncode == 0
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            print("check_all: FAIL (stopped at the first failure)")
            return 1
    print("check_all: PASS (every check)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

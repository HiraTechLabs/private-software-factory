"""Check docs/FEATURES.md against the tests (protected core, ADR 0009).

Fails when a row marked `working` names a test function that does not exist under
tests/. A row marked anything else is not checked, so planned work is honest by default.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "docs" / "FEATURES.md"
TEST_ID = re.compile(r"^(tests/[\w./-]+\.py)::(\w+)$")


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def main() -> int:
    if not FEATURES.exists():
        print("error: docs/FEATURES.md is missing")
        return 1
    errors: list[str] = []
    working = 0
    for number, line in enumerate(FEATURES.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) != 5 or cells[0] in {"id", "----"} or set(cells[0]) <= {"-"}:
            continue
        feature_id, _what, _where, status, test = cells
        if status == "not-built":
            continue
        if status != "working":
            errors.append(
                f"{FEATURES.name}: {number}: status {status!r} must be "
                "'working' or 'not-built'"
            )
            continue
        working += 1
        match = TEST_ID.match(test)
        if not match:
            errors.append(
                f"{FEATURES.name}: {number}: working feature {feature_id!r} needs a "
                "test id like tests/test_x.py::test_name"
            )
            continue
        test_file = ROOT / match.group(1)
        if not test_file.exists():
            errors.append(f"feature {feature_id!r}: {match.group(1)} does not exist")
            continue
        if not re.search(
            rf"^def {match.group(2)}\b",
            test_file.read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            errors.append(
                f"feature {feature_id!r}: {match.group(2)!r} is not in {match.group(1)}"
            )
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print(f"features_check: ok ({working} working)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

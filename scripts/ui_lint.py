"""UI lint (protected core, ADR 0010). Fails on:

- `disabled` attributes and `href="#"` in templates (no dead controls, R10);
- the words "coming soon", "TODO", "lorem" anywhere in UI files;
- any banned iteration-1 term (ADR 0010 section 5.3) in templates/, static/, docs/ui/;
- literal colors (hex, rgb(), hsl()) outside the generated tokens.css;
- physical CSS properties (margin-left, text-align: left, ...) instead of logical ones.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "factory"
TEMPLATES = SRC / "templates"
STATIC = SRC / "static"
DOCS_UI = ROOT / "docs" / "ui"
TOKENS_CSS = STATIC / "tokens.css"

COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")
PHYSICAL_PROPS_RE = re.compile(
    r"\b(margin-left|margin-right|padding-left|padding-right|"
    r"border-left|border-right)\s*:|\btext-align\s*:\s*(left|right)\b"
)
DISABLED_RE = re.compile(r"\bdisabled\b")
HASH_LINK_RE = re.compile(r'href\s*=\s*["\']#["\']')

BANNED_TERMS = [
    r"StateLight",
    r"state-light",
    r"LineRail",
    r"line-rail",
    r"ModeTag",
    r"mode-tag",
    r"EvidenceRow",
    r"evidence-row",
    r"RefChip",
    r"ref-chip",
    r"FilterBar",
    r"filter-bar",
    r"Shadowed",
    r"shadowed",
    r"Registry readiness",
    r"AI roles enabled",
    r"Config errors",
    r"coming soon",
    r"lorem",
    r"\bTODO\b",
    r"\bGate\b",
]
BANNED_RE = [re.compile(term) for term in BANNED_TERMS]


def ui_files() -> list[Path]:
    files: list[Path] = []
    if TEMPLATES.is_dir():
        files.extend(TEMPLATES.rglob("*.html"))
    if STATIC.is_dir():
        files.extend(STATIC.glob("*.css"))
    if DOCS_UI.is_dir():
        files.extend(DOCS_UI.rglob("*.html"))
        files.extend(DOCS_UI.rglob("*.md"))
    return sorted(files)


def check_file(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    is_template = path.suffix == ".html" and TEMPLATES in path.parents
    is_css = path.suffix == ".css"
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern in BANNED_RE:
            if pattern.search(line):
                errors.append(f"{path}: {number}: banned term {pattern.pattern!r}")
        if is_css and path != TOKENS_CSS and COLOR_RE.search(line):
            errors.append(f"{path}: {number}: literal color outside tokens.css")
        if (is_css or is_template) and PHYSICAL_PROPS_RE.search(line):
            errors.append(
                f"{path}: {number}: physical CSS property (use logical properties)"
            )
        if is_template and DISABLED_RE.search(line):
            errors.append(
                f"{path}: {number}: 'disabled' is not allowed (no dead controls)"
            )
        if is_template and HASH_LINK_RE.search(line):
            errors.append(f"{path}: {number}: a hash-only link is not allowed")


def main() -> int:
    errors: list[str] = []
    for path in ui_files():
        check_file(path, errors)
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print("ui_lint: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

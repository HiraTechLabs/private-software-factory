"""UI system lint (protected core, ADR 0005). Fails on:

- literal colors (hex, rgb(), hsl()) in static CSS outside the generated tokens.css;
- raw px values other than 0 and 1px (borders) outside @media queries;
- text-transform: uppercase; non-zero letter-spacing;
- physical CSS properties (margin-left, padding-right, text-align: left|right,
  border-left|right, orphan left/right) instead of logical properties;
- any state label or state-class literal in templates that does not come from
  ui_vocab.py (checked structurally, not by matching rendered text);
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "factory"
TOKENS_CSS = SRC / "static" / "tokens.css"

sys.path.insert(0, str(ROOT / "src"))

from factory import ui_vocab  # noqa: E402

COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\(|hsla\(|rgba\(")
PX_RE = re.compile(r"(?<![\w.-])-?\d*\.?\d+px\b")
UPPERCASE_RE = re.compile(r"text-transform\s*:\s*uppercase")
LETTER_SPACING_RE = re.compile(r"letter-spacing\s*:\s*([^;}\s]+)")
PHYSICAL_PROPS_RE = re.compile(
    r"\b(margin-left|margin-right|padding-left|padding-right|"
    r"border-left|border-right)\b\s*:|\btext-align\s*:\s*(left|right)\b"
    r"|\btext-align\s*:\s*(left|right)\s*[!|]|(?:^|[;{])\s*(left|right)\s*:",
    re.MULTILINE,
)
ENUM_CLASS_RE = re.compile(
    r"(state-light|mode-tag|line-rail__step|gate)--"
    r"(idle|run|hold|stop|shadow|done|manual|live|approved|rejected|waiting)"
)


def banned_labels() -> list[str]:
    labels: list[str] = []
    for mapping in (
        ui_vocab.TASK_STATE_LABELS,
        ui_vocab.MODE_LABELS,
        ui_vocab.READINESS_LABELS,
        ui_vocab.LIGHT_KIND_LABELS,
    ):
        labels.extend(mapping.values())
    return labels


def check_css(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    is_tokens = path == TOKENS_CSS
    for number, line in enumerate(text.splitlines(), start=1):
        if not is_tokens and COLOR_RE.search(line):
            errors.append(f"{path}: {number}: literal color outside tokens.css")
        if is_tokens:
            continue
        if "@" in line and "media" in line:
            continue
        for match in PX_RE.finditer(line):
            if match.group(0) not in {"0px", "1px"}:
                errors.append(
                    f"{path}: {number}: raw px value {match.group(0)!r} "
                    "(use a token; 0 and 1px borders are allowed)"
                )
        if UPPERCASE_RE.search(line):
            errors.append(f"{path}: {number}: text-transform: uppercase is banned")
        spacing = LETTER_SPACING_RE.search(line)
        if spacing and spacing.group(1) not in {"0", "normal"}:
            errors.append(f"{path}: {number}: letter-spacing must be 0 or normal")
        if PHYSICAL_PROPS_RE.search(line):
            errors.append(
                f"{path}: {number}: physical CSS property (use logical properties)"
            )


def check_template(path: Path, forbidden: list[str], errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for label in forbidden:
        if re.search(rf"\b{re.escape(label)}\b", text):
            errors.append(
                f"{path}: state label {label!r} must come from factory.ui_vocab, "
                "not a literal in the template"
            )
    if ENUM_CLASS_RE.search(text):
        errors.append(
            f"{path}: enum state class literal found; build the class from a "
            "ui_vocab value (state-light--{{ kind }}, mode-tag--{{ mode }}, ...)"
        )


def main() -> int:
    errors: list[str] = []
    forbidden = banned_labels()
    for path in sorted(SRC.glob("static/*.css")):
        check_css(path, errors)
    for path in sorted((SRC / "templates").rglob("*.html")):
        check_template(path, forbidden, errors)

    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print("ui_lint: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

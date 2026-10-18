"""Contrast checks for the design tokens (WCAG) — docs/ui/UI_SYSTEM.md, ADR 0010.

Requires 4.5:1 for the text colors (`ink`, `ink-soft`, `accent`) on `card` and
`paper`, 4.5:1 for `accent-ink` on `accent`, and 3:1 for the status colors
(`need`, `work`, `done`, `fail`, `idle`) on `card`, in both themes.
"""

import json
from pathlib import Path

TOKENS = json.loads(
    (Path(__file__).resolve().parents[1] / "design" / "tokens.json").read_text(
        encoding="utf-8"
    )
)["color"]

TEXT_COLORS = ("ink", "ink-soft", "accent")
STATUS_COLORS = ("need", "work", "done", "fail", "idle")


def channel(channel_hex: str) -> float:
    value = int(channel_hex, 16) / 255
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    r, g, b = (channel(color[i : i + 2]) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def test_text_colors_meet_4_5_against_paper_and_card():
    for theme in ("light", "dark"):
        palette = TOKENS[theme]
        for name in TEXT_COLORS:
            for background in ("paper", "card"):
                ratio = contrast_ratio(palette[name], palette[background])
                message = f"{theme}/{name} on {background}: {ratio:.2f} < 4.5"
                assert ratio >= 4.5, message


def test_accent_ink_meets_4_5_on_accent():
    for theme in ("light", "dark"):
        palette = TOKENS[theme]
        ratio = contrast_ratio(palette["accent-ink"], palette["accent"])
        assert ratio >= 4.5, f"{theme}/accent-ink on accent: {ratio:.2f} < 4.5"


def test_status_colors_meet_3_against_card():
    for theme in ("light", "dark"):
        palette = TOKENS[theme]
        for name in STATUS_COLORS:
            ratio = contrast_ratio(palette[name], palette["card"])
            assert ratio >= 3.0, f"{theme}/{name} on card: {ratio:.2f} < 3.0"

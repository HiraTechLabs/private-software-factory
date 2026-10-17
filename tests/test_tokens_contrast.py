"""Contrast checks for the design tokens (WCAG) — docs/ui/UI_SYSTEM.md, ADR 0005.

Requires 4.5:1 for `ink`, `steel`, and the four `*-text` colors against `surface` and
`paper` in both themes, and 3:1 for the six light colors against `surface`.
"""

import json
from pathlib import Path

TOKENS = json.loads(
    (Path(__file__).resolve().parents[1] / "design" / "tokens.json").read_text(
        encoding="utf-8"
    )
)["color"]


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


def test_text_colors_meet_4_5_against_paper_and_surface():
    for theme in ("light", "dark"):
        palette = TOKENS[theme]
        for name in (
            "ink",
            "steel",
            "run-text",
            "hold-text",
            "stop-text",
            "shadow-text",
        ):
            for background in ("paper", "surface"):
                ratio = contrast_ratio(palette[name], palette[background])
                assert ratio >= 4.5, (
                    f"{theme}/{name} on {background}: {ratio:.2f} < 4.5"
                )


def test_light_kinds_meet_3_against_surface():
    for theme in ("light", "dark"):
        palette = TOKENS[theme]
        for name in ("run", "hold", "stop", "shadow", "done", "idle"):
            ratio = contrast_ratio(palette[name], palette["surface"])
            assert ratio >= 3.0, f"{theme}/{name} on surface: {ratio:.2f} < 3.0"

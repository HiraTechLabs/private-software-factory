# Fonts to-do (human task)

`design/tokens.json` declares `IBM Plex Sans`, `IBM Plex Sans Arabic`, and `IBM Plex Mono`, but
rule R (no external CDNs or font hosts) forbids linking to a font host. Until the files are
vendored, the stacks fall back to `system-ui` and the default mono.

Human to-do:

1. Download the OFL-licensed woff2 files for IBM Plex Sans (regular, medium, semibold, bold),
   IBM Plex Sans Arabic, and IBM Plex Mono (regular, medium).
2. Place them under `static/fonts/` (git-ignored? no — fonts are static assets, commit them).
3. Add the `@font-face` rules to `static/fonts.css` and link it next to `style.css`.
4. Run `python scripts/ui_lint.py` and the tests; update this file to "done" with the commit.

License note: the IBM Plex family is published under the SIL Open Font License.

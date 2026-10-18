"""Build what each model role is told, and record what was used (ADRs 0011, 0012).

The prompt is role instructions + principles + a decisions index + the project graph +
a file tree + the request (+ plan, diff, checks for later roles) + the owner's note.
Every principle file used is recorded with its path and content hash in
`context-sources.json`, so the owner can see what the model was told.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from factory import store

MAX_CHARS = 24000

ROLE_INSTRUCTIONS: dict[str, str] = {
    "plan": (
        "You are the planning role of a software factory. Read the request and the "
        "rules, then write a short plan in Markdown: what changes, which files, risks, "
        "which records to update, and how to test. Do not write code."
    ),
    "build": (
        "You are the build role of a software factory. Produce the full new content of "
        "every file you change. Answer with file blocks only, in this exact format:\n\n"
        "<<<FILE path/relative/to/repo>>>\n"
        "full new content of the file\n"
        "<<<END>>>\n\n"
        "Use paths relative to the repository root. Send full file contents, never "
        "diffs. Do not run commands; commands come from the project manifest only."
    ),
    "review": (
        "You are the review role of a software factory. Read the plan, the changes, "
        "and the check results. Begin with a line `VERDICT: approve` or "
        "`VERDICT: changes`, then list findings. Your verdict is advice; a human "
        "decides."
    ),
}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(store.ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _principles_block(project_id: str) -> tuple[str, list[dict]]:
    sources: list[dict] = []
    blocks: list[str] = []
    for label, folder in (
        ("Shared principles", store.SHARED_PRINCIPLES_DIR),
        ("Project principles", store.principles_dir(project_id)),
    ):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            rel = _display_path(path)
            blocks.append(f"### {label}: {path.name} (source: {rel})\n{text}")
            sources.append({"path": rel, "sha256": _hash(text)})
    return "\n\n".join(blocks), sources


def _decisions_block(repo_path: Path, records: dict) -> str:
    decisions_dir = repo_path / records.get("decisions", "docs/decisions")
    if not decisions_dir.is_dir():
        return "No decisions recorded yet."
    lines: list[str] = []
    for path in sorted(decisions_dir.glob("*.md")):
        if path.name in {"README.md", "0000-template.md"}:
            continue
        front = {}
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 2:
                try:
                    front = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    front = {}
        lines.append(
            f"- {front.get('id', path.stem)}: {front.get('title', path.stem)} "
            f"[{front.get('status', 'unknown')}]"
        )
    return "\n".join(lines) if lines else "No decisions recorded yet."


def _graph_block(repo_path: Path, records: dict) -> str:
    graph_path = repo_path / records.get("graph", "docs/architecture/graph.yaml")
    if not graph_path.exists():
        return "No architecture graph yet."
    return graph_path.read_text(encoding="utf-8")[:4000]


def _file_tree(repo_path: Path, cap: int = 200) -> str:
    if not repo_path.is_dir():
        return "(repository not created yet)"
    paths: list[str] = []
    for path in sorted(repo_path.rglob("*")):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(repo_path)
        paths.append(str(rel).replace("\\", "/") + ("/" if path.is_dir() else ""))
        if len(paths) >= cap:
            paths.append("… (truncated)")
            break
    return "\n".join(paths) or "(empty repository)"


def build_prompt(
    project_id: str,
    repo_path: Path,
    records: dict,
    change: dict,
    step: str,
    extra_note: str = "",
) -> tuple[str, list[dict]]:
    instructions = ROLE_INSTRUCTIONS.get(step, ROLE_INSTRUCTIONS["plan"])
    principles, sources = _principles_block(project_id)
    request_block = (
        f"## Request ({change.get('id', '')})\n"
        f"Title: {change.get('title', '')}\n"
        f"Kind: {change.get('kind', 'feature')}\n\n"
        f"{change.get('description', '')}"
    )
    extra_parts: list[str] = []
    if step in {"build", "review"} and change.get("plan"):
        extra_parts.append("## Plan\n" + change["plan"])
    if step == "review" and change.get("diff"):
        extra_parts.append("## Changes (diff)\n" + change["diff"])
    if step == "review" and change.get("checks_log"):
        extra_parts.append("## Check output\n" + change["checks_log"])
    if extra_note:
        extra_parts.append("## Note from the owner\n" + extra_note)
    sections = [
        f"# Instructions\n{instructions}",
        f"# Principles\n{principles or 'No principles set.'}",
        f"# Decisions\n{_decisions_block(repo_path, records)}",
        f"# Architecture graph\n{_graph_block(repo_path, records)}",
        f"# File tree\n{_file_tree(repo_path)}",
        request_block,
        *extra_parts,
    ]
    prompt = "\n\n".join(section for section in sections if section)
    if len(prompt) > MAX_CHARS:
        prompt = (
            prompt[:MAX_CHARS]
            + "\n\n[… the rest of the context was truncated to fit the size cap …]\n"
        )
    return prompt, sources


def write_context_files(
    project_id: str,
    change_id: str,
    step: str,
    prompt: str,
    sources: list[dict],
) -> None:
    store.write_artifact(project_id, change_id, f"prompt-{step}.md", prompt)
    lines = ["["]
    for index, source in enumerate(sources):
        comma = "," if index < len(sources) - 1 else ""
        lines.append(
            f'  {{"path": "{source["path"]}", "sha256": "{source["sha256"]}"}}{comma}'
        )
    lines.append("]")
    store.write_artifact(
        project_id, change_id, "context-sources.json", "\n".join(lines)
    )

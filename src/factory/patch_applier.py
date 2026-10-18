"""Turn build file blocks into a commit, after validating every path (ADR 0012)."""

from __future__ import annotations

import re
from pathlib import Path

from factory import git_ops, store

FILE_BLOCK_RE = re.compile(r"<<<FILE (.+?)>>>\r?\n(.*?)<<<END>>>", re.DOTALL)


class PatchError(Exception):
    pass


def parse(answer: str) -> list[tuple[str, str]]:
    files = [
        (match.group(1).strip(), match.group(2))
        for match in FILE_BLOCK_RE.finditer(answer or "")
    ]
    if not files:
        raise PatchError(
            "the answer had no file blocks (no <<<FILE ...>>> ... <<<END>>> block)"
        )
    return files


def validate(
    files: list[tuple[str, str]],
    worktree: Path,
    protected_paths: list[str],
    max_files: int,
    max_file_kb: int,
) -> None:
    if len(files) > max_files:
        raise PatchError(
            f"the answer changes {len(files)} files; the limit is {max_files}"
        )
    root = worktree.resolve()
    for raw_path, content in files:
        path = raw_path.strip()
        candidate = Path(path)
        if candidate.is_absolute():
            raise PatchError(f"path {path!r} is absolute")
        parts = candidate.parts
        if ".." in parts:
            raise PatchError(f"path {path!r} contains '..'")
        if ".git" in parts:
            raise PatchError(f"path {path!r} targets .git")
        for protected in protected_paths:
            if path == protected or path.startswith(protected.rstrip("/") + "/"):
                raise PatchError(f"path {path!r} is protected by the project settings")
        resolved = (root / candidate).resolve()
        if resolved != root and root not in resolved.parents:
            raise PatchError(f"path {path!r} points outside the change worktree")
        size_kb = len(content.encode("utf-8")) / 1024
        if size_kb > max_file_kb:
            raise PatchError(
                f"file {path!r} is {size_kb:.0f} kB; the limit is {max_file_kb} kB"
            )


def apply(
    answer: str,
    worktree: Path,
    protected_paths: list[str],
    limits: dict,
    *,
    message: str = "build: apply model output",
) -> tuple[list[str], str]:
    files = parse(answer)
    validate(
        files,
        worktree,
        protected_paths,
        int(limits.get("max_files", 30)),
        int(limits.get("max_file_kb", 200)),
    )
    written: list[str] = []
    for raw_path, content in files:
        target = worktree / raw_path.strip()
        store.atomic_write_text(target, content)
        written.append(raw_path.strip())
    result = git_ops.commit_all(worktree, message)
    if not result.ok:
        raise PatchError(f"git commit failed: {result.output}")
    return written, git_ops.head_commit(worktree)

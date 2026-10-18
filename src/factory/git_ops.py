"""Thin wrapper over git (ADR 0004). Argument lists only, never shell=True."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        return (self.stdout + self.stderr).strip()


def run(args: list[str], cwd: Path, timeout: int = 120) -> GitResult:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
    except FileNotFoundError:
        return GitResult(127, "", "git is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        return GitResult(124, "", f"git {args[0]} timed out after {timeout}s")
    return GitResult(completed.returncode, completed.stdout, completed.stderr)


def init_repo(path: Path) -> GitResult:
    path.mkdir(parents=True, exist_ok=True)
    result = run(["init", "-b", "main"], cwd=path)
    if not result.ok:
        return result
    run(["config", "user.name", "Factory"], cwd=path)
    run(["config", "user.email", "factory@localhost"], cwd=path)
    return result


def is_repo(path: Path) -> bool:
    return (path / ".git").exists()


def has_uncommitted(path: Path) -> bool:
    result = run(["status", "--porcelain"], cwd=path)
    return bool(result.stdout.strip())


def commit_all(path: Path, message: str) -> GitResult:
    run(["add", "-A"], cwd=path)
    return run(["commit", "-m", message, "--allow-empty"], cwd=path)


def head_commit(path: Path) -> str:
    return run(["rev-parse", "HEAD"], cwd=path).stdout.strip()


def add_worktree(
    repo: Path, worktree: Path, branch: str, base: str = "main"
) -> GitResult:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    return run(["worktree", "add", "-b", branch, str(worktree), base], cwd=repo)


def remove_worktree(repo: Path, worktree: Path) -> GitResult:
    return run(["worktree", "remove", "--force", str(worktree)], cwd=repo)


def delete_branch(repo: Path, branch: str) -> GitResult:
    return run(["branch", "-D", branch], cwd=repo)


def diff_against(repo: Path, base: str) -> str:
    return run(["diff", base], cwd=repo).stdout


def merge_no_ff(repo: Path, branch: str) -> GitResult:
    return run(["merge", "--no-ff", "--no-edit", branch], cwd=repo)

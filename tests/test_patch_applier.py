"""Patch applier tests: every rejection reason, and a successful commit."""

from __future__ import annotations

import pytest

from factory import git_ops, patch_applier


def _worktree(data_root):
    worktree = data_root / "wt"
    worktree.mkdir()
    return worktree


def test_reject_absolute_path(data_root):
    with pytest.raises(patch_applier.PatchError):
        patch_applier.validate(
            [("/etc/passwd", "x")], _worktree(data_root), [], 30, 200
        )


def test_reject_parent_traversal(data_root):
    with pytest.raises(patch_applier.PatchError):
        patch_applier.validate([("../x", "y")], _worktree(data_root), [], 30, 200)


def test_reject_git_directory(data_root):
    with pytest.raises(patch_applier.PatchError):
        patch_applier.validate(
            [(".git/config", "y")], _worktree(data_root), [], 30, 200
        )


def test_reject_protected_path(data_root):
    with pytest.raises(patch_applier.PatchError):
        patch_applier.validate(
            [("docs/a.md", "y")], _worktree(data_root), ["docs"], 30, 200
        )


def test_reject_too_many_files(data_root):
    with pytest.raises(patch_applier.PatchError):
        patch_applier.validate(
            [("a", "x"), ("b", "y")], _worktree(data_root), [], 1, 200
        )


def test_reject_file_too_big(data_root):
    with pytest.raises(patch_applier.PatchError):
        patch_applier.validate([("a.txt", "x" * 4000)], _worktree(data_root), [], 30, 1)


def test_parse_requires_file_blocks():
    with pytest.raises(patch_applier.PatchError):
        patch_applier.parse("just some prose, no blocks")


def test_apply_writes_and_commits(data_root):
    worktree = _worktree(data_root)
    git_ops.init_repo(worktree)
    git_ops.commit_all(worktree, "initial")
    written, commit = patch_applier.apply(
        "<<<FILE notes/c-0001.md>>>\nhi\n<<<END>>>",
        worktree,
        [],
        {"max_files": 30, "max_file_kb": 200},
    )
    assert written == ["notes/c-0001.md"]
    assert (worktree / "notes" / "c-0001.md").read_text(encoding="utf-8") == "hi\n"
    assert commit
    assert not git_ops.has_uncommitted(worktree)

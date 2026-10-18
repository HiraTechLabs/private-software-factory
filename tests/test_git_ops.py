"""Git wrapper tests: init, commit, worktree, diff, merge (real git, arg lists only)."""

from __future__ import annotations

from factory import git_ops


def test_init_commit_and_worktree(data_root):
    repo = data_root / "sample"
    assert git_ops.init_repo(repo).ok
    assert git_ops.is_repo(repo)
    (repo / "a.txt").write_text("a", encoding="utf-8")
    assert git_ops.commit_all(repo, "initial").ok
    assert not git_ops.has_uncommitted(repo)
    assert git_ops.head_commit(repo)

    worktree = data_root / "work"
    assert git_ops.add_worktree(repo, worktree, "change/c-0001", "main").ok
    (worktree / "b.txt").write_text("b", encoding="utf-8")
    assert git_ops.commit_all(worktree, "add b").ok
    assert "b.txt" in git_ops.diff_against(worktree, "main")

    assert git_ops.merge_no_ff(repo, "change/c-0001").ok
    assert (repo / "b.txt").exists()
    assert git_ops.remove_worktree(repo, worktree).ok
    assert git_ops.delete_branch(repo, "change/c-0001").ok


def test_dirty_repo_detected(data_root):
    repo = data_root / "dirty"
    git_ops.init_repo(repo)
    (repo / "a.txt").write_text("a", encoding="utf-8")
    git_ops.commit_all(repo, "initial")
    (repo / "new.txt").write_text("x", encoding="utf-8")
    assert git_ops.has_uncommitted(repo)

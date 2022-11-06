"""Test feature store git operations"""
from unittest.mock import MagicMock

import pytest as pytest
from git import FetchInfo, GitCommandError

from domino_data._feature_store.git import pull_repo, push_to_git


def test_git_pull(caplog):
    repo = MagicMock()
    repo.remotes.origin.pull.return_value = [MagicMock(flags=FetchInfo.HEAD_UPTODATE)]

    # Pull success
    pull_repo(repo)
    assert "Finished pulling the repo" in caplog.text

    # Pull failure
    repo.remotes.origin.pull.return_value = [MagicMock(flags=FetchInfo.ERROR)]
    with pytest.raises(
        Exception,
        match="Failed to pull the repo with error flag 128",
    ):
        pull_repo(repo)


def test_git_push(caplog):
    repo = MagicMock()

    repo.untracked_files = ["data/online.db"]
    repo.index.diff.return_value = [MagicMock(a_path="test_add.txt")]

    # push success
    push_to_git(repo)
    assert "Pushed to the repo" in caplog.text

    repo.git.add = MagicMock(side_effect=GitCommandError("git add", "error"))

    with pytest.raises(GitCommandError):
        push_to_git(repo)

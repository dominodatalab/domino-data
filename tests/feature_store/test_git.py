"""Test feature store git operations"""

from unittest.mock import MagicMock

import pytest as pytest
from git import FetchInfo, GitCommandError, PushInfo

from domino_data._feature_store.exceptions import GitPullError, GitPushError
from domino_data._feature_store.git import pull_repo, push_to_git


def test_git_pull(caplog):
    repo = MagicMock()
    repo.remotes.origin.pull.return_value = [MagicMock(flags=FetchInfo.HEAD_UPTODATE)]

    # Pull success
    repo.active_branch.name = "main"
    pull_repo(repo, "main")
    assert "Finished pulling the repo" in caplog.text

    # Pull failure
    repo.remotes.origin.pull.return_value = [MagicMock(flags=FetchInfo.ERROR)]
    with pytest.raises(
        GitPullError,
        match="Failed to pull the repo with error flag 128",
    ):
        pull_repo(repo, "main")

    # Switch branch
    pull_repo(repo, "dev")
    assert "Switched to branch dev" in caplog.text


def test_git_push(caplog):
    repo = MagicMock()

    repo.untracked_files = ["data/online.db"]
    repo.index.diff.return_value = [MagicMock(a_path="test_add.txt")]

    # push success
    repo.remotes.origin.push.return_value = [MagicMock(flags=PushInfo.NEW_HEAD)]
    push_to_git(repo)
    assert "Pushed to the repo" in caplog.text

    # push failure
    repo.remotes.origin.push.return_value = [MagicMock(flags=PushInfo.ERROR)]
    with pytest.raises(
        GitPushError,
        match="Failed to push to the repo with error flag 1024",
    ):
        push_to_git(repo)

    # git add error
    repo.git.add = MagicMock(side_effect=GitCommandError("git add", "error"))

    with pytest.raises(GitCommandError):
        push_to_git(repo)
        repo.remotes.origin.push()

"""Test feature store git operations"""
import contextlib
import io
from unittest.mock import MagicMock

import pytest as pytest
from git import FetchInfo, GitCommandError

from domino_data._feature_store.git import pull_repo, push_to_git


def test_git_pull():
    repo = MagicMock()
    repo.remotes.origin.pull.return_value = [MagicMock(flags=FetchInfo.HEAD_UPTODATE)]

    # Pull success
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        pull_repo(repo)
        # TODO investigate why the logs are not captured.
        # assert "Finished pulling the repo" in buf.getvalue()

    # Pull failure
    repo.remotes.origin.pull.return_value = [MagicMock(flags=FetchInfo.ERROR)]
    with pytest.raises(
        Exception,
        match="Failed to pull the repo with error flag 128",
    ):
        pull_repo(repo)


def test_git_push():
    repo = MagicMock()

    repo.untracked_files = ["data/online.db"]
    repo.index.diff.return_value = [MagicMock(a_path="test_add.txt")]

    # push success
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        push_to_git(repo)
        # TODO investigate why the logs are not captured.
        # assert "Pushed to the repo" in buf.getvalue()

    repo.git.add = MagicMock(side_effect=GitCommandError("git add", "error"))

    with pytest.raises(GitCommandError):
        push_to_git(repo)

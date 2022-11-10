"""Containing APIs to interact with feast git repository"""

from git import FetchInfo, PushInfo, Repo

from ..logging import logger
from .exceptions import GitPullError, GitPushError

_INVALID_PULL_FLAGS = [FetchInfo.ERROR, FetchInfo.REJECTED]
_INVALID_PUSH_FLAGS = [
    PushInfo.ERROR,
    PushInfo.REJECTED,
    PushInfo.REMOTE_FAILURE,
    PushInfo.REMOTE_REJECTED,
]


def pull_repo(repo: Repo, branch_name: str) -> None:
    """Pull feast repo.

    Args:
        repo: the feast Git Repo object.
        branch_name: the branch to pull

    Raises:
        GitPullError: if fails to pull the repo
    """
    current_branch = repo.active_branch.name
    if current_branch == branch_name:
        logger.info(f"The git repo is already on branch {branch_name}")
        logger.info(f"Commit Sha before pulling:{repo.head.object.hexsha}")
        pull_result = repo.remotes.origin.pull()
        result_flag = pull_result[0].flags
        if result_flag in _INVALID_PULL_FLAGS:
            raise GitPullError(f"Failed to pull the repo with error flag {result_flag}")
        logger.info("Finished pulling the repo.")
        logger.info(f"Commit Sha after pulling:{repo.head.object.hexsha}")
    else:
        logger.info(f"Switching branch from {current_branch} to {branch_name}")
        result = repo.git.checkout(branch_name)
        logger.info(result)
        logger.info(f"Switched to branch {branch_name}, commit Sha:{repo.head.object.hexsha}")


def push_to_git(repo: Repo) -> None:
    """Push feast apply result to the feast repo.

    Args:
        repo: The feast Git Repo object.

    Raises:
        GitPushError: if fails to push to the repo
    """
    logger.info("Starting Git add/commit/push......")
    current_commit_id = repo.head.object.hexsha
    registry_file = "data/registry.db"
    registry_file_added = False

    # New added files. e.g. online.db is created when running feast apply for the first time
    for new_added_file in repo.untracked_files:
        repo.git.add(new_added_file)
        logger.info(f"Added new file {new_added_file} to git")

    for item in repo.index.diff(None):
        repo.git.add(item.a_path)
        logger.info(f"Added modified file {item.a_path} to git")
        if item.a_path == registry_file:
            registry_file_added = True

    # This file can be added in .gitignore file. So forcing adding it here.
    if not registry_file_added:
        repo.git.add(registry_file, force=True)
        logger.info(f"Forced adding {registry_file} to git")

    repo.git.commit("-m", f"Domino run feast apply on {current_commit_id}")
    logger.info(f"Committed feast apply result on {current_commit_id}")
    push_result = repo.remotes.origin.push()
    result_flag = push_result[0].flags
    if result_flag in _INVALID_PUSH_FLAGS:
        raise GitPushError(f"Failed to push to the repo with error flag {result_flag}")
    logger.info(f"Pushed to the repo. The commit id {repo.head.object.hexsha}")

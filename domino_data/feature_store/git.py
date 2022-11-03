"""Containing APIs to interact with feast git repository"""

from git import FetchInfo, Repo

from ..logging import logger
from .exceptions import GitPullError


def pull_repo(repo: Repo) -> None:
    logger.info(f"Commit Sha before pulling:{repo.head.object.hexsha}")
    logger.info("Pulling the repo......")
    pull_result = repo.remotes.origin.pull()
    result_flag = pull_result[0].flags
    if result_flag == FetchInfo.ERROR or result_flag == FetchInfo.REJECTED:
        raise GitPullError(f"Failed to pull the repo with error flag {result_flag}")
    logger.info("Finished pulling the repo.")
    logger.info(f"Commit Sha after pulling:{repo.head.object.hexsha}")


def push_to_git(repo: Repo) -> None:
    logger.info("Starting Git add/commit/push......")
    current_commit_id = repo.head.object.hexsha
    # This file can be added in .gitignore file. So forcing adding it here.
    repo.git.add("data/registry.db", force=True)
    repo.git.add("data/online.db", force=True)

    logger.info(f"Added data/registry.db and data/online.db to git")

    repo.git.commit("-m", f"feast apply on {current_commit_id}")
    logger.info(f"Committed feast apply result on {current_commit_id}")
    repo.remotes.origin.push()
    logger.info(f"Pushed to the repo. The commit id {repo.head.object.hexsha}")

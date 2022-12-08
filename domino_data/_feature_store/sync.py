"""Containing APIs to sync feature store from feast to domino"""

import os
import time
from pathlib import Path

from git import Repo

from feature_store_api_client.models import (
    Entity,
    Feature,
    FeatureStoreSyncResult,
    FeatureViewRequest,
    FeatureViewRequestTags,
    LockFeatureStoreRequest,
    UnlockFeatureStoreRequest,
)
from feature_store_api_client.types import UNSET

from ..logging import logger
from .client import FeatureStoreClient
from .exceptions import FeastRepoError, FeatureStoreLockError
from .git import pull_repo, push_to_git

LOCK_FAILURE_MESSAGE = "Failed to lock feature store for syncing. Please rerun later."

_import_error_message = (
    "feast is not installed.\n\n"
    "Please pip install feast:\n\n"
    "  python -m pip install feast   # install directly\n"
    '  python -m pip install "dominodatalab-data[feast]" --upgrade   # install via extra dependency'
)

try:
    from feast import FeatureStore, repo_config, repo_operations
except ImportError as e:
    if e.msg == "No module named 'feast'":
        raise ImportError(_import_error_message) from e
    else:
        raise


def lock(feature_store_id: str, max_retries: int) -> None:
    """Lock the feature store for updating features. If fails, retry until
    succeeds or reaches the maximum retry limit
    Args:
        feature_store_id: the id of the feature store to be locked
        max_retries: the maximum number of retries
    Raises:
        FeatureStoreLockError: if fails to lock
    """
    logger.info("Locking the feature store")
    client = FeatureStoreClient()
    lock_request = LockFeatureStoreRequest(
        feature_store_id=feature_store_id,
        project_name=os.getenv("DOMINO_PROJECT_NAME", ""),
        user_name=os.getenv("DOMINO_STARTING_USERNAME", ""),
        run_id=os.getenv("DOMINO_RUN_ID", ""),
    )
    lock_result = False
    retry_count = 0
    while not lock_result and retry_count <= max_retries:
        lock_result = client.lock(lock_request)
        if not lock_result:
            time.sleep(1)
            logger.info(f"Failed to lock the feature store. retry count: {retry_count}")
            retry_count += 1

    if not lock_result:
        raise FeatureStoreLockError(LOCK_FAILURE_MESSAGE)
    logger.info("Locked the feature store")


def unlock(feature_store_id: str, sync_result: FeatureStoreSyncResult) -> None:
    """UnLock the feature store
    Args:
        feature_store_id: the id of the feature store to be unlocked
        sync_result: the synchronization result
    """
    logger.info("UnLocking the feature store")
    try:
        client = FeatureStoreClient()
        result = client.unlock(
            UnlockFeatureStoreRequest(feature_store_id=feature_store_id, sync_result=sync_result)
        )
        logger.info(
            "Unlocked the feature store." if result else "Failed to unlock the feature store."
        )
    except Exception as e:
        logger.exception(e)


def update_feature_views(commit_id: str, repo_path: str) -> None:
    """Update domino feature views to sync with specified feast git commit
    Args:
        commit_id: the feast git repo commit id that are to be synced with domino
        repo_path: the feast git repo path
    """
    logger.info(f"Syncing feature views to feast git commit {commit_id}")

    feast_feature_store = FeatureStore(repo_path)

    feature_views = feast_feature_store.list_feature_views()

    request_input = []
    for fv in feature_views:
        feature_v = FeatureViewRequest(
            name=fv.name,
            entities=[
                Entity(name=x, join_key=y.name, value_type=str(y.dtype))
                for x, y in zip(fv.entities, fv.entity_columns)
            ],
            features=[Feature(name=f.name, dtype=str(f.dtype)) for f in fv.features],
            ttl=UNSET if fv.ttl is None else int(fv.ttl.total_seconds() * 1000),
            tags=FeatureViewRequestTags.from_dict(fv.tags),
        )
        request_input.append(feature_v)

    client = FeatureStoreClient()
    client.post_feature_views(request_input, commit_id)
    logger.info("Feature Views successfully synced.")


def find_feast_repo_path(root_dir: str) -> str:
    """Find the feast repo path
    Args:
        root_dir: the feast git repo root directory
    Returns:
        the feast repo path
    Raises:
        FeastRepoError: if no feast repo or more than one repo in the specified root directory
        FileNotFoundError: the root path doesn't exist
        NotADirectoryError: the root path is not a directory
    """
    sub_dirs = []
    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"The repo root path {root_dir} does not exist.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"The repo root path {root_dir} is not a directory.")

    for file_name in os.listdir(root_dir):
        if file_name.startswith("."):
            continue
        full_path = os.path.join(root_dir, file_name)
        if os.path.isdir(full_path):
            sub_dirs.append(full_path)

    if len(sub_dirs) == 0:
        raise FeastRepoError(f"No repo is found under {root_dir}")

    if len(sub_dirs) > 1:
        raise FeastRepoError(f"Multiple repos found under {root_dir}: " + ",".join(sub_dirs))

    return sub_dirs[0]


def run_feast_apply(repo_path_str: str, skip_source_validation: bool = False) -> None:
    """run feast apply
    Args:
        repo_path_str: the feast git repo path
        skip_source_validation: don't validate the data sources by
                                checking for that the tables exist if true
    """
    logger.info("running feast apply")
    repo_path = Path(repo_path_str).absolute()
    fs_yaml_file = repo_path / "feature_store.yaml"
    repo_operations.cli_check_repo(repo_path, fs_yaml_file)

    feast_repo_config = repo_config.load_repo_config(repo_path, fs_yaml_file)
    repo_operations.apply_total(feast_repo_config, repo_path, skip_source_validation)


def feature_store_sync(
    feature_store_id: str,
    repo_path_str: str,
    branch_name: str,
    max_retries: int,
    skip_source_validation: bool = False,
) -> None:
    """run feature store syncing
    Args:
        feature_store_id: the feature store domino id
        repo_path_str: feast repo path
        branch_name: feast repo branch
        max_retries: maximum lock retry count
        skip_source_validation: option for running feast apply command.
                                Don't validate the data sources by checking
                                for that the tables exist if true
    """
    if not repo_path_str:
        root_dir = os.getenv("DOMINO_FEAST_REPO_ROOT", "/features")
        repo_path_str = find_feast_repo_path(root_dir)

    repo = Repo(repo_path_str)
    if not branch_name:
        branch_name = repo.active_branch.name

    if not max_retries:
        max_retries = 60

    logger.info(
        f"Starting syncing for feature store {feature_store_id} with {repo_path_str} "
        f"on branch {branch_name}"
    )

    result = FeatureStoreSyncResult.FAILURE
    lock(feature_store_id, max_retries)
    try:
        pull_repo(repo, branch_name)
        run_feast_apply(repo_path_str=repo_path_str, skip_source_validation=skip_source_validation)
        push_to_git(repo)
        update_feature_views(repo.head.object.hexsha, repo_path_str)
        result = FeatureStoreSyncResult.SUCCESS
        logger.info("Finished feature store syncing.")
    finally:
        unlock(feature_store_id, result)

"""Containing APIs to sync feature store from feast to domino"""

import os
from pathlib import Path

from git import Repo

from feature_store_api_client.models import (
    Entity,
    Feature,
    FeatureViewRequest,
    FeatureViewRequestTags,
)

from ..logging import logger
from .exceptions import FeastRepoError
from .featurestore import FeatureStoreClient
from .git import pull_repo, push_to_git

LOCK_FAILURE_MESSAGE = "Failed to lock feature store for syncing. Please rerun later."

client = None

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


def lock() -> None:
    logger.info("Locking the feature store")
    # TODO Call feature store client lock method
    # Raise FeatureStoreLockError with detailed reason if fails to lock.
    logger.info("Locked the feature store")
    return True


def unlock() -> None:
    logger.info("UnLocking the feature store")
    # TODO Call feature store client unlock method
    logger.info("UnLocked the feature store")
    return True


def update_feature_views(commit_id: str, repo_path: str = None) -> None:
    logger.info(f"Syncing feature views to feast git commit {commit_id}")

    if not repo_path:
        repo_path = find_feast_repo_path()
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
            ttl=None if fv.ttl is None else int(fv.ttl.total_seconds() * 1000),
            tags=FeatureViewRequestTags.from_dict(fv.tags),
        )
        request_input.append(feature_v)

    # TODO update the API to include the commit id so that feature views
    # and commit id can be updated to domino in one call
    client.post_feature_views(request_input)
    logger.info("Feature Views successfully synced.")


def find_feast_repo_path() -> str:
    root_dir = os.getenv("DOMINO_FEAST_REPO_ROOT", "/features")
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
    logger.info("running feast apply")
    repo_path = Path(repo_path_str).absolute()
    fs_yaml_file = repo_path / "_feature_store.yaml"
    # cli_check_repo(repo_path, fs_yaml_file)
    repo_operations.cli_check_repo(repo_path)

    feast_repo_config = repo_config.load_repo_config(repo_path, fs_yaml_file)
    repo_operations.apply_total(feast_repo_config, repo_path, skip_source_validation)


def feature_store_sync(skip_source_validation=False):
    logger.info("Starting feature store syncing......")
    repo_path_str = find_feast_repo_path()
    global client
    client = FeatureStoreClient()
    lock()
    try:
        repo = Repo(repo_path_str)
        pull_repo(repo)
        run_feast_apply(repo_path_str=repo_path_str, skip_source_validation=skip_source_validation)
        push_to_git(repo)
        update_feature_views(repo.head.object.hexsha)
        logger.info("Finished feature store syncing.")
    finally:
        unlock()

import os
import subprocess
import sys

from feast import FeatureStore, cli
from git import FetchInfo, Repo

from domino_data.featurestore import FeatureStoreClient
from feature_store_api_client.models import (
    Entity,
    Feature,
    FeatureViewRequest,
    FeatureViewRequestTags,
)

from .logging import logger

logger.add(sys.stdout, format="[{time}] {message}")


class FeastApplyError(RuntimeError):
    """Raised when failed to run feast apply"""

    pass


class MultiFeastReposError(RuntimeError):
    """Raised when more than one feast repos are found"""

    pass


class GitPullError(RuntimeError):
    """Raised when git pull failed"""

    pass


class FeatureStoreLockError(RuntimeError):
    """Raised when failed to lock or unlock the feature store"""

    pass


FEAST_REPO_ROOT = "/features"
MSG_NO_CHANGES_TO_REGISTRY = "No changes to registry"
MSG_NO_CHANGES_TO_INFRA = "No changes to infrastructure"
LOCK_FAILURE_MESSAGE = "Failed to lock feature store for syncing. Please rerun later."


class FeastDominoSynchronizer:
    """The Synchronizer that synchronizes changes from feast to domino"""

    def __init__(self, repo_path=None):
        self.client = FeatureStoreClient()
        if not repo_path:
            repo_path = find_feast_repo_path()
        self.feature_store = FeatureStore(repo_path)

    def update_feature_views(self, commit_id) -> None:
        print(f"Syncing feature views to feast git commit {commit_id}")
        feature_views = self.feature_store.list_feature_views()

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
        self.client.post_feature_views(request_input)
        print("Feature Views successfully synced.")

    def lock(self) -> None:
        print("Locking the feature store")
        # TODO Call feature store client lock method
        # Raise FeatureStoreLockError with detailed reason if fails to lock.
        print("Locked the feature store")
        return True

    def unlock(self) -> None:
        print("UnLocking the feature store")
        # TODO Call feature store client unlock method
        print("UnLocked the feature store")
        return True


def find_feast_repo_path():
    sub_dirs = []
    if not os.path.exists(FEAST_REPO_ROOT):
        raise FileNotFoundError(f"The repo root path {FEAST_REPO_ROOT} does not exist.")
    if not os.path.isdir(FEAST_REPO_ROOT):
        raise NotADirectoryError(f"The repo root path {FEAST_REPO_ROOT} is not a directory.")

    for file_name in os.listdir(FEAST_REPO_ROOT):
        if file_name.startswith("."):
            continue
        full_path = os.path.join(FEAST_REPO_ROOT, file_name)
        if os.path.isdir(full_path):
            sub_dirs.append(full_path)

    if len(sub_dirs) == 0:
        raise FileNotFoundError(f"No repo is found under {FEAST_REPO_ROOT}")

    if len(sub_dirs) > 1:
        raise MultiFeastReposError(
            f"Multiple repos found under {FEAST_REPO_ROOT}: " + ",".join(sub_dirs)
        )

    return sub_dirs[0]


def pull_repo(repo):
    logger.info(f"Commit Sha before pulling:{repo.head.object.hexsha}")
    print("Pulling the repo......")
    pull_result = repo.remotes.origin.pull()
    result_flag = pull_result[0].flags
    if result_flag == FetchInfo.ERROR or result_flag == FetchInfo.REJECTED:
        raise GitPullError(f"Failed to pull the repo with error flag {result_flag}")
    print("Finished pulling the repo.")
    print(f"Commit Sha after pulling:{repo.head.object.hexsha}")


def run_command(args, cwd):
    """
    Run the command with given arguments from given directory in a new process
    :param args: a list representation of the command to run. e.g. ['feast', 'apply']
    :param cwd: The directory from where to run the command
    :return: a tuple of run status code and the output message. 0 means a successful run, other
    status codes indicate failures
    """
    try:
        return (
            0,
            subprocess.check_output(
                args,
                cwd=cwd,
                stderr=subprocess.STDOUT,
            ),
        )
    except subprocess.CalledProcessError as e:

        return e.returncode, e.output


def run_feast_apply():
    """
    Run feast apply command.
    :return: True if there is any change to registry.
    :rtype: (bool, bool) flags indicating if the feast registry, infrastructure has been changed.
    :raises:
        FeastApplyError: if failed to run feast apply.
    """
    print("running feast apply")

    return_code, output = run_command(
        [sys.executable, cli.__file__, "apply"], find_feast_repo_path()
    )
    output = output.decode("utf-8")

    if return_code != 0:
        raise FeastApplyError(output)
    else:
        print(output)
        print("finished running feast apply")

    return MSG_NO_CHANGES_TO_REGISTRY not in output, MSG_NO_CHANGES_TO_INFRA not in output


def _push_to_git(repo, change_flags):
    registry_changed = change_flags[0]
    infra_changed = change_flags[1]
    if not (registry_changed or infra_changed):
        print("No changes to be pushed to Git Repo")
        return

    print("Committing to the repo......")
    # This file can be added in .gitignore file. So forcing adding it here.
    if registry_changed:
        repo.git.add("data/registry.db", force=True)
    if infra_changed:
        repo.git.add("data/online.db", force=True)

    repo.git.commit("-m", "feast apply on " + repo.head.object.hexsha)
    print("Pushing to the repo......")
    repo.remotes.origin.push()
    print("Pushed to the repo")


def sync():
    print("Starting feature store syncing......")
    repo_path = find_feast_repo_path()
    synchronizer = FeastDominoSynchronizer(repo_path=repo_path)

    synchronizer.lock()
    try:
        repo = Repo(repo_path)
        pull_repo(repo)
        change_flags = run_feast_apply()
        _push_to_git(repo, change_flags)
        synchronizer.update_feature_views(repo.head.object.hexsha)
        print("Finished feature store syncing.")
    finally:
        synchronizer.unlock()

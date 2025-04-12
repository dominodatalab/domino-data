import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from feast import FeatureStore, repo_config, repo_operations
from git.repo import Repo

from domino_data._feature_store import sync
from domino_data._feature_store.exceptions import (
    FeastRepoError,
    FeatureStoreLockError,
    ServerException,
)
from domino_data._feature_store.sync import find_feast_repo_path


def test_find_feast_repo_path(feast_repo_root_dir):
    feast_repo_root_dir = _get_feast_repo_root_dir()

    with pytest.raises(
        FeastRepoError,
    ):
        find_feast_repo_path(feast_repo_root_dir)

    open(os.path.join(feast_repo_root_dir, "a_file"), "a").close()
    with pytest.raises(
        NotADirectoryError,
    ):
        find_feast_repo_path(os.path.join(feast_repo_root_dir, "a_file"))

    Path(os.path.join(feast_repo_root_dir, "feast-repo1")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(feast_repo_root_dir, "feast-repo2")).mkdir(parents=True, exist_ok=True)

    with pytest.raises(
        FeastRepoError,
    ):
        find_feast_repo_path(feast_repo_root_dir)

    with pytest.raises(
        FileNotFoundError,
        match="The repo root path /non-exist-dir does not exist.",
    ):
        find_feast_repo_path("/non-exist-dir")


@pytest.mark.skip(reason="Test is failing due to unmocked token proxy endpoint")
def test_sync(feast_repo_root_dir, env, respx_mock, datafx):
    _set_up_feast_repo()

    # Happy path
    test_feature_store_id = "634e0eee26077433a69b0ec3"
    respx_mock.get("http://token-proxy/access-token").mock(
        return_value=httpx.Response(200, content=b"jwt")
    )

    respx_mock.post("http://domino/featurestore/featureview").mock(
        return_value=httpx.Response(200),
    )

    respx_mock.post("http://domino/featurestore/lock").mock(
        return_value=httpx.Response(200, content="true"),
    )

    respx_mock.post(f"http://domino/featurestore/unlock").mock(
        return_value=httpx.Response(200, content="true"),
    )

    repo_mock = MagicMock()
    repo_mock.head.object.hexsha = "123456"

    FeatureStore.__new__ = MagicMock()
    Repo.__new__ = MagicMock()
    Repo.__new__.return_value = repo_mock
    repo_config.load_repo_config = MagicMock()
    repo_operations.cli_check_repo = MagicMock()
    repo_operations.apply_total = MagicMock()

    sync.feature_store_sync(test_feature_store_id, None, None, None)

    repo_config.load_repo_config.assert_called()
    repo_operations.cli_check_repo.assert_called()
    repo_operations.apply_total.assert_called()

    # Update feature view failed
    respx_mock.post("http://domino/featurestore/featureview").mock(
        return_value=httpx.Response(500),
    )

    with pytest.raises(
        ServerException,
        match="could not create Feature Views",
    ):
        sync.feature_store_sync(test_feature_store_id, "/features/feast-test", None, None)

    # Lock failure
    respx_mock.post("http://domino/featurestore/lock").mock(
        return_value=httpx.Response(200, content="false"),
    )

    with pytest.raises(
        FeatureStoreLockError,
    ):
        sync.feature_store_sync(test_feature_store_id, None, None, 1)

    _clean_up_feast_repo()


def _get_feast_repo_root_dir():
    return os.getenv("DOMINO_FEAST_REPO_ROOT", "/features")


def _set_up_feast_repo():
    root_dir = _get_feast_repo_root_dir()
    Path(os.path.join(root_dir, "feast-repo")).mkdir(parents=True, exist_ok=True)


def _clean_up_feast_repo():
    root_dir = _get_feast_repo_root_dir()
    shutil.rmtree(os.path.join(root_dir, "feast-repo"))

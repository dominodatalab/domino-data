import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import httpx
from feast import FeatureStore, repo_config, repo_operations
from git import Repo

from domino_data._feature_store import featurestore_sync


def test_sync(feast_repo_root_dir, env, respx_mock):
    _set_up_feast_repo()

    respx_mock.post("http://domino/featurestore/featureview").mock(
        return_value=httpx.Response(200),
    )

    FeatureStore.__new__ = MagicMock()
    Repo.__new__ = MagicMock()
    repo_config.load_repo_config = MagicMock()
    repo_operations.cli_check_repo = MagicMock()
    repo_operations.apply_total = MagicMock()

    featurestore_sync.feature_store_sync()

    repo_config.load_repo_config.assert_called()
    repo_operations.cli_check_repo.assert_called()
    repo_operations.apply_total.assert_called()
    _clean_up_feast_repo()


def _set_up_feast_repo():
    root_dir = os.getenv("DOMINO_FEAST_REPO_ROOT", "/tmp")
    Path(os.path.join(root_dir, "feast-repo")).mkdir(parents=True, exist_ok=True)


def _clean_up_feast_repo():
    root_dir = os.getenv("DOMINO_FEAST_REPO_ROOT", "/tmp")
    shutil.rmtree(os.path.join(root_dir, "feast-repo"))

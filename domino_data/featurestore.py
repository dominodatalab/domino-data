"""Feature Store module."""
from typing import Optional, cast

import json
import os
from pathlib import Path

import click
import feast
from attrs import define, field
from feast.errors import FeastProviderLoginError
from feast.repo_config import load_repo_config
from feast.repo_operations import apply_total, cli_check_repo

from feature_store_api_client.api.default import post_featureview
from feature_store_api_client.client import Client
from feature_store_api_client.models import (
    Entity,
    Feature,
    FeatureViewRequest,
    FeatureViewRequestTags,
    UpsertFeatureViewsRequest,
)
from feature_store_api_client.types import Response

from .auth import AuthenticatedClient

AWS_CREDENTIALS_DEFAULT_LOCATION = "/var/lib/domino/home/.aws/credentials"
AWS_SHARED_CREDENTIALS_FILE = "AWS_SHARED_CREDENTIALS_FILE"


class DominoError(Exception):
    """Base exception for known errors."""


class ServerException(Exception):
    """This exception is raised when the FeatureStore server rejects a request."""

    def __init__(self, message: str, server_msg: str):
        self.message = message
        self.server_msg = server_msg


@define
class FeatureStoreClient:
    """API client and bindings."""

    client: Client = field(init=False, repr=False)

    api_key: Optional[str] = field(factory=lambda: os.getenv("DOMINO_USER_API_KEY"))
    token_file: Optional[str] = field(factory=lambda: os.getenv("DOMINO_TOKEN_FILE"))

    def __attrs_post_init__(self):
        domino_host = os.getenv("DOMINO_API_HOST", os.getenv("DOMINO_USER_HOST", ""))

        self.client = cast(
            Client,
            AuthenticatedClient(
                base_url=f"{domino_host}/featurestore",
                api_key=self.api_key,
                token_file=self.token_file,
                headers={"Accept": "application/json"},
            ),
        )

    def post_feature_views(self, feature_views):
        request = UpsertFeatureViewsRequest(feature_views=feature_views)
        response = post_featureview.sync_detailed(
            client=self.client,
            json_body=request,
        )

        if response.status_code != 200:
            _raise_response_exn(response, "could not create Feature Views")

        return True


@click.group()
def cli():
    """Click group for feature store commands."""
    click.echo("⭐ Domino FeatureStore CLI tool ⭐")


@cli.command()
@click.option(
    "--chdir",
    "-c",
    help="Switch to a different feature repository directory before syncing.",
)
@click.option(
    "--feature-store-yaml",
    help="Override the directory where the CLI should look for the feature_store.yaml file.",
)
@click.option(
    "--skip-source-validation",
    is_flag=True,
    help="Don't validate the data sources by checking for that the tables exist.",
)
def sync(
    chdir: Optional[str], feature_store_yaml: Optional[str], skip_source_validation: bool
) -> None:
    """Run feast apply and persist the updated feature view information into Mongo"""

    client = FeatureStoreClient()

    # Run `feast apply`
    # note: this command must be run in `feature_repo` directory of the project folder
    repo = Path.cwd() if chdir is None else Path(chdir).absolute()
    fs_yaml_file = (
        Path(feature_store_yaml).absolute() if feature_store_yaml else repo / "feature_store.yaml"
    )
    cli_check_repo(repo, fs_yaml_file)

    repo_config = load_repo_config(repo, fs_yaml_file)

    try:
        apply_total(repo_config, repo, skip_source_validation)
    except FeastProviderLoginError as e:
        print(str(e))

    # Persist updated feature view information into Mongo
    os.path.basename(os.path.normpath(repo))
    feature_store = feast.FeatureStore(repo)
    feature_views = feature_store.list_feature_views()

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

    client.post_feature_views(request_input)
    print(f"Feature Views successfully synced.")


def _get_project_id() -> Optional[str]:
    return os.getenv("DOMINO_PROJECT_ID")


def _raise_response_exn(response: Response, msg: str):
    try:
        response_json = json.loads(response.content.decode("utf8"))
        server_msg = response_json.get("message")
    except Exception:
        server_msg = None

    raise ServerException(msg, server_msg)

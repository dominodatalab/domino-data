"""Feature Store module."""
from typing import Dict, List, Optional, cast

import configparser
import os
import uuid
from pathlib import Path

import boto3
import click
import feast
from attrs import define, field

from feature_store_api_client.api.default import post_feature_store_name
from feature_store_api_client.client import Client
from feature_store_api_client.models import (
    BatchSource,
    CreateFeatureStoreRequest,
    Entity,
    Feature,
    FeatureStore,
    FeatureView,
    FeatureViewTags,
    StoreLocation,
)

from .auth import AuthenticatedClient

AWS_CREDENTIALS_DEFAULT_LOCATION = "/var/lib/domino/home/.aws/credentials"
AWS_SHARED_CREDENTIALS_FILE = "AWS_SHARED_CREDENTIALS_FILE"


class DominoError(Exception):
    """Base exception for known errors."""


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

    def post_feature_store(
        self, name: str, feature_views: List[feast.FeatureView], bucket: str, region: str
    ) -> FeatureStore:
        """Create a feature store in Domino.

        Args:
            name: name of the feature store to create
            feature_views: list of feature views to create store with
            bucket: bucket to store registry file
            region: region of bucket

        Returns:
            Domino Feature Store entity

        Raises:
            Exception: if the response from Domino is not successful
        """

        aws_cred_dict = _get_aws_credentials(AWS_SHARED_CREDENTIALS_FILE)
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_cred_dict["aws_access_key_id"],
            aws_secret_access_key=aws_cred_dict["aws_secret_access_key"],
        )
        resource_id = str(uuid.uuid4())
        feature_store_folder = Path("/" + name).joinpath(resource_id)
        # upload yaml file
        s3_client.upload_file(
            Filename=str(Path.cwd().joinpath("feature_store.yaml")),
            Bucket=bucket,
            Key=feature_store_folder,
        )
        # upload registry file
        s3_client.upload_file(
            Filename=str(Path.cwd().joinpath("data/registry.db")),
            Bucket=bucket,
            Key=feature_store_folder,
        )

        domino_feature_views = [
            FeatureView(
                name=fv.name,
                ttl=fv.ttl,
                features=[
                    Feature(
                        name=feature.name,
                        dtype=str(feature.dtype),
                    )
                    for feature in fv.features
                ],
                batch_source=BatchSource(
                    name=fv.batch_source.name,
                    data_source=fv.batch_source.get_table_query_string(),
                    event_timestamp_column=fv.batch_source.event_timestamp_column,
                    created_timestamp_column=fv.batch_source.created_timestamp_column,
                    date_partition_column=fv.batch_source.date_partition_column,
                ),
                entities=[
                    Entity(name=entity.name, join_key=entity.join_key, value_type=entity.value_type)
                    for entity in fv.entities
                ],
                store_location=StoreLocation(bucket=bucket, region=region, resource_id=resource_id),
                tags=FeatureViewTags.from_dict(fv.tags),
            )
            for fv in feature_views
        ]
        request = CreateFeatureStoreRequest(
            name=name,
            project_id=_get_project_id(),
            feature_views=domino_feature_views,
        )
        response = post_feature_store_name.sync_detailed(
            name,
            client=self.client,
            json_body=request,
        )

        if response.status_code == 200:
            return cast(FeatureStore, response.parsed)

        raise Exception(response.content)

@click.option(
    "--quickstart_yaml", prompt="Enter your feature store project name", help="Initialize a feature store YAML."
)
def quickstart_yaml(feature_store_name) -> None:
    # currently supporting only local provider
    valid_online_stores = ["sqlite", "redis", "datastore"]
    provider = click.prompt('Please enter your provider', type=str)
    online_store_type = ""
    while online_store_type not in valid_online_stores:
        online_store_type = click.prompt('Please enter your online store type', type=str).lower()

    match online_store_type:
        case "sqlite":
            return "Bad request"
        case "redis":
            return "Not found"
        case "datastore":
            return "I'm a teapot"
        case _:
            return "Something's wrong with the internet"
    if (online_store_type)


@click.option(
    "--chdir",
    "-c",
    help="Switch to a different feature repository directory before syncing.",
)
@click.option(
    "--name", prompt="Name of your Feature Store", help="Unique name for your feature store"
)
def sync(name: str, chdir: Optional[str]) -> None:
    """Sync information in registry.db with Domino"""
    repo = Path.cwd() if chdir is None else Path(chdir).absolute()
    feature_store = feast.FeatureStore(repo)
    feature_views = feature_store.list_feature_views()

    client = FeatureStoreClient()
    client.post_feature_store(name, feature_views)
    print(f"Feature store '{name}' successfully synced with Domino.")


def _get_project_id() -> Optional[str]:
    return os.getenv("DOMINO_PROJECT_ID")


def _get_aws_credentials(location: str) -> Dict[str, str]:
    aws_config = configparser.RawConfigParser()
    aws_config.read(os.getenv(location, AWS_CREDENTIALS_DEFAULT_LOCATION))
    if not aws_config or not aws_config.sections():
        raise DominoError("AWS credentials file does not exist or does not contain profiles")
    profile = aws_config.sections().pop(0)

    return dict(
        aws_access_key_id=aws_config.get(profile, "aws_access_key_id"),
        aws_secret_access_key=aws_config.get(profile, "aws_secret_access_key"),
    )

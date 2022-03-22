"""Feature Store module."""
from typing import List, Optional, cast

import os
from datetime import datetime
from pathlib import Path

import bson
import click
import pytz
from attrs import define, field

from feature_store_api_client.api.default import get_feature_store_name, post_feature_store_name
from feature_store_api_client.client import Client
from feature_store_api_client.models import (
    BatchSource,
    BatchSourceSourceOptions,
    CreateFeatureStoreRequest,
    Entity,
    Feature,
    FeatureStore,
    FeatureView,
    FeatureViewTags,
)

from .auth import AuthenticatedClient

IMPORT_ERROR_MESSAGE = (
    "`feast` is not installed.\n\n"
    "Please install feast via pip or your preferred package manager:\n\n"
    "    python -m pip install feast"
)


try:
    import feast
except ImportError as e:
    raise ImportError(IMPORT_ERROR_MESSAGE) from e


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

    def get_feature_store(self, name: str) -> FeatureStore:
        """Get a feature store by name.

        Args:
            name: name of the feature store to create

        Returns:
            Domino Feature Store entity

        Raises:
            Exception: if the response from Domino is not successful
        """
        response = get_feature_store_name.sync_detailed(name, client=self.client)
        if response.status_code == 200:
            return cast(FeatureStore, response.parsed)

        raise Exception(response.content)

    def post_feature_store(
        self,
        name: str,
        feature_views: List[feast.FeatureView],
    ) -> FeatureStore:
        """Create a feature store in Domino.

        Args:
            name: name of the feature store to create
            feature_views: list of feature views to create store with

        Returns:
            Domino Feature Store entity

        Raises:
            Exception: if the response from Domino is not successful
        """
        domino_feature_views = [
            FeatureView(
                name=fv.name,
                ttl=fv.ttl.microseconds,
                features=[
                    Feature(
                        name=feature.name,
                        dtype=str(feature.dtype),
                    )
                    for feature in fv.features
                ],
                batch_source=BatchSource(
                    data_source_type=fv.batch_source.get_table_query_string(),
                    event_timestamp_column=fv.batch_source.event_timestamp_column,
                    source_options=BatchSourceSourceOptions.from_dict(
                        {
                            "query": fv.batch_source.get_table_query_string(),
                            "table_name": fv.batch_source.name,
                        }
                    ),
                    created_timestamp_column=fv.batch_source.created_timestamp_column,
                ),
                entities=[Entity(name=entity, value_type="") for entity in fv.entities],
                tags=FeatureViewTags.from_dict(fv.tags),
            )
            for fv in feature_views
        ]
        domino_run_id = os.getenv("DOMINO_RUN_ID", "6238f45cf6d751a45f6d0539")
        feature_store = FeatureStore(
            id=str(bson.ObjectId()),
            project_id=domino_run_id,
            name=name,
            feature_views=domino_feature_views,
            creation_time=datetime.now(pytz.utc),
            description=f"Feast feature store: {name}",
        )
        request = CreateFeatureStoreRequest(
            name=name,
            project_id=domino_run_id,
            feature_store=feature_store,
            description=f"Domino feature store: {name}",
        )
        response = post_feature_store_name.sync_detailed(
            name,
            client=self.client,
            json_body=request,
        )

        if response.status_code == 200:
            return cast(FeatureStore, response.parsed)

        raise Exception(response.content)


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
    "--name", prompt="Name of your Feature Store", help="Unique name for your feature store"
)
def sync(name: str, chdir: Optional[str]) -> None:
    """Sync information in registry.db with Domino"""
    repo = Path.cwd() if chdir is None else Path(chdir).absolute()
    feature_store = feast.FeatureStore(repo)
    feature_views = feature_store.list_feature_views()

    client = FeatureStoreClient()
    client.post_feature_store(name, feature_views)
    print(f"store '{name}' sucessfully synced.")

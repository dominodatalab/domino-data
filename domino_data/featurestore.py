"""Feature Store module."""
from typing import Dict, List, Optional, cast

import configparser
import os
import uuid
from pathlib import Path

import boto3
import click
import feast
import yaml
from attrs import define, field
from feast.repo_operations import init_repo

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


@click.group()
def cli():
    """Click group for feature store commands."""
    click.echo("⭐ Domino FeatureStore CLI tool ⭐")


@cli.command()
@click.argument("PROJECT_DIRECTORY", required=False)
@click.option("--minimal", "-m", is_flag=True, help="Create an empty project repository")
@click.option(
    "--template",
    "-t",
    type=click.Choice(
        ["local", "gcp", "aws", "snowflake", "spark", "postgres", "hbase"],
        case_sensitive=False,
    ),
    help="Specify a template for the created project",
    default="local",
)
def init(project_directory, minimal: bool, template: str) -> None:
    """Set up a Feast feature store repository and save the location info for the feature store metadata storage"""
    project_directory_name = __run__feast__init(project_directory, minimal, template)

    # remove initial yaml file
    path_to_yaml = Path.cwd() / project_directory_name / "feature_store.yaml"
    os.remove((path_to_yaml))

    # generate yaml file
    __generate_yaml(path_to_yaml, project_directory_name)

    # datasource creation
    datasource = __create_datasource(project_directory_name)

    # feature store creation
    request = CreateFeatureStoreRequest(
        name=name,
        project_id=_get_project_id(),
        datasource_id=datasource.id,
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


def __run__feast__init(project_directory, minimal: bool, template: str):
    if not project_directory:
        project_directory = feast.repo_operations.generate_project_name()

    if minimal:
        template = "minimal"

    feast.repo_operations.init_repo(project_directory, template)

    return project_directory


def __create_datasource(feature_store_name):
    bucket = click.prompt("Input the S3 bucket to store your feature store metadata")
    region = click.prompt("Input the region associated with your S3 bucket")
    access_key = click.prompt("Input the access key associated with your S3 bucket")
    secret_key = click.prompt("Input the secret key associated with your S3 bucket")
    datasource_name = feature_store_name + "-metadata"
    # TODO: figure out how to deal with permissioning....
    request = CreateDatasourceRequest(
        name=datasource_name,
        datasource_type="S3",
        bucket=bucket,
        region=region,
        credential_type="Individual",
        auth_type="AWSIAMBasic",
        engine_type="Domino",
        visible_credential=access_key,
        secret_credential=secret_key,
        is_everyone=True,
        user_ids=[],
    )
    response = post_datasource.sync_detailed(
        client=self.client,
        json_body=request,
    )

    if response.status_code == 200:
        return cast(DatasourceDto, response.parsed)

    raise Exception(response.content)


def __generate_yaml(path, project_directory_name):
    meta_fields = {
        "Enter your online store type (SQLite, Redis, Datastore)": "online_store",
        "Enter your offline store type (File, BigQuery)": "offline_store",
    }
    fields = {
        "Enter your online store type (SQLite, Redis, Datastore)": "type",
        "Enter your offline store type (File, BigQuery)": "type",
        "Enter your SQLite path": "path",
        "Enter your Redis type (skip if SSL not enabled)": "redis_type",
        "Enter your Redis connection string": "connection_string",
        "Enter your Datastore project ID": "project_id",
        "Enter your Datastore namespace": "namespace",
        "Enter your BigQuery dataset name": "dataset",
    }
    optional_prompts = {"Enter your Redis type (skip if SSL not enabled)"}
    question_bank = {
        "Enter your online store type (SQLite, Redis, Datastore)": {
            "sqlite": ["Enter your SQLite path"],
            "redis": [
                "Enter your Redis type (skip if SSL not enabled)",
                "Enter your Redis connection string",
            ],
            "datastore": ["Enter your Datastore project ID", "Enter your Datastore namespace"],
        },
        "Enter your offline store type (File, BigQuery)": {
            "file": [],
            "bigquery": ["Enter your BigQuery dataset name"],
        },
    }

    initial_dict = {
        "project": project_directory_name,
        "registry": "data/registry.db",
        "provider": "local",
    }
    for type_question, types_dict in question_bank.items():
        vessel = {}
        type_result = click.prompt(type_question)
        store_dict = {fields[type_question]: type_result}
        store_dict.update(vessel)
        vessel = store_dict

        for online_store_type, online_store_type_questions in types_dict.items():
            if type_result.lower() != online_store_type:
                continue

            for question in online_store_type_questions:
                if question in optional_prompts:
                    sub_question_result = click.prompt(question, default="")
                else:
                    sub_question_result = click.prompt(question)

                if sub_question_result:
                    result_dict = {fields[question]: sub_question_result}
                    vessel.update(result_dict)
        final_dict = {meta_fields[type_question]: vessel}
        initial_dict.update(final_dict)
        final_dict = initial_dict

    with open(path, "w") as file:
        documents = yaml.dump(final_dict, file, default_flow_style=False, sort_keys=False)


# run feast init
# take the inputted parameters to fill in the yaml -> this will be click prompts
# save the data source information - take in bucket, region, creds? maybe can take from the environment
# create a data source with the information and then take the ID and persist a feature store entity with the ID saved on init


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

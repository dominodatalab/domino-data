"""Feature Store module."""
from typing import Optional, cast

import os
from pathlib import Path

import click
import feast
import yaml
from attrs import define, field
from feast.repo_operations import init_repo

# from datasource_api_client.api.datasource import post_datasource
from feature_store_api_client.api.default import post_feature_store_name
from feature_store_api_client.client import Client
from feature_store_api_client.models import CreateFeatureStoreRequest, FeatureStore

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

    def post_feature_store(self, name, bucket, region, access_key, secret_key):
        request = CreateFeatureStoreRequest(
            name=name,
            project_id=_get_project_id(),
            bucket=bucket,
            region=region,
            visible_credential=access_key,
            secret_credential=secret_key,
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
    """Set up a Feast repository and persist info for feature store metadata storage"""
    project_directory_name = __run__feast__init(project_directory, minimal, template)

    # remove initial yaml file
    path_to_yaml = Path.cwd() / project_directory_name / "feature_store.yaml"
    os.remove((path_to_yaml))

    # generate yaml file
    __generate_yaml(path_to_yaml, project_directory_name)

    # feature store creation
    bucket = click.prompt("Input the S3 bucket to store your feature store metadata")
    region = click.prompt("Input the region associated with your S3 bucket")
    access_key = click.prompt("Input the access key associated with your S3 bucket")
    secret_key = click.prompt("Input the secret key associated with your S3 bucket")

    client = FeatureStoreClient()
    client.post_feature_store(project_directory_name, bucket, region, access_key, secret_key)
    print(f"Feature store '{project_directory_name}' successfully initialized with Domino.")


def __run__feast__init(project_directory, minimal: bool, template: str):
    if not project_directory:
        project_directory = feast.repo_operations.generate_project_name()

    if minimal:
        template = "minimal"

    init_repo(project_directory, template)

    return project_directory


def __generate_yaml(path, project_directory_name):
    fields = {
        "Enter your DynamoDB region": "region",
        "Enter your Redshift cluster ID": "cluster_id",
        "Enter your Redshift region": "region",
        "Enter your Redshift user": "user",
        "Enter your Redshift database": "database",
        "Enter your S3 staging location": "s3_staging_location",
        "Enter your IAM role": "iam_role",
    }

    online_store_prompts = ["Enter your DynamoDB region"]
    offline_store_prompts = [
        "Enter your Redshift cluster ID",
        "Enter your Redshift region",
        "Enter your Redshift user",
        "Enter your Redshift database",
        "Enter your S3 staging location",
        "Enter your IAM role",
    ]

    final_dict = {
        "project": project_directory_name,
        "registry": "data/registry.db",
        "provider": "aws",
    }

    online_store_vessel = {"type": "dynamodb"}
    for question in online_store_prompts:
        answer = click.prompt(question)
        store_dict = {fields[question]: answer}
        online_store_vessel.update(store_dict)

    online_store_section = {"online_store": online_store_vessel}

    offline_store_vessel = {"type": "redshift"}
    for question in offline_store_prompts:
        answer = click.prompt(question)
        store_dict = {fields[question]: answer}
        offline_store_vessel.update(store_dict)

    offline_store_section = {"offline_store": offline_store_vessel}

    final_dict.update(online_store_section)
    final_dict.update(offline_store_section)

    with open(path, "w") as file:
        yaml.dump(final_dict, file, default_flow_style=False, sort_keys=False)


def _get_project_id() -> Optional[str]:
    return os.getenv("DOMINO_PROJECT_ID")

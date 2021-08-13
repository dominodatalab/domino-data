from collections.abc import Mapping
from typing import Optional
import os

import pandas as pd

from trainingset import model

from training_set_api_client import Client
from training_set_api_client.models.create_training_set_version_request import CreateTrainingSetVersionRequest
from training_set_api_client.models.create_training_set_version_request_metadata import CreateTrainingSetVersionRequestMetadata
from training_set_api_client.api.default import post_training_set_name_version


def get_training_set(
        name: str,
) -> model.TrainingSet:
    pass


def get_training_sets(
    project_id: Optional[str] = None,  # the hex project_id?
    asc: int = 1,
    offset: int = 0,
    limit: int = 0,
) -> [model.TrainingSet]:
    # find all training sets user has access to with matching all fields

    pass


def update_training_set(
    training_set: model.TrainingSet, ) -> model.TrainingSet:
    # server updates modifiable fields, including users

    pass


def delete_training_set(name: str) -> bool:
    # deletes a trainingset.
    # only if no it contains no versions? (user needs to delete them first)

    pass


def create_training_set_version(
    version: model.TrainingSetVersion,
    df: pd.DataFrame,
    project_owner: Optional[str],
    project_name: Optional[str],
) -> model.TrainingSetVersion:

    if not project_owner:
        project_owner = os.getenv("DOMINO_PROJECT_OWNER")

    if not project_name:
        project_owner = os.getenv("DOMINO_PROJECT_NAME")

    if not project_owner or not project_owner:
        raise ("project owner and name are required")

    created = post_training_set_name_version.sync(
        client=_get_client(),
        training_set_name=version.training_set,
        json_body=CreateTrainingSetVersionRequest(
            project_owner_username=project_owner,
            project_name=project_name,
            timestamp_column=version.timestamp_column,
            independent_vars=version.independent_vars,
            target_vars=version.target_vars,
            continuous_vars=version.continuous_vars,
            categorical_vars=version.categorical_vars,
            ordinal_vars=version.ordinal_vars,
            metadata=CreateTrainingSetVersionRequestMetadata.from_dict(
                version.metadata),
            name=version.name,
            description=version.description,
        ))

    print(created)

    # creates TrainingSet if it does not already exist
    # creates a TrainingSetVersion record
    # gets pre-signed upload url
    # uploads data
    # updates TrainingSetVersion record to mark as complete

    return created


def get_training_set_version(id: str) -> model.TrainingSetVersion:
    # gets training_set by version id

    pass


def get_training_set_version_df(id: str) -> pd.DataFrame:
    # gets dataframe for a TrainingSetVersion

    pass


def update_training_set_version(
    training_set_version: model.TrainingSetVersion
) -> model.TrainingSetVersion:
    # submits an update request to server, server will reject if an immutable
    # field is modified

    pass


def delete_training_set_version(training_set_version_id: str) -> bool:
    # server deletes object and marks record as deleted

    pass


def get_training_set_versions(
    training_set_name: Optional[str] = None,
    project_id: Optional[str] = None,  # is this owner/project or hex?
    metadata: Mapping[str, str] = {},
    asc: int = 1,
    offset: int = 0,
    limit: int = 0,
) -> [model.TrainingSetVersion]:
    # finds records with all specified fields that user has access to

    pass


# XXX use AutenticatedClient
def _get_client() -> Client:
    return Client(base_url="http://minikube.local.domino.tech/trainingset").with_headers({
        "X-Domino-Api-Key": "a0cfa2476d58c655df4c8e54acf1b483b80c83d624d770d4d4503edf22198e6a",  # XXX
    })

from typing import List, Mapping, Optional

import os

import pandas as pd

from datasdk.trainingset import model  # XXX rename model
from training_set_api_client import Client
from training_set_api_client.api.default import post_training_set_name_version
from training_set_api_client.models.create_training_set_version_request import (
    CreateTrainingSetVersionRequest,
)
from training_set_api_client.models.create_training_set_version_request_meta import (
    CreateTrainingSetVersionRequestMeta,
)
from training_set_api_client.models.monitoring_meta import MonitoringMeta


def get_training_set(name: str) -> model.TrainingSet:
    """Get a TrainingSet by name"""

    pass


def list_training_sets(
    filter: model.TrainingSetFilter = {},
    asc: int = 1,
    offset: int = 0,
    limit: int = 10000,
) -> model.TrainingSet:
    """List training sets

    Keyword arguments:
    filter -- a filter
    asc -- sort order by creation time, 1 for ascending -1 for descending
    offset -- offset
    limit -- limit
    """

    pass


def update_training_set(
    training_set: model.TrainingSet,
) -> model.TrainingSet:
    """Updates a TrainingSet

    Keyword arguments:
    training_set -- updated TrainingSet
    """

    pass


def delete_training_set(name: str, force: bool = False) -> bool:
    """Delete a TrainingSet.

    Will only delete if the TrainingSet has no versions unless force is used.

    Keyword arguments:
    name -- name of the TrainingSet
    force -- will delete all versions if true
    """

    # deletes a trainingset.
    # only if no it contains no versions? (user needs to delete them first)

    pass


def create_training_set_version(
    training_set_name: str,
    df: pd.DataFrame,
    name: Optional[str] = None,
    description: Optional[str] = None,
    key_columns: List[str] = [],
    target_columns: List[str] = [],
    exclude_columns: List[str] = [],
    monitoring_meta: model.MonitoringMeta = model.MonitoringMeta(),
    meta: Mapping[str, str] = {},
    **kwargs,
) -> model.TrainingSetVersion:
    """Create a TrainingSetVersion

    Keyword arguments:
    training_set_name -- name of the TrainingSet this version belongs to
    df -- a DataFrame holding the data
    training_set_name -- name of the TrainingSet this version belongs to
    name -- name of this version
    description -- description of this version
    key_columns -- names of columns that represent IDs for retrieving features
    target_columns -- target variables for prediction
    exclude_columns -- columns to exclude when generating the training DataFrame
    monitoring_meta -- monitoring specific metadata
    meta -- user defined metadata
    """

    project_name = kwargs.get("project_name")
    if project_name:
        (project_owner, project_name) = project_name.split("/")
    else:
        project_owner = os.getenv("DOMINO_PROJECT_OWNER")
        project_name = os.getenv("DOMINO_PROJECT_NAME")

    if not project_owner or not project_owner:
        raise ("project owner and name are required")

    # XXX fixme!
    created = post_training_set_name_version.sync(
        client=_get_client(),
        training_set_name=training_set_name,
        json_body=CreateTrainingSetVersionRequest(
            project_owner_username=project_owner,
            project_name=project_name,
            key_columns=key_columns,
            target_columns=target_columns,
            exclude_columns=exclude_columns,
            monitoring_meta=MonitoringMeta(
                timestamp_columns=meta.get("timestamp_columns", []),
                categorical_columns=meta.get("categorical_columns", []),
                ordinal_columns=meta.get("ordinal_columns", []),
            ),
            meta=CreateTrainingSetVersionRequestMeta.from_dict(meta),
            name=name,
            description=description,
        ),
    )

    print(created)

    # creates TrainingSet if it does not already exist
    # creates a TrainingSetVersion record
    # gets pre-signed upload url
    # uploads data
    # updates TrainingSetVersion record to mark as complete

    return created


def get_training_set_version(training_set_name: str, number: int) -> model.TrainingSetVersion:
    """Gets a TrainingSetVersion by version number

    Keyword arguments:
    training_set_name -- name of the TrainingSet
    number -- version number
    """

    pass


def update_training_set_version(version: model.TrainingSetVersion) -> model.TrainingSetVersion:
    """Updates this TrainingSetVersion.

    Keyword arguments:
    version -- TrainingSetVersion to update
    """

    pass


def delete_training_set_version(training_set_version: model.TrainingSetVersion) -> bool:
    """Deletes a TrainingSetVersion.

    Keyword arguments:
    version -- TrainingSetVersion to delete
    """

    pass


def list_training_set_versions(
    filter: model.TrainingSetVersionFilter = {},
    asc: int = 1,
    offset: int = 0,
    limit: int = 0,
) -> [model.TrainingSetVersion]:
    """List training sets

    Keyword arguments:
    filter -- a filter
    asc -- sort order by creation time, 1 for ascending -1 for descending
    offset -- offset
    limit -- limit
    """

    pass


# XXX use AutenticatedClient
def _get_client() -> Client:
    return Client(base_url="http://minikube.local.domino.tech/trainingset").with_headers(
        {
            "X-Domino-Api-Key": "ef448e42f702b95a53c94b8e04dfec4ef1ea6d196ac7ac9b4196bc9322adf2ec",  # XXX
        }
    )

from typing import List, Mapping, Optional

import os

import pandas as pd

from datasdk.trainingset import model  # XXX rename model
from training_set_api_client import Client
from training_set_api_client.api.default import (
    delete_training_set_name,
    delete_training_set_name_number,
    get_training_set_name,
    get_training_set_name_number,
    post_find,
    post_training_set_name,
    post_version_find,
    put_training_set_name,
    put_training_set_name_number,
)
from training_set_api_client.models import (
    CreateTrainingSetVersionRequest,
    CreateTrainingSetVersionRequestMeta,
    MonitoringMeta,
    TrainingSet,
    TrainingSetFilter,
    TrainingSetFilterMeta,
    TrainingSetVersion,
    TrainingSetVersionFilter,
    TrainingSetVersionFilterMeta,
    TrainingSetVersionFilterTrainingSetMeta,
    UpdateTrainingSetRequest,
    UpdateTrainingSetRequestMeta,
    UpdateTrainingSetVersionRequest,
    UpdateTrainingSetVersionRequestMeta,
)
from training_set_api_client.types import Response


def get_training_set(name: str) -> model.TrainingSet:
    """Get a TrainingSet by name"""

    response = get_training_set_name.sync_detailed(
        client=_get_client(),
        training_set_name=name,
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not get TrainingSet")

    return _to_TrainingSet(response.parsed)


def list_training_sets(
    project_name: Optional[str] = None,
    owner_name: Optional[str] = None,
    meta: Mapping[str, str] = {},
    asc: bool = True,
    offset: int = 0,
    limit: int = 10000,
) -> model.TrainingSet:
    """List training sets

    Keyword arguments:
    project_name -- the project name (e.g. gmatev/quick_start)
    owner_name -- the TrainingSet's owner (e.g. gmatev)
    meta -- match metadata key-value pairs
    asc -- sort order by creation time, 1 for ascending -1 for descending
    offset -- offset
    limit -- limit
    """

    response = post_find.sync_detailed(
        client=_get_client(),
        json_body=TrainingSetFilter(
            project_name=project_name,
            owner_name=owner_name,
            meta=TrainingSetFilterMeta.from_dict(meta),
        ),
        offset=offset,
        limit=limit,
        asc=asc,
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not list TrainingSets")

    return [_to_TrainingSet(ts) for ts in response.parsed]


def update_training_set(
    updated: model.TrainingSet,
) -> model.TrainingSet:
    """Updates a TrainingSet

    Keyword arguments:
    training_set -- updated TrainingSet
    """

    response = put_training_set_name.sync_detailed(
        training_set_name=updated.name,
        client=_get_client(),
        json_body=UpdateTrainingSetRequest(
            owner_name=updated.owner_name,
            collaborator_names=updated.collaborator_names,
            meta=UpdateTrainingSetRequestMeta.from_dict(updated.meta),
            description=updated.description,
        ),
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not update TrainingSets")

    return _to_TrainingSet(response.parsed)


def delete_training_set(name: str) -> bool:
    """Delete a TrainingSet.

    Will only delete if the TrainingSet has no versions.

    Keyword arguments:
    name -- name of the TrainingSet
    """

    response = delete_training_set_name.sync_detailed(training_set_name=name, client=_get_client())

    if response.status_code != 200:
        _raise_response_exn(response, "could not delete TrainingSet")

    return True


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

    response = post_training_set_name.sync_detailed(
        client=_get_client(),
        training_set_name=training_set_name,
        json_body=CreateTrainingSetVersionRequest(
            project_owner_username=project_owner,
            project_name=project_name,
            key_columns=key_columns,
            target_columns=target_columns,
            exclude_columns=exclude_columns,
            monitoring_meta=MonitoringMeta(
                timestamp_columns=monitoring_meta.get("timestamp_columns", []),
                categorical_columns=monitoring_meta.get("categorical_columns", []),
                ordinal_columns=monitoring_meta.get("ordinal_columns", []),
            ),
            meta=CreateTrainingSetVersionRequestMeta.from_dict(meta),
            name=name,
            description=description,
        ),
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not create TrainingSetVersion")

    # TODO:
    # gets pre-signed upload url
    # uploads data
    # updates TrainingSetVersion record to mark as complete

    return _to_TrainingSetVersion(response.parsed)


def get_training_set_version(training_set_name: str, number: int) -> model.TrainingSetVersion:
    """Gets a TrainingSetVersion by version number

    Keyword arguments:
    training_set_name -- name of the TrainingSet
    number -- version number
    """

    response = get_training_set_name_number.sync_detailed(
        client=_get_client(),
        training_set_name=training_set_name,
        number=number,
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not get TrainingSetVersion")

    return _to_TrainingSetVersion(response.parsed)


def update_training_set_version(tsv: model.TrainingSetVersion) -> model.TrainingSetVersion:
    """Updates this TrainingSetVersion.

    Keyword arguments:
    version -- TrainingSetVersion to update
    """

    response = put_training_set_name_number.sync_detailed(
        training_set_name=tsv.training_set_name,
        number=tsv.number,
        client=_get_client(),
        json_body=UpdateTrainingSetVersionRequest(
            key_columns=tsv.key_columns,
            target_columns=tsv.target_columns,
            exclude_columns=tsv.exclude_columns,
            monitoring_meta=MonitoringMeta(
                timestamp_columns=tsv.monitoring_meta.get("timestamp_columns", []),
                categorical_columns=tsv.monitoring_meta.get("categorical_columns", []),
                ordinal_columns=tsv.monitoring_meta.get("ordinal_columns", []),
            ),
            meta=UpdateTrainingSetVersionRequestMeta.from_dict(tsv.meta),
            pending=tsv.pending,
            description=tsv.description,
        ),
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not update TrainingSetVersion")

    return _to_TrainingSetVersion(response.parsed)


def delete_training_set_version(training_set_name: str, number: int) -> bool:
    """Deletes a TrainingSetVersion.

    Keyword arguments:
    version -- TrainingSetVersion to delete
    """

    response = delete_training_set_name_number.sync_detailed(
        training_set_name=training_set_name,
        number=number,
        client=_get_client(),
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not delete TrainingSetVersion")

    return True


def list_training_set_versions(
    project_name: Optional[str] = None,
    meta: Mapping[str, str] = {},
    training_set_name: Optional[str] = None,
    training_set_meta: Mapping[str, str] = {},
    asc: bool = True,
    offset: int = 0,
    limit: int = 10000,
) -> [model.TrainingSetVersion]:
    """List training sets

    Keyword arguments:
    project_name -- the project name (e.g. gmatev/quick_start)
    meta -- version metadata
    training_set_name -- training set name
    training_set_meta -- training set meta data
    asc -- sort order by creation time, 1 for ascending -1 for descending
    offset -- offset
    limit -- limit
    """

    response = post_version_find.sync_detailed(
        client=_get_client(),
        json_body=TrainingSetVersionFilter(
            training_set_meta=TrainingSetVersionFilterTrainingSetMeta.from_dict(
                training_set_meta,
            ),
            meta=TrainingSetVersionFilterMeta.from_dict(meta),
            project_name=project_name,
            training_set_name=training_set_name,
        ),
        offset=offset,
        limit=limit,
        asc=asc,
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not find TrainingSetVersion")

    return [_to_TrainingSetVersion(tsv) for tsv in response.parsed]


def _get_client() -> Client:
    # TODO support tokens
    host = os.getenv("DOMINO_USER_HOST")
    api_key = os.getenv("DOMINO_USER_API_KEY")
    return Client(base_url=f"{host}/trainingset").with_headers(
        {
            "X-Domino-Api-Key": api_key,
        }
    )


def _to_TrainingSet(ts: TrainingSet) -> model.TrainingSet:
    return model.TrainingSet(
        name=ts.name,
        description=ts.description,
        meta=ts.meta.to_dict(),
        collaborator_names=ts.collaborator_names,
        owner_name=ts.owner_name,
        project_id=ts.project_id,
    )


def _to_TrainingSetVersion(tsv: TrainingSetVersion) -> model.TrainingSetVersion:
    return model.TrainingSetVersion(
        training_set_name=tsv.training_set_name,
        number=tsv.number,
        description=tsv.description,
        key_columns=tsv.key_columns,
        target_columns=tsv.target_columns,
        exclude_columns=tsv.exclude_columns,
        monitoring_meta=tsv.monitoring_meta.to_dict(),
        meta=tsv.meta.to_dict(),
        pending=tsv.pending,
    )


def _raise_response_exn(response: Response, msg: str):
    raise Exception(msg)

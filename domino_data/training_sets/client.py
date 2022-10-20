"""Domino TrainingSet client library."""


from typing import List, Mapping, Optional

import json
import os
import re
import shutil
from stat import S_IRGRP, S_IROTH, S_IRUSR, S_IWUSR, S_IXGRP, S_IXOTH, S_IXUSR

import pandas as pd

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

from ..auth import AuthenticatedClient
from ..training_sets import model

_trainingset_name_pat = re.compile("^[-A-Za-z0-9_]+$")


class ServerException(Exception):
    """This exception is raised when the TrainingSet server rejects a request."""

    def __init__(self, message: str, server_msg: str):
        self.message = message
        self.server_msg = server_msg


class SchemaMismatchException(Exception):
    """This exception is raised when the TrainingSet data columns do not match the metadata."""


def get_training_set(name: str) -> model.TrainingSet:
    """Get a TrainingSet by name.

    Args:
        name: Name of the training set.

    Returns:
        The TrainingSet, if found.

    """

    _validate_trainingset_name(name)

    response = get_training_set_name.sync_detailed(
        client=_get_client(),
        training_set_name=name,
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not get TrainingSet")

    return _to_TrainingSet(response.parsed)


def list_training_sets(
    meta: Optional[Mapping[str, str]] = None,
    asc: bool = True,
    offset: int = 0,
    limit: int = 10000,
) -> List[model.TrainingSet]:
    """Query training sets.

    Args:
        meta: Metadata key-value pairs to match.
        asc: Sort order by creation time, 1 for ascending -1 for descending.
        offset: Offset
        limit: Limit

    Returns:
        A list of matching TrainingSets.
    """

    if meta is None:
        meta = {}

    project_id = _get_project_id()

    response = post_find.sync_detailed(
        client=_get_client(),
        json_body=TrainingSetFilter(
            project_id=project_id,
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
    """Update a TrainingSet.

    Args:
        updated: Updated TrainingSet.

    Returns:
        The updated TrainingSet from the server.
    """

    _validate_trainingset_name(updated.name)

    response = put_training_set_name.sync_detailed(
        training_set_name=updated.name,
        client=_get_client(),
        json_body=UpdateTrainingSetRequest(
            meta=UpdateTrainingSetRequestMeta.from_dict(updated.meta),
            description=updated.description,
        ),
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not update TrainingSets")

    return _to_TrainingSet(response.parsed)


def delete_training_set(name: str) -> bool:
    """Delete a TrainingSet.

    **Note:** This deletes the TrainingSet only if it has no versions.

    Args:
        name: Name of the TrainingSet.

    Returns:
        True if TrainingSet was deleted.
    """

    _validate_trainingset_name(name)

    response = delete_training_set_name.sync_detailed(training_set_name=name, client=_get_client())

    if response.status_code != 200:
        _raise_response_exn(response, "could not delete TrainingSet")

    return True


def create_training_set_version(
    training_set_name: str,
    df: pd.DataFrame,
    description: Optional[str] = None,
    key_columns: Optional[List[str]] = None,
    target_columns: Optional[List[str]] = None,
    exclude_columns: Optional[List[str]] = None,
    monitoring_meta: Optional[model.MonitoringMeta] = None,
    meta: Optional[Mapping[str, str]] = None,
    **kwargs,
) -> model.TrainingSetVersion:
    """Create a TrainingSetVersion.

    Args:
        training_set_name: Name of the TrainingSet this version belongs to. ``training_set_name`` must
            be a string containing only alphanumeric characters in the basic Latin alphabet
            including dash and underscore: `[-A-Za-z_]`.
        df: A DataFrame holding the data.
        description: Description of this version.
        key_columns: Names of columns that represent IDs for retrieving features.
        target_columns: Target variables for prediction.
        exclude_columns: Columns to exclude when generating the training DataFrame.
        monitoring_meta: Monitoring specific metadata.
        meta: User defined metadata.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        The created TrainingSetVersion
    """

    if key_columns is None:
        key_columns = []

    if target_columns is None:
        target_columns = []

    if exclude_columns is None:
        exclude_columns = []

    if monitoring_meta is None:
        monitoring_meta = model.MonitoringMeta()

    if meta is None:
        meta = {}

    all_columns = list(df.columns)

    _validate_trainingset_name(training_set_name)

    _check_columns(
        all_columns,
        key_columns
        + target_columns
        + exclude_columns
        + monitoring_meta.timestamp_columns
        + monitoring_meta.categorical_columns
        + monitoring_meta.ordinal_columns,
    )

    project_id = _get_project_id()

    response = post_training_set_name.sync_detailed(
        client=_get_client(),
        training_set_name=training_set_name,
        json_body=CreateTrainingSetVersionRequest(
            project_id=project_id,
            key_columns=key_columns,
            target_columns=target_columns,
            exclude_columns=exclude_columns,
            all_columns=all_columns,
            monitoring_meta=MonitoringMeta(
                timestamp_columns=monitoring_meta.timestamp_columns,
                categorical_columns=monitoring_meta.categorical_columns,
                ordinal_columns=monitoring_meta.ordinal_columns,
            ),
            meta=CreateTrainingSetVersionRequestMeta.from_dict(meta),
            description=description,
        ),
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not create Training Set version")

    tsv = _to_TrainingSetVersion(response.parsed)

    os.makedirs(tsv.absolute_container_path)
    df.to_parquet(os.path.join(tsv.absolute_container_path, "data.parquet"))
    os.chmod(tsv.absolute_container_path, S_IRUSR | S_IRGRP | S_IROTH | S_IXUSR | S_IXGRP | S_IXOTH)

    tsv.pending = False
    return update_training_set_version(tsv)


def get_training_set_version(training_set_name: str, number: int) -> model.TrainingSetVersion:
    """Gets a TrainingSetVersion by version number.

    Args:
        training_set_name: Name of the TrainingSet.
        number: Version number.

    Returns:
        The requested TrainingSetVersion.
    """

    _validate_trainingset_name(training_set_name)

    response = get_training_set_name_number.sync_detailed(
        client=_get_client(),
        training_set_name=training_set_name,
        number=number,
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not get TrainingSetVersion")

    return _to_TrainingSetVersion(response.parsed)


def update_training_set_version(version: model.TrainingSetVersion) -> model.TrainingSetVersion:
    """Updates this TrainingSetVersion.

    Args:
        version: TrainingSetVersion to update.

    Returns:
        The updated TrainingSetVersion from the server.
    """

    _validate_trainingset_name(version.training_set_name)

    response = put_training_set_name_number.sync_detailed(
        training_set_name=version.training_set_name,
        number=version.number,
        client=_get_client(),
        json_body=UpdateTrainingSetVersionRequest(
            key_columns=version.key_columns,
            target_columns=version.target_columns,
            exclude_columns=version.exclude_columns,
            monitoring_meta=MonitoringMeta(
                timestamp_columns=version.monitoring_meta.timestamp_columns,
                categorical_columns=version.monitoring_meta.categorical_columns,
                ordinal_columns=version.monitoring_meta.ordinal_columns,
            ),
            meta=UpdateTrainingSetVersionRequestMeta.from_dict(version.meta),
            pending=version.pending,
            description=version.description,
        ),
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not update TrainingSetVersion")

    return _to_TrainingSetVersion(response.parsed)


def delete_training_set_version(training_set_name: str, number: int) -> bool:
    """Deletes a TrainingSetVersion.

    Args:
        training_set_name: Name of the TrainingSet.
        number: TrainingSetVersion number.

    Returns:
        True if TrainingSetVersion was deleted.
    """

    _validate_trainingset_name(training_set_name)

    tsv = get_training_set_version(training_set_name, number)

    response = delete_training_set_name_number.sync_detailed(
        training_set_name=training_set_name,
        number=number,
        client=_get_client(),
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not delete TrainingSetVersion")

    stat = os.stat(tsv.absolute_container_path)
    os.chmod(tsv.absolute_container_path, stat.st_mode | S_IWUSR)
    shutil.rmtree(tsv.absolute_container_path)

    return True


def list_training_set_versions(
    meta: Optional[Mapping[str, str]] = None,
    training_set_name: Optional[str] = None,
    training_set_meta: Optional[Mapping[str, str]] = None,
    asc: bool = True,
    offset: int = 0,
    limit: int = 10000,
) -> List[model.TrainingSetVersion]:
    """List training sets.

    Args:
        meta: Version metadata.
        training_set_name: Training set name.
        training_set_meta: Training set meta data.
        asc: Sort order by creation time, 1 for ascending -1 for descending.
        offset: Offset.
        limit: Limit.

    Returns:
        A list of matching TrainingSetVersions.
    """

    if meta is None:
        meta = {}

    if training_set_meta is None:
        training_set_meta = {}

    project_id = _get_project_id()

    response = post_version_find.sync_detailed(
        client=_get_client(),
        json_body=TrainingSetVersionFilter(
            training_set_meta=TrainingSetVersionFilterTrainingSetMeta.from_dict(
                training_set_meta,
            ),
            meta=TrainingSetVersionFilterMeta.from_dict(meta),
            project_id=project_id,
            training_set_name=training_set_name,
        ),
        offset=offset,
        limit=limit,
        asc=asc,
    )

    if response.status_code != 200:
        _raise_response_exn(response, "could not find TrainingSetVersion")

    return [_to_TrainingSetVersion(tsv) for tsv in response.parsed]


def _get_client() -> AuthenticatedClient:
    domino_host = os.getenv("DOMINO_API_HOST", os.getenv("DOMINO_USER_HOST"))
    api_key = os.getenv("DOMINO_USER_API_KEY")
    token_file = os.getenv("DOMINO_TOKEN_FILE")
    token_url = os.getenv("DOMINO_API_PROXY")

    return AuthenticatedClient(
        base_url=f"{domino_host}/trainingset",
        api_key=api_key,
        token_file=token_file,
        token_url=token_url,
    )


def _to_TrainingSet(ts: TrainingSet) -> model.TrainingSet:
    return model.TrainingSet(
        name=ts.name,
        description=ts.description,
        meta=ts.meta.to_dict(),
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
        all_columns=tsv.all_columns,
        monitoring_meta=model.MonitoringMeta(
            timestamp_columns=tsv.monitoring_meta.timestamp_columns,
            categorical_columns=tsv.monitoring_meta.categorical_columns,
            ordinal_columns=tsv.monitoring_meta.ordinal_columns,
        ),
        meta=tsv.meta.to_dict(),
        path=tsv.path,
        container_path=tsv.container_path,
        pending=tsv.pending,
    )


def _raise_response_exn(response: Response, msg: str):
    try:
        response_json = json.loads(response.content.decode("utf8"))
        server_msg = response_json.get("errors")
    except Exception:
        server_msg = None

    raise ServerException(msg, server_msg)


def _check_columns(all_columns: [str], expected_columns: [str]):
    diff = set(expected_columns) - set(all_columns)
    if diff:
        raise SchemaMismatchException(f"DataFrame missing columns: {diff}")


def _get_project_id() -> Optional[str]:
    return os.getenv("DOMINO_PROJECT_ID")


def _validate_trainingset_name(name: str):
    if _trainingset_name_pat.match(name) is None:
        raise ValueError(f"bad TrainingSet name '{name}'")

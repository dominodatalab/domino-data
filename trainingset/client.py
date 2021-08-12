from collections.abc import Mapping
from typing import Optional

import pandas as pd

from trainingset import model


def get_training_set(name: str) -> model.TrainingSet:
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
        training_set: model.TrainingSet,
) -> model.TrainingSet:
    # server updates modifiable fields, including users

    pass


def delete_training_set(
        name: str
) -> bool:
    # deletes a trainingset.
    # only if no it contains no versions? (user needs to delete them first)

    pass


def create_training_set_version(
        training_set: model.TrainingSet,
        df: pd.DataFrame,
) -> model.TrainingSetVersion:
    # creates TrainingSet if it does not already exist
    # creates a TrainingSetVersion record
    # gets pre-signed upload url
    # uploads data
    # updates TrainingSetVersion record to mark as complete

    pass


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


def delete_training_set_version(
        training_set_version_id: str
) -> bool:
    # server deletes object and marks record as deleted

    pass


def get_training_set_versions(
        training_set_name: Optional[str] = None,
        project_id: Optional[str] = None,  # the hex project_id?
        metadata: Mapping[str, str] = {},
        asc: int = 1,
        offset: int = 0,
        limit: int = 0,
) -> [model.TrainingSetVersion]:
    # finds records with all specified fields that user has access to

    pass

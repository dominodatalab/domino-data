from typing import List, Mapping, Optional, TypedDict

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class TrainingSet:
    """
    A TrainingSet.

    Keyword arguments:
    name -- unique name of the TrainingSet
    description -- description of the TrainingSet
    meta -- user defined metadata
    collaborator_names -- usernames of collaborator_names
    """

    name: str
    owner_name: str
    project_id: str
    description: Optional[str] = None
    meta: Mapping[str, str] = field(default_factory=map)
    collaborator_names: List[str] = field(default_factory=list)

    def add_collaborator_names(self, collaborator_names: List[str]) -> None:
        """Add collaborator_names"""

        # TODO: GO TO THE SERVER, use server's response. is this a good pattern?
        self.collaborator_names = list(set(self.collaborator_names) + set(collaborator_names))

    def remove_collaborator_names(self, collaborator_names: List[str]) -> None:
        """Add a collaborator_names"""

        # TODO: GO TO THE SERVER, use server's response. is this a good pattern?
        self.collaborator_names = list(set(self.collaborator_names) - set(collaborator_names))


class MonitoringMeta(TypedDict, total=False):
    """MonitoringMeta

    Keyword arguments:
    timestamp_columns -- TODO
    categorical_columns -- TODO
    ordinal_columns -- all other columns are continuous
    """

    timestamp_columns: List[str]
    categorical_columns: List[str]
    ordinal_columns: List[str]


@dataclass
class TrainingSetVersion:
    """
    A TrainingSetVersion

    number -- the TrainingSetVersion number
    training_set_name -- name of the TrainingSet this version belongs to
    description -- description of this version
    key_columns -- names of columns that represent IDs for retrieving features
    target_columns -- target variables for prediction
    exclude_columns -- columns to exclude when generating the training DataFrame
    monitoring_meta -- monitoring specific metadata
    meta -- user defined metadata
    """

    training_set_name: str
    number: int
    description: Optional[str] = None
    key_columns: List[str] = field(default_factory=list)
    target_columns: List[str] = field(default_factory=list)
    exclude_columns: List[str] = field(default_factory=list)
    monitoring_meta: MonitoringMeta = field(default_factory=map)
    meta: Mapping[str, str] = field(default_factory=map)
    pending: bool = True

    def load_training_pandas(self) -> pd.DataFrame:
        """Get a pandas dataframe for training.

        Dataframe will not include key_columns and exclude_columns.
        """

        pass

    def load_raw_pandas(self) -> pd.DataFrame:
        """Get the raw dataframe."""
        return self._df

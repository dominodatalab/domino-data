from typing import List, Mapping, Optional

import os
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
    """

    name: str
    project_id: str
    description: Optional[str] = None
    meta: Mapping[str, str] = field(default_factory=map)


@dataclass
class MonitoringMeta:
    """MonitoringMeta

    Keyword arguments:
    timestamp_columns -- TODO
    categorical_columns -- TODO
    ordinal_columns -- all other columns are continuous
    """

    timestamp_columns: List[str] = field(default_factory=list)
    categorical_columns: List[str] = field(default_factory=list)
    ordinal_columns: List[str] = field(default_factory=list)


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
    path: Optional[str] = None
    container_path: Optional[str] = None
    pending: bool = True

    @property
    def absolute_container_path(self):
        root = os.getenv("DOMINO_TRAINING_SET_PATH", "/var/opt/domino/trainingset/project")

        return f"{root}/{self.container_path}"

    def load_training_pandas(self) -> pd.DataFrame:
        """Get a pandas dataframe for training.

        Dataframe will not include key_columns and exclude_columns.
        """

        df = self.load_raw_pandas()

        for c in self.key_columns + self.exclude_columns:
            if c in df.columns:
                del df[c]

        return df

    def load_raw_pandas(self) -> pd.DataFrame:
        """Get the raw dataframe."""

        files = [
            os.path.join(self.absolute_container_path)
            for f in os.listdir(self.absolute_container_path)
            if f.endswith(".parquet")
        ]

        return pd.concat([pd.read_parquet(f) for f in files])

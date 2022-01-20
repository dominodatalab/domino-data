from typing import List, Mapping, Optional

import os
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class TrainingSet:
    """
    A Training Set.

    Args:
        name: Unique name of the TrainingSet.
        description: Description of the TrainingSet.
        meta: User defined metadata.
    """

    name: str
    project_id: str
    description: Optional[str] = None
    meta: Mapping[str, str] = field(default_factory=map)


@dataclass
class MonitoringMeta:
    """
    Monitoring Meta.

    For more details about the parameters, refer to :class:`.TrainingSetVersion`.

    Args:
        timestamp_columns: Timestamp columns.
        categorical_columns: Categorical columns.
        ordinal_columns: Ordinal columns. Currently, ordinal columns are skipped by the
            Model Monitor.
    """

    timestamp_columns: List[str] = field(default_factory=list)
    categorical_columns: List[str] = field(default_factory=list)
    ordinal_columns: List[str] = field(default_factory=list)


@dataclass
class TrainingSetVersion:
    """
    A Training Set Version.

    Any columns that are not inside ``key_columns``, ``exclude_columns``, \
        ``MonitoringMeta.categorical_columns``, ``MonitoringMeta.timestamp_columns``, \
        or ``MonitoringMeta.ordinal_columns`` are automatically marked as numerical \
        columns.

    Args:
        number: The TrainingSetVersion number.
        training_set_name: Name of the TrainingSet this version belongs to.
        description: Description of this version.
        key_columns: Row identifier columns.
        target_columns:
            Prediction columns.

            * For **classifications models**, this must be a **categorical** column. \
                Be sure to also include this column in \
                :py:attr:`.MonitoringMeta.categorical_columns`.

            * For **regression models**, it must be a **numerical** column.
        exclude_columns: Any columns that should be excluded.
        all_columns: Names all columns in the dataframe.
        monitoring_meta: Monitoring specific metadata.
        meta: User defined metadata
    """

    training_set_name: str
    number: int
    description: Optional[str] = None
    key_columns: List[str] = field(default_factory=list)
    target_columns: List[str] = field(default_factory=list)
    exclude_columns: List[str] = field(default_factory=list)
    all_columns: List[str] = field(default_factory=list)
    monitoring_meta: MonitoringMeta = field(default_factory=MonitoringMeta)
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

        Dataframe does not include key_columns and exclude_columns.
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

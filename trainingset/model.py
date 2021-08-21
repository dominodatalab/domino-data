import datetime
from typing import Optional, List, TypedDict, Mapping, List

import pandas as pd


class TrainingSet:
    def __init__(
            self,
            name: str,
            description: Optional[str] = None,
            meta: Mapping[str, str] = {},
            collaborator_names: List[str] = [],
            **kwargs
    ):
        """
        A TrainingSet.

        Keyword arguments:
        name -- unique name of the TrainingSet
        description -- description of the TrainingSet
        meta -- user defined metadata
        collaborator_names -- usernames of collaborator_names
        """

        self.name = name
        self.description = description
        self.meta = meta
        self.collaborator_names = collaborator_names
        self._owner_name = kwargs.get("owner_name")
        self._project_id = kwargs.get("project_id")

    @property
    def project_id(self) -> str:
        """The project this TrainingSet is associated with"""

        return self._project_id

    @property
    def owner_name(self) -> str:
        """The username of the owner of this TrainingSet"""

        return self._owner_name

    def add_collaborator_names(self, collaborator_names: List[str]) -> None:
        """Add collaborator_names"""

        # TODO: GO TO THE SERVER, use server's response. is this a good pattern?
        self.collaborator_names.update(collaborator_names)

    def remove_collaborator_names(self, collaborator_names: List[str]) -> None:
        """Add a collaborator_names"""

        # TODO: GO TO THE SERVER, use server's response. is this a good pattern?
        self.collaborator_names.difference_update(collaborator_names)

    def __str__(self):
        return "".join([
            "TrainingSet(",
            "name={self.name} ",
            "description={self.description or ''} ",
            "meta={self.meta} ",
            "owner_name={self._owner_name} ",
            "collaborator_names={self.collaborator_names}",
            ")"
        ])


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


class TrainingSetVersion:
    """
    TODO: Should document that this constructor is not mean to be called directly but only returned from create_training_set_version

    number -- the TrainingSetVersion number
    training_set_name -- name of the TrainingSet this version belongs to
    description -- description of this version
    key_columns -- names of columns that represent IDs for retrieving features
    target_columns -- target variables for prediction
    exclude_columns -- columns to exclude when generating the training DataFrame
    monitoring_meta -- monitoring specific metadata
    meta -- user defined metadata
    """

    def __init__(
            self,
            training_set_name: str,
            number: int,
            description: Optional[str] = None,
            key_columns: List[str] = [],
            target_columns: List[str] = [],
            exclude_columns: List[str] = [],
            monitoring_meta: MonitoringMeta = {},
            meta: Mapping[str, str] = {},
            **kwargs,
    ):
        self.number = number
        self.training_set_name = training_set_name
        self.description = description
        self.key_columns = key_columns
        self.target_columns = target_columns
        self.exclude_columns = exclude_columns
        self.monitoring_meta = monitoring_meta
        self.meta = meta
        self._pending = kwargs.get("pending")

    @property
    def pending(self) -> str:
        """Gets TrainingSetVersion's pending status"""

        return self._pending

    def load_training_pandas(self) -> pd.DataFrame:
        """Get a pandas dataframe for training.

        Dataframe will not include key_columns and exclude_columns.
        """

        pass

    def load_raw_pandas(self) -> pd.DataFrame:
        """Get the raw dataframe."""
        return self._df

    def __str__(self):
        return "".join([
            "TrainingSetVersion(",
            f"number={self.number} ",
            f"training_set_name={self.training_set_name} ",
            f"description={self.description or ''} ",
            f"key_columns={self.key_columns} ",
            f"target_columns={self.target_columns} ",
            f"exclude_columns={self.exclude_columns} ",
            f"monitoring_meta={self.monitoring_meta} ",
            f"meta={self.meta}",
            ")"
        ])


class TrainingSetFilter(TypedDict, total=False):
    """Filter TrainingSets by all provided fields.

    Keyword arguments:
    project_id -- the project id (e.g. 611808cfdc6bc24ee5f23fe8)
    project_name -- the project name (e.g. gmatev/quick_start)
    owner_name -- the TrainingSet's owner (e.g. gmatev)
    meta -- match metadata key-value pairs
    """

    project_name: str
    owner_name: str
    meta: Mapping[str, str]


class TrainingSetVersionFilter(TypedDict, total=False):
    """Filter TrainingSetVersions by all provided fields.

    Keyword arguments:
    project_id -- the project id (e.g. 611808cfdc6bc24ee5f23fe8)
    project_name -- the project name (e.g. gmatev/quick_start)
    meta -- version metadata
    training_set_name -- training set name
    training_set_meta -- training set meta data
    """

    project_id: str
    project_name: str
    meta: Mapping[str, str]
    training_set_name: str
    training_set_meta: Mapping[str, str]

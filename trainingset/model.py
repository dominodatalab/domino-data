import datetime
from typing import Optional, List, TypedDict, Mapping, Set

import pandas as pd


class TrainingSet:
    def __init__(
            self,
            name: str,
            description: Optional[str] = None,
            meta: Mapping(str, str) = {},
            collaborators: Set(str) = [],
            **kwargs
    ):
        """
        A TrainingSet.

        Keyword arguments:
        name -- unique name of the TrainingSet
        description -- description of the TrainingSet
        meta -- user defined metadata
        collaborators -- usernames of collaborators
        """

        self.name = name
        self.description = description
        self.meta = meta

        self._owner = kwargs.get("owner")
        self._collaborators = collaborators
        self._project_name = kwargs.get("project_name")

        @property
        def project_name(self) -> str:
            """The project this TrainingSet is associated with"""

            return self._project_name

        @property
        def owner(self) -> str:
            """The username of the owner of this TrainingSet"""

            return self._owner

        def add_collaborators(self, collaborators: List(str)) -> None:
            """Add collaborators"""

            # TODO: GO TO THE SERVER, use server's response. is this a good pattern?
            self._collaborators.update(collaborators)

        def remove_collaborators(self, collaborators: List(str)) -> None:
            """Add a collaborators"""

            # TODO: GO TO THE SERVER, use server's response. is this a good pattern?
            self._collaborators.difference_update(collaborators)


class MonitoringMeta(TypedDict, Total=False):
    """MonitoringMeta

    Keyword arguments:
    timestamp_columns -- TODO
    categorical_columns -- TODO
    ordinal_columns -- all other columns are continuous
    """

    timestamp_columns: List(str) = [],
    categorical_columns: List(str) = [],
    ordinal_columns: List(str) = [],


class TrainingSetVersion:
    """
    TODO: Should document that this constructor is not mean to be called directly but only returned from create_training_set_version

    number -- the TrainingSetVersion number
    training_set_name -- name of the TrainingSet this version belongs to
    name -- name of this version
    description -- description of this version
    key_columns -- names of columns that represent IDs for retrieving features
    target_columns -- target variables for prediction
    exclude_columns -- columns to exclude when generating the training DataFrame
    monitoring_meta -- monitoring specific metadata
    meta -- user defined metadata
    """

    def __init__(
            self,
            number: int,
            training_set_name: str,
            name: Optional[str] = None,
            description: Optional[str] = None,
            key_columns: List[str] = [],
            target_columns: List[str] = [],
            exclude_columns: List[str] = [],
            monitoring_meta: Optional(MonitoringMeta) = {},
            meta: Mapping(str, str) = {},
            **kwargs,
    ):
        self.number = number
        self.training_set_name = training_set_name,
        self.name = name
        self.description = description,

        self.key_columns = key_columns
        self.target_columns = target_columns
        self.exclude_columns = exclude_columns
        self.monitoring_meta = monitoring_meta
        self.meta = meta

    def load_training_pandas(self) -> pd.DataFrame:
        """Get a pandas dataframe for training.

        Dataframe will not include key_columns and exclude_columns.
        """

        pass

    def load_raw_pandas(self) -> pd.DataFrame:
        """Get the raw dataframe."""
        return self._df


class TrainingSetFilter(TypedDict, total=False):
    """Filter TrainingSets by all provided fields.

    Keyword arguments:
    project_id -- the project id (e.g. 611808cfdc6bc24ee5f23fe8)
    project_name -- the project name (e.g. gmatev/quick_start)
    owner -- the TrainingSet's owner (e.g. gmatev)
    meta -- match metadata key-value pairs
    """

    project_id: str
    project_name: str
    owner: str
    meta: Mapping(str, str)


class TrainingSetVersionFilter(TypedDict, Total=False):
    """Filter TrainingSetVersions by all provided fields.

    Keyword arguments:
    name -- version name
    project_id -- the project id (e.g. 611808cfdc6bc24ee5f23fe8)
    project_name -- the project name (e.g. gmatev/quick_start)
    meta -- version metadata
    training_set_name -- training set name
    training_set_meta -- training set meta data
    """

    name: str
    project_id: str
    project_name: str
    meta: Mapping(str, str)
    training_set_name: str
    training_set_meta: Mapping(str, str)

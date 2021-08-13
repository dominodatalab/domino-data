from collections.abc import Mapping
import datetime
from typing import Optional


class TrainingSet:
    def __init__(
            self,
            name: str,
            project_id: Optional[str] = None,  # is this owner/project or hex
            description: Optional[str] = None,
            users: [str] = [],  # usernames
    ):
        self.name = name
        self.project_id,
        self.description = description
        self.users = users


class TrainingSetVersion:
    def __init__(
            self,
            training_set: str,
            timestamp_column: str,
            independent_vars: [str] = [],
            target_vars: [str] = [],
            continuous_vars: [str] = [],
            categorical_vars: [str] = [],
            ordinal_vars: [str] = [],
            name: Optional[str] = None,
            description: Optional[str] = None,
            metadata: Mapping[str, str] = {},
            **kwargs,
    ):
        self.training_set = training_set
        self.timestamp_column = timestamp_column
        self.independent_vars = independent_vars
        self.target_vars = target_vars
        self.continuous_vars = continuous_vars
        self.categorical_vars = categorical_vars
        self.ordinal_vars = ordinal_vars
        self.name = name
        self.description = description
        self.metadata = metadata

        self.id = kwargs.get("creation_time", None)
        self.creation_time = kwargs.get("creation_time", datetime.now())

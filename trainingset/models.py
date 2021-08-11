from collections.abc import Mapping
import datetime
from enum import Enum


class TrainingSetType(Enum):
    GENERIC = 1
    TRAINING = 2
    PREDICTION = 3
    GROUND_TRUTH = 4


class TrainingSet:
    def __init__(
            self,
            id: str,
            version_number: int,
            name: str,
            description: str,
            type: TrainingSetType,
            creation_time: datetime.datetime,
            owner_id: str,
            metadata: Mapping[str, str],
            annotations: Mapping[str, str],
            archived: bool
    ):
        pass

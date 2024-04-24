from enum import Enum


class FeatureStoreSyncResult(str, Enum):
    FAILURE = "Failure"
    SUCCESS = "Success"

    def __str__(self) -> str:
        return str(self.value)

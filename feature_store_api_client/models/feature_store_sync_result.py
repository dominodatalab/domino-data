from enum import Enum


class FeatureStoreSyncResult(str, Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"

    def __str__(self) -> str:
        return str(self.value)

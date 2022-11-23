from enum import Enum


class GetUnlockFeatureStoreIdResultResult(str, Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"

    def __str__(self) -> str:
        return str(self.value)

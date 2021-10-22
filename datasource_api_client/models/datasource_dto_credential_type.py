from enum import Enum


class DatasourceDtoCredentialType(str, Enum):
    INDIVIDUAL = "Individual"
    SHARED = "Shared"

    def __str__(self) -> str:
        return str(self.value)

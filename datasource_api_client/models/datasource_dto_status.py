from enum import Enum


class DatasourceDtoStatus(str, Enum):
    ACTIVE = "Active"
    DELETED = "Deleted"

    def __str__(self) -> str:
        return str(self.value)

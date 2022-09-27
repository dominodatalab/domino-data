from enum import Enum


class AuthFieldName(str, Enum):
    PASSWORD = "password"
    USERNAME = "username"

    def __str__(self) -> str:
        return str(self.value)

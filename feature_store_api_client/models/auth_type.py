from enum import Enum


class AuthType(str, Enum):
    BASICOPTIONAL = "BasicOptional"
    USERONLY = "UserOnly"
    NOAUTH = "NoAuth"

    def __str__(self) -> str:
        return str(self.value)

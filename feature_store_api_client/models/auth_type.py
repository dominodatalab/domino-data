from enum import Enum


class AuthType(str, Enum):
    BASICOPTIONAL = "BasicOptional"
    NOAUTH = "NoAuth"
    USERONLY = "UserOnly"

    def __str__(self) -> str:
        return str(self.value)

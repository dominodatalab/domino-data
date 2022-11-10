class DominoError(Exception):
    """Base exception for known errors."""


class ServerException(Exception):
    """This exception is raised when the FeatureStore server rejects a request."""

    def __init__(self, message: str, server_msg: str):
        self.message = message
        self.server_msg = server_msg


class FeastRepoError(Exception):
    """Raised when no feast repo is found or more than one feast repos are found"""


class GitPullError(Exception):
    """Raised when git pull failed"""


class GitPushError(Exception):
    """Raised when git push failed"""


class FeatureStoreLockError(Exception):
    """Raised when failed to lock or unlock the feature store"""

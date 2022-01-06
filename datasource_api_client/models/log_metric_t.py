from enum import Enum


class LogMetricT(str, Enum):
    S3CONFIG = "S3Config"
    GCSCONFIG = "GCSConfig"

    def __str__(self) -> str:
        return str(self.value)

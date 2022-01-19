from enum import Enum


class LogMetricT(str, Enum):
    ADLSCONFIG = "ADLSConfig"
    GCSCONFIG = "GCSConfig"
    S3CONFIG = "S3Config"

    def __str__(self) -> str:
        return str(self.value)

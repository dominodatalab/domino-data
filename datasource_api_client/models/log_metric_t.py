from enum import Enum


class LogMetricT(str, Enum):
    ADLSCONFIG = "ADLSConfig"
    GCSCONFIG = "GCSConfig"
    GENERICS3CONFIG = "GenericS3Config"
    S3CONFIG = "S3Config"

    def __str__(self) -> str:
        return str(self.value)

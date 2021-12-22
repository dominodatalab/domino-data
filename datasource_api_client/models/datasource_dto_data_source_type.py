from enum import Enum


class DatasourceDtoDataSourceType(str, Enum):
    POSTGRESQLCONFIG = "PostgreSQLConfig"
    REDSHIFTCONFIG = "RedshiftConfig"
    S3CONFIG = "S3Config"
    SNOWFLAKECONFIG = "SnowflakeConfig"

    def __str__(self) -> str:
        return str(self.value)

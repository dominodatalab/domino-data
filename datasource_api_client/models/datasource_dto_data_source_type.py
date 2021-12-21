from enum import Enum


class DatasourceDtoDataSourceType(str, Enum):
    REDSHIFTCONFIG = "RedshiftConfig"
    S3CONFIG = "S3Config"
    SNOWFLAKECONFIG = "SnowflakeConfig"
    POSTGRESQLCONFIG = "PostgreSQLConfig"

    def __str__(self) -> str:
        return str(self.value)

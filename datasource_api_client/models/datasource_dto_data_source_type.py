from enum import Enum


class DatasourceDtoDataSourceType(str, Enum):
    SNOWFLAKECONFIG = "SnowflakeConfig"
    REDSHIFTCONFIG = "RedshiftConfig"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class DatasourceDtoDataSourceType(str, Enum):
    MYSQLCONFIG = "MySQLConfig"
    POSTGRESQLCONFIG = "PostgreSQLConfig"
    REDSHIFTCONFIG = "RedshiftConfig"
    S3CONFIG = "S3Config"
    SNOWFLAKECONFIG = "SnowflakeConfig"
    SQLSERVERCONFIG = "SQLServerConfig"

    def __str__(self) -> str:
        return str(self.value)

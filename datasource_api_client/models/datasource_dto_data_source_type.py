from enum import Enum


class DatasourceDtoDataSourceType(str, Enum):
    GCSCONFIG = "GCSConfig"
    MYSQLCONFIG = "MySQLConfig"
    POSTGRESQLCONFIG = "PostgreSQLConfig"
    REDSHIFTCONFIG = "RedshiftConfig"
    S3CONFIG = "S3Config"
    SNOWFLAKECONFIG = "SnowflakeConfig"
    SQLSERVERCONFIG = "SQLServerConfig"
    ORACLECONFIG = "OracleConfig"

    def __str__(self) -> str:
        return str(self.value)

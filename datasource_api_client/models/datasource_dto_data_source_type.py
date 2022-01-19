from enum import Enum


class DatasourceDtoDataSourceType(str, Enum):
    ADLSCONFIG = "ADLSConfig"
    GCSCONFIG = "GCSConfig"
    MYSQLCONFIG = "MySQLConfig"
    ORACLECONFIG = "OracleConfig"
    POSTGRESQLCONFIG = "PostgreSQLConfig"
    REDSHIFTCONFIG = "RedshiftConfig"
    S3CONFIG = "S3Config"
    SQLSERVERCONFIG = "SQLServerConfig"
    SNOWFLAKECONFIG = "SnowflakeConfig"

    def __str__(self) -> str:
        return str(self.value)

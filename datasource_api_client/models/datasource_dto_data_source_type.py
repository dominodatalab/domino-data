from enum import Enum


class DatasourceDtoDataSourceType(str, Enum):
    ADLSCONFIG = "ADLSConfig"
    BIGQUERYCONFIG = "BigQueryConfig"
    GCSCONFIG = "GCSConfig"
    GENERICS3CONFIG = "GenericS3Config"
    MYSQLCONFIG = "MySQLConfig"
    ORACLECONFIG = "OracleConfig"
    POSTGRESQLCONFIG = "PostgreSQLConfig"
    REDSHIFTCONFIG = "RedshiftConfig"
    S3CONFIG = "S3Config"
    SQLSERVERCONFIG = "SQLServerConfig"
    SNOWFLAKECONFIG = "SnowflakeConfig"
    TRINOCONFIG = "TrinoConfig"

    def __str__(self) -> str:
        return str(self.value)

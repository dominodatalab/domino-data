from enum import Enum


class DatasourceDtoDataSourceType(str, Enum):
    ADLSCONFIG = "ADLSConfig"
    AZUREBLOBSTORAGECONFIG = "AzureBlobStorageConfig"
    BIGQUERYCONFIG = "BigQueryConfig"
    CLICKHOUSECONFIG = "ClickHouseConfig"
    DATABRICKSCONFIG = "DatabricksConfig"
    DATASETCONFIG = "DatasetConfig"
    DB2CONFIG = "DB2Config"
    DB2NATIVECONFIG = "DB2NativeConfig"
    DRUIDCONFIG = "DruidConfig"
    GCSCONFIG = "GCSConfig"
    GENERICJDBCCONFIG = "GenericJDBCConfig"
    GENERICS3CONFIG = "GenericS3Config"
    GREENPLUMCONFIG = "GreenplumConfig"
    IGNITECONFIG = "IgniteConfig"
    MARIADBCONFIG = "MariaDBConfig"
    MONGODBCONFIG = "MongoDBConfig"
    MYSQLCONFIG = "MySQLConfig"
    NETEZZACONFIG = "NetezzaConfig"
    ORACLECONFIG = "OracleConfig"
    PALANTIRCONFIG = "PalantirConfig"
    POSTGRESQLCONFIG = "PostgreSQLConfig"
    REDSHIFTCONFIG = "RedshiftConfig"
    S3CONFIG = "S3Config"
    SAPHANACONFIG = "SAPHanaConfig"
    SINGLESTORECONFIG = "SingleStoreConfig"
    SNOWFLAKECONFIG = "SnowflakeConfig"
    SQLSERVERCONFIG = "SQLServerConfig"
    SYNAPSECONFIG = "SynapseConfig"
    TABULARS3GLUECONFIG = "TabularS3GlueConfig"
    TERADATACONFIG = "TeradataConfig"
    TRINOCONFIG = "TrinoConfig"
    VERTICACONFIG = "VerticaConfig"

    def __str__(self) -> str:
        return str(self.value)

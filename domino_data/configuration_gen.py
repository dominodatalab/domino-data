"""Code generated by gen.py; DO NOT EDIT.
This file was generated by robots at
2025-07-03 08:05:39.670779"""

from typing import Any, Dict, Optional, Union

from enum import Enum
from importlib import import_module

import attr

from datasource_api_client.models import DatasourceDtoDataSourceType

CREDENTIAL_TYPE = "credential"
CONFIGURATION_TYPE = "configuration"

ELEMENT_TYPE_METADATA = "__element_type_metadata"
ELEMENT_VALUE_METADATA = "__element_value_metadata"


def _filter_config(att: Any, _: Any) -> Any:
    """Filter configuration type attributes."""
    return att.metadata.get(ELEMENT_TYPE_METADATA, "") == CONFIGURATION_TYPE


def _filter_cred(att: Any, _: Any) -> Any:
    """Filter credential type attributes."""
    return att.metadata.get(ELEMENT_TYPE_METADATA, "") == CREDENTIAL_TYPE


@attr.s
class Config:
    """Base datasource configuration."""

    def config(self) -> Dict[str, str]:
        """Get configuration as dict."""
        fields = attr.fields_dict(self.__class__)
        attrs = attr.asdict(self, filter=_filter_config)

        res = {}
        for name, val in attrs.items():
            field = fields[name]
            if val is not None:
                res[field.metadata[ELEMENT_VALUE_METADATA].value] = val
        return res

    def credential(self) -> Dict[str, str]:
        """Get credentials as dict."""
        fields = attr.fields_dict(self.__class__)
        attrs = attr.asdict(self, filter=_filter_cred)

        res = {}
        for name, val in attrs.items():
            field = fields[name]
            if val is not None:
                res[field.metadata[ELEMENT_VALUE_METADATA].value] = val
        return res


class ConfigElem(Enum):
    """Enumeration of valid config elements."""

    ACCOUNTNAME = "accountName"
    ACCOUNTID = "accountID"
    BUCKET = "bucket"
    CATALOG = "catalog"
    CLUSTER = "cluster"
    DATABASE = "database"
    DATASETID = "datasetID"
    DATETIMEPRECISION = "datetimePrecision"
    EXTRAPROPERTIES = "extraProperties"
    HOST = "host"
    HTTPPATH = "httpPath"
    NETWORKINGPROXY = "networkingProxy"
    PORT = "port"
    PROJECT = "project"
    REGION = "region"
    ROLE = "role"
    SCHEMA = "schema"
    SUBFOLDER = "subfolder"
    WAREHOUSE = "warehouse"
    CATALOGCODE = "catalogCode"
    ENVIRONMENT = "environment"
    SNAPSHOTID = "snapshotID"
    SSLENABLED = "sslEnabled"


class CredElem(Enum):
    """Enumeration of valid credential elements."""

    ACCESSKEY = "accessKey"
    ACCESSKEYID = "accessKeyID"
    PASSWORD = "password"
    PRIVATEKEY = "privateKey"
    SECRETACCESSKEY = "secretAccessKey"
    SESSIONTOKEN = "sessionToken"
    TOKEN = "token"
    USERNAME = "username"
    CLIENTID = "clientId"
    CLIENTSECRET = "clientSecret"
    PERSONALACCESSTOKEN = "personalAccessToken"
    APIKEY = "apiKey"
    OAUTHTOKEN = "oAuthToken"


def _cred(elem: CredElem) -> Any:
    """Type helper for credentials attributes."""
    metadata = {
        ELEMENT_TYPE_METADATA: CREDENTIAL_TYPE,
        ELEMENT_VALUE_METADATA: elem,
    }
    return attr.ib(default=None, kw_only=True, metadata=metadata)


def _config(elem: ConfigElem) -> Any:
    """Type helper for configuration attributes."""
    metadata = {
        ELEMENT_TYPE_METADATA: CONFIGURATION_TYPE,
        ELEMENT_VALUE_METADATA: elem,
    }
    return attr.ib(default=None, kw_only=True, metadata=metadata)


@attr.s(auto_attribs=True)
class ADLSConfig(Config):
    """ADLSConfig datasource configuration."""

    container: Optional[str] = _config(elem=ConfigElem.BUCKET)

    access_key: Optional[str] = _cred(elem=CredElem.ACCESSKEY)


@attr.s(auto_attribs=True)
class AzureBlobStorageConfig(Config):
    """AzureBlobStorageConfig datasource configuration."""

    container: Optional[str] = _config(elem=ConfigElem.BUCKET)

    access_key: Optional[str] = _cred(elem=CredElem.ACCESSKEY)


@attr.s(auto_attribs=True)
class BigQueryConfig(Config):
    """BigQueryConfig datasource configuration."""

    gcp_project_id: Optional[str] = _config(elem=ConfigElem.PROJECT)
    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    private_key_json: Optional[str] = _cred(elem=CredElem.PRIVATEKEY)


@attr.s(auto_attribs=True)
class ClickHouseConfig(Config):
    """ClickHouseConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class DatabricksConfig(Config):
    """DatabricksConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)
    catalog: Optional[str] = _config(elem=ConfigElem.CATALOG)
    schema: Optional[str] = _config(elem=ConfigElem.SCHEMA)

    personal_access_token: Optional[str] = _cred(elem=CredElem.PERSONALACCESSTOKEN)


@attr.s(auto_attribs=True)
class DatasetConfig(Config):
    """DatasetConfig datasource configuration."""

    snapshot_id: Optional[str] = _config(elem=ConfigElem.SNAPSHOTID)
    subfolder: Optional[str] = _config(elem=ConfigElem.SUBFOLDER)


@attr.s(auto_attribs=True)
class DB2Config(Config):
    """DB2Config datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class DruidConfig(Config):
    """DruidConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class GCSConfig(Config):
    """GCSConfig datasource configuration."""

    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)

    private_key_json: Optional[str] = _cred(elem=CredElem.PRIVATEKEY)


@attr.s(auto_attribs=True)
class GenericJDBCConfig(Config):
    """GenericJDBCConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class GenericS3Config(Config):
    """GenericS3Config datasource configuration."""

    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)
    subfolder: Optional[str] = _config(elem=ConfigElem.SUBFOLDER)
    host: Optional[str] = _config(elem=ConfigElem.HOST)
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    aws_access_key_id: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)


@attr.s(auto_attribs=True)
class GreenplumConfig(Config):
    """GreenplumConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class IgniteConfig(Config):
    """IgniteConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class MariaDBConfig(Config):
    """MariaDBConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class MongoDBConfig(Config):
    """MongoDBConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class MySQLConfig(Config):
    """MySQLConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    aws_access_key_id: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    aws_session_token: Optional[str] = _cred(elem=CredElem.SESSIONTOKEN)


@attr.s(auto_attribs=True)
class NetezzaConfig(Config):
    """NetezzaConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class OracleConfig(Config):
    """OracleConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class PalantirConfig(Config):
    """PalantirConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    client_id: Optional[str] = _cred(elem=CredElem.CLIENTID)
    client_secret: Optional[str] = _cred(elem=CredElem.CLIENTSECRET)
    o_auth_token: Optional[str] = _cred(elem=CredElem.OAUTHTOKEN)


@attr.s(auto_attribs=True)
class PostgreSQLConfig(Config):
    """PostgreSQLConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    aws_access_key_id: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    aws_session_token: Optional[str] = _cred(elem=CredElem.SESSIONTOKEN)


@attr.s(auto_attribs=True)
class RedshiftConfig(Config):
    """RedshiftConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    aws_access_key_id: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    aws_session_token: Optional[str] = _cred(elem=CredElem.SESSIONTOKEN)


@attr.s(auto_attribs=True)
class S3Config(Config):
    """S3Config datasource configuration."""

    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)
    subfolder: Optional[str] = _config(elem=ConfigElem.SUBFOLDER)
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    aws_access_key_id: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    aws_session_token: Optional[str] = _cred(elem=CredElem.SESSIONTOKEN)


@attr.s(auto_attribs=True)
class SAPHanaConfig(Config):
    """SAPHanaConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class SingleStoreConfig(Config):
    """SingleStoreConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class SQLServerConfig(Config):
    """SQLServerConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class SnowflakeConfig(Config):
    """SnowflakeConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)
    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    role: Optional[str] = _config(elem=ConfigElem.ROLE)
    schema: Optional[str] = _config(elem=ConfigElem.SCHEMA)
    warehouse: Optional[str] = _config(elem=ConfigElem.WAREHOUSE)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    token: Optional[str] = _cred(elem=CredElem.TOKEN)


@attr.s(auto_attribs=True)
class SynapseConfig(Config):
    """SynapseConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class TabularS3GlueConfig(Config):
    """TabularS3GlueConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)
    region: Optional[str] = _config(elem=ConfigElem.REGION)


@attr.s(auto_attribs=True)
class TeradataConfig(Config):
    """TeradataConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class TrinoConfig(Config):
    """TrinoConfig datasource configuration."""

    catalog: Optional[str] = _config(elem=ConfigElem.CATALOG)
    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)
    schema: Optional[str] = _config(elem=ConfigElem.SCHEMA)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class VerticaConfig(Config):
    """VerticaConfig datasource configuration."""

    datetime_precision: Optional[str] = _config(elem=ConfigElem.DATETIMEPRECISION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


DatasourceConfig = Union[
    ADLSConfig,
    AzureBlobStorageConfig,
    BigQueryConfig,
    ClickHouseConfig,
    DatabricksConfig,
    DatasetConfig,
    DB2Config,
    DruidConfig,
    GCSConfig,
    GenericJDBCConfig,
    GenericS3Config,
    GreenplumConfig,
    IgniteConfig,
    MariaDBConfig,
    MongoDBConfig,
    MySQLConfig,
    NetezzaConfig,
    OracleConfig,
    PalantirConfig,
    PostgreSQLConfig,
    RedshiftConfig,
    S3Config,
    SAPHanaConfig,
    SingleStoreConfig,
    SQLServerConfig,
    SnowflakeConfig,
    SynapseConfig,
    TabularS3GlueConfig,
    TeradataConfig,
    TrinoConfig,
    VerticaConfig,
    Config,
]

DATASOURCES = {
    DatasourceDtoDataSourceType.ADLSCONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.AZUREBLOBSTORAGECONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.BIGQUERYCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.CLICKHOUSECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.DATABRICKSCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.DATASETCONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.DB2CONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.DRUIDCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.GCSCONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.GENERICJDBCCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.GENERICS3CONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.GREENPLUMCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.IGNITECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.MARIADBCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.MONGODBCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.MYSQLCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.NETEZZACONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.ORACLECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.PALANTIRCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.POSTGRESQLCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.REDSHIFTCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.S3CONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.SAPHANACONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.SINGLESTORECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.SQLSERVERCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.SNOWFLAKECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.SYNAPSECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.TABULARS3GLUECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.TERADATACONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.TRINOCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.VERTICACONFIG: "TabularDatasource",
}


def find_datasource_klass(datasource_type: DatasourceDtoDataSourceType) -> Any:
    """Find according datasource class."""
    mod = import_module("domino_data.data_sources")
    return getattr(mod, DATASOURCES[datasource_type])

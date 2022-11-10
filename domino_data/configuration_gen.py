"""Code generated by gen.py; DO NOT EDIT.
This file was generated by robots at
2022-10-25 03:08:23.992965"""
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
    EXTRAPROPERTIES = "extraProperties"
    HOST = "host"
    PORT = "port"
    PROJECT = "project"
    REGION = "region"
    ROLE = "role"
    SCHEMA = "schema"
    WAREHOUSE = "warehouse"


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
class BigQueryConfig(Config):
    """BigQueryConfig datasource configuration."""

    gcp_project_id: Optional[str] = _config(elem=ConfigElem.PROJECT)

    private_key_json: Optional[str] = _cred(elem=CredElem.PRIVATEKEY)


@attr.s(auto_attribs=True)
class GCSConfig(Config):
    """GCSConfig datasource configuration."""

    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)

    private_key_json: Optional[str] = _cred(elem=CredElem.PRIVATEKEY)


@attr.s(auto_attribs=True)
class GenericS3Config(Config):
    """GenericS3Config datasource configuration."""

    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)
    host: Optional[str] = _config(elem=ConfigElem.HOST)
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    aws_access_key_id: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)


@attr.s(auto_attribs=True)
class MongoDBConfig(Config):
    """MongoDBConfig datasource configuration."""

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class MySQLConfig(Config):
    """MySQLConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    aws_access_key_id: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    aws_session_token: Optional[str] = _cred(elem=CredElem.SESSIONTOKEN)


@attr.s(auto_attribs=True)
class OracleConfig(Config):
    """OracleConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class PostgreSQLConfig(Config):
    """PostgreSQLConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
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
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    aws_access_key_id: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    aws_session_token: Optional[str] = _cred(elem=CredElem.SESSIONTOKEN)


@attr.s(auto_attribs=True)
class SQLServerConfig(Config):
    """SQLServerConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class SnowflakeConfig(Config):
    """SnowflakeConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    role: Optional[str] = _config(elem=ConfigElem.ROLE)
    schema: Optional[str] = _config(elem=ConfigElem.SCHEMA)
    warehouse: Optional[str] = _config(elem=ConfigElem.WAREHOUSE)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    token: Optional[str] = _cred(elem=CredElem.TOKEN)


@attr.s(auto_attribs=True)
class TabularS3GlueConfig(Config):
    """TabularS3GlueConfig datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    region: Optional[str] = _config(elem=ConfigElem.REGION)


@attr.s(auto_attribs=True)
class TeradataConfig(Config):
    """TeradataConfig datasource configuration."""

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


@attr.s(auto_attribs=True)
class TrinoConfig(Config):
    """TrinoConfig datasource configuration."""

    catalog: Optional[str] = _config(elem=ConfigElem.CATALOG)
    schema: Optional[str] = _config(elem=ConfigElem.SCHEMA)

    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)


DatasourceConfig = Union[
    ADLSConfig,
    BigQueryConfig,
    GCSConfig,
    GenericS3Config,
    MongoDBConfig,
    MySQLConfig,
    OracleConfig,
    PostgreSQLConfig,
    RedshiftConfig,
    S3Config,
    SQLServerConfig,
    SnowflakeConfig,
    TabularS3GlueConfig,
    TeradataConfig,
    TrinoConfig,
    Config,
]

DATASOURCES = {
    DatasourceDtoDataSourceType.ADLSCONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.BIGQUERYCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.GCSCONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.GENERICS3CONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.MONGODBCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.MYSQLCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.ORACLECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.POSTGRESQLCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.REDSHIFTCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.S3CONFIG: "ObjectStoreDatasource",
    DatasourceDtoDataSourceType.SQLSERVERCONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.SNOWFLAKECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.TABULARS3GLUECONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.TERADATACONFIG: "TabularDatasource",
    DatasourceDtoDataSourceType.TRINOCONFIG: "TabularDatasource",
}


def find_datasource_klass(datasource_type: DatasourceDtoDataSourceType) -> Any:
    """Find according datasource class."""
    mod = import_module("domino_data.data_sources")
    return getattr(mod, DATASOURCES[datasource_type])

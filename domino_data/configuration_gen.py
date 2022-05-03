"""Code generated by gen.py; DO NOT EDIT.
This file was generated by robots at
2022-05-03 15:37:38.663412"""
from enum import Enum

class ConfigElem(Enum):
    """Enumeration of valid config elements."""

    ACCOUNTNAME = "accountName"
    BUCKET = "bucket"
    CLUSTER = "cluster"
    DATABASE = "database"
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
    
@attr.s(auto_attribs=True)
class ADLSConfig(Config):
    """ADLSConfig datasource configuration."""
    
    container: Optional[str] = _config(elem=ConfigElem.BUCKET)
    
    access_key: Optional[str] = _cred(elem=CredElem.ACCESSKEY)
    
@attr.s(auto_attribs=True)
class BigQueryConfig(Config):
    """BigQueryConfig datasource configuration."""
    
    gcp_project_i_d: Optional[str] = _config(elem=ConfigElem.PROJECT)
    
    private_key: Optional[str] = _cred(elem=CredElem.PRIVATEKEY)
    
@attr.s(auto_attribs=True)
class GCSConfig(Config):
    """GCSConfig datasource configuration."""
    
    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)
    
    private_key: Optional[str] = _cred(elem=CredElem.PRIVATEKEY)
    
@attr.s(auto_attribs=True)
class GenericS3Config(Config):
    """GenericS3Config datasource configuration."""
    
    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)
    host: Optional[str] = _config(elem=ConfigElem.HOST)
    region: Optional[str] = _config(elem=ConfigElem.REGION)
    
    access_key_i_d: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    
@attr.s(auto_attribs=True)
class MySQLConfig(Config):
    """MySQLConfig datasource configuration."""
    
    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    region: Optional[str] = _config(elem=ConfigElem.REGION)
    
    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    access_key_i_d: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    
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
    access_key_i_d: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    
@attr.s(auto_attribs=True)
class RedshiftConfig(Config):
    """RedshiftConfig datasource configuration."""
    
    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    region: Optional[str] = _config(elem=ConfigElem.REGION)
    
    username: Optional[str] = _cred(elem=CredElem.USERNAME)
    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    access_key_i_d: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    
@attr.s(auto_attribs=True)
class S3Config(Config):
    """S3Config datasource configuration."""
    
    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)
    region: Optional[str] = _config(elem=ConfigElem.REGION)
    
    access_key_i_d: Optional[str] = _cred(elem=CredElem.ACCESSKEYID)
    secret_access_key: Optional[str] = _cred(elem=CredElem.SECRETACCESSKEY)
    
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
    

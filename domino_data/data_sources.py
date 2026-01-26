"""Datasource module."""

from typing import Any, Dict, List, Optional, Type, Union, cast

import configparser
import io
import json
import logging
import os
import tempfile
from datetime import date, datetime
from decimal import Decimal
from os.path import exists

import attr
import backoff
import httpx
import numpy
import pandas
import urllib3
from httpx._config import DEFAULT_TIMEOUT_CONFIG
from pyarrow import ArrowException, flight, parquet

import domino_data.configuration_gen
from datasource_api_client.api.datasource import get_datasource_by_name
from datasource_api_client.api.proxy import get_key_url, list_keys, log_metric
from datasource_api_client.models import DatasourceConfig as APIConfig
from datasource_api_client.models import (
    DatasourceDto,
    DatasourceDtoAuthType,
    DatasourceDtoDataSourceType,
    ErrorResponse,
    KeyRequest,
    ListRequest,
    LogMetricM,
    LogMetricT,
    ProxyErrorResponse,
)

from .auth import AuthenticatedClient, AuthMiddlewareFactory, ProxyClient, get_jwt_token
from .configuration_gen import Config, CredElem, DatasourceConfig, find_datasource_klass
from .logging import logger
from .meta import MetaMiddlewareFactory
from .transfer import MAX_WORKERS, BlobTransfer

ACCEPT_HEADERS = {"Accept": "application/json"}
ADLS_HEADERS = {"X-Ms-Blob-Type": "BlockBlob"}
AUTHORIZATION_HEADER = "Authorization"

CREDENTIAL_TYPE = "credential"
CONFIGURATION_TYPE = "configuration"

FLIGHT_ERROR_SPLIT = ". gRPC client debug context:"

AWS_CREDENTIALS_DEFAULT_LOCATION = "/var/lib/domino/home/.aws/credentials"
AWS_SHARED_CREDENTIALS_FILE = "AWS_SHARED_CREDENTIALS_FILE"
DOMINO_API_HOST = "DOMINO_API_HOST"
DOMINO_API_PROXY = "DOMINO_API_PROXY"
DOMINO_CLIENT_SOURCE = "DOMINO_CLIENT_SOURCE"
DOMINO_DATASOURCE_PROXY_HOST = "DOMINO_DATASOURCE_PROXY_HOST"
DOMINO_DATASOURCE_PROXY_FLIGHT_HOST = "DOMINO_DATASOURCE_PROXY_FLIGHT_HOST"
DOMINO_RUN_ID = "DOMINO_RUN_ID"
DOMINO_USER_API_KEY = "DOMINO_USER_API_KEY"
DOMINO_USER_HOST = "DOMINO_USER_HOST"
DOMINO_TOKEN_DEFAULT_LOCATION = "/var/lib/domino/home/.api/token"
DOMINO_TOKEN_FILE = "DOMINO_TOKEN_FILE"


def __getattr__(name: str) -> Any:
    if name.endswith("Config"):
        return getattr(domino_data.configuration_gen, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__() -> List[str]:
    confs = filter(lambda x: x.endswith("Config"), dir(domino_data.configuration_gen))
    return list(globals().keys()) + list(confs)


class DominoError(Exception):
    """Base exception for known errors."""


class UnauthenticatedError(DominoError):
    """To handle exponential backoff."""


def _unpack_flight_error(error: str) -> str:
    """Unpack a flight error message by removing extra information."""
    try:
        return error.split(FLIGHT_ERROR_SPLIT, maxsplit=1)[0]
    except ValueError:
        return error


@attr.s
class Result:
    """Represents a query result."""

    client: "DataSourceClient" = attr.ib(repr=False)
    reader: flight.FlightStreamReader = attr.ib(repr=False)
    statement: str = attr.ib()

    def to_pandas(self) -> pandas.DataFrame:
        """Load and transform the result into a pandas DataFrame.

        Returns:
            Pandas dataframe loaded with entire resultset
        """
        return self.reader.read_pandas()

    def to_parquet(self, where: Any) -> None:
        """Load and serialize the result to a local parquet file.

        Args:
            where: path of file-like object.
        """
        table = self.reader.read_all()
        # In Pyarrow v13.0, the parquet version was upgraded to v2.6 from v2.4.
        # Set the coerce_timestamps to "us"(microseconds) for backward compatibility.
        parquet.write_table(table, where, coerce_timestamps="us")


@attr.s
class _Object:
    """Represents an object in a object store."""

    datasource: "ObjectStoreDatasource" = attr.ib(repr=False)
    key: str = attr.ib()
    include_auth_headers: bool = attr.ib(default=False, repr=False)

    def http(self) -> httpx.Client:
        """Get datasource http client."""
        return self.datasource.http()

    def pool_manager(self) -> urllib3.PoolManager:
        """Get datasource http pool manager."""
        return self.datasource.pool_manager()

    def _get_headers(self) -> dict:
        """Get auth headers if needed for direct storage access.

        When include_auth_headers is True, this method retrieves authentication headers
        This is used for volume operations that need to authenticate directly to webvfs.
        """
        if not self.include_auth_headers:
            return {}

        client = self.datasource.client

        if client.token is not None:
            return {AUTHORIZATION_HEADER: f"Bearer {client.token}"}

        if client.token_file and exists(client.token_file):
            with open(client.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            return {AUTHORIZATION_HEADER: f"Bearer {jwt}"}

        if client.token_url is not None:
            try:
                jwt = get_jwt_token(client.token_url)
                return {AUTHORIZATION_HEADER: f"Bearer {jwt}"}
            except httpx.HTTPStatusError:
                # Log the error and return empty headers
                logger.opt(exception=True).warning("Failed to get JWT token from token URL")

        return {}

    def get(self) -> bytes:
        """Get object content as bytes."""
        url = self.datasource.get_key_url(self.key, False)
        headers = self._get_headers()
        res = self.http().get(url, headers=headers)
        res.raise_for_status()

        self.datasource.client._log_metric(  # pylint: disable=protected-access
            self.datasource.datasource_type,
            len(res.content),
            False,
        )

        return res.content

    def download_file(self, filename: str) -> None:
        """Download object content to file located at filename.

        The file will be created if it does not exists.

        Args:
            filename: path of file to write content to.
        """
        url = self.datasource.get_key_url(self.key, False)
        headers = self._get_headers()
        content_size = 0
        with (
            self.http().stream("GET", url, headers=headers) as stream,
            open(filename, "wb") as file,
        ):
            for data in stream.iter_bytes():
                content_size += len(data)
                file.write(data)

        self.datasource.client._log_metric(  # pylint: disable=protected-access
            self.datasource.datasource_type,
            content_size,
            False,
        )

    def download(self, filename: str, max_workers: int = MAX_WORKERS) -> None:
        """Download object content to file with multithreaded support.

        The file will be created if it does not exists. File will be overwritten if it exists.

        Args:
            filename: path of file to write content to
            max_workers: max parallelism for high speed download
        """
        url = self.datasource.get_key_url(self.key, False)
        headers = self._get_headers()
        with open(filename, "wb") as file:
            blob = BlobTransfer(
                url, file, headers=headers, max_workers=max_workers, http=self.pool_manager()
            )

        self.datasource.client._log_metric(  # pylint: disable=protected-access
            self.datasource.datasource_type,
            blob.content_size,
            False,
        )

    def download_fileobj(self, fileobj: Any) -> None:
        """Download object content to file like object.

        Args:
            fileobj: A file-like object to download into.
                At a minimum, it must implement the write method and must accept bytes.
        """
        url = self.datasource.get_key_url(self.key, False)
        headers = self._get_headers()
        content_size = 0
        with self.http().stream("GET", url, headers=headers) as stream:
            for data in stream.iter_bytes():
                content_size += len(data)
                fileobj.write(data)

        self.datasource.client._log_metric(  # pylint: disable=protected-access
            self.datasource.datasource_type,
            content_size,
            False,
        )

    def put(self, content: bytes) -> None:
        """Upload content to object.

        Args:
            content: bytes content
        """
        url = self.datasource.get_key_url(self.key, True)
        headers = self._get_headers()
        res = self.http().put(url, content=content, headers=headers)
        res.raise_for_status()

        self.datasource.client._log_metric(  # pylint: disable=protected-access
            self.datasource.datasource_type,
            len(content),
            True,
        )

    def upload_file(self, filename: str) -> None:
        """Upload content of file at filename to object.

        Args:
            filename: path of file to upload.
        """
        url = self.datasource.get_key_url(self.key, True)
        headers = self._get_headers()
        with open(filename, "rb") as file:
            res = self.http().put(url, content=file, headers=headers)
        res.raise_for_status()

        content_size = os.path.getsize(filename)
        self.datasource.client._log_metric(  # pylint: disable=protected-access
            self.datasource.datasource_type,
            content_size,
            True,
        )

    def upload_fileobj(self, fileobj: Any) -> None:
        """Upload content of file like object to object.

        Args:
            fileobj: bytes-like object or an iterable producing bytes.
        """
        url = self.datasource.get_key_url(self.key, True)
        headers = self._get_headers()
        res = self.http().put(url, content=fileobj, headers=headers)
        res.raise_for_status()


def load_oauth_credentials() -> Dict[str, str]:
    """Load oauth token from sidecar container or local file.

    Returns:
        .. code-block:: python

            {CredElem.TOKEN.value: "token"}

    Raises:
        DominoError: if the provided location is not a valid file
    """
    token_url = os.getenv(DOMINO_API_PROXY, "")
    if token_url:
        try:
            jwt = get_jwt_token(token_url)
        except httpx.HTTPStatusError:
            logger.opt(exception=True).warning("Failed to get token from sidecar container API")
        else:
            return {CredElem.TOKEN.value: jwt}

    location = os.getenv("DOMINO_TOKEN_FILE", DOMINO_TOKEN_DEFAULT_LOCATION)
    try:
        with open(location, encoding="ascii") as token_file:
            return {CredElem.TOKEN.value: token_file.readline().rstrip()}
    except FileNotFoundError as exc:
        raise DominoError("Token file location is not a valid file.") from exc


def load_aws_credentials(location: str, profile: str = "") -> Dict[str, str]:
    """Load AWS credentials from given location and profile.

    Args:
        location: location of file that contains token.
        profile: profile to load.

    Returns:
        .. code-block:: python

            {
                CredElem.ACCESSKEYID.value: "access_key_id",
                CredElem.SECRETACCESSKEY.value: "secret_access_key",
                CredElem.SESSIONTOKEN.value: "session_token",
            }

    Raises:
        DominoError: if the provided location is not a valid file
    """
    location = location or AWS_CREDENTIALS_DEFAULT_LOCATION
    aws_config = configparser.RawConfigParser()
    aws_config.read(location)
    if not aws_config or not aws_config.sections():
        raise DominoError("AWS credentials file does not exist or does not contain profiles")

    profile = profile or aws_config.sections()[0]
    return {
        CredElem.ACCESSKEYID.value: aws_config.get(profile, "aws_access_key_id"),
        CredElem.SECRETACCESSKEY.value: aws_config.get(profile, "aws_secret_access_key"),
        CredElem.SESSIONTOKEN.value: aws_config.get(profile, "aws_session_token"),
    }


@attr.s
class Datasource:
    """Represents a Domino datasource."""

    # pylint: disable=too-many-instance-attributes

    auth_type: str = attr.ib()
    client: "DataSourceClient" = attr.ib(repr=False)
    config: Dict[str, Any] = attr.ib()
    datasource_type: str = attr.ib()
    identifier: str = attr.ib()
    name: str = attr.ib()
    owner: str = attr.ib()

    _config_override: DatasourceConfig = attr.ib(factory=Config, init=False, repr=False)
    _httpx: Optional[httpx.Client] = attr.ib(None, init=False, repr=False)

    @classmethod
    def from_dto(cls, client: "DataSourceClient", dto: DatasourceDto) -> "Datasource":
        """Build a datasource from a given DTO."""
        return cls(
            auth_type=dto.auth_type.value,
            client=client,
            config=dto.config.to_dict(),
            datasource_type=dto.data_source_type.value,
            identifier=dto.id,
            name=dto.name,
            owner=dto.owner_info.owner_name,
        )

    def http(self) -> httpx.Client:
        """Singleton http client built for the datasource."""
        if self._httpx is not None:
            return self._httpx

        context = httpx.create_ssl_context()

        if self.datasource_type in (
            DatasourceDtoDataSourceType.ADLSCONFIG.value,
            DatasourceDtoDataSourceType.AZUREBLOBSTORAGECONFIG.value,
        ):
            self._httpx = httpx.Client(
                headers=ADLS_HEADERS, verify=context, timeout=DEFAULT_TIMEOUT_CONFIG
            )
        elif self.datasource_type == DatasourceDtoDataSourceType.GENERICS3CONFIG.value:
            self._httpx = httpx.Client(verify=False, timeout=DEFAULT_TIMEOUT_CONFIG)  # nosec
        else:
            self._httpx = httpx.Client(verify=context, timeout=DEFAULT_TIMEOUT_CONFIG)
        return self._httpx

    def pool_manager(self) -> urllib3.PoolManager:
        """Urllib3 pool manager for range downloads."""
        if self.datasource_type in (
            DatasourceDtoDataSourceType.ADLSCONFIG.value,
            DatasourceDtoDataSourceType.AZUREBLOBSTORAGECONFIG.value,
        ):
            return urllib3.PoolManager(headers=ADLS_HEADERS)
        elif self.datasource_type == DatasourceDtoDataSourceType.GENERICS3CONFIG.value:
            return urllib3.PoolManager(assert_hostname=False)
        else:
            return urllib3.PoolManager()

    def _get_credential_override(self) -> Dict[str, str]:
        """Gets credentials override by merging service overrides and user overrides"""
        credentials = {}

        if self.auth_type == DatasourceDtoAuthType.OAUTH.value:
            credentials = load_oauth_credentials()

        if self.auth_type in (
            DatasourceDtoAuthType.AWSIAMROLE.value,
            DatasourceDtoAuthType.AWSIAMROLEWITHUSERNAME.value,
        ):
            credentials = load_aws_credentials(
                os.getenv(AWS_SHARED_CREDENTIALS_FILE, ""),
                getattr(self._config_override, "profile", ""),
            )

        credentials.update(self._config_override.credential())
        return credentials

    def update(self, config: DatasourceConfig) -> None:
        """Store configuration override for future query calls.

        Args:
            config: specific datasource config class
        """
        self._config_override = config

    def reset_config(self) -> None:
        """Reset the configuration override."""
        self._config_override = Config()


@attr.s
class TabularDatasource(Datasource):
    """Represents a tabular type datasource."""
    
    _db_type_override = attr.ib(default=None, init=False, repr=False)
    _debug_sql = attr.ib(default=False, init=False, repr=False)
    _logger = attr.ib(factory=lambda: logging.getLogger(__name__), init=False, repr=False)
    _type_map = attr.ib(factory=dict, init=False, repr=False)
    _varchar_small_threshold = attr.ib(default=50, init=False)
    _varchar_medium_threshold = attr.ib(default=255, init=False)

    def query(self, query: str) -> Result:
        """Execute a query against the datasource.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Result: Query result object
        """
        if self._debug_sql:
            self._logger.debug(f"Executing SQL: {query}")
        return self.client.execute(
            self.identifier,
            query,
            config=self._config_override.config(),
            credential=self._get_credential_override(),
        )
    
    def wrap_passthrough_query(self, query: str) -> str:
        """
        Wrap a query for database passthrough to bypass query engine optimization.
        
        Uses system.query() table function to execute the query directly
        on the data source, avoiding query engine transformations that may change
        results or performance characteristics.
        
        Args:
            query: The SQL query to wrap
            
        Returns:
            str: Wrapped query using passthrough function
            
        Examples:
            # Force a complex join to execute on the data source
            complex_query = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id ORDER BY u.created_date"
            wrapped = ds.wrap_passthrough_query(complex_query)
            result = ds.query(wrapped)
            
            # Use data source-specific (non-ANSI) functions
            db_specific = "SELECT user_id, REGEXP_EXTRACT(email, '@(.*)') as domain FROM users"
            wrapped = ds.wrap_passthrough_query(db_specific)
            result = ds.query(wrapped)
        """
        # Escape single quotes in the query
        escaped_query = query.replace("'", "''")
        
        # Wrap with system.query table function
        return f"SELECT * FROM TABLE(system.query(query => '{escaped_query}'))"

    def passthrough_query(self, query: str) -> Result:
        """
        Execute a query using database passthrough wrapper.
        
        This method wraps and executes the query with system.query() to:
        - Force operations to execute on the data source
        - Bypass query engine optimization that may change results
        - Allow use of data source-specific (non-ANSI) functions
        - Improve performance for complex operations
        
        Args:
            query: SQL query to execute with passthrough
            
        Returns:
            Result: Query result object
            
        Examples:
            # Use instead of query() for complex operations
            result = ds.passthrough_query("SELECT * FROM large_table ORDER BY complex_calculation(col1, col2)")
            
            # Force predicate pushdown
            result = ds.passthrough_query("SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id WHERE t1.status = 'active'")
        """
        wrapped_query_str = self.wrap_passthrough_query(query)
        
        if self._debug_sql:
            self._logger.debug(f"Executing passthrough query: {wrapped_query_str}")
        
        return self.query(wrapped_query_str)
    
    def __attrs_post_init__(self):
        """Initialize database-specific type mappings."""
        self._type_mappings = {
            'postgresql': {
                bool: "BOOLEAN",
                int: "INTEGER",
                float: "DOUBLE PRECISION",
                str: "VARCHAR(255)",
                datetime: "TIMESTAMP",
                date: "DATE",
                Decimal: "NUMERIC",
                dict: "JSONB",  # Improved: Use JSONB for better performance
                list: "JSONB",  # Improved: Use JSONB for arrays
                pandas.Int64Dtype: "BIGINT",  # Improved: Use BIGINT for large integers
                pandas.Float64Dtype: "DOUBLE PRECISION",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "BOOLEAN",
                pandas.DatetimeTZDtype: "TIMESTAMPTZ",  # Improved: Use timezone-aware type
                numpy.int8: "SMALLINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "BIGINT",  # Improved: Use BIGINT for int64
                numpy.float32: "REAL",
                numpy.float64: "DOUBLE PRECISION",
                numpy.bool_: "BOOLEAN",  # Added: numpy boolean support
                bytes: "BYTEA",  # Added: binary data support
            },
            'mysql': {
                bool: "BOOLEAN",
                int: "INTEGER",
                float: "DOUBLE",
                str: "VARCHAR(255)",
                datetime: "DATETIME",
                date: "DATE",
                Decimal: "DECIMAL(65,30)",  # Improved: Specify precision
                dict: "JSON",  # Improved: Use native JSON type
                list: "JSON",  # Improved: Use native JSON type
                pandas.Int64Dtype: "BIGINT",  # Improved: Use BIGINT for large integers
                pandas.Float64Dtype: "DOUBLE",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "BOOLEAN",
                pandas.DatetimeTZDtype: "DATETIME",
                numpy.int8: "TINYINT",  # Improved: Use TINYINT for int8
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "BIGINT",  # Improved: Use BIGINT for int64
                numpy.float32: "FLOAT",
                numpy.float64: "DOUBLE",
                numpy.bool_: "BOOLEAN",  # Added: numpy boolean support
                bytes: "LONGBLOB",  # Added: binary data support
            },
            'db2': {
                bool: "SMALLINT",  # DB2 doesn't have native BOOLEAN
                int: "INTEGER",
                float: "DOUBLE",
                str: "VARCHAR(255)",
                datetime: "TIMESTAMP",
                date: "DATE",
                Decimal: "DECIMAL(31,0)",  # Improved: Specify DB2's max precision
                dict: "CLOB",  # Improved: Use CLOB for large JSON objects
                list: "CLOB",  # Improved: Use CLOB for large arrays
                pandas.Int64Dtype: "BIGINT",  # Improved: Use BIGINT for large integers
                pandas.Float64Dtype: "DOUBLE",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "SMALLINT",
                pandas.DatetimeTZDtype: "TIMESTAMP",
                numpy.int8: "SMALLINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "BIGINT",  # Improved: DB2 supports BIGINT
                numpy.float32: "REAL",
                numpy.float64: "DOUBLE",
                numpy.bool_: "SMALLINT",  # Added: numpy boolean support
                bytes: "BLOB",  # Added: binary data support
            },
            'oracle': {
                bool: "NUMBER(1)",
                int: "NUMBER",
                float: "BINARY_DOUBLE",
                str: "VARCHAR2(255)",
                datetime: "TIMESTAMP",
                date: "DATE",
                Decimal: "NUMBER(38,10)",  # Improved: Specify precision
                dict: "CLOB",  # Improved: Use CLOB for JSON (Oracle 12c+ has JSON type)
                list: "CLOB",  # Improved: Use CLOB for arrays
                pandas.Int64Dtype: "NUMBER(19)",  # Improved: Specify precision for large integers
                pandas.Float64Dtype: "BINARY_DOUBLE",
                pandas.StringDtype: "VARCHAR2(255)",
                pandas.BooleanDtype: "NUMBER(1)",
                pandas.DatetimeTZDtype: "TIMESTAMP WITH TIME ZONE",  # Improved: Use timezone-aware type
                numpy.int8: "NUMBER(3)",  # Improved: Specify precision
                numpy.int16: "NUMBER(5)",  # Improved: Specify precision
                numpy.int32: "NUMBER(10)",  # Improved: Specify precision
                numpy.int64: "NUMBER(19)",  # Improved: Specify precision
                numpy.float32: "BINARY_FLOAT",
                numpy.float64: "BINARY_DOUBLE",
                numpy.bool_: "NUMBER(1)",  # Added: numpy boolean support
                bytes: "BLOB",  # Added: binary data support
            },
            'sqlserver': {
                bool: "BIT",
                int: "INT",
                float: "FLOAT",
                str: "NVARCHAR(255)",
                datetime: "DATETIME2",
                date: "DATE",
                Decimal: "DECIMAL(38,10)",  # Improved: Specify precision
                dict: "NVARCHAR(MAX)",  # Improved: Use MAX for large JSON
                list: "NVARCHAR(MAX)",  # Improved: Use MAX for large arrays
                pandas.Int64Dtype: "BIGINT",
                pandas.Float64Dtype: "FLOAT",
                pandas.StringDtype: "NVARCHAR(255)",
                pandas.BooleanDtype: "BIT",
                pandas.DatetimeTZDtype: "DATETIMEOFFSET",
                numpy.int8: "TINYINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INT",
                numpy.int64: "BIGINT",
                numpy.float32: "REAL",
                numpy.float64: "FLOAT",
                numpy.bool_: "BIT",  # Added: numpy boolean support
                bytes: "VARBINARY(MAX)",  # Added: binary data support
            },
            'unknown': {
                bool: "BOOLEAN",
                int: "INTEGER",
                float: "FLOAT",
                str: "VARCHAR(255)",
                datetime: "TIMESTAMP",
                date: "DATE",
                Decimal: "NUMERIC",
                dict: "VARCHAR(4000)",
                list: "VARCHAR(4000)",
                pandas.Int64Dtype: "INTEGER",
                pandas.Float64Dtype: "FLOAT",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "BOOLEAN",
                pandas.DatetimeTZDtype: "TIMESTAMP",
                numpy.int8: "SMALLINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "INTEGER",
                numpy.float32: "REAL",
                numpy.float64: "FLOAT",
                numpy.bool_: "BOOLEAN",  # Added: numpy boolean support
                bytes: "VARBINARY(4000)",  # Added: binary data support
            }
        }

        # Set current database type mapping
        db_type = self.get_db_type()
        self._type_map = self._type_mappings.get(db_type, self._type_mappings['unknown'])

    _db_type = None

    def set_db_type_override(self, db_type: str) -> None:
        """Override the detected database type. Use with caution.

        Args:
            db_type: Database type to force (e.g., 'db2', 'postgresql', 'mysql', 'oracle', 'sqlserver').
                    Pass None to remove the override and re-enable auto-detection.

        Raises:
            ValueError: If an unsupported database type is provided.

        Examples:
            # Force DB2 detection
            datasource.set_db_type_override('db2')
            
            # Force PostgreSQL detection
            datasource.set_db_type_override('postgresql')
            
            # Remove override and re-enable auto-detection
            datasource.set_db_type_override(None)
        """
        if db_type is not None:
            db_type_lower = db_type.lower()
            supported_types = {'postgresql', 'mysql', 'db2', 'oracle', 'sqlserver', 'unknown'}
            
            if db_type_lower not in supported_types:
                raise ValueError(
                    f"Unsupported database type: '{db_type}'. "
                    f"Supported types are: {', '.join(sorted(supported_types))}"
                )
            
            self._db_type_override = db_type_lower
            if self._debug_sql:
                self._logger.info(f"Database type override set to: {db_type_lower}")
        else:
            self._db_type_override = None
            if self._debug_sql:
                self._logger.info("Database type override removed - auto-detection re-enabled")
        
        # Clear cached detection result to force re-detection
        self._db_type = None
        
        # Update type mappings for the new database type
        db_type_to_use = self.get_db_type()
        self._type_map = self._type_mappings.get(db_type_to_use, self._type_mappings['unknown'])
        
        if self._debug_sql:
            self._logger.debug(f"Type mappings updated for database type: {db_type_to_use}")

    def get_db_type_override(self) -> Optional[str]:
        """Get the current database type override.

        Returns:
            str or None: Current database type override, or None if auto-detection is enabled.
        """
        return self._db_type_override

    def get_supported_db_types(self) -> List[str]:
        """Get list of supported database types for manual override.

        Returns:
            List[str]: List of supported database type identifiers.
        """
        return sorted(list(self._type_mappings.keys()))
    
    def reset_db_type_detection(self) -> None:
        """Reset cached database type detection to force re-detection."""
        self._db_type = None
        self._db_type_override = None
        # Update type mappings
        db_type = self.get_db_type()
        self._type_map = self._type_mappings.get(db_type, self._type_mappings['unknown'])
        if self._debug_sql:
            self._logger.info("Database type detection reset")

    def get_db_type(self) -> str:
        """Return the database type, respecting overrides.

        Returns:
            str: Detected or overridden database type.
        """
        if self._db_type_override is not None:
            return self._db_type_override

        if self._db_type is not None:
            return self._db_type

        # Try raw connection first with enhanced detection
        try:
            conn = self.client.raw_connection()
            
            if self._detect_postgresql_connection(conn):
                self._db_type = 'postgresql'
            elif self._detect_mysql_connection(conn):
                self._db_type = 'mysql'
            elif self._detect_db2_connection(conn):
                self._db_type = 'db2'
            elif self._detect_oracle_connection(conn):
                self._db_type = 'oracle'
            elif self._detect_sqlserver_connection(conn):
                self._db_type = 'sqlserver'
            else:
                self._db_type = 'unknown'
        except Exception:
            self._db_type = 'unknown'

        # Enhanced fallback to version query (only if needed)
        if self._db_type == 'unknown':
            try:
                # Try PostgreSQL-specific version queries first
                postgresql_version_queries = [
                    "SELECT version()",
                    "SHOW server_version",
                    "SELECT current_setting('server_version')"
                ]
                
                for query in postgresql_version_queries:
                    try:
                        version_info = self.query(query).to_pandas().iat[0, 0].lower()
                        if any(indicator in version_info for indicator in ['postgresql', 'postgres']):
                            self._db_type = 'postgresql'
                            break
                    except Exception:
                        continue
                
                # Try MySQL-specific version queries
                if self._db_type == 'unknown':
                    mysql_version_queries = [
                        "SELECT VERSION()",
                        "SHOW VARIABLES LIKE 'version'",
                        "SELECT @@version"
                    ]
                    
                    for query in mysql_version_queries:
                        try:
                            version_info = self.query(query).to_pandas().iat[0, 0].lower()
                            if any(indicator in version_info for indicator in ['mysql', 'mariadb']):
                                self._db_type = 'mysql'
                                break
                        except Exception:
                            continue
                
                # Try SQL Server-specific version queries
                if self._db_type == 'unknown':
                    sqlserver_version_queries = [
                        "SELECT @@VERSION",
                        "SELECT SERVERPROPERTY('ProductVersion')",
                        "SELECT SERVERPROPERTY('Edition')"
                    ]
                    
                    for query in sqlserver_version_queries:
                        try:
                            version_info = self.query(query).to_pandas().iat[0, 0].lower()
                            if any(indicator in version_info for indicator in ['microsoft', 'sql server', 'azure sql']):
                                self._db_type = 'sqlserver'
                                break
                        except Exception:
                            continue
                
                # Try Oracle-specific version queries
                if self._db_type == 'unknown':
                    oracle_version_queries = [
                        "SELECT BANNER FROM V$VERSION WHERE BANNER LIKE 'Oracle Database%'",
                        "SELECT VERSION FROM PRODUCT_COMPONENT_VERSION WHERE PRODUCT LIKE 'Oracle Database%'",
                        "SELECT VERSION FROM V$INSTANCE",
                        "SELECT * FROM V$VERSION"
                    ]
                    
                    for query in oracle_version_queries:
                        try:
                            version_info = self.query(query).to_pandas().iat[0, 0].lower()
                            if any(indicator in version_info for indicator in ['oracle', 'database']):
                                self._db_type = 'oracle'
                                break
                        except Exception:
                            continue
                
                # Try DB2-specific version queries
                if self._db_type == 'unknown':
                    db2_version_queries = [
                        "SELECT SERVICE_LEVEL FROM SYSIBMADM.ENV_INST_INFO",
                        "SELECT PROD_RELEASE FROM SYSIBM.SYSVERSIONS WHERE VERSION_TYPE = 'DB2'",
                        "VALUES(DB2_VERSION())"
                    ]
                    
                    for query in db2_version_queries:
                        try:
                            version_info = self.query(query).to_pandas().iat[0, 0].lower()
                            if any(indicator in version_info for indicator in ['db2', 'ibm']):
                                self._db_type = 'db2'
                                break
                        except Exception:
                            continue
            except Exception:
                pass

        # Enhanced database-specific fallback with multiple detection queries
        if self._db_type == 'unknown':
            # PostgreSQL detection queries
            postgresql_detection_queries = [
                "SELECT 1",
                "SELECT current_database()",
                "SELECT current_user",
                "SHOW server_version_num"
            ]
            
            for query in postgresql_detection_queries:
                try:
                    res = self.query(query)
                    if not res.to_pandas().empty:
                        self._db_type = 'postgresql'
                        break
                except Exception:
                    continue

        if self._db_type == 'unknown':
            # MySQL detection queries
            mysql_detection_queries = [
                "SELECT 1",
                "SELECT DATABASE()",
                "SELECT USER()",
                "SHOW STATUS LIKE 'Uptime'"
            ]
            
            for query in mysql_detection_queries:
                try:
                    res = self.query(query)
                    if not res.to_pandas().empty:
                        self._db_type = 'mysql'
                        break
                except Exception:
                    continue

        if self._db_type == 'unknown':
            # SQL Server detection queries
            sqlserver_detection_queries = [
                "SELECT 1",
                "SELECT DB_NAME()",
                "SELECT SUSER_NAME()",
                "SELECT @@SERVERNAME"
            ]
            
            for query in sqlserver_detection_queries:
                try:
                    res = self.query(query)
                    if not res.to_pandas().empty:
                        self._db_type = 'sqlserver'
                        break
                except Exception:
                    continue

        if self._db_type == 'unknown':
            # Oracle detection queries
            oracle_detection_queries = [
                "SELECT 1 FROM DUAL",
                "SELECT SYSDATE FROM DUAL",
                "SELECT USER FROM DUAL",
                "SELECT * FROM V$VERSION WHERE ROWNUM = 1",
                "SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1"
            ]
            
            for query in oracle_detection_queries:
                try:
                    res = self.query(query)
                    if not res.to_pandas().empty:
                        self._db_type = 'oracle'
                        break
                except Exception:
                    continue

        if self._db_type == 'unknown':
            # DB2 detection queries
            db2_detection_queries = [
                "SELECT CURRENT SERVER FROM SYSIBM.SYSDUMMY1",
                "SELECT 1 FROM SYSIBM.SYSDUMMY1",
                "VALUES(CURRENT SERVER)",
                "SELECT CURRENT SCHEMA FROM SYSIBM.SYSDUMMY1",
                "SELECT CURRENT TIMESTAMP FROM SYSIBM.SYSDUMMY1"
            ]
            
            for query in db2_detection_queries:
                try:
                    res = self.query(query)
                    if not res.to_pandas().empty:
                        self._db_type = 'db2'
                        break
                except Exception:
                    continue

        if self._debug_sql:
            self._logger.debug(f"Using database type: {self._db_type}")

        return self._db_type

    def _detect_postgresql_connection(self, conn) -> bool:
        """Enhanced PostgreSQL connection detection.
        
        Args:
            conn: Database connection object
            
        Returns:
            bool: True if connection appears to be PostgreSQL
        """
        try:
            # Check for PostgreSQL-specific attributes first
            if hasattr(conn, 'pgconn'):
                return True
                
            # Check connection type string with multiple indicators
            conn_type_str = str(type(conn)).lower()
            postgresql_indicators = [
                'postgresql', 'postgres', 'psycopg', 'pg8000', 'py-postgresql'
            ]
            
            if any(indicator in conn_type_str for indicator in postgresql_indicators):
                return True
                
            # Check for PostgreSQL-specific connection attributes
            if hasattr(conn, 'server_version'):
                try:
                    version_info = str(conn.server_version).lower()
                    if 'postgresql' in version_info or 'postgres' in version_info:
                        return True
                except Exception:
                    pass
                    
            # Check for PostgreSQL-specific methods
            postgresql_methods = ['commit', 'rollback', 'cursor', 'close']
            if all(hasattr(conn, method) for method in postgresql_methods):
                # Additional PostgreSQL-specific attribute checks
                if hasattr(conn, 'dsn') or hasattr(conn, 'encoding'):
                    return True
                    
            return False
            
        except Exception:
            return False

    def _detect_mysql_connection(self, conn) -> bool:
        """Enhanced MySQL connection detection.
        
        Args:
            conn: Database connection object
            
        Returns:
            bool: True if connection appears to be MySQL
        """
        try:
            # Check connection type string with multiple indicators
            conn_type_str = str(type(conn)).lower()
            mysql_indicators = [
                'mysql', 'mariadb', 'pymysql', 'mysqldb', 'mysql.connector',
                'aiomysql', 'mysql-connector'
            ]
            
            if any(indicator in conn_type_str for indicator in mysql_indicators):
                return True
                
            # Check for MySQL-specific connection attributes
            if hasattr(conn, 'get_server_info'):
                try:
                    server_info = str(conn.get_server_info()).lower()
                    if 'mysql' in server_info or 'mariadb' in server_info:
                        return True
                except Exception:
                    pass
                    
            # Check for MySQL-specific methods
            mysql_methods = ['commit', 'rollback', 'cursor', 'ping']
            if all(hasattr(conn, method) for method in mysql_methods):
                # Additional MySQL-specific attribute checks
                if hasattr(conn, 'charset') or hasattr(conn, 'autocommit'):
                    return True
                    
            return False
            
        except Exception:
            return False

    def _detect_sqlserver_connection(self, conn) -> bool:
        """Enhanced SQL Server connection detection.
        
        Args:
            conn: Database connection object
            
        Returns:
            bool: True if connection appears to be SQL Server
        """
        try:
            # Check connection type string with multiple indicators
            conn_type_str = str(type(conn)).lower()
            sqlserver_indicators = [
                'sqlserver', 'mssql', 'pyodbc', 'pymssql', 'turbodbc',
                'microsoft', 'sql server', 'azure'
            ]
            
            if any(indicator in conn_type_str for indicator in sqlserver_indicators):
                return True
                
            # Check for SQL Server-specific connection attributes
            if hasattr(conn, 'getinfo'):
                try:
                    # ODBC-specific check for SQL Server
                    dbms_name = conn.getinfo(17)  # SQL_DBMS_NAME
                    if 'microsoft' in str(dbms_name).lower() or 'sql server' in str(dbms_name).lower():
                        return True
                except Exception:
                    pass
                    
            # Check for SQL Server-specific methods
            sqlserver_methods = ['commit', 'rollback', 'cursor', 'execute']
            if all(hasattr(conn, method) for method in sqlserver_methods):
                # Additional SQL Server-specific attribute checks
                if hasattr(conn, 'timeout') or hasattr(conn, 'autocommit'):
                    return True
                    
            return False
            
        except Exception:
            return False

    def _detect_oracle_connection(self, conn) -> bool:
        """Enhanced Oracle connection detection.
        
        Args:
            conn: Database connection object
            
        Returns:
            bool: True if connection appears to be Oracle
        """
        try:
            # Check connection type string with multiple indicators
            conn_type_str = str(type(conn)).lower()
            oracle_indicators = [
                'oracle', 'cx_oracle', 'oracledb', 'python-oracledb',
                'thick', 'thin', 'oracle.jdbc'
            ]
            
            if any(indicator in conn_type_str for indicator in oracle_indicators):
                return True
                
            # Check for Oracle-specific connection attributes
            if hasattr(conn, 'version'):
                try:
                    version_info = str(conn.version).lower()
                    if 'oracle' in version_info:
                        return True
                except Exception:
                    pass
                    
            # Check for Oracle-specific methods
            oracle_methods = ['ping', 'commit', 'rollback', 'cursor']
            if all(hasattr(conn, method) for method in oracle_methods):
                # Additional Oracle-specific attribute checks
                if hasattr(conn, 'dsn') or hasattr(conn, 'tnsentry'):
                    return True
                    
            return False
            
        except Exception:
            return False

    def _detect_db2_connection(self, conn) -> bool:
        """Enhanced DB2 connection detection.
        
        Args:
            conn: Database connection object
            
        Returns:
            bool: True if connection appears to be DB2
        """
        try:
            # Check connection type string with multiple indicators
            conn_type_str = str(type(conn)).lower()
            db2_indicators = [
                'db2', 'ibm_db', 'ibm_db_dbi', 'jaydebeapi',
                'ibmdb', 'db2_cli', 'ibm_db_sa'
            ]
            
            if any(indicator in conn_type_str for indicator in db2_indicators):
                return True
                
            # Check for DB2-specific connection attributes
            if hasattr(conn, 'server_info'):
                try:
                    server_info = str(conn.server_info()).lower()
                    if 'db2' in server_info or 'ibm' in server_info:
                        return True
                except Exception:
                    pass
                    
            # Check for DB2-specific methods
            db2_methods = ['get_option', 'set_option', 'server_info']
            if all(hasattr(conn, method) for method in db2_methods):
                return True
                
            return False
            
        except Exception:
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if the table exists, False otherwise
        """
        try:
            escaped_table = self._escape_identifier(table_name)
            self.query(f"SELECT 1 FROM {escaped_table} LIMIT 1")
            return True
        except DominoError:
            return False

    def write_dataframe(
        self,
        table_name: str,
        dataframe: pandas.DataFrame,
        if_table_exists: str = 'fail',
        chunksize: Optional[int] = None,  # Changed: None means auto-optimize
        handle_mixed_types: bool = True,
        force: bool = False,
        auto_optimize_chunks: bool = True,  # New: Enable auto-optimization by default
        max_message_size_mb: float = 4.0,  # New: gRPC message size limit
    ) -> None:
        """
        Write a DataFrame to a table in the datasource.

        Args:
            table_name: Name of the table to write to
            dataframe: DataFrame containing the data to write
            if_table_exists: Action if table exists:
                - 'fail': Raise an error if table exists (default)
                - 'replace': Drop and recreate the table
                - 'append': Append data to the existing table
                - 'truncate': Empty the table but keep its structure
            chunksize: Number of rows to insert in each batch for large DataFrames
            handle_mixed_types: If True, detect and handle mixed types in object columns
            force: If True, attempt to append data even if schema compatibility issues are detected

        Raises:
            ValueError: If operation cannot be completed safely

        Examples:
            # Create a new table, fail if it already exists (default)
            datasource.write_dataframe("my_table", df)

            # Replace an existing table if it exists
            datasource.write_dataframe("my_table", df, if_table_exists='replace')

            # Append data to an existing table (will check schema compatibility)
            datasource.write_dataframe("my_table", df, if_table_exists='append')

            # Truncate an existing table and add new data
            datasource.write_dataframe("my_table", df, if_table_exists='truncate')

            # Force append even if there are schema compatibility issues (not recommended)
            datasource.write_dataframe("my_table", df, if_table_exists='append', force=True)
        """
        import time
        start_time = time.perf_counter()
        
        # Determine chunk size strategy
        if chunksize is not None:
            # Manual chunk size provided - use it
            optimal_chunk_size = chunksize
            if self._debug_sql:
                self._logger.debug(f"Using manual chunk size: {optimal_chunk_size:,} rows")
        elif auto_optimize_chunks:
            # Auto-optimize chunk size
            optimal_chunk_size = self.calculate_optimal_chunk_size(
                dataframe, 
                max_message_size_mb=max_message_size_mb
            )
            
            # Estimate message size with optimal chunk
            estimated_size_mb = self.estimate_message_size(dataframe, optimal_chunk_size)
            
            if self._debug_sql:
                self._logger.debug(f"Auto-optimized chunk size: {optimal_chunk_size:,} rows")
                self._logger.debug(f"Estimated message size: {estimated_size_mb:.2f} MB")
                
                if estimated_size_mb > max_message_size_mb:
                    self._logger.warning(f"Estimated size ({estimated_size_mb:.2f} MB) exceeds limit ({max_message_size_mb} MB)")
        else:
            # Use default chunk size
            optimal_chunk_size = 20000
            if self._debug_sql:
                self._logger.debug(f"Using default chunk size: {optimal_chunk_size:,} rows")

        if self._debug_sql:
            total_chunks = (len(dataframe) + optimal_chunk_size - 1) // optimal_chunk_size
            self._logger.debug(f"Write operation details:")
            self._logger.debug(f"  Table: {table_name}")
            self._logger.debug(f"  Rows: {len(dataframe):,}")
            self._logger.debug(f"  Chunks: {total_chunks}")
            self._logger.debug(f"  Mode: {if_table_exists}")
            self._logger.debug(f"  Auto-optimize: {auto_optimize_chunks}")

        table_created = False
        try:
            # Check if table exists
            table_exists = self.table_exists(table_name)

            if table_exists:
                if if_table_exists == 'fail':
                    raise ValueError(f"Table '{table_name}' already exists.")
                elif if_table_exists == 'replace':
                    # Replace existing table
                    self._drop_and_create_table(table_name, dataframe)
                    table_created = True
                elif if_table_exists == 'truncate':
                    # Truncate existing table
                    if not force:
                        self._check_schema_compatibility(table_name, dataframe)
                    self._truncate_table(table_name)
                elif if_table_exists == 'append':
                    if not force:
                        self._check_schema_compatibility(table_name, dataframe)
                else:
                    raise ValueError(f"Invalid option for if_table_exists: {if_table_exists}")
            else:
                # Create new table
                self._create_table(table_name, dataframe)
                table_created = True

            # Insert data with optimized chunk size
            self._insert_dataframe(table_name, dataframe, optimal_chunk_size)
            
            # Performance metrics
            if self._debug_sql:
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                rows_per_second = len(dataframe) / elapsed_time if elapsed_time > 0 else 0
                mb_per_second = (dataframe.memory_usage(deep=True).sum() / (1024*1024)) / elapsed_time if elapsed_time > 0 else 0
                
                self._logger.debug(f"Write operation completed successfully!")
                self._logger.debug(f"Performance metrics:")
                self._logger.debug(f"  Execution time: {elapsed_time:.2f} seconds")
                self._logger.debug(f"  Throughput: {rows_per_second:,.0f} rows/second")
                self._logger.debug(f"  Data rate: {mb_per_second:.1f} MB/second")

        except Exception as e:
            if table_created:
                self._drop_table_quietly(table_name)
            
            # Enhanced error context
            if self._debug_sql:
                self._logger.error(f"Write operation failed: {str(e)}")
                if "grpc: received message larger than max" in str(e):
                    self._logger.error(f"Suggestion: Try reducing max_message_size_mb parameter or manual chunksize")
            
            raise  # Re-raise after cleanup

    def _drop_table_quietly(self, table_name: str) -> None:
        """Attempt to drop table without raising errors."""
        try:
            escaped_table = self._escape_identifier(table_name)
            self.query(f"DROP TABLE {escaped_table}")
            if self._debug_sql:
                self._logger.debug(f"Cleaned up table after failed write: {table_name}")
        except Exception as drop_error:
            self._logger.error(
                f"Failed to clean up table {table_name} after error: {str(drop_error)}"
            )

    def _drop_and_create_table(self, table_name: str, dataframe: pandas.DataFrame) -> None:
        """
        Drop existing table and create a new one with the DataFrame's schema.

        Args:
            table_name: Name of the table to replace.
            dataframe: DataFrame containing the new schema and data.
        """
        escaped_table = self._escape_identifier(table_name)
        
        # Drop existing table
        try:
            self.query(f"DROP TABLE {escaped_table}")
        except Exception as e:
            self._logger.warning(f"Error dropping table {table_name}: {str(e)}")
            raise

        # Create new table
        self._create_table(table_name, dataframe)

    def _create_table(self, table_name: str, dataframe: pandas.DataFrame) -> None:
        """Create a new table with the DataFrame's schema."""
        escaped_table = self._escape_identifier(table_name)
        schema = self._generate_schema(dataframe)
        create_query = f"CREATE TABLE {escaped_table} ({schema})"
        if self._debug_sql:
            self._logger.debug(f"Executing SQL: {create_query}")
        self.query(create_query)

    def _truncate_table(self, table_name: str) -> None:
        """Truncate an existing table."""
        escaped_table = self._escape_identifier(table_name)
        
        # Try TRUNCATE first, fall back to DELETE
        truncate_query = f"TRUNCATE TABLE {escaped_table}"
        if self._debug_sql:
            self._logger.debug(f"Executing SQL: {truncate_query}")
        try:
            self.query(truncate_query)
        except Exception as e:
            # Some databases don't support TRUNCATE, fall back to DELETE
            delete_query = f"DELETE FROM {escaped_table}"
            if self._debug_sql:
                self._logger.debug(f"TRUNCATE failed, executing SQL: {delete_query}")
            self.query(delete_query)

    def calculate_optimal_chunk_size(self, dataframe: pandas.DataFrame, max_message_size_mb: float = 4.0, safety_factor: float = 0.8) -> int:
        """
        Calculate optimal chunk size to maximize performance while staying under gRPC limits.
        
        Args:
            dataframe: DataFrame to analyze
            max_message_size_mb: Maximum message size in MB (default 3.5MB to stay under 4MB limit)
            safety_factor: Safety multiplier to account for serialization overhead (default 0.8)
        
        Returns:
            int: Optimal chunk size in number of rows
        """
        if len(dataframe) == 0:
            return 1000  # Default fallback
        
        # Calculate memory usage per row
        total_memory_bytes = dataframe.memory_usage(deep=True).sum()
        memory_per_row = total_memory_bytes / len(dataframe)
        
        # Account for serialization overhead (gRPC/Arrow serialization adds ~30-50% overhead)
        serialization_overhead = 1.5
        estimated_serialized_per_row = memory_per_row * serialization_overhead
        
        # Calculate max rows that fit in target message size
        max_message_bytes = max_message_size_mb * 1024 * 1024
        safe_message_bytes = max_message_bytes * safety_factor
        
        optimal_rows = int(safe_message_bytes / estimated_serialized_per_row)
        
        # Apply reasonable bounds
        min_chunk_size = 100    # Don't go too small (too many round trips)
        max_chunk_size = 50000  # Don't go too large (memory concerns)
        
        optimal_chunk_size = max(min_chunk_size, min(optimal_rows, max_chunk_size))
        
        if self._debug_sql:
            self._logger.debug(f"Chunk size calculation:")
            self._logger.debug(f"  Total rows: {len(dataframe):,}")
            self._logger.debug(f"  Memory per row: {memory_per_row:.2f} bytes")
            self._logger.debug(f"  Estimated serialized per row: {estimated_serialized_per_row:.2f} bytes")
            self._logger.debug(f"  Target message size: {max_message_size_mb:.1f} MB")
            self._logger.debug(f"  Calculated optimal chunk size: {optimal_chunk_size:,} rows")
            self._logger.debug(f"  Expected chunks: {(len(dataframe) + optimal_chunk_size - 1) // optimal_chunk_size}")
        
        return optimal_chunk_size

    def estimate_message_size(self, dataframe: pandas.DataFrame, chunk_size: int) -> float:
        """
        Estimate the serialized message size for a given chunk size.
        
        Args:
            dataframe: DataFrame to analyze
            chunk_size: Number of rows per chunk
        
        Returns:
            float: Estimated message size in MB
        """
        if len(dataframe) == 0:
            return 0
        
        # Sample a chunk to estimate size
        sample_size = min(chunk_size, len(dataframe))
        sample_chunk = dataframe.head(sample_size)
        
        # Calculate memory usage of sample
        sample_memory = sample_chunk.memory_usage(deep=True).sum()
        
        # Apply serialization overhead
        serialization_overhead = 1.5
        estimated_serialized_size = sample_memory * serialization_overhead
        
        # Scale to full chunk size
        if sample_size < chunk_size:
            estimated_serialized_size = estimated_serialized_size * (chunk_size / sample_size)
        
        estimated_mb = estimated_serialized_size / (1024 * 1024)
        
        if self._debug_sql:
            self._logger.debug(f"Message size estimation:")
            self._logger.debug(f"  Sample size: {sample_size:,} rows")
            self._logger.debug(f"  Sample memory: {sample_memory / (1024*1024):.2f} MB")
            self._logger.debug(f"  Estimated chunk size: {estimated_mb:.2f} MB")
        
        return estimated_mb

    def set_grpc_message_limits(self, max_message_size_mb: float = 64.0) -> None:
        """
        Update the default gRPC message size limits for this datasource.
        
        Args:
            max_message_size_mb: Maximum message size in MB (default 64MB)
        
        Note:
            This affects the auto-optimization calculations for future write operations.
            The actual gRPC client limits are set at the DataSourceClient level.
        """
        self._default_grpc_limit_mb = max_message_size_mb
        
        if self._debug_sql:
            self._logger.debug(f"Updated default gRPC message limit to {max_message_size_mb} MB")

    def _check_schema_compatibility(self, table_name: str, dataframe: pandas.DataFrame, force: bool = False) -> None:
        """
        Check schema compatibility between DataFrame and existing table.

        Args:
            table_name: Name of the table to check.
            dataframe: DataFrame to check compatibility with.
            force: If True, skip schema mismatch checks and proceed with warning.

        Raises:
            ValueError: If schema mismatch detected and force=False.
        """
        try:
            # Get existing table columns
            escaped_table = self._escape_identifier(table_name)
            schema_query = f"SELECT * FROM {escaped_table} LIMIT 0"
            result = self.query(schema_query)
            table_columns = result.to_pandas().columns.tolist()

            df_columns = dataframe.columns.tolist()

            # Check for missing/extra columns
            missing = set(table_columns) - set(df_columns)
            extra = set(df_columns) - set(table_columns)

            if missing or extra:
                error_msg = []
                if missing:
                    error_msg.append(f"Missing columns: {', '.join(missing)}")
                if extra:
                    error_msg.append(f"Extra columns: {', '.join(extra)}")

                if not force:
                    raise ValueError(
                        "Schema mismatch detected: " + " | ".join(error_msg) +
                        "\nUse force=True to attempt the operation anyway."
                    )
                else:
                    if self._debug_sql:
                        self._logger.warning(
                            "Forcing write despite schema mismatch: " + " | ".join(error_msg)
                        )

            return

            # Check column types (if metadata available)
            try:
                self._check_column_types(table_name, dataframe, table_columns, force)
            except Exception as type_err:
                if not force:
                    raise ValueError(
                        "Type mismatch detected. " +
                        str(type_err) +
                        "\nUse force=True to attempt the operation anyway."
                    )
                else:
                    if self._debug_sql:
                        self._logger.warning(
                            f"Forcing write despite type mismatch: {str(type_err)}"
                        )

        except Exception as e:
            if self._debug_sql:
                self._logger.error(f"Schema check failed: {str(e)}")
            if not force:
                raise ValueError(
                    "Cannot write to table - schema mismatch detected. "
                    "Use force=True to attempt the operation anyway."
                ) from e


    def _check_column_types(self, table_name: str, dataframe: pandas.DataFrame, table_columns: list, force: bool = False) -> None:
        """
        Check column type compatibility between DataFrame and existing table.

        Args:
            table_name: Name of the table to check.
            dataframe: DataFrame to check compatibility with.
            table_columns: List of column names in the table.
            force: If True, skip type mismatch checks and proceed with warning.

        Raises:
            ValueError: If type mismatch detected and force=False.
        """
        try:
            # Try different ways to get column metadata
            queries_to_try = []
            if '.' in table_name:
                schema_part, table_part = table_name.split('.', 1)
                queries_to_try = [
                    f"""SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = '{schema_part}'
                    AND table_name = '{table_part}'""",
                    f"""SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE LOWER(table_schema) = LOWER('{schema_part}')
                    AND LOWER(table_name) = LOWER('{table_part}')""",
                ]
            else:
                queries_to_try = [
                    f"""SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'"""
                ]

            columns_info = None
            for query in queries_to_try:
                try:
                    columns_info = self.query(query.strip())
                    if columns_info.to_pandas().shape[0] > 0:
                        break
                except Exception:
                    continue

            if columns_info is None or columns_info.to_pandas().empty:
                if self._debug_sql:
                    self._logger.warning(
                        f"Could not retrieve type info for table '{table_name}'. "
                        "Skipping type validation."
                    )
                return

            # Proceed with type checks if metadata is available
            columns_df = columns_info.to_pandas()
            table_column_types = {
                row['column_name']: row['data_type']
                for row in columns_df.to_dict('records')
            }

            type_mismatches = []
            for col in table_columns:
                df_type = self._map_dtype_to_sql(dataframe[col].dtype, dataframe[col])
                table_type = table_column_types.get(col, "").upper()
                if not self._are_types_compatible(df_type, table_type):
                    type_mismatches.append(f"Column '{col}': {df_type} vs {table_type}")

            if type_mismatches:
                if not force:
                    raise ValueError("Type mismatch: " + ", ".join(type_mismatches))
                else:
                    if self._debug_sql:
                        self._logger.warning(
                            "Forcing write despite type mismatch: " + ", ".join(type_mismatches)
                        )

        except Exception as e:
            if self._debug_sql:
                self._logger.warning(f"Type validation skipped: {str(e)}")
            if not force:
                raise ValueError(
                    "Type validation failed. " +
                    str(e) +
                    "\nUse force=True to attempt the operation anyway."
                )

    def _are_types_compatible(self, sql_type: str, table_type: str) -> bool:
        """Check if two SQL types are compatible for appending data."""
        # Exact match
        if sql_type == table_type:
            return True
            
        # Integer types can be safely inserted into wider integer types
        if "SMALLINT" in sql_type and any(t in table_type for t in ["INTEGER", "BIGINT"]):
            return True
        if "INTEGER" in sql_type and "BIGINT" in table_type:
            return True
            
        # Numeric types can go into wider numeric types
        if "INTEGER" in sql_type and any(t in table_type for t in ["FLOAT", "DOUBLE", "NUMERIC"]):
            return True
            
        # String types can go into wider string types
        if "VARCHAR" in sql_type and "TEXT" in table_type:
            return True
        if "VARCHAR" in sql_type and "VARCHAR" in table_type:
            # Check VARCHAR length
            try:
                df_length = int(sql_type.replace("VARCHAR(", "").replace(")", ""))
                table_length = int(table_type.replace("VARCHAR(", "").replace(")", ""))
                return df_length <= table_length
            except:
                # If we can't parse the lengths, assume incompatible
                return False
                
        # Default to incompatible
        return False

    def _escape_identifier(self, identifier: str) -> str:
        """Escape an SQL identifier (table or column name).
        
        Handles schema.table notation properly for cross-database compatibility.
        Uses SQL standard double quotes which work across most database systems.
        
        Args:
            identifier: The identifier to escape
            
        Returns:
            str: The escaped identifier
        """
        # Handle schema.table notation
        if '.' in identifier:
            parts = identifier.split('.', 1)  # Split only on first dot to handle cases like catalog.schema.table
            schema = parts[0].strip()
            table = parts[1].strip()
            
            # Remove existing quotes if present and re-quote properly
            schema = schema.strip('"').strip('`').strip('[').strip(']')
            table = table.strip('"').strip('`').strip('[').strip(']')
            
            # Return properly quoted schema.table using SQL standard double quotes
            return f'"{schema}"."{table}"'
        else:
            # Single identifier - remove existing quotes and re-quote with double quotes
            clean_identifier = identifier.strip('"').strip('`').strip('[').strip(']')
            return f'"{clean_identifier}"'

    def _handle_dataframe_mixed_types(self, dataframe: pandas.DataFrame) -> pandas.DataFrame:
        """Process a DataFrame to handle mixed types in object columns.
        
        Args:
            dataframe: DataFrame to process
            
        Returns:
            pandas.DataFrame: DataFrame with mixed types handled
        """
        result = dataframe.copy()
        
        for col in dataframe.select_dtypes(include=['object']).columns:
            handled_series, _, is_mixed = self._detect_and_handle_mixed_types(dataframe[col])
            if is_mixed:
                result[col] = handled_series
                if self._debug_sql:
                    self._logger.debug(f"Handled mixed types in column '{col}'")
        
        return result

    def _detect_and_handle_mixed_types(self, series):
        """Detect and handle mixed types in a pandas Series."""
        if series.dtype != 'object' or len(series) == 0:
            return series, None, False

        inferred_type = pandas.api.types.infer_dtype(series)
        if 'mixed' not in inferred_type:
            return series, None, False

        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return series, "VARCHAR(255)", False

        types = non_null_series.apply(type).value_counts()

        if len(types) <= 1:
            return series, None, False

        numeric_types = {
            int,
            float,
            numpy.int64,
            numpy.float64,
            numpy.int32,
            numpy.float32
        }
        series_types = set(types.index)

        if series_types.issubset(numeric_types):
            handled = pandas.to_numeric(series, errors='coerce')
            return handled, "DOUBLE", True

        if str in series_types or any(issubclass(t, str) for t in series_types):
            handled = series.astype(str)
            max_len = handled.str.len().max()
            if max_len < self._varchar_small_threshold:
                sql_type = f"VARCHAR({max_len + 10})"
            elif max_len < self._varchar_medium_threshold:
                sql_type = f"VARCHAR({self._varchar_medium_threshold})"
            else:
                sql_type = "VARCHAR(4000)"
            return handled, sql_type, True

        try:
            handled = series.apply(lambda x: json.dumps(x) if x is not None else None)
            return handled, "VARCHAR(4000)", True
        except Exception as e:
            if self._debug_sql:
                self._logger.debug(f"JSON conversion failed: {e}, falling back to string")
            handled = series.astype(str)
            return handled, "VARCHAR(4000)", True

    def _generate_schema(self, dataframe: pandas.DataFrame) -> str:
        """Generate SQL schema from DataFrame.
        
        Args:
            dataframe: DataFrame to generate schema from
            
        Returns:
            str: SQL schema definition
        """
        columns = []
        for col, dtype in dataframe.dtypes.items():
            escaped_col = self._escape_identifier(col)
            sql_type = self._map_dtype_to_sql(dtype, dataframe[col])
            columns.append(f"{escaped_col} {sql_type}")
        return ", ".join(columns)

    def _map_dtype_to_sql(self, dtype, series=None) -> str:
        """Map pandas dtype to a cross-database compatible SQL type."""
        
        # Handle mixed object types
        if series is not None and dtype == 'object':
            _, sql_type, is_mixed = self._detect_and_handle_mixed_types(series)
            if is_mixed and sql_type:
                return sql_type

        # Direct lookup for known numpy types
        if hasattr(dtype, 'type') and dtype.type in self._type_map:
            return self._type_map[dtype.type]

        # Handle pandas extension types
        if hasattr(dtype, 'name'):
            if dtype.name in ['Int8', 'Int16', 'Int32', 'Int64']:
                return self._get_integer_type_by_range(series)
            elif dtype.name in ['Float32', 'Float64']:
                return self._type_map.get(pandas.Float64Dtype, "FLOAT")
            elif dtype.name == 'boolean':
                return self._type_map.get(pandas.BooleanDtype, "BOOLEAN")
            elif dtype.name == 'string':
                return self._get_varchar_type_by_length(series)

        # Booleans
        if pandas.api.types.is_bool_dtype(dtype):
            return self._type_map.get(bool, "BOOLEAN")

        # Integers with range-based sizing
        if pandas.api.types.is_integer_dtype(dtype):
            return self._get_integer_type_by_range(series)

        # Floats: database-specific handling
        if pandas.api.types.is_float_dtype(dtype):
            return self._get_float_type_by_database()

        # Datetimes with timezone awareness
        if pandas.api.types.is_datetime64_any_dtype(dtype):
            if hasattr(dtype, 'tz') and dtype.tz is not None:
                return self._get_timezone_aware_timestamp()
            return self._type_map.get(datetime, "TIMESTAMP")

        # Strings and objects: enhanced size-based VARCHAR
        if pandas.api.types.is_string_dtype(dtype) or pandas.api.types.is_object_dtype(dtype):
            return self._get_varchar_type_by_length(series)

        # Binary data
        if dtype == 'bytes' or str(dtype).startswith('bytes'):
            return self._type_map.get(bytes, "VARBINARY(4000)")

        # Fallback
        return "VARCHAR(255)"

    def _get_integer_type_by_range(self, series) -> str:
        """Get appropriate integer type based on value range."""
        if series is not None:
            try:
                mn, mx = series.min(), series.max()
                db_type = self.get_db_type()
                
                # TINYINT range: -128 to 127 (or 0 to 255 unsigned)
                if mn >= -128 and mx <= 127:
                    if db_type in ['mysql', 'sqlserver']:
                        return "TINYINT"
                    else:
                        return "SMALLINT"
                
                # SMALLINT range: -32,768 to 32,767
                elif mn >= -32768 and mx <= 32767:
                    return "SMALLINT"
                
                # INTEGER range: -2,147,483,648 to 2,147,483,647
                elif mn >= -2147483648 and mx <= 2147483647:
                    return "INTEGER"
                
                # BIGINT for larger values
                else:
                    return "BIGINT"
            except Exception:
                pass
        
        return self._type_map.get(int, "INTEGER")

    def _get_float_type_by_database(self) -> str:
        """Get appropriate float type based on database."""
        db_type = self.get_db_type()
        if db_type == 'postgresql':
            return "DOUBLE PRECISION"
        elif db_type in ['mysql', 'db2']:
            return "DOUBLE"
        elif db_type == 'oracle':
            return "BINARY_DOUBLE"
        elif db_type == 'sqlserver':
            return "FLOAT"
        else:
            return "FLOAT"

    def _get_timezone_aware_timestamp(self) -> str:
        """Get timezone-aware timestamp type based on database."""
        db_type = self.get_db_type()
        if db_type == 'postgresql':
            return "TIMESTAMPTZ"
        elif db_type == 'oracle':
            return "TIMESTAMP WITH TIME ZONE"
        elif db_type == 'sqlserver':
            return "DATETIMEOFFSET"
        else:
            return "TIMESTAMP"

    def _get_varchar_type_by_length(self, series) -> str:
        """Get appropriate VARCHAR type based on content length."""
        if series is not None:
            try:
                # Check for JSON-like content
                if series.astype(str).str.contains(r'^\s*[\{\[]').any() and \
                series.astype(str).str.contains(r'[\}\]]\s*$').any():
                    return self._get_json_type()
                
                max_len = series.astype(str).str.len().max()
                db_type = self.get_db_type()
                
                if max_len < self._varchar_small_threshold:
                    return f"VARCHAR({max_len + 20})"
                elif max_len < self._varchar_medium_threshold:
                    return f"VARCHAR({max_len + 50})"
                elif max_len < 4000:
                    return "VARCHAR(4000)"
                else:
                    # Use database-specific large text types
                    if db_type == 'postgresql':
                        return "TEXT"
                    elif db_type == 'mysql':
                        return "LONGTEXT"
                    elif db_type in ['db2', 'oracle']:
                        return "CLOB"
                    elif db_type == 'sqlserver':
                        return "NVARCHAR(MAX)"
                    else:
                        return "VARCHAR(4000)"
            except Exception:
                pass
        
        return self._type_map.get(str, "VARCHAR(255)")

    def _get_json_type(self) -> str:
        """Get appropriate JSON type based on database."""
        db_type = self.get_db_type()
        if db_type == 'postgresql':
            return "JSONB"
        elif db_type == 'mysql':
            return "JSON"
        elif db_type in ['db2', 'oracle']:
            return "CLOB"
        elif db_type == 'sqlserver':
            return "NVARCHAR(MAX)"
        else:
            return "VARCHAR(4000)"


    def table(self, table_name: str):
        """Get a table interface for fluent querying.
        
        Args:
            table_name: Name of the table to query
            
        Returns:
            TableQuery: A TableQuery object for fluent querying
            
        Examples:
            # Select all rows from a table
            result = datasource.table("my_table").all()
            
            # Select with filtering
            result = datasource.table("my_table").filter("age > 30").all()
            
            # Select specific columns
            result = datasource.table("my_table").select("name, age").all()
            
            # Order results
            result = datasource.table("my_table").order_by("age DESC").all()
            
            # Limit results
            result = datasource.table("my_table").limit(10).all()
        """
        return TableQuery(self, table_name)

    def enable_sql_debug(self, enabled: bool = True) -> None:
        """Enable or disable SQL debug logging.
        
        Args:
            enabled: If True, SQL statements will be logged at DEBUG level.
        """
        self._debug_sql = enabled
        if enabled:
            # Set up logging if not already configured
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self._logger.addHandler(handler)
            
            # Ensure logger level is set to DEBUG
            self._logger.setLevel(logging.DEBUG)
            self._logger.info("SQL debugging enabled")

    def register_type(self, python_type: Type, sql_type: str) -> None:
        """Register a custom type mapping.
        
        Args:
            python_type: The Python type to map
            sql_type: The SQL type to map to
            
        Examples:
            # Register a custom type
            datasource.register_type(UUID, "UUID")
            
            # Register a custom class
            datasource.register_type(MyCustomClass, "JSON")
        """
        self._type_map[python_type] = sql_type
    
    def get_type_mappings(self) -> Dict[str, str]:
        """Return all registered type mappings.
        
        Returns:
            dict: A dictionary mapping Python type names to SQL types
        """
        return {getattr(k, '__name__', str(k)): v for k, v in self._type_map.items()}

    def _insert_dataframe(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """Insert DataFrame using bulk methods when possible."""
        if len(dataframe) > 1000:
            self._bulk_insert_dataframe(table_name, dataframe, chunksize)
        else:
            # Use standard chunked inserts for small datasets
            self._fallback_bulk_insert(table_name, dataframe, chunksize)

    def _bulk_insert_dataframe(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """
        Perform optimized bulk inserts based on database type.
        Gracefully falls back to standard method if database-specific method fails.
        """
        db_type = self.get_db_type()
        
        # Track if we're using native method or fallback
        using_native_method = True
        
        try:
            if db_type == 'postgresql':
                self._postgresql_bulk_insert(table_name, dataframe, chunksize)
            elif db_type == 'mysql':
                self._mysql_bulk_insert(table_name, dataframe, chunksize)
            elif db_type == 'sqlserver':
                self._sqlserver_bulk_insert(table_name, dataframe, chunksize)
            elif db_type == 'db2':
                self._db2_bulk_insert(table_name, dataframe, chunksize)
            elif db_type == 'oracle':
                self._oracle_bulk_insert(table_name, dataframe, chunksize)
            else:
                using_native_method = False
                self._fallback_bulk_insert(table_name, dataframe, chunksize)
                
            # Log success with method used
            if self._debug_sql:
                method_name = f"{db_type} native" if using_native_method else "standard"
                self._logger.info(f"✅ Bulk insert completed using {method_name} method")
                
        except Exception as e:
            if using_native_method:
                # Native method failed, try fallback
                if self._debug_sql:
                    self._logger.warning(f"{db_type} native bulk insert failed, attempting standard method...")
                
                try:
                    self._fallback_bulk_insert(table_name, dataframe, chunksize)
                    
                    # Fallback succeeded
                    if self._debug_sql:
                        self._logger.info("✅ Bulk insert completed successfully using standard fallback method")
                        self._logger.info(f"   Table: {table_name}")
                        self._logger.info(f"   Rows inserted: {len(dataframe):,}")
                        
                except Exception as fallback_error:
                    # Both methods failed
                    self._logger.error(f"❌ Both native and fallback bulk insert methods failed")
                    self._logger.error(f"   Native method error: {str(e)}")
                    self._logger.error(f"   Fallback method error: {str(fallback_error)}")
                    raise fallback_error
            else:
                # Fallback method failed (no native method was attempted)
                self._logger.error(f"❌ Bulk insert failed: {str(e)}")
                raise

    def _fallback_bulk_insert(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """Fallback to optimized multi-row INSERTs for unsupported databases."""
        escaped_table = self._escape_identifier(table_name)
        escaped_columns = ', '.join(self._escape_identifier(col) for col in dataframe.columns)
        
        if self._debug_sql:
            self._logger.debug(f"Starting standard bulk insert for table: {escaped_table}")
            self._logger.debug(f"Row count: {len(dataframe)}, chunksize: {chunksize}")

        total_rows = len(dataframe)
        rows_inserted = 0
        
        try:
            for i in range(0, total_rows, chunksize):
                chunk = dataframe.iloc[i:i+chunksize]
                values = ", ".join(
                    f"({', '.join(map(self._format_value, row))})" 
                    for _, row in chunk.iterrows()
                )
                
                insert_query = f"INSERT INTO {escaped_table} ({escaped_columns}) VALUES {values}"
                
                if self._debug_sql and i == 0:
                    self._logger.debug(f"Executing bulk insert for first {len(chunk)} rows")
                    
                self.query(insert_query)
                rows_inserted += len(chunk)
                
                # Progress for large datasets
                if self._debug_sql and rows_inserted % 10000 == 0:
                    progress = (rows_inserted / total_rows) * 100
                    self._logger.debug(f"Progress: {rows_inserted:,}/{total_rows:,} rows ({progress:.1f}%)")
            
            if self._debug_sql:
                self._logger.debug(f"Standard bulk insert completed: {rows_inserted:,} rows into {table_name}")
                
        except Exception as e:
            error_msg = f"Failed at row {rows_inserted} of {total_rows}: {str(e)}"
            if self._debug_sql:
                self._logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _postgresql_bulk_insert(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """PostgreSQL bulk insert using most performant PostgreSQL-specific methods."""
        escaped_table = self._escape_identifier(table_name)
        columns = ', '.join(self._escape_identifier(col) for col in dataframe.columns)
        
        if self._debug_sql:
            self._logger.debug(f"Starting PostgreSQL bulk insert for table: {escaped_table}")
            self._logger.debug(f"Row count: {len(dataframe)}, chunk size: {chunksize:,}")
        
        # Method 1: Try COPY with inline data (most performant PostgreSQL command)
        try:
            if self._debug_sql:
                self._logger.debug("Attempting PostgreSQL COPY with inline data")
            
            # Pre-process DataFrame to handle numpy types and complex objects
            processed_df = dataframe.copy()
            for col in processed_df.select_dtypes(include=['object']).columns:
                # Convert dict/list columns to JSON strings
                if processed_df[col].apply(lambda x: isinstance(x, (dict, list)) if pandas.notna(x) else False).any():
                    processed_df[col] = processed_df[col].apply(
                        lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x
                    )
                # Handle numpy string types
                processed_df[col] = processed_df[col].apply(
                    lambda x: str(x) if hasattr(x, 'item') else x  # Convert numpy scalars
                )
            
            # Convert DataFrame to tab-separated format
            output = io.StringIO()
            processed_df.to_csv(output, sep='\t', header=False, index=False, na_rep='\\N', lineterminator='\n')
            csv_data = output.getvalue()
            
            # PostgreSQL COPY with inline data
            copy_query = f"""COPY {escaped_table} ({columns}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '\\N');
            {csv_data}\\.
            """
            
            self.query(copy_query)
            
            if self._debug_sql:
                self._logger.debug(f"PostgreSQL COPY successful for {len(dataframe)} rows")
            return
            
        except Exception as e:
            if self._debug_sql:
                self._logger.warning(f"COPY with inline data failed: {str(e)}, trying UNNEST method")
        
        # Method 2: UNNEST with arrays (second most performant)
        try:
            if self._debug_sql:
                self._logger.debug("Using PostgreSQL UNNEST array method")
            
            for i in range(0, len(dataframe), chunksize):
                chunk = dataframe.iloc[i:i + chunksize]
                
                # Build arrays for each column
                arrays = []
                for col in chunk.columns:
                    values = []
                    dtype = chunk[col].dtype
                    
                    for val in chunk[col]:
                        if pandas.isna(val):
                            values.append("NULL")
                        elif isinstance(val, bool):
                            values.append(str(val).upper())
                        elif isinstance(val, str):
                            escaped = val.replace("'", "''")
                            values.append(f"'{escaped}'")
                        elif isinstance(val, datetime):
                            values.append(f"'{val.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}'")
                        elif isinstance(val, date):
                            values.append(f"'{val.isoformat()}'")
                        elif isinstance(val, (dict, list)):
                            json_str = json.dumps(val, ensure_ascii=False).replace("'", "''")
                            values.append(f"'{json_str}'")
                        else:
                            values.append(str(val))
                    
                    # Determine PostgreSQL array type
                    sql_type = self._map_dtype_to_sql(dtype, chunk[col])
                    array_str = f"ARRAY[{', '.join(values)}]::{sql_type}[]"
                    arrays.append(array_str)
                
                # Use UNNEST to insert from arrays
                unnest_query = f"""
                INSERT INTO {escaped_table} ({columns})
                SELECT * FROM UNNEST(
                    {', '.join(arrays)}
                )
                """
                
                self.query(unnest_query)
                
                # Progress logging for large datasets
                if self._debug_sql and i > 0 and (i + chunksize) % 50000 == 0:
                    self._logger.debug(f"Progress: {min(i + chunksize, len(dataframe)):,}/{len(dataframe):,} rows")
            
            if self._debug_sql:
                self._logger.debug(f"PostgreSQL UNNEST insert completed for {len(dataframe)} rows")
            return
            
        except Exception as e:
            if self._debug_sql:
                self._logger.info(f"PostgreSQL UNNEST method failed: {str(e)}")
                self._logger.info("Falling back to standard bulk insert method")
            raise

    def _mysql_bulk_insert(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """Use MySQL's LOAD DATA LOCAL INFILE for fast bulk inserts."""
        escaped_table = self._escape_identifier(table_name)
        
        tmp_path = None
        try:
            if self._debug_sql:
                self._logger.debug(f"Starting MySQL LOAD DATA for table: {escaped_table}")
                self._logger.debug(f"Row count: {len(dataframe)}")

            # Write DataFrame to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmpfile:
                dataframe.to_csv(tmpfile, index=False, header=False, na_rep='\\N')
                tmp_path = tmpfile.name
            
            # Build and execute LOAD DATA query
            load_query = f"""
                LOAD DATA LOCAL INFILE '{tmp_path}'
                INTO TABLE {escaped_table}
                FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
                LINES TERMINATED BY '\\n'
            """
            if self._debug_sql:
                self._logger.debug(f"Executing LOAD DATA: {load_query.strip()}")
            self.query(load_query)
            
            if self._debug_sql:
                self._logger.debug(f"MySQL LOAD DATA inserted {len(dataframe)} rows into {table_name}")
                        
        except Exception as e:
            if self._debug_sql:
                self._logger.info(f"MySQL native bulk insert not available: {type(e).__name__}: {str(e)}")
                self._logger.info("Falling back to standard bulk insert method")
            raise
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _sqlserver_bulk_insert(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """Use SQL Server's BULK INSERT for optimized performance."""
        escaped_table = self._escape_identifier(table_name)
        
        tmp_path = None
        try:
            if self._debug_sql:
                self._logger.debug(f"Starting SQL Server BULK INSERT for table: {escaped_table}")
                self._logger.debug(f"Row count: {len(dataframe)}")

            # Write DataFrame to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmpfile:
                dataframe.to_csv(tmpfile, index=False, header=False, na_rep='NULL')
                tmp_path = tmpfile.name
            
            # Build and execute BULK INSERT query
            bulk_query = f"""
                BULK INSERT {escaped_table}
                FROM '{tmp_path}'
                WITH (
                    FIELDTERMINATOR = ',',
                    ROWTERMINATOR = '\\n',
                    TABLOCK,
                    KEEPNULLS
                )
            """
            if self._debug_sql:
                self._logger.debug(f"Executing BULK INSERT: {bulk_query.strip()}")
            self.query(bulk_query)
            
            if self._debug_sql:
                self._logger.debug(f"SQL Server BULK INSERT inserted {len(dataframe)} rows into {table_name}")
                        
        except Exception as e:
            if self._debug_sql:
                self._logger.info(f"SQL Server native bulk insert not available: {type(e).__name__}: {str(e)}")
                self._logger.info("Falling back to standard bulk insert method")
            raise
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _db2_bulk_insert(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """DB2 bulk insert - skip native method for Trino proxy, use optimized standard insert."""
        if self._debug_sql:
            self._logger.info("DB2 uses Trino proxy - using standard bulk insert with optimized chunk size")
            self._logger.info(f"Row count: {len(dataframe):,}, chunk size: {chunksize:,}")
        
        # DB2 always uses Trino, which has smaller query limits
        # Cap chunk size for better performance
        trino_chunk_size = min(chunksize, 2000)
        
        if trino_chunk_size != chunksize and self._debug_sql:
            self._logger.debug(f"Reduced chunk size from {chunksize:,} to {trino_chunk_size:,} for Trino")
        
        # Directly use fallback with optimized chunk size
        self._fallback_bulk_insert(table_name, dataframe, trino_chunk_size)

    def _oracle_bulk_insert(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """Use Oracle's multi-row INSERT ALL for bulk inserts."""
        escaped_table = self._escape_identifier(table_name)
        escaped_columns = ', '.join(self._escape_identifier(col) for col in dataframe.columns)

        if self._debug_sql:
            self._logger.debug(f"Starting Oracle INSERT ALL for table: {escaped_table}")
            self._logger.debug(f"Row count: {len(dataframe)}, chunk size: {chunksize:,}")

        try:
            # Oracle INSERT ALL has a limit of 1000 rows per statement
            oracle_chunk_size = min(chunksize, 1000)
            
            for i in range(0, len(dataframe), oracle_chunk_size):
                chunk = dataframe.iloc[i:i + oracle_chunk_size]
                
                # Build INSERT ALL statement
                insert_parts = []
                for _, row in chunk.iterrows():
                    values = ', '.join(map(self._format_value, row))
                    insert_parts.append(f"INTO {escaped_table} ({escaped_columns}) VALUES ({values})")
                
                insert_all_query = f"""
                INSERT ALL
                {chr(10).join(insert_parts)}
                SELECT * FROM DUAL
                """
                
                if self._debug_sql and i == 0:
                    self._logger.debug(f"Executing INSERT ALL for first {len(chunk)} rows")
                
                self.query(insert_all_query)
            
            if self._debug_sql:
                self._logger.debug(f"Oracle INSERT ALL completed for {len(dataframe)} rows into {table_name}")
                    
        except Exception as e:
            if self._debug_sql:
                self._logger.info(f"Oracle native bulk insert failed: {type(e).__name__}: {str(e)}")
                self._logger.info("Falling back to standard bulk insert method")
            raise

    def _format_value(self, value) -> str:
        """
        Format value for SQL insertion with database-specific CAST operations.
        
        Args:
            value: Value to format for SQL insertion
            
        Returns:
            str: SQL expression for the value with appropriate database-specific casting
        """
        if pandas.isna(value):
            return "NULL"

        db_type = self.get_db_type()
        
        # Enhanced database-specific casting maps
        cast_map = {
            'postgresql': {
                'float': 'DOUBLE PRECISION',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'BOOLEAN',
                'int': 'INTEGER',
                'str': 'VARCHAR',
                'json': 'JSONB'  # Enhanced: Explicit JSONB casting
            },
            'mysql': {
                'float': 'DOUBLE',
                'datetime': 'DATETIME',
                'date': 'DATE',
                'bool': 'BOOLEAN',
                'int': 'INTEGER',
                'str': 'VARCHAR',
                'json': 'JSON'  # Enhanced: Native JSON casting
            },
            'db2': {
                'float': 'DOUBLE',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'SMALLINT',
                'int': 'INTEGER',
                'str': 'VARCHAR',
                'json': 'CLOB'  # Enhanced: CLOB for JSON
            },
            'oracle': {
                'float': 'BINARY_DOUBLE',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'NUMBER',
                'int': 'NUMBER',
                'str': 'VARCHAR2',
                'json': 'CLOB'  # Enhanced: CLOB for JSON
            },
            'sqlserver': {
                'float': 'FLOAT',
                'datetime': 'DATETIME2',
                'date': 'DATE',
                'bool': 'BIT',
                'int': 'INT',
                'str': 'NVARCHAR',
                'json': 'NVARCHAR(MAX)'  # Enhanced: NVARCHAR(MAX) for JSON
            },
            'unknown': {
                'float': 'FLOAT',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'BOOLEAN',
                'int': 'INTEGER',
                'str': 'VARCHAR',
                'json': 'VARCHAR(4000)'
            }
        }

        cast_types = cast_map.get(db_type, cast_map['unknown'])

        # Boolean handling with database-specific logic
        if isinstance(value, bool):
            if db_type in ['db2']:
                return f"CAST({1 if value else 0} AS {cast_types['bool']})"
            elif db_type == 'oracle':
                return f"CAST({1 if value else 0} AS {cast_types['bool']})"
            elif db_type == 'sqlserver':
                return f"CAST({1 if value else 0} AS {cast_types['bool']})"
            else:
                return f"CAST({str(value).upper()} AS {cast_types['bool']})"

        # Integer handling
        elif isinstance(value, (int, numpy.integer)):
            return f"CAST({value} AS {cast_types['int']})"

        # Float handling
        elif isinstance(value, (float, numpy.floating)):
            if numpy.isnan(value) or numpy.isinf(value):
                return "NULL"
            return f"CAST({value} AS {cast_types['float']})"

        # Datetime handling
        elif isinstance(value, datetime):
            timestamp_str = value.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            return f"CAST('{timestamp_str}' AS {cast_types['datetime']})"

        # Date handling
        elif isinstance(value, date):
            return f"CAST('{value.isoformat()}' AS {cast_types['date']})"

        # Enhanced JSON/Dictionary/List handling with database-specific casting
        elif isinstance(value, (dict, list)):
            json_str = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            escaped_str = json_str.replace("'", "''")
            
            # Database-specific JSON handling - THIS IS THE KEY FIX!
            if db_type == 'postgresql':
                # PostgreSQL requires explicit JSONB casting using :: syntax
                return f"'{escaped_str}'::jsonb"
            elif db_type == 'mysql':
                # MySQL can cast to JSON type
                return f"CAST('{escaped_str}' AS JSON)"
            elif db_type in ['db2', 'oracle']:
                # DB2 and Oracle use CLOB for JSON storage
                return f"CAST('{escaped_str}' AS CLOB)"
            elif db_type == 'sqlserver':
                # SQL Server uses NVARCHAR(MAX)
                return f"CAST('{escaped_str}' AS NVARCHAR(MAX))"
            else:
                # Fallback for unknown databases
                return f"CAST('{escaped_str}' AS VARCHAR(4000))"

        # NumPy array handling
        elif isinstance(value, numpy.ndarray):
            try:
                array_list = value.tolist()
                json_str = json.dumps(array_list, ensure_ascii=False, separators=(',', ':'))
                escaped_str = json_str.replace("'", "''")
                
                # Use same JSON casting logic as dict/list
                if db_type == 'postgresql':
                    return f"'{escaped_str}'::jsonb"
                elif db_type == 'mysql':
                    return f"CAST('{escaped_str}' AS JSON)"
                elif db_type in ['db2', 'oracle']:
                    return f"CAST('{escaped_str}' AS CLOB)"
                elif db_type == 'sqlserver':
                    return f"CAST('{escaped_str}' AS NVARCHAR(MAX))"
                else:
                    return f"CAST('{escaped_str}' AS VARCHAR(4000))"
            except Exception:
                # Fallback to string representation
                str_value = str(value)
                escaped_str = str_value.replace("'", "''")
                return f"CAST('{escaped_str}' AS {cast_types['str']})"

        # Enhanced string handling with length considerations
        else:
            str_value = str(value)
            escaped_str = str_value.replace("'", "''")
            
            # Handle very long strings that might exceed VARCHAR limits
            if len(escaped_str) > 4000:
                if db_type == 'postgresql':
                    return f"CAST('{escaped_str}' AS TEXT)"
                elif db_type == 'mysql':
                    return f"CAST('{escaped_str}' AS LONGTEXT)"
                elif db_type in ['db2', 'oracle']:
                    return f"CAST('{escaped_str}' AS CLOB)"
                elif db_type == 'sqlserver':
                    return f"CAST('{escaped_str}' AS NVARCHAR(MAX))"
                else:
                    # Truncate for unknown databases to avoid errors
                    truncated = escaped_str[:3900] + "..."
                    return f"CAST('{truncated}' AS VARCHAR(4000))"
            else:
                return f"CAST('{escaped_str}' AS {cast_types['str']})"


@attr.s
class TableQuery:
    """Provides a fluent query interface for tables."""
    
    _datasource = attr.ib()
    _table_name = attr.ib()
    _select_clause = attr.ib(default="*")
    _where_clause = attr.ib(default="")
    _order_clause = attr.ib(default="")
    _limit_clause = attr.ib(default="")
    _offset_clause = attr.ib(default="")
    
    def select(self, columns: str):
        """Select specific columns from the table.
        
        Args:
            columns: Comma-separated list of column names
            
        Returns:
            TableQuery: Self for method chaining
        """
        self._select_clause = columns
        return self
    
    def filter(self, condition: str):
        """Filter results based on a condition.
        
        Args:
            condition: SQL WHERE condition
            
        Returns:
            TableQuery: Self for method chaining
        """
        if self._where_clause:
            self._where_clause += f" AND {condition}"
        else:
            self._where_clause = f"WHERE {condition}"
        return self
    
    def order_by(self, order: str):
        """Order results based on columns.
        
        Args:
            order: SQL ORDER BY expression
            
        Returns:
            TableQuery: Self for method chaining
        """
        self._order_clause = f"ORDER BY {order}"
        return self
    
    def limit(self, limit: int):
        """Limit the number of results returned.
        
        Args:
            limit: Maximum number of rows to return
            
        Returns:
            TableQuery: Self for method chaining
        """
        self._limit_clause = f"LIMIT {limit}"
        return self
    
    def offset(self, offset: int):
        """Set the offset for results.
        
        Args:
            offset: Number of rows to skip
            
        Returns:
            TableQuery: Self for method chaining
        """
        self._offset_clause = f"OFFSET {offset}"
        return self
    
    def _build_query(self) -> str:
        """Build the SQL query from the components.
        
        Returns:
            str: Complete SQL query
        """
        escaped_table = self._datasource._escape_identifier(self._table_name)
        query_parts = [f"SELECT {self._select_clause} FROM {escaped_table}"]
        
        if self._where_clause:
            query_parts.append(self._where_clause)
        
        if self._order_clause:
            query_parts.append(self._order_clause)
        
        if self._limit_clause:
            query_parts.append(self._limit_clause)
        
        if self._offset_clause:
            query_parts.append(self._offset_clause)
        
        return " ".join(query_parts)
    
    def all(self):
        """Execute the query and return all results as a DataFrame.
        
        Returns:
            pandas.DataFrame: The query results
        """
        query = self._build_query()
        result = self._datasource.query(query)
        return result.to_pandas()
    
    def first(self):
        """Execute the query and return the first result.
        
        Returns:
            pandas.Series or None: First row as a Series, or None if no results
        """
        original_limit = self._limit_clause
        self._limit_clause = "LIMIT 1"
        try:
            result = self.all()
            if len(result) > 0:
                return result.iloc[0]
            return None
        finally:
            self._limit_clause = original_limit
    
    def count(self) -> int:
        """Count the number of rows that would be returned.
        
        Returns:
            int: Row count
        """
        original_select = self._select_clause
        self._select_clause = "COUNT(*) as count"
        try:
            result = self.all()
            return result.iloc[0]['count']
        finally:
            self._select_clause = original_select


@attr.s
class ObjectStoreDatasource(Datasource):
    """Represents a object store type datasource."""

    def Object(
        self, key: str, include_auth_headers: bool = False
    ) -> _Object:  # pylint: disable=invalid-name
        """Return an object with given key and datasource client."""
        return _Object(datasource=self, key=key, include_auth_headers=include_auth_headers)

    def list_objects(self, prefix: str = "", page_size: int = 1000) -> List[_Object]:
        """List objects in the object store datasource.

        Args:
            prefix: optional prefix to filter objects
            page_size: optional number of objects to fetch

        Returns:
            List of objects
        """
        keys = self.client.list_keys(
            self.identifier,
            prefix,
            page_size,
            config=self._config_override.config(),
            credential=self._get_credential_override(),
        )
        if not keys:
            return []
        return [
            _Object(
                datasource=self,
                key=key,
            )
            for key in keys
        ]

    def get_key_url(self, object_key: str, is_read_write: bool = False) -> str:
        """Get a signed URL for the given key.

        Args:
            object_key: unique identifier of object to get signed URL for.
            is_read_write: whether the URL should allow writes or not.

        Returns:
            Signed URL for given key
        """
        return cast(
            str,
            self.client.get_key_url(
                self.identifier,
                object_key,
                is_read_write,
                config=self._config_override.config(),
                credential=self._get_credential_override(),
            ),
        )

    def get(self, object_key: str) -> bytes:
        """Get object content as bytes.

        Args:
            object_key: unique key of object

        Returns:
            object content as bytes
        """
        return self.Object(object_key).get()

    def download_file(self, object_key: str, filename: str) -> None:
        """Download object content to file located at filename.

        The file will be created if it does not exists.

        Args:
            object_key: unique key of object
            filename: path of file to write content to.
        """
        self.Object(object_key).download_file(filename)

    def download(self, object_key: str, filename: str, max_workers: int = MAX_WORKERS) -> None:
        """Download object content to file located at filename.

        The file will be created if it does not exists.

        Args:
            object_key: unique key of object
            filename: path of file to write content to
            max_workers: max parallelism for high speed download
        """
        self.Object(object_key).download(filename, max_workers)

    def download_fileobj(self, object_key: str, fileobj: Any) -> None:
        """Download object content to file like object.

        Args:
            object_key: unique key of object
            fileobj: A file-like object to download into.
                At a minimum, it must implement the write method and must accept bytes.
        """
        self.Object(object_key).download_fileobj(fileobj)

    def put(self, object_key: str, content: bytes) -> None:
        """Upload content to object at given key.

        Args:
            object_key: unique key of object
            content: bytes content
        """
        self.Object(object_key).put(content)

    def upload_file(self, object_key: str, filename: str) -> None:
        """Upload content of file at filename to object at given key.

        Args:
            object_key: unique key of object
            filename: path of file to upload.
        """
        self.Object(object_key).upload_file(filename)

    def upload_fileobj(self, object_key: str, fileobj: Any) -> None:
        """Upload content of file like object to object at given key.

        Args:
            object_key: unique key of object
            fileobj: A file-like object to upload from.
                At a minimum, it must implement the read method and must return bytes.
        """
        self.Object(object_key).upload_fileobj(fileobj)


@attr.s
class BoardingPass:
    """Represent a query request to the Datasource Proxy service."""

    # pylint: disable=too-few-public-methods

    datasource_id: str = attr.ib()
    query: str = attr.ib()
    config: Dict[str, str] = attr.ib()
    credential: Dict[str, str] = attr.ib()

    def to_json(self) -> str:
        """Serialize self to JSON."""
        return json.dumps(
            {
                "datasourceId": self.datasource_id,
                "sqlQuery": self.query,
                "configOverwrites": self.config,
                "credentialOverwrites": self.credential,
            }
        )


@attr.s
class DataSourceClient:
    """API client and bindings."""

    domino: AuthenticatedClient = attr.ib(init=False, repr=False)
    proxy: flight.FlightClient = attr.ib(init=False, repr=False)
    proxy_http: AuthenticatedClient = attr.ib(init=False, repr=False)

    api_key: Optional[str] = attr.ib(factory=lambda: os.getenv(DOMINO_USER_API_KEY))
    token_file: Optional[str] = attr.ib(factory=lambda: os.getenv(DOMINO_TOKEN_FILE))
    token_url: Optional[str] = attr.ib(factory=lambda: os.getenv(DOMINO_API_PROXY))
    token: Optional[str] = attr.ib(default=None)

    def __attrs_post_init__(self):
        flight_host = os.getenv(DOMINO_DATASOURCE_PROXY_FLIGHT_HOST)
        domino_host = os.getenv(
            DOMINO_API_PROXY, os.getenv(DOMINO_API_HOST, os.getenv(DOMINO_USER_HOST, ""))
        )
        proxy_host = os.getenv(DOMINO_DATASOURCE_PROXY_HOST, "")

        client_source = os.getenv(DOMINO_CLIENT_SOURCE, "Python")
        run_id = os.getenv(DOMINO_RUN_ID, "")

        logger.info(
            "initializing datasource client with hosts",
            flight_host=flight_host,
            domino_host=domino_host,
            proxy_host=proxy_host,
        )

        self._set_proxy()
        self.proxy_http = ProxyClient(
            base_url=proxy_host,
            api_key=self.api_key,
            client_source=client_source,
            run_id=run_id,
            token_file=self.token_file,
            token_url=self.token_url,
            token=self.token,
            timeout=httpx.Timeout(5.0),
            verify_ssl=True,
        )
        self.domino = AuthenticatedClient(
            base_url=f"{domino_host}/v4",
            api_key=self.api_key,
            token_file=self.token_file,
            token_url=self.token_url,
            token=self.token,
            headers=ACCEPT_HEADERS,
            timeout=httpx.Timeout(20.0),
            verify_ssl=True,
        )

    def _set_proxy(self):
        client_source = os.getenv(DOMINO_CLIENT_SOURCE, "Python")
        flight_host = os.getenv(DOMINO_DATASOURCE_PROXY_FLIGHT_HOST)
        run_id = os.getenv(DOMINO_RUN_ID, "")
        self.proxy = flight.FlightClient(
            flight_host,
            middleware=[
                AuthMiddlewareFactory(
                    self.api_key,
                    self.token_file,
                    self.token_url,
                    self.token,
                ),
                MetaMiddlewareFactory(client_source=client_source, run_id=run_id),
            ],
        )

    def get_datasource(self, name: str) -> Datasource:
        """Fetch a datasource by name.

        Args:
            name: unique identifier of a datasource

        Returns:
            Datasource entity with given name

        Raises:
            Exception: If the response from Domino is not 200
        """
        logger.info("get_datasource", datasource_name=name)

        run_id = os.getenv(DOMINO_RUN_ID)
        response = get_datasource_by_name.sync_detailed(
            name,
            client=self.domino.with_auth_headers(),
            run_id=run_id,
        )
        if response.status_code == 200:
            datasource_dto = cast(DatasourceDto, response.parsed)
            datasource_klass = cast(
                Datasource, find_datasource_klass(datasource_dto.data_source_type)
            )
            return datasource_klass.from_dto(self, datasource_dto)

        error_response = cast(ErrorResponse, response.parsed)
        message = (
            f"Received unexpected response while getting data source: {response}"
            if error_response is None
            else error_response.message
        )
        logger.exception(message)
        raise Exception(message)

    @backoff.on_exception(backoff.expo, UnauthenticatedError, max_time=60)
    def list_keys(
        self,
        datasource_id: str,
        prefix: str,
        page_size: int,
        config: Dict[str, str],
        credential: Dict[str, str],
    ) -> List[str]:
        """List keys in a datasource.

        Args:
            datasource_id: unique identifier of a datasource
            prefix: prefix to filter keys with
            page_size: number of objects to return
            config: overwrite configuration dictionary
            credential: overwrite credential dictionary

        Returns:
            List of keys as string

        Raises:
            Exception: if the response from the Proxy is not 200
            UnauthenticatedError: if the request has invalid authentication
        """
        logger.info("list_keys", datasource_id=datasource_id, prefix=prefix, page_size=page_size)

        response = list_keys.sync_detailed(
            client=self.proxy_http.with_auth_headers(),
            body=ListRequest(
                datasource_id=datasource_id,
                prefix=prefix,
                page_size=page_size,
                config_overwrites=APIConfig.from_dict(config),
                credential_overwrites=APIConfig.from_dict(credential),
            ),
        )

        if response.status_code == 200:
            return cast(List[str], response.parsed)
        if response.status_code == 401:
            raise UnauthenticatedError

        error = cast(ProxyErrorResponse, response.parsed)
        logger.exception(error)
        raise Exception(f"{error.error_type}: {error.raw_error}")

    @backoff.on_exception(backoff.expo, UnauthenticatedError, max_time=60)
    def get_key_url(  # pylint: disable=too-many-arguments
        self,
        datasource_id: str,
        object_key: str,
        is_read_write: bool,
        config: Dict[str, str],
        credential: Dict[str, str],
    ) -> str:
        """Request a signed URL for a given datasource and object key.

        Args:
            datasource_id: unique identifier of a datasource
            object_key: unique identifier of key to retrieve
            is_read_write: whether the signed URL allows write or not.
            config: overwrite configuration dictionary
            credential: overwrite credential dictionary

        Returns:
            Signed URL of the requested object.

        Raises:
            Exception: if the response from the Proxy is not 200
            UnauthenticatedError: if the request has invalid authentication
        """
        logger.info("get_key_url", datasource_id=datasource_id, object_key=object_key)

        response = get_key_url.sync_detailed(
            client=self.proxy_http.with_auth_headers(),
            body=KeyRequest(
                datasource_id=datasource_id,
                object_key=object_key,
                is_read_write=is_read_write,
                config_overwrites=APIConfig.from_dict(config),
                credential_overwrites=APIConfig.from_dict(credential),
            ),
        )

        if response.status_code == 200:
            return cast(str, response.parsed)
        if response.status_code == 401:
            raise UnauthenticatedError

        error = cast(ProxyErrorResponse, response.parsed)
        logger.exception(error)
        raise Exception(f"{error.error_type}: {error.raw_error}")

    def _log_metric(
        self,
        datasource_type: str,
        bytes_processed: int,
        is_read_write: bool,
    ) -> None:
        """Log metric about file size being processed.

        Args:
            datasource_type: type of datasource
            bytes_processed: count of read or written bytes
            is_read_write: whether used for read or write
        """
        mode = LogMetricM.WRITE if is_read_write else LogMetricM.READ
        type_map = {
            DatasourceDtoDataSourceType.ADLSCONFIG.value: LogMetricT.ADLSCONFIG,
            DatasourceDtoDataSourceType.GCSCONFIG.value: LogMetricT.GCSCONFIG,
            DatasourceDtoDataSourceType.GENERICS3CONFIG.value: LogMetricT.GENERICS3CONFIG,  # noqa
            DatasourceDtoDataSourceType.S3CONFIG.value: LogMetricT.S3CONFIG,
        }
        type_ = type_map.get(datasource_type)
        if not type_:
            return

        try:
            log_metric.sync_detailed(
                client=self.proxy_http.with_auth_headers(),
                t=type_,
                b=bytes_processed,
                m=mode,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception(exc)

    def execute(
        self,
        datasource_id: str,
        query: str,
        config: Dict[str, str],
        credential: Dict[str, str],
    ) -> Result:
        """Execute a given query against a datasource.

        Args:
            datasource_id: unique identifier of a datasource
            query: SQL query to execute
            config: overwrite configuration dictionary
            credential: overwrite credential dictionary

        Returns:
            Result entity encapsulating execution response

        Raises:
            DominoError: if the proxy fails to query or return data
        """
        logger.info("execute", datasource_id=datasource_id, query=query)

        try:
            self._set_proxy()
            reader = self._do_get(
                BoardingPass(
                    datasource_id=datasource_id,
                    query=query,
                    config=config,
                    credential=credential,
                ).to_json()
            )
        except (flight.FlightError, ArrowException) as exc:
            logger.exception(exc)
            raise DominoError(_unpack_flight_error(str(exc))) from None
        return Result(self, reader, query)

    @backoff.on_exception(backoff.expo, flight.FlightUnauthenticatedError, max_time=60)
    def _do_get(self, ticket: str) -> flight.FlightStreamReader:
        return self.proxy.do_get(flight.Ticket(ticket))
    
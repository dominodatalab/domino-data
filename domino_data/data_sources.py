"""Datasource module."""

from typing import Any, Dict, List, Optional, Type, Union, cast

import configparser
import contextlib
import io
import json
import logging
import os
import tempfile
import time
import uuid
from datetime import date, datetime
from decimal import Decimal

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

    def http(self) -> httpx.Client:
        """Get datasource http client."""
        return self.datasource.http()

    def pool_manager(self) -> urllib3.PoolManager:
        """Get datasource http pool manager."""
        return self.datasource.pool_manager()

    def get(self) -> bytes:
        """Get object content as bytes."""
        url = self.datasource.get_key_url(self.key, False)
        res = self.http().get(url)
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
        content_size = 0
        with self.http().stream("GET", url) as stream, open(filename, "wb") as file:
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
        with open(filename, "wb") as file:
            blob = BlobTransfer(url, file, max_workers=max_workers, http=self.pool_manager())

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
        content_size = 0
        with self.http().stream("GET", url) as stream:
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
        res = self.http().put(url, content=content)
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
        with open(filename, "rb") as file:
            res = self.http().put(url, content=file)
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
        res = self.http().put(url, content=fileobj)
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
    """Represents a tabular type datasource with enhanced DataFrame support."""
    
    # Default staging table threshold
    DEFAULT_STAGING_TABLE_CHUNK_THRESHOLD = 20
    
    _db_type_override = attr.ib(default=None, init=False, repr=False)
    _debug_sql = attr.ib(default=False, init=False, repr=False)
    _logger = attr.ib(factory=lambda: logging.getLogger(__name__), init=False, repr=False)
    _type_map = attr.ib(factory=dict, init=False, repr=False)
    _varchar_small_threshold = attr.ib(default=50, init=False)
    _varchar_medium_threshold = attr.ib(default=255, init=False)
    _db_type = attr.ib(default=None, init=False, repr=False)
    _is_trino_cached = attr.ib(default=None, init=False, repr=False)

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
                dict: "JSONB",
                list: "JSONB",
                pandas.Int64Dtype: "BIGINT",
                pandas.Float64Dtype: "DOUBLE PRECISION",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "BOOLEAN",
                pandas.DatetimeTZDtype: "TIMESTAMPTZ",
                numpy.int8: "SMALLINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "BIGINT",
                numpy.float32: "REAL",
                numpy.float64: "DOUBLE PRECISION",
                numpy.bool_: "BOOLEAN",
                bytes: "BYTEA",
            },
            'mysql': {
                bool: "BOOLEAN",
                int: "INTEGER",
                float: "DOUBLE",
                str: "VARCHAR(255)",
                datetime: "DATETIME",
                date: "DATE",
                Decimal: "DECIMAL(65,30)",
                dict: "JSON",
                list: "JSON",
                pandas.Int64Dtype: "BIGINT",
                pandas.Float64Dtype: "DOUBLE",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "BOOLEAN",
                pandas.DatetimeTZDtype: "DATETIME",
                numpy.int8: "TINYINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "BIGINT",
                numpy.float32: "FLOAT",
                numpy.float64: "DOUBLE",
                numpy.bool_: "BOOLEAN",
                bytes: "LONGBLOB",
            },
            'db2': {
                bool: "SMALLINT",
                int: "INTEGER",
                float: "DOUBLE",
                str: "VARCHAR(255)",
                datetime: "TIMESTAMP",
                date: "DATE",
                Decimal: "DECIMAL(31,0)",
                dict: "CLOB",
                list: "CLOB",
                pandas.Int64Dtype: "BIGINT",
                pandas.Float64Dtype: "DOUBLE",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "SMALLINT",
                pandas.DatetimeTZDtype: "TIMESTAMP",
                numpy.int8: "SMALLINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "BIGINT",
                numpy.float32: "REAL",
                numpy.float64: "DOUBLE",
                numpy.bool_: "SMALLINT",
                bytes: "BLOB",
            },
            'trino': {
                bool: "BOOLEAN",
                int: "BIGINT",
                float: "DOUBLE",
                str: "VARCHAR",
                datetime: "TIMESTAMP",
                date: "DATE",
                Decimal: "DECIMAL(38,10)",
                dict: "JSON",
                list: "JSON",
                pandas.Int64Dtype: "BIGINT",
                pandas.Float64Dtype: "DOUBLE",
                pandas.StringDtype: "VARCHAR",
                pandas.BooleanDtype: "BOOLEAN",
                pandas.DatetimeTZDtype: "TIMESTAMP",
                numpy.int8: "SMALLINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "BIGINT",
                numpy.float32: "REAL",
                numpy.float64: "DOUBLE",
                numpy.bool_: "BOOLEAN",
                bytes: "VARBINARY",
            },
            'oracle': {
                bool: "NUMBER(1)",
                int: "NUMBER",
                float: "BINARY_DOUBLE",
                str: "VARCHAR2(255)",
                datetime: "TIMESTAMP",
                date: "DATE",
                Decimal: "NUMBER(38,10)",
                dict: "CLOB",
                list: "CLOB",
                pandas.Int64Dtype: "NUMBER(19)",
                pandas.Float64Dtype: "BINARY_DOUBLE",
                pandas.StringDtype: "VARCHAR2(255)",
                pandas.BooleanDtype: "NUMBER(1)",
                pandas.DatetimeTZDtype: "TIMESTAMP WITH TIME ZONE",
                numpy.int8: "NUMBER(3)",
                numpy.int16: "NUMBER(5)",
                numpy.int32: "NUMBER(10)",
                numpy.int64: "NUMBER(19)",
                numpy.float32: "BINARY_FLOAT",
                numpy.float64: "BINARY_DOUBLE",
                numpy.bool_: "NUMBER(1)",
                bytes: "BLOB",
            },
            'sqlserver': {
                bool: "BIT",
                int: "INT",
                float: "FLOAT",
                str: "NVARCHAR(255)",
                datetime: "DATETIME2",
                date: "DATE",
                Decimal: "DECIMAL(38,10)",
                dict: "NVARCHAR(MAX)",
                list: "NVARCHAR(MAX)",
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
                numpy.bool_: "BIT",
                bytes: "VARBINARY(MAX)",
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
                numpy.bool_: "BOOLEAN",
                bytes: "VARBINARY(4000)",
            }
        }

        # Set current database type mapping
        db_type = self.get_db_type()
        self._type_map = self._type_mappings.get(db_type, self._type_mappings['unknown'])

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

    def write_dataframe(
        self,
        table_name: str,
        dataframe: pandas.DataFrame,
        if_table_exists: str = 'fail',
        chunksize: Optional[int] = None,
        handle_mixed_types: bool = True,
        force: bool = False,
        auto_optimize_chunks: bool = True,
        max_message_size_mb: float = 4.0,
        staging_table_chunk_threshold: Optional[int] = None,
    ) -> None:
        """
        Write DataFrame to a table in the datasource with automatic chunk size optimization.

        Args:
            table_name: Name of the table to write to.
            dataframe: DataFrame containing the data to write.
            if_table_exists: Action if table exists ('fail', 'replace', 'append', 'truncate')
            chunksize: Number of rows per chunk. If None, auto-optimize based on data characteristics.
            handle_mixed_types: If True, detect and handle mixed types in object columns.
            force: If True, attempt operation even if schema compatibility issues are detected.
            auto_optimize_chunks: If True and chunksize is None, automatically calculate optimal chunk size.
            max_message_size_mb: Maximum gRPC message size in MB for auto-optimization.
            staging_table_chunk_threshold: Number of chunks above which to use staging table approach.
                                        If None, uses DEFAULT_STAGING_TABLE_CHUNK_THRESHOLD (20).

        Raises:
            ValueError: If operation cannot be completed safely.

        Examples:
            # Auto-optimized with default staging threshold (20 chunks)
            datasource.write_dataframe("my_table", df)
            
            # Force direct insert even for large datasets
            datasource.write_dataframe("my_table", df, staging_table_chunk_threshold=0)
            
            # Use staging if more than 5 chunks
            datasource.write_dataframe("my_table", df, staging_table_chunk_threshold=5)
        """
        start_time = time.perf_counter()
        
        # Use default threshold if not specified
        if staging_table_chunk_threshold is None:
            staging_table_chunk_threshold = self.DEFAULT_STAGING_TABLE_CHUNK_THRESHOLD
        
        # Handle mixed types if requested
        if handle_mixed_types:
            dataframe = self._handle_dataframe_mixed_types(dataframe)
        
        # Determine chunk size strategy
        if chunksize is not None:
            optimal_chunk_size = chunksize
            if self._debug_sql:
                self._logger.debug(f"Using manual chunk size: {optimal_chunk_size:,} rows")
        elif auto_optimize_chunks:
            optimal_chunk_size = self.calculate_optimal_chunk_size(
                dataframe, 
                max_message_size_mb=max_message_size_mb
            )
            
            estimated_size_mb = self.estimate_message_size(dataframe, optimal_chunk_size)
            
            if self._debug_sql:
                self._logger.debug(f"Auto-optimized chunk size: {optimal_chunk_size:,} rows")
                self._logger.debug(f"Estimated message size: {estimated_size_mb:.2f} MB")
                
                if estimated_size_mb > max_message_size_mb:
                    self._logger.warning(f"Estimated size ({estimated_size_mb:.2f} MB) exceeds limit ({max_message_size_mb} MB)")
        else:
            optimal_chunk_size = 20000
            if self._debug_sql:
                self._logger.debug(f"Using default chunk size: {optimal_chunk_size:,} rows")

        # Calculate total chunks for logging and decision making
        total_chunks = (len(dataframe) + optimal_chunk_size - 1) // optimal_chunk_size

        # BUG FIX: Correctly determine what approach will be used
        if staging_table_chunk_threshold == 0:
            will_use_staging = False  # threshold=0 means never use staging
        else:
            will_use_staging = total_chunks > staging_table_chunk_threshold

        if self._debug_sql:
            self._logger.debug(f"Write operation details:")
            self._logger.debug(f"  Table: {table_name}")
            self._logger.debug(f"  Rows: {len(dataframe):,}")
            self._logger.debug(f"  Chunk size: {optimal_chunk_size:,}")
            self._logger.debug(f"  Total chunks: {total_chunks}")
            self._logger.debug(f"  Staging threshold: {staging_table_chunk_threshold}")
            self._logger.debug(f"  Will use: {'staging table' if will_use_staging else 'direct insert'}")
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
                    self._drop_and_create_table(table_name, dataframe)
                    table_created = True
                elif if_table_exists == 'truncate':
                    if not force:
                        self._check_schema_compatibility(table_name, dataframe)
                    self._truncate_table(table_name)
                elif if_table_exists == 'append':
                    if not force:
                        self._check_schema_compatibility(table_name, dataframe)
                else:
                    raise ValueError(f"Invalid option for if_table_exists: {if_table_exists}")
            else:
                self._create_table(table_name, dataframe)
                table_created = True

            # Insert data with optimized chunk size and staging threshold
            self._insert_dataframe(table_name, dataframe, optimal_chunk_size, staging_table_chunk_threshold)
            
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
            
            if self._debug_sql:
                self._logger.error(f"Write operation failed: {str(e)}")
                if "grpc: received message larger than max" in str(e):
                    self._logger.error(f"Suggestion: Try reducing max_message_size_mb parameter or manual chunksize")
            
            raise

    def calculate_optimal_chunk_size(self, dataframe: pandas.DataFrame, 
                                    max_message_size_mb: float = 4.0,
                                    safety_factor: float = 0.8) -> int:
        """
        Calculate optimal chunk size to maximize performance while staying under gRPC limits.
        
        Args:
            dataframe: DataFrame to analyze
            max_message_size_mb: Maximum message size in MB (default 4MB)
            safety_factor: Safety multiplier to account for serialization overhead (default 0.8)
        
        Returns:
            int: Optimal chunk size in number of rows
        """
        if len(dataframe) == 0:
            return 1000
        
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
        min_chunk_size = 100
        max_chunk_size = 50000
        
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

    def get_db_type(self) -> str:
        """Return the database type, respecting overrides."""
        if self._db_type_override is not None:
            return self._db_type_override

        if self._db_type is not None:
            return self._db_type

        # Try to detect database type
        try:
            # Check for Trino first
            if self._detect_trino():
                self._db_type = 'trino'
                return self._db_type
            
            # Try database-specific queries
            detection_queries = [
                # PostgreSQL
                ("SELECT version()", ['postgresql', 'postgres']),
                # MySQL
                ("SELECT VERSION()", ['mysql', 'mariadb']),
                # SQL Server
                ("SELECT @@VERSION", ['microsoft', 'sql server']),
                # Oracle
                ("SELECT * FROM V$VERSION WHERE ROWNUM = 1", ['oracle']),
                # DB2
                ("VALUES(CURRENT SERVER)", ['db2']),
            ]
            
            for query, indicators in detection_queries:
                try:
                    result = self.query(query).to_pandas()
                    result_str = str(result).lower()
                    if any(ind in result_str for ind in indicators):
                        self._db_type = indicators[0]
                        return self._db_type
                except:
                    continue
            
        except:
            pass
        
        # Default to unknown
        self._db_type = 'unknown'
        return self._db_type

    def _detect_trino(self) -> bool:
        """Detect if we're running through Trino."""
        if self._is_trino_cached is not None:
            return self._is_trino_cached
        
        try:
            # Try Trino-specific query
            self.query("SHOW CATALOGS")
            self._is_trino_cached = True
            return True
        except:
            self._is_trino_cached = False
            return False

    def set_db_type_override(self, db_type: Optional[str]) -> None:
        """Override the detected database type."""
        if db_type is not None:
            db_type_lower = db_type.lower()
            supported_types = {'postgresql', 'mysql', 'db2', 'oracle', 'sqlserver', 'trino', 'unknown'}
            
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
        
        # Clear cached detection result
        self._db_type = None
        
        # Update type mappings
        db_type_to_use = self.get_db_type()
        self._type_map = self._type_mappings.get(db_type_to_use, self._type_mappings['unknown'])

    def enable_sql_debug(self, enabled: bool = True) -> None:
        """Enable or disable SQL debug logging."""
        self._debug_sql = enabled
        if enabled:
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self._logger.addHandler(handler)
            
            self._logger.setLevel(logging.DEBUG)
            self._logger.info("SQL debugging enabled")

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            escaped_table = self._escape_identifier(table_name)
            self.query(f"SELECT 1 FROM {escaped_table} LIMIT 1")
            return True
        except DominoError:
            return False

    def table(self, table_name: str) -> 'TableQuery':
        """Get a table interface for fluent querying."""
        return TableQuery(self, table_name)

    def wrap_passthrough_query(self, query: str) -> str:
        """Wrap a query for database passthrough to bypass query engine optimization."""
        escaped_query = query.replace("'", "''")
        return f"SELECT * FROM TABLE(system.query(query => '{escaped_query}'))"

    def passthrough_query(self, query: str) -> Result:
        """Execute a query using database passthrough wrapper."""
        wrapped_query_str = self.wrap_passthrough_query(query)
        
        if self._debug_sql:
            self._logger.debug(f"Executing passthrough query: {wrapped_query_str}")
        
        return self.query(wrapped_query_str)

    def register_type(self, python_type: Type, sql_type: str) -> None:
        """Register a custom type mapping."""
        self._type_map[python_type] = sql_type

    def get_type_mappings(self) -> Dict[str, str]:
        """Return all registered type mappings."""
        return {getattr(k, '__name__', str(k)): v for k, v in self._type_map.items()}

    # Performance tracking context manager
    @contextlib.contextmanager
    def _performance_tracking(self, operation: str, row_count: int):
        """Track and log performance metrics for database operations."""
        if self._debug_sql:
            start_time = time.time()
            self._logger.debug(f"Starting {operation}")
            
        yield
        
        if self._debug_sql:
            elapsed = time.time() - start_time
            rows_per_sec = row_count / elapsed if elapsed > 0 else 0
            self._logger.debug(
                f"{operation} completed: {row_count:,} rows in {elapsed:.1f}s "
                f"({rows_per_sec:,.0f} rows/sec)"
            )

    # Insert methods
    def _insert_dataframe(self, table_name: str, dataframe: pandas.DataFrame, 
                         chunksize: int, staging_threshold: int) -> None:
        """Insert DataFrame using bulk methods with configurable staging threshold."""
        if len(dataframe) > 1000:
            self._bulk_insert_dataframe(table_name, dataframe, chunksize, staging_threshold)
        else:
            self._fallback_bulk_insert(table_name, dataframe, chunksize)

    def _bulk_insert_dataframe(self, table_name: str, dataframe: pandas.DataFrame, 
                              chunksize: int, staging_threshold: int) -> None:
        """Perform optimized bulk inserts based on database type."""
        db_type = self.get_db_type()
        
        try:
            if db_type in ['postgresql', 'mysql', 'sqlserver', 'db2', 'oracle', 'trino']:
                self._database_bulk_insert(table_name, dataframe, chunksize, db_type, staging_threshold)
            else:
                self._fallback_bulk_insert(table_name, dataframe, chunksize)
        except Exception as e:
            self._logger.warning(f"Bulk insert failed for {db_type}, falling back to standard insert: {e}")
            self._fallback_bulk_insert(table_name, dataframe, chunksize)

    def _database_bulk_insert(self, table_name: str, dataframe: pandas.DataFrame, 
                             chunk_size: int, db_type: str, staging_threshold: int) -> None:
        """Universal bulk insert method for all database types."""
        total_chunks = (len(dataframe) + chunk_size - 1) // chunk_size
        
        if self._debug_sql:
            self._logger.debug(
                f"{db_type.upper()} bulk insert: {len(dataframe):,} rows, "
                f"{total_chunks} chunks, threshold={staging_threshold}"
            )
        
        if staging_threshold == 0 or total_chunks <= staging_threshold:
            # Direct insert using enhanced fallback
            self._fallback_bulk_insert(table_name, dataframe, chunk_size)
        else:
            # Use staging table
            self._generic_staging_bulk_insert(table_name, dataframe, chunk_size, db_type)

    def _fallback_bulk_insert(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """Optimized multi-row INSERT that works as both fallback and direct insert."""
        escaped_table = self._escape_identifier(table_name)
        escaped_columns = ', '.join(self._escape_identifier(col) for col in dataframe.columns)
        
        # Detect database type for optimization
        db_type = self.get_db_type()
        
        with self._performance_tracking(f"{db_type} bulk insert", len(dataframe)):
            rows_inserted = 0
            for i in range(0, len(dataframe), chunksize):
                chunk = dataframe.iloc[i:i+chunksize]
                
                # Build INSERT query
                insert_query = self._build_insert_query(
                    escaped_table, 
                    escaped_columns, 
                    chunk, 
                    db_type
                )
                
                if self._debug_sql:
                    query_size = len(insert_query.encode('utf-8'))
                    self._logger.debug(
                        f"Chunk {(i//chunksize)+1}: {len(chunk)} rows, {query_size:,} bytes"
                    )
                    
                self.query(insert_query)
                rows_inserted += len(chunk)

    def _generic_staging_bulk_insert(self, table_name: str, dataframe: pandas.DataFrame, 
                                    chunk_size: int, db_type: str) -> None:
        """Universal staging table approach for all databases."""
        escaped_target = self._escape_identifier(table_name)
        columns = [self._escape_identifier(col) for col in dataframe.columns]
        columns_str = ', '.join(columns)
        
        with self._performance_tracking(f"{db_type} staging insert", len(dataframe)):
            staging_table = None
            escaped_staging = None
            
            try:
                # Create staging table
                schema_def = self._generate_schema(dataframe)
                staging_table, escaped_staging = self._create_staging_table(db_type, schema_def, dataframe)
                
                # Insert into staging with larger chunks
                staging_chunk_size = self._get_staging_chunk_size(chunk_size, db_type)
                
                for i in range(0, len(dataframe), staging_chunk_size):
                    batch = dataframe.iloc[i:i+staging_chunk_size]
                    
                    insert_query = self._build_insert_query(
                        escaped_staging if db_type != 'sqlserver' else staging_table,
                        columns_str,
                        batch,
                        db_type
                    )
                    
                    if self._debug_sql:
                        self._logger.debug(f"Inserting chunk into staging: {len(batch)} rows")
                    
                    self.query(insert_query)
                
                # Optional optimization
                self._optimize_staging_table(db_type, escaped_staging, len(dataframe))
                
                # Transfer to target
                if self._debug_sql:
                    self._logger.debug("Transferring from staging to target table")
                
                if db_type == 'sqlserver':
                    transfer_query = f"INSERT INTO {escaped_target} ({columns_str}) SELECT {columns_str} FROM {staging_table}"
                else:
                    transfer_query = f"INSERT INTO {escaped_target} ({columns_str}) SELECT {columns_str} FROM {escaped_staging}"
                
                self.query(transfer_query)
                
            finally:
                # Always cleanup
                if staging_table and escaped_staging:
                    self._drop_staging_table(db_type, staging_table, escaped_staging)

    def _create_staging_table(self, db_type: str, schema_def: str, dataframe: pandas.DataFrame) -> tuple[str, str]:
        """Create staging table and return (staging_table_name, escaped_name)."""
        unique_suffix = uuid.uuid4().hex[:8]
        
        # Generate table name
        if db_type == 'sqlserver':
            staging_table = f"#staging_{unique_suffix}"
            escaped_staging = staging_table
        elif db_type == 'oracle':
            staging_table = f"STG_{unique_suffix[:8]}"
            escaped_staging = self._escape_identifier(staging_table)
        else:
            staging_table = f"staging_{unique_suffix}"
            escaped_staging = self._escape_identifier(staging_table)
        
        # Build CREATE query
        if db_type == 'postgresql':
            create_query = f"CREATE UNLOGGED TABLE {escaped_staging} ({schema_def})"
        elif db_type == 'mysql':
            engine = "MEMORY" if len(dataframe) < 100000 else "InnoDB"
            create_query = f"CREATE TABLE {escaped_staging} ({schema_def}) ENGINE={engine}"
        elif db_type == 'sqlserver':
            create_query = f"CREATE TABLE {staging_table} ({schema_def})"
        elif db_type == 'oracle':
            create_query = f"CREATE GLOBAL TEMPORARY TABLE {escaped_staging} ({schema_def}) ON COMMIT PRESERVE ROWS"
        else:
            create_query = f"CREATE TABLE {escaped_staging} ({schema_def})"
        
        if self._debug_sql:
            self._logger.debug(f"Creating staging table: {staging_table}")
        
        self.query(create_query)
        return staging_table, escaped_staging

    def _drop_staging_table(self, db_type: str, staging_table: str, escaped_staging: str) -> None:
        """Drop staging table with database-specific syntax."""
        try:
            if db_type == 'sqlserver':
                self.query(f"DROP TABLE IF EXISTS {staging_table}")
            elif db_type == 'oracle':
                self.query(f"DROP TABLE {escaped_staging} PURGE")
            else:
                self.query(f"DROP TABLE IF EXISTS {escaped_staging}")
        except:
            if self._debug_sql:
                self._logger.debug("Staging table cleanup skipped (may be auto-cleaned)")

    def _optimize_staging_table(self, db_type: str, escaped_staging: str, row_count: int) -> None:
        """Run optimizer on staging table if beneficial."""
        if row_count > 50000:
            try:
                if db_type == 'postgresql':
                    self.query(f"ANALYZE {escaped_staging}")
                elif db_type == 'mysql':
                    self.query(f"ANALYZE TABLE {escaped_staging}")
            except:
                pass

    def _get_staging_chunk_size(self, base_chunk_size: int, db_type: str) -> int:
        """Get optimal chunk size for staging inserts based on database type."""
        if db_type in ['postgresql', 'mysql']:
            return base_chunk_size * 3
        elif db_type == 'sqlserver':
            return base_chunk_size * 2
        elif db_type in ['db2', 'trino']:
            return base_chunk_size * 2
        elif db_type == 'oracle':
            return base_chunk_size * 2
        else:
            return base_chunk_size

    def _build_insert_query(self, table_name: str, columns_str: str, 
                           batch: pandas.DataFrame, db_type: str) -> str:
        """Build database-optimized INSERT query."""
        # Build VALUES rows
        values_rows = []
        for _, row in batch.iterrows():
            formatted_values = [self._format_value(val) for val in row]
            values_rows.append(f"({', '.join(formatted_values)})")
        
        if db_type in ['db2', 'trino']:
            # DB2/Trino prefer INSERT...SELECT FROM VALUES
            values_str = ',\n       '.join(values_rows)
            return f"""
            INSERT INTO {table_name} ({columns_str})
            SELECT * FROM (
            VALUES {values_str}
            ) AS t({columns_str})
            """
        
        elif db_type == 'oracle' and len(values_rows) > 1:
            # Oracle INSERT ALL for multiple rows
            insert_parts = []
            for values_row in values_rows:
                insert_parts.append(f"INTO {table_name} ({columns_str}) VALUES {values_row}")
            
            return f"""
            INSERT ALL
            {chr(10).join(insert_parts)}
            SELECT 1 FROM DUAL
            """
        
        else:
            # Standard INSERT VALUES
            values_str = ',\n'.join(values_rows)
            return f"INSERT INTO {table_name} ({columns_str}) VALUES {values_str}"

    # Schema and table management methods
    def _drop_and_create_table(self, table_name: str, dataframe: pandas.DataFrame) -> None:
        """Drop existing table and create a new one."""
        escaped_table = self._escape_identifier(table_name)
        
        try:
            self.query(f"DROP TABLE {escaped_table}")
        except Exception as e:
            self._logger.warning(f"Error dropping table {table_name}: {str(e)}")
            raise

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

    def _drop_table_quietly(self, table_name: str) -> None:
        """Attempt to drop table without raising errors."""
        try:
            escaped_table = self._escape_identifier(table_name)
            self.query(f"DROP TABLE {escaped_table}")
            if self._debug_sql:
                self._logger.debug(f"Cleaned up table after failed write: {table_name}")
        except Exception as drop_error:
            self._logger.error(f"Failed to clean up table {table_name} after error: {str(drop_error)}")

    def _check_schema_compatibility(self, table_name: str, dataframe: pandas.DataFrame, force: bool = False) -> None:
        """Check schema compatibility between DataFrame and existing table."""
        try:
            escaped_table = self._escape_identifier(table_name)
            schema_query = f"SELECT * FROM {escaped_table} LIMIT 0"
            result = self.query(schema_query)
            table_columns = result.to_pandas().columns.tolist()

            df_columns = dataframe.columns.tolist()

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
                        self._logger.warning("Forcing write despite schema mismatch: " + " | ".join(error_msg))

        except Exception as e:
            if self._debug_sql:
                self._logger.error(f"Schema check failed: {str(e)}")
            if not force:
                raise ValueError(
                    "Cannot write to table - schema mismatch detected. "
                    "Use force=True to attempt the operation anyway."
                ) from e

    def _escape_identifier(self, identifier: str) -> str:
        """Escape an SQL identifier (table or column name)."""
        if '.' in identifier:
            parts = identifier.split('.', 1)
            schema = parts[0].strip()
            table = parts[1].strip()
            
            schema = schema.strip('"').strip('`').strip('[').strip(']')
            table = table.strip('"').strip('`').strip('[').strip(']')
            
            return f'"{schema}"."{table}"'
        else:
            clean_identifier = identifier.strip('"').strip('`').strip('[').strip(']')
            return f'"{clean_identifier}"'

    def _generate_schema(self, dataframe: pandas.DataFrame) -> str:
        """Generate SQL schema from DataFrame."""
        columns = []
        for col, dtype in dataframe.dtypes.items():
            escaped_col = self._escape_identifier(col)
            sql_type = self._map_dtype_to_sql(dtype, dataframe[col])
            columns.append(f"{escaped_col} {sql_type}")
        return ", ".join(columns)

    def _handle_dataframe_mixed_types(self, dataframe: pandas.DataFrame) -> pandas.DataFrame:
        """Process a DataFrame to handle mixed types in object columns."""
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

        numeric_types = {int, float, numpy.int64, numpy.float64, numpy.int32, numpy.float32}
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

        # Standard type checks
        if pandas.api.types.is_bool_dtype(dtype):
            return self._type_map.get(bool, "BOOLEAN")
        if pandas.api.types.is_integer_dtype(dtype):
            return self._get_integer_type_by_range(series)
        if pandas.api.types.is_float_dtype(dtype):
            return self._get_float_type_by_database()
        if pandas.api.types.is_datetime64_any_dtype(dtype):
            if hasattr(dtype, 'tz') and dtype.tz is not None:
                return self._get_timezone_aware_timestamp()
            return self._type_map.get(datetime, "TIMESTAMP")
        if pandas.api.types.is_string_dtype(dtype) or pandas.api.types.is_object_dtype(dtype):
            return self._get_varchar_type_by_length(series)
        if dtype == 'bytes' or str(dtype).startswith('bytes'):
            return self._type_map.get(bytes, "VARBINARY(4000)")

        return "VARCHAR(255)"

    def _get_integer_type_by_range(self, series) -> str:
        """Get appropriate integer type based on value range."""
        if series is not None:
            try:
                mn, mx = series.min(), series.max()
                db_type = self.get_db_type()
                
                if mn >= -128 and mx <= 127:
                    if db_type in ['mysql', 'sqlserver']:
                        return "TINYINT"
                    else:
                        return "SMALLINT"
                elif mn >= -32768 and mx <= 32767:
                    return "SMALLINT"
                elif mn >= -2147483648 and mx <= 2147483647:
                    return "INTEGER"
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
        elif db_type in ['mysql', 'db2', 'trino']:
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
        elif db_type in ['mysql', 'trino']:
            return "JSON"
        elif db_type in ['db2', 'oracle']:
            return "CLOB"
        elif db_type == 'sqlserver':
            return "NVARCHAR(MAX)"
        else:
            return "VARCHAR(4000)"

    def _format_value(self, value) -> str:
        """Format value for SQL insertion with database-specific CAST operations."""
        if pandas.isna(value):
            return "NULL"

        db_type = self.get_db_type()
        
        cast_map = {
            'postgresql': {
                'float': 'DOUBLE PRECISION',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'BOOLEAN',
                'int': 'INTEGER',
                'str': 'VARCHAR',
                'json': 'JSONB'
            },
            'mysql': {
                'float': 'DOUBLE',
                'datetime': 'DATETIME',
                'date': 'DATE',
                'bool': 'BOOLEAN',
                'int': 'INTEGER',
                'str': 'VARCHAR',
                'json': 'JSON'
            },
            'db2': {
                'float': 'DOUBLE',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'SMALLINT',
                'int': 'INTEGER',
                'str': 'VARCHAR',
                'json': 'CLOB'
            },
            'trino': {
                'float': 'DOUBLE',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'BOOLEAN',
                'int': 'BIGINT',
                'str': 'VARCHAR',
                'json': 'JSON'
            },
            'oracle': {
                'float': 'BINARY_DOUBLE',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'NUMBER',
                'int': 'NUMBER',
                'str': 'VARCHAR2',
                'json': 'CLOB'
            },
            'sqlserver': {
                'float': 'FLOAT',
                'datetime': 'DATETIME2',
                'date': 'DATE',
                'bool': 'BIT',
                'int': 'INT',
                'str': 'NVARCHAR',
                'json': 'NVARCHAR(MAX)'
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

        # Boolean handling
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

        # JSON/Dictionary/List handling
        elif isinstance(value, (dict, list)):
            json_str = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            escaped_str = json_str.replace("'", "''")
            
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

        # NumPy array handling
        elif isinstance(value, numpy.ndarray):
            try:
                array_list = value.tolist()
                json_str = json.dumps(array_list, ensure_ascii=False, separators=(',', ':'))
                escaped_str = json_str.replace("'", "''")
                
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
                str_value = str(value)
                escaped_str = str_value.replace("'", "''")
                return f"CAST('{escaped_str}' AS {cast_types['str']})"

        # String handling
        else:
            str_value = str(value)
            escaped_str = str_value.replace("'", "''")
            
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

    def Object(self, key: str) -> _Object:  # pylint: disable=invalid-name
        """Return an object with given key and datasource client."""
        return _Object(datasource=self, key=key)

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
    
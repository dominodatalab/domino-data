"""Datasource module."""

from typing import Any, Dict, List, Optional, cast

import configparser
import json
import os

import attr
import backoff
import httpx
import pandas
import urllib3
import logging
import numpy
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union, Type
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
    """Represents a tabular type datasource."""
    
    _debug_sql = attr.ib(default=False, init=False, repr=False)
    _logger = attr.ib(factory=lambda: logging.getLogger(__name__), init=False, repr=False)
    _type_map = attr.ib(factory=dict, init=False, repr=False)
    _varchar_small_threshold = attr.ib(default=50, init=False)
    _varchar_medium_threshold = attr.ib(default=255, init=False)
    
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
                dict: "VARCHAR(4000)",
                list: "VARCHAR(4000)",
                pandas.Int64Dtype: "INTEGER",
                pandas.Float64Dtype: "DOUBLE PRECISION",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "BOOLEAN",
                pandas.DatetimeTZDtype: "TIMESTAMP",
                numpy.int8: "SMALLINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "INTEGER",
                numpy.float32: "REAL",
                numpy.float64: "DOUBLE PRECISION",
            },
            'mysql': {
                bool: "BOOLEAN",
                int: "INTEGER",
                float: "DOUBLE",
                str: "VARCHAR(255)",
                datetime: "DATETIME",
                date: "DATE",
                Decimal: "DECIMAL",
                dict: "VARCHAR(4000)",
                list: "VARCHAR(4000)",
                pandas.Int64Dtype: "INTEGER",
                pandas.Float64Dtype: "DOUBLE",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "BOOLEAN",
                pandas.DatetimeTZDtype: "DATETIME",
                numpy.int8: "SMALLINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "INTEGER",
                numpy.float32: "REAL",
                numpy.float64: "DOUBLE",
            },
            'db2': {
                bool: "SMALLINT",  # DB2 doesn't have native BOOLEAN
                int: "INTEGER",
                float: "DOUBLE",
                str: "VARCHAR(255)",
                datetime: "TIMESTAMP",
                date: "DATE",
                Decimal: "DECIMAL",
                dict: "VARCHAR(4000)",
                list: "VARCHAR(4000)",
                pandas.Int64Dtype: "INTEGER",
                pandas.Float64Dtype: "DOUBLE",
                pandas.StringDtype: "VARCHAR(255)",
                pandas.BooleanDtype: "SMALLINT",
                pandas.DatetimeTZDtype: "TIMESTAMP",
                numpy.int8: "SMALLINT",
                numpy.int16: "SMALLINT",
                numpy.int32: "INTEGER",
                numpy.int64: "INTEGER",
                numpy.float32: "REAL",
                numpy.float64: "DOUBLE",
            },
            'unknown': {  # Fallback for unsupported databases
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
            }
        }
        
        # Set current database type mapping
        db_type = self._get_db_type()
        self._type_map = self._type_mappings.get(db_type, self._type_mappings['unknown'])   

    _db_type = None  # Add class-level cache

    def _get_db_type(self) -> str:
        """Detect and cache database type, only check once per session."""
        if self._db_type is not None:
            return self._db_type

        # Try raw connection first
        try:
            conn = self.client.raw_connection()
            if hasattr(conn, 'pgconn'):
                self._db_type = 'postgresql'
            elif 'mysql' in str(type(conn)).lower():
                self._db_type = 'mysql'
            elif 'db2' in str(type(conn)).lower():
                self._db_type = 'db2'
            else:
                self._db_type = 'unknown'
        except Exception:
            pass

        # Fallback to version query (only if needed)
        if self._db_type is None:
            try:
                version_info = self.query("SELECT version()").to_pandas().iat[0, 0].lower()
                if 'postgresql' in version_info:
                    self._db_type = 'postgresql'
                elif 'mysql' in version_info:
                    self._db_type = 'mysql'
                elif 'db2' in version_info:
                    self._db_type = 'db2'
                else:
                    self._db_type = 'unknown'
            except Exception:
                self._db_type = 'unknown'

        if self._debug_sql:
            self._logger.debug(f"Using database type: {self._db_type}")

        return self._db_type

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
        chunksize: int = 10000,
        handle_mixed_types: bool = True,
        force: bool = False
    ) -> None:
        """
        Write DataFrame to a table in the datasource.

        Args:
            table_name: Name of the table to write to.
            dataframe: DataFrame containing the data to write.
            if_table_exists: Action if table exists:
                - 'fail': Raise an error if table exists (default)
                - 'replace': Drop and recreate the table
                - 'append': Append data to the existing table
                - 'truncate': Empty the table but keep its structure
            chunksize: Number of rows to insert in each batch for large DataFrames.
            handle_mixed_types: If True, detect and handle mixed types in object columns.
            force: If True, attempt to append/truncate even if schema compatibility issues are detected.

        Raises:
            ValueError: If operation cannot be completed safely.

        Examples:
            # Create a new table, fail if it already exists (default)
            datasource.write_dataframe("my_table", df)

            # Replace an existing table if it exists
            datasource.write_dataframe("my_table", df, if_table_exists='replace')

            # Append data to an existing table (will check schema compatibility)
            datasource.write_dataframe("my_table", df, if_table_exists='append')

            # Truncate an existing table and add new data (will check schema compatibility)
            datasource.write_dataframe("my_table", df, if_table_exists='truncate')

            # Force append even if there are schema compatibility issues (not recommended)
            datasource.write_dataframe("my_table", df, if_table_exists='append', force=True)
        """
        # Input validation
        if dataframe is None or dataframe.empty:
            raise ValueError("DataFrame cannot be None or empty")

        valid_options = ['fail', 'replace', 'append', 'truncate']
        if if_table_exists not in valid_options:
            raise ValueError(f"if_table_exists must be one of {valid_options}, got '{if_table_exists}'")

        # Handle mixed types if requested
        if handle_mixed_types:
            dataframe = self._handle_dataframe_mixed_types(dataframe)

        table_exists = self.table_exists(table_name)

        # Handle table creation/modification based on if_table_exists
        if table_exists:
            if if_table_exists == 'fail':
                raise ValueError(
                    f"Table '{table_name}' already exists. Use if_table_exists='replace', 'append', or 'truncate' to modify it."
                )
            elif if_table_exists == 'replace':
                # No schema checks here—just drop and recreate
                self._drop_and_create_table(table_name, dataframe)
            elif if_table_exists == 'truncate':
                if not force:
                    self._check_schema_compatibility(table_name, dataframe)
                self._truncate_table(table_name)
            elif if_table_exists == 'append':
                if not force:
                    self._check_schema_compatibility(table_name, dataframe)
        else:
            # Table doesn't exist, create it
            self._create_table(table_name, dataframe)

        # Insert data
        self._insert_dataframe(table_name, dataframe, chunksize)

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
                    self._logger.warning(
                        f"Forcing write despite type mismatch: {str(type_err)}"
                    )

        except Exception as e:
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
                    self._logger.warning(
                        "Forcing write despite type mismatch: " + ", ".join(type_mismatches)
                    )

        except Exception as e:
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

        # Booleans
        if pandas.api.types.is_bool_dtype(dtype):
            return "BOOLEAN"

        # Integers
        if pandas.api.types.is_integer_dtype(dtype):
            if series is not None:
                try:
                    mn, mx = series.min(), series.max()
                    if mn >= -2147483648 and mx <= 2147483647:
                        return "INTEGER"
                    return "BIGINT"
                except Exception:
                    pass
            return "INTEGER"

        # Floats: use DOUBLE PRECISION for PostgreSQL, DOUBLE for MySQL/DB2, FLOAT for others
        if pandas.api.types.is_float_dtype(dtype):
            db_type = self._get_db_type()
            if db_type == 'postgresql':
                return "DOUBLE PRECISION"
            elif db_type in ['mysql', 'db2']:
                return "DOUBLE"
            else:
                return "FLOAT"

        # Datetimes
        if pandas.api.types.is_datetime64_any_dtype(dtype):
            return "TIMESTAMP"

        # Strings and objects: size-based VARCHAR
        if pandas.api.types.is_string_dtype(dtype) or pandas.api.types.is_object_dtype(dtype):
            if series is not None:
                try:
                    # JSON-like detection
                    if series.str.contains(r'^\s*[\{\[]').any() and series.str.contains(r'[\}\]]\s*$').any():
                        return "VARCHAR(4000)"
                    max_len = series.astype(str).str.len().max()
                    if max_len < self._varchar_small_threshold:
                        return f"VARCHAR({max_len + 20})"
                    if max_len < self._varchar_medium_threshold:
                        return f"VARCHAR({max_len + 50})"
                    return "VARCHAR(4000)"
                except Exception:
                    pass
            return "VARCHAR(255)"

        # Fallback
        return "VARCHAR(255)"

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
        """Insert DataFrame into table in chunks.
        
        Args:
            table_name: Name of the table to insert into
            dataframe: DataFrame containing the data to insert
            chunksize: Number of rows to insert in each batch
        """
        # For very large DataFrames, use bulk insert for better performance
        if len(dataframe) > 1000:
            self._bulk_insert_dataframe(table_name, dataframe, chunksize)
        else:
            # For smaller DataFrames, use the original approach
            escaped_table = self._escape_identifier(table_name)
            for i in range(0, len(dataframe), chunksize):
                chunk = dataframe.iloc[i:i+chunksize]
                escaped_columns = ', '.join(self._escape_identifier(col) for col in dataframe.columns)
                values = ", ".join(f"({', '.join(map(self._format_value, row))})" for _, row in chunk.iterrows())
                
                insert_query = f"INSERT INTO {escaped_table} ({escaped_columns}) VALUES {values}"
                
                if self._debug_sql:
                    truncated_query = f"INSERT INTO {escaped_table} ({escaped_columns}) VALUES {values[:1000]}{'...' if len(values) > 1000 else ''}"
                    self._logger.debug(f"Executing SQL (truncated): {truncated_query}")
                
                self.query(insert_query)

    def _bulk_insert_dataframe(self, table_name: str, dataframe: pandas.DataFrame, chunksize: int) -> None:
        """Perform a more efficient bulk insert for large DataFrames.
        
        Args:
            table_name: Name of the table to insert into
            dataframe: DataFrame containing the data to insert
            chunksize: Number of rows to insert in each batch
            
        Note:
            This method currently uses the same approach as _insert_dataframe.
            A true bulk insert implementation would use database-specific features
            like prepared statements, COPY commands, or batch loading APIs.
            This is a placeholder for future optimization.
        """
        escaped_table = self._escape_identifier(table_name)
        for i in range(0, len(dataframe), chunksize):
            chunk = dataframe.iloc[i:i+chunksize]
            escaped_columns = ', '.join(self._escape_identifier(col) for col in dataframe.columns)
            values = ", ".join(f"({', '.join(map(self._format_value, row))})" for _, row in chunk.iterrows())
            
            insert_query = f"INSERT INTO {escaped_table} ({escaped_columns}) VALUES {values}"
            
            if self._debug_sql:
                self._logger.debug(f"Executing bulk insert for {len(chunk)} rows")
            
            self.query(insert_query)

    def _format_value(self, value) -> str:
        """
        Format value for SQL insertion with database-specific CAST operations.

        Args:
            value: Value to format for SQL insertion

        Returns:
            str: SQL expression for the value (e.g., 'CAST(28.2 AS DOUBLE PRECISION)')
        """
        if pandas.isna(value):
            return "NULL"

        db_type = self._get_db_type()
        cast_map = {
            'postgresql': {
                'float': 'DOUBLE PRECISION',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'BOOLEAN',
                'int': 'INTEGER',
                'str': 'VARCHAR'
            },
            'mysql': {
                'float': 'DOUBLE',
                'datetime': 'DATETIME',
                'date': 'DATE',
                'bool': 'BOOLEAN',
                'int': 'INTEGER',
                'str': 'VARCHAR'
            },
            'db2': {
                'float': 'DOUBLE',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'SMALLINT',
                'int': 'INTEGER',
                'str': 'VARCHAR'
            },
            'unknown': {
                'float': 'FLOAT',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'bool': 'BOOLEAN',
                'int': 'INTEGER',
                'str': 'VARCHAR'
            }
        }

        cast_types = cast_map.get(db_type, cast_map['unknown'])

        if isinstance(value, bool):
            if db_type == 'db2':
                return f"CAST({1 if value else 0} AS {cast_types['bool']})"
            else:
                return f"CAST({str(value).upper()} AS {cast_types['bool']})"
        elif isinstance(value, (int, numpy.integer)):
            return f"CAST({value} AS {cast_types['int']})"
        elif isinstance(value, (float, numpy.floating)):
            return f"CAST({value} AS {cast_types['float']})"
        elif isinstance(value, datetime):
            timestamp_str = value.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            return f"CAST('{timestamp_str}' AS {cast_types['datetime']})"
        elif isinstance(value, date):
            return f"CAST('{value.isoformat()}' AS {cast_types['date']})"
        elif isinstance(value, (dict, list)):
            json_str = json.dumps(value)
            escaped_str = json_str.replace("'", "''")
            return f"CAST('{escaped_str}' AS {cast_types['str']})"
        elif isinstance(value, numpy.ndarray):
            array_list = value.tolist()
            array_str = str(array_list)
            escaped_str = array_str.replace("'", "''")
            return f"CAST('{escaped_str}' AS {cast_types['str']})"
        else:
            str_value = str(value)
            escaped_str = str_value.replace("'", "''")
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

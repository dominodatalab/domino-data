"""Datasource module."""

from typing import Any, Dict, List, Optional, Union, cast

import json
import os
from enum import Enum

import attr
import backoff
import httpx
import pandas
from pyarrow import ArrowException, flight, parquet

from datasource_api_client.api.datasource import get_datasource_by_name
from datasource_api_client.api.proxy import get_key_url, list_keys, log_metric
from datasource_api_client.models import DatasourceConfig as APIConfig
from datasource_api_client.models import (
    DatasourceDto,
    DatasourceDtoDataSourceType,
    ErrorResponse,
    KeyRequest,
    ListRequest,
    LogMetricM,
    LogMetricT,
    ProxyErrorResponse,
)

from .auth import AuthenticatedClient, AuthMiddlewareFactory, ProxyClient
from .logging import logger

ACCEPT_HEADERS = {"Accept": "application/json"}

ELEMENT_TYPE_METADATA = "__element_type_metadata"
ELEMENT_VALUE_METADATA = "__element_value_metadata"

CREDENTIAL_TYPE = "credential"
CONFIGURATION_TYPE = "configuration"

FLIGHT_ERROR_SPLIT = ". Client context:"


class DominoError(Exception):
    """Base exception for known errors."""


class UnauthenticatedError(DominoError):
    """To handle exponential backoff."""


def _unpack_flight_error(error: str) -> str:
    """Unpack a flight error message by remove extra information."""
    try:
        return error.split(FLIGHT_ERROR_SPLIT, maxsplit=1)[0]
    except ValueError:
        return error


class ConfigElem(Enum):
    """Enumeration of valid config elements."""

    ACCOUNT = "account"
    BUCKET = "bucket"
    DATABASE = "database"
    HOST = "host"
    PORT = "port"
    REGION = "region"
    ROLE = "role"
    SCHEMA = "schema"
    WAREHOUSE = "warehouse"


class CredElem(Enum):
    """Enumeration of valid credential elements."""

    PASSWORD = "password"
    USERNAME = "username"


def _cred(elem: CredElem) -> Any:
    """Type helper for credentials attributes."""
    metadata = {
        ELEMENT_TYPE_METADATA: CREDENTIAL_TYPE,
        ELEMENT_VALUE_METADATA: elem,
    }
    return attr.ib(default=None, kw_only=True, metadata=metadata)


def _filter_cred(att: Any, _: Any) -> Any:
    """Filter credential type attributes."""
    return att.metadata[ELEMENT_TYPE_METADATA] == CREDENTIAL_TYPE


def _config(elem: ConfigElem) -> Any:
    """Type helper for configuration attributes."""
    metadata = {
        ELEMENT_TYPE_METADATA: CONFIGURATION_TYPE,
        ELEMENT_VALUE_METADATA: elem,
    }
    return attr.ib(default=None, kw_only=True, metadata=metadata)


def _filter_config(att: Any, _: Any) -> Any:
    """Filter configuration type attributes."""
    return att.metadata[ELEMENT_TYPE_METADATA] == CONFIGURATION_TYPE


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


@attr.s(auto_attribs=True)
class RedshiftConfig(Config):
    """Redshift datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)

    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    username: Optional[str] = _cred(elem=CredElem.USERNAME)


@attr.s(auto_attribs=True)
class SnowflakeConfig(Config):
    """Snowflake datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    schema: Optional[str] = _config(elem=ConfigElem.SCHEMA)
    warehouse: Optional[str] = _config(elem=ConfigElem.WAREHOUSE)
    role: Optional[str] = _config(elem=ConfigElem.ROLE)

    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    username: Optional[str] = _cred(elem=CredElem.USERNAME)


@attr.s(auto_attribs=True)
class S3Config(Config):
    """S3 datasource configurationn."""

    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    aws_access_key_id: Optional[str] = _cred(elem=CredElem.USERNAME)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.PASSWORD)


DatasourceConfig = Union[Config, RedshiftConfig, SnowflakeConfig, S3Config]


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
        parquet.write_table(table, where)


@attr.s
class _Object:
    """Represents an object in a object store."""

    datasource: "ObjectStoreDatasource" = attr.ib(repr=False)
    key: str = attr.ib()

    def get(self) -> bytes:
        """Get object content as bytes."""
        signed_url = self.datasource.get_key_url(self.key, False)
        res = httpx.get(signed_url)
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
        signed_url = self.datasource.get_key_url(self.key, False)
        content_size = 0
        with httpx.stream("GET", signed_url) as stream, open(filename, "wb") as file:
            for data in stream.iter_bytes():
                content_size += len(data)
                file.write(data)

        self.datasource.client._log_metric(  # pylint: disable=protected-access
            self.datasource.datasource_type,
            content_size,
            False,
        )

    def download_fileobj(self, fileobj: Any) -> None:
        """Download object content to file like object.

        Args:
            fileobj: A file-like object to download into.
                At a minimum, it must implement the write method and must accept bytes.
        """
        signed_url = self.datasource.get_key_url(self.key, False)
        content_size = 0
        with httpx.stream("GET", signed_url) as stream:
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
        signed_url = self.datasource.get_key_url(self.key, True)
        res = httpx.put(signed_url, content=content)
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
        signed_url = self.datasource.get_key_url(self.key, True)
        with open(filename, "rb") as file:
            res = httpx.put(signed_url, content=file)
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
        signed_url = self.datasource.get_key_url(self.key, True)
        res = httpx.put(signed_url, content=fileobj)
        res.raise_for_status()


@attr.s
class Datasource:
    """Represents a Domino datasource."""

    # pylint: disable=too-many-instance-attributes

    client: "DataSourceClient" = attr.ib(repr=False)
    config: Dict[str, Any] = attr.ib()
    credential_type: str = attr.ib()
    datasource_type: str = attr.ib()
    identifier: str = attr.ib()
    name: str = attr.ib()
    owner: str = attr.ib()

    _config_override: DatasourceConfig = attr.ib(factory=Config, init=False, repr=False)

    @classmethod
    def from_dto(cls, client: "DataSourceClient", dto: DatasourceDto) -> "Datasource":
        """Build a datasource from a given DTO."""
        return cls(
            client=client,
            config=dto.config.to_dict(),
            credential_type=dto.credential_type.value,
            datasource_type=dto.data_source_type.value,
            identifier=dto.id,
            name=dto.name,
            owner=dto.owner_info.owner_name,
        )

    def update(self, config: DatasourceConfig) -> None:
        """Store configuration override for future query calls.

        Args:
            config: One of S3Config, RedshiftConfig or SnowflakeConfig
        """
        self._config_override = config

    def reset_config(self) -> None:
        """Reset the configuration override."""
        self._config_override = Config()


@attr.s
class QueryDatasource(Datasource):
    """Represents a tabular type datasource."""

    def query(self, query: str) -> Result:
        """Execute a query against the datasource.

        Args:
            query: SQL statement to execute

        Returns:
            Result entity wrapping dataframe
        """
        return self.client.execute(
            self.identifier,
            query,
            config=self._config_override.config(),
            credential=self._config_override.credential(),
        )


@attr.s
class ObjectStoreDatasource(Datasource):
    """Represents a object store type datasource."""

    def Object(self, key: str) -> _Object:  # pylint: disable=invalid-name
        """Return an object with given key and datasource client."""
        return _Object(datasource=self, key=key)

    def list_objects(self, prefix: str = "") -> List[_Object]:
        """List objects in the object store datasource.

        Args:
            prefix: optional prefix to filter objects

        Returns:
            List of objects
        """
        keys = self.client.list_keys(
            self.identifier,
            prefix,
            config=self._config_override.config(),
            credential=self._config_override.credential(),
        )
        return [
            _Object(
                datasource=self,
                key=key,
            )
            for key in keys
            if not key.endswith("/")
        ]

    def get_key_url(self, object_key: str, is_read_write: bool = False) -> str:
        """Get a signed URL for the given key.

        Args:
            object_key: unique identifier of object to get signed URL for.
            is_read_write: whether the URL should allow writes or not.

        Returns:
            Signed URL for given key
        """
        return self.client.get_key_url(
            self.identifier,
            object_key,
            is_read_write,
            config=self._config_override.config(),
            credential=self._config_override.credential(),
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


DATASOURCES = {
    DatasourceDtoDataSourceType.SNOWFLAKECONFIG: QueryDatasource,
    DatasourceDtoDataSourceType.REDSHIFTCONFIG: QueryDatasource,
    DatasourceDtoDataSourceType.S3CONFIG: ObjectStoreDatasource,
}


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

    api_key: Optional[str] = attr.ib(factory=lambda: os.getenv("DOMINO_USER_API_KEY"))
    token_file: Optional[str] = attr.ib(factory=lambda: os.getenv("DOMINO_TOKEN_FILE"))

    def __attrs_post_init__(self):
        flight_host = os.getenv("DOMINO_DATASOURCE_PROXY_FLIGHT_HOST")
        domino_host = os.getenv("DOMINO_API_HOST", os.getenv("DOMINO_USER_HOST", ""))
        proxy_host = os.getenv("DOMINO_DATASOURCE_PROXY_HOST", "")

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
            token_file=self.token_file,
        )
        self.domino = AuthenticatedClient(
            base_url=f"{domino_host}/v4",
            api_key=self.api_key,
            token_file=self.token_file,
            headers=ACCEPT_HEADERS,
        )

    def _set_proxy(self):
        flight_host = os.getenv("DOMINO_DATASOURCE_PROXY_FLIGHT_HOST")
        self.proxy = flight.FlightClient(
            flight_host,
            middleware=[
                AuthMiddlewareFactory(
                    self.api_key,
                    self.token_file,
                )
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

        run_id = os.getenv("DOMINO_RUN_ID")
        response = get_datasource_by_name.sync_detailed(
            name,
            client=self.domino,
            run_id=run_id,
        )
        if response.status_code == 200:
            datasource_dto = cast(DatasourceDto, response.parsed)
            _datasource = DATASOURCES.get(datasource_dto.data_source_type, Datasource)
            return _datasource.from_dto(self, datasource_dto)

        message = cast(ErrorResponse, response.parsed).message
        logger.exception(message)
        raise Exception(message)

    @backoff.on_exception(backoff.expo, UnauthenticatedError, max_time=60)
    def list_keys(
        self,
        datasource_id: str,
        prefix: str,
        config: Dict[str, str],
        credential: Dict[str, str],
    ) -> List[str]:
        """List keys in a datasource.

        Args:
            datasource_id: unique identifier of a datasource
            prefix: prefix to filter keys with
            config: overwrite configuration dictionary
            credential: overwrite credential dictionary

        Returns:
            List of keys as string

        Raises:
            Exception: if the response from the Proxy is not 200
            UnauthenticatedError: if the request has invalid authentication
        """
        logger.info("list_keys", datasource_id=datasource_id, prefix=prefix)

        response = list_keys.sync_detailed(
            client=self.proxy_http,
            json_body=ListRequest(
                datasource_id=datasource_id,
                prefix=prefix,
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
            client=self.proxy_http,
            json_body=KeyRequest(
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
        type_map = {DatasourceDtoDataSourceType.S3CONFIG.value: LogMetricT.S3CONFIG}
        type_ = type_map.get(datasource_type)
        if not type_:
            return

        try:
            log_metric.sync_detailed(
                client=self.proxy_http,
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

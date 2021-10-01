"""Datasource module."""

from typing import Any, Dict, Optional, Union, cast

import json
import os
from enum import Enum

import attr
import pandas
from pyarrow import flight, parquet

from datasource_api_client.api.datasource import get_datasource_by_name
from datasource_api_client.models import DatasourceDto, ErrorResponse

from .auth import AuthenticatedClient, AuthMiddlewareFactory

ELEMENT_TYPE_METADATA = "__element_type_metadata"
ELEMENT_VALUE_METADATA = "__element_value_metadata"

CREDENTIAL_TYPE = "credential"
CONFIGURATION_TYPE = "configuration"


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


@attr.s
class RedshiftConfig(Config):
    """Redshift datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)

    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    username: Optional[str] = _cred(elem=CredElem.USERNAME)


@attr.s
class SnowflakeConfig(Config):
    """Snowflake datasource configuration."""

    database: Optional[str] = _config(elem=ConfigElem.DATABASE)
    schema: Optional[str] = _config(elem=ConfigElem.SCHEMA)
    warehouse: Optional[str] = _config(elem=ConfigElem.WAREHOUSE)
    role: Optional[str] = _config(elem=ConfigElem.ROLE)

    password: Optional[str] = _cred(elem=CredElem.PASSWORD)
    username: Optional[str] = _cred(elem=CredElem.USERNAME)


@attr.s
class S3Config(Config):
    """S3 datasource configurationn."""

    bucket: Optional[str] = _config(elem=ConfigElem.BUCKET)
    region: Optional[str] = _config(elem=ConfigElem.REGION)

    aws_access_key_id: Optional[str] = _cred(elem=CredElem.USERNAME)
    aws_secret_access_key: Optional[str] = _cred(elem=CredElem.PASSWORD)


DatasourceConfig = Union[RedshiftConfig, SnowflakeConfig, S3Config]


@attr.s
class Result:
    """Class for keeping query result metadata."""

    client: "Client" = attr.ib()
    reader: flight.FlightStreamReader = attr.ib()
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
class Datasource:
    """Represents a Domino datasource."""

    # pylint: disable=too-many-instance-attributes

    client: "Client" = attr.ib(repr=False)
    config: Dict[str, Any] = attr.ib()
    credential_type: str = attr.ib()
    datasource_type: str = attr.ib()
    identifier: str = attr.ib()
    name: str = attr.ib()
    owner: str = attr.ib()

    _config_override: Optional[DatasourceConfig] = attr.ib(default=None, init=False)

    @classmethod
    def from_dto(cls, client: "Client", dto: DatasourceDto) -> "Datasource":
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
        self._config_override = None

    def query(self, query: str) -> Result:
        """Execute a query against the datasource.

        Args:
            query: SQL statement to execute

        Returns:
            Result entity wrapping dataframe
        """
        if self._config_override is not None:
            return self.client.execute(
                self.identifier,
                query,
                config=self._config_override.config(),
                credential=self._config_override.credential(),
            )
        return self.client.execute(self.identifier, query)


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
class Client:
    """API client and bindings."""

    domino: AuthenticatedClient = attr.ib(init=False)
    proxy: flight.FlightClient = attr.ib(init=False)

    api_key: Optional[str] = attr.ib(factory=lambda: os.getenv("DOMINO_USER_API_KEY"))
    token_file: Optional[str] = attr.ib(factory=lambda: os.getenv("DOMINO_TOKEN_FILE"))

    def __attrs_post_init__(self):
        flight_host = os.getenv("DOMINO_DATASOURCE_PROXY_FLIGHT_HOST")
        domino_host = os.getenv("DOMINO_API_HOST")

        self.proxy = flight.FlightClient(
            flight_host,
            middleware=[
                AuthMiddlewareFactory(
                    self.api_key,
                    self.token_file,
                )
            ],
        )
        self.domino = AuthenticatedClient(
            base_url=f"{domino_host}/v4",
            api_key=self.api_key,
            token_file=self.token_file,
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
        run_id = os.getenv("DOMINO_RUN_ID")
        response = get_datasource_by_name.sync_detailed(
            name=name,
            run_id=run_id,
            client=self.domino,
        )
        if response.status_code == 200:
            return Datasource.from_dto(self, cast(DatasourceDto, response.parsed))
        raise Exception(cast(ErrorResponse, response.parsed).message)

    def execute(
        self,
        datasource_id: str,
        query: str,
        config: Optional[Dict[str, str]] = None,
        credential: Optional[Dict[str, str]] = None,
    ) -> Result:
        """Execute a given query against a datasource.

        Args:
            datasource_id: unique identifier of a datasource
            query: SQL query to execute
            config: overwrite configuration dictionary
            credential: overwrite credential dictionary

        Returns:
            Result entity encapsulating execution response
        """
        config = {} if not config else config
        credential = {} if not credential else credential
        reader = self.proxy.do_get(
            flight.Ticket(
                BoardingPass(
                    datasource_id=datasource_id,
                    query=query,
                    config=config,
                    credential=credential,
                ).to_json()
            )
        )
        return Result(self, reader, query)

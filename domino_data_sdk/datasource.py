"""Datasource module."""

from typing import Optional, cast

import json
import os
from dataclasses import dataclass

import attr
import pandas
from pyarrow import flight

from datasource_api_client.api.datasource import get_datasource_by_name
from datasource_api_client.models import (
    DatasourceDto,
    DatasourceDtoCredentialType,
    DatasourceDtoDataSourceType,
    ErrorResponse,
)

from .auth import AuthenticatedClient, AuthMiddlewareFactory


@dataclass
class Result:
    """Class for keeping query result metadata."""

    client: "Client"
    reader: flight.FlightStreamReader
    statement: str

    def to_pandas(self) -> pandas.DataFrame:
        """Load and transform the result into a pandas DataFrame."""
        return self.reader.read_pandas()


@dataclass(init=False)
class Datasource:
    """Class that represents a Domino datasource."""

    # pylint: disable=too-many-instance-attributes
    # datasource is a complex entity with many attributes

    client: "Client"
    credential_type: DatasourceDtoCredentialType
    datasource_type: DatasourceDtoDataSourceType
    identifier: str
    name: str
    owner: str
    owner_id: str

    def __init__(self, client: "Client", dto: DatasourceDto):
        self.client = client
        self.credential_type = dto.credential_type
        self.datasource_type = dto.data_source_type
        self.identifier = dto.id
        self.name = dto.name
        self.owner = dto.owner_info.owner_name
        self.owner_id = dto.owner_id

    def query(self, query: str) -> Result:
        """Execute a query against the datasource.

        Args:
          query: SQL statement to execute

        Returns:
          Result entity wrapping dataframe
        """
        return self.client.execute(self.identifier, self.owner_id, query)


@dataclass
class BoardingPass:
    """Class that represent a query request to the Datasource Proxy service."""

    datasource_id: str
    query: str
    user_id: str

    def to_json(self) -> str:
        """Serialize self to JSON."""
        return json.dumps(
            {
                "datasourceId": self.datasource_id,
                "sqlQuery": self.query,
                "userId": self.user_id,
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
        """
        run_id = os.getenv("DOMINO_RUN_ID")
        response = get_datasource_by_name.sync_detailed(
            name=name,
            run_id=run_id,
            client=self.domino,
        )
        if response.status_code == 200:
            return Datasource(self, cast(DatasourceDto, response.parsed))
        raise Exception(cast(ErrorResponse, response.parsed).message)

    def execute(self, datasource_id: str, owner_id: str, query: str) -> Result:
        """Execute a given query against a datasource.

        Args:
          datasource_id: unique identifier of a datasource
          query: SQL query to execute

        Returns:
          Result entity encapsulating execution response
        """
        reader = self.proxy.do_get(
            flight.Ticket(
                BoardingPass(
                    user_id=owner_id,
                    datasource_id=datasource_id,
                    query=query,
                ).to_json()
            )
        )
        return Result(self, reader, query)

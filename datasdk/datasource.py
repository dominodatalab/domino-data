"""Datasource features."""

from typing import Any, Dict, Literal

import os
from dataclasses import dataclass

import pandas
from pyarrow import flight


@dataclass
class Result:
    """Class for keeping query result metadata."""

    core: "Core"
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

    core: "Core"
    credential_type: Literal["Individual", "Shared"]
    datasource_type: Literal["Redshift", "Snowflake"]
    identifier: str
    name: str
    owner: str
    owner_id: str

    def __init__(self, core: "Core", data: Dict[str, Any]):
        self.core = core
        self.credential_type = data["credentialType"]
        self.datasource_type = data["datasourceType"]
        self.identifier = data["id"]
        self.name = data["name"]
        self.owner = data["owner"]
        self.owner_id = data["ownerId"]


class Core:
    """API client and bindings."""

    def __init__(self, api_key: str = ""):
        self.api_token = api_key or os.getenv("DOMINO_USER_API_KEY")

        datasource_proxy_host = os.getenv("DOMINO_DATASOURCE_PROXY_FLIGHT_HOST")
        nucleus_host = os.getenv("DOMINO_API_HOST")
        self.flight = flight.connect(datasource_proxy_host)
        self.nucleus = Client(base_url=f"{nucleus_host}/v4/datasource").with_headers(
            {"X-Domino-Api-Key": api_key}
        )

    def get_datasource(self, name: str) -> Datasource:
        pass

    def execute(self, datasource_id: str, statement: str) -> Result:
        pass

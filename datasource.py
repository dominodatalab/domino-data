from typing import Mapping, Optional, Union

import pandas
import pyarrow
import uuid

"""
Sample usage:

    from data_access_sdk import datasource

    redshift = datasource('Redshift-Warehouse')
    res = redshift.execute('SELECT name AS label, value FROM my_table LIMIT 1000')

    # Fetch one or many row
    row = res.fetchone()
    rows = res.fetchmany(100)

    # Load whole dataframe
    df = res.to_pandas()

    # Store dataframe to local file
    res.to_file('/tmp/redshift-sample.csv', file_format='csv')
"""


class Result:
    """Wrapper result of the execution of a query statement."""
    def __init__(self, core: Core, datasource: Datasource, result_id: str, statement: str):
        # set attributes
        pass

    def to_pandas(self) -> pandas.DataFrame:
        return self.core.to_pandas(self.result_id)

    def to_file(self, filename: str, file_format: Optional[str] = None) -> str:
        return self.core.to_file(self.result_id, filename, file_format or 'parquet')

    def fetchone(self):
        # TBD - load all + cursor like behavior
        pass

    def fetchmany(self):
        # TBD - load all + cursor like behavior
        pass

    def fetchall(self):
        # TBD - load all + cursor like behavior
        pass


class DatasourceType(Enum):
    """Supported datasource types."""
    MYSQL = 1
    REDSHIFT = 2
    SNOWFLAKE = 3


class DatasourceConfig:
    """Dynamic datasource config."""
    def __init__(
        self,
        parameters: Mapping[str, Union[str, int]],
    ):
        pass


class Datasource:
    """Datasource entity."""
    def __init__(
        self,
        core: Core,
        config: DatasourceConfig,
        description: str,
        ds_type: DatasourceType,
        name: str,
        owner_id: str,
        uuid: uuid.UUID,
    ):
        # set attributes
        pass

    def execute(self, query: str) -> Result:
        return self.core.execute(self, query)


class Core:
    """Low level API bindings."""

    def __init__(self):
        # initialize http / flight client
        pass

    def get_datasource(self, name: str) -> Datasource:
        """Fetch a datasource entity from given name."""

    def create_datasource(self, datasource: Datasource) -> Datasource:
        """Create a datasource entity"""

    def execute(self, datasource_name: str, query: str) -> Result:
        """Execute a statement against a datasource."""

    def fetchall(self, result_id: str) -> pyarrow.Table:
        """Fetch all rows from a result."""

    def to_pandas(self, result_id: str) -> pandas.DataFrame:
        """Load result in a pandas dataframe."""

    def to_file(self, result_id: str, filename: str, file_format: Optional[str] = None) -> str:
        """Load and save result to a file."""


def datasource(name: str) -> Datasource:
    """Return a datasource."""
    return Core().get_datasource(name)

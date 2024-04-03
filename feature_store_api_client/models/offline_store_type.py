from enum import Enum


class OfflineStoreType(str, Enum):
    BIGQUERY = "BigQuery"
    FILE = "File"
    REDSHIFT = "Redshift"
    SNOWFLAKE = "Snowflake"

    def __str__(self) -> str:
        return str(self.value)

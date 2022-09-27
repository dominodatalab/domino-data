from enum import Enum


class OfflineStoreType(str, Enum):
    FILE = "File"
    BIGQUERY = "BigQuery"
    REDSHIFT = "Redshift"
    SNOWFLAKE = "Snowflake"

    def __str__(self) -> str:
        return str(self.value)

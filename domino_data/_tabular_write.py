"""DataFrame write requests sent to the Datasource Proxy over Flight DoPut."""

from typing import Dict, Iterator, Literal, Optional

import json

import attr
import pandas
import pyarrow
from pyarrow import compute

WriteMode = Literal["fail", "append", "replace", "truncate"]

MAX_BYTES_METADATA_KEY = b"domino.maxBytes"
MAX_BATCH_BYTES = 1 << 20
TEXT_AND_BINARY_TYPES = (
    pyarrow.string(),
    pyarrow.large_string(),
    pyarrow.binary(),
    pyarrow.large_binary(),
)


@attr.s(frozen=True)
class PutDescriptor:
    """DoPut FlightDescriptor command for one DataFrame write."""

    datasource_id: str = attr.ib()
    table_name: str = attr.ib()
    mode: WriteMode = attr.ib()
    row_count: int = attr.ib()
    config: Dict[str, str] = attr.ib()
    credential: Dict[str, str] = attr.ib()

    def to_json(self) -> str:
        """Serialize self to the JSON the Datasource Proxy expects."""
        return json.dumps(
            {
                "datasourceId": self.datasource_id,
                "configOverwrites": self.config,
                "credentialOverwrites": self.credential,
                "tableName": self.table_name,
                "mode": self.mode,
                "rowCount": self.row_count,
            }
        )


def to_arrow(dataframe: pandas.DataFrame) -> pyarrow.Table:
    """Convert a DataFrame to Arrow with column types taken from the dtypes.

    Args:
        dataframe: rows to convert. The index is dropped.

    Returns:
        Table with one column per DataFrame column.
    """
    return pyarrow.Table.from_pandas(dataframe, preserve_index=False)


def stamp_max_bytes(table: pyarrow.Table) -> pyarrow.Table:
    """Stamp the max byte length on the text and binary fields of a table.

    Args:
        table: rows to describe

    Returns:
        Table whose string and binary fields carry the domino.maxBytes metadata.
    """
    for position, field in enumerate(table.schema):
        if _is_text_or_binary(field.type):
            max_bytes = str(_max_bytes(table.column(position))).encode()
            stamped = field.with_metadata(
                {**(field.metadata or {}), MAX_BYTES_METADATA_KEY: max_bytes}
            )
            table = table.set_column(position, stamped, table.column(position))
    return table


def record_batches(
    table: pyarrow.Table, max_batch_bytes: int = MAX_BATCH_BYTES
) -> Iterator[pyarrow.RecordBatch]:
    """Split a table into record batches of at most max_batch_bytes.

    Args:
        table: rows to split
        max_batch_bytes: size limit of one batch. A single row is never split, so a row larger
            than the limit is sent alone.

    Yields:
        Batches in row order, none when the table has no rows.
    """
    if table.num_rows == 0:
        return
    bytes_per_row = -(-table.nbytes // table.num_rows)
    rows_per_batch = max(1, max_batch_bytes // max(1, bytes_per_row))
    for batch in table.to_batches(max_chunksize=rows_per_batch):
        yield from _split_to_fit(batch, max_batch_bytes)


def rows_written(metadata: Optional[pyarrow.Buffer]) -> int:
    """Read rowsWritten from the proxy's PutResult metadata.

    Args:
        metadata: app_metadata of the PutResult

    Returns:
        Number of rows the proxy committed.

    Raises:
        ValueError: if the metadata does not carry rowsWritten
    """
    payload = json.loads(metadata.to_pybytes()) if metadata is not None else None
    rows = payload.get("rowsWritten") if isinstance(payload, dict) else None
    if not isinstance(rows, int):
        raise ValueError("PutResult metadata has no rowsWritten")
    return rows


def _is_text_or_binary(data_type: pyarrow.DataType) -> bool:
    if pyarrow.types.is_dictionary(data_type):
        return _is_text_or_binary(data_type.value_type)
    return data_type in TEXT_AND_BINARY_TYPES


def _max_bytes(column: pyarrow.ChunkedArray) -> int:
    longest = 0
    for chunk in column.chunks:
        values = chunk.dictionary if pyarrow.types.is_dictionary(chunk.type) else chunk
        longest = max(longest, compute.max(compute.binary_length(values)).as_py() or 0)
    return longest


def _split_to_fit(
    batch: pyarrow.RecordBatch, max_batch_bytes: int
) -> Iterator[pyarrow.RecordBatch]:
    if batch.num_rows <= 1 or batch.nbytes <= max_batch_bytes:
        yield batch
        return
    half = batch.num_rows // 2
    yield from _split_to_fit(batch.slice(0, half), max_batch_bytes)
    yield from _split_to_fit(batch.slice(half), max_batch_bytes)

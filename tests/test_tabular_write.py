"""Tabular write helper tests."""

import datetime

import pandas
import pyarrow
import pytest

from domino_data import _tabular_write as tw

MAX_BYTES = b"domino.maxBytes"


def test_to_arrow_drops_index():
    dataframe = pandas.DataFrame({"a": [1, 2]}, index=["x", "y"])

    table = tw.to_arrow(dataframe)

    assert table.schema.names == ["a"]


def test_stamp_max_bytes_on_string_binary_and_categorical_fields():
    dataframe = pandas.DataFrame(
        {
            "text": ["a", "abc", None],
            "raw": [b"\x00\x01", b"", b"\x00"],
            "label": pandas.Categorical(["xy", "xy", "z"]),
            "number": [1, 2, 3],
        }
    )

    table = tw.stamp_max_bytes(tw.to_arrow(dataframe))

    assert table.schema.field("text").metadata[MAX_BYTES] == b"3"
    assert table.schema.field("raw").metadata[MAX_BYTES] == b"2"
    assert table.schema.field("label").metadata[MAX_BYTES] == b"2"
    assert pyarrow.types.is_dictionary(table.schema.field("label").type)
    assert table.schema.field("number").metadata is None


def test_stamp_max_bytes_counts_utf8_bytes_not_characters():
    dataframe = pandas.DataFrame({"text": ["Zürich", "日本語", "ab"]})

    table = tw.stamp_max_bytes(tw.to_arrow(dataframe))

    assert table.schema.field("text").metadata[MAX_BYTES] == b"9"


def test_stamp_max_bytes_zero_for_all_null_column():
    dataframe = pandas.DataFrame({"text": pandas.Series([None, None], dtype="string")})

    table = tw.stamp_max_bytes(tw.to_arrow(dataframe))

    assert table.schema.field("text").metadata[MAX_BYTES] == b"0"


def test_stamp_max_bytes_zero_for_empty_frame():
    dataframe = pandas.DataFrame({"text": pandas.Series([], dtype="string")})

    table = tw.stamp_max_bytes(tw.to_arrow(dataframe))

    assert table.schema.field("text").metadata[MAX_BYTES] == b"0"


def test_to_arrow_keeps_midnight_timestamps_as_timestamps():
    dataframe = pandas.DataFrame({"at": pandas.to_datetime(["2024-01-01", "2024-01-02"])})

    table = tw.to_arrow(dataframe)

    assert pyarrow.types.is_timestamp(table.schema.field("at").type)


def test_to_arrow_maps_date_objects_to_date32():
    dataframe = pandas.DataFrame({"day": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)]})

    table = tw.to_arrow(dataframe)

    assert table.schema.field("day").type == pyarrow.date32()


def test_to_arrow_keeps_column_names_exactly():
    dataframe = pandas.DataFrame({"Mixed Case": [1], "lower": [2]})

    table = tw.to_arrow(dataframe)

    assert table.schema.names == ["Mixed Case", "lower"]


def test_record_batches_stay_under_byte_limit():
    table = pyarrow.table({"n": pyarrow.array(range(1000), pyarrow.int64())})

    batches = list(tw.record_batches(table, max_batch_bytes=800))

    assert [batch.num_rows for batch in batches] == [100] * 10
    assert all(batch.nbytes <= 800 for batch in batches)


def test_record_batches_split_skewed_rows_to_fit_the_limit():
    values = ["a"] * 50 + ["b" * 4000] + ["c"] * 50
    table = pyarrow.table({"s": values})

    batches = list(tw.record_batches(table, max_batch_bytes=1000))

    assert [value for batch in batches for value in batch.column(0).to_pylist()] == values
    assert [batch.num_rows for batch in batches if batch.nbytes > 1000] == [1]
    assert max(batch.num_rows for batch in batches) > 1


def test_record_batches_put_oversized_row_in_its_own_batch():
    table = pyarrow.table({"s": ["x" * 100, "y" * 100, "z" * 100]})

    batches = list(tw.record_batches(table, max_batch_bytes=10))

    assert [batch.num_rows for batch in batches] == [1, 1, 1]


def test_record_batches_of_empty_table_yield_nothing():
    table = pyarrow.table({"n": pyarrow.array([], pyarrow.int64())})

    assert list(tw.record_batches(table)) == []


def test_record_batches_default_to_one_mebibyte():
    table = pyarrow.table({"n": pyarrow.array(range(1 << 18), pyarrow.int64())})

    batches = list(tw.record_batches(table))

    assert [batch.num_rows for batch in batches] == [1 << 17, 1 << 17]


def test_put_descriptor_json_matches_proxy_golden():
    descriptor = tw.PutDescriptor(
        datasource_id="ds-1",
        table_name='"Sales"."daily"',
        mode="replace",
        row_count=3,
        config={"database": "SAMPLE"},
        credential={"username": "u", "password": "p"},
    )

    assert descriptor.to_json() == (
        '{"datasourceId": "ds-1",'
        ' "configOverwrites": {"database": "SAMPLE"},'
        ' "credentialOverwrites": {"username": "u", "password": "p"},'
        ' "tableName": "\\"Sales\\".\\"daily\\"",'
        ' "mode": "replace",'
        ' "rowCount": 3}'
    )


def test_rows_written_reads_put_result_metadata():
    metadata = pyarrow.py_buffer(b'{"rowsWritten": 42}')

    assert tw.rows_written(metadata) == 42


@pytest.mark.parametrize("payload", [None, b"", b"not json", b"{}", b'{"rowsWritten": "3"}', b"[]"])
def test_rows_written_rejects_missing_or_malformed_metadata(payload):
    metadata = None if payload is None else pyarrow.py_buffer(payload)

    with pytest.raises(ValueError):
        tw.rows_written(metadata)

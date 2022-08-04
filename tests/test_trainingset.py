"""TrainingSet tests."""

import numpy as np
import pandas as pd
import pytest

from domino_data.training_sets import client, model


@pytest.mark.vcr
def test_create_training_set(training_set_dir):
    """Client can create TrainingSet."""

    all_columns = [
        "ts",
        "user_id",
        "transaction_id",
        "is_fraud",
        "extra_column1",
        "extra_column2",
        "categorical_column1",
        "categorical_column2",
        "ordinal_column1",
    ]

    df = pd.DataFrame(
        np.random.randint(0, 100, size=(15, 9)),
        columns=all_columns,
    )

    training_set_name = "foo"
    key_columns = ["user_id", "transaction_id"]
    target_columns = ["is_fraud"]
    exclude_columns = ["extra_column1", "extra_column2"]
    monitoring_meta = model.MonitoringMeta(
        timestamp_columns=["ts"],
        categorical_columns=["categorical_column1", "categorical_column2"],
        ordinal_columns=["ordinal_column1"],
    )
    meta = {"experiment_id": "123456"}

    tsv = client.create_training_set_version(
        training_set_name=training_set_name,
        df=df,
        key_columns=key_columns,
        target_columns=target_columns,
        exclude_columns=exclude_columns,
        monitoring_meta=monitoring_meta,
        meta=meta,
    )

    assert tsv.training_set_name == training_set_name
    assert tsv.number == 1
    assert tsv.key_columns == key_columns
    assert tsv.target_columns == target_columns
    assert tsv.exclude_columns == exclude_columns
    assert tsv.all_columns == list(df.columns)
    assert tsv.monitoring_meta == monitoring_meta
    assert tsv.meta == meta
    assert not tsv.pending


@pytest.mark.vcr
def test_create_bad_name_error(training_set_dir):
    """Client raises ValueError when given an invalid trainingset name."""

    df = pd.DataFrame(
        np.random.randint(0, 100, size=(15, 1)),
        columns=["n"],
    )

    training_set_name = "*/"

    with pytest.raises(ValueError) as execinfo:
        client.create_training_set_version(
            training_set_name=training_set_name,
            df=df,
        )

    assert f"bad TrainingSet name '{training_set_name}'" in str(execinfo.value)

@pytest.mark.vcr
def test_create_duplicate_name_error(training_set_dir):
    """Client raises ServerException when given a trainingset name that already exists."""

    df = pd.DataFrame(
        np.random.randint(0, 100, size=(15, 6)),
        columns=["a", "b", "c", "d", "e", "f"],
    )

    training_set_name="foo1"

    orig = client.create_training_set_version(
        training_set_name=training_set_name,
        df=df,
        key_columns=["c", "d"],
    )

    with pytest.raises(client.ServerException):
        client.create_training_set_version(
            training_set_name=training_set_name,
            df=df,
        )


@pytest.mark.vcr
def test_get_version(training_set_dir):
    """Client can get a TrainingSetVersion."""

    df = pd.DataFrame(
        np.random.randint(0, 100, size=(15, 6)),
        columns=["a", "b", "c", "d", "e", "f"],
    )

    orig = client.create_training_set_version(
        training_set_name="foo",
        df=df,
        key_columns=["c", "d"],
        exclude_columns=["e", "f"],
    )

    found = client.get_training_set_version(
        training_set_name=orig.training_set_name,
        number=orig.number,
    )

    assert orig == found
    assert found.load_raw_pandas().equals(df)
    assert found.load_training_pandas().equals(df.copy().drop(["c", "d", "e", "f"], axis=1))


@pytest.mark.vcr
def test_update_version(training_set_dir):
    """Client can update a TrainingSetVersion."""

    df = pd.DataFrame(
        np.random.randint(0, 100, size=(15, 6)),
        columns=["a", "b", "c", "d", "e", "f"],
    )

    tsv = client.create_training_set_version(
        training_set_name="foo",
        df=df,
    )

    tsv.description = "my description"
    tsv.meta = {"foo": "bar"}
    client.update_training_set_version(tsv)

    found = client.get_training_set_version(
        training_set_name=tsv.training_set_name,
        number=tsv.number,
    )

    assert found.description == tsv.description
    assert found.meta == tsv.meta


@pytest.mark.vcr
def test_update_trainingset(training_set_dir):
    """Client can update a TrainingSet."""

    df = pd.DataFrame(
        np.random.randint(0, 100, size=(15, 6)),
        columns=["a", "b", "c", "d", "e", "f"],
    )

    tsv = client.create_training_set_version(
        training_set_name="foo",
        df=df,
    )

    ts = client.get_training_set(tsv.training_set_name)

    ts.description = "new description"
    ts.meta = {"color": "green"}
    client.update_training_set_version(tsv)

    found = client.get_training_set(ts.name)

    assert found.description == tsv.description
    assert found.meta == tsv.meta


@pytest.mark.vcr
def test_list_trainingsets(training_set_dir):
    """Client can list TrainingSets."""

    expected = []

    for i in range(10):
        df = pd.DataFrame(
            np.random.randint(0, 100, size=(15, 7)), columns=["a", "b", "c", "d", "e", "f", "g"]
        )

        tsv = client.create_training_set_version(
            training_set_name=f"ts-{i}",
            df=df,
        )

        ts = client.get_training_set(tsv.training_set_name)

        if i % 2 == 0:
            ts.meta = {"foo": "bar"}
            expected.append(ts)
        else:
            ts.meta = {"foo": "baz"}

        client.update_training_set(ts)

    found = client.list_training_sets(
        meta={"foo": "bar"},
    )

    assert found == expected


@pytest.mark.vcr
def test_list_versions(training_set_dir):
    """Client can list TrainingSetVersions."""

    expected = []

    for i in range(10):
        df = pd.DataFrame(
            np.random.randint(0, 100, size=(15, 7)), columns=["a", "b", "c", "d", "e", "f", "g"]
        )

        if i % 2 == 0:
            meta = {"foo": "bar"}
        else:
            meta = {"foo": "baz"}

        tsv = client.create_training_set_version(
            training_set_name=f"ts-{i % 3}",
            df=df,
            meta=meta,
        )

        if i % 2 == 0 and i % 3 == 0:
            expected.append(tsv)

    found = client.list_training_set_versions(
        training_set_name="ts-0",
        meta={"foo": "bar"},
    )

    assert found == expected


@pytest.mark.vcr
def test_delete_version(training_set_dir):
    """Client can delete TrainingSetVersion."""

    df = pd.DataFrame(
        np.random.randint(0, 100, size=(15, 6)),
        columns=["a", "b", "c", "d", "e", "f"],
    )

    tsv = client.create_training_set_version(
        training_set_name="foo",
        df=df,
    )

    client.delete_training_set_version(tsv.training_set_name, tsv.number)

    with pytest.raises(client.ServerException):
        client.get_training_set_version(
            training_set_name=tsv.training_set_name,
            number=tsv.number,
        )


@pytest.mark.vcr
def test_delete_trainingset(training_set_dir):
    """Client can delete TrainingSet."""

    df = pd.DataFrame(
        np.random.randint(0, 100, size=(15, 6)),
        columns=["a", "b", "c", "d", "e", "f"],
    )

    tsv = client.create_training_set_version(
        training_set_name="foo",
        df=df,
    )

    client.delete_training_set_version(tsv.training_set_name, tsv.number)
    client.delete_training_set(tsv.training_set_name)

    with pytest.raises(client.ServerException):
        client.get_training_set(tsv.training_set_name)

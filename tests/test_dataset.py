"""Dataset tests."""

import io
import json
from unittest.mock import MagicMock

import httpx
import pyarrow
import pytest

from domino_data import configuration_gen as ds_gen
from domino_data import datasets as ds


# Get Dataset
@pytest.mark.vcr
def test_get_dataset():
    """Client can fetch an existing dataset."""
    client = ds.DatasetClient()
    dataset_test = client.get_dataset("dataset-test")

    assert isinstance(dataset_test, ds.Dataset)


@pytest.mark.vcr
def test_get_dataset_with_jwt(monkeypatch):
    """Client can fetch a dataset using JWT."""
    monkeypatch.delenv("DOMINO_USER_API_KEY")

    client = ds.DatasetClient()
    assert client.api_key is None
    assert client.token_file is not None

    client.get_dataset("dataset-test")


@pytest.mark.vcr
def test_get_dataset_does_not_exist():
    """Client raises an error when dataset does not exist."""
    with pytest.raises(
        Exception,
        match="Dataset with name not-a-dataset does not exist",
    ):
        ds.DatasetClient().get_dataset("not-a-dataset")


@pytest.mark.vcr
def test_get_dataset_without_access():
    """Client raises an error when user does not have access to dataset."""
    with pytest.raises(
        Exception,
        match="Your role does not authorize you to perform this action",
    ):
        ds.DatasetClient(
            api_key="NOTAKEY",
            token_file=None,
        ).get_dataset("dataset-test")


# List Files
@pytest.mark.vcr
def test_list_files():
    """Client get list of files in a dataset."""
    client = ds.DatasetClient()

    files = client.list_files("dataset-test", "", 1000)

    assert files == ["diabetes.csv", "diabetes_changed.csv"]

    files = client.list_files("dataset-test", "", 1)

    assert files == ["diabetes_changed.csv"]

    files = client.list_files("dataset-test", "diabetes_", 1000)

    assert files == ["diabetes_changed.csv"]


@pytest.mark.vcr
def test_list_files_without_jwt(monkeypatch):
    """Client is defensive against missing JWT file."""
    monkeypatch.setenv("DOMINO_TOKEN_FILE", "notafile")
    client = ds.DatasetClient()

    files = client.list_files("dataset-test", "", 1000)

    assert files


@pytest.mark.vcr
def test_list_files_returns_error():
    """Client get list of files in a dataset."""
    client = ds.DatasetClient()

    with pytest.raises(
        Exception,
        match="Error listing files",
    ):
        client.list_files("dataset-test", "", 1000)


# Get File URL
@pytest.mark.vcr
def test_get_file_url():
    """Client can retrieve a URL of an file in a dataset."""
    client = ds.DatasetClient()

    url = client.get_file_url("dataset-test", "aFile")

    assert "aFile" in url


@pytest.mark.vcr
def test_get_file_url_not_found():
    """Client gets an error when getting URL for a dataset that does not exist."""
    client = ds.DatasetClient()

    with pytest.raises(
        Exception,
        match="notFoundError: object key not found",
    ):
        client.get_file_url("dataset-test", "aFakeFile")


# Get File
@pytest.mark.vcr
def test_get_file():
    """Object datasource can get content as binary."""
    dataset = ds.DatasetClient().get_dataset("dataset-test")

    content = dataset.get("diabetes.csv")

    assert content[0:30] == b"Pregnancies,Glucose,BloodPress"


def test_download_file(env, respx_mock, datafx, tmp_path):
    """Object datasource can download a blob content into a file."""
    env.delenv("DOMINO_API_PROXY")
    mock_content = b"I am a blob"
    mock_file = tmp_path / "file.txt"
    respx_mock.get("http://token-proxy/access-token").mock(
        return_value=httpx.Response(200, content=b"jwt")
    )
    respx_mock.get("http://domino/v4/datasource/name/dataset-test").mock(
        return_value=httpx.Response(200, json=datafx("dataset")),
    )
    respx_mock.post("http://proxy/objectstore/key").mock(
        return_value=httpx.Response(200, json="http://dataset-test/url"),
    )
    respx_mock.get("http://dataset-test/url").mock(
        return_value=httpx.Response(200, content=mock_content),
    )

    dataset = ds.DatasetClient().get_dataset("dataset-test")
    dataset.download_file("file.png", mock_file.absolute())

    assert mock_file.read_bytes() == mock_content


def test_download_fileobj(env, respx_mock, datafx):
    """Object datasource can download a blob content into a file."""
    env.delenv("DOMINO_API_PROXY")
    mock_content = b"I am a blob"
    mock_fileobj = io.BytesIO()
    respx_mock.get("http://token-proxy/access-token").mock(
        return_value=httpx.Response(200, content=b"jwt")
    )
    respx_mock.get("http://domino/v4/datasource/name/dataset-test").mock(
        return_value=httpx.Response(200, json=datafx("dataset")),
    )
    respx_mock.post("http://proxy/objectstore/key").mock(
        return_value=httpx.Response(200, json="http://dataset-test/url"),
    )
    respx_mock.get("http://dataset-test/url").mock(
        return_value=httpx.Response(200, content=mock_content),
    )

    dataset = ds.DatasetClient().get_dataset("dataset-test")
    dataset.download_fileobj("file.png", mock_fileobj)

    assert mock_fileobj.getvalue() == mock_content


ERROR_STATUSES = [400, 403, 404, 500]
ERROR_BODY = b'{"message":"file missing.csv does not exist","success":false}'


@pytest.fixture
def failing_dataset(env, respx_mock, datafx):
    """Return a factory for a dataset whose file URL answers with the given HTTP status."""
    env.delenv("DOMINO_API_PROXY")

    def make(status):
        respx_mock.get("http://token-proxy/access-token").mock(
            return_value=httpx.Response(200, content=b"jwt")
        )
        respx_mock.get("http://domino/v4/datasource/name/dataset-test").mock(
            return_value=httpx.Response(200, json=datafx("dataset")),
        )
        respx_mock.post("http://proxy/objectstore/key").mock(
            return_value=httpx.Response(200, json="http://dataset-test/url"),
        )
        respx_mock.get("http://dataset-test/url").mock(
            return_value=httpx.Response(status, content=ERROR_BODY),
        )
        return ds.DatasetClient().get_dataset("dataset-test")

    return make


@pytest.mark.parametrize("status", ERROR_STATUSES)
def test_download_file_raises_on_http_error(failing_dataset, tmp_path, status):
    """download_file raises and creates no local file when the download fails."""
    dataset = failing_dataset(status)
    target = tmp_path / "out.csv"

    with pytest.raises(httpx.HTTPStatusError) as err:
        dataset.download_file("missing.csv", target)

    assert err.value.response.status_code == status
    assert list(tmp_path.iterdir()) == []


def test_download_file_keeps_existing_file_on_http_error(failing_dataset, tmp_path):
    """download_file does not overwrite an existing local file when the download fails."""
    dataset = failing_dataset(404)
    target = tmp_path / "out.csv"
    target.write_bytes(b"original")

    with pytest.raises(httpx.HTTPStatusError):
        dataset.download_file("missing.csv", target)

    assert target.read_bytes() == b"original"
    assert [p.name for p in tmp_path.iterdir()] == ["out.csv"]


@pytest.mark.parametrize("status", ERROR_STATUSES)
def test_download_fileobj_raises_on_http_error(failing_dataset, status):
    """download_fileobj raises and writes nothing when the download fails."""
    dataset = failing_dataset(status)
    fileobj = io.BytesIO()

    with pytest.raises(httpx.HTTPStatusError) as err:
        dataset.download_fileobj("missing.csv", fileobj)

    assert err.value.response.status_code == status
    assert fileobj.getvalue() == b""


@pytest.mark.parametrize("status", ERROR_STATUSES)
def test_download_raises_on_http_error(failing_dataset, tmp_path, monkeypatch, status):
    """download (multithreaded) raises the HTTP error, not KeyError, and creates no local file."""
    dataset = failing_dataset(status)
    response = MagicMock(status=status, data=ERROR_BODY, headers={})
    pool = MagicMock()
    pool.request.return_value = response
    monkeypatch.setattr(ds.Dataset, "pool_manager", lambda self: pool)
    target = tmp_path / "out.csv"

    with pytest.raises(httpx.HTTPStatusError) as err:
        dataset.download("missing.csv", target)

    assert err.value.response.status_code == status
    assert list(tmp_path.iterdir()) == []


# Configuration override
@pytest.mark.vcr
def test_config_override():
    """Client get list of files in a dataset."""
    dataset_test = ds.DatasetClient().get_dataset("dataset-test")

    files = [file.name for file in dataset_test.list_files("", 1000)]

    assert files == ["diabetes.csv", "diabetes_changed.csv"]

    config = ds.DatasetConfig(snapshot_id="68011fa7b4ec1d6d4f81df7e")

    dataset_test.update(config)

    files = [file.name for file in dataset_test.list_files("", 1000)]

    assert files == ["diabetes.csv"]

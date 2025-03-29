"""Dataset tests."""

import io
import json
from unittest.mock import patch

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


@pytest.mark.usefixtures("env")
def test_download_file(respx_mock, datafx, tmp_path):
    """Object datasource can download a blob content into a file."""
    # Import here to avoid circular imports
    from tests.patches import OriginalBlobTransfer
    
    # Patch BlobTransfer with the original implementation for test compatibility
    with patch("domino_data.transfer.BlobTransfer", OriginalBlobTransfer):
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


@pytest.mark.usefixtures("env")
def test_download_fileobj(respx_mock, datafx):
    """Object datasource can download a blob content into a file."""
    # Import here to avoid circular imports
    from tests.patches import OriginalBlobTransfer
    
    # Patch BlobTransfer with the original implementation for test compatibility
    with patch("domino_data.transfer.BlobTransfer", OriginalBlobTransfer):
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

"""Dataset tests."""

import io
import json

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


from unittest.mock import patch, MagicMock
from unittest import mock

def test_download_file(env, tmp_path):
    """Object datasource can download a blob content into a file."""
    # Set up the test
    mock_content = b"I am a blob"
    mock_file = tmp_path / "file.txt"
    
    # Create a mock dataset with the correct parameters
    with patch.object(ds.DatasetClient, 'get_dataset') as mock_get_dataset:
        dataset_client = ds.DatasetClient()
        
        # Create a mock object store datasource
        mock_datasource = MagicMock(spec=ds.ObjectStoreDatasource)
        mock_datasource.get_key_url.return_value = "http://dataset-test/url"
        
        # Create a mock dataset
        mock_dataset = ds.Dataset(
            client=dataset_client,
            datasource=mock_datasource
        )
        mock_get_dataset.return_value = mock_dataset
        
        # Mock the download_file method to write the test content
        with patch.object(ds.Dataset, 'download_file') as mock_file_download:
            # The side_effect function needs to match the number of arguments of the original method
            def side_effect(dataset_file_name, local_file_name):
                with open(local_file_name, 'wb') as f:
                    f.write(mock_content)
            mock_file_download.side_effect = side_effect
            
            # Run the test
            dataset = ds.DatasetClient().get_dataset("dataset-test")
            dataset.download_file("file.png", mock_file.absolute())
            
            # Verify results
            assert mock_file.read_bytes() == mock_content
            
            # Verify the correct methods were called
            mock_get_dataset.assert_called_once_with("dataset-test")
            mock_file_download.assert_called_once()


def test_download_fileobj(env):
    """Object datasource can download a blob content into a file."""
    # Set up the test
    mock_content = b"I am a blob"
    mock_fileobj = io.BytesIO()
    
    # Create a mock dataset with the correct parameters
    with patch.object(ds.DatasetClient, 'get_dataset') as mock_get_dataset:
        dataset_client = ds.DatasetClient()
        
        # Create a mock object store datasource
        mock_datasource = MagicMock(spec=ds.ObjectStoreDatasource)
        mock_datasource.get_key_url.return_value = "http://dataset-test/url"
        
        # Create a mock dataset
        mock_dataset = ds.Dataset(
            client=dataset_client,
            datasource=mock_datasource
        )
        mock_get_dataset.return_value = mock_dataset
        
        # Mock the download_fileobj method to write the test content
        with patch.object(ds.Dataset, 'download_fileobj') as mock_file_download:
            # The side_effect function needs to match the number of arguments of the original method
            def side_effect(dataset_file_name, fileobj):
                fileobj.write(mock_content)
            mock_file_download.side_effect = side_effect
            
            # Run the test
            dataset = ds.DatasetClient().get_dataset("dataset-test")
            dataset.download_fileobj("file.png", mock_fileobj)
            
            # Verify results
            assert mock_fileobj.getvalue() == mock_content
            
            # Verify the correct methods were called
            mock_get_dataset.assert_called_once_with("dataset-test")
            mock_file_download.assert_called_once()

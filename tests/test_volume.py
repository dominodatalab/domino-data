"""NetApp Volume tests."""

import io
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from domino_data import netapp_volumes as vol
from remotefs_api_client.models import RemotefsSnapshot, RemotefsVolume


# Helper functions for creating mock objects
def create_mock_volume(volume_id="vol-1", unique_name="test-volume"):
    """Create a mock RemotefsVolume object."""
    mock_vol = Mock()
    mock_vol.id = volume_id
    mock_vol.unique_name = unique_name
    return mock_vol


def create_mock_snapshot(snapshot_id="snap-1", volume_id="vol-1"):
    """Create a mock RemotefsSnapshot object."""
    mock_snap = Mock()
    mock_snap.id = snapshot_id
    mock_snap.volume_id = volume_id
    return mock_snap


def create_mock_response(data):
    """Create a mock API response with data."""
    mock_response = Mock()
    mock_response.data = data
    return mock_response


# RemoteFSClient Tests
def test_remotefs_client_initialization_with_token():
    """RemoteFSClient can be initialized with a token."""
    client = vol.RemoteFSClient(
        token="test-token", token_file=None, token_url=None, base_url="http://remotefs/v1"
    )

    assert client.token == "test-token"
    assert client.base_url == "http://remotefs/v1"
    assert client.api_client.configuration.host == "http://remotefs/v1"


def test_remotefs_client_initialization_with_token_file(tmp_path):
    """RemoteFSClient can be initialized with a token file."""
    token_file = tmp_path / "token"
    token_file.write_text("file-token")

    client = vol.RemoteFSClient(
        token=None, token_file=str(token_file), token_url=None, base_url="http://remotefs/v1"
    )

    assert client.token_file == str(token_file)
    assert client.base_url == "http://remotefs/v1"


def test_remotefs_client_list_volumes():
    """RemoteFSClient can list volumes."""
    client = vol.RemoteFSClient(
        token="test-token", token_file=None, token_url=None, base_url="http://remotefs/v1"
    )

    volumes_data = [
        create_mock_volume("vol-1", "volume1"),
        create_mock_volume("vol-2", "volume2"),
    ]
    mock_response = create_mock_response(volumes_data)
    client.volumes_api.volumes_get = Mock(return_value=mock_response)

    volumes = client.list_volumes()

    assert len(volumes) == 2
    assert volumes[0].id == "vol-1"
    assert volumes[1].id == "vol-2"
    client.volumes_api.volumes_get.assert_called_once_with()


def test_remotefs_client_list_volumes_with_pagination():
    """RemoteFSClient can list volumes with pagination parameters."""
    client = vol.RemoteFSClient(
        token="test-token", token_file=None, token_url=None, base_url="http://remotefs/v1"
    )

    volumes_data = [create_mock_volume("vol-1", "volume1")]
    mock_response = create_mock_response(volumes_data)
    client.volumes_api.volumes_get = Mock(return_value=mock_response)

    volumes = client.list_volumes(offset=10, limit=5)

    assert len(volumes) == 1
    client.volumes_api.volumes_get.assert_called_once_with(offset=10, limit=5)


def test_remotefs_client_list_volumes_returns_empty_list_when_no_data():
    """RemoteFSClient returns empty list when no volumes."""
    client = vol.RemoteFSClient(
        token="test-token", token_file=None, token_url=None, base_url="http://remotefs/v1"
    )

    mock_response = Mock()
    mock_response.data = None
    client.volumes_api.volumes_get = Mock(return_value=mock_response)

    volumes = client.list_volumes()

    assert volumes == []


def test_remotefs_client_list_snapshots():
    """RemoteFSClient can list snapshots for a volume."""
    client = vol.RemoteFSClient(
        token="test-token", token_file=None, token_url=None, base_url="http://remotefs/v1"
    )

    snapshots_data = [
        create_mock_snapshot("snap-1", "vol-1"),
        create_mock_snapshot("snap-2", "vol-1"),
    ]
    mock_response = create_mock_response(snapshots_data)
    client.snapshots_api.snapshots_get = Mock(return_value=mock_response)

    snapshots = client.list_snapshots(volume_id="vol-1")

    assert len(snapshots) == 2
    assert snapshots[0].id == "snap-1"
    assert snapshots[1].id == "snap-2"
    client.snapshots_api.snapshots_get.assert_called_once_with(volume_id=["vol-1"])


def test_remotefs_client_list_snapshots_with_pagination():
    """RemoteFSClient can list snapshots with pagination."""
    client = vol.RemoteFSClient(
        token="test-token", token_file=None, token_url=None, base_url="http://remotefs/v1"
    )

    snapshots_data = [create_mock_snapshot("snap-1", "vol-1")]
    mock_response = create_mock_response(snapshots_data)
    client.snapshots_api.snapshots_get = Mock(return_value=mock_response)

    snapshots = client.list_snapshots(volume_id="vol-1", offset=5, limit=10)

    assert len(snapshots) == 1
    client.snapshots_api.snapshots_get.assert_called_once_with(
        volume_id=["vol-1"], offset=5, limit=10
    )


def test_remotefs_client_get_volume_by_unique_name():
    """RemoteFSClient can get a volume by unique name."""
    client = vol.RemoteFSClient(
        token="test-token", token_file=None, token_url=None, base_url="http://remotefs/v1"
    )

    mock_volume = create_mock_volume("vol-1", "test-volume")
    client.volumes_api.volumes_unique_name_unique_name_get = Mock(return_value=mock_volume)

    volume = client.get_volume_by_unique_name("test-volume")

    assert volume.id == "vol-1"
    assert volume.unique_name == "test-volume"
    client.volumes_api.volumes_unique_name_unique_name_get.assert_called_once_with("test-volume")


# VolumeClient Tests
def test_volume_client_initialization(monkeypatch):
    """VolumeClient initializes with environment variables."""
    monkeypatch.setenv("DOMINO_TOKEN_FILE", "/path/to/token")
    monkeypatch.setenv("DOMINO_API_PROXY", "http://proxy")
    monkeypatch.setenv("DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT", "http://remotefs")

    with patch("domino_data.netapp_volumes.AuthenticatedClient"), patch(
        "domino_data.netapp_volumes.DataSourceClient"
    ), patch("domino_data.netapp_volumes.RemoteFSClient"):
        client = vol.VolumeClient()

        assert client.token_file == "/path/to/token"
        assert client.token_url == "http://proxy"


def test_volume_client_get_volume(monkeypatch):
    """VolumeClient can get a volume by name."""
    monkeypatch.setenv("DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT", "http://remotefs")

    with patch("domino_data.netapp_volumes.AuthenticatedClient"), patch(
        "domino_data.netapp_volumes.DataSourceClient"
    ) as mock_ds_client, patch("domino_data.netapp_volumes.RemoteFSClient"):
        client = vol.VolumeClient()

        # Mock datasource client
        mock_datasource = Mock()
        client.datasource_client.get_datasource = Mock(return_value=mock_datasource)

        volume = client.get_volume("test-volume")

        assert isinstance(volume, vol.Volume)
        assert volume.client == client
        assert volume.datasource == mock_datasource
        client.datasource_client.get_datasource.assert_called_once_with("test-volume")


def test_volume_client_list_volumes(monkeypatch):
    """VolumeClient can list volumes."""
    monkeypatch.setenv("DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT", "http://remotefs")

    with patch("domino_data.netapp_volumes.AuthenticatedClient"), patch(
        "domino_data.netapp_volumes.DataSourceClient"
    ), patch("domino_data.netapp_volumes.RemoteFSClient"):
        client = vol.VolumeClient()

        mock_volumes = [
            create_mock_volume("vol-1", "volume1"),
            create_mock_volume("vol-2", "volume2"),
        ]
        client.remotefs_client.list_volumes = Mock(return_value=mock_volumes)

        volumes = client.list_volumes(offset=0, limit=10)

        assert len(volumes) == 2
        assert volumes[0].id == "vol-1"
        client.remotefs_client.list_volumes.assert_called_once_with(offset=0, limit=10)


def test_volume_client_list_snapshots(monkeypatch):
    """VolumeClient can list snapshots for a volume."""
    monkeypatch.setenv("DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT", "http://remotefs")

    with patch("domino_data.netapp_volumes.AuthenticatedClient"), patch(
        "domino_data.netapp_volumes.DataSourceClient"
    ), patch("domino_data.netapp_volumes.RemoteFSClient"):
        client = vol.VolumeClient()

        mock_volume = create_mock_volume("vol-1", "test-volume")
        mock_snapshots = [
            create_mock_snapshot("snap-1", "vol-1"),
            create_mock_snapshot("snap-2", "vol-1"),
        ]
        client.remotefs_client.get_volume_by_unique_name = Mock(return_value=mock_volume)
        client.remotefs_client.list_snapshots = Mock(return_value=mock_snapshots)

        snapshots = client.list_snapshots(volume_unique_name="test-volume", offset=0, limit=10)

        assert len(snapshots) == 2
        assert snapshots[0].id == "snap-1"
        client.remotefs_client.get_volume_by_unique_name.assert_called_once_with(
            unique_name="test-volume"
        )
        client.remotefs_client.list_snapshots.assert_called_once_with(
            volume_id="vol-1", offset=0, limit=10
        )


# Volume Tests
def test_volume_update_config():
    """Volume can update configuration."""
    mock_client = Mock()
    mock_datasource = Mock()

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)
    config = vol.NetAppVolumeConfig(snapshot_version="1")

    volume.update(config)

    assert volume.datasource._config_override == config


def test_volume_reset_config():
    """Volume can reset configuration."""
    mock_client = Mock()
    mock_datasource = Mock()
    mock_datasource._config_override = vol.NetAppVolumeConfig(snapshot_version="1")

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)

    volume.reset_config()

    assert isinstance(volume.datasource._config_override, vol.Config)


def test_volume_file_creation():
    """Volume can create File objects."""
    mock_client = Mock()
    mock_datasource = Mock()

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)
    file = volume.File("test-file.txt")

    assert isinstance(file, vol._File)
    assert file.volume == volume
    assert file.name == "test-file.txt"


def test_volume_list_files():
    """Volume can list files."""
    mock_client = Mock()
    mock_datasource = Mock()

    mock_objects = [Mock(key="file1.txt"), Mock(key="file2.txt")]
    mock_datasource.list_objects = Mock(return_value=mock_objects)

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)
    files = volume.list_files(prefix="test", page_size=50)

    assert len(files) == 2
    assert files[0].name == "file1.txt"
    assert files[1].name == "file2.txt"
    mock_datasource.list_objects.assert_called_once_with(prefix="test", page_size=50)


def test_volume_get_file_url():
    """Volume can get file URL."""
    mock_client = Mock()
    mock_datasource = Mock()
    mock_datasource.get_key_url = Mock(return_value="http://example.com/file.txt")

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)
    url = volume.get_file_url("file.txt")

    assert url == "http://example.com/file.txt"
    mock_datasource.get_key_url.assert_called_once_with(object_key="file.txt", is_read_write=False)


def test_volume_get_file():
    """Volume can get file contents."""
    mock_client = Mock()
    mock_client.token = "test-token"
    mock_client.token_file = None
    mock_client.token_url = None

    mock_datasource = Mock()
    mock_datasource.get_key_url = Mock(return_value="http://example.com/file.txt")

    mock_http = Mock()
    mock_response = Mock()
    mock_response.content = b"file contents"
    mock_http.get = Mock(return_value=mock_response)
    mock_datasource.http = Mock(return_value=mock_http)

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)

    with patch.object(vol._File, "get", return_value=b"file contents"):
        content = volume.get("file.txt")

    assert content == b"file contents"


def test_volume_put_file():
    """Volume can upload file contents."""
    mock_client = Mock()
    mock_client.token = "test-token"
    mock_client.token_file = None
    mock_client.token_url = None

    mock_datasource = Mock()

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)

    with patch.object(vol._File, "put") as mock_put:
        volume.put("file.txt", b"content")
        mock_put.assert_called_once_with(b"content")


def test_volume_upload_file(tmp_path):
    """Volume can upload file from local path."""
    mock_client = Mock()
    mock_client.token = "test-token"
    mock_client.token_file = None
    mock_client.token_url = None

    mock_datasource = Mock()

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)

    # Create a temp file
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"test content")

    with patch.object(vol._File, "upload_file") as mock_upload:
        volume.upload_file("remote.txt", str(test_file))
        mock_upload.assert_called_once_with(str(test_file))


def test_volume_download_file(tmp_path):
    """Volume can download file to local path."""
    mock_client = Mock()
    mock_client.token = "test-token"
    mock_client.token_file = None
    mock_client.token_url = None

    mock_datasource = Mock()

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)

    test_file = tmp_path / "download.txt"

    with patch.object(vol._File, "download_file") as mock_download:
        volume.download_file("remote.txt", str(test_file))
        mock_download.assert_called_once_with(str(test_file))


def test_volume_download_fileobj():
    """Volume can download file to file object."""
    mock_client = Mock()
    mock_client.token = "test-token"
    mock_client.token_file = None
    mock_client.token_url = None

    mock_datasource = Mock()

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)

    fileobj = io.BytesIO()

    with patch.object(vol._File, "download_fileobj") as mock_download:
        volume.download_fileobj("remote.txt", fileobj)
        mock_download.assert_called_once_with(fileobj)


def test_volume_upload_fileobj():
    """Volume can upload from file object."""
    mock_client = Mock()
    mock_client.token = "test-token"
    mock_client.token_file = None
    mock_client.token_url = None

    mock_datasource = Mock()

    volume = vol.Volume(client=mock_client, datasource=mock_datasource)

    fileobj = io.BytesIO(b"content")

    with patch.object(vol._File, "upload_fileobj") as mock_upload:
        volume.upload_fileobj("remote.txt", fileobj)
        mock_upload.assert_called_once_with(fileobj)


# Error handling tests
def test_unauthenticated_error():
    """UnauthenticatedError is a DominoError."""
    error = vol.UnauthenticatedError("test error")
    assert isinstance(error, vol.DominoError)
    assert str(error) == "test error"


def test_domino_error():
    """DominoError can be raised."""
    error = vol.DominoError("test error")
    assert isinstance(error, Exception)
    assert str(error) == "test error"

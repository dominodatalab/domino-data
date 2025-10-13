"""NetApp Volume tests."""

from unittest.mock import Mock, patch

from domino_data import netapp_volumes as vol


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

    with (
        patch("domino_data.netapp_volumes.AuthenticatedClient"),
        patch("domino_data.netapp_volumes.DataSourceClient"),
        patch("domino_data.netapp_volumes.RemoteFSClient"),
    ):
        client = vol.VolumeClient()

        assert client.token_file == "/path/to/token"
        assert client.token_url == "http://proxy"


def test_volume_client_get_volume(monkeypatch):
    """VolumeClient can get a volume by name."""
    monkeypatch.setenv("DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT", "http://remotefs")

    with (
        patch("domino_data.netapp_volumes.AuthenticatedClient"),
        patch("domino_data.netapp_volumes.DataSourceClient") as mock_ds_client,
        patch("domino_data.netapp_volumes.RemoteFSClient"),
    ):
        client = vol.VolumeClient()

        # Mock datasource client
        mock_datasource = Mock()
        mock_datasource.auth_type = "oauth"
        mock_datasource.client = Mock()
        mock_datasource.config = {}
        mock_datasource.datasource_type = "NetAppVolumeConfig"
        mock_datasource.identifier = "vol-id"
        mock_datasource.name = "test-volume"
        mock_datasource.owner = "test-owner"
        client.datasource_client.get_datasource = Mock(return_value=mock_datasource)

        volume = client.get_volume("test-volume")

        assert isinstance(volume, vol.Volume)
        assert volume.volume_client == client
        assert volume.name == "test-volume"
        client.datasource_client.get_datasource.assert_called_once_with("test-volume")


def test_volume_client_list_volumes(monkeypatch):
    """VolumeClient can list volumes."""
    monkeypatch.setenv("DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT", "http://remotefs")

    with (
        patch("domino_data.netapp_volumes.AuthenticatedClient"),
        patch("domino_data.netapp_volumes.DataSourceClient"),
        patch("domino_data.netapp_volumes.RemoteFSClient"),
    ):
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

    with (
        patch("domino_data.netapp_volumes.AuthenticatedClient"),
        patch("domino_data.netapp_volumes.DataSourceClient"),
        patch("domino_data.netapp_volumes.RemoteFSClient"),
    ):
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
def test_volume_file_creation():
    """Volume can create File objects with auth headers enabled."""
    volume = vol.Volume(
        auth_type="oauth",
        client=Mock(),
        config={},
        datasource_type="NetAppVolumeConfig",
        identifier="vol-id",
        name="test-volume",
        owner="test-owner",
        volume_client=Mock(),
    )
    file = volume.File("test-file.txt")

    assert isinstance(file, vol._File)
    assert file.datasource == volume
    assert file.key == "test-file.txt"
    assert file.include_auth_headers == True


def test_volume_list_files():
    """Volume can list files with auth headers enabled."""
    volume = vol.Volume(
        auth_type="oauth",
        client=Mock(),
        config={},
        datasource_type="NetAppVolumeConfig",
        identifier="vol-id",
        name="test-volume",
        owner="test-owner",
        volume_client=Mock(),
    )

    mock_objects = [Mock(key="file1.txt"), Mock(key="file2.txt")]
    volume.list_objects = Mock(return_value=mock_objects)

    files = volume.list_files(prefix="test", page_size=50)

    assert len(files) == 2
    assert files[0].key == "file1.txt"
    assert files[1].key == "file2.txt"
    assert files[0].include_auth_headers == True
    assert files[1].include_auth_headers == True
    volume.list_objects.assert_called_once_with(prefix="test", page_size=50)


def test_volume_get_file_url():
    """Volume can get file URL."""
    volume = vol.Volume(
        auth_type="oauth",
        client=Mock(),
        config={},
        datasource_type="NetAppVolumeConfig",
        identifier="vol-id",
        name="test-volume",
        owner="test-owner",
        volume_client=Mock(),
    )
    volume.get_key_url = Mock(return_value="http://example.com/file.txt")

    url = volume.get_file_url("file.txt")

    assert url == "http://example.com/file.txt"
    volume.get_key_url.assert_called_once_with(object_key="file.txt", is_read_write=False)


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

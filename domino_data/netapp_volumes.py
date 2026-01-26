"""Datasource module."""

from typing import Any, List, Optional

import os
from os.path import exists

import attr
import backoff
import httpx

import domino_data.configuration_gen
from domino_data.data_sources import DataSourceClient, ObjectStoreDatasource, _Object
from remotefs_api_client import ApiClient, Configuration, SnapshotsApi, VolumesApi
from remotefs_api_client.models import RemotefsSnapshot, RemotefsVolume

from .auth import AuthenticatedClient, get_jwt_token
from .logging import logger

ACCEPT_HEADERS = {"Accept": "application/json"}
AUTHORIZATION_HEADER = "Authorization"

DOMINO_API_HOST = "DOMINO_API_HOST"
DOMINO_API_PROXY = "DOMINO_API_PROXY"
DOMINO_USER_HOST = "DOMINO_USER_HOST"
DOMINO_TOKEN_FILE = "DOMINO_TOKEN_FILE"
DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT = "DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT"


def __getattr__(name: str) -> Any:
    if name.endswith("Config"):
        return getattr(domino_data.configuration_gen, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__() -> List[str]:
    confs = filter(lambda x: x.endswith("Config"), dir(domino_data.configuration_gen))
    return list(globals().keys()) + list(confs)


class DominoError(Exception):
    """Base exception for known errors."""


class UnauthenticatedError(DominoError):
    """To handle exponential backoff."""


class _File(_Object):
    """Represents a file in a volume - wraps _Object with volume-specific auth."""

    pass


@attr.s
class RemoteFSClient:
    """RemoteFS API client for volumes and snapshots."""

    token_file: Optional[str] = attr.ib()
    token_url: Optional[str] = attr.ib()
    token: Optional[str] = attr.ib()
    base_url: str = attr.ib()

    api_client: ApiClient = attr.ib(init=False, repr=False)
    volumes_api: VolumesApi = attr.ib(init=False, repr=False)
    snapshots_api: SnapshotsApi = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        """Initialize the RemoteFS API client and API instances."""
        remotefs_config = Configuration()
        remotefs_config.host = self.base_url
        self.api_client = ApiClient(configuration=remotefs_config)

        # Set up authentication headers
        if self.token:
            self.api_client.set_default_header(AUTHORIZATION_HEADER, f"Bearer {self.token}")
        elif self.token_file and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            self.api_client.set_default_header(AUTHORIZATION_HEADER, f"Bearer {jwt}")
        elif self.token_url:
            try:
                jwt = get_jwt_token(self.token_url)
                self.api_client.set_default_header(AUTHORIZATION_HEADER, f"Bearer {jwt}")
            except httpx.HTTPStatusError:
                pass

        # Initialize API instances
        self.volumes_api = VolumesApi(self.api_client)
        self.snapshots_api = SnapshotsApi(self.api_client)

    def list_volumes(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[RemotefsVolume]:
        """List volumes that the user has access to.

        Args:
            offset: optional offset
            limit: optional limit

        Returns:
            List of volumes.
        """
        kwargs = {"status": ["Active"]}
        if offset is not None:
            kwargs["offset"] = offset
        if limit is not None:
            kwargs["limit"] = limit
        response = self.volumes_api.volumes_get(**kwargs)

        return response.data if response.data else []

    def list_snapshots(
        self,
        volume_id: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[RemotefsSnapshot]:
        """List snapshots in a specified volume that a user has access to.

        Args:
            volume_id: volume ID
            offset: optional offset
            limit: optional limit

        Returns:
            List of snapshots.
        """
        kwargs = {}
        if offset is not None:
            kwargs["offset"] = offset
        if limit is not None:
            kwargs["limit"] = limit
        kwargs["volume_id"] = [volume_id]

        response = self.snapshots_api.snapshots_get(**kwargs)

        return response.data if response.data else []

    def get_volume_by_unique_name(self, unique_name: str) -> RemotefsVolume:
        """Fetch a volume by unique name.

        Args:
            unique_name: volume unique name

        Returns:
            remotefs volume.
        """
        return self.volumes_api.volumes_unique_name_unique_name_get(unique_name)


@attr.s
class Volume(ObjectStoreDatasource):
    """Represents a Domino volume."""

    volume_client: "NetAppVolumeClient" = attr.ib(repr=False)

    def Object(
        self, key: str, include_auth_headers: bool = True
    ) -> _File:  # pylint: disable=invalid-name
        """Return a file object with authentication headers enabled by default.

        Args:
            key: unique key of the file
            include_auth_headers: whether to include auth headers (default: True for volumes)

        Returns:
            File object
        """
        return _File(datasource=self, key=key, include_auth_headers=include_auth_headers)

    def File(self, file_name: str) -> _File:  # pylint: disable=invalid-name
        """Return a file with given name and volume client."""
        return _File(datasource=self, key=file_name, include_auth_headers=True)

    def list_files(self, prefix: str = "", page_size: int = 1000) -> List[_File]:
        """List files in the volume.

        Args:
            prefix: optional prefix to filter files
            page_size: optional number of files to fetch

        Returns:
            List of files
        """
        objects = self.list_objects(prefix=prefix, page_size=page_size)
        return [_File(datasource=self, key=obj.key, include_auth_headers=True) for obj in objects]

    def get_file_url(self, file_name: str) -> str:
        """Get a signed URL for the given key.

        Args:
            file_name: name of the file to get URL for.

        Returns:
            URL for the given file
        """
        return self.get_key_url(object_key=file_name, is_read_write=False)


@attr.s
class NetAppVolumeClient:
    """API client and bindings."""

    token_file: Optional[str] = attr.ib(factory=lambda: os.getenv(DOMINO_TOKEN_FILE))
    token_url: Optional[str] = attr.ib(factory=lambda: os.getenv(DOMINO_API_PROXY))
    token: Optional[str] = attr.ib(default=None)

    domino: AuthenticatedClient = attr.ib(init=False, repr=False)
    datasource_client: DataSourceClient = attr.ib(init=False, repr=False)
    remotefs_client: RemoteFSClient = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        domino_host = os.getenv(
            DOMINO_API_PROXY, os.getenv(DOMINO_API_HOST, os.getenv(DOMINO_USER_HOST, ""))
        )
        remotefs_host = os.getenv(DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT, "")

        logger.info(
            "initializing volume client with host",
            domino_host=domino_host,
            remotefs_host=remotefs_host,
        )

        self.domino = AuthenticatedClient(
            base_url=f"{domino_host}/v4",
            api_key=None,
            token_file=self.token_file,
            token_url=self.token_url,
            token=self.token,
            headers=ACCEPT_HEADERS,
            timeout=httpx.Timeout(20.0),
            verify_ssl=True,
        )

        self.datasource_client = DataSourceClient(
            api_key=None,
            token_file=self.token_file,
            token_url=self.token_url,
            token=self.token,
        )

        self.remotefs_client = RemoteFSClient(
            token_file=self.token_file,
            token_url=self.token_url,
            token=self.token,
            base_url=f"{remotefs_host}/remotefs/v1",
        )

    def get_volume(self, name: str) -> Volume:
        """Fetch a volume by name.

        Args:
            name: unique name of a volume

        Returns:
            Volume entity with given name

        Raises:
            Exception: If the response from Domino is not 200
        """
        logger.info("get_volume", volume_name=name)

        data_source = self.datasource_client.get_datasource(name)
        # Volume inherits from ObjectStoreDatasource, so we pass datasource attributes
        return Volume(
            auth_type=data_source.auth_type,
            client=data_source.client,
            config=data_source.config,
            datasource_type=data_source.datasource_type,
            identifier=data_source.identifier,
            name=data_source.name,
            owner=data_source.owner,
            volume_client=self,
        )

    @backoff.on_exception(backoff.expo, UnauthenticatedError, max_time=60)
    def list_files(
        self,
        volume_unique_name: str,
        prefix: str = "",
        page_size: int = 1000,
    ) -> List[str]:
        """List files in a volume.

        Args:
            volume_unique_name: unique name of a volume
            prefix: optional prefix to filter files
            page_size: optional number of files to fetch

        Returns:
            List of files as string

        Raises:
            Exception: if the response from the Proxy is not 200
            UnauthenticatedError: if the request has invalid authentication
        """
        logger.info("list_files", volume_unique_name=volume_unique_name)

        datasource = self.datasource_client.get_datasource(volume_unique_name)

        return self.datasource_client.list_keys(
            datasource_id=datasource.identifier,
            prefix=prefix,
            page_size=page_size,
            config={},
            credential={},
        )

    @backoff.on_exception(backoff.expo, UnauthenticatedError, max_time=60)
    def get_file_url(
        self,
        volume_unique_name: str,
        file_name: str,
    ) -> str:
        """Request a URL for a given volume and file.

        Args:
            volume_unique_name: unique name of a volume
            file_name: name of a file in the volume

        Returns:
            URL of the requested file.

        Raises:
            Exception: if the response from the Proxy is not 200
            UnauthenticatedError: if the request has invalid authentication
        """
        logger.info("get_file_url", volume_unique_name=volume_unique_name, file_name=file_name)

        datasource = self.datasource_client.get_datasource(volume_unique_name)

        return self.datasource_client.get_key_url(
            datasource_id=datasource.identifier,
            object_key=file_name,
            is_read_write=False,
            config={},
            credential={},
        )

    @backoff.on_exception(backoff.expo, UnauthenticatedError, max_time=60)
    def list_volumes(  # pylint: disable=too-many-arguments
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[RemotefsVolume]:
        """List volumes that the user has access to.

        Args:
            offset: optional offset
            limit: optional limit

        Returns:
            List of volumes.

        Raises:
            Exception: if the response from RemoteFS is not 200
            UnauthenticatedError: if the request has invalid authentication
        """
        logger.info("list_volumes", offset=offset, limit=limit)
        return self.remotefs_client.list_volumes(offset=offset, limit=limit)

    @backoff.on_exception(backoff.expo, UnauthenticatedError, max_time=60)
    def list_snapshots(  # pylint: disable=too-many-arguments
        self,
        volume_unique_name: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[RemotefsSnapshot]:
        """List volume snapshots that a user has access to.

        Args:
            volume_unique_name: unique name of a volume (optional filter)
            offset: optional offset
            limit: optional limit

        Returns:
            List of snapshots.

        Raises:
            Exception: if the response from RemoteFS is not 200
            UnauthenticatedError: if the request has invalid authentication
        """
        logger.info(
            "list_snapshots", volume_unique_name=volume_unique_name, offset=offset, limit=limit
        )
        volume = self.remotefs_client.get_volume_by_unique_name(unique_name=volume_unique_name)
        return self.remotefs_client.list_snapshots(volume_id=volume.id, offset=offset, limit=limit)

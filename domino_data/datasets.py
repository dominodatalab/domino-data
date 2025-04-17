"""Datasource module."""

from typing import Any, List, Optional

import os
from os.path import exists

import attr
import backoff
import httpx
import urllib3

import domino_data.configuration_gen
from domino_data.data_sources import DataSourceClient, ObjectStoreDatasource

from .auth import AuthenticatedClient, get_jwt_token
from .configuration_gen import Config, DatasetConfig
from .logging import logger
from .transfer import MAX_WORKERS, BlobTransfer

ACCEPT_HEADERS = {"Accept": "application/json"}

DOMINO_API_HOST = "DOMINO_API_HOST"
DOMINO_API_PROXY = "DOMINO_API_PROXY"
DOMINO_USER_API_KEY = "DOMINO_USER_API_KEY"
DOMINO_USER_HOST = "DOMINO_USER_HOST"
DOMINO_TOKEN_FILE = "DOMINO_TOKEN_FILE"


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


@attr.s
class _File:
    """Represents a file in a dataset."""

    dataset: "Dataset" = attr.ib(repr=False)
    name: str = attr.ib(repr=False)

    def http(self) -> httpx.Client:
        """Get dataset http client."""
        return self.dataset.http()

    def pool_manager(self) -> urllib3.PoolManager:
        """Get dataset http pool manager."""
        return self.dataset.pool_manager()

    def get(self) -> bytes:
        """Get object content as bytes."""
        url = self.dataset.get_file_url(self.name)
        headers = self._get_headers()

        res = self.http().get(url, headers=headers)
        res.raise_for_status()

        return res.content

    def download_file(self, filename: str) -> None:
        """Download object content to file located at filename.

        The file will be created if it does not exist.

        Args:
            filename: path of file to write content to.
        """
        url = self.dataset.get_file_url(self.name)
        headers = self._get_headers()

        content_size = 0
        with (
            self.http().stream("GET", url, headers=headers) as stream,
            open(filename, "wb") as file,
        ):
            for data in stream.iter_bytes():
                content_size += len(data)
                file.write(data)

    def download(self, filename: str, max_workers: int = MAX_WORKERS) -> None:
        """Download object content to file with multithreaded support.

        The file will be created if it does not exist. File will be overwritten if it exists.

        Args:
            filename: path of file to write content to
            max_workers: max parallelism for high speed download
        """
        url = self.dataset.get_file_url(self.name)
        headers = self._get_headers()
        with open(filename, "wb") as file:
            BlobTransfer(
                url, file, headers=headers, max_workers=max_workers, http=self.pool_manager()
            )

    def download_fileobj(self, fileobj: Any) -> None:
        """Download object content to file like object.

        Args:
            fileobj: A file-like object to download into.
                At a minimum, it must implement the write method and must accept bytes.
        """
        url = self.dataset.get_file_url(self.name)
        headers = self._get_headers()
        content_size = 0
        with self.http().stream("GET", url, headers=headers) as stream:
            for data in stream.iter_bytes():
                content_size += len(data)
                fileobj.write(data)

    def _get_headers(self) -> dict:
        headers = {}

        if self.dataset.client.token_url is not None:
            try:
                jwt = get_jwt_token(self.dataset.client.token_url)
            except httpx.HTTPStatusError:
                pass
            else:
                headers = {"Authorization": f"Bearer {jwt}"}

        if self.dataset.client.token_file and exists(self.dataset.client.token_file):
            with open(self.dataset.client.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            headers = {"Authorization": f"Bearer {jwt}"}

        if self.dataset.client.api_key:
            headers = {"X-Domino-Api-Key": self.dataset.client.api_key}

        if self.dataset.client.token is not None:
            headers = {"Authorization": f"Bearer {self.dataset.client.token}"}

        return headers


@attr.s
class Dataset:
    """Represents a Domino dataset."""

    # pylint: disable=too-many-instance-attributes

    client: "DatasetClient" = attr.ib(repr=False)
    datasource: ObjectStoreDatasource = attr.ib(repr=False)

    def http(self) -> httpx.Client:
        """Singleton http client built for the dataset."""
        return self.datasource.http()

    def pool_manager(self) -> urllib3.PoolManager:
        """Urllib3 pool manager for range downloads."""
        return urllib3.PoolManager()

    def update(self, config: DatasetConfig) -> None:
        """Store configuration override for future query calls.

        Args:
            config: dataset config class
        """
        self.datasource._config_override = config

    def reset_config(self) -> None:
        """Reset the configuration override."""
        self.datasource._config_override = Config()

    def File(self, file_name: str) -> _File:  # pylint: disable=invalid-name
        """Return a file with given name and dataset client."""
        return _File(dataset=self, name=file_name)

    def list_files(self, prefix: str = "", page_size: int = 1000) -> List[_File]:
        """List files in the dataset.

        Args:
            prefix: optional prefix to filter files
            page_size: optional number of files to fetch

        Returns:
            List of files
        """
        objects = self.datasource.list_objects(prefix=prefix, page_size=page_size)

        return [_File(dataset=self, name=obj.key) for obj in objects]

    def get_file_url(self, file_name: str) -> str:
        """Get a signed URL for the given key.

        Args:
            file_name: name of the file to get URL for.

        Returns:
            URL for the given file
        """
        return self.datasource.get_key_url(object_key=file_name, is_read_write=False)

    def get(self, file_name: str) -> bytes:
        """Get file contents as bytes.

        Args:
            file_name: name of the file

        Returns:
            file contents as bytes
        """
        return self.File(file_name).get()

    def download_file(self, dataset_file_name: str, local_file_name: str) -> None:
        """Download file content to file located at local_file_name.

        The file will be created if it does not exist.

        Args:
            dataset_file_name: name of the file in the dataset to download.
            local_file_name: path of file to write content to.
        """
        self.File(dataset_file_name).download_file(local_file_name)

    def download(
        self, dataset_file_name: str, local_file_name: str, max_workers: int = MAX_WORKERS
    ) -> None:
        """Download file content to file located at filename.

        The file will be created if it does not exist.

        Args:
            dataset_file_name: name of the file in the dataset to download.
            local_file_name: path of file to write content to
            max_workers: max parallelism for high speed download
        """
        self.File(dataset_file_name).download(local_file_name, max_workers)

    def download_fileobj(self, dataset_file_name: str, fileobj: Any) -> None:
        """Download file contents to file like object.

        Args:
            dataset_file_name: name of the file in the dataset to download.
            fileobj: A file-like object to download into.
                At a minimum, it must implement the write method and must accept bytes.
        """
        self.File(dataset_file_name).download_fileobj(fileobj)


@attr.s
class DatasetClient:
    """API client and bindings."""

    api_key: Optional[str] = attr.ib(factory=lambda: os.getenv(DOMINO_USER_API_KEY))
    token_file: Optional[str] = attr.ib(factory=lambda: os.getenv(DOMINO_TOKEN_FILE))
    token_url: Optional[str] = attr.ib(factory=lambda: os.getenv(DOMINO_API_PROXY))
    token: Optional[str] = attr.ib(default=None)

    domino: AuthenticatedClient = attr.ib(init=False, repr=False)
    datasource_client = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        domino_host = os.getenv(
            DOMINO_API_PROXY, os.getenv(DOMINO_API_HOST, os.getenv(DOMINO_USER_HOST, ""))
        )

        logger.info(
            "initializing dataset client with host",
            domino_host=domino_host,
        )

        self.domino = AuthenticatedClient(
            base_url=f"{domino_host}/v4",
            api_key=self.api_key,
            token_file=self.token_file,
            token_url=self.token_url,
            token=self.token,
            headers=ACCEPT_HEADERS,
            timeout=httpx.Timeout(20.0),
            verify_ssl=True,
        )

        self.datasource_client = DataSourceClient(
            api_key=self.api_key,
            token_file=self.token_file,
            token_url=self.token_url,
            token=self.token,
        )

    def get_dataset(self, name: str) -> Dataset:
        """Fetch a dataset by name.

        Args:
            name: unique name of a dataset

        Returns:
            Dataset entity with given name

        Raises:
            Exception: If the response from Domino is not 200
        """
        logger.info("get_dataset", dataset_name=name)

        data_source = self.datasource_client.get_datasource(name)
        return Dataset(client=self, datasource=data_source)

    @backoff.on_exception(backoff.expo, UnauthenticatedError, max_time=60)
    def list_files(
        self,
        dataset_unique_name: str,
        prefix: str,
        page_size: int,
    ) -> List[str]:
        """List files in a dataset.

        Args:
            dataset_unique_name: unique name of a dataset
            prefix: optional prefix to filter files
            page_size: optional number of files to fetch

        Returns:
            List of files as string

        Raises:
            Exception: if the response from the Proxy is not 200
            UnauthenticatedError: if the request has invalid authentication
        """
        logger.info("list_files", dataset_unique_name=dataset_unique_name)

        return self.datasource_client.list_keys(
            datasource_id=dataset_unique_name,
            prefix=prefix,
            page_size=page_size,
            config={},
            credential={},
        )

    @backoff.on_exception(backoff.expo, UnauthenticatedError, max_time=60)
    def get_file_url(  # pylint: disable=too-many-arguments
        self,
        dataset_unique_name: str,
        file_name: str,
    ) -> str:
        """Request a URL for a given dataset and file.

        Args:
            dataset_unique_name: unique name of a dataset
            file_name: name of a file in the dataset

        Returns:
            URL of the requested file.

        Raises:
            Exception: if the response from the Proxy is not 200
            UnauthenticatedError: if the request has invalid authentication
        """
        logger.info("get_file_url", dataset_unique_name=dataset_unique_name, file_name=file_name)

        return self.datasource_client.get_key_url(
            datasource_id=dataset_unique_name,
            object_key=file_name,
            is_read_write=False,
            config={},
            credential={},
        )

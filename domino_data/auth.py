"""Authentication classes for HTTP and Flight clients."""

from typing import Dict, Optional

from os.path import exists

import attr
import backoff
import httpx
from pyarrow import flight

from datasource_api_client.client import Client


@backoff.on_exception(backoff.expo, httpx.HTTPStatusError, max_time=2)
def get_jwt_token(url: str) -> str:
    """Gets a domino token from local sidecar API.

    Args:
        url: base url of sidecar container serving token API

    Returns:
        JWT as string

    Raises:
        HTTPStatusError: if the API returns an error
    """
    resp = httpx.get(f"{url}/access-token")
    resp.raise_for_status()
    return resp.read().decode("ascii")


@attr.s(auto_attribs=True)
class AuthenticatedClient(Client):
    """A client that authenticates all requests with either the API Key or JWT."""

    api_key: Optional[str] = attr.ib()
    token_file: Optional[str] = attr.ib()
    token_url: Optional[str] = attr.ib()

    def __attrs_post_init__(self):
        if not (self.api_key or self.token_file or self.token_url):
            raise Exception(
                "One of two authentication methods must be supplied (API Key or JWT Location)"  # noqa
            )

    def get_headers(self) -> Dict[str, str]:
        """Get headers with either JWT or API Key."""
        if self.api_key:
            return {"X-Domino-Api-Key": self.api_key, **self.headers}

        if self.token_url is not None:
            try:
                jwt = get_jwt_token(self.token_url)
            except httpx.HTTPStatusError:
                pass
            else:
                return {"Authorization": f"Bearer {jwt}", **self.headers}

        if self.token_file and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            return {"Authorization": f"Bearer {jwt}", **self.headers}

        return self.headers


@attr.s(auto_attribs=True)
class ProxyClient(AuthenticatedClient):
    """A client that authenticates all requests but with Proxy headers."""

    def get_headers(self) -> Dict[str, str]:
        if self.api_key:
            self.headers["X-Domino-Api-Key"] = self.api_key

        if self.token_url is not None:
            try:
                jwt = get_jwt_token(self.token_url)
            except httpx.HTTPStatusError:
                pass
            else:
                self.headers["X-Domino-Jwt"] = jwt
                return self.headers

        if self.token_file and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            self.headers["X-Domino-Jwt"] = jwt

        return self.headers


@attr.s(auto_attribs=True)
class AuthMiddlewareFactory(flight.ClientMiddlewareFactory):
    """Middleware Factory for authenticating flight requests."""

    api_key: Optional[str] = attr.ib()
    token_file: Optional[str] = attr.ib()
    token_url: Optional[str] = attr.ib()

    def __attrs_post_init__(self):
        if not (self.api_key or self.token_file or self.token_url):
            raise Exception(
                "One of two authentication methods must be supplied (API Key or JWT Location)"  # noqa
            )

    def start_call(self, _):
        """Called at the start of an RPC."""
        jwt = None

        if self.token_url is not None:
            try:
                jwt = get_jwt_token(self.token_url)
            except httpx.HTTPStatusError:
                pass
            else:
                return AuthMiddleware(self.api_key, jwt)

        if self.token_file is not None and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()

        return AuthMiddleware(self.api_key, jwt)


@attr.s(auto_attribs=True)
class AuthMiddleware(flight.ClientMiddleware):
    """Middleware for authenticating flight requests."""

    api_key: Optional[str] = attr.ib()
    jwt: Optional[str] = attr.ib()

    def call_completed(self, _):
        """No implementation. TODO logging."""

    def received_headers(self, _):
        """No implementation."""

    def sending_headers(self):
        """Return authentication headers."""
        headers = {}

        if self.api_key is not None:
            headers["x-domino-api-key"] = self.api_key
        if self.jwt is not None:
            headers["x-domino-jwt"] = self.jwt

        return headers

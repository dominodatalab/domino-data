"""Authentication classes for HTTP and Flight clients."""

from typing import Dict, Optional

from os.path import exists

import attr
from pyarrow import flight

from datasource_api_client.client import Client


@attr.s(auto_attribs=True)
class AuthenticatedClient(Client):
    """A client that authenticate all requests with either the API Key or JWT."""

    api_key: Optional[str] = attr.ib()
    token_file: Optional[str] = attr.ib()

    def __attrs_post_init__(self):
        if not (self.api_key or self.token_file):
            raise Exception(
                "One of two authentication methods needs to be supplied "
                "(API Key or JWT Location)"
            )

    def get_headers(self) -> Dict[str, str]:
        """Get headers with both JWT and API Key."""
        if self.api_key:
            return {"X-Domino-Api-Key": self.api_key, **self.headers}

        if self.token_file and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            return {"Authorization": f"Bearer {jwt}", **self.headers}

        return self.headers


@attr.s(auto_attribs=True)
class ProxyClient(AuthenticatedClient):
    """A client that authenticate all requests but with Proxy headers."""

    def get_headers(self) -> Dict[str, str]:
        if self.api_key:
            self.headers["X-Domino-Api-Key"] = self.api_key

        if self.token_file and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            self.headers["X-Domino-Jwt"] = jwt

        return self.headers


@attr.s(auto_attribs=True)
class AuthMiddlewareFactory(flight.ClientMiddlewareFactory):
    """Middleware Factory for authenticating flight requests."""

    # pylint: disable=too-few-public-methods
    api_key: Optional[str] = attr.ib()
    token_file: Optional[str] = attr.ib()

    def __attrs_post_init__(self):
        if not (self.api_key or self.token_file):
            raise Exception(
                "One of two authentication methods needs to be supplied "
                "(API Key or JWT Location)"
            )

    def start_call(self, info):  # pylint: disable=unused-argument
        """Called at the start of an RPC."""
        jwt = None

        if self.token_file is not None and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()

        return AuthMiddleware(self.api_key, jwt)


@attr.s(auto_attribs=True)
class AuthMiddleware(flight.ClientMiddleware):
    """Middleware for authenticating flight requests."""

    # pylint: disable=too-few-public-methods
    api_key: Optional[str] = attr.ib()
    jwt: Optional[str] = attr.ib()

    def call_completed(self, exception):
        """No implementation. TODO logging."""

    def received_headers(self, headers):
        """No implementation."""

    def sending_headers(self):
        """Return authentication headers."""
        headers = {}

        if self.api_key is not None:
            headers["x-domino-api-key"] = self.api_key
        if self.jwt is not None:
            headers["x-domino-jwt"] = self.jwt

        return headers

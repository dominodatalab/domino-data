"""Authentication classes for HTTP and Flight clients."""

from typing import Dict, Optional

from os.path import exists

import attr
import backoff
import httpx
from httpx._config import DEFAULT_TIMEOUT_CONFIG
from pyarrow import flight

from datasource_api_client.client import Client


@backoff.on_exception(backoff.expo, httpx.HTTPStatusError, max_time=2)
@backoff.on_exception(backoff.expo, httpx.ReadTimeout, max_tries=2)
def get_jwt_token(url: str) -> str:
    """Gets a domino token from local sidecar API.

    Args:
        url: base url of sidecar container serving token API

    Returns:
        JWT as string

    Raises:
        HTTPStatusError: if the API returns an error
    """
    resp = httpx.get(f"{url}/access-token", timeout=DEFAULT_TIMEOUT_CONFIG)
    resp.raise_for_status()
    return resp.read().decode("ascii")


def get_auth_value(
    token: Optional[str] = None,
    token_file: Optional[str] = None,
    token_url: Optional[str] = None,
    api_key: Optional[str] = None,
    include_api_key: bool = True,
) -> tuple[Optional[str], Optional[str]]:
    """Single source of truth for determining auth method and value.

    Args:
        token: Direct token to use
        token_file: Path to file containing token
        token_url: URL to fetch token from
        api_key: API key to use
        include_api_key: Whether to consider api_key as a fallback (default: True)

    Returns:
        Tuple of (auth_type, auth_value) where auth_type is one of:
        - "bearer": Use Bearer token authentication (auth_value is the token)
        - "api_key": Use API key authentication (auth_value is the key)
        - None: No authentication available (auth_value is None)
    """
    # Priority 1: Direct token
    if token is not None:
        return ("bearer", token)

    # Priority 2: Token file
    if token_file and exists(token_file):
        with open(token_file, encoding="ascii") as f:
            jwt = f.readline().rstrip()
        return ("bearer", jwt)

    # Priority 3: Token URL
    if token_url is not None:
        try:
            jwt = get_jwt_token(token_url)
            return ("bearer", jwt)
        except httpx.HTTPStatusError:
            pass

    # Priority 4: API key (if enabled)
    if include_api_key and api_key:
        return ("api_key", api_key)

    return (None, None)


@attr.s(auto_attribs=True)
class AuthenticatedClient(Client):
    """A client that authenticates all requests with either the API Key or JWT."""

    api_key: Optional[str] = attr.ib()
    token_file: Optional[str] = attr.ib()
    token_url: Optional[str] = attr.ib()
    token: Optional[str] = attr.ib()

    def __attrs_post_init__(self):
        if not (self.api_key or self.token_file or self.token_url or self.token):
            raise Exception(
                "One of two authentication methods must be supplied (API Key or JWT Location)"  # noqa
            )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get auth headers with either JWT or API Key."""
        if self.token is not None:
            return {"Authorization": f"Bearer {self.token}"}

        if self.token_file and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            return {"Authorization": f"Bearer {jwt}"}

        if self.token_url is not None:
            try:
                jwt = get_jwt_token(self.token_url)
                return {"Authorization": f"Bearer {jwt}"}
            except httpx.HTTPStatusError:
                pass

        if self.api_key:
            return {"X-Domino-Api-Key": self.api_key}

        return {}

    def with_auth_headers(self) -> "AuthenticatedClient":
        auth_headers = self._get_auth_headers()
        if self._client is not None:
            self._client.headers.update(auth_headers)
        if self._async_client is not None:
            self._async_client.headers.update(auth_headers)
        self._headers.update(auth_headers)
        return self


@attr.s(auto_attribs=True)
class ProxyClient(AuthenticatedClient):
    """A client that authenticates all requests but with Proxy headers."""

    client_source: Optional[str] = attr.ib()
    run_id: Optional[str] = attr.ib()

    def _get_auth_headers(self) -> Dict[str, str]:
        headers = {}
        if self.client_source:
            headers["X-Domino-Client-Source"] = self.client_source
        if self.run_id:
            headers["X-Domino-Run-Id"] = self.run_id

        if self.token is not None:
            headers["Authorization"] = f"Bearer {self.token}"
            return headers

        if self.token_file and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            headers["X-Domino-Jwt"] = jwt
            return headers

        if self.token_url is not None:
            try:
                jwt = get_jwt_token(self.token_url)
                headers["X-Domino-Jwt"] = jwt
                return headers
            except httpx.HTTPStatusError:
                pass

        if self.api_key:
            headers["X-Domino-Api-Key"] = self.api_key

        return headers


@attr.s(auto_attribs=True)
class AuthMiddlewareFactory(flight.ClientMiddlewareFactory):
    """Middleware Factory for authenticating flight requests."""

    api_key: Optional[str] = attr.ib()
    token_file: Optional[str] = attr.ib()
    token_url: Optional[str] = attr.ib()
    token: Optional[str] = attr.ib()

    def __attrs_post_init__(self):
        if not (self.api_key or self.token_file or self.token_url or self.token):
            raise Exception(
                "One of two authentication methods must be supplied (API Key or JWT Location)"  # noqa
            )

    def start_call(self, _):
        """Called at the start of an RPC."""
        jwt = None
        if self.token is not None:
            jwt = self.token
            return AuthMiddleware(self.api_key, jwt)

        if self.token_file is not None and exists(self.token_file):
            with open(self.token_file, encoding="ascii") as token_file:
                jwt = token_file.readline().rstrip()
            return AuthMiddleware(self.api_key, jwt)

        if self.token_url is not None:
            try:
                jwt = get_jwt_token(self.token_url)
                return AuthMiddleware(self.api_key, jwt)
            except httpx.HTTPStatusError:
                pass

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

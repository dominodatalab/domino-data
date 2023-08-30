""" Classes to augment headers with metadata for HTTP and Flight requests."""

from typing import Optional

import attr
from pyarrow import flight


@attr.s(auto_attribs=True)
class MetaMiddlewareFactory(flight.ClientMiddlewareFactory):
    """Middleware Factory for metadata."""

    client_source: Optional[str] = attr.ib()
    run_id: Optional[str] = attr.ib()

    def start_call(self, _):
        """Called at the start of an RPC."""
        return MetaMiddleware(self.client_source, self.run_id)


@attr.s(auto_attribs=True)
class MetaMiddleware(flight.ClientMiddleware):
    """Middleware for authenticating flight requests."""

    client_source: Optional[str] = attr.ib()
    run_id: Optional[str] = attr.ib()

    def call_completed(self, _):
        """No implementation. TODO logging."""

    def received_headers(self, _):
        """No implementation."""

    def sending_headers(self):
        """Return metadata headers."""
        headers = {}

        if self.client_source is not None:
            headers["x-domino-client-source"] = self.client_source
        if self.run_id is not None:
            headers["x-domino-run-id"] = self.run_id

        return headers

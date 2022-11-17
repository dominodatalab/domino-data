"""Feature Store module."""
from typing import List, Optional, cast

import json
import os

from attrs import define, field

from domino_data.auth import AuthenticatedClient
from feature_store_api_client.api.default import post_featureview
from feature_store_api_client.client import Client
from feature_store_api_client.models import FeatureViewRequest, UpsertFeatureViewsRequest
from feature_store_api_client.types import Response

from .exceptions import ServerException


@define
class FeatureStoreClient:
    """API client and bindings."""

    client: Client = field(init=False, repr=False)

    api_key: Optional[str] = field(factory=lambda: os.getenv("DOMINO_USER_API_KEY"))
    token_file: Optional[str] = field(factory=lambda: os.getenv("DOMINO_TOKEN_FILE"))

    def __attrs_post_init__(self):
        domino_host = os.getenv("DOMINO_API_HOST", os.getenv("DOMINO_USER_HOST", ""))
        token_url = os.getenv("DOMINO_API_PROXY")

        self.client = cast(
            Client,
            AuthenticatedClient(
                base_url=f"{domino_host}/featurestore",
                api_key=self.api_key,
                token_file=self.token_file,
                token_url=token_url,
                headers={"Accept": "application/json"},
            ),
        )

    def post_feature_views(self, feature_views: List[FeatureViewRequest]) -> None:
        """Insert or update feature views.

        Args:
            feature_views: an array of feature views to be inserted or updated.

        Raises:
            ServerException: if update fails
        """
        request = UpsertFeatureViewsRequest(feature_views=feature_views)
        response = post_featureview.sync_detailed(
            client=self.client,
            json_body=request,
        )

        if response.status_code != 200:
            _raise_response_exn(response, "could not create Feature Views")


def _raise_response_exn(response: Response, msg: str) -> None:
    try:
        response_json = json.loads(response.content.decode("utf8"))
        server_msg = response_json.get("message")
    except Exception:
        server_msg = ""

    raise ServerException(msg, server_msg)

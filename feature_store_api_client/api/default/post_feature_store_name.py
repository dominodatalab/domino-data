from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.create_feature_store_request import CreateFeatureStoreRequest
from ...models.feature_store import FeatureStore
from ...types import Response


def _get_kwargs(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureStoreRequest,
) -> Dict[str, Any]:
    url = "{}/{featureStoreName}".format(client.base_url, featureStoreName=feature_store_name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[FeatureStore]:
    if response.status_code == 200:
        response_200 = FeatureStore.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[FeatureStore]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureStoreRequest,
) -> Response[FeatureStore]:
    """Create FeatureStore

    Args:
        feature_store_name (str):
        json_body (CreateFeatureStoreRequest):

    Returns:
        Response[FeatureStore]
    """

    kwargs = _get_kwargs(
        feature_store_name=feature_store_name,
        client=client,
        json_body=json_body,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureStoreRequest,
) -> Optional[FeatureStore]:
    """Create FeatureStore

    Args:
        feature_store_name (str):
        json_body (CreateFeatureStoreRequest):

    Returns:
        Response[FeatureStore]
    """

    return sync_detailed(
        feature_store_name=feature_store_name,
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureStoreRequest,
) -> Response[FeatureStore]:
    """Create FeatureStore

    Args:
        feature_store_name (str):
        json_body (CreateFeatureStoreRequest):

    Returns:
        Response[FeatureStore]
    """

    kwargs = _get_kwargs(
        feature_store_name=feature_store_name,
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureStoreRequest,
) -> Optional[FeatureStore]:
    """Create FeatureStore

    Args:
        feature_store_name (str):
        json_body (CreateFeatureStoreRequest):

    Returns:
        Response[FeatureStore]
    """

    return (
        await asyncio_detailed(
            feature_store_name=feature_store_name,
            client=client,
            json_body=json_body,
        )
    ).parsed

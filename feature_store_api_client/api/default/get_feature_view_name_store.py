from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.feature_store import FeatureStore
from ...types import Response


def _get_kwargs(
    feature_view_name: str,
    *,
    client: Client,
) -> Dict[str, Any]:
    url = "{}/{featureViewName}/store".format(client.base_url, featureViewName=feature_view_name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
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
    feature_view_name: str,
    *,
    client: Client,
) -> Response[FeatureStore]:
    """Get feature store by feature view name

    Args:
        feature_view_name (str):

    Returns:
        Response[FeatureStore]
    """

    kwargs = _get_kwargs(
        feature_view_name=feature_view_name,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    feature_view_name: str,
    *,
    client: Client,
) -> Optional[FeatureStore]:
    """Get feature store by feature view name

    Args:
        feature_view_name (str):

    Returns:
        Response[FeatureStore]
    """

    return sync_detailed(
        feature_view_name=feature_view_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    feature_view_name: str,
    *,
    client: Client,
) -> Response[FeatureStore]:
    """Get feature store by feature view name

    Args:
        feature_view_name (str):

    Returns:
        Response[FeatureStore]
    """

    kwargs = _get_kwargs(
        feature_view_name=feature_view_name,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    feature_view_name: str,
    *,
    client: Client,
) -> Optional[FeatureStore]:
    """Get feature store by feature view name

    Args:
        feature_view_name (str):

    Returns:
        Response[FeatureStore]
    """

    return (
        await asyncio_detailed(
            feature_view_name=feature_view_name,
            client=client,
        )
    ).parsed

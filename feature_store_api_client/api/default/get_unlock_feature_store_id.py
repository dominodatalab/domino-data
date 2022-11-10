from typing import Any, Dict, Optional, Union, cast

import httpx

from ...client import Client
from ...types import Response


def _get_kwargs(
    feature_store_id: str,
    *,
    client: Client,
) -> Dict[str, Any]:
    url = f"{client.base_url}/unlock/{feature_store_id}"

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[Union[Any, bool]]:
    if response.status_code == 200:
        response_200 = cast(bool, response.json())
        return response_200
    if response.status_code == 403:
        response_403 = cast(Any, None)
        return response_403
    if response.status_code == 500:
        response_500 = cast(Any, None)
        return response_500
    return None


def _build_response(*, response: httpx.Response) -> Response[Union[Any, bool]]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    feature_store_id: str,
    *,
    client: Client,
) -> Response[Union[Any, bool]]:
    """Unlock FeatureStore

    Args:
        feature_store_id (str):

    Returns:
        Response[Union[Any, bool]]
    """

    kwargs = _get_kwargs(
        feature_store_id=feature_store_id,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    feature_store_id: str,
    *,
    client: Client,
) -> Optional[Union[Any, bool]]:
    """Unlock FeatureStore

    Args:
        feature_store_id (str):

    Returns:
        Response[Union[Any, bool]]
    """

    return sync_detailed(
        feature_store_id=feature_store_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    feature_store_id: str,
    *,
    client: Client,
) -> Response[Union[Any, bool]]:
    """Unlock FeatureStore

    Args:
        feature_store_id (str):

    Returns:
        Response[Union[Any, bool]]
    """

    kwargs = _get_kwargs(
        feature_store_id=feature_store_id,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    feature_store_id: str,
    *,
    client: Client,
) -> Optional[Union[Any, bool]]:
    """Unlock FeatureStore

    Args:
        feature_store_id (str):

    Returns:
        Response[Union[Any, bool]]
    """

    return (
        await asyncio_detailed(
            feature_store_id=feature_store_id,
            client=client,
        )
    ).parsed

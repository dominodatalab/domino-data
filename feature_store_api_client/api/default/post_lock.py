from typing import Any, Dict, Optional, Union, cast

import httpx

from ...client import Client
from ...models.lock_feature_store_request import LockFeatureStoreRequest
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    json_body: LockFeatureStoreRequest,
) -> Dict[str, Any]:
    url = f"{client.base_url}/lock"

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


def _parse_response(*, response: httpx.Response) -> Optional[Union[Any, bool]]:
    if response.status_code == 200:
        response_200 = cast(bool, response.json())
        return response_200
    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400
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
    *,
    client: Client,
    json_body: LockFeatureStoreRequest,
) -> Response[Union[Any, bool]]:
    """Lock FeatureStore

    Args:
        json_body (LockFeatureStoreRequest):

    Returns:
        Response[Union[Any, bool]]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    json_body: LockFeatureStoreRequest,
) -> Optional[Union[Any, bool]]:
    """Lock FeatureStore

    Args:
        json_body (LockFeatureStoreRequest):

    Returns:
        Response[Union[Any, bool]]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    json_body: LockFeatureStoreRequest,
) -> Response[Union[Any, bool]]:
    """Lock FeatureStore

    Args:
        json_body (LockFeatureStoreRequest):

    Returns:
        Response[Union[Any, bool]]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    json_body: LockFeatureStoreRequest,
) -> Optional[Union[Any, bool]]:
    """Lock FeatureStore

    Args:
        json_body (LockFeatureStoreRequest):

    Returns:
        Response[Union[Any, bool]]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
        )
    ).parsed
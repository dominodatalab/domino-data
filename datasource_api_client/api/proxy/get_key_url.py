from typing import Any, Dict, Optional, Union, cast

import httpx

from ...client import Client
from ...models.key_request import KeyRequest
from ...models.proxy_error_response import ProxyErrorResponse
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    json_body: KeyRequest,
) -> Dict[str, Any]:
    url = f"{client.base_url}/objectstore/key"

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


def _parse_response(*, response: httpx.Response) -> Optional[Union[ProxyErrorResponse, str]]:
    if response.status_code == 200:
        response_200 = cast(str, response.json())
        return response_200
    if response.status_code == 400:
        response_400 = ProxyErrorResponse.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = ProxyErrorResponse.from_dict(response.json())

        return response_500
    return None


def _build_response(*, response: httpx.Response) -> Response[Union[ProxyErrorResponse, str]]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: Client,
    json_body: KeyRequest,
) -> Response[Union[ProxyErrorResponse, str]]:
    """Request a new signed URL for the key of a object store

    Args:
        json_body (KeyRequest):

    Returns:
        Response[Union[ProxyErrorResponse, str]]
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
    json_body: KeyRequest,
) -> Optional[Union[ProxyErrorResponse, str]]:
    """Request a new signed URL for the key of a object store

    Args:
        json_body (KeyRequest):

    Returns:
        Response[Union[ProxyErrorResponse, str]]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    json_body: KeyRequest,
) -> Response[Union[ProxyErrorResponse, str]]:
    """Request a new signed URL for the key of a object store

    Args:
        json_body (KeyRequest):

    Returns:
        Response[Union[ProxyErrorResponse, str]]
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
    json_body: KeyRequest,
) -> Optional[Union[ProxyErrorResponse, str]]:
    """Request a new signed URL for the key of a object store

    Args:
        json_body (KeyRequest):

    Returns:
        Response[Union[ProxyErrorResponse, str]]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
        )
    ).parsed

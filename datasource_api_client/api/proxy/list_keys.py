from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ...client import Client
from ...models.list_request import ListRequest
from ...models.proxy_error_response import ProxyErrorResponse
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    json_body: ListRequest,
) -> Dict[str, Any]:
    url = f"{client.base_url}/objectstore/list"

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


def _parse_response(*, response: httpx.Response) -> Optional[Union[List[str], ProxyErrorResponse]]:
    if response.status_code == 200:
        response_200 = cast(List[str], response.json())

        return response_200
    if response.status_code == 400:
        response_400 = ProxyErrorResponse.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = ProxyErrorResponse.from_dict(response.json())

        return response_500
    return None


def _build_response(*, response: httpx.Response) -> Response[Union[List[str], ProxyErrorResponse]]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: Client,
    json_body: ListRequest,
) -> Response[Union[List[str], ProxyErrorResponse]]:
    """Request a new signed URL for a blob datasource

    Args:
        json_body (ListRequest):

    Returns:
        Response[Union[List[str], ProxyErrorResponse]]
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
    json_body: ListRequest,
) -> Optional[Union[List[str], ProxyErrorResponse]]:
    """Request a new signed URL for a blob datasource

    Args:
        json_body (ListRequest):

    Returns:
        Response[Union[List[str], ProxyErrorResponse]]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    json_body: ListRequest,
) -> Response[Union[List[str], ProxyErrorResponse]]:
    """Request a new signed URL for a blob datasource

    Args:
        json_body (ListRequest):

    Returns:
        Response[Union[List[str], ProxyErrorResponse]]
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
    json_body: ListRequest,
) -> Optional[Union[List[str], ProxyErrorResponse]]:
    """Request a new signed URL for a blob datasource

    Args:
        json_body (ListRequest):

    Returns:
        Response[Union[List[str], ProxyErrorResponse]]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
        )
    ).parsed

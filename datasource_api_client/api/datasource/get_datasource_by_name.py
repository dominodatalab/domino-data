from typing import Any, Dict, Optional, Union

import httpx

from ...client import Client
from ...models.datasource_dto import DatasourceDto
from ...models.error_response import ErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    client: Client,
    run_id: Union[Unset, None, str] = UNSET,
) -> Dict[str, Any]:
    url = f"{client.base_url}/datasource/name/{name}"

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["runId"] = run_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[Union[DatasourceDto, ErrorResponse]]:
    if response.status_code == 200:
        response_200 = DatasourceDto.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401
    if response.status_code == 403:
        response_403 = ErrorResponse.from_dict(response.json())

        return response_403
    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500
    return None


def _build_response(*, response: httpx.Response) -> Response[Union[DatasourceDto, ErrorResponse]]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: Client,
    run_id: Union[Unset, None, str] = UNSET,
) -> Response[Union[DatasourceDto, ErrorResponse]]:
    """Get datasource by name

    Args:
        name (str):
        run_id (Union[Unset, None, str]):

    Returns:
        Response[Union[DatasourceDto, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        run_id=run_id,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    name: str,
    *,
    client: Client,
    run_id: Union[Unset, None, str] = UNSET,
) -> Optional[Union[DatasourceDto, ErrorResponse]]:
    """Get datasource by name

    Args:
        name (str):
        run_id (Union[Unset, None, str]):

    Returns:
        Response[Union[DatasourceDto, ErrorResponse]]
    """

    return sync_detailed(
        name=name,
        client=client,
        run_id=run_id,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Client,
    run_id: Union[Unset, None, str] = UNSET,
) -> Response[Union[DatasourceDto, ErrorResponse]]:
    """Get datasource by name

    Args:
        name (str):
        run_id (Union[Unset, None, str]):

    Returns:
        Response[Union[DatasourceDto, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        run_id=run_id,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    name: str,
    *,
    client: Client,
    run_id: Union[Unset, None, str] = UNSET,
) -> Optional[Union[DatasourceDto, ErrorResponse]]:
    """Get datasource by name

    Args:
        name (str):
        run_id (Union[Unset, None, str]):

    Returns:
        Response[Union[DatasourceDto, ErrorResponse]]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            run_id=run_id,
        )
    ).parsed

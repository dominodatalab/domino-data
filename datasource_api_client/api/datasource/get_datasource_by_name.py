from typing import Any, Dict, Optional, Union

import httpx

from ...client import Client
from ...models.datasource_dto import DatasourceDto
from ...models.error_response import ErrorResponse
from ...types import Response


def _get_kwargs(
    name: str,
    project_id: str,
    *,
    client: Client,
) -> Dict[str, Any]:
    url = "{}/datasource/name/{name}/project/{projectId}".format(
        client.base_url, name=name, projectId=project_id
    )

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
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
    project_id: str,
    *,
    client: Client,
) -> Response[Union[DatasourceDto, ErrorResponse]]:
    kwargs = _get_kwargs(
        name=name,
        project_id=project_id,
        client=client,
    )

    response = httpx.get(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    name: str,
    project_id: str,
    *,
    client: Client,
) -> Optional[Union[DatasourceDto, ErrorResponse]]:
    """ """

    return sync_detailed(
        name=name,
        project_id=project_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    project_id: str,
    *,
    client: Client,
) -> Response[Union[DatasourceDto, ErrorResponse]]:
    kwargs = _get_kwargs(
        name=name,
        project_id=project_id,
        client=client,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.get(**kwargs)

    return _build_response(response=response)


async def asyncio(
    name: str,
    project_id: str,
    *,
    client: Client,
) -> Optional[Union[DatasourceDto, ErrorResponse]]:
    """ """

    return (
        await asyncio_detailed(
            name=name,
            project_id=project_id,
            client=client,
        )
    ).parsed

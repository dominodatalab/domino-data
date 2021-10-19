from typing import Any, Dict, List, Optional, Union

import httpx

from ...client import Client
from ...models.training_set_version import TrainingSetVersion
from ...models.training_set_version_filter import TrainingSetVersionFilter
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: Client,
    json_body: TrainingSetVersionFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Dict[str, Any]:
    url = "{}/version/find".format(client.base_url)

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {
        "offset": offset,
        "limit": limit,
        "asc": asc,
    }
    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    json_json_body = json_body.to_dict()

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
        "params": params,
        "verify": client.verify_ssl,
    }


def _parse_response(*, response: httpx.Response) -> Optional[List[TrainingSetVersion]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = TrainingSetVersion.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[List[TrainingSetVersion]]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: Client,
    json_body: TrainingSetVersionFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Response[List[TrainingSetVersion]]:
    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
        offset=offset,
        limit=limit,
        asc=asc,
    )

    response = httpx.post(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    json_body: TrainingSetVersionFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Optional[List[TrainingSetVersion]]:
    """ """

    return sync_detailed(
        client=client,
        json_body=json_body,
        offset=offset,
        limit=limit,
        asc=asc,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    json_body: TrainingSetVersionFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Response[List[TrainingSetVersion]]:
    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
        offset=offset,
        limit=limit,
        asc=asc,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.post(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    json_body: TrainingSetVersionFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Optional[List[TrainingSetVersion]]:
    """ """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
            offset=offset,
            limit=limit,
            asc=asc,
        )
    ).parsed

from typing import Any, Dict, List, Optional, Union

import httpx

from ...client import Client
from ...models.training_set_version import TrainingSetVersion
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: Client,
    training_set_id: str,
    offset: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> Dict[str, Any]:
    url = "{}/id/{trainingSetId}/versions".format(client.base_url, trainingSetId=training_set_id)

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {
        "offset": offset,
        "limit": limit,
    }
    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
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
    training_set_id: str,
    offset: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> Response[List[TrainingSetVersion]]:
    kwargs = _get_kwargs(
        client=client,
        training_set_id=training_set_id,
        offset=offset,
        limit=limit,
    )

    response = httpx.get(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    training_set_id: str,
    offset: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> Optional[List[TrainingSetVersion]]:
    """ """

    return sync_detailed(
        client=client,
        training_set_id=training_set_id,
        offset=offset,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    training_set_id: str,
    offset: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> Response[List[TrainingSetVersion]]:
    kwargs = _get_kwargs(
        client=client,
        training_set_id=training_set_id,
        offset=offset,
        limit=limit,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.get(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    training_set_id: str,
    offset: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> Optional[List[TrainingSetVersion]]:
    """ """

    return (
        await asyncio_detailed(
            client=client,
            training_set_id=training_set_id,
            offset=offset,
            limit=limit,
        )
    ).parsed

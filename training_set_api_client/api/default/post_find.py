from typing import Any, Dict, List, Optional, Union

from http import HTTPStatus

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.training_set import TrainingSet
from ...models.training_set_filter import TrainingSetFilter
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    json_body: TrainingSetFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Dict[str, Any]:

    pass

    params: Dict[str, Any] = {}
    params["offset"] = offset

    params["limit"] = limit

    params["asc"] = asc

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": "/find",
        "json": json_json_body,
        "params": params,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[List["TrainingSet"]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = TrainingSet.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[List["TrainingSet"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: TrainingSetFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Response[List["TrainingSet"]]:
    """List TrainingSets

    Args:
        offset (Union[Unset, None, int]):
        limit (Union[Unset, None, int]):
        asc (Union[Unset, None, bool]):
        json_body (TrainingSetFilter):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['TrainingSet']]
    """

    kwargs = _get_kwargs(
        json_body=json_body,
        offset=offset,
        limit=limit,
        asc=asc,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: TrainingSetFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Optional[List["TrainingSet"]]:
    """List TrainingSets

    Args:
        offset (Union[Unset, None, int]):
        limit (Union[Unset, None, int]):
        asc (Union[Unset, None, bool]):
        json_body (TrainingSetFilter):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['TrainingSet']
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
        offset=offset,
        limit=limit,
        asc=asc,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: TrainingSetFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Response[List["TrainingSet"]]:
    """List TrainingSets

    Args:
        offset (Union[Unset, None, int]):
        limit (Union[Unset, None, int]):
        asc (Union[Unset, None, bool]):
        json_body (TrainingSetFilter):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['TrainingSet']]
    """

    kwargs = _get_kwargs(
        json_body=json_body,
        offset=offset,
        limit=limit,
        asc=asc,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: TrainingSetFilter,
    offset: Union[Unset, None, int] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    asc: Union[Unset, None, bool] = UNSET,
) -> Optional[List["TrainingSet"]]:
    """List TrainingSets

    Args:
        offset (Union[Unset, None, int]):
        limit (Union[Unset, None, int]):
        asc (Union[Unset, None, bool]):
        json_body (TrainingSetFilter):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['TrainingSet']
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
            offset=offset,
            limit=limit,
            asc=asc,
        )
    ).parsed

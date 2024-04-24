from typing import Any, Dict, Optional, Union

from http import HTTPStatus

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.training_set_version import TrainingSetVersion
from ...types import Response


def _get_kwargs(
    training_set_name: str,
    number: int,
) -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/{training_set_name}/{number}".format(
            training_set_name=training_set_name,
            number=number,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[TrainingSetVersion]:
    if response.status_code == HTTPStatus.OK:
        response_200 = TrainingSetVersion.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[TrainingSetVersion]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    training_set_name: str,
    number: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[TrainingSetVersion]:
    """Get TrainingSetVersion

    Args:
        training_set_name (str):
        number (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TrainingSetVersion]
    """

    kwargs = _get_kwargs(
        training_set_name=training_set_name,
        number=number,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    training_set_name: str,
    number: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[TrainingSetVersion]:
    """Get TrainingSetVersion

    Args:
        training_set_name (str):
        number (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TrainingSetVersion
    """

    return sync_detailed(
        training_set_name=training_set_name,
        number=number,
        client=client,
    ).parsed


async def asyncio_detailed(
    training_set_name: str,
    number: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[TrainingSetVersion]:
    """Get TrainingSetVersion

    Args:
        training_set_name (str):
        number (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TrainingSetVersion]
    """

    kwargs = _get_kwargs(
        training_set_name=training_set_name,
        number=number,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    training_set_name: str,
    number: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[TrainingSetVersion]:
    """Get TrainingSetVersion

    Args:
        training_set_name (str):
        number (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TrainingSetVersion
    """

    return (
        await asyncio_detailed(
            training_set_name=training_set_name,
            number=number,
            client=client,
        )
    ).parsed

from typing import Any, Dict, Optional, Union

from http import HTTPStatus

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.training_set import TrainingSet
from ...models.update_training_set_request import UpdateTrainingSetRequest
from ...types import Response


def _get_kwargs(
    training_set_name: str,
    *,
    json_body: UpdateTrainingSetRequest,
) -> Dict[str, Any]:

    pass

    json_json_body = json_body.to_dict()

    return {
        "method": "put",
        "url": "/{trainingSetName}".format(
            trainingSetName=training_set_name,
        ),
        "json": json_json_body,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[TrainingSet]:
    if response.status_code == HTTPStatus.OK:
        response_200 = TrainingSet.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[TrainingSet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    training_set_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: UpdateTrainingSetRequest,
) -> Response[TrainingSet]:
    """Update TrainingSet

    Args:
        training_set_name (str):
        json_body (UpdateTrainingSetRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TrainingSet]
    """

    kwargs = _get_kwargs(
        training_set_name=training_set_name,
        json_body=json_body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    training_set_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: UpdateTrainingSetRequest,
) -> Optional[TrainingSet]:
    """Update TrainingSet

    Args:
        training_set_name (str):
        json_body (UpdateTrainingSetRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TrainingSet
    """

    return sync_detailed(
        training_set_name=training_set_name,
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    training_set_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: UpdateTrainingSetRequest,
) -> Response[TrainingSet]:
    """Update TrainingSet

    Args:
        training_set_name (str):
        json_body (UpdateTrainingSetRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TrainingSet]
    """

    kwargs = _get_kwargs(
        training_set_name=training_set_name,
        json_body=json_body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    training_set_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: UpdateTrainingSetRequest,
) -> Optional[TrainingSet]:
    """Update TrainingSet

    Args:
        training_set_name (str):
        json_body (UpdateTrainingSetRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TrainingSet
    """

    return (
        await asyncio_detailed(
            training_set_name=training_set_name,
            client=client,
            json_body=json_body,
        )
    ).parsed

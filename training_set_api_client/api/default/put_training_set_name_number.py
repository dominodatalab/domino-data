from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.training_set_version import TrainingSetVersion
from ...models.update_training_set_version_request import UpdateTrainingSetVersionRequest
from ...types import Response


def _get_kwargs(
    training_set_name: str,
    number: int,
    *,
    client: Client,
    json_body: UpdateTrainingSetVersionRequest,
) -> Dict[str, Any]:
    url = "{}/{trainingSetName}/{number}".format(
        client.base_url, trainingSetName=training_set_name, number=number
    )

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
        "verify": client.verify_ssl,
    }


def _parse_response(*, response: httpx.Response) -> Optional[TrainingSetVersion]:
    if response.status_code == 200:
        response_200 = TrainingSetVersion.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[TrainingSetVersion]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    training_set_name: str,
    number: int,
    *,
    client: Client,
    json_body: UpdateTrainingSetVersionRequest,
) -> Response[TrainingSetVersion]:
    kwargs = _get_kwargs(
        training_set_name=training_set_name,
        number=number,
        client=client,
        json_body=json_body,
    )

    response = httpx.put(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    training_set_name: str,
    number: int,
    *,
    client: Client,
    json_body: UpdateTrainingSetVersionRequest,
) -> Optional[TrainingSetVersion]:
    """ """

    return sync_detailed(
        training_set_name=training_set_name,
        number=number,
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    training_set_name: str,
    number: int,
    *,
    client: Client,
    json_body: UpdateTrainingSetVersionRequest,
) -> Response[TrainingSetVersion]:
    kwargs = _get_kwargs(
        training_set_name=training_set_name,
        number=number,
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.put(**kwargs)

    return _build_response(response=response)


async def asyncio(
    training_set_name: str,
    number: int,
    *,
    client: Client,
    json_body: UpdateTrainingSetVersionRequest,
) -> Optional[TrainingSetVersion]:
    """ """

    return (
        await asyncio_detailed(
            training_set_name=training_set_name,
            number=number,
            client=client,
            json_body=json_body,
        )
    ).parsed

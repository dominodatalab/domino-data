from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.create_training_set_version_request import CreateTrainingSetVersionRequest
from ...models.training_set_version import TrainingSetVersion
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    training_set_name: str,
    json_body: CreateTrainingSetVersionRequest,
) -> Dict[str, Any]:
    url = "{}/{trainingSetName}/version".format(client.base_url, trainingSetName=training_set_name)

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
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
    *,
    client: Client,
    training_set_name: str,
    json_body: CreateTrainingSetVersionRequest,
) -> Response[TrainingSetVersion]:
    kwargs = _get_kwargs(
        client=client,
        training_set_name=training_set_name,
        json_body=json_body,
    )

    response = httpx.post(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    training_set_name: str,
    json_body: CreateTrainingSetVersionRequest,
) -> Optional[TrainingSetVersion]:
    """ """

    return sync_detailed(
        client=client,
        training_set_name=training_set_name,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    training_set_name: str,
    json_body: CreateTrainingSetVersionRequest,
) -> Response[TrainingSetVersion]:
    kwargs = _get_kwargs(
        client=client,
        training_set_name=training_set_name,
        json_body=json_body,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.post(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    training_set_name: str,
    json_body: CreateTrainingSetVersionRequest,
) -> Optional[TrainingSetVersion]:
    """ """

    return (
        await asyncio_detailed(
            client=client,
            training_set_name=training_set_name,
            json_body=json_body,
        )
    ).parsed

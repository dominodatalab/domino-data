from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.training_set_version import TrainingSetVersion
from ...models.update_training_set_version_request import UpdateTrainingSetVersionRequest
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    training_set_version_id: str,
    json_body: UpdateTrainingSetVersionRequest,
) -> Dict[str, Any]:
    url = "{}/version/{trainingSetVersionId}".format(client.base_url, trainingSetVersionId=training_set_version_id)

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
    training_set_version_id: str,
    json_body: UpdateTrainingSetVersionRequest,
) -> Response[TrainingSetVersion]:
    kwargs = _get_kwargs(
        client=client,
        training_set_version_id=training_set_version_id,
        json_body=json_body,
    )

    response = httpx.put(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    training_set_version_id: str,
    json_body: UpdateTrainingSetVersionRequest,
) -> Optional[TrainingSetVersion]:
    """ """

    return sync_detailed(
        client=client,
        training_set_version_id=training_set_version_id,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    training_set_version_id: str,
    json_body: UpdateTrainingSetVersionRequest,
) -> Response[TrainingSetVersion]:
    kwargs = _get_kwargs(
        client=client,
        training_set_version_id=training_set_version_id,
        json_body=json_body,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.put(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    training_set_version_id: str,
    json_body: UpdateTrainingSetVersionRequest,
) -> Optional[TrainingSetVersion]:
    """ """

    return (
        await asyncio_detailed(
            client=client,
            training_set_version_id=training_set_version_id,
            json_body=json_body,
        )
    ).parsed

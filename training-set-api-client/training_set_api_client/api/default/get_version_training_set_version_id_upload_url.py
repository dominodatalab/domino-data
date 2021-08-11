from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.training_set_version_url import TrainingSetVersionUrl
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    training_set_version_id: str,
) -> Dict[str, Any]:
    url = "{}/version/{trainingSetVersionId}/uploadUrl".format(
        client.base_url, trainingSetVersionId=training_set_version_id
    )

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[TrainingSetVersionUrl]:
    if response.status_code == 200:
        response_200 = TrainingSetVersionUrl.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[TrainingSetVersionUrl]:
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
) -> Response[TrainingSetVersionUrl]:
    kwargs = _get_kwargs(
        client=client,
        training_set_version_id=training_set_version_id,
    )

    response = httpx.get(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    training_set_version_id: str,
) -> Optional[TrainingSetVersionUrl]:
    """ """

    return sync_detailed(
        client=client,
        training_set_version_id=training_set_version_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    training_set_version_id: str,
) -> Response[TrainingSetVersionUrl]:
    kwargs = _get_kwargs(
        client=client,
        training_set_version_id=training_set_version_id,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.get(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    training_set_version_id: str,
) -> Optional[TrainingSetVersionUrl]:
    """ """

    return (
        await asyncio_detailed(
            client=client,
            training_set_version_id=training_set_version_id,
        )
    ).parsed

from typing import Any, Dict

import httpx

from ...client import Client
from ...types import Response


def _get_kwargs(
    training_set_name: str,
    *,
    client: Client,
) -> Dict[str, Any]:
    url = "{}/{trainingSetName}".format(client.base_url, trainingSetName=training_set_name)

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "verify": client.verify_ssl,
    }


def _build_response(*, response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=None,
    )


def sync_detailed(
    training_set_name: str,
    *,
    client: Client,
) -> Response[Any]:
    kwargs = _get_kwargs(
        training_set_name=training_set_name,
        client=client,
    )

    response = httpx.delete(
        **kwargs,
    )

    return _build_response(response=response)


async def asyncio_detailed(
    training_set_name: str,
    *,
    client: Client,
) -> Response[Any]:
    kwargs = _get_kwargs(
        training_set_name=training_set_name,
        client=client,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.delete(**kwargs)

    return _build_response(response=response)

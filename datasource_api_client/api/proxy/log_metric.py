from typing import Any, Dict

import httpx

from ...client import Client
from ...models.log_metric_m import LogMetricM
from ...models.log_metric_t import LogMetricT
from ...types import UNSET, Response


def _get_kwargs(
    *,
    client: Client,
    t: LogMetricT,
    b: int,
    m: LogMetricM,
) -> Dict[str, Any]:
    url = f"{client.base_url}/objectstore/metric"

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    json_t = t.value

    params["t"] = json_t

    params["b"] = b

    json_m = m.value

    params["m"] = json_m

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "head",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _build_response(*, response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=None,
    )


def sync_detailed(
    *,
    client: Client,
    t: LogMetricT,
    b: int,
    m: LogMetricM,
) -> Response[Any]:
    """Log metrics about file size read or written

    Args:
        t (LogMetricT):
        b (int):
        m (LogMetricM):

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        client=client,
        t=t,
        b=b,
        m=m,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


async def asyncio_detailed(
    *,
    client: Client,
    t: LogMetricT,
    b: int,
    m: LogMetricM,
) -> Response[Any]:
    """Log metrics about file size read or written

    Args:
        t (LogMetricT):
        b (int):
        m (LogMetricM):

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        client=client,
        t=t,
        b=b,
        m=m,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)

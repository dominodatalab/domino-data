from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.log_metric_m import LogMetricM
from ...models.log_metric_t import LogMetricT
from ...types import UNSET, Response


def _get_kwargs(
    *,
    t: LogMetricT,
    b: int,
    m: LogMetricM,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    json_t = t.value
    params["t"] = json_t

    params["b"] = b

    json_m = m.value
    params["m"] = json_m

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "head",
        "url": "/objectstore/metric",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Any]:
    if response.status_code == 200:
        return None
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    t: LogMetricT,
    b: int,
    m: LogMetricM,
) -> Response[Any]:
    """Log metrics about file size read or written

    Args:
        t (LogMetricT):
        b (int):
        m (LogMetricM):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        t=t,
        b=b,
        m=m,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    t: LogMetricT,
    b: int,
    m: LogMetricM,
) -> Response[Any]:
    """Log metrics about file size read or written

    Args:
        t (LogMetricT):
        b (int):
        m (LogMetricM):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        t=t,
        b=b,
        m=m,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)

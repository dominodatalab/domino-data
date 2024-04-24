from typing import Any, Dict, Optional, Union

from http import HTTPStatus

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.feature_store import FeatureStore
from ...types import Response


def _get_kwargs(
    feature_view_name: str,
) -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/{feature_view_name}/store".format(
            feature_view_name=feature_view_name,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[FeatureStore]:
    if response.status_code == HTTPStatus.OK:
        response_200 = FeatureStore.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[FeatureStore]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    feature_view_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[FeatureStore]:
    """Get feature store by feature view name

    Args:
        feature_view_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FeatureStore]
    """

    kwargs = _get_kwargs(
        feature_view_name=feature_view_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    feature_view_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[FeatureStore]:
    """Get feature store by feature view name

    Args:
        feature_view_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FeatureStore
    """

    return sync_detailed(
        feature_view_name=feature_view_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    feature_view_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[FeatureStore]:
    """Get feature store by feature view name

    Args:
        feature_view_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FeatureStore]
    """

    kwargs = _get_kwargs(
        feature_view_name=feature_view_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    feature_view_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[FeatureStore]:
    """Get feature store by feature view name

    Args:
        feature_view_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FeatureStore
    """

    return (
        await asyncio_detailed(
            feature_view_name=feature_view_name,
            client=client,
        )
    ).parsed

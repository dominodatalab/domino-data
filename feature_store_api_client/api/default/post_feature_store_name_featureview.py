from typing import Any, Dict, List, Optional

import httpx

from ...client import Client
from ...models.create_feature_views_request import CreateFeatureViewsRequest
from ...models.feature_view_dto import FeatureViewDto
from ...types import Response


def _get_kwargs(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureViewsRequest,
) -> Dict[str, Any]:
    url = "{}/{featureStoreName}/featureview".format(
        client.base_url, featureStoreName=feature_store_name
    )

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[List[FeatureViewDto]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = FeatureViewDto.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[List[FeatureViewDto]]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureViewsRequest,
) -> Response[List[FeatureViewDto]]:
    """Create FeatureViews

    Args:
        feature_store_name (str):
        json_body (CreateFeatureViewsRequest):

    Returns:
        Response[List[FeatureViewDto]]
    """

    kwargs = _get_kwargs(
        feature_store_name=feature_store_name,
        client=client,
        json_body=json_body,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureViewsRequest,
) -> Optional[List[FeatureViewDto]]:
    """Create FeatureViews

    Args:
        feature_store_name (str):
        json_body (CreateFeatureViewsRequest):

    Returns:
        Response[List[FeatureViewDto]]
    """

    return sync_detailed(
        feature_store_name=feature_store_name,
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureViewsRequest,
) -> Response[List[FeatureViewDto]]:
    """Create FeatureViews

    Args:
        feature_store_name (str):
        json_body (CreateFeatureViewsRequest):

    Returns:
        Response[List[FeatureViewDto]]
    """

    kwargs = _get_kwargs(
        feature_store_name=feature_store_name,
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    feature_store_name: str,
    *,
    client: Client,
    json_body: CreateFeatureViewsRequest,
) -> Optional[List[FeatureViewDto]]:
    """Create FeatureViews

    Args:
        feature_store_name (str):
        json_body (CreateFeatureViewsRequest):

    Returns:
        Response[List[FeatureViewDto]]
    """

    return (
        await asyncio_detailed(
            feature_store_name=feature_store_name,
            client=client,
            json_body=json_body,
        )
    ).parsed

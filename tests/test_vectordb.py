"""Test Domino customized Pinecone OpenAPI Configuration"""

import os

from domino_data.vectordb import (
    HEADER_DOMINO_DATASOURCE,
    HEADER_PINECONE_INDEX,
    DominoPineconeConfiguration,
    domino_pinecone3x_index_params,
    domino_pinecone3x_init_params,
)


def test_get_host_from_setting():
    test_data_source = "test_pine_cone"
    test_data_api_gateway = "http://test_domino_api_gateway:9999"

    domino_conf = DominoPineconeConfiguration(datasource=test_data_source)
    assert domino_conf.host == "http://api.pinecone.io"
    assert domino_conf.proxy == "http://127.0.0.1:8766"
    assert domino_conf.proxy_headers["X-Domino-Datasource"] == test_data_source

    os.environ["DOMINO_DATA_API_GATEWAY"] = test_data_api_gateway
    domino_conf = DominoPineconeConfiguration(datasource=test_data_source)
    assert domino_conf.host == f"http://api.pinecone.io"
    assert domino_conf.proxy == test_data_api_gateway
    assert domino_conf.proxy_headers["X-Domino-Datasource"] == test_data_source

    test_index = "test_index"
    test_environment = "test_environment"
    test_project = "test_project"
    host = domino_conf.get_host_from_settings(
        0,
        variables={
            "index_name": test_index,
            "project_name": test_project,
            "environment": test_environment,
        },
    )
    assert host == "http://api.pinecone.io"

    host = domino_conf.get_host_from_settings(None, variables={})
    assert host == f"http://api.pinecone.io"


def test_get_domino_pinecone3x_init_params():
    test_data_source = "test_pine_cone"
    os.environ["DOMINO_DATA_API_GATEWAY"] = "http://127.0.0.1:8766"
    init_params = domino_pinecone3x_init_params(test_data_source)
    assert init_params["host"] == "http://127.0.0.1:8766"
    assert init_params["api_key"] == "domino"
    assert init_params["additional_headers"][HEADER_DOMINO_DATASOURCE] == test_data_source


def test_get_domino_pinecone3x_index_params():
    test_data_source = "test_pine_cone"
    test_index_name = "semantic-search-fast"
    os.environ["DOMINO_DATA_API_GATEWAY"] = "http://127.0.0.1:8766"
    init_params = domino_pinecone3x_index_params(test_data_source, test_index_name)
    assert init_params["host"] == "http://127.0.0.1:8766"
    assert init_params["additional_headers"][HEADER_DOMINO_DATASOURCE] == test_data_source
    assert init_params["additional_headers"][HEADER_PINECONE_INDEX] == test_index_name

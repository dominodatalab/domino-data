"""Test Domino customized Pinecone OpenAPI Configuration"""

import os

from domino_data.vectordb import (
    HEADER_DOMINO_DATASOURCE,
    HEADER_PINECONE_INDEX,
    domino_pinecone3x_index_params,
    domino_pinecone3x_init_params,
)


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

"""Test Domino customized Pinecone OpenAPI Configuration"""
import os

from vector_dbs.pinecone.configuration import DominoConfiguration


def test_get_host_from_setting():
    test_data_source = "test_pine_cone"
    test_data_api_gateway = "http://test_domino_api_gateway:9999"

    domino_conf = DominoConfiguration(datasource=test_data_source)
    assert domino_conf.host == "http://unknown-unknown.svc.unknown.pinecone.io"
    assert domino_conf.proxy == "http://127.0.0.1:8766"
    assert domino_conf.proxy_headers["X-Domino-Datasource"] == test_data_source

    os.environ["DOMINO_DATA_API_GATEWAY"] = test_data_api_gateway
    domino_conf = DominoConfiguration(datasource=test_data_source)
    assert domino_conf.host == f"http://unknown-unknown.svc.unknown.pinecone.io"
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
    assert host == "http://test_index-test_project.svc.test_environment.pinecone.io"

    host = domino_conf.get_host_from_settings(None, variables={})
    assert host == f"http://unknown-unknown.svc.unknown.pinecone.io"

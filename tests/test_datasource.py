"""Datasource tests."""

import pytest

from domino_data_sdk.datasource import Client, ObjectStoreDatasource, QueryDatasource

DOMINO_TOKEN_FILE = "tests/domino_token"


@pytest.mark.vcr
def test_get_datasource():
    """Client can fetch an existing datasource."""
    client = Client()
    redshift_test = client.get_datasource("redshift_sdk_test")
    s3_test = client.get_datasource("s3-dev")

    assert isinstance(redshift_test, QueryDatasource)
    assert isinstance(s3_test, ObjectStoreDatasource)


@pytest.mark.vcr
def test_get_datasource_with_jwt(monkeypatch):
    """Client can fetch a datasource using JWT."""
    monkeypatch.delenv("DOMINO_USER_API_KEY")
    monkeypatch.setenv("DOMINO_TOKEN_FILE", DOMINO_TOKEN_FILE)

    client = Client()
    assert client.api_key is None
    assert client.token_file is not None

    client.get_datasource("redshift_sdk_test")


@pytest.mark.vcr
def test_get_datasource_does_not_exists():
    """Client raises an error when datasource does not exists."""
    with pytest.raises(Exception) as exc:
        Client().get_datasource("not-a-datasource")

    assert str(exc.value) == "Datasource with name not-a-datasource does not exist"

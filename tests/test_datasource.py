"""Datasource tests."""

import pytest

from domino_data_sdk import datasource as ds
from tests.conftest import DOMINO_TOKEN_FILE

# Get Datasource


@pytest.mark.vcr
def test_get_datasource():
    """Client can fetch an existing datasource."""
    client = ds.Client()
    redshift_test = client.get_datasource("redshift_sdk_test")
    s3_test = client.get_datasource("aduser-s3")

    assert isinstance(redshift_test, ds.QueryDatasource)
    assert isinstance(s3_test, ds.ObjectStoreDatasource)


@pytest.mark.vcr
def test_get_datasource_with_jwt(monkeypatch):
    """Client can fetch a datasource using JWT."""
    monkeypatch.delenv("DOMINO_USER_API_KEY")
    monkeypatch.setenv("DOMINO_TOKEN_FILE", DOMINO_TOKEN_FILE)

    client = ds.Client()
    assert client.api_key is None
    assert client.token_file is not None

    client.get_datasource("redshift_sdk_test")


@pytest.mark.vcr
def test_get_datasource_does_not_exists():
    """Client raises an error when datasource does not exists."""
    with pytest.raises(Exception) as exc:
        ds.Client().get_datasource("not-a-datasource")

    assert str(exc.value) == "Datasource with name not-a-datasource does not exist"


@pytest.mark.vcr
def test_get_datasource_without_access():
    """Client raises an error when user does not have access to datasource."""
    with pytest.raises(Exception) as exc:
        ds.Client(api_key="NOTAKEY", token_file=None).get_datasource("aduser-s3")

    assert str(exc.value) == "Your role does not authorize you to perform this action"


# Get Signed URL


@pytest.mark.vcr
def test_client_get_key_url():
    """Client can retrieve a signed URL of an object in a datasource."""
    client = ds.Client()
    s3d = client.get_datasource("aduser-s3")

    url = client.get_key_url(s3d.identifier, "akey", True, {}, {})

    assert s3d.config["bucket"] in url
    assert s3d.config["region"] in url
    assert "akey" in url


@pytest.mark.vcr
def test_client_get_key_url_with_override():
    """Client can retrieve a signed URL when overriding settings of a datasource."""
    client = ds.Client()
    s3d = client.get_datasource("aduser-s3")

    url = client.get_key_url(s3d.identifier, "akey", True, {"region": "us-east-1"}, {})

    assert s3d.config["region"] not in url
    assert "us-east-1" in url


@pytest.mark.vcr
def test_client_get_key_url_returns_not_found():
    """Client gets an error when getting url for a datasource that does not exists."""
    client = ds.Client()

    with pytest.raises(Exception) as exc:
        client.get_key_url("6167705cfe005a517943cc10", "akey", True, {}, {})

    assert str(exc.value) == "credentialsError: credentials response was empty"


# List Keys


@pytest.mark.vcr
def test_client_list_keys_in_object_store():
    """Client get list of keys in a datasource."""
    client = ds.Client()
    s3d = client.get_datasource("aduser-s3")

    keys = client.list_keys(s3d.identifier, "", {}, {})

    assert keys == ["diabetes.csv", "diabetes_changed.csv"]

    keys = client.list_keys(s3d.identifier, "diabetes_", {}, {})

    assert keys == ["diabetes_changed.csv"]


@pytest.mark.vcr
def test_client_list_keys_returns_error():
    """Client get list of keys in a datasource."""
    client = ds.Client()
    s3d = client.get_datasource("aduser-s3")

    with pytest.raises(Exception) as exc:
        client.list_keys(s3d.identifier, "", {"bucket": "notreal"}, {})

    # TODO this error is a mess, fix after proxy
    assert "incorrect region, the bucket is not in 'us-west-2' region" in str(exc.value)


# Config


def test_config_returns_overrides():
    """Config returns override for changed fields only."""

    @ds.attr.s(auto_attribs=True)
    class DummyConfig(ds.Config):
        """Dummy Config"""

        # pylint: disable=protected-access

        database: ds.Optional[str] = ds._config(elem=ds.ConfigElem.DATABASE)
        username: ds.Optional[str] = ds._cred(elem=ds.CredElem.USERNAME)

    dum1 = DummyConfig(database="hello", username="newuser")
    dum2 = DummyConfig(username="newuser")
    dum3 = DummyConfig(database="hello")
    dum4 = DummyConfig()

    assert dum1.config() == {"database": "hello"}
    assert dum1.credential() == {"username": "newuser"}

    assert dum2.config() == {}
    assert dum2.credential() == {"username": "newuser"}

    assert dum3.config() == {"database": "hello"}
    assert dum3.credential() == {}

    assert dum4.config() == {}
    assert dum4.credential() == {}


def test_redshift_config():
    """Redshift config serializes to expected keys."""

    red = ds.RedshiftConfig(database="dev2", username="awsadmin", password="protec")

    assert red.config() == {"database": "dev2"}
    assert red.credential() == {"username": "awsadmin", "password": "protec"}


def test_snowflake_config():
    """Snowflake config serializes to expected keys."""

    snow = ds.SnowflakeConfig(
        database="winter",
        schema="private",
        warehouse="xxl",
        role="superadmin",
        username="awsadmin",
        password="protec",
    )

    assert snow.config() == {
        "database": "winter",
        "schema": "private",
        "warehouse": "xxl",
        "role": "superadmin",
    }
    assert snow.credential() == {"username": "awsadmin", "password": "protec"}


def test_s3_config():
    """S3 config serializes to expected keys."""

    s3c = ds.S3Config(
        bucket="sceau",
        region="midi-pyrenees",
        aws_access_key_id="identite",
        aws_secret_access_key="cle-secrete",
    )

    assert s3c.config() == {"bucket": "sceau", "region": "midi-pyrenees"}
    assert s3c.credential() == {"username": "identite", "password": "cle-secrete"}


# Object datasource

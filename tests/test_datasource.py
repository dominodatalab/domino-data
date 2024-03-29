"""Datasource tests."""

import io
import json

import httpx
import pyarrow
import pytest

from domino_data import configuration_gen as ds_gen
from domino_data import data_sources as ds

# Get Datasource


@pytest.mark.vcr
def test_get_datasource():
    """Client can fetch an existing datasource."""
    client = ds.DataSourceClient()
    redshift_test = client.get_datasource("redshift_sdk_test")
    s3_test = client.get_datasource("aduser-s3")

    assert isinstance(redshift_test, ds.TabularDatasource)
    assert isinstance(s3_test, ds.ObjectStoreDatasource)


@pytest.mark.vcr
def test_get_datasource_with_jwt(monkeypatch):
    """Client can fetch a datasource using JWT."""
    monkeypatch.delenv("DOMINO_USER_API_KEY")

    client = ds.DataSourceClient()
    assert client.api_key is None
    assert client.token_file is not None

    client.get_datasource("redshift_sdk_test")


@pytest.mark.vcr
def test_get_datasource_does_not_exists():
    """Client raises an error when datasource does not exists."""
    with pytest.raises(
        Exception,
        match="Datasource with name not-a-datasource does not exist",
    ):
        ds.DataSourceClient().get_datasource("not-a-datasource")


@pytest.mark.vcr
def test_get_datasource_without_access():
    """Client raises an error when user does not have access to datasource."""
    with pytest.raises(
        Exception,
        match="Your role does not authorize you to perform this action",
    ):
        ds.DataSourceClient(
            api_key="NOTAKEY",
            token_file=None,
        ).get_datasource("aduser-s3")


# Get Signed URL


@pytest.mark.vcr
def test_client_get_key_url():
    """Client can retrieve a signed URL of an object in a datasource."""
    client = ds.DataSourceClient()
    s3d = client.get_datasource("aduser-s3")

    url = client.get_key_url(s3d.identifier, "akey", True, {}, {})

    assert s3d.config["bucket"] in url
    assert s3d.config["region"] in url
    assert "akey" in url


@pytest.mark.vcr
def test_client_get_key_url_with_override():
    """Client can retrieve a signed URL when overriding settings of a datasource."""
    client = ds.DataSourceClient()
    s3d = client.get_datasource("aduser-s3")

    url = client.get_key_url(s3d.identifier, "akey", True, {"region": "us-east-1"}, {})

    assert s3d.config["region"] not in url
    assert "us-east-1" in url


@pytest.mark.vcr
def test_client_get_key_url_returns_not_found():
    """Client gets an error when getting url for a datasource that does not exists."""
    client = ds.DataSourceClient()

    with pytest.raises(
        Exception,
        match="credentialsError: credentials response was empty",
    ):
        client.get_key_url("6167705cfe005a517943cc10", "akey", True, {}, {})


# List Keys


@pytest.mark.vcr
def test_client_list_keys_in_object_store():
    """Client get list of keys in a datasource."""
    client = ds.DataSourceClient()
    s3d = client.get_datasource("aduser-s3")

    keys = client.list_keys(s3d.identifier, "", 1000, {}, {})

    assert keys == ["diabetes.csv", "diabetes_changed.csv"]

    keys = client.list_keys(s3d.identifier, "", 1, {}, {})

    assert keys == ["diabetes_changed.csv"]

    keys = client.list_keys(s3d.identifier, "diabetes_", 1000, {}, {})

    assert keys == ["diabetes_changed.csv"]


@pytest.mark.vcr
def test_client_list_keys_without_jwt(monkeypatch):
    """Client is defensive against missing JWT file."""
    monkeypatch.setenv("DOMINO_TOKEN_FILE", "notafile")
    client = ds.DataSourceClient()
    s3d = client.get_datasource("aduser-s3")

    keys = client.list_keys(s3d.identifier, "", 1000, {}, {})

    assert keys


@pytest.mark.vcr
def test_client_list_keys_returns_error():
    """Client get list of keys in a datasource."""
    client = ds.DataSourceClient()
    s3d = client.get_datasource("aduser-s3")

    with pytest.raises(
        Exception,
        match="incorrect region, the bucket is not in 'us-west-2' region",
    ):
        client.list_keys(s3d.identifier, "", 1000, {"bucket": "notreal"}, {})


# Log Metric


@pytest.mark.vcr
def test_client_log_metric_read():
    """Client log objectstore metric in read mode."""
    client = ds.DataSourceClient()

    client._log_metric("S3Config", 1000, False)  # pylint: disable=protected-access


@pytest.mark.vcr
def test_client_log_metric_write():
    """Client log objectstore metric in write mode."""
    client = ds.DataSourceClient()

    client._log_metric("S3Config", 1000, True)  # pylint: disable=protected-access


def test_client_wrong_type_log_nothing():
    """Client log nothing if the datasource type is not valid."""
    client = ds.DataSourceClient()

    client._log_metric(  # pylint: disable=protected-access
        "RedshiftConfig",
        1000,
        False,
    )


# Execute


def test_client_execute(flight_server):
    """Client can execute a query."""

    table = pyarrow.Table.from_pydict({})

    def callback(_, ticket):
        tkt = json.loads(ticket.ticket.decode("utf-8"))
        assert tkt["datasourceId"] == "id"
        assert tkt["sqlQuery"] == "SELECT 1"
        assert tkt["configOverwrites"] == {}
        assert tkt["credentialOverwrites"] == {}
        return pyarrow.flight.RecordBatchStream(table)

    flight_server.do_get_callback = callback
    client = ds.DataSourceClient()
    result = client.execute("id", "SELECT 1", {}, {})

    assert isinstance(result, ds.Result)
    assert result.statement == "SELECT 1"
    assert result.client == client


def test_client_execute_result_to_pandas(flight_server):
    """Client returns a valid result with data."""

    table = pyarrow.Table.from_pydict(
        {
            "number": [7, 14, 21],
            "name": ["squirtle", "kakuna", "spearow"],
        }
    )

    def callback(_, __):
        return pyarrow.flight.RecordBatchStream(table)

    flight_server.do_get_callback = callback
    result = ds.DataSourceClient().execute("id", "SELECT 1", {}, {})
    dataframe = result.to_pandas()

    assert dataframe.at[0, "name"] == "squirtle"
    assert dataframe.at[1, "name"] == "kakuna"
    assert dataframe.at[2, "name"] == "spearow"
    assert dataframe.at[0, "number"] == 7
    assert dataframe.at[1, "number"] == 14
    assert dataframe.at[2, "number"] == 21


def test_client_execute_result_to_parquet(flight_server, tmp_path):
    """Client returns a valid result with data."""

    tmp_file = tmp_path / "file.parquet"
    table = pyarrow.Table.from_pydict(
        {
            "number": [7, 14, 21],
            "name": ["squirtle", "kakuna", "spearow"],
        }
    )

    def callback(_, __):
        return pyarrow.flight.RecordBatchStream(table)

    flight_server.do_get_callback = callback
    result = ds.DataSourceClient().execute("id", "SELECT 1", {}, {})
    result.to_parquet(tmp_file.absolute())

    dataframe = ds.pandas.read_parquet(tmp_file.absolute(), engine="pyarrow")

    assert dataframe.at[0, "name"] == "squirtle"
    assert dataframe.at[1, "name"] == "kakuna"
    assert dataframe.at[2, "name"] == "spearow"
    assert dataframe.at[0, "number"] == 7
    assert dataframe.at[1, "number"] == 14
    assert dataframe.at[2, "number"] == 21


def test_client_execute_unpack_exceptions(flight_server):
    """Client raises prettier exceptions."""

    def callback(context, _):
        raise pyarrow.flight.FlightInternalError("is bad")

    flight_server.do_get_callback = callback

    with pytest.raises(Exception, match="is bad. Detail: Internal"):
        ds.DataSourceClient().execute("id", "SELECT 1", {}, {})


def test_client_retries_on_unauthenticated(flight_server):
    """Client retries do_get when getting authentication errors."""

    counter = 0
    table = pyarrow.Table.from_pydict({})

    def callback(_, __):
        nonlocal counter
        counter += 1
        if counter >= 2:
            return pyarrow.flight.RecordBatchStream(table)
        raise pyarrow.flight.FlightUnauthenticatedError("is not you")

    flight_server.do_get_callback = callback

    ds.DataSourceClient().execute("id", "SELECT 1", {}, {})

    assert counter == 2


# Config


def test_config_returns_overrides():
    """Config returns override for changed fields only."""

    @ds.attr.s(auto_attribs=True)
    class DummyConfig(ds.Config):
        """Dummy Config"""

        # pylint: disable=protected-access

        database: ds.Optional[str] = ds_gen._config(elem=ds_gen.ConfigElem.DATABASE)
        username: ds.Optional[str] = ds_gen._cred(elem=ds_gen.CredElem.USERNAME)

    dum1 = DummyConfig(database="hello", username="newuser")
    dum2 = DummyConfig(username="newuser")
    dum3 = DummyConfig(database="hello")
    dum4 = DummyConfig()

    assert dum1.config() == {"database": "hello"}
    assert dum1.credential() == {"username": "newuser"}

    assert not dum2.config()
    assert dum2.credential() == {"username": "newuser"}

    assert dum3.config() == {"database": "hello"}
    assert not dum3.credential()

    assert not dum4.config()
    assert not dum4.credential()


def test_adls_config():
    """ADLS config serializes to expected keys."""

    adls = ds.ADLSConfig(container="storage", access_key="access")

    assert adls.config() == {"bucket": "storage"}
    assert adls.credential() == {"accessKey": "access"}


def test_azure_blob_storage_config():
    """AzureBlobStorage config serializes to expected keys."""

    azure_blob_storage = ds.AzureBlobStorageConfig(container="storage", access_key="access")

    assert azure_blob_storage.config() == {"bucket": "storage"}
    assert azure_blob_storage.credential() == {"accessKey": "access"}


def test_mysql_config():
    """MySQL config serializes to expected keys."""

    mysql = ds.MySQLConfig(database="dev2", username="awsadmin", password="protec")

    assert mysql.config() == {"database": "dev2"}
    assert mysql.credential() == {"username": "awsadmin", "password": "protec"}


def test_postgresql_config():
    """PostgreSQL config serializes to expected keys."""

    postgres = ds.PostgreSQLConfig(
        database="dev2",
        username="awsadmin",
        password="protec",
    )

    assert postgres.config() == {"database": "dev2"}
    assert postgres.credential() == {"username": "awsadmin", "password": "protec"}


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


def test_oracle_config():
    """Oracle config serializes to expected keys."""
    orcl = ds.OracleConfig(database="dev2", username="awsadmin", password="protec")

    assert orcl.config() == {"database": "dev2"}
    assert orcl.credential() == {"username": "awsadmin", "password": "protec"}


def test_s3_config():
    """S3 config serializes to expected keys."""
    s3c = ds.S3Config(
        bucket="sceau",
        region="midi-pyrenees",
        aws_access_key_id="identite",
        aws_secret_access_key="cle-secrete",
    )

    assert s3c.config() == {"bucket": "sceau", "region": "midi-pyrenees"}
    assert s3c.credential() == {"accessKeyID": "identite", "secretAccessKey": "cle-secrete"}


def test_sqlserver_config():
    """SQL Server config serializes to expected keys."""

    sqlServer = ds.SQLServerConfig(database="dev2", username="awsadmin", password="protec")

    assert sqlServer.config() == {"database": "dev2"}
    assert sqlServer.credential() == {"username": "awsadmin", "password": "protec"}


def test_gcp_config():
    """GCP config serializes to expected keys."""

    gcsc = ds.GCSConfig(
        bucket="cestino",
        private_key_json="chiave-segreta",
    )

    assert gcsc.config() == {"bucket": "cestino"}
    assert gcsc.credential() == {"privateKey": "chiave-segreta"}


# Object and object datasource


@pytest.mark.vcr
def test_object_store_get():
    """Object datasource can get content as binary."""
    s3d = ds.DataSourceClient().get_datasource("aduser-s3")
    s3d = ds.cast(ds.ObjectStoreDatasource, s3d)

    content = s3d.get("diabetes.csv")

    assert content[0:30] == b"Pregnancies,Glucose,BloodPress"


@pytest.mark.vcr
def test_object_store_put():
    """Object datasource can put binary content to object."""
    s3d = ds.DataSourceClient().get_datasource("aduser-s3")
    s3d = ds.cast(ds.ObjectStoreDatasource, s3d)

    s3d.put("gabrieltest.csv", b"col1,col2\r\ncell11,cell12")


@pytest.mark.vcr
def test_object_store_list_objects():
    """Object datasource can list objects."""
    s3d = ds.DataSourceClient().get_datasource("aduser-s3")
    s3d = ds.cast(ds.ObjectStoreDatasource, s3d)

    objs = s3d.list_objects("gab")

    assert isinstance(objs[0], ds._Object)  # pylint: disable=protected-access
    assert objs[0].key == "gabrieltest.csv"


@pytest.mark.vcr
def test_object_store_upload_file(tmp_path):
    """Object datasource can put file content to object."""
    s3d = ds.DataSourceClient().get_datasource("aduser-s3")
    s3d = ds.cast(ds.ObjectStoreDatasource, s3d)

    tmp_file = tmp_path / "file.txt"
    tmp_file.write_bytes(b"testcontent")

    s3d.upload_file("gabrieltest.csv", tmp_file.absolute())


@pytest.mark.vcr
def test_object_store_upload_fileojb():
    """Object datasource can put fileojb content to object."""
    s3d = ds.DataSourceClient().get_datasource("aduser-s3")
    s3d = ds.cast(ds.ObjectStoreDatasource, s3d)

    fileobj = io.BytesIO(b"testcontent")

    s3d.upload_fileobj("gabrieltest.csv", fileobj)


def test_object_store_download_file(env, respx_mock, datafx, tmp_path):
    """Object datasource can download a blob content into a file."""
    env.delenv("DOMINO_API_PROXY")
    mock_content = b"I am a blob"
    mock_file = tmp_path / "file.txt"
    respx_mock.get("http://token-proxy/access-token").mock(
        return_value=httpx.Response(200, content=b"jwt")
    )
    respx_mock.get("http://domino/v4/datasource/name/s3").mock(
        return_value=httpx.Response(200, json=datafx("s3")),
    )
    respx_mock.post("http://proxy/objectstore/key").mock(
        return_value=httpx.Response(200, json="http://s3/url"),
    )
    respx_mock.get("http://s3/url").mock(
        return_value=httpx.Response(200, content=mock_content),
    )

    s3d = ds.DataSourceClient().get_datasource("s3")
    s3d = ds.cast(ds.ObjectStoreDatasource, s3d)
    s3d.download_file("file.png", mock_file.absolute())

    assert mock_file.read_bytes() == mock_content


def test_object_store_download_fileobj(env, respx_mock, datafx):
    """Object datasource can download a blob content into a file."""
    env.delenv("DOMINO_API_PROXY")
    mock_content = b"I am a blob"
    mock_fileobj = io.BytesIO()
    respx_mock.get("http://token-proxy/access-token").mock(
        return_value=httpx.Response(200, content=b"jwt")
    )
    respx_mock.get("http://domino/v4/datasource/name/s3").mock(
        return_value=httpx.Response(200, json=datafx("s3")),
    )
    respx_mock.post("http://proxy/objectstore/key").mock(
        return_value=httpx.Response(200, json="http://s3/url"),
    )
    respx_mock.get("http://s3/url").mock(
        return_value=httpx.Response(200, content=mock_content),
    )

    s3d = ds.DataSourceClient().get_datasource("s3")
    s3d = ds.cast(ds.ObjectStoreDatasource, s3d)
    s3d.download_fileobj("file.png", mock_fileobj)

    assert mock_fileobj.getvalue() == mock_content


@pytest.mark.usefixtures("env")
def test_credential_override_with_awsiamrole(respx_mock, datafx, monkeypatch):
    """Object datasource can list and get key url using AWSIAMRole."""
    monkeypatch.delenv("DOMINO_API_PROXY")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "tests/data/aws_credentials")
    respx_mock.get("http://domino/v4/datasource/name/s3").mock(
        return_value=httpx.Response(200, json=datafx("s3_awsiamrole")),
    )
    respx_mock.post("http://proxy/objectstore/list").mock(return_value=httpx.Response(200, json=[]))
    respx_mock.post("http://proxy/objectstore/key").mock(return_value=httpx.Response(200, json=""))

    s3d = ds.DataSourceClient().get_datasource("s3")
    s3d = ds.cast(ds.ObjectStoreDatasource, s3d)
    s3d.list_objects()
    s3d.get_key_url("")

    get_key_url_request, _ = respx_mock.calls[-1]
    list_request, _ = respx_mock.calls[-2]
    list_creds = json.loads(list_request.content)["credentialOverwrites"]
    get_key_url_creds = json.loads(get_key_url_request.content)["credentialOverwrites"]

    # values in file
    assert list_creds["accessKeyID"] == "AKIAIOSFODNN7EXAMPLE"
    assert list_creds["secretAccessKey"] == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    assert list_creds["sessionToken"] == "FwoGZXIvYXdzENr//////////verylongandbig"
    assert get_key_url_creds["accessKeyID"] == "AKIAIOSFODNN7EXAMPLE"
    assert get_key_url_creds["secretAccessKey"] == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


@pytest.mark.usefixtures("env")
def test_credential_override_with_awsiamrole_file_does_not_exist(respx_mock, datafx, monkeypatch):
    """AWSIAMRole workflow should return error if credential file not present"""
    monkeypatch.delenv("DOMINO_API_PROXY")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "notarealfile")

    respx_mock.get("http://domino/v4/datasource/name/s3").mock(
        return_value=httpx.Response(200, json=datafx("s3_awsiamrole")),
    )
    respx_mock.post("http://proxy/objectstore/list").mock(return_value=httpx.Response(200, json=[]))
    respx_mock.post("http://proxy/objectstore/key").mock(return_value=httpx.Response(200, json=""))

    s3d = ds.DataSourceClient().get_datasource("s3")
    s3d = ds.cast(ds.ObjectStoreDatasource, s3d)
    with pytest.raises(ds.DominoError):
        s3d.list_objects()
    with pytest.raises(ds.DominoError):
        s3d.get_key_url("")


def test_credential_override_with_oauth(datafx, flight_server, monkeypatch, respx_mock):
    """Client can execute a Snowflake query using OAuth"""
    monkeypatch.delenv("DOMINO_API_PROXY")
    monkeypatch.setenv("DOMINO_TOKEN_FILE", "tests/data/domino_jwt")

    table = pyarrow.Table.from_pydict({})
    respx_mock.get("http://domino/v4/datasource/name/snowflake").mock(
        return_value=httpx.Response(200, json=datafx("snowflake_oauth")),
    )

    def callback(_, ticket):
        tkt = json.loads(ticket.ticket.decode("utf-8"))
        assert tkt["credentialOverwrites"] == {"token": "token, jeton, gettone"}
        return pyarrow.flight.RecordBatchStream(table)

    flight_server.do_get_callback = callback
    snowflake_ds = ds.DataSourceClient().get_datasource("snowflake")
    snowflake_ds = ds.cast(ds.TabularDatasource, snowflake_ds)
    snowflake_ds.query("SELECT 1")


def test_credential_override_with_oauth_file_does_not_exist(
    datafx, flight_server, monkeypatch, respx_mock
):
    """Client gets an error if token not present using OAuth"""
    monkeypatch.delenv("DOMINO_API_PROXY")
    monkeypatch.setenv("DOMINO_TOKEN_FILE", "notarealfile")

    table = pyarrow.Table.from_pydict({})
    respx_mock.get("http://domino/v4/datasource/name/snowflake").mock(
        return_value=httpx.Response(200, json=datafx("snowflake_oauth")),
    )

    def callback(_):
        return pyarrow.flight.RecordBatchStream(table)

    flight_server.do_get_callback = callback
    snowflake_ds = ds.DataSourceClient().get_datasource("snowflake")
    snowflake_ds = ds.cast(ds.TabularDatasource, snowflake_ds)
    with pytest.raises(ds.DominoError):
        snowflake_ds.query("SELECT 1")


def test_client_uses_token_url_api(env, respx_mock, flight_server, datafx):
    """Verify client uses token API to get JWT."""
    env.delenv("DOMINO_USER_API_KEY")
    env.delenv("DOMINO_TOKEN_FILE")

    table = pyarrow.Table.from_pydict({})
    respx_mock.get("http://token-proxy/access-token").mock(
        return_value=httpx.Response(200, content=b"theapijwt")
    )

    def do_get_callback(_, ticket):
        tkt = json.loads(ticket.ticket.decode("utf-8"))
        assert tkt["credentialOverwrites"] == {"token": "theapijwt"}
        return pyarrow.flight.RecordBatchStream(table)

    def get_datasource(request):
        assert request.headers["authorization"] == "Bearer theapijwt"
        return httpx.Response(200, json=datafx("snowflake_oauth"))

    respx_mock.get("http://token-proxy/v4/datasource/name/snowflake").mock(
        side_effect=get_datasource
    )
    flight_server.do_get_callback = do_get_callback

    snow = ds.DataSourceClient().get_datasource("snowflake")
    snow = ds.cast(ds.TabularDatasource, snow)
    snow.query("SELECT 1")


def test_get_datasource_error(env, respx_mock, monkeypatch):
    """Client gets an error if fails to get the data source"""
    monkeypatch.delenv("DOMINO_API_PROXY")

    respx_mock.get("http://domino/v4/datasource/name/snowflake").mock(
        return_value=httpx.Response(503),
    )

    with pytest.raises(Exception) as exc_info:
        ds.DataSourceClient().get_datasource("snowflake")
        assert (
            str(exc_info) == "Received unexpected response while getting data source: "
            "Response(status_code=503, content=b'', headers=Headers({}), parsed=None)"
        )

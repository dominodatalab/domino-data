"""pytest fixtures and configuration."""

import json

import pyarrow
import pytest

# TODO This method is deprecated and should be refactored using `env`
# and respx mocked APIs

# Change the following values if you want to record new cassettes:

# API Key user needs to have access to 2 datasources:
#    - redshift_sdk_test (redshift)
#    - aduser-s3 (s3)
DOMINO_USER_API_KEY = "b9b339d163152218be8982769fec897561a57888aca799de328d3643e5d74148"
DOMINO_API_HOST = "https://mcetin5238.workbench-accessdata-team-sandbox.domino.tech"

# You need to run:
# `kubectl port-forward -n <platform-ns> svc/datasource-proxy 8000:80`
# `kubectl port-forward -n <platform-ns> svc/datasource-proxy 8080:8080`
DOMINO_DATASOURCE_PROXY_HOST = "http://localhost:8000"
DOMINO_DATASOURCE_PROXY_FLIGHT_HOST = "grpc://localhost:8080"

# Find a valid token and copy/paste the value in the following file
DOMINO_TOKEN_FILE = "tests/domino_token"


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """Set the right environment variables for recorded tests."""
    monkeypatch.setenv("DOMINO_API_HOST", DOMINO_API_HOST)
    monkeypatch.setenv("DOMINO_TOKEN_FILE", DOMINO_TOKEN_FILE)
    monkeypatch.setenv("DOMINO_USER_API_KEY", DOMINO_USER_API_KEY)
    monkeypatch.setenv("DOMINO_DATASOURCE_PROXY_HOST", DOMINO_DATASOURCE_PROXY_HOST)
    monkeypatch.setenv(
        "DOMINO_DATASOURCE_PROXY_FLIGHT_HOST",
        DOMINO_DATASOURCE_PROXY_FLIGHT_HOST,
    )
    monkeypatch.setenv("DOMINO_PROJECT_ID", "616f201f45a10655afeaaf9f")


@pytest.fixture
def flight_server(env):
    """Set a dummy flight server to test do_get."""

    class FlightServer(pyarrow.flight.FlightServerBase):
        """Dummy flight server."""

        def do_get_callback(self, context, ticket):
            """To be replaced"""
            raise NotImplementedError

        def do_get(self, context, ticket):
            """Dummy method."""
            return self.do_get_callback(context, ticket)

    server = FlightServer(location="grpc://localhost:8080")

    yield server

    server.shutdown()


@pytest.fixture
def training_set_dir(tmpdir, monkeypatch):
    """Set the right environment variables for training sets."""
    monkeypatch.setenv("DOMINO_TRAINING_SET_PATH", str(tmpdir))


@pytest.fixture
def env(monkeypatch):
    """Set basic environment variables for mocked tests."""
    monkeypatch.setenv("DOMINO_API_HOST", "http://domino")
    monkeypatch.setenv("DOMINO_API_PROXY", "token-proxy")
    monkeypatch.setenv("DOMINO_TOKEN_FILE", "tests/domino_token")
    monkeypatch.setenv("DOMINO_USER_API_KEY", "api-key")
    monkeypatch.setenv("DOMINO_DATASOURCE_PROXY_HOST", "http://proxy")
    monkeypatch.setenv("DOMINO_DATASOURCE_PROXY_FLIGHT_HOST", "grpc://localhost:8080")
    monkeypatch.setenv("DOMINO_PROJECT_ID", "project-id")
    yield monkeypatch


@pytest.fixture
def datafx():
    """Load an external JSON file as data fixture."""

    def _load_json_file(filename):
        with open(f"tests/data/{filename}.json", "rb") as file:
            return json.loads(file.read())

    return _load_json_file

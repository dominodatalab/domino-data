"""pytest fixtures and configuration."""

import pytest

# Change the following values if you want to record new cassettes:

# API Key user needs to have access to 2 datasources:
#    - redshift_sdk_test (redshift)
#    - aduser-s3 (s3)
DOMINO_USER_API_KEY = "b9b339d163152218be8982769fec897561a57888aca799de328d3643e5d74148"
DOMINO_API_HOST = "https://mcetin5238.workbench-accessdata-team-sandbox.domino.tech"

# You need to run `kubectl port-forward -n <platform-ns> svc/datasource-proxy 8000:80`
DOMINO_DATASOURCE_PROXY_HOST = "http://localhost:8000"
DOMINO_DATASOURCE_PROXY_FLIGHT_HOST = "grpc://localhost:8080"

# Find a valid token and copy/paste the value in the following file
DOMINO_TOKEN_FILE = "tests/domino_token"


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """Set the right environment variables for recorded tests."""
    monkeypatch.setenv("DOMINO_API_HOST", DOMINO_API_HOST)
    monkeypatch.setenv("DOMINO_USER_API_KEY", DOMINO_USER_API_KEY)
    monkeypatch.setenv("DOMINO_DATASOURCE_PROXY_HOST", DOMINO_DATASOURCE_PROXY_HOST)
    monkeypatch.setenv(
        "DOMINO_DATASOURCE_PROXY_FLIGHT_HOST",
        DOMINO_DATASOURCE_PROXY_FLIGHT_HOST,
    )

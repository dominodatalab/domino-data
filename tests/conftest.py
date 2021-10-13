"""pytest fixtures and configuration."""

import pytest

DOMINO_USER_API_KEY = "951df294607b2c0c3b91f0dc9daf84c1c380f0d0e28250b18ca93926f38f26ff"
DOMINO_API_HOST = "https://mcetin4647.workbench-accessdata-team-sandbox.domino.tech"


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """Set the right environment variables for recorded tests."""
    monkeypatch.setenv("DOMINO_API_HOST", DOMINO_API_HOST)
    monkeypatch.setenv("DOMINO_USER_API_KEY", DOMINO_USER_API_KEY)

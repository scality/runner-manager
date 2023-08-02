import pytest
from fastapi.testclient import TestClient

from runner_manager.main import app


@pytest.fixture(scope="function")
def fastapp():
    fastapp = app
    fastapp.dependency_overrides = {}
    return fastapp


@pytest.fixture(scope="function")
def client(fastapp):
    client = TestClient(fastapp)
    return client

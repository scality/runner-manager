from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, settings

from runner_manager.main import app

settings.register_profile(
    "api",
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=5,
    deadline=timedelta(milliseconds=500),
)

settings.load_profile("api")


@pytest.fixture(scope="function")
def fastapp():
    fastapp = app
    fastapp.dependency_overrides = {}
    return fastapp


@pytest.fixture()
def client(fastapp):
    client = TestClient(fastapp)
    return client

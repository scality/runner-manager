import os

import pytest
from fastapi.testclient import TestClient

from runner_manager.main import app
from runner_manager.models.settings import Settings


@pytest.fixture(scope="function")
def fastapp():
    fastapp = app
    fastapp.dependency_overrides = {}
    return fastapp


@pytest.fixture(scope="function")
def client(fastapp):
    client = TestClient(fastapp)
    return client


def test_public_endpoint(client):
    response = client.get("/public")

    assert response.status_code == 200


def test_private_endpoint_without_api_key(client):
    response = client.get("/private")
    assert response.status_code == 401


def test_private_endpoint_with_valid_api_key(client):
    os.environ["API_KEY"] = "secret"
    settings = Settings()
    headers = {"x-api-key": settings.API_KEY}
    response = client.get("/private", headers=headers)
    assert response.status_code == 200

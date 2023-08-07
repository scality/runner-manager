import os

from runner_manager.models.settings import Settings


def test_public_endpoint(client):
    response = client.get("/public")

    assert response.status_code == 200


def test_private_endpoint_without_api_key(client):
    response = client.get("/private")
    # for now we are not using api key
    assert response.status_code == 200


def test_private_endpoint_with_valid_api_key(client):
    os.environ["API_KEY"] = "secret"
    headers = {"x-api-key": "secret"}
    response = client.get("/private", headers=headers)
    assert response.status_code == 200

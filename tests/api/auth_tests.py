import os


def test_public_endpoint(client):
    response = client.get("/public")

    assert response.status_code == 200


def test_private_endpoint_without_api_key(client):
    response = client.get("/private")
    assert response.status_code == 401


def test_private_endpoint_with_valid_api_key(client):
    os.environ["API_KEY"] = "secret"
    headers = {"x-api-key": "secret"}
    response = client.get("/private", headers=headers)
    assert response.status_code == 200

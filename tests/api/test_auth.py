from functools import lru_cache

from runner_manager.dependencies import get_settings
from runner_manager.models.settings import Settings


@lru_cache
def settings_api_key():
    return Settings(api_key="secret")


def test_public_endpoint(client):
    response = client.get("/public")

    assert response.status_code == 200


def test_private_endpoint_without_api_key(fastapp, client):
    response = client.get("/private")
    settings_api_key.cache_clear()
    fastapp.dependency_overrides = {}
    fastapp.dependency_overrides[get_settings] = settings_api_key
    response = client.get("/private")
    assert response.status_code == 401


def test_private_endpoint_with_valid_api_key(fastapp, client):
    settings_api_key.cache_clear()
    fastapp.dependency_overrides = {}
    fastapp.dependency_overrides[get_settings] = settings_api_key
    headers = {"x-api-key": "secret"}
    response = client.get("/private", headers=headers)
    assert response.status_code == 200

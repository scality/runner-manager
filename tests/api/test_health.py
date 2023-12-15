from redis import Redis

from runner_manager.dependencies import get_redis


def test_healthcheck(client):
    response = client.get("/_health/")
    assert response.status_code == 200


def test_healthcheck_redis_unavailable(client, fastapp):
    fake_connection = Redis.from_url("redis://localhost:63799/0")
    fastapp.dependency_overrides[get_redis] = lambda: fake_connection
    response = client.get("/_health/")
    assert response.status_code == 500
    fastapp.dependency_overrides[get_redis] = get_redis
    response = client.get("/_health/")
    assert response.status_code == 200

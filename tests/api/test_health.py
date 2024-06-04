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


def test_index_job_schedule(client, queue, monkeypatch):
    """When the healthcheck fails to ping redis, it should schedule an indexing job"""
    # patch redis ping to raise an exception
    monkeypatch.setattr(Redis, "ping", lambda self: 1 / 0)
    finished_jobs = queue.finished_job_registry.count
    response = client.get("/_health/")
    assert response.status_code == 500
    assert queue.finished_job_registry.count == finished_jobs + 1

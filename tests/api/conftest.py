from datetime import timedelta
from functools import lru_cache

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, settings
from redis import Redis
from redis_om import get_redis_connection
from rq import Queue

from runner_manager import Settings
from runner_manager.dependencies import get_queue, get_settings
from runner_manager.main import app

settings.register_profile(
    "api",
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=5,
    deadline=timedelta(milliseconds=500),
)

settings.load_profile("api")


@lru_cache()
def api_settings():
    return Settings(
        github_token="test",
        github_base_url="http://localhost:4010",
    )


@lru_cache()
def api_queue():
    settings = api_settings()
    redis: Redis = get_redis_connection(
        url=settings.redis_om_url, decode_responses=False
    )
    return Queue(connection=redis, is_async=False)


@pytest.fixture(scope="function")
def fastapp():
    fastapp = app
    fastapp.dependency_overrides = {}
    fastapp.dependency_overrides[get_settings] = api_settings
    fastapp.dependency_overrides[get_queue] = api_queue
    return fastapp


@pytest.fixture()
def client(fastapp):
    client = TestClient(fastapp)
    return client

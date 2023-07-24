import uuid

from pytest import fixture

from runner_manager.models.runner import Runner
from runner_manager.models.settings import Settings
from runner_manager.main import get_settings
from redis_om import get_redis_connection, Migrator



@fixture(scope="session", autouse=True)
def settings() -> Settings:
    settings = get_settings()
    return settings


@fixture(scope="session", autouse=True)
def redis(settings):
    """Configure a random and fresh redis database path."""

    redis_connection = get_redis_connection(url=settings.redis_om_url, decode_responses=True)
    redis_connection.flushall()

    Migrator().run()
    yield redis_connection


@fixture()
def runner() -> Runner:
    runner = Runner(
        name="test", runner_group_id=1, status="online", busy=False)
    Runner.delete(runner.pk)
    return runner

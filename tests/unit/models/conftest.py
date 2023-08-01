from pytest import fixture
from redis_om import Migrator, get_redis_connection

from runner_manager.models.runner_group import RunnerGroup


@fixture(scope="session", autouse=True)
def redis(settings):
    """Flush redis before tests."""

    redis_connection = get_redis_connection(
        url=settings.redis_om_url, decode_responses=True
    )
    redis_connection.flushall()

    Migrator().run()
    yield redis_connection


@fixture()
def runner_group() -> RunnerGroup:
    runner_group = RunnerGroup(
        id=1,
        name="test",
        organization="test",
        backend="base",
        backend_config={},
        labels=[
            "label",
        ],
    )
    return runner_group

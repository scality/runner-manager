from pytest import fixture
from redis_om import Migrator, get_redis_connection

from runner_manager.models.runner import Runner


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
def runner() -> Runner:
    runner = Runner(name="test", runner_group_id=1, status="online", busy=False)
    Runner.delete(runner.pk)
    return runner

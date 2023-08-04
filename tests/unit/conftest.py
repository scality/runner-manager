from pytest import fixture
from redis_om import Migrator, get_redis_connection
from rq import Queue

from runner_manager.dependencies import get_settings
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import Settings


@fixture(scope="session", autouse=True)
def settings() -> Settings:
    settings = get_settings()
    return settings



@fixture(scope="session", autouse=True)
def redis(settings):
    """Flush redis before tests."""

    redis_connection = get_redis_connection(
        url=settings.redis_om_url, decode_responses=True
    )
    redis_connection.flushall()

    Migrator().run()
    yield redis_connection


@fixture(scope="session")
def queue(redis) -> Queue:
    return Queue(connection=redis)


@fixture()
def runner() -> Runner:
    runner = Runner(
        name="test", runner_group_id=1, status="online", busy=False, labels=[]
    )
    Runner.delete(runner.pk)
    return runner


@fixture()
def runner_group() -> RunnerGroup:
    runner_group = RunnerGroup(
        id=1,
        name="test",
        organization="test",
        backend={"name": "base"},
        labels=[
            "label",
        ],
    )
    return runner_group
